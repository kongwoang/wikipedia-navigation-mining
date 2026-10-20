"""Immutable small directed graph, independent hyperlink provenance and queries."""

from dataclasses import dataclass
from datetime import date
from types import MappingProxyType
from typing import Iterable, Mapping

from .config import Protocol
from .utils import digest, positive_integer


@dataclass(frozen=True)
class HyperlinkGraph:
    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str], ...]
    snapshot: str
    source_kind: str
    source_sha256: str

    def __post_init__(self) -> None:
        if self.source_kind not in {"synthetic_hyperlink", "independent_hyperlink"}:
            raise ValueError("Hyperlink topology must not come from clickstream")
        date.fromisoformat(self.snapshot)
        nodes = tuple(sorted(self.nodes))
        if len(set(nodes)) != len(nodes) or any(not isinstance(n, str) or not n for n in nodes):
            raise ValueError("Graph nodes must be unique nonempty string IDs")
        if len(nodes) > 10000 or len(self.edges) > 100000:
            raise ValueError("Reference graph limit exceeded; use a sparse production backend")
        node_set = set(nodes)
        edges = set()
        for source, target in self.edges:
            if source not in node_set or target not in node_set:
                raise ValueError("Edge endpoint absent from frozen node inventory")
            if source == target:
                raise ValueError("Self-loops must be removed and logged during preparation")
            edges.add((source, target))
        if len(self.source_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.source_sha256):
            raise ValueError("A source SHA256 is required")
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "edges", tuple(sorted(edges)))
        outgoing = {node: [] for node in nodes}
        for source, target in sorted(edges):
            outgoing[source].append(target)
        object.__setattr__(self, "_outgoing", MappingProxyType({
            node: tuple(targets) for node, targets in outgoing.items()
        }))

    def validate_protocol(self, protocol: Protocol) -> None:
        if self.snapshot != protocol.graph_snapshot:
            raise ValueError("Graph snapshot differs from protocol")
        if date.fromisoformat(self.snapshot) > protocol.training_cutoff:
            raise ValueError("Future graph")

    def candidates(self, source: str) -> tuple[str, ...]:
        if source not in self._outgoing:
            raise ValueError("Unknown source outside frozen node inventory")
        return self._outgoing[source]

    @property
    def fingerprint(self) -> str:
        return digest({
            "nodes": self.nodes, "edges": self.edges, "snapshot": self.snapshot,
            "source_kind": self.source_kind, "source_sha256": self.source_sha256,
        })

    def candidate_fingerprint(self, sources: Iterable[str]) -> str:
        sources = tuple(sources)
        if len(set(sources)) != len(sources):
            raise ValueError("Duplicate query source")
        return digest([[source, self.candidates(source)] for source in sorted(sources)])


def sample_sources(graph: HyperlinkGraph, size: int, seed: int) -> tuple[str, ...]:
    """Uniform deterministic query sampling from graph only, never future labels."""
    positive_integer(size, "size")
    if type(seed) is not int:
        raise ValueError("seed must be an integer")
    return tuple(sorted(graph.nodes, key=lambda node: (digest([seed, node]), node))[:size])


def transition_rows(nodes: Iterable[str],
                    weights: Mapping[tuple[str, str], float]) -> dict[str, dict[str, float]]:
    """Empty rows are dangling; no fabricated edges or automatic backoff."""
    import math

    nodes = tuple(nodes)
    if len(set(nodes)) != len(nodes):
        raise ValueError("Duplicate nodes")
    rows: dict[str, dict[str, float]] = {node: {} for node in nodes}
    for (source, target), weight in sorted(weights.items()):
        if source not in rows or target not in rows:
            raise ValueError("Unknown transition endpoint")
        if isinstance(weight, bool) or not math.isfinite(weight) or weight <= 0:
            raise ValueError("Weights must be finite and positive")
        rows[source][target] = float(weight)
    for row in rows.values():
        total = math.fsum(row.values())
        if row:
            if not math.isfinite(total):
                raise ValueError("Transition row overflow")
            for target in row:
                row[target] /= total
    return rows
