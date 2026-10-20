"""Auditable CPU reference scorers. Full Wikipedia requires a sparse backend."""

from collections import Counter, defaultdict
from dataclasses import dataclass
import math
from typing import Mapping, Sequence

from .data import TrainBundle
from .graph import HyperlinkGraph, transition_rows
from .ranking import rank_candidates
from .utils import digest, positive_integer


def bounded_float(value: float, name: str, low: float, high: float) -> None:
    if isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
        raise ValueError(f"{name} must be finite and in [{low}, {high}]")


class Ranker:
    name = "abstract"

    def _set_context(self, train: TrainBundle, graph: HyperlinkGraph | None) -> None:
        if not isinstance(train, TrainBundle):
            raise TypeError("fit requires TrainBundle, not evaluation labels")
        self._train_hash = train.fingerprint
        self._graph_hash = graph.fingerprint if graph else None
        self._fitted = True

    def _require_fit(self) -> None:
        if not getattr(self, "_fitted", False):
            raise ValueError("Call fit before score")

    @property
    def parameters(self) -> dict:
        return {}

    @property
    def fingerprint(self) -> str:
        self._require_fit()
        return digest({"model": self.name, "parameters": self.parameters,
                       "train": self._train_hash, "graph": self._graph_hash})

    def recommend(self, source: str, candidates: Sequence[str],
                  *, k: int = 10, seed: int = 2026) -> list[str]:
        return rank_candidates(source, candidates, self.score(source, candidates),
                               k=k, seed=seed)


class GlobalPopularity(Ranker):
    name = "M0_global"

    def fit(self, train: TrainBundle, graph: HyperlinkGraph | None = None):
        self._set_context(train, None)
        self.popularity = Counter()
        self.local = defaultdict(Counter)
        for (source, target), count in train.counts.items():
            self.popularity[target] += count
            self.local[source][target] += count
        self.totals = {source: sum(row.values()) for source, row in self.local.items()}
        return self

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        return {target: float(self.popularity[target]) for target in candidates}


class LocalMarkov(GlobalPopularity):
    name = "M1_local"

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        row = self.local.get(source, {})
        if not any(row.get(target, 0) for target in candidates):
            return super().score(source, candidates)
        return {target: row.get(target, 0) / self.totals[source] for target in candidates}


class BackoffMarkov(GlobalPopularity):
    name = "M1B_backoff"

    def __init__(self, mu: float = 100.0, eta: float = 1.0):
        bounded_float(mu, "mu", 0, 1e12)
        bounded_float(eta, "eta", 0, 1)
        self.mu, self.eta = mu, eta

    @property
    def parameters(self) -> dict:
        return {"mu": self.mu, "eta": self.eta, "global_epsilon": 1.0}

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        if not candidates:
            return {}
        row = self.local.get(source, {})
        total = sum(row.get(target, 0) for target in candidates)
        global_total = sum(self.popularity[target] + 1 for target in candidates)
        global_prior = {
            target: (self.popularity[target] + 1) / global_total for target in candidates
        }
        if self.mu == 0 and total == 0:
            return global_prior
        prior = {target: (1 - self.eta) / len(candidates) + self.eta * global_prior[target]
                 for target in candidates}
        return {target: (row.get(target, 0) + self.mu * prior[target]) / (total + self.mu)
                for target in candidates}


class UniformHyperlink(Ranker):
    name = "M2_uniform"

    def fit(self, train: TrainBundle, graph: HyperlinkGraph | None = None):
        self._set_context(train, None)
        return self

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        return {target: 1 / len(candidates) for target in candidates}


class InDegree(Ranker):
    name = "M2D_indegree"

    def fit(self, train: TrainBundle, graph: HyperlinkGraph):
        self._set_context(train, graph)
        self.degree = Counter(target for _, target in graph.edges)
        return self

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        return {target: float(self.degree[target]) for target in candidates}


@dataclass(frozen=True)
class PPRResult:
    scores: Mapping[str, float]
    iterations: int
    residual: float
    residual_curve: tuple[float, ...]
    error_bound: float


class ConvergenceError(RuntimeError):
    pass


def personalized_pagerank(rows: Mapping[str, Mapping[str, float]], source: str,
                         *, damping: float = 0.5, tolerance: float = 1e-10,
                         max_iterations: int = 1000) -> PPRResult:
    """Power iteration with absolute fixed-point L1 residual, dangling→source."""
    bounded_float(damping, "damping", 0, 1)
    if not 0 < damping < 1:
        raise ValueError("Require 0 < damping < 1")
    bounded_float(tolerance, "tolerance", 1e-15, 1e-2)
    positive_integer(max_iterations, "max_iterations")
    if source not in rows:
        raise ValueError("Unknown PPR source")
    if len(rows) > 10000 or sum(map(len, rows.values())) > 100000:
        raise ValueError("PPR reference budget exceeded")
    nodes = tuple(sorted(rows))
    for row in rows.values():
        if any(target not in rows or isinstance(weight, bool)
               or not math.isfinite(weight) or weight <= 0 for target, weight in row.items()):
            raise ValueError("Invalid transition probability or endpoint")
        if row and not math.isclose(math.fsum(row.values()), 1.0, abs_tol=1e-12,
                                    rel_tol=0):
            raise ValueError("Non-dangling transition rows must sum to one")
    current = dict.fromkeys(nodes, 0.0)
    current[source] = 1.0
    curve = []
    for iteration in range(max_iterations + 1):
        following = dict.fromkeys(nodes, 0.0)
        following[source] = 1 - damping
        for node in nodes:
            mass = damping * current[node]
            if not rows[node]:
                following[source] += mass
            else:
                for target, probability in sorted(rows[node].items()):
                    following[target] += mass * probability
        residual = math.fsum(abs(following[node] - current[node]) for node in nodes)
        curve.append(residual)
        if residual <= tolerance:
            if not math.isclose(math.fsum(current.values()), 1.0, abs_tol=1e-10):
                raise ArithmeticError("PPR probability mass lost")
            return PPRResult(current, iteration, residual, tuple(curve),
                             residual / (1 - damping))
        current = following
    raise ConvergenceError(
        f"PPR did not converge within {max_iterations} iterations; residual={residual:g}"
    )


class PPR(Ranker):
    def __init__(self, mode: str = "hyperlink", *, damping: float = 0.5,
                 tolerance: float = 1e-10, max_iterations: int = 1000):
        names = {"hyperlink": "M3_ppr_h", "click": "M4C_ppr_c",
                 "click_on_hyperlink": "M4CH_ppr_c_intersect_h"}
        if mode not in names:
            raise ValueError("Unsupported PPR graph mode")
        bounded_float(damping, "damping", 0, 1)
        if not 0 < damping < 1:
            raise ValueError("Require 0 < damping < 1")
        bounded_float(tolerance, "tolerance", 1e-15, 1e-2)
        positive_integer(max_iterations, "max_iterations")
        self.mode, self.name = mode, names[mode]
        self.damping, self.tolerance, self.max_iterations = damping, tolerance, max_iterations

    @property
    def parameters(self) -> dict:
        return {"mode": self.mode, "damping": self.damping, "tolerance": self.tolerance,
                "max_iterations": self.max_iterations, "dangling": "restart_at_source"}

    def fit(self, train: TrainBundle, graph: HyperlinkGraph):
        self._set_context(train, graph)
        support = set(graph.edges)
        if self.mode == "hyperlink":
            weights = {edge: 1.0 for edge in graph.edges}
        else:
            weights = {edge: count for edge, count in train.counts.items()
                       if self.mode == "click" or edge in support}
        self.rows = transition_rows(graph.nodes, weights)
        self.cache: dict[tuple, dict] = {}
        self.diagnostics: dict[str, dict] = {}
        return self

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        if source not in self.rows or any(target not in self.rows for target in candidates):
            raise ValueError("PPR source/candidate outside frozen graph")
        if not candidates:
            return {}
        key = (source, tuple(sorted(candidates)))
        if key not in self.cache:
            result = personalized_pagerank(
                self.rows, source, damping=self.damping, tolerance=self.tolerance,
                max_iterations=self.max_iterations
            )
            self.cache[key] = {target: result.scores[target] for target in candidates}
            self.diagnostics[source] = {
                "iterations": result.iterations, "residual": result.residual,
                "error_bound": result.error_bound, "residual_curve": result.residual_curve,
            }
        return dict(self.cache[key])


class ScoreHybrid(Ranker):
    name = "M6B_score_fusion"

    def __init__(self, click_weight: float = 0.5, *, mu: float = 100.0,
                 eta: float = 1.0, damping: float = 0.5,
                 tolerance: float = 1e-10, max_iterations: int = 1000):
        bounded_float(click_weight, "click_weight", 0, 1)
        self.click_weight = click_weight
        self.behavior = BackoffMarkov(mu, eta)
        self.topology = PPR(damping=damping, tolerance=tolerance,
                            max_iterations=max_iterations)
        self.fallback_sources: set[str] = set()

    @property
    def parameters(self) -> dict:
        return {"click_weight": self.click_weight, "behavior": self.behavior.parameters,
                "topology": self.topology.parameters, "normalization": "candidate_l1"}

    def fit(self, train: TrainBundle, graph: HyperlinkGraph):
        self._set_context(train, graph)
        self.behavior.fit(train)
        self.topology.fit(train, graph)
        self.fallback_sources = set()
        return self

    def score(self, source: str, candidates: Sequence[str]) -> dict[str, float]:
        self._require_fit()
        if not candidates:
            return {}
        behavior = self.behavior.score(source, candidates)
        if self.click_weight == 1:
            return behavior
        # Solver errors are NOT silently hidden: the runner must log any fallback.
        topology = self.topology.score(source, candidates)
        mass = math.fsum(topology.values())
        if mass == 0:
            self.fallback_sources.add(source)
            topology = {target: 1 / len(candidates) for target in candidates}
        else:
            topology = {target: score / mass for target, score in topology.items()}
        return {target: self.click_weight * behavior[target]
                + (1 - self.click_weight) * topology[target] for target in candidates}
