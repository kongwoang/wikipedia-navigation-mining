import math
import unittest
from types import SimpleNamespace
try:
    import numpy as np
    from scipy import sparse
    from wikinav.extension_models import PreparedPPR,tie_scores,adaptive_scores,cycle_scores,rewire_graph
    from wikinav.sparse_models import solve_ppr,normalize
except ImportError:
    np=None


def fixture(edges,counts=None,query=0,n=4):
    rows,cols=zip(*edges)
    a=sparse.csr_matrix((np.ones(len(edges)),(rows,cols)),shape=(n,n))
    c=sparse.csr_matrix((n,n)) if counts is None else sparse.csr_matrix(np.array(counts))
    data=SimpleNamespace(ids=list(map(str,range(n))),adjacency=a,counts=c,queries=[query])
    data.candidates=lambda s:a.indices[a.indptr[s]:a.indptr[s+1]]
    return data


@unittest.skipIf(np is None,'scientific dependencies unavailable')
class ExtensionTests(unittest.TestCase):
    def test_prepared_ppr_matches_reference_with_dangling(self):
        d=fixture([(0,1),(0,2),(2,0),(2,3)])
        for damping in (.15,.5,.85):
            x,info=PreparedPPR(d.adjacency).solve(0,damping)
            y,_=solve_ppr(normalize(d.adjacency),0,damping)
            np.testing.assert_allclose(x,y,atol=1e-13)
            self.assertLessEqual(info['residual'],1e-8)

    def test_ppr_zero_budget_fails(self):
        from wikinav.models import ConvergenceError
        d=fixture([(0,1),(1,0)])
        with self.assertRaises(ConvergenceError):PreparedPPR(d.adjacency).solve(0,max_iterations=0)

    def test_tie_break_never_inverts_unequal_counts(self):
        d=fixture([(0,1),(0,2),(0,3)],[[0,20,10,10],[0]*4,[0]*4,[0]*4])
        s=tie_scores(d,{0:np.array([.01,.1,.9])})[0]
        self.assertGreater(s[0],s[2]);self.assertGreater(s[2],s[1])

    def test_adaptive_zero_history_is_topology(self):
        d=fixture([(0,1),(0,2)])
        s=adaptive_scores(d,{0:np.array([1.,0.])},{0:np.array([1.,3.])},100)[0]
        np.testing.assert_allclose(s,[.25,.75])

    def test_cycle_triangle_scores_both_nodes(self):
        d=fixture([(0,1),(1,2),(2,0),(0,2)])
        scores,counts=cycle_scores(d,3)
        np.testing.assert_allclose(scores[0],[math.exp(-3),math.exp(-2)+math.exp(-3)])
        self.assertEqual(counts['0'],{'cycles2':1,'cycles3':1})

    def test_cycle_length2_excludes_triangle(self):
        d=fixture([(0,1),(1,2),(2,0)])
        s,info=cycle_scores(d,2);self.assertEqual(s[0][0],0)
        self.assertEqual(info['0']['cycles3'],0)

    def test_rewire_preserves_degrees_queries_and_seed(self):
        d=fixture([(0,1),(0,2),(1,2),(1,3),(2,3),(2,4),(3,4),(3,5),(4,5),(4,1),(5,1),(5,2)],n=6)
        a,info=rewire_graph(d.adjacency,[0],17,2,100)
        b,_=rewire_graph(d.adjacency,[0],17,2,100)
        self.assertEqual((a!=b).nnz,0);self.assertGreater(info['accepted_swaps'],0)
        np.testing.assert_equal(a.sum(axis=0),d.adjacency.sum(axis=0))
        np.testing.assert_equal(a.sum(axis=1),d.adjacency.sum(axis=1))
        self.assertEqual((a[0]!=d.adjacency[0]).nnz,0)
        self.assertEqual(a.diagonal().sum(),0)

@unittest.skipIf(np is None,'scientific dependencies unavailable')
class PeriodIntegrityTests(unittest.TestCase):
    def test_period_mapping_and_history_priors(self):
        import tempfile,gzip
        from pathlib import Path
        import duckdb
        from wikinav.extension_data import PeriodStore
        from wikinav.study_data import StudyData
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);prepared=root/'prepared';prepared.mkdir();raw=root/'raw';raw.mkdir()
            con=duckdb.connect(str(prepared/'study.duckdb'))
            con.execute('CREATE TABLE titlemap(title VARCHAR,canonical BIGINT)')
            con.execute("INSERT INTO titlemap VALUES ('A',1),('Alias',1),('B',2),('C',3),('D',4)");con.close()
            for month,text in [('2018-01','A\tB\tlink\t10\nAlias\tB\tlink\t15\nA\tUnknown\tlink\t12\nD\tB\tlink\t100\n'),('2018-02','A\tC\tlink\t20\n')]:
                with gzip.open(raw/f'clickstream-eswiki-{month}.tsv.gz','wt') as f:f.write(text)
            store=PeriodStore(prepared,raw,root/'extension.duckdb')
            labels,_=store.period('2018-01',['1'])
            self.assertEqual(labels,{'1':{'2':25,'oov:Unknown':12}})
            a=sparse.csr_matrix([[0,1,1],[0,0,0],[0,0,0]])
            data=StudyData(['1','2','3'],['A','B','C'],a,sparse.csr_matrix((3,3)),[0],{}, {})
            jan=store.training(data,['2018-01']);feb=store.training(data,['2018-02'])
            self.assertEqual(jan.counts[0,1],25)
            self.assertEqual(jan.features['popularity'][1],125)
            self.assertEqual(feb.features['popularity'][1],0)
            self.assertEqual(feb.counts[0,2],20)
            store.close()

    def test_frozen_prediction_tampering_rejected(self):
        import tempfile,json
        from pathlib import Path
        from unittest.mock import patch
        from wikinav.extension_experiment import freeze,frozen_predictions
        with tempfile.TemporaryDirectory() as tmp,patch('wikinav.extension_experiment.signature',return_value={'fixture':1}):
            p=Path(tmp);freeze(p,{'model':{'fixture':1}},{})
            self.assertEqual(frozen_predictions(p),{'model':{'fixture':1}})
            (p/'predictions.json').write_text(json.dumps({'model':{'fixture':2}}))
            with self.assertRaisesRegex(ValueError,'predictions changed'):frozen_predictions(p)
