"""Read frozen study evidence for the 10-slide course presentation; no experiments."""
import csv
import hashlib
import json
from pathlib import Path
from statistics import median

ROOT=Path(__file__).resolve().parents[1]
def rows(name):return list(csv.DictReader((ROOT/'reports/generated/tables'/name).open()))
def build():
    models=[('M2_uniform','Uniform'),('M0_global','Global popularity'),('M1B_backoff','Markov / backoff'),('HITS','HITS-global'),('M3_ppr_h','PPR-H'),('M5H_node2vec','Node2Vec-H'),('M6B_fusion','Fusion')]
    metrics=rows('metrics.csv');table=[]
    for model,label in models:
        matches=[r for r in metrics if (r['month'],r['model'],r['denominator'],r['aggregation'])==('2018-05',model,'all','macro')]
        assert len(matches)==1
        table.append({'model':model,'label':label,**{k:float(matches[0][k]) for k in ['recall@5','recall@10','recall@20','mrr@10','ndcg@10']}})
    concentration=[r for r in rows('training_concentration.csv') if r['top1_share']]
    pairs=json.loads((ROOT/'reports/generated/paired_comparisons.json').read_text())
    sparse=[r for r in rows('transition_sparsity.csv') if r['month']=='2018-05' and r['edge_group']=='unobserved' and r['model'] in ['M1B_backoff','M3_ppr_h','M6B_fusion']]
    sources=['reports/generated/tables/metrics.csv','reports/generated/tables/training_concentration.csv','reports/generated/paired_comparisons.json','reports/generated/tables/transition_sparsity.csv','reports/CASE_STUDIES.md','reports/crawl/audit-v2/summary.json','reports/crawl/audit-v2/review_summary.json']
    return {'metrics':table,'concentration':{'sources':len(concentration),'median_top1':median(float(r['top1_share']) for r in concentration),'median_top5':median(float(r['top5_share']) for r in concentration)},
     'primary':pairs['2018-05']['M6B_fusion - M1B_backoff'],'sparsity':sparse,
     'crawl':json.loads((ROOT/'reports/crawl/audit-v2/summary.json').read_text()),
     'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources}}
if __name__=='__main__':
    out=ROOT/'.cache/deck-build/data.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n');print(out)
