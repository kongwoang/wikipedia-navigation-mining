"""Independent DOM differential audit and blinded-to-production review sample.

Optional dependencies: requirements-audit.lock. Raw captures remain local.
This checks extraction, not recommendation or unbiased population accuracy.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from urllib.parse import urljoin, urlsplit, unquote
import unicodedata
from bs4 import BeautifulSoup

OMIT={'navbox','vertical-navbox','infobox','reference','references','reflist','toc','mw-editsection','metadata','mw-authority-control','mw-mf-linked-projects'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def stable(s):return hashlib.sha256(s.encode()).hexdigest()
def normalize(t):return unicodedata.normalize('NFC',t.replace('_',' ')).strip()

def independent_target(href,base,namespaces):
    if not href or href.startswith('#'):return None
    u=urlsplit(urljoin(base,href));origin=urlsplit(base)
    if u.scheme!='https' or u.netloc!=origin.netloc or u.query or not u.path.startswith('/wiki/'):return None
    title=normalize(unquote(u.path[6:]))
    if not title or (':' in title and title.split(':',1)[0].casefold() in namespaces):return None
    return title

def scan(raw,base,namespaces):
    soup=BeautifulSoup(raw,'html5lib');items=[]
    for i,a in enumerate(soup.find_all('a',href=True)):
        chain=[a,*a.parents];inside=any('mw-parser-output' in x.get('class',[]) for x in chain if x.name)
        inside=inside and not any(set(x.get('class',[])) & {'mw-indicators','mw-indicator','vector-body-before-content'} for x in chain if x.name)
        excluded=any(OMIT.intersection(x.get('class',[])) or x.name in ('script','style','nav') for x in chain if x.name)
        target=independent_target(a['href'],base,namespaces)
        red='new' in a.get('class',[])
        text=' '.join(a.get_text().split())
        context=' > '.join(x.name+('.'+'.'.join(x.get('class',[])) if x.get('class') else '') for x in reversed(chain[:-1]) if x.name)
        items.append({'dom_index':i,'href':a['href'],'anchor_text':text,'target':target,'inside':inside,'excluded':bool(excluded),'redlink':red,
            'eligible':bool(inside and target and not excluded and not red),
            'group':'outside' if not inside else 'ineligible' if not target or red else 'excluded' if excluded else 'body',
            'ancestry':context,'parent_excerpt':' '.join(a.parent.get_text(' ',strip=True).split())[:220],
            'anchor_html':str(a)[:650]})
    return items

def key(x):return (x['href'],x['anchor_text'],bool(x['excluded']),bool(x['redlink']))

def audit(raw_root,out,review_pool=None):
    out.mkdir(parents=True,exist_ok=False)
    state=json.loads((raw_root/'state.json').read_text());namespaces=set()
    for meta in (raw_root/'raw').glob('*.json'):
        m=json.loads(meta.read_text());p=meta.with_suffix('.body');assert sha(p)==m['sha256']
        if 'siprop=' in m['url']:
            site=json.loads(p.read_bytes())['query']
            for ns in site['namespaces'].values():
                if ns['id']!=0:
                    for k in ('name','canonical'):
                        if ns.get(k):namespaces.add(normalize(ns[k]).casefold())
            namespaces.update(normalize(x['alias']).casefold() for x in site['namespacealiases'] if x['id']!=0)
    if not namespaces:raise ValueError('Namespace inventory missing')
    from wikinav.crawl import parse_article
    locked=json.loads(review_pool.read_text()) if review_pool else None
    pages=[];samples=[];deltas=[]
    for title,entry in state['completed'].items():
        p=raw_root/entry['artifact'];assert sha(p)==entry['sha256'];r=json.loads(p.read_text())
        info=r['html']['request'];raw=raw_root/'raw'/(stable(info['url'])+'.body');assert sha(raw)==info['sha256']
        items=scan(raw.read_bytes(),info['url'],namespaces)
        r['html']={**r['html'],**parse_article(raw.read_text(),info['url'],namespaces)}
        observed=[x for x in items if x['inside'] and x['target']]
        ref=Counter(key(x) for x in observed)
        prod=Counter((x['href'],x['anchor_text'],bool(x['excluded_context']),bool(x['redlink'])) for x in r['html']['occurrences'])
        refbody={x['target'] for x in items if x['eligible']};prodbody=set(r['html']['body_targets'])
        pageid=r['api']['page_id']
        pages.append({'title':title,'page_id':pageid,'revision_id':r['html']['revision_id'],'url':info['url'],'raw_sha256':info['sha256'],
            'dom_anchors':len(items),'dom_article_occurrences':sum(ref.values()),'production_occurrences':sum(prod.values()),
            'dom_body_targets':len(refbody),'production_body_targets':len(prodbody),'occurrence_missing':sum((ref-prod).values()),
            'occurrence_extra':sum((prod-ref).values()),'body_missing':sorted(refbody-prodbody),'body_extra':sorted(prodbody-refbody),
            'matched_revision':r['comparison']['matched_revision']})
        if ref!=prod or refbody!=prodbody:
            deltas.append({'title':title,'missing':[{'key':k,'n':n} for k,n in (ref-prod).items()], 'extra':[{'key':k,'n':n} for k,n in (prod-ref).items()]})
        chosen=[]
        for group,n in [('body',2),('excluded',2),('outside',1),('ineligible',1)]:
            candidates=sorted([x for x in items if x['group']==group],key=lambda x:stable(f"occurrence-audit-v1:{pageid}:{x['dom_index']}"))
            chosen.extend(candidates[:n])
        ids={x['dom_index'] for x in chosen}
        rest=sorted([x for x in items if x['dom_index'] not in ids],key=lambda x:stable(f"fill-audit-v1:{pageid}:{x['dom_index']}"))
        chosen.extend(rest[:6-len(chosen)])
        if locked is not None:
            ids={x['dom_index'] for x in locked if x['page_id']==pageid}
            chosen=[x for x in items if x['dom_index'] in ids]
        for x in sorted(chosen,key=lambda x:x['dom_index']):
            samples.append({'id':f"{pageid}:{x['dom_index']}",'page_title':title,'page_id':pageid,'raw_sha256':info['sha256'],**x})
    for name,obj in [('pages',pages),('review_pool',samples),('differential',deltas)]:
        (out/(name+'.json')).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pages':len(pages),'review_occurrences':len(samples),'differential_pages':len(deltas),'missing':sum(x['occurrence_missing'] for x in pages),'extra':sum(x['occurrence_extra'] for x in pages)},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--review-pool',type=Path);a=p.parse_args();audit(a.raw,a.out,a.review_pool)
