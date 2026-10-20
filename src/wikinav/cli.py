"""Offline development entry points; real-data training remains gated."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys

from .config import load_config
from .data import audit_clickstream
from .pipeline import run_toy
from .utils import digest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wikinav")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Inspect Python and optional packages; no network access")
    validate = commands.add_parser("validate-config", help="Validate temporal/task contract")
    validate.add_argument("--config", type=Path, default=Path("configs/eswiki_2018.toml"))
    audit = commands.add_parser("audit-clickstream", help="Audit a bounded local TSV(.gz) prefix")
    audit.add_argument("path", type=Path)
    audit.add_argument("--month", required=True)
    audit.add_argument("--max-rows", type=int, default=10000)
    toy = commands.add_parser("toy-run", help="Synthetic end-to-end smoke run, NOT a benchmark")
    toy.add_argument("--config", type=Path, default=Path("configs/eswiki_2018.toml"))
    toy.add_argument("--fixtures", type=Path, default=Path("tests/fixtures/toy"))
    toy.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            result = {
                "python": platform.python_version(), "platform": platform.platform(),
                "cpu_count_visible_to_python": os.cpu_count(),
                "core_runtime": "Python standard library; no third-party runtime dependencies",
                "optional_modules": {name: importlib.util.find_spec(name) is not None
                                     for name in ("numpy", "scipy", "polars", "pytest", "gensim")},
                "ram_bytes": None, "ram_status": "not measured",
            }
        elif args.command == "validate-config":
            protocol, config = load_config(args.config)
            result = {"protocol": protocol.as_dict(), "protocol_hash": protocol.fingerprint,
                      "config_hash": digest(config), "validation": "passed",
                      "dataset_gate": config.get("data_gate", "pending")}
        elif args.command == "audit-clickstream":
            result = audit_clickstream(args.path, args.month, max_rows=args.max_rows)
        else:
            result = run_toy(args.config, args.fixtures, args.output)
    except (ValueError, TypeError, KeyError, OSError, EOFError, RuntimeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False))
    return 0
