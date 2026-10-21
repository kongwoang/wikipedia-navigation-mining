"""Independently recompute published main metrics from portable demo predictions.

Standard-library only: no downloads, model training or scientific dependencies.
"""
import argparse
import csv
import json
import math
from pathlib import Path

from .evaluation import evaluate_source, aggregate_results
from .ranking import rank_candidates
from .utils import file_digest


def verify(folder: Path):
    manifest_path=folder/'bundle_manifest.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        for name,checksum in manifest['sha256'].items():
            path=folder/name
            if not path.is_file() or file_digest(path)!=checksum:
                raise ValueError(f'Artifact mismatch: {name}')
    payload=json.loads((folder/'demo_data.json').read_text())
    freeze=json.loads((folder/'freeze.json').read_text())
    aggregates={}; checked=0
    for month in payload['months']:
        for model in payload['models']:
            rows=[]
            for query in payload['queries']:
                candidates=[target for target,d in query['destinations'].items() if d['hyperlink']]
                labels={target:d['future'][month] for target,d in query['destinations'].items() if d['future'][month]>0}
                prediction=query['predictions'][model]
                if rank_candidates(query['id'],candidates,prediction['scores'],k=20,seed=freeze['tie_seed'])!=prediction['ranked']:
                    raise ValueError('Rank/score/tie-policy mismatch')
                row=evaluate_source(query['id'],candidates,prediction['ranked'],labels)
                for field,metrics in (('all',row.all_metrics),('conditional',row.conditional_metrics)):
                    for key,value in metrics.items():
                        saved=query['metrics'][month][model][field][key]
                        if value is None:
                            if saved is not None: raise ValueError('Missing-label mismatch')
                        elif saved is None or not math.isclose(value,saved,rel_tol=1e-12,abs_tol=1e-12):
                            raise ValueError('Per-source metric mismatch')
                rows.append(row);checked+=1
            aggregates[(month,model)]=aggregate_results(rows)
    with (folder/'tables/metrics.csv').open() as f:
        for row in csv.DictReader(f):
            key=(row['month'],row['model'])
            if key not in aggregates: continue
            result=aggregates[key][row['denominator']]
            for metric in ('recall@5','recall@10','recall@20','mrr@10','ndcg@10','mass_recall@10','expected_rr@10'):
                value=result[metric][row['aggregation']]
                saved=float(row[metric]) if row[metric] else None
                if value is None:
                    if saved is not None: raise ValueError('Aggregate NA mismatch')
                elif saved is None or not math.isclose(value,saved,rel_tol=1e-12,abs_tol=1e-12):
                    raise ValueError('Aggregate metric mismatch')
    return {'source_model_period_evaluations':checked,'main_models':len(payload['models']),
            'queries':len(payload['queries']),'periods':payload['months'],'status':'verified'}


def seal(folder: Path):
    result=verify(folder)
    manifest={'verification':result,'sha256':{str(p.relative_to(folder)):file_digest(p)
        for p in sorted(folder.rglob('*')) if p.is_file() and p.name!='bundle_manifest.json'}}
    (folder/'bundle_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path('reports/generated'))
    p.add_argument('--seal',action='store_true');args=p.parse_args()
    print(json.dumps((seal if args.seal else verify)(args.folder),indent=2))
