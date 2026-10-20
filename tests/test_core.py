import gzip
import json
import math
from pathlib import Path
import random
import shutil
import tempfile
import unittest
from unittest.mock import patch

from wikinav.cli import main
from wikinav.config import Protocol, load_config
from wikinav.data import (
    ClickRecord, MAX_INT64, audit_clickstream, build_training,
    normalize_title, read_clickstream,
)
from wikinav.evaluation import aggregate_results, evaluate_source, paired_bootstrap
from wikinav.graph import HyperlinkGraph, sample_sources, transition_rows
from wikinav.models import (
    BackoffMarkov, ConvergenceError, GlobalPopularity, InDegree, LocalMarkov,
    PPR, ScoreHybrid, UniformHyperlink, personalized_pagerank,
)
from wikinav.pipeline import run_toy
from wikinav.ranking import rank_candidates
from wikinav.utils import digest, file_digest

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/toy"
CONFIG = ROOT / "configs/eswiki_2018.toml"


def protocol(**changes):
    values = dict(edition="eswiki", graph_snapshot="2018-03-01",
                  mapping_snapshot="2018-03-01",
                  train_months=("2018-01", "2018-02", "2018-03"),
                  validation_month="2018-04", test_month="2018-05", seed=2026)
    values.update(changes)
    return Protocol(**values)


def graph():
    return HyperlinkGraph(
        ("A", "B", "C", "D", "E", "F"),
        (("A", "B"), ("A", "C"), ("A", "E"), ("B", "A"), ("B", "D"),
         ("C", "A"), ("E", "B")), "2018-03-01", "synthetic_hyperlink", "a" * 64
    )


def train():
    return build_training([
        ClickRecord("2018-01", "A", "B", "link", 36),
        ClickRecord("2018-01", "A", "C", "link", 12),
        ClickRecord("2018-01", "B", "A", "link", 12),
        ClickRecord("2018-01", "B", "E", "link", 11),
    ], protocol(), {n: n for n in graph().nodes})


class ProtocolTests(unittest.TestCase):
    def test_config_and_cutoff(self):
        p, config = load_config(CONFIG)
        self.assertEqual(str(p.training_cutoff), "2018-03-31")
        self.assertEqual(config["data_gate"], "pending")
        self.assertEqual(p.fingerprint, protocol().fingerprint)

    def test_temporal_rejections(self):
        for changes in (
            {"test_month": "2018-04"},
            {"validation_month": "2018-02"},
            {"train_months": ("2018-03", "2018-01")},
            {"train_months": ("2018-01", "2018-01")},
            {"test_month": "2018-13"},
            {"test_month": "2018-5"},
            {"graph_snapshot": "2018-04-01"},
            {"mapping_snapshot": "2026-01-01"},
            {"train_months": ()},
            {"seed": True},
        ):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                protocol(**changes)

    def test_immutable_months(self):
        months = ["2018-01", "2018-02", "2018-03"]
        p = protocol(train_months=months)
        months.append("2018-05")
        self.assertEqual(p.train_months, ("2018-01", "2018-02", "2018-03"))

    def test_unsupported_task_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.toml"
            path.write_text(CONFIG.read_text().replace(
                'task = "source_conditioned_next_article"', 'task = "personalized_user"'
            ))
            with self.assertRaises(ValueError):
                load_config(path)


class DataTests(unittest.TestCase):
    def test_normalization_preserves_case_accents_and_literals(self):
        self.assertEqual(normalize_title("Café_con_Leche"), "Café con Leche")
        self.assertEqual(normalize_title("Cafe\u0301"), "Café")
        self.assertEqual(normalize_title("A%20B"), "A%20B")
        self.assertEqual(normalize_title("A#B"), "A#B")
        self.assertNotEqual(normalize_title("ABC"), normalize_title("abc"))

    def test_invalid_titles(self):
        for title in ("", "\t", "A\nB", "___"):
            with self.subTest(title=title), self.assertRaises(ValueError):
                normalize_title(title)

    def test_read_plain_and_gzip(self):
        data = "A\tB\tlink\t11\nC\tD\tother\t12\n"
        with tempfile.TemporaryDirectory() as folder:
            plain, compressed = Path(folder) / "a.tsv", Path(folder) / "a.tsv.gz"
            plain.write_text(data)
            with gzip.open(compressed, "wt") as f:
                f.write(data)
            self.assertEqual(list(read_clickstream(plain, "2018-01")),
                             list(read_clickstream(compressed, "2018-01")))

    def test_bad_schema_threshold_types_and_counts(self):
        bad_lines = [
            "prev\tcurr\ttype\tn\n", "A\tB\tlink\t10\n", "A\tB\tlink\t1.5\n",
            "A\tB\twrong\t11\n", "A\tB\tlink\t-11\n", "A\tB\tlink\t0\n",
            "A\tB\tlink\t11\textra\n", f"A\tB\tlink\t{MAX_INT64+1}\n",
            "\n", "A\tB\tlink\t+11\n",
        ]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.tsv"
            for line in bad_lines:
                with self.subTest(line=line):
                    path.write_text(line)
                    with self.assertRaisesRegex(ValueError, "bad.tsv:1:"):
                        list(read_clickstream(path, "2018-01"))

    def test_line_budget_and_utf8(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "bad.tsv"
            path.write_text("A" * 100 + "\tB\tlink\t11\n")
            with self.assertRaisesRegex(ValueError, "budget"):
                list(read_clickstream(path, "2018-01", max_line_bytes=20))
            path.write_bytes(b"\xff\tB\tlink\t11\n")
            with self.assertRaises(ValueError):
                list(read_clickstream(path, "2018-01"))

    def test_raw_duplicate_is_not_aggregated(self):
        record = ClickRecord("2018-01", "A", "B", "link", 11)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            build_training([record, record], protocol(), {"A": "A", "B": "B"})

    def test_canonical_alias_collisions_and_months_sum(self):
        records = [
            ClickRecord("2018-01", "A_alias", "B", "link", 11),
            ClickRecord("2018-01", "A", "B", "link", 12),
            ClickRecord("2018-02", "A", "B", "link", 13),
        ]
        fitted = build_training(records, protocol(), {"A alias": "A", "A": "A", "B": "B"})
        self.assertEqual(fitted.counts[("A", "B")], 36)
        with self.assertRaises(TypeError):
            fitted.counts[("A", "B")] = 100

    def test_future_rows_rejected_even_if_filtered(self):
        for kind in ("link", "external"):
            with self.assertRaisesRegex(ValueError, "Held-out"):
                build_training([ClickRecord("2018-05", "A", "B", kind, 11)],
                               protocol(), {"A": "A", "B": "B"})

    def test_coverage_ledger_reconciles(self):
        records = list(read_clickstream(FIXTURES / "2018-01.tsv", "2018-01"))
        fitted = build_training(records, protocol(), {n: n for n in graph().nodes})
        self.assertEqual(sum(fitted.ledger["rows"].values()), 8)
        self.assertEqual(sum(fitted.ledger["mass"].values()), sum(r.count for r in records))
        self.assertEqual(fitted.ledger["mass"]["kept"], sum(fitted.counts.values()))
        self.assertEqual(fitted.ledger["rows"]["non_link"], 1)
        self.assertEqual(fitted.ledger["rows"]["unmapped"], 1)
        self.assertEqual(fitted.ledger["rows"]["self_loop"], 1)

    def test_prefix_audit_scope(self):
        result = audit_clickstream(FIXTURES / "2018-01.tsv", "2018-01", max_rows=2)
        self.assertEqual(result["scope"], "prefix_only")
        self.assertFalse(result["representative_sample"])
        self.assertEqual(result["rows"], 2)
        self.assertIsNone(result["full_file_checksum"])
        result = audit_clickstream(FIXTURES / "2018-01.tsv", "2018-01")
        self.assertEqual(result["scope"], "complete_file")
        self.assertTrue(result["file_read_to_eof"])
        self.assertIsNone(result["gzip_integrity_checked_to_eof"])

    def test_gzip_audit_integrity_and_truncation(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "clicks.tsv.gz"
            with gzip.open(path, "wt") as stream:
                stream.write("A\tB\tlink\t11\nB\tC\tlink\t12\n")
            self.assertTrue(audit_clickstream(path, "2018-01")["gzip_integrity_checked_to_eof"])
            prefix = audit_clickstream(path, "2018-01", max_rows=1)
            self.assertFalse(prefix["gzip_integrity_checked_to_eof"])
            path.write_bytes(path.read_bytes()[:-4])
            with self.assertRaises(EOFError):
                audit_clickstream(path, "2018-01")

    def test_invalid_historical_mapping_rejected(self):
        row = ClickRecord("2018-01", "A", "B", "link", 11)
        for mapping in ({"A": 1, "B": "B"}, {"A": "", "B": "B"},
                        {"A_alias": "A", "B": "B"}):
            with self.subTest(mapping=mapping), self.assertRaises(ValueError):
                build_training([row], protocol(), mapping)

    def test_prefix_duplicate_detection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "duplicate.tsv"
            path.write_text("A\tB\tlink\t11\nA\tB\tlink\t11\n")
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                audit_clickstream(path, "2018-01")

    def test_count_overflow_after_sum(self):
        records = [ClickRecord(month, "A", "B", "link", MAX_INT64)
                   for month in ("2018-01", "2018-02")]
        with self.assertRaisesRegex(ValueError, "int64"):
            build_training(records, protocol(), {"A": "A", "B": "B"})

    def test_reference_budget(self):
        records = [ClickRecord("2018-01", "A", target, "link", 11) for target in ("B", "C")]
        with self.assertRaisesRegex(ValueError, "budget"):
            build_training(records, protocol(), {"A": "A", "B": "B", "C": "C"}, max_rows=1)

    def test_row_order_invariance(self):
        records = list(read_clickstream(FIXTURES / "2018-01.tsv", "2018-01"))
        mapping = {n: n for n in graph().nodes}
        self.assertEqual(build_training(records, protocol(), mapping).fingerprint,
                         build_training(reversed(records), protocol(), mapping).fingerprint)


class GraphAndRankingTests(unittest.TestCase):
    def test_directed_candidates_and_dangling(self):
        g = graph()
        self.assertIn("C", g.candidates("A"))
        self.assertNotIn("B", g.candidates("C"))
        self.assertEqual(g.candidates("D"), ())
        self.assertEqual(g.candidates("F"), ())
        with self.assertRaises(ValueError):
            g.candidates("unknown")

    def test_provenance_and_future_snapshot_rejected(self):
        with self.assertRaisesRegex(ValueError, "clickstream"):
            HyperlinkGraph(("A", "B"), (("A", "B"),), "2018-03-01", "clickstream", "a"*64)
        with self.assertRaisesRegex(ValueError, "snapshot"):
            graph().validate_protocol(protocol(graph_snapshot="2018-02-01"))

    def test_selfloop_unknown_endpoint_and_duplicate_nodes(self):
        for nodes, edges in (
            (("A",), (("A", "A"),)),
            (("A",), (("A", "B"),)),
            (("A", "A"), ()),
        ):
            with self.assertRaises(ValueError):
                HyperlinkGraph(nodes, edges, "2018-03-01", "synthetic_hyperlink", "a"*64)

    def test_row_normalization_and_no_reverse_edges(self):
        rows = transition_rows(("A", "B", "C"), {("A", "B"): 3, ("A", "C"): 1})
        self.assertEqual(rows["A"], {"B": 0.75, "C": 0.25})
        self.assertEqual(rows["B"], {})

    def test_invalid_weights(self):
        for value in (0, -1, math.nan, math.inf, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                transition_rows(("A", "B"), {("A", "B"): value})

    def test_queries_graph_only_and_stable(self):
        a = sample_sources(graph(), 3, 2026)
        self.assertEqual(a, sample_sources(graph(), 3, 2026))
        self.assertEqual(len(set(a)), 3)
        self.assertEqual(graph().candidate_fingerprint(a),
                         graph().candidate_fingerprint(reversed(a)))

    def test_tie_order_and_restrictions(self):
        first = rank_candidates("A", ("B", "C", "D"), {"B": 1, "C": 1, "D": 2}, k=20)
        second = rank_candidates("A", ("D", "C", "B"), {"D": 2, "C": 1, "B": 1}, k=20)
        self.assertEqual(first, second)
        self.assertEqual(first[0], "D")
        with self.assertRaises(ValueError):
            rank_candidates("A", ("B",), {"B": 1, "outside": 100}, k=10)
        with self.assertRaises(ValueError):
            rank_candidates("A", ("B", "B"), {"B": 1}, k=10)
        with self.assertRaises(ValueError):
            rank_candidates("A", ("B",), {"B": math.nan}, k=10)
        self.assertEqual(rank_candidates("A", (), {}, k=10), [])

    def test_graph_dedup_and_fingerprint_stability(self):
        g = graph()
        other = HyperlinkGraph(tuple(reversed(g.nodes)), (*reversed(g.edges), g.edges[0]),
                               g.snapshot, g.source_kind, g.source_sha256)
        self.assertEqual(g.fingerprint, other.fingerprint)


class MetricTests(unittest.TestCase):
    def fixture(self):
        return evaluate_source("A", ("B", "C", "E"), ["C", "B", "E"], {"B": 3, "D": 1},
                               recall_ks=(2,), rank_k=2)

    def test_hand_computed_full_denominator(self):
        result = self.fixture()
        self.assertEqual(result.all_metrics["recall@2"], 0.5)
        self.assertEqual(result.all_metrics["mrr@2"], 0.5)
        self.assertEqual(result.all_metrics["mass_recall@2"], 0.75)
        self.assertEqual(result.all_metrics["expected_rr@2"], 0.375)
        expected = (2 / math.log2(3)) / (2 + 1 / math.log2(3))
        self.assertAlmostEqual(result.all_metrics["ndcg@2"], expected)
        self.assertEqual(result.label_pairs, 2)
        self.assertEqual(result.eligible_pairs, 1)

    def test_conditional_denominator_and_rank_not_recompressed(self):
        result = self.fixture()
        self.assertEqual(result.conditional_metrics["recall@2"], 1)
        self.assertAlmostEqual(result.conditional_metrics["ndcg@2"], 1 / math.log2(3))
        self.assertEqual(result.conditional_metrics["mrr@2"], 0.5)
        self.assertEqual(result.conditional_metrics["expected_rr@2"], 0.5)

    def test_empty_labels_are_na(self):
        result = evaluate_source("A", ("B",), ["B"], {})
        self.assertEqual(result.status, "no_observable_labels")
        self.assertTrue(all(value is None for value in result.all_metrics.values()))

    def test_empty_candidates_full_zero_conditional_na(self):
        result = evaluate_source("A", (), [], {"D": 3})
        self.assertTrue(all(value == 0 for value in result.all_metrics.values()))
        self.assertTrue(all(value is None for value in result.conditional_metrics.values()))

    def test_outside_candidate_positive_not_dropped(self):
        result = evaluate_source("A", ("B",), ["B"], {"D": 3})
        self.assertEqual(result.status, "no_eligible_labels")
        self.assertEqual(result.all_metrics["recall@10"], 0)
        self.assertEqual(result.label_mass, 3)

    def test_invalid_predictions_and_labels_rejected(self):
        for candidates, ranked, labels in (
            (("B",), ["C"], {"B": 1}),
            (("B",), ["B", "B"], {"B": 1}),
            (("A",), ["A"], {"B": 1}),
            (("B",), ["B"], {"B": 0}),
            (("B",), ["B"], {"B": True}),
            (("B",), ["B"], {"A": 1}),
        ):
            with self.assertRaises(ValueError):
                evaluate_source("A", candidates, ranked, labels)

    def test_macro_and_traffic_weighting(self):
        first = evaluate_source("A", ("B",), ["B"], {"B": 1})
        second = evaluate_source("C", ("D",), ["D"], {"E": 9})
        empty = evaluate_source("F", (), [], {})
        result = aggregate_results([first, second, empty])
        metric = result["all"]["mass_recall@10"]
        self.assertEqual(metric["macro"], 0.5)
        self.assertEqual(metric["traffic_weighted"], 0.1)
        self.assertEqual(metric["sources"], 2)
        self.assertEqual(result["q_conditional"], 1)
        self.assertEqual(result["mass_candidate_coverage"], 0.1)
        self.assertEqual(result["pair_candidate_coverage"], 0.5)
        self.assertEqual(result["queries"], 3)

    def test_all_unlabeled_aggregate_is_na(self):
        result = aggregate_results([evaluate_source("A", (), [], {})])
        self.assertIsNone(result["all"]["ndcg@10"]["macro"])
        self.assertIsNone(result["mass_candidate_coverage"])

    def test_duplicate_sources_rejected(self):
        result = self.fixture()
        with self.assertRaises(ValueError):
            aggregate_results([result, result])

    def test_randomized_bounds_and_perfect_ndcg(self):
        rng = random.Random(42)
        for size in range(1, 25):
            labels = {f"v{i}": rng.randint(1, 10000) for i in range(size)}
            ranked = sorted(labels, key=labels.get, reverse=True)
            result = evaluate_source("u", list(labels), ranked, labels)
            self.assertAlmostEqual(result.all_metrics["ndcg@10"], 1)
            rng.shuffle(ranked)
            shuffled = evaluate_source("u", list(labels), ranked, labels)
            self.assertTrue(all(0 <= value <= 1 + 1e-12
                                for value in shuffled.all_metrics.values()))
            self.assertLessEqual(shuffled.all_metrics["recall@5"],
                                 shuffled.all_metrics["recall@10"])

    def test_paired_bootstrap(self):
        left = {"A": 0.8, "B": 0.4}
        right = {"A": 0.6, "B": 0.2}
        result = paired_bootstrap(left, right, resamples=100)
        self.assertAlmostEqual(result["difference"], 0.2)
        self.assertAlmostEqual(result["ci95"][0], 0.2)
        self.assertEqual(result, paired_bootstrap(left, right, resamples=100))
        with self.assertRaises(ValueError):
            paired_bootstrap(left, {"A": 0.2}, resamples=100)


class ModelTests(unittest.TestCase):
    def test_fit_required(self):
        with self.assertRaises(ValueError):
            GlobalPopularity().score("A", ("B",))

    def test_baseline_counts_and_fallback(self):
        data = train()
        candidates = graph().candidates("A")
        global_model = GlobalPopularity().fit(data)
        local = LocalMarkov().fit(data)
        scores = local.score("A", candidates)
        self.assertEqual(scores["B"], 0.75)
        self.assertEqual(scores["C"], 0.25)
        self.assertEqual(scores["E"], 0)
        self.assertEqual(local.score("F", candidates), global_model.score("F", candidates))
        self.assertEqual(local.score("A", ("D",)), global_model.score("A", ("D",)))

    def test_backoff_formula_and_cold_source(self):
        model = BackoffMarkov(mu=4, eta=0).fit(train())
        scores = model.score("A", ("B", "C"))
        self.assertAlmostEqual(scores["B"], 38/52)
        self.assertAlmostEqual(scores["C"], 14/52)
        self.assertEqual(model.score("F", ("B", "C")), {"B": 0.5, "C": 0.5})
        self.assertEqual(model.score("F", ()), {})
        cold = BackoffMarkov(mu=0).fit(train()).score("F", ("B", "C"))
        self.assertAlmostEqual(sum(cold.values()), 1)
        self.assertGreater(cold["B"], cold["C"])

    def test_uniform_and_indegree(self):
        self.assertEqual(UniformHyperlink().fit(train()).score("A", ("B", "C")),
                         {"B": 0.5, "C": 0.5})
        self.assertEqual(UniformHyperlink().fit(train()).score("A", ()), {})
        degree = InDegree().fit(train(), graph()).score("A", ("B", "C", "E"))
        self.assertEqual(degree, {"B": 2, "C": 1, "E": 1})

    def test_two_cycle_analytic_ppr(self):
        rows = {"A": {"B": 1}, "B": {"A": 1}}
        for damping in (0.15, 0.5, 0.85):
            result = personalized_pagerank(rows, "A", damping=damping)
            self.assertAlmostEqual(result.scores["A"], 1/(1+damping), places=9)
            self.assertAlmostEqual(result.scores["B"], damping/(1+damping), places=9)
            self.assertLessEqual(result.residual, 1e-10)
            self.assertAlmostEqual(sum(result.scores.values()), 1)

    def test_dangling_chain_analytic_and_direction(self):
        rows = {"A": {"B": 1}, "B": {"C": 1}, "C": {}, "D": {}}
        result = personalized_pagerank(rows, "A", damping=0.5)
        self.assertAlmostEqual(result.scores["A"], 4/7, places=9)
        self.assertAlmostEqual(result.scores["B"], 2/7, places=9)
        self.assertAlmostEqual(result.scores["C"], 1/7, places=9)
        self.assertEqual(result.scores["D"], 0)
        dangling = personalized_pagerank(rows, "D")
        self.assertEqual(dangling.scores["D"], 1)
        self.assertEqual(dangling.residual, 0)

    def test_residual_matches_returned_vector(self):
        rows = {"A": {"B": 1}, "B": {"C": 1}, "C": {}}
        result = personalized_pagerank(rows, "A", damping=0.85, tolerance=1e-6)
        r = result.scores
        transformed = {"A": 0.15+0.85*r["C"], "B": 0.85*r["A"], "C": 0.85*r["B"]}
        self.assertAlmostEqual(result.residual,
                               sum(abs(transformed[n]-r[n]) for n in rows), places=14)

    def test_nonconvergence_and_bad_rows_fail(self):
        with self.assertRaises(ConvergenceError):
            personalized_pagerank({"A": {"B": 1}, "B": {"A": 1}}, "A", max_iterations=1)
        with self.assertRaises(ValueError):
            personalized_pagerank({"A": {"B": 0.7}, "B": {}}, "A")
        for damping in (0, 1, -0.1, math.nan):
            with self.assertRaises(ValueError):
                PPR(damping=damping)

    def test_support_behavior_only_vs_intersection(self):
        pure = PPR("click").fit(train(), graph())
        restricted = PPR("click_on_hyperlink").fit(train(), graph())
        self.assertIn("E", pure.rows["B"])
        self.assertNotIn("E", restricted.rows["B"])
        self.assertEqual(pure.rows["E"], {})
        self.assertEqual(PPR().fit(train(), graph()).rows["E"], {"B": 1})

    def test_hybrid_endpoints_and_normalization(self):
        data, g = train(), graph()
        local = BackoffMarkov().fit(data)
        ppr = PPR().fit(data, g)
        first = ScoreHybrid(1).fit(data, g)
        last = ScoreHybrid(0).fit(data, g)
        middle = ScoreHybrid(0.5).fit(data, g)
        for source in g.nodes:
            candidates = g.candidates(source)
            self.assertEqual(first.recommend(source, candidates),
                             local.recommend(source, candidates))
            self.assertEqual(last.recommend(source, candidates),
                             ppr.recommend(source, candidates))
            scores = middle.score(source, candidates)
            if scores:
                self.assertAlmostEqual(sum(scores.values()), 1)

    def test_cached_scores_cannot_be_mutated_by_caller(self):
        model = PPR().fit(train(), graph())
        scores = model.score("A", ("B", "C"))
        scores["B"] = -100
        self.assertGreaterEqual(model.score("A", ("B", "C"))["B"], 0)

    def test_fingerprints_include_parameters(self):
        self.assertNotEqual(BackoffMarkov(10).fit(train()).fingerprint,
                            BackoffMarkov(100).fit(train()).fingerprint)


class IntegrationTests(unittest.TestCase):
    def test_end_to_end_reproducibility_and_coverage(self):
        with tempfile.TemporaryDirectory() as folder:
            outputs = [Path(folder)/"first", Path(folder)/"second"]
            for output in outputs:
                completion = run_toy(CONFIG, FIXTURES, output)
                self.assertEqual(completion["models"], 9)
                self.assertFalse(completion["benchmark_result"])
                self.assertEqual(completion["status"], "complete")
                for name, sha in completion["outputs"].items():
                    self.assertEqual(file_digest(output/name), sha)
            for name in ("freeze.json", "predictions.json", "metrics.json",
                         "source_metrics.json", "coverage.json", "ppr_diagnostics.json"):
                self.assertEqual((outputs[0]/name).read_bytes(), (outputs[1]/name).read_bytes())
            metrics = json.loads((outputs[0]/"metrics.json").read_text())["models"]
            for model, values in metrics.items():
                with self.subTest(model=model):
                    self.assertEqual(values["queries"], 6)
                    self.assertEqual(values["q_all"], 5)
                    self.assertEqual(values["q_conditional"], 4)
                    self.assertEqual(values["label_mass"], 119)
                    self.assertEqual(values["eligible_mass"], 72)
                    self.assertEqual(values["label_pairs"], 8)
                    self.assertEqual(values["eligible_pairs"], 5)
                    self.assertEqual(values["fallback_queries"], 0)

    def test_heldout_mutation_does_not_change_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            fixtures = folder/"fixtures"
            shutil.copytree(FIXTURES, fixtures)
            run_toy(CONFIG, fixtures, folder/"before")
            (fixtures/"2018-05.tsv").write_text("A\tC\tlink\t999\nE\tB\tlink\t55\n")
            run_toy(CONFIG, fixtures, folder/"after")
            for artifact in ("freeze.json", "predictions.json"):
                self.assertEqual((folder/"before"/artifact).read_bytes(),
                                 (folder/"after"/artifact).read_bytes())
            self.assertNotEqual((folder/"before/metrics.json").read_bytes(),
                                (folder/"after/metrics.json").read_bytes())

    def test_freeze_and_predictions_exist_before_test_read(self):
        from wikinav import pipeline
        original = pipeline.read_clickstream
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/"run"

            def guarded(path, month, **kwargs):
                if month == "2018-05":
                    self.assertTrue((output/"freeze.json").is_file())
                    self.assertTrue((output/"predictions.json").is_file())
                return original(path, month, **kwargs)

            with patch.object(pipeline, "read_clickstream", side_effect=guarded):
                run_toy(CONFIG, FIXTURES, output)

    def test_output_overwrite_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/"run"
            run_toy(CONFIG, FIXTURES, output)
            original = file_digest(output/"metrics.json")
            with self.assertRaises(FileExistsError):
                run_toy(CONFIG, FIXTURES, output)
            self.assertEqual(file_digest(output/"metrics.json"), original)

    def test_real_data_rejected_by_toy_command(self):
        with tempfile.TemporaryDirectory() as folder:
            folder = Path(folder)
            fixtures = folder/"fixtures"
            shutil.copytree(FIXTURES, fixtures)
            description = json.loads((fixtures/"graph.json").read_text())
            description["data_kind"] = "real"
            (fixtures/"graph.json").write_text(json.dumps(description))
            with self.assertRaisesRegex(ValueError, "synthetic"):
                run_toy(CONFIG, fixtures, folder/"run")

    def test_cli_invalid_input_returns_failure(self):
        with patch("sys.stderr"):
            self.assertEqual(main(["audit-clickstream", "missing.tsv", "--month", "bad"]), 2)


if __name__ == "__main__":
    unittest.main()
