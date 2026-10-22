"""Controlled extension scorers: reusable sparse PPR, tie-break and cycle relevance."""
import math
import time
import numpy as np
from scipy import sparse
from .models import ConvergenceError
from .sparse_models import normalize
from .utils import digest


class PreparedPPR:
    """Prepare transpose/dangling once; same fixed-point contract as reference."""
    def __init__(self, weights):
        matrix=normalize(weights)
        self.dangling=np.asarray(matrix.sum(axis=1)).ravel()==0
        self.transpose=matrix.T.tocsr()
        self.n=matrix.shape[0]

    def solve(self, source, damping=.15, tolerance=1e-8, max_iterations=1000):
        if not 0<damping<1 or tolerance<=0 or not 0<=source<self.n:
            raise ValueError('Invalid PPR parameters')
        x=np.zeros(self.n);x[source]=1.
        start=time.perf_counter()
        for iteration in range(max_iterations+1):
            y=damping*(self.transpose@x)
            y[source]+=1-damping+damping*x[self.dangling].sum()
            residual=float(np.abs(y-x).sum())
            if residual<=tolerance:
                if not np.isfinite(x).all() or np.any(x<0) or not np.isclose(x.sum(),1.,atol=1e-10):
                    raise ArithmeticError('Invalid PPR distribution')
                return x,{'iterations':iteration,'residual':residual,'error_bound':residual/(1-damping),
                          'seconds':time.perf_counter()-start}
            x=y
        raise ConvergenceError('Extension PPR iteration budget exceeded')


def score_ppr(data, weights, damping=.15):
    solver=PreparedPPR(weights);scores={};diagnostics={}
    for s in data.queries:
        x,d=solver.solve(s,damping)
        scores[s]=x[data.candidates(s)];diagnostics[str(data.ids[s])]=d
    return scores,diagnostics


def tie_scores(data, topology, seed=2026):
    """Ordinal scores encode lexicographic count/PPR/hash order, not probabilities."""
    scores={}
    for s in data.queries:
        candidates=data.candidates(s)
        counts=data.counts[s,candidates].toarray().ravel()
        order=sorted(range(len(candidates)),key=lambda i:(-int(counts[i]),-float(topology[s][i]),
            digest([seed,str(data.ids[s]),str(data.ids[candidates[i]])]),str(data.ids[candidates[i]])))
        row=np.empty(len(order),dtype=float)
        for rank,i in enumerate(order):row[i]=len(order)-rank
        scores[s]=row
    return scores


def adaptive_scores(data, behavior, topology, tau):
    if tau<=0:raise ValueError('tau must be positive')
    scores={}
    for s in data.queries:
        mass=float(data.counts[s,data.candidates(s)].sum())
        weight=mass/(mass+tau)
        top=topology[s].copy()
        if len(top):top=top/top.sum() if top.sum() else np.ones(len(top))/len(top)
        scores[s]=weight*behavior[s]+(1-weight)*top
    return scores


def cycle_scores(data, max_length=3):
    """Exact rooted simple directed cycles of length 2 or 3, exp(-length) gain.

    Each cycle starts at source, so rotations are not double counted. Reverse
    directed cycles are distinct. Both non-source nodes in a triangle receive
    the cycle's contribution. This is bounded CycleRank, not full enumeration.
    """
    if max_length not in (2,3):raise ValueError('Only audited bounded lengths 2/3')
    a=data.adjacency.tocsr();at=a.T.tocsr()
    neighbors=[a.indices[a.indptr[i]:a.indptr[i+1]] for i in range(a.shape[0])]
    scores={};stats={}
    for s in data.queries:
        incoming=set(at.indices[at.indptr[s]:at.indptr[s+1]])
        values={};counts={2:0,3:0}
        for v in neighbors[s]:
            if v==s:continue
            if v in incoming:
                values[v]=values.get(v,0.)+math.exp(-2);counts[2]+=1
            if max_length==3:
                for w in neighbors[v]:
                    if w==s or w==v or w not in incoming:continue
                    for node in (v,w):values[node]=values.get(node,0.)+math.exp(-3)
                    counts[3]+=1
        scores[s]=np.array([values.get(v,0.) for v in data.candidates(s)])
        stats[str(data.ids[s])]={'cycles2':counts[2],'cycles3':counts[3]}
    return scores,stats


def rewire_graph(adjacency, protected_sources, seed, swaps_per_edge=5, attempts_per_edge=100):
    """Degree-preserving directed swaps with protected query outgoing edges."""
    coo=adjacency.tocoo();edges=list(zip(map(int,coo.row),map(int,coo.col)))
    if any(s==t for s,t in edges) or len(set(edges))!=len(edges):raise ValueError('Requires loop-free simple graph')
    protected=set(protected_sources)
    positions=[i for i,(s,t) in enumerate(edges) if s not in protected]
    target=swaps_per_edge*len(positions);limit=attempts_per_edge*len(positions)
    if len(positions)<2:raise ValueError('Insufficient modifiable edges')
    membership=set(edges);rng=np.random.default_rng(seed);accepted=attempts=0
    while accepted<target and attempts<limit:
        attempts+=1
        i,j=(positions[int(x)] for x in rng.integers(len(positions),size=2))
        a,b=edges[i];c,d=edges[j]
        if a==c or b==d or a==d or c==b or (a,d) in membership or (c,b) in membership:continue
        membership.remove((a,b));membership.remove((c,d))
        membership.add((a,d));membership.add((c,b));edges[i]=(a,d);edges[j]=(c,b);accepted+=1
    s,t=np.array(edges,dtype=np.int32).T
    result=sparse.csr_matrix((np.ones(len(edges),dtype=np.uint8),(s,t)),shape=adjacency.shape)
    if not np.array_equal(result.sum(axis=0),adjacency.sum(axis=0)) or not np.array_equal(result.sum(axis=1),adjacency.sum(axis=1)):
        raise AssertionError('Degree sequence changed')
    if (result[list(protected)]!=adjacency[list(protected)]).nnz:raise AssertionError('Protected candidates changed')
    return result,{'seed':seed,'accepted_swaps':accepted,'target_swaps':target,'attempts':attempts,
                   'target_reached':accepted==target,'edge_overlap':result.multiply(adjacency).nnz/adjacency.nnz,
                   'degree_invariant':True,'query_candidates_invariant':True,'interpretation':'descriptive perturbation; not equilibrium null p-value'}
