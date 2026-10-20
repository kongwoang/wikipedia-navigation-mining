"""One tie policy shared by all scorers and candidate sets."""

import math
from typing import Mapping, Sequence

from .utils import digest, positive_integer


def rank_candidates(source: str, candidates: Sequence[str], scores: Mapping[str, float],
                    *, k: int, seed: int = 2026) -> list[str]:
    positive_integer(k, "k")
    if len(set(candidates)) != len(candidates) or source in candidates:
        raise ValueError("Candidates must be unique and exclude the source")
    if set(scores) != set(candidates):
        raise ValueError("Scores must cover exactly the shared candidate set")
    if any(isinstance(score, bool) or not math.isfinite(score) for score in scores.values()):
        raise ValueError("Scores must be finite")
    return sorted(candidates, key=lambda target: (
        -scores[target], digest([seed, source, target]), target
    ))[:k]
