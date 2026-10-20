"""Versioned temporal protocol, validated without reading held-out labels."""

import calendar
from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
import tomllib

from .utils import digest


def validate_month(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError(f"Invalid month: {value!r}")
    date.fromisoformat(value + "-01")
    return value


@dataclass(frozen=True)
class Protocol:
    edition: str
    graph_snapshot: str
    mapping_snapshot: str
    train_months: tuple[str, ...]
    validation_month: str
    test_month: str
    seed: int = 2026

    def __post_init__(self) -> None:
        object.__setattr__(self, "train_months", tuple(self.train_months))
        if not self.edition or not self.train_months:
            raise ValueError("Edition and training months are required")
        months = (*self.train_months, self.validation_month, self.test_month)
        for month in months:
            validate_month(month)
        if len(set(months)) != len(months):
            raise ValueError("Temporal partitions must not overlap or repeat months")
        if tuple(sorted(self.train_months)) != self.train_months:
            raise ValueError("Training months must be chronological")
        if not max(self.train_months) < self.validation_month < self.test_month:
            raise ValueError("Require train < validation < test")
        for snapshot in (self.graph_snapshot, self.mapping_snapshot):
            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", snapshot):
                raise ValueError("Snapshot must be ISO YYYY-MM-DD")
            if date.fromisoformat(snapshot) > self.training_cutoff:
                raise ValueError("Future graph/redirect mapping is forbidden")
        if type(self.seed) is not int:
            raise ValueError("Seed must be an integer")

    @property
    def training_cutoff(self) -> date:
        year, month = map(int, self.train_months[-1].split("-"))
        return date(year, month, calendar.monthrange(year, month)[1])

    def as_dict(self) -> dict:
        return {
            "edition": self.edition, "graph_snapshot": self.graph_snapshot,
            "mapping_snapshot": self.mapping_snapshot,
            "train_months": list(self.train_months),
            "validation_month": self.validation_month, "test_month": self.test_month,
            "seed": self.seed,
        }

    @property
    def fingerprint(self) -> str:
        return digest(self.as_dict())


def load_config(path: Path) -> tuple[Protocol, dict]:
    with path.open("rb") as stream:
        config = tomllib.load(stream)
    expected = {
        "protocol_version": 1,
        "task": "source_conditioned_next_article",
        "candidate_policy": "frozen_outgoing_hyperlinks",
        "selection_metric": "macro_ndcg_all@10",
        "gain": "log2_1p",
        "tie_policy": "sha256_seed_source_target",
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise ValueError(f"Unsupported {key}: {config.get(key)!r}")
    protocol = Protocol(**{key: config[key] for key in (
        "edition", "graph_snapshot", "mapping_snapshot", "train_months",
        "validation_month", "test_month", "seed"
    )})
    return protocol, config
