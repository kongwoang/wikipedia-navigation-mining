"""Sparse graph scorers, with the same residual/dangling contract as the oracle."""

import math
import time

import numpy as np
from scipy import sparse

from .models import ConvergenceError


def normalize(matrix):
    m = sparse.csr_matrix(matrix, dtype=np.float64)
    m.eliminate_zeros()
    if not np.isfinite(m.data).all() or np.any(m.data < 0):
        raise ValueError("Invalid sparse weights")
    totals = np.asarray(m.sum(axis=1)).ravel()
    inv = np.divide(1.0, totals, out=np.zeros_like(totals), where=totals > 0)
    return sparse.diags(inv).dot(m).tocsr()


def transitions(data, mode="H", mu=100.0, mixing=0.5):
    h = normalize(data.adjacency)
    if mode == "H":
        return h
    if mode == "C":
        return normalize(data.counts)
    eligible = data.counts.multiply(data.adjacency)
    if mode == "CH":
        return normalize(eligible)
    if mode == "WH":
        if mu <= 0:
            raise ValueError("Positive smoothing required for fixed H support")
        return normalize(eligible + mu * h)
    if mode == "MIX":
        pc = normalize(eligible)
        empty = np.asarray(pc.sum(axis=1)).ravel() == 0
        pc = pc + sparse.diags(empty.astype(float)) @ h
        return (mixing * pc + (1-mixing) * h).tocsr()
    raise ValueError("Unknown transition mode")


def solve_ppr(matrix, source, damping=0.5, tolerance=1e-8, max_iterations=1000):
    if not 0 < damping < 1 or tolerance <= 0:
        raise ValueError("Invalid solver parameters")
    row_sum = np.asarray(matrix.sum(axis=1)).ravel()
    if np.any((row_sum != 0) & (np.abs(row_sum-1) > 1e-12)):
        raise ValueError("Transition rows must sum to one or zero")
    dangling = row_sum == 0
    transposed = matrix.T.tocsr()
    current = np.zeros(matrix.shape[0])
    current[source] = 1
    curve = []
    start = time.perf_counter()
    for iteration in range(max_iterations+1):
        following = damping * (transposed @ current)
        following[source] += 1-damping + damping*current[dangling].sum()
        residual = float(np.abs(following-current).sum())
        curve.append(residual)
        if residual <= tolerance:
            if not np.isclose(current.sum(), 1.0, atol=1e-10) or np.any(current < 0):
                raise ArithmeticError("Probability conservation failure")
            return current, {"iterations": iteration, "residual": residual,
                             "error_bound": residual/(1-damping), "residual_curve": curve,
                             "seconds": time.perf_counter()-start}
        current = following
    raise ConvergenceError(f"Sparse PPR residual {residual} exceeds {tolerance}")


def ppr_scores(data, matrix, damping, tolerance=1e-8):
    scores, diagnostics = {}, {}
    for source in data.queries:
        candidates = data.candidates(source)
        if len(candidates) == 0:
            scores[source], diagnostics[source] = np.empty(0), {"status": "empty_candidates"}
            continue
        r, diagnostic = solve_ppr(matrix, source, damping, tolerance)
        scores[source] = r[candidates]
        diagnostics[source] = diagnostic
    return scores, diagnostics


def baseline_scores(data, kind, mu=100.0, eta=1.0):
    result = {}
    indegree = np.asarray(data.adjacency.sum(axis=0)).ravel()
    for source in data.queries:
        candidates = data.candidates(source)
        local = data.counts[source, candidates].toarray().ravel().astype(float)
        popularity = np.asarray(data.features["popularity"][candidates], dtype=float)
        if kind == "global":
            score = popularity
        elif kind == "local":
            score = local if local.sum() else popularity
        elif kind == "uniform":
            score = np.ones(len(candidates))
        elif kind == "indegree":
            score = indegree[candidates]
        elif kind == "backoff":
            if not len(candidates):
                score = np.empty(0)
            else:
                prior_global = (popularity+1)/(popularity+1).sum()
                prior = (1-eta)/len(candidates) + eta*prior_global
                total = local.sum()
                score = prior_global if total+mu == 0 else (local+mu*prior)/(total+mu)
        else:
            raise ValueError("Unknown baseline")
        result[source] = score
    return result


def fusion(behavior, topology, weight):
    result = {}
    for source, score in behavior.items():
        top = topology[source]
        mass = top.sum()
        if len(top):
            top = top/mass if mass else np.ones(len(top))/len(top)
        result[source] = weight*score+(1-weight)*top
    return result


def hits_scores(data, tolerance=1e-10, max_iterations=2000):
    a = data.adjacency
    authority = np.ones(a.shape[0])/math.sqrt(a.shape[0])
    for i in range(max_iterations):
        following = a.T @ (a @ authority)
        norm = np.linalg.norm(following)
        if norm == 0:
            following = np.zeros_like(authority)
        else:
            following /= norm
        residual = np.linalg.norm(following-authority)
        authority = following
        if residual < tolerance:
            return {s: authority[data.candidates(s)] for s in data.queries}, {
                "iterations": i+1, "l2_iterate_difference": float(residual)}
    raise ConvergenceError("HITS failed")
