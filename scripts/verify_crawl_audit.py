"""Portable integrity checks for the published extraction audit (no raw replay)."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text())
def verify():
    report='reports/crawl/audit-v2/'
    for name,digest in read(report+'manifest.json')['files'].items():
        if hashlib.sha256((ROOT/report/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed audit artifact: '+name)
    result=read(report+'review_summary.json')
    for field,name in [('sample_sha256','crawl-audit-review-pool.json'),('labels_sha256','crawl-audit-labels.json')]:
        if hashlib.sha256((ROOT/'docs/evidence'/name).read_bytes()).hexdigest()!=result[field]:raise ValueError('Changed review evidence')
    sample=read('docs/evidence/crawl-audit-review-pool.json');labels=read('docs/evidence/crawl-audit-labels.json')['labels'];pred=read(report+'review_predictions.json')
    ids=lambda items:{x['id'] for x in items}
    if not len(sample)==len(labels)==len(pred)==len(ids(sample))==120 or ids(sample)!=ids(labels) or ids(labels)!=ids(pred):raise ValueError('Review sample identity differs')
    if len(Counter(x['page_id'] for x in sample))!=20 or set(Counter(x['page_id'] for x in sample).values())!={6}:raise ValueError('Six occurrences/page required')
    gold={x['id']:x['include'] for x in labels}
    for stage in ['before','after']:
        counts={k:0 for k in ['tp','fp','tn','fn']}
        for x in pred:
            truth=gold[x['id']];p=x[stage];counts['tp' if truth and p else 'fn' if truth else 'fp' if p else 'tn']+=1
        if counts!=result[stage]:raise ValueError('Confusion table mismatch')
    summary=read(report+'summary.json');pages=read(report+'dom_pages.json')
    if len(pages)!=summary['completed_pages'] or sum(x['matched_revision'] for x in pages)!=summary['matched_revision_pairs']:raise ValueError('Page totals differ')
    if read(report+'dom_differential.json') or any(x['body_missing'] or x['body_extra'] or x['occurrence_missing'] or x['occurrence_extra'] for x in pages):raise ValueError('Differential extraction mismatch')
    return {'status':'verified','pages':len(pages),'review_occurrences':len(sample),'before':result['before'],'after':result['after'],'scope':'Published hashes/counts/annotations only; no raw HTML replay, human adjudication or browser QA.'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
