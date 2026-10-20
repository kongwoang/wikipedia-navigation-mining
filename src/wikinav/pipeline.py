"""An end-to-end synthetic smoke run with predictions frozen before test labels."""

from collections import Counter, defaultdict
from datetime import datetime, timezone
from itertools import chain
import json
from pathlib import Path
import platform
import time

from .config import load_config
from .data import build_training, normalize_title, read_clickstream, verified_local_input
from .evaluation import aggregate_results, evaluate_source
from .graph import HyperlinkGraph, sample_sources
from .models import (
    BackoffMarkov, ConvergenceError, GlobalPopularity, InDegree,
    LocalMarkov, PPR, ScoreHybrid, UniformHyperlink,
)
from .ranking import rank_candidates
from .utils import digest, file_digest, write_json


def source_code_fingerprint() -> str:
    package = Path(__file__).parent
    return digest({p.name: file_digest(p) for p in sorted(package.glob("*.py"))})


def run_toy(config_path: Path, fixture_dir: Path, output: Path) -> dict:
    """Run reference models only on the explicit synthetic fixture.

    Deliberately not a general real-data runner: historical canonicalization and
    sparse/resource gates are not yet implemented.
    """
    started = time.perf_counter()
    protocol, config = load_config(config_path)
    graph_path = fixture_dir / "graph.json"
    description = json.loads(graph_path.read_text(encoding="utf-8"))
    if description.get("data_kind") != "synthetic":
        raise ValueError("toy-run accepts only explicitly synthetic fixtures")
    graph = HyperlinkGraph(tuple(description["nodes"]), tuple(map(tuple, description["edges"])),
                           description["snapshot"], "synthetic_hyperlink", file_digest(graph_path))
    graph.validate_protocol(protocol)
    mapping = {normalize_title(node): node for node in graph.nodes}
    train_inputs = [
        verified_local_input(fixture_dir / f"{month}.tsv", month, "train")
        for month in protocol.train_months
    ]
    records = chain.from_iterable(read_clickstream(fixture_dir / f"{month}.tsv", month)
                                  for month in protocol.train_months)
    train = build_training(records, protocol, mapping)
    queries = sample_sources(graph, len(graph.nodes), protocol.seed)
    knobs = config["models"]
    ppr_args = {
        "damping": knobs["damping"], "tolerance": knobs["tolerance"],
        "max_iterations": knobs["max_iterations"],
    }
    models = [
        GlobalPopularity(), LocalMarkov(),
        BackoffMarkov(knobs["markov_mu"], knobs["markov_eta"]),
        UniformHyperlink(), InDegree(),
        PPR(**ppr_args), PPR("click", **ppr_args), PPR("click_on_hyperlink", **ppr_args),
        ScoreHybrid(knobs["hybrid_click_weight"], mu=knobs["markov_mu"],
                    eta=knobs["markov_eta"], **ppr_args),
    ]
    for model in models:
        model.fit(train, graph)
    frozen = {
        "data_kind": "synthetic", "benchmark_result": False,
        "protocol": protocol.as_dict(), "protocol_hash": protocol.fingerprint,
        "config_sha256": file_digest(config_path), "code_sha256": source_code_fingerprint(),
        "graph_hash": graph.fingerprint, "train_hash": train.fingerprint,
        "train_inputs": train_inputs, "query_ids": queries,
        "query_selection": "graph_only_hash_order_all_nodes",
        "candidate_hash": graph.candidate_fingerprint(queries),
        "tie_seed": protocol.seed,
        "metrics": {"recall_ks": [5, 10, 20], "rank_k": 10, "gain": "log2_1p"},
        "models": {model.name: {"parameters": model.parameters, "hash": model.fingerprint}
                   for model in models},
        "tuning": "none; fixed synthetic correctness configuration",
    }
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / "freeze.json", frozen)
    predictions = {}
    for model in models:
        source_predictions = {}
        for source in queries:
            candidates = graph.candidates(source)
            status, failure = "ok", None
            try:
                scores = model.score(source, candidates)
            except ConvergenceError as exc:
                scores = UniformHyperlink().fit(train).score(source, candidates)
                status, failure = "fallback_uniform_nonconvergence", str(exc)
            ranking = rank_candidates(source, candidates, scores, k=20, seed=protocol.seed)
            source_predictions[source] = {
                "ranked": ranking, "scores": scores, "status": status, "failure": failure,
            }
        predictions[model.name] = source_predictions
    write_json(output / "predictions.json", predictions)

    # First test-file access occurs here, AFTER frozen model inputs and predictions.
    labels: dict[str, Counter] = defaultdict(Counter)
    seen = set()
    label_ledger = Counter()
    test_path = fixture_dir / f"{protocol.test_month}.tsv"
    for record in read_clickstream(test_path, protocol.test_month):
        if record.raw_key in seen:
            raise ValueError("Duplicate raw held-out row")
        seen.add(record.raw_key)
        source, target = normalize_title(record.prev), normalize_title(record.curr)
        if record.kind != "link":
            label_ledger["non_link_rows"] += 1
        elif source == target:
            label_ledger["self_loop_rows"] += 1
        elif source not in graph.nodes:
            label_ledger["outside_universe_source_rows"] += 1
            label_ledger["outside_universe_source_mass"] += record.count
        else:
            # Unmapped target remains a positive evaluator key, never a model node.
            labels[source][target] += record.count
            label_ledger["kept_rows"] += 1
            label_ledger["kept_mass"] += record.count
            if target not in graph.nodes:
                label_ledger["outside_universe_target_mass"] += record.count
    source_results = {}
    summaries = {}
    for model in models:
        results = [
            evaluate_source(source, graph.candidates(source),
                            predictions[model.name][source]["ranked"], labels.get(source, {}))
            for source in queries
        ]
        source_results[model.name] = [result.as_dict() for result in results]
        summaries[model.name] = aggregate_results(results)
        summaries[model.name]["fallback_queries"] = sum(
            row["status"] != "ok" for row in predictions[model.name].values()
        )
    if graph.fingerprint != frozen["graph_hash"] or train.fingerprint != frozen["train_hash"]:
        raise RuntimeError("Training/graph artifacts changed during evaluation")
    if graph.candidate_fingerprint(queries) != frozen["candidate_hash"]:
        raise RuntimeError("Candidate set changed during evaluation")
    write_json(output / "source_metrics.json", source_results)
    write_json(output / "metrics.json", {
        "data_kind": "synthetic", "benchmark_result": False, "models": summaries
    })
    write_json(output / "coverage.json", {
        "training": {key: dict(value) for key, value in train.ledger.items()},
        "held_out": dict(label_ledger),
        "query_scope": "all synthetic graph nodes; not Wikipedia population",
    })
    diagnostics = {}
    for model in models:
        if isinstance(model, PPR):
            diagnostics[model.name] = model.diagnostics
        elif isinstance(model, ScoreHybrid):
            diagnostics[model.name] = model.topology.diagnostics
    write_json(output / "ppr_diagnostics.json", diagnostics)
    completion = {
        "status": "complete", "data_kind": "synthetic", "benchmark_result": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "platform": platform.platform(),
        "elapsed_seconds": time.perf_counter() - started,
        "test_input": verified_local_input(test_path, protocol.test_month, "test"),
        "outputs": {p.name: file_digest(p) for p in sorted(output.glob("*.json"))},
        "models": len(models), "queries": len(queries),
    }
    write_json(output / "completion.json", completion)
    return completion
