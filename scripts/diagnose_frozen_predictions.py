"""Post-hoc mechanism diagnostics; never fit, tune, or modify published rankings."""
import argparse
import csv
import json
import math
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from wikinav.evaluation import paired_bootstrap
from wikinav.utils import file_digest
from wikinav.verify_bundle import verify

MODELS = ['M1B_backoff', 'M3_ppr_h', 'M6B_fusion']


def diagnostics(bundle, output, plot=False):
    verification = verify(bundle)
    payload = json.loads((bundle / 'demo_data.json').read_text())
    output.mkdir(parents=True, exist_ok=False)
    rows, summary = [], {}
    for month in payload['months']:
        period = []
        for query in payload['queries']:
            labels = {t: d['future'][month] for t, d in query['destinations'].items()
                      if d['future'][month] > 0}
            if not labels:
                continue
            ideal = sum(math.log2(1+n) / math.log2(i+2)
                        for i, n in enumerate(sorted(labels.values(), reverse=True)[:10]))
            eligible = [n for t, n in labels.items() if query['destinations'][t]['hyperlink']]
            ceiling = sum(math.log2(1+n) / math.log2(i+2)
                          for i, n in enumerate(sorted(eligible, reverse=True)[:10])) / ideal
            row = {'month': month, 'source': query['id'], 'title': query['title'],
                   'candidate_oracle_ndcg': ceiling}
            for model in MODELS:
                parts = {'train_observed': 0., 'train_unobserved': 0.}
                for i, target in enumerate(query['predictions'][model]['ranked'][:10]):
                    key = ('train_observed' if query['destinations'][target]['train_count']
                           else 'train_unobserved')
                    parts[key] += math.log2(1+labels.get(target, 0)) / math.log2(i+2) / ideal
                total = sum(parts.values())
                expected = query['metrics'][month][model]['all']['ndcg@10']
                if not math.isclose(total, expected, abs_tol=1e-12, rel_tol=1e-12):
                    raise ValueError('Decomposition does not match frozen NDCG')
                if total > ceiling + 1e-12:
                    raise ValueError('Ranking exceeded same-candidate oracle')
                row[model + ':ndcg'] = total
                row.update({model + ':' + key: value for key, value in parts.items()})
            period.append(row)
        rows.extend(period)
        mean = lambda key: math.fsum(r[key] for r in period) / len(period)
        contrasts = {}
        for model in MODELS[1:]:
            contrasts[model + ' - M1B_backoff'] = {}
            for component in ('ndcg', 'train_observed', 'train_unobserved'):
                left = {r['source']: r[model+':'+component] for r in period}
                right = {r['source']: r['M1B_backoff:'+component] for r in period}
                contrasts[model+' - M1B_backoff'][component] = paired_bootstrap(
                    left, right, seed=2026, resamples=2000)
        summary[month] = {'sources': len(period), 'candidate_oracle_ndcg': mean('candidate_oracle_ndcg'),
                          'model_ndcg': {m: mean(m+':ndcg') for m in MODELS},
                          'contrasts': contrasts}
    with (output/'source_decomposition.csv').open('x', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    result = {'status': 'post-hoc exploratory analysis of the existing study-v3 holdout',
              'definition': 'Additive NDCG components share the FULL per-source IDCG; rankings unchanged.',
              'oracle': 'Future-label same-candidate upper bound, not a deployable model or candidate generator.',
              'limitations': 'Published training absence is censored. Query bootstrap assumes approximate exchangeability; no causal claim.',
              'bundle_verification': verification,
              'payload_sha256': file_digest(bundle/'demo_data.json'), 'periods': summary}
    (output/'mechanism_diagnostics.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    if plot:
        plot_summary(summary, output)
    print(json.dumps({m: {'sources': s['sources'], 'oracle_ndcg': s['candidate_oracle_ndcg'],
                         'fusion_delta': {k: v['difference'] for k, v in s['contrasts']['M6B_fusion - M1B_backoff'].items()}}
                      for m, s in summary.items()}, indent=2))


def plot_summary(summary, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(len(summary), 2, figsize=(11, 6), squeeze=False)
    for row, (month, period) in enumerate(summary.items()):
        for col, model in enumerate(MODELS[1:]):
            ax = axes[row, col]
            contrast = period['contrasts'][model+' - M1B_backoff']
            keys = ['train_observed', 'train_unobserved', 'ndcg']
            values = [contrast[k]['difference'] for k in keys]
            ax.barh(range(3), values, color=['#4b7195', '#d78b39', '#546065'])
            ax.set_yticks(range(3), ['Train-observed', 'Train-unobserved', 'Total'])
            ax.invert_yaxis(); ax.axvline(0, color='black', linewidth=.6)
            ax.set_title(month+' | '+model+' minus Markov', fontsize=10)
            ax.set_xlabel('Delta full macro NDCG@10')
            for y, value in enumerate(values):
                ax.annotate(f'{value:+.6f}', (value, y), xytext=(4 if value >= 0 else -4, 0),
                            textcoords='offset points', ha='left' if value >= 0 else 'right',
                            va='center', fontsize=8)
            ax.margins(x=.30)
            ax.spines[['top', 'right']].set_visible(False)
    fig.suptitle('Frozen-ranking decomposition | Separate axis scales | Exploratory point estimates', fontsize=11)
    fig.tight_layout()
    fig.savefig(output/'decomposition.png', dpi=160)
    fig.savefig(output/'decomposition.svg')
    plt.close(fig)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--bundle', type=Path, default=Path('reports/generated'))
    p.add_argument('--output', type=Path, default=Path('reports/extensions/mechanism-v1'))
    p.add_argument('--plot', action='store_true', help='Requires matplotlib; optional scientific figure')
    args = p.parse_args(); diagnostics(args.bundle, args.output, args.plot)
