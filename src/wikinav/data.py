"""Strict Clickstream parsing and bounded training aggregation.

Title normalization is NOT redirect resolution. Production joins must supply an
independently audited historical article mapping before creating TrainBundle.
"""

from collections import Counter
from dataclasses import dataclass
import gzip
from pathlib import Path
import re
from types import MappingProxyType
from typing import Iterable, Iterator, Mapping
import unicodedata

from .config import Protocol, validate_month
from .utils import digest, file_digest, positive_integer

MAX_INT64 = 2**63 - 1
TYPES = frozenset({"link", "external", "other"})
PSEUDO_NODES = frozenset({
    "other-internal", "other-search", "other-external", "other-empty", "other-other"
})


def normalize_title(title: str) -> str:
    if not isinstance(title, str) or not title or any(c in title for c in "\t\r\n"):
        raise ValueError("Article title must be a nonempty single field")
    # Preserve case, accents, literal percent signs and fragments.
    normalized = unicodedata.normalize("NFC", title.replace("_", " "))
    if not normalized.strip():
        raise ValueError("Empty normalized title")
    return normalized


@dataclass(frozen=True)
class ClickRecord:
    month: str
    prev: str
    curr: str
    kind: str
    count: int

    def __post_init__(self) -> None:
        validate_month(self.month)
        normalize_title(self.prev)
        normalize_title(self.curr)
        if self.kind not in TYPES:
            raise ValueError(f"Unknown transition type: {self.kind!r}")
        positive_integer(self.count, "count")
        if self.count > MAX_INT64:
            raise ValueError("Count exceeds int64")

    @property
    def raw_key(self) -> tuple[str, str, str, str]:
        return self.month, self.prev, self.curr, self.kind


def read_clickstream(path: Path, month: str, *, minimum_count: int = 11,
                     max_line_bytes: int = 65536) -> Iterator[ClickRecord]:
    """Read headerless UTF-8 TSV(.gz), failing with line number on bad input."""
    validate_month(month)
    positive_integer(minimum_count, "minimum_count")
    positive_integer(max_line_bytes, "max_line_bytes")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rb") as stream:
        line_no = 0
        while raw := stream.readline(max_line_bytes + 1):
            line_no += 1
            try:
                if len(raw) > max_line_bytes:
                    raise ValueError("Line exceeds byte budget")
                fields = raw.decode("utf-8").rstrip("\r\n").split("\t")
                if len(fields) != 4 or not re.fullmatch(r"[0-9]+", fields[3]):
                    raise ValueError("Expected prev<TAB>curr<TAB>type<TAB>integer count")
                record = ClickRecord(month, fields[0], fields[1], fields[2], int(fields[3]))
                if record.count < minimum_count:
                    raise ValueError(f"Published count below configured minimum {minimum_count}")
                yield record
            except (ValueError, UnicodeError) as exc:
                raise ValueError(f"{path.name}:{line_no}: {exc}") from exc


def audit_clickstream(path: Path, month: str, *, max_rows: int = 10000) -> dict:
    """Audit a PREFIX, not a representative/random sample of the dataset."""
    positive_integer(max_rows, "max_rows")
    if max_rows > 100000:
        raise ValueError("Reference audit capped at 100000 rows")
    seen: set[tuple] = set()
    rows_by_type: Counter = Counter()
    mass_by_type: Counter = Counter()
    count_min = None
    count_max = None
    complete = True
    records = read_clickstream(path, month)
    try:
        for i, record in enumerate(records):
            if i == max_rows:
                complete = False
                break
            if record.raw_key in seen:
                raise ValueError(f"Duplicate raw Clickstream key: {record.raw_key}")
            seen.add(record.raw_key)
            rows_by_type[record.kind] += 1
            mass_by_type[record.kind] += record.count
            count_min = record.count if count_min is None else min(count_min, record.count)
            count_max = record.count if count_max is None else max(count_max, record.count)
    finally:
        records.close()
    # Full hashing is opt-in at artifact ingestion, not a hidden full scan here.
    return {
        "scope": "complete_file" if complete else "prefix_only",
        "representative_sample": False,
        "month": month, "filename": path.name, "file_bytes": path.stat().st_size,
        "rows": sum(rows_by_type.values()), "rows_by_type": dict(rows_by_type),
        "mass_by_type": dict(mass_by_type), "minimum_count": count_min,
        "maximum_count": count_max, "raw_duplicate_check": "passed_in_audited_rows",
        "full_file_checksum": None, "file_read_to_eof": complete,
        "gzip_integrity_checked_to_eof": complete if path.suffix == ".gz" else None,
    }


@dataclass(frozen=True)
class TrainBundle:
    """Canonical IDs and training-only observed counts; no evaluation labels."""

    months: tuple[str, ...]
    protocol_hash: str
    counts: Mapping[tuple[str, str], int]
    ledger: Mapping[str, Mapping[str, int]]

    def __post_init__(self) -> None:
        clean = dict(self.counts)
        for (source, target), count in clean.items():
            if (not isinstance(source, str) or not isinstance(target, str)
                    or not source or not target or source == target):
                raise ValueError("Training pairs require distinct, nonempty IDs")
            positive_integer(count, "count")
            if count > MAX_INT64:
                raise ValueError("Aggregated count exceeds int64")
        object.__setattr__(self, "months", tuple(self.months))
        object.__setattr__(self, "counts", MappingProxyType(clean))
        object.__setattr__(self, "ledger", MappingProxyType({
            key: MappingProxyType(dict(value)) for key, value in self.ledger.items()
        }))

    @property
    def fingerprint(self) -> str:
        return digest({
            "months": self.months, "protocol_hash": self.protocol_hash,
            "counts": [[s, t, c] for (s, t), c in sorted(self.counts.items())],
        })


def build_training(records: Iterable[ClickRecord], protocol: Protocol,
                   title_to_id: Mapping[str, str], *, max_rows: int = 100000) -> TrainBundle:
    """Mapping keys must be normalized titles from the historical inventory."""
    positive_integer(max_rows, "max_rows")
    if max_rows > 100000:
        raise ValueError("Reference aggregation capped at 100000 records")
    for title, node_id in title_to_id.items():
        if normalize_title(title) != title or not isinstance(node_id, str) or not node_id:
            raise ValueError("Historical mapping requires normalized titles and nonempty string IDs")
    seen: set[tuple] = set()
    counts: Counter = Counter()
    row_ledger: Counter = Counter()
    mass_ledger: Counter = Counter()
    for i, record in enumerate(records):
        if i >= max_rows:
            raise ValueError("Training row budget exceeded; no partial artifact returned")
        if record.month not in protocol.train_months:
            raise ValueError(f"Held-out/non-training month in fit input: {record.month}")
        if record.raw_key in seen:
            raise ValueError(f"Duplicate raw record: {record.raw_key}")
        seen.add(record.raw_key)
        source_title, target_title = normalize_title(record.prev), normalize_title(record.curr)
        if record.kind != "link":
            reason = "non_link"
        elif source_title in PSEUDO_NODES or target_title in PSEUDO_NODES:
            reason = "pseudo_node"
        elif source_title not in title_to_id or target_title not in title_to_id:
            reason = "unmapped"
        else:
            source, target = title_to_id[source_title], title_to_id[target_title]
            if source == target:
                reason = "self_loop"
            else:
                reason = "kept"
                counts[source, target] += record.count
                if counts[source, target] > MAX_INT64:
                    raise ValueError("Aggregated count exceeds int64")
        row_ledger[reason] += 1
        mass_ledger[reason] += record.count
    return TrainBundle(protocol.train_months, protocol.fingerprint, counts,
                       {"rows": row_ledger, "mass": mass_ledger})


def verified_local_input(path: Path, month: str, role: str) -> dict:
    """Full hash only when explicitly registering a local input."""
    validate_month(month)
    if role not in {"train", "validation", "test"}:
        raise ValueError("Invalid input role")
    return {"filename": path.name, "month": month, "role": role,
            "bytes": path.stat().st_size, "sha256": file_digest(path)}
