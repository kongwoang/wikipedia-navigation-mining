"""Offline extraction audit and graph export from cached crawl observations."""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
from urllib.parse import quote
from .utils import file_digest,write_json
from .crawl import compare,title_key,timestamp,parse_article,api_article


def collapse_edges(rows,count_key=None):
    """Known title aliases must not create parallel edges in a simple graph."""
    groups={}
    for row in rows:
        key=(row['source'],row['target'])
        if key not in groups:
            groups[key]={**row,'target_titles':[row['target_title']]}
            continue
        g=groups[key];g['target_titles'].append(row['target_title'])
        if count_key:
            g[count_key]+=row[count_key];g['in_lead']|=row['in_lead']
            if row['first_body_link_position']<g['first_body_link_position']:
                g['first_body_link_position']=row['first_body_link_position'];g['first_section']=row['first_section']
    for g in groups.values():
        g['target_titles']=sorted(set(g['target_titles']));g['target_title']=g['target_titles'][0]
    return [groups[k] for k in sorted(groups)]


def export(raw,processed,report):
    state=json.loads((raw/'state.json').read_text())
    if processed.exists() or report.exists():raise FileExistsError('Use fresh output directories')
    records=[]
    for entry in state['completed'].values():
        path=raw/entry['artifact']
        if file_digest(path)!=entry['sha256']:raise ValueError('Changed crawl record')
        records.append(json.loads(path.read_text()))
    captures=[]
    for meta in sorted((raw/'raw').glob('*.json')):
        info=json.loads(meta.read_text());body=meta.with_suffix('.body')
        if file_digest(body)!=info['sha256']:raise ValueError('Changed raw capture')
        captures.append(info)
    by_url={c['url']:c for c in captures}
    def body_for(info):
        import hashlib
        key=hashlib.sha256(info['url'].encode()).hexdigest()
        if by_url[info['url']]['sha256']!=info['sha256']:raise ValueError('Record/capture mismatch')
        return (raw/'raw'/f'{key}.body').read_bytes()
    namespaces=set()
    for c in captures:
        if 'meta=siteinfo' in c['url']:
            site=json.loads(body_for(c))['query']
            for n in site['namespaces'].values():
                if n['id']!=0:namespaces.update(title_key(n[k]).casefold() for k in ('name','canonical') if n.get(k))
            namespaces.update(title_key(n['alias']).casefold() for n in site['namespacealiases'] if n['id']!=0)
    for r in records:
        if 'html' in r:
            h=r['html'];replayed=parse_article(body_for(h['request']).decode('utf-8'),h['request']['url'],namespaces)
            if state['signature']['config']['mode']=='html':
                for field in ('body_targets','all_article_targets'):replayed[field]=[t for t in replayed[field] if ':' not in t]
            expected={k:v for k,v in h.items() if k not in ('request','namespace_policy')}
            if replayed!=expected:raise ValueError('HTML parsing replay differs')
        if 'api' in r:
            class ReplayClient:
                def __init__(self):self.pending=iter(r['api']['requests'])
                def api(self,**params):
                    info=next(self.pending);return json.loads(body_for(info)),info
            if api_article(ReplayClient(),r['seed_or_discovered_title'])!=r['api']:raise ValueError('API pagination replay differs')
    source_ids={}
    crawled_titles={title_key(r.get('api',{}).get('title',r['seed_or_discovered_title'])) for r in records}
    crawled_titles.update(title_key(r['seed_or_discovered_title']) for r in records)
    for r in records:
        a=r.get('api',{});h=r.get('html',{});pid=a.get('page_id',h.get('page_id'))
        for title in (a.get('title'),r['seed_or_discovered_title']):
            if title and pid:source_ids[title_key(title)]=pid
    processed.mkdir(parents=True);report.mkdir(parents=True)
    rows=[];nodes={};api_edges=[];html_edges=[];occurrences=[];pages=[];history=[]
    edition=state['signature']['config']['edition']
    def node(title):
        key=title_key(title);pid=source_ids.get(key)
        identity=f'{edition}:page:{pid}' if pid else f'{edition}:unresolved-title:{key}'
        nodes.setdefault(identity,{'node_id':identity,'title':key,'page_id':pid,'crawled':key in crawled_titles,
                                   'outgoing_unknown':key not in crawled_titles})
        return identity
    for r in records:
        api=r.get('api');html=r.get('html');title=api['title'] if api else r['seed_or_discovered_title'];source=node(title)
        if api and html:
            check=compare(api,html)
            if check!=r['comparison']:raise ValueError('Extraction comparison differs from stored result')
        if 'historical_api' in r:
            h=r['historical_api']
            if timestamp(h['revision_timestamp'])>timestamp(h['cutoff']):raise ValueError('Future historical content')
            history.append({k:v for k,v in h.items() if k not in ('wikitext','request')})
        api_targets=set(api['targets']) if api else set()
        html_targets=set(html['body_targets']) if html else set()
        for target in sorted(api_targets):
            dest=node(target)
            if dest!=source:api_edges.append({'source':source,'target':dest,'target_title':target,'weight':1,'weight_semantics':'API link presence'})
        grouped=defaultdict(list)
        for occurrence in html.get('occurrences',[]) if html else []:
            occurrences.append({'source':source,**occurrence})
            if not occurrence['excluded_context'] and not occurrence['redlink'] and occurrence['target_title'] in html_targets:
                grouped[occurrence['target_title']].append(occurrence)
        for target,items in sorted(grouped.items()):
            dest=node(target)
            if dest==source:continue
            first=min(items,key=lambda x:x['body_link_position'])
            html_edges.append({'source':source,'target':dest,'target_title':target,'occurrence_count':len(items),
                'first_body_link_position':first['body_link_position'],'first_section':first['section'],
                'in_lead':any(x['section']=='lead' for x in items),
                'weight_semantics':'Editorial link repetition, not click frequency'})
        rows.append({'source_title':title,'page_id':api['page_id'] if api else html['page_id'],
                     'depth':r['depth'],'api_revision':api['revision_id'] if api else None,
                     'html_revision':html['revision_id'] if html else None,
                     'matched_revision':r.get('comparison',{}).get('matched_revision'),
                     'api_targets':len(api_targets),'html_body_targets':len(html_targets),
                     'html_occurrences':len(html['occurrences']) if html else 0,
                     'body_jaccard':r.get('comparison',{}).get('body_jaccard'),
                     'all_context_jaccard':r.get('comparison',{}).get('all_context_jaccard'),
                     'historical_available':'historical_api' in r})
        pages.append({'source':source,'title':title,'text':html.get('text') if html else None,
                      'api_revision':api.get('revision_id') if api else None,'html_revision':html.get('revision_id') if html else None,
                      'article_url':f'https://{edition}.wikipedia.org/wiki/'+quote(title.replace(' ','_'),safe=''),
                      'license_note':'Wikipedia text: consult article licensing/history; CC BY-SA attribution applies, not Clickstream CC0.'})
    api_edges=collapse_edges(api_edges)
    html_edges=collapse_edges(html_edges,'occurrence_count')
    for name,items in [('nodes',list(nodes.values())),('api_edges',api_edges),('html_edges',html_edges),('occurrences',occurrences),('pages',pages)]:
        with (processed/(name+'.jsonl')).open('x') as f:
            for item in items:f.write(json.dumps(item,ensure_ascii=False,sort_keys=True)+'\n')
    summary={'completed_pages':len(records),'failed_pages':len(state['failures']),
             'distinct_source_page_ids':len(set(source_ids.values())),
             'matched_revision_pairs':sum(r['matched_revision'] is True for r in rows),
             'historical_available':len(history),'historical_unavailable':sum('historical_error' in r for r in records),
             'raw_captures':len(captures),'raw_bytes':sum(c['bytes'] for c in captures),
             'capture_start':min(c['fetched_at'] for c in captures),'capture_end':max(c['fetched_at'] for c in captures),
             'api_edges':len(api_edges),'html_edges':len(html_edges),'html_occurrences':len(occurrences),
             'nodes_in_export':len(nodes),'unresolved_target_nodes':sum(n['outgoing_unknown'] for n in nodes.values()),
             'frontier_remaining':len(state['pending']),
             'raw_parsing_replay_verified':True,
             'scope':'Current title-level crawl extraction pilot. No Clickstream labels, no recommendation accuracy claims.'}
    write_json(report/'summary.json',summary);write_json(report/'historical_revisions.json',history)
    with (report/'source_comparison.csv').open('x',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
    write_json(processed/'manifest.json',{'crawl_signature':state['signature'],'summary':summary,
        'files':{p.name:file_digest(p) for p in sorted(processed.glob('*.jsonl'))}})
    write_json(report/'provenance.json',{'crawl_signature':state['signature'],'captures':captures,
        'processed_manifest':json.loads((processed/'manifest.json').read_text()),
        'note':'Pilot-v2 reuses captures from pilot-v1; final transport adds 5s pause after slow API requests. Capture times are recorded; collection is not an atomic snapshot.'})
    lines=['# Crawl pilot: MediaWiki API và HTML','',
           'Đây là dữ liệu tự thu thập từ Wikipedia, không tải một graph dataset có sẵn. Pilot kiểm tra acquisition/extraction; chưa đánh giá model recommendation.','',
           f"Hoàn thành **{summary['completed_pages']} trang**, {summary['matched_revision_pairs']} cặp API/HTML khớp revision, {summary['historical_available']} historical revisions trước cutoff. {summary['historical_unavailable']} trang không có revision phù hợp cutoff được ghi nhận, không lấy bản hiện tại thay thế.",'',
           f"Raw captures: {summary['raw_captures']} responses, {summary['raw_bytes']:,} bytes; API graph {len(api_edges)} edges, HTML body graph {len(html_edges)} edges, {len(occurrences)} link occurrences. Có {summary['unresolved_target_nodes']} target nodes chưa crawl/resolve; không coi chúng là dangling nodes.",'',
           '| Source | API targets | HTML body targets | Body Jaccard | All-context Jaccard |','|---|---:|---:|---:|---:|']
    for row in rows:
        fmt=lambda v:'N/A' if v is None else f'{v:.4f}'
        lines.append(f"| {row['source_title']} | {row['api_targets']} | {row['html_body_targets']} | {fmt(row['body_jaccard'])} | {fmt(row['all_context_jaccard'])} |")
    lines += ['', 'API links và body links đo hai phạm vi khác nhau: infobox/reference/template links có thể bị loại khỏi body graph. Jaccard thấp không tự chứng minh scraper sai hoặc một graph tốt hơn cho recommendation. Equal article revision cũng không bảo đảm templates/cache hoàn toàn đồng thời.','',
              'Seed sampling: năm nguồn từ original train-defined panel, thứ tự SHA256(`crawl-pilot-v1:` + source ID), rồi depth1 BFS deterministic. Frontier thiên về wrestling vì seed đầu có nhiều links và budget nhỏ; đây là pilot kỹ thuật, không representative corpus.','',
              'Xem [thiết kế tích hợp](../../../docs/CRAWLING_EXTENSION.md) cho hướng mở rộng và temporal safeguards. Raw HTML/wikitext ở data/raw (Git-ignored), graph/features ở data/processed (Git-ignored); report lưu counts, provenance và URLs. Không nhập current graph vào benchmark2018.']
    (report/'PILOT.md').write_text('\n'.join(lines)+'\n')
    write_json(report/'manifest.json',{'files':{p.name:file_digest(p) for p in sorted(report.iterdir()) if p.is_file()}})
    return summary


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,default=Path('data/raw/crawl/pilot-v2'))
    p.add_argument('--processed',type=Path,default=Path('data/processed/crawl/pilot-v2'))
    p.add_argument('--report',type=Path,default=Path('reports/crawl/pilot-v2'));a=p.parse_args()
    print(json.dumps(export(a.raw,a.processed,a.report),indent=2))
