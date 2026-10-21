"""Resolve historical redirect state from events, independent of click labels."""

import csv
from datetime import datetime, timezone
import gzip
from pathlib import Path

from .data import normalize_title


def latest_redirects(path: Path, cutoff: str):
    boundary = datetime.fromisoformat(cutoff).replace(tzinfo=timezone.utc)
    states = {}; audit = {"rows": 0, "future_events_excluded": 0, "conflicting_states": 0,
                          "whitespace_normalized_targets": 0, "empty_targets_quarantined": 0}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        expected = ["page_id", "page_title", "revision_id", "revision_parent_id",
                    "revision_timestamp", "revision_minor", "redirect.target", "redirect.tosection"]
        if next(reader) != expected:
            raise ValueError("Unexpected redirect event header")
        for row in reader:
            audit["rows"] += 1
            if len(row) != 8:
                raise ValueError("Malformed redirect event")
            timestamp = datetime.fromisoformat(row[4].replace("Z", "+00:00"))
            if timestamp.tzinfo is None:
                raise ValueError("Redirect timestamp requires timezone")
            if timestamp > boundary:
                audit["future_events_excluded"] += 1
                continue
            node, revision = int(row[0]), int(row[2])
            # Wikitext link targets may contain layout whitespace. This rule is
            # specific to redirect target syntax, never applied to click titles.
            folded = " ".join(row[6].split())
            if folded != row[6]:
                audit["whitespace_normalized_targets"] += 1
            if not folded:
                target = "#INVALID"
                audit["empty_targets_quarantined"] += 1
            else:
                target = normalize_title(folded)
            key = timestamp, revision
            previous = states.get(node)
            if previous is None or key > previous[0]:
                states[node] = (key, target)
            elif key == previous[0] and previous[1] != target:
                states[node] = (key, "#AMBIGUOUS")
                audit["conflicting_states"] += 1
    audit["latest_states"] = len(states)
    return {node: value[1] for node, value in states.items()}, audit


def resolve_targets(targets: dict[int, int | None]):
    """targets contains ONLY redirect nodes; missing key means ordinary article.

    None means dangling/ambiguous; cycles and chains into cycles are quarantined.
    """
    resolved = {}; status = {}
    for start in sorted(targets):
        trail = []; visited = set(); current = start
        while current is not None and current in targets and current not in resolved:
            if current in visited:
                current = None
                reason = "cycle"
                break
            visited.add(current); trail.append(current)
            current = targets[current]
        else:
            reason = "dangling" if current is None else status.get(current, "resolved")
        terminal = resolved.get(current, current) if current is not None else None
        for node in trail:
            resolved[node] = terminal; status[node] = reason
    return resolved, status
