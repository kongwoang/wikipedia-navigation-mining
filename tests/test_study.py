import csv
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import numpy as np
    from scipy import sparse
    import duckdb
    import gensim
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

if AVAILABLE:
    from wikinav.embeddings import DirectedWalks, train_embedding
    from wikinav.models import personalized_pagerank
    from wikinav.sparse_models import normalize, solve_ppr, transitions, baseline_scores, fusion
    from wikinav.study_data import StudyData, prepare, heldout, load_study, click_table, connection

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(AVAILABLE, "Install requirements-study.lock for sparse/data integration tests")
class SparseTests(unittest.TestCase):
    def setUp(self):
        a = sparse.csr_matrix(np.array([[0,1,1,0],[1,0,0,1],[0,1,0,0],[0,0,0,0]],dtype=float))
        c = sparse.csr_matrix(np.array([[0,4,0,0],[0,0,2,0],[0,0,0,0],[0,0,0,0]],dtype=float))
        self.data = StudyData(["A","B","C","D"],["A","B","C","D"],a,c,[0,1,2,3],
                              {"popularity":np.array([0,4,2,0])},{})

    def test_sparse_matches_dictionary_oracle(self):
        p = normalize(self.data.adjacency)
        rows = {str(i):{str(j):float(p[i,j]) for j in p[i].indices} for i in range(4)}
        for d in (.15,.5,.85):
            actual, info = solve_ppr(p,0,d,1e-12)
            expected = personalized_pagerank(rows,"0",damping=d,tolerance=1e-12)
            np.testing.assert_allclose(actual,[expected.scores[str(i)] for i in range(4)],atol=1e-11)
            self.assertLessEqual(info["residual"],1e-12)

    def test_weighting_support_and_empty_row_fallback(self):
        h, wh, ch = (transitions(self.data,k) for k in ("H","WH","CH"))
        self.assertEqual(set(zip(*h.nonzero())),set(zip(*wh.nonzero())))
        self.assertLess(ch.nnz,h.nnz)
        mixed = transitions(self.data,"MIX",mixing=1)
        np.testing.assert_allclose(mixed[2].toarray(),h[2].toarray())
        self.assertEqual(transitions(self.data,"C")[1,2],1)
        self.assertEqual(ch[1,2],0)

    def test_fusion_endpoints(self):
        b=baseline_scores(self.data,"backoff")
        h=baseline_scores(self.data,"uniform")
        for i in b:
            np.testing.assert_allclose(fusion(b,h,1)[i],b[i])
            if len(h[i]):
                np.testing.assert_allclose(fusion(b,h,0)[i],h[i]/h[i].sum())

    def test_directed_node2vec_convention_and_weight(self):
        # At B after A: return A weight 1/p; D does not point to A => 1/q.
        walks=DirectedWalks(self.data.adjacency,p=2,q=.5,walks=2,length=6)
        np.testing.assert_allclose(walks.probabilities(0,1),[.2,.8])
        self.assertEqual(list(walks),list(walks))
        for walk in walks:
            for s,t in zip(walk,walk[1:]):
                self.assertGreater(self.data.adjacency[int(s),int(t)],0)
        weighted=DirectedWalks(sparse.csr_matrix([[0,2,1],[0,0,0],[0,0,0]]))
        np.testing.assert_allclose(weighted.probabilities(None,0),[2/3,1/3])

    def test_embedding_reproducibility_and_loss_semantics(self):
        kwargs=dict(dimension=8,walks=2,length=5,epochs=2,seed=17)
        _, v1, info=train_embedding(self.data,self.data.adjacency,**kwargs)
        _, v2, _=train_embedding(self.data,self.data.adjacency,**kwargs)
        np.testing.assert_array_equal(v1,v2)
        cumulative=[r["cumulative_sgns_loss"] for r in info["loss"]]
        self.assertEqual(len(cumulative),2)
        self.assertTrue(all(r["epoch_loss_delta"]>=0 for r in info["loss"]))
        self.assertAlmostEqual(sum(r["epoch_loss_delta"] for r in info["loss"]),cumulative[-1])


@unittest.skipUnless(AVAILABLE, "Install study dependencies")
class PreparationTests(unittest.TestCase):
    def test_redirect_chains_cycles_and_missing_targets(self):
        from wikinav.redirects import resolve_targets
        resolved,status=resolve_targets({1:2,2:3,4:5,5:4,6:4,7:None,8:7})
        self.assertEqual(resolved,{1:3,2:3,4:None,5:None,6:None,7:None,8:None})
        self.assertEqual(status[6],'cycle')
        self.assertEqual(status[8],'dangling')

    def test_redirect_events_unsorted_and_utc_boundary(self):
        from wikinav.redirects import latest_redirects
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'r.gz'
            with gzip.open(path,'wt') as f:
                f.write('page_id,page_title,revision_id,revision_parent_id,revision_timestamp,revision_minor,redirect.target,redirect.tosection\n')
                f.write('1,A,3,2,2018-03-01T00:00:01Z,0,FUTURE,\n')
                f.write('1,A,2,1,2018-02-28T23:59:59Z,0,B,\n')
                f.write('1,A,1,0,2018-01-01T00:00:00Z,0,C,\n')
                f.write('2,B,2,1,2018-02-20T00:00:00Z,0,#NOREDIRECT,\n')
            states,audit=latest_redirects(path,'2018-03-01')
            self.assertEqual(states,{1:'B',2:'#NOREDIRECT'})
            self.assertEqual(audit['future_events_excluded'],1)

    def make_raw(self, root):
        raw=root/"raw"; raw.mkdir()
        mapping=raw/"eswiki.snapshot.resolve_redirect.2018-03-01.csv.gz"
        header=["page_id","page_title","revision_id","revision_parent_id","revision_timestamp",
                "redirect_id","redirect_title","redirect_revision_id","redirect_revision_parent_id",
                "redirect_revision_timestamp"]
        with gzip.open(mapping,"wt") as f:
            writer=csv.writer(f); writer.writerow(header)
            for i,title,j,dest in [(1,"A",1,"A"),(2,"B",2,"B"),(3,"Alias B",2,"B"),(4,"D",4,"D")]:
                writer.writerow([i,title,1,0,"2018-02-01T00:00:00+00:00",j,dest,1,0,"2018-02-01T00:00:00+00:00"])
        with gzip.open(raw/"eswiki.wikilink_graph.2018-03-01.csv.gz","wt") as f:
            f.write("page_id_from\tpage_title_from\tpage_id_to\tpage_title_to\n")
            f.write("1\tA\t3\tAlias B\n2\tB\t1\tA\n1\tA\t4\tD\n4\tD\t1\tA\n")
        with gzip.open(raw/'eswiki.redirects.20180301.csv.gz','wt') as f:
            f.write('page_id,page_title,revision_id,revision_parent_id,revision_timestamp,revision_minor,redirect.target,redirect.tosection\n')
            f.write('3,Alias B,1,0,2018-02-01T00:00:00Z,0,B,\n')
        for m in range(1,7):
            with gzip.open(raw/f"clickstream-eswiki-2018-{m:02}.tsv.gz","wt") as f:
                if m==5:
                    f.write("A\tB\tlink\t10\nA\tNew_article\tlink\t20\n")
                else:
                    f.write(f"A\tB\tlink\t{m*10}\nB\tA\tlink\t10\nother-search\tA\texternal\t20\n")
        cfg=root/"study.toml"
        cfg.write_text((ROOT/"configs/study.toml").read_text().replace("query_degree_min = 5","query_degree_min = 1").replace('duplicate_policy = "quarantine"','duplicate_policy = "error"'))
        return raw,cfg

    def test_preparation_and_unreachable_heldout_label(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); raw,cfg=self.make_raw(root); output=root/"prepared"
            result=prepare(raw,output,cfg)
            self.assertEqual(result["full"]["mapping_nonidentity_rows"],1)
            self.assertEqual(result["full"]["sample_nodes"],3)
            data=load_study(output)
            self.assertEqual(data.ids,["1","2","4"])
            self.assertEqual(data.counts[0,1],60)
            short=load_study(output,["2018-03"])
            self.assertEqual(short.counts[0,1],30)
            self.assertEqual(short.features["popularity"][1],30)
            labels,audit=heldout(raw,output,"2018-05")
            self.assertEqual(labels["1"],{"2":10,"oov:New article":20})
            self.assertEqual(audit["ledger"]["unmapped"]["mass"],20)
            frozen=file_hashes(output)
            # Held-out labels never affect graph, mapping, sampled queries or training artifacts.
            with gzip.open(raw/"clickstream-eswiki-2018-05.tsv.gz","wt") as f:
                f.write("A\tD\tlink\t100\n")
            heldout(raw,output,"2018-05")
            self.assertEqual(frozen,file_hashes(output))

    def test_duplicate_raw_rows_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); raw,cfg=self.make_raw(root)
            with gzip.open(raw/"clickstream-eswiki-2018-01.tsv.gz","wt") as f:
                f.write("A\tB\tlink\t10\nA\tB\tlink\t10\n")
            with self.assertRaisesRegex(ValueError,"duplicate"):
                prepare(raw,root/"prepared",cfg)

    def test_quarantine_removes_entire_duplicate_group_and_reconciles(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); raw,cfg=self.make_raw(root)
            cfg.write_text(cfg.read_text().replace('duplicate_policy = "error"','duplicate_policy = "quarantine"'))
            with gzip.open(raw/'clickstream-eswiki-2018-01.tsv.gz','wt') as f:
                f.write('A\tB\tlink\t10\nA\tB\tlink\t20\nB\tA\tlink\t30\n')
            result=prepare(raw,root/'prepared',cfg)
            audit=result['training_audits'][0]
            self.assertEqual(audit['ledger']['duplicate_raw_quarantined'],{'rows':2,'mass':30})
            self.assertEqual(sum(x['mass'] for x in audit['ledger'].values()),60)
            data=load_study(root/'prepared',['2018-01'])
            self.assertEqual(data.counts[0,1],0)

    def test_future_mapping_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); raw,cfg=self.make_raw(root)
            path=raw/"eswiki.snapshot.resolve_redirect.2018-03-01.csv.gz"
            with gzip.open(path,"rt") as f: content=f.read()
            with gzip.open(path,"wt") as f: f.write(content.replace("2018-02-01","2018-04-01"))
            with self.assertRaisesRegex(ValueError,"future"):
                prepare(raw,root/"prepared",cfg)

    def test_experiment_freezes_before_test_and_completes(self):
        from wikinav.experiment import run
        from wikinav.study_data import heldout as actual_heldout
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); raw,cfg=self.make_raw(root)
            text=cfg.read_text()
            for old,new in [
                ('damping = [0.15, 0.5, 0.85]','damping = [0.5]'),
                ('mu = [0.0, 10.0, 100.0, 1000.0]','mu = [10.0]'),
                ('eta = [0.0, 0.5, 1.0]','eta = [1.0]'),
                ('lambda = [0.0, 0.25, 0.5, 0.75, 1.0]','lambda = [0.0, 1.0]'),
                ('embedding_seeds = [17, 29, 43]','embedding_seeds = [17]'),
                ('embedding_dimensions = [32, 64]','embedding_dimensions = [8]'),
                ('embedding_pq = [[1.0, 1.0], [0.5, 2.0], [2.0, 0.5]]','embedding_pq = [[1.0, 1.0]]'),
                ('bootstrap_resamples = 2000','bootstrap_resamples = 100'),
                ('embedding_epochs = 5','embedding_epochs = 2')]:
                text=text.replace(old,new)
            cfg.write_text(text)
            prepared=root/'prepared'; output=root/'run'
            prepare(raw,prepared,cfg)
            calls=[]
            def guard(raw,prepared,month):
                if month in ('2018-05','2018-06'):
                    self.assertTrue((output/'freeze.json').exists())
                    self.assertTrue((output/'predictions.json').exists())
                calls.append(month)
                return actual_heldout(raw,prepared,month)
            with patch('wikinav.experiment.heldout',side_effect=guard):
                result=run(raw,prepared,output,cfg)
            self.assertEqual(calls,['2018-04','2018-05','2018-06'])
            self.assertEqual(set(result),{'2018-05','2018-06'})
            self.assertEqual(json.loads((output/'completion.json').read_text())['status'],'complete')
            with self.assertRaises(FileExistsError):
                run(raw,prepared,output,cfg)


def file_hashes(folder):
    from wikinav.utils import file_digest
    return {p.name:file_digest(p) for p in folder.glob("*.parquet")}
