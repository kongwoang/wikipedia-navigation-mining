"""Portable extension verification; only Python's standard library is required."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from .evaluation import aggregate_results, evaluate_source
from .ranking import rank_candidates
from .utils import file_digest


def assert_same(actual, expected, location="root"):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or actual.keys() != expected.keys():
            raise ValueError(f"Different fields at {location}")
        for key in expected:
            assert_same(actual[key], expected[key], f"{location}/{key}")
    elif isinstance(expected, float):
        if actual is None or not math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(f"Metric mismatch at {location}: {actual} != {expected}")
    elif actual != expected:
        raise ValueError(f"Value mismatch at {location}")


def verify_timeline(events, freezes):
    """Check the recorded prediction-before-read contract for each rolling window."""
    for month, freeze in freezes.items():
        frozen = [e for e in events if e['event'] == 'predictions_frozen' and e.get('test') == month]
        reads = [e for e in events if e['event'] == 'test_read_start' and e.get('test') == month]
        if len(frozen) != 1 or not reads:
            raise ValueError(f"Missing/ambiguous temporal evidence: {month}")
        if not freeze['frozen_at_unix'] <= frozen[0]['time_unix'] <= min(e['time_unix'] for e in reads):
            raise ValueError(f"Test read before freeze: {month}")
        if frozen[0]['sha256'] != freeze['predictions_sha256']:
            raise ValueError(f"Frozen hash differs from event log: {month}")
        scope = freeze['scope']
        if not max(scope['train']) < scope['validation'] < scope['test'] == month:
            raise ValueError(f"Nonchronological window: {month}")


def verify_payload(payload):
    # Reconstruct exact original write_json bytes, not just a new compact hash.
    ranked_checks = 0
    for group, predictions in payload['prediction_groups'].items():
        raw = (json.dumps(predictions, ensure_ascii=False, sort_keys=True, indent=2,
                          allow_nan=False) + '\n').encode()
        if hashlib.sha256(raw).hexdigest() != payload['freezes'][group]['predictions_sha256']:
            raise ValueError(f"Prediction payload differs from frozen experiment: {group}")
        for model, sources in predictions.items():
            for source, p in sources.items():
                candidates = payload['candidates'][source]
                if rank_candidates(source, candidates, p['scores'], k=20, seed=2026) != p['ranked']:
                    raise ValueError(f"Ranking mismatch: {group}/{model}/{source}")
                ranked_checks += 1
    checked = 0
    for evaluation in payload['evaluations']:
        month = evaluation['month']
        sources = evaluation['sources']
        models = payload['prediction_groups'][evaluation['group']]
        for model, expected in evaluation['metrics'].items():
            rows = [evaluate_source(s, payload['candidates'][s], models[model][s]['ranked'],
                                    payload['labels'][month].get(s, {})) for s in sources]
            assert_same(aggregate_results(rows), expected, f"{evaluation['name']}/{month}/{model}")
            checked += len(rows)
    return {'source_model_period_evaluations': checked, 'ranking_checks': ranked_checks}


def verify(folder):
    manifest = json.loads((folder/'bundle_manifest.json').read_text())
    for name, checksum in manifest['sha256'].items():
        if file_digest(folder/name) != checksum:
            raise ValueError(f"Artifact changed: {name}")
    totals = {'source_model_period_evaluations': 0, 'ranking_checks': 0}
    freezes = {}
    rolling = {}
    for name in manifest['payloads']:
        with gzip.open(folder/name, 'rt', encoding='utf-8') as stream:
            payload = json.load(stream)
        result = verify_payload(payload)
        for k in totals:
            totals[k] += result[k]
        if payload['kind'] == 'rolling':
            freezes[payload['month']] = payload['freezes']['rolling']
            rolling[payload['month']] = payload
    events = [json.loads(line) for line in (folder/'provenance/rolling-events.jsonl').read_text().splitlines()]
    verify_timeline(events, freezes)
    demo = json.loads((folder/'demo_data.json').read_text())
    seen = set()
    demo_checks = 0
    for query in demo['queries']:
        month, source = query['month'], query['id']
        if (month, source) in seen:
            raise ValueError('Duplicate demo query-period')
        seen.add((month, source))
        p = rolling[month]
        candidates, labels = p['candidates'][source], p['labels'][month].get(source, {})
        assert_same(query['scope'], p['freezes']['rolling']['scope'])
        assert_same(query['candidates'], len(candidates))
        assert_same(query['future_pairs'], len(labels))
        assert_same({t:d['future'] for t,d in query['targets'].items() if d['future']}, labels)
        for t, d in query['targets'].items():
            assert_same(d['eligible'], t in candidates)
        for model, view in query['models'].items():
            prediction = p['prediction_groups']['rolling'][model][source]
            assert_same(view['ranked'], prediction['ranked'][:10])
            assert_same(view['scores'], {t:prediction['scores'][t] for t in view['ranked']})
            metric = evaluate_source(source, candidates, prediction['ranked'], labels).all_metrics['ndcg@10']
            assert_same(view['ndcg'], metric)
            demo_checks += 1
    expected = {(month, s) for month,p in rolling.items() for s in p['candidates']}
    if seen != expected:
        raise ValueError('Incomplete demo panel')
    html = (folder/'demo.html').read_text()
    embedded = html.split('<script id="payload" type="application/json">', 1)[1].split('</script>', 1)[0]
    assert_same(json.loads(embedded), demo, 'HTML embedded payload')
    return {'status': 'verified', **totals, 'rolling_windows': sorted(freezes), 'demo_model_checks': demo_checks,
            'scope': 'Frozen score/rank/label re-evaluation and recorded chronology; not model retraining.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--folder', type=Path, default=Path('reports/extensions/study-v2'))
    print(json.dumps(verify(parser.parse_args().folder), indent=2))
