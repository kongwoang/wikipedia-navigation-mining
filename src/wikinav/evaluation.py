"""Observable-label metrics: retain out-of-candidate positives in full denominators."""

from dataclasses import asdict, dataclass
import math
import random
from typing import Mapping, Sequence

from .utils import positive_integer


@dataclass(frozen=True)
class SourceResult:
    source: str
    status: str
    label_pairs: int
    label_mass: int
    eligible_pairs: int
    eligible_mass: int
    candidate_count: int
    returned_count: int
    all_metrics: Mapping[str, float | None]
    conditional_metrics: Mapping[str, float | None]

    def as_dict(self) -> dict:
        return asdict(self)


def _metrics(ranked: Sequence[str], labels: Mapping[str, int],
             recall_ks: Sequence[int], rank_k: int) -> dict[str, float | None]:
    keys = [f"recall@{k}" for k in recall_ks] + [
        f"mrr@{rank_k}", f"ndcg@{rank_k}", f"expected_rr@{rank_k}"
    ] + [f"mass_recall@{k}" for k in recall_ks]
    if not labels:
        return dict.fromkeys(keys, None)
    mass = sum(labels.values())
    result: dict[str, float | None] = {}
    for k in recall_ks:
        result[f"recall@{k}"] = sum(target in labels for target in ranked[:k]) / len(labels)
        result[f"mass_recall@{k}"] = sum(labels.get(t, 0) for t in ranked[:k]) / mass
    top = ranked[:rank_k]
    first = next((rank for rank, target in enumerate(top, 1) if target in labels), None)
    result[f"mrr@{rank_k}"] = 1 / first if first else 0.0
    result[f"expected_rr@{rank_k}"] = math.fsum(
        labels.get(target, 0) / mass / rank for rank, target in enumerate(top, 1)
    )
    dcg = math.fsum(math.log2(1 + labels.get(target, 0)) / math.log2(rank + 1)
                    for rank, target in enumerate(top, 1))
    ideal = sorted(labels.values(), reverse=True)[:rank_k]
    idcg = math.fsum(math.log2(1 + count) / math.log2(rank + 1)
                     for rank, count in enumerate(ideal, 1))
    result[f"ndcg@{rank_k}"] = dcg / idcg
    return result


def evaluate_source(source: str, candidates: Sequence[str], ranked: Sequence[str],
                    labels: Mapping[str, int], *, recall_ks: Sequence[int] = (5, 10, 20),
                    rank_k: int = 10) -> SourceResult:
    if not recall_ks or len(set(recall_ks)) != len(recall_ks):
        raise ValueError("Recall cutoffs must be nonempty and unique")
    for k in (*recall_ks, rank_k):
        positive_integer(k, "cutoff")
    candidate_set = set(candidates)
    if len(candidate_set) != len(candidates) or source in candidate_set:
        raise ValueError("Invalid candidate set")
    if len(set(ranked)) != len(ranked) or not set(ranked) <= candidate_set:
        raise ValueError("Ranking contains duplicate or ineligible targets")
    for target, count in labels.items():
        if target == source or not target:
            raise ValueError("Remove/log self-loop labels before evaluation")
        positive_integer(count, "observed label count")
    eligible = {target: count for target, count in labels.items() if target in candidate_set}
    if not labels:
        status = "no_observable_labels"
    elif not candidates:
        status = "empty_candidates"
    elif not eligible:
        status = "no_eligible_labels"
    else:
        status = "evaluated"
    return SourceResult(
        source, status, len(labels), sum(labels.values()), len(eligible),
        sum(eligible.values()), len(candidates), len(ranked),
        _metrics(ranked, labels, recall_ks, rank_k),
        _metrics(ranked, eligible, recall_ks, rank_k),
    )


def aggregate_results(results: Sequence[SourceResult]) -> dict:
    if not results:
        raise ValueError("Cannot aggregate zero query sources")
    if len({r.source for r in results}) != len(results):
        raise ValueError("Duplicate source results")
    expected_keys = set(results[0].all_metrics)
    if any(set(r.all_metrics) != expected_keys or set(r.conditional_metrics) != expected_keys
           for r in results):
        raise ValueError("Inconsistent metric definitions across sources")
    summary = {
        "queries": len(results),
        "q_all": sum(r.label_pairs > 0 for r in results),
        "q_conditional": sum(r.eligible_pairs > 0 for r in results),
        "no_observable_labels": sum(r.label_pairs == 0 for r in results),
        "empty_candidates": sum(r.candidate_count == 0 for r in results),
        "label_pairs": sum(r.label_pairs for r in results),
        "label_mass": sum(r.label_mass for r in results),
        "eligible_pairs": sum(r.eligible_pairs for r in results),
        "eligible_mass": sum(r.eligible_mass for r in results),
    }
    for numerator, denominator, name in (
        ("eligible_pairs", "label_pairs", "pair_candidate_coverage"),
        ("eligible_mass", "label_mass", "mass_candidate_coverage"),
    ):
        summary[name] = summary[numerator] / summary[denominator] if summary[denominator] else None
    summary["service_coverage"] = sum(r.returned_count > 0 for r in results) / len(results)
    for attr, label in (("all_metrics", "all"), ("conditional_metrics", "conditional")):
        metric_summary = {}
        for metric in sorted(expected_keys):
            scored = [(r, getattr(r, attr)[metric]) for r in results
                      if getattr(r, attr)[metric] is not None]
            # Conditional traffic weighting uses FULL source label mass, as specified.
            metric_summary[metric] = {
                "macro": math.fsum(value for _, value in scored) / len(scored) if scored else None,
                "traffic_weighted": (
                    math.fsum(r.label_mass * value for r, value in scored)
                    / sum(r.label_mass for r, _ in scored)
                ) if scored else None,
                "sources": len(scored),
            }
        summary[label] = metric_summary
    return summary


def paired_bootstrap(left: Mapping[str, float], right: Mapping[str, float], *,
                     seed: int = 2026, resamples: int = 2000) -> dict:
    """Paired source-resampling CI for mean(left-right), not iid click events."""
    if not left or set(left) != set(right):
        raise ValueError("Paired comparison requires identical nonempty source sets")
    positive_integer(resamples, "resamples")
    if resamples < 100:
        raise ValueError("At least 100 bootstrap resamples required")
    if any(not math.isfinite(v) for v in (*left.values(), *right.values())):
        raise ValueError("Nonfinite paired metric")
    differences = [left[source] - right[source] for source in sorted(left)]
    rng = random.Random(seed)
    samples = sorted(math.fsum(rng.choices(differences, k=len(differences))) / len(differences)
                     for _ in range(resamples))

    def quantile(p: float) -> float:
        index = p * (len(samples) - 1)
        lo, hi = math.floor(index), math.ceil(index)
        return samples[lo] + (samples[hi] - samples[lo]) * (index - lo)

    return {
        "difference": math.fsum(differences) / len(differences),
        "ci95": [quantile(0.025), quantile(0.975)],
        "sources": len(differences), "resamples": resamples, "seed": seed,
        "unit": "source_article", "method": "paired_percentile_bootstrap",
        "limitation": "Conditional query-level approximation; graph sources may be dependent.",
    }
