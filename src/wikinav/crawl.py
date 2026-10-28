"""Bounded Wikipedia collection: independent API and HTML observations, no labels.

Only current HTML is crawled. Historical API revisions are stored as wikitext;
re-rendering an old revision today is not treated as historical page exposure.
"""
import argparse
from collections import deque
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import hashlib
from html.parser import HTMLParser
import json
import math
from pathlib import Path
import re
import time
import tomllib
import unicodedata
from urllib import error, parse, request, robotparser

from .utils import digest, file_digest, write_json

USER_AGENT='WikipediaNavigationMiningBot/0.1 (https://github.com/kongwoang/wikipedia-navigation-mining)'
VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
EXCLUDE={'navbox','vertical-navbox','infobox','reference','references','reflist','toc','mw-editsection','metadata'}


def utc():return datetime.now(timezone.utc).isoformat()
def title_key(title):return unicodedata.normalize('NFC',title.replace('_',' ')).strip()
def timestamp(value):
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('Explicit timezone required')
    return result


def article_target(href,base,namespaces):
    """Same-origin /wiki/ article URLs only; preserve case and legal title colons."""
    if not href or href.startswith('#'):return None
    url=parse.urlsplit(parse.urljoin(base,href));origin=parse.urlsplit(base)
    if url.scheme!='https' or url.netloc!=origin.netloc or url.query or not url.path.startswith('/wiki/'):
        return None
    title=title_key(parse.unquote(url.path[len('/wiki/'):]))
    if not title or ':' in title and title.split(':',1)[0].casefold() in namespaces:return None
    return title


class ArticleHTML(HTMLParser):
    """Document-order features, not viewport exposure or historical rendering."""
    def __init__(self,base,namespaces):
        super().__init__(convert_charrefs=True)
        self.base=base;self.namespaces=namespaces;self.stack=[];self.links=[]
        self.anchor=None;self.heading=None;self.section='lead';self.paragraph=0
        self.text=[];self.body_roots=0

    def handle_starttag(self,tag,attrs):
        a=dict(attrs);classes=set(a.get('class','').split())
        parent=self.stack[-1] if self.stack else {'body':False,'excluded':False}
        root='mw-parser-output' in classes and not parent['body']
        body=parent['body'] or root
        excluded=parent['excluded'] or bool(classes&EXCLUDE) or tag in {'script','style','nav'}
        entry={'tag':tag,'body':body,'excluded':excluded}
        if tag not in VOID:self.stack.append(entry)
        if root:self.body_roots+=1
        if not body:return
        if tag in {'h2','h3','h4','h5','h6'} and not excluded:self.heading=[]
        if tag=='p' and not excluded:self.paragraph+=1
        if tag=='a':
            target=article_target(a.get('href'),self.base,self.namespaces)
            if target:
                self.anchor={'target_title':target,'anchor_parts':[],'section':self.section,
                    'paragraph_index':self.paragraph,'excluded_context':excluded,
                    'redlink':'new' in classes,'href':a.get('href'),'occurrence_index':len(self.links)}

    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in VOID:self.handle_endtag(tag)

    def handle_data(self,data):
        if self.anchor is not None:self.anchor['anchor_parts'].append(data)
        if self.heading is not None:self.heading.append(data)
        if self.stack and self.stack[-1]['body'] and not self.stack[-1]['excluded'] and data.strip():self.text.append(data)

    def handle_endtag(self,tag):
        if tag=='a' and self.anchor is not None:
            self.anchor['anchor_text']=' '.join(''.join(self.anchor.pop('anchor_parts')).split())
            self.links.append(self.anchor);self.anchor=None
        if tag in {'h2','h3','h4','h5','h6'} and self.heading is not None:
            self.section=' '.join(''.join(self.heading).split()) or self.section;self.heading=None
        for i in range(len(self.stack)-1,-1,-1):
            if self.stack[i]['tag']==tag:
                del self.stack[i:];break


def parse_article(html,base,namespaces):
    parser=ArticleHTML(base,namespaces);parser.feed(html);parser.close()
    def identifier(key):
        m=re.search(r'"'+key+r'"\s*:\s*(\d+)',html)
        return int(m.group(1)) if m else None
    links=parser.links
    # Record all contexts separately; eligible body links exclude template boxes/refs.
    eligible=[x for x in links if not x['excluded_context'] and not x['redlink']]
    for i,x in enumerate(eligible):x['body_link_position']=i
    return {'revision_id':identifier('wgRevisionId'),'page_id':identifier('wgArticleId'),
            'body_roots':parser.body_roots,'text':' '.join(' '.join(parser.text).split()),
            'occurrences':links,'body_targets':sorted({x['target_title'] for x in eligible}),
            'all_article_targets':sorted({x['target_title'] for x in links if not x['redlink']}),
            'position_semantics':'zero-based document order, not visual position or viewport exposure'}


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):return None


class CrawlStop(RuntimeError):pass


class Client:
    """Serial, bounded transport with content-addressed cache and explicit errors."""
    def __init__(self,root,host,delay=1.,max_requests=80,max_bytes=2_000_000,retries=2):
        self.root=root;self.host=host;self.delay=delay;self.max_requests=max_requests
        self.max_bytes=max_bytes;self.retries=retries;self.calls=0;self.last=0.
        self.opener=request.build_opener(NoRedirect());self.robot=None;self.next_delay=delay
        (root/'raw').mkdir(parents=True,exist_ok=True)

    def fetch(self,url,kind):
        u=parse.urlsplit(url)
        if u.scheme!='https' or u.netloc!=self.host:raise ValueError('Out-of-scope origin')
        if kind=='html':
            if self.robot is None or not self.robot.can_fetch(USER_AGENT,url):raise CrawlStop('robots.txt disallows HTML URL')
            if not u.path.startswith('/wiki/') or u.query:raise ValueError('Only canonical article HTML URLs allowed')
        key=hashlib.sha256(url.encode()).hexdigest();body=self.root/'raw'/f'{key}.body';meta=self.root/'raw'/f'{key}.json'
        if meta.exists():
            info=json.loads(meta.read_text());raw=body.read_bytes()
            if hashlib.sha256(raw).hexdigest()!=info['sha256']:raise ValueError('Cached body changed')
            return raw,info
        for attempt in range(self.retries+1):
            if self.calls>=self.max_requests:raise CrawlStop('Request budget exhausted; resume with same budget per invocation')
            time.sleep(max(0,max(self.delay,self.next_delay)-(time.monotonic()-self.last)));self.calls+=1
            started=time.monotonic()
            req=request.Request(url,headers={'User-Agent':USER_AGENT,'Accept':'text/html' if kind=='html' else '*/*'})
            try:
                with self.opener.open(req,timeout=25) as r:
                    raw=r.read(self.max_bytes+1)
                    if len(raw)>self.max_bytes:raise ValueError('Response exceeds byte cap')
                    info={'url':url,'kind':kind,'status':r.status,'fetched_at':utc(),'bytes':len(raw),
                          'sha256':hashlib.sha256(raw).hexdigest(),'content_type':r.headers.get('Content-Type'),
                          'etag':r.headers.get('ETag'),'last_modified':r.headers.get('Last-Modified')}
                self.last=time.monotonic()
                self.next_delay=5. if kind=='api' and self.last-started>1 else self.delay
                info['elapsed_seconds']=self.last-started
                if kind=='api':
                    result=json.loads(raw)
                    if result.get('error'):
                        code=result['error'].get('code')
                        if code=='maxlag' and attempt<self.retries:time.sleep(5);continue
                        raise CrawlStop('API error: '+str(code))
                body.write_bytes(raw);write_json(meta,info);return raw,info
            except error.HTTPError as exc:
                self.last=time.monotonic();self.log_failure(url,exc.code,str(exc))
                if exc.code in (401,403):raise CrawlStop(f'HTTP {exc.code}; no access-control bypass') from exc
                if exc.code not in (429,500,502,503,504):raise
                if attempt==self.retries:raise CrawlStop(f'HTTP {exc.code}; retry budget exhausted') from exc
                value=exc.headers.get('Retry-After','')
                try:wait=float(value)
                except ValueError:
                    try:wait=(parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds()
                    except (ValueError,TypeError):wait=2**(attempt+1)
                if wait>60:raise CrawlStop('Retry-After >60s; resume later') from exc
                time.sleep(max(1,wait))
            except (error.URLError,TimeoutError) as exc:
                self.last=time.monotonic();self.log_failure(url,None,str(exc))
                if attempt==self.retries:raise CrawlStop('Network retry budget exhausted') from exc
                time.sleep(2**(attempt+1))
        raise CrawlStop('Retry budget exhausted')

    def log_failure(self,url,status,message):
        with (self.root/'request_errors.jsonl').open('a') as f:f.write(json.dumps({'at':utc(),'url':url,'status':status,'message':message})+'\n')

    def api(self,**params):
        params={'action':'query','format':'json','formatversion':'2','maxlag':'5',**params}
        url='https://'+self.host+'/w/api.php?'+parse.urlencode(sorted(params.items()))
        raw,info=self.fetch(url,'api');return json.loads(raw),info

    def robots(self):
        raw,info=self.fetch('https://'+self.host+'/robots.txt','robots')
        self.robot=robotparser.RobotFileParser();self.robot.parse(raw.decode('utf-8').splitlines())
        delay=self.robot.crawl_delay(USER_AGENT)
        if delay is not None:self.delay=max(self.delay,delay)
        rate=self.robot.request_rate(USER_AGENT)
        if rate:self.delay=max(self.delay,rate.seconds/rate.requests)
        return info


def api_article(client,title):
    params={'prop':'revisions|links','titles':title,'redirects':'1','rvprop':'ids|timestamp|content',
            'rvslots':'main','plnamespace':'0','pllimit':'500'}
    links=set();observations=[];revision=None;page=None;seen=set()
    while True:
        result,info=client.api(**params);observations.append(info)
        pages=result.get('query',{}).get('pages',[])
        if len(pages)!=1 or pages[0].get('missing') or pages[0].get('invalid'):raise ValueError('Missing or invalid API source')
        p=pages[0]
        if p['ns']!=0:raise ValueError('Source is not main namespace')
        r=p.get('revisions',[{}])[0]
        if not r.get('revid') or 'content' not in r.get('slots',{}).get('main',{}):raise ValueError('Revision unavailable')
        if revision is not None and r['revid']!=revision['revid']:raise ValueError('Revision changed during API pagination')
        revision=r;page=p
        links.update(title_key(x['title']) for x in p.get('links',[]) if x['ns']==0)
        continuation=result.get('continue')
        if not continuation:break
        marker=json.dumps(continuation,sort_keys=True)
        if marker in seen:raise ValueError('Repeated API continuation')
        seen.add(marker);params.update(continuation)
    links.discard(title_key(page['title']))
    return {'page_id':page['pageid'],'title':page['title'],'revision_id':revision['revid'],
            'revision_timestamp':revision['timestamp'],'wikitext':revision['slots']['main']['content'],
            'targets':sorted(links),'requests':observations,
            'target_semantics':'API main-namespace link titles; target existence/redirect canonicalization not certified'}


def historical_article(client,page_id,cutoff):
    result,info=client.api(prop='revisions',pageids=str(page_id),rvprop='ids|timestamp|content',
        rvslots='main',rvstart=cutoff,rvdir='older',rvlimit='1')
    pages=result.get('query',{}).get('pages',[])
    if len(pages)!=1 or not pages[0].get('revisions'):raise ValueError('Historical revision unavailable')
    p=pages[0];r=p['revisions'][0]
    if p.get('pageid')!=page_id or timestamp(r['timestamp'])>timestamp(cutoff):raise ValueError('Historical identity/cutoff violation')
    content=r.get('slots',{}).get('main',{}).get('content')
    if content is None:raise ValueError('Historical content unavailable')
    return {'page_id':page_id,'current_title':p['title'],'revision_id':r['revid'],'revision_timestamp':r['timestamp'],
            'cutoff':cutoff,'wikitext':content,'request':info,
            'limitation':'Current title is not a historical mapping. Wikitext only; no historical template expansion or exposure claim.'}


def compare(api,html):
    a=set(api['targets']);h=set(html['body_targets']);all_h=set(html['all_article_targets'])
    h.discard(title_key(api['title']));all_h.discard(title_key(api['title']))
    matched=html['revision_id']==api['revision_id'] and html['page_id']==api['page_id']
    return {'matched_revision':matched,'api_revision':api['revision_id'],'html_revision':html['revision_id'],
            'api_targets':len(a),'html_body_targets':len(h),'html_all_targets':len(all_h),
            'body_jaccard':len(a&h)/len(a|h) if matched and a|h else None,
            'all_context_jaccard':len(a&all_h)/len(a|all_h) if matched and a|all_h else None,
            'api_only_titles':sorted(a-h),'html_body_only_titles':sorted(h-a),
            'interpretation':'Title-level extraction agreement, not precision/recall against ground truth; null metrics on revision mismatch.'}


def validate(config):
    if not re.fullmatch(r'[a-z]{2,12}',config['edition']):raise ValueError('Invalid Wikipedia edition')
    if config['mode'] not in ('api','html','both'):raise ValueError('Invalid collector mode')
    for key in ('max_pages','max_requests','max_response_bytes'):
        if type(config[key]) is not int or config[key]<1:raise ValueError('Positive integer budget required: '+key)
    if type(config['max_depth']) is not int or config['max_depth']<0 or type(config['delay_seconds']) not in (int,float) or not math.isfinite(config['delay_seconds']) or config['delay_seconds']<1:
        raise ValueError('Depth >=0 and serial delay >=1s required')
    if not config['seeds'] or len(config['seeds'])>config['max_pages']:raise ValueError('Seeds exceed page budget')
    if config.get('historical_cutoff'):timestamp(config['historical_cutoff'])


def run(config_path,output):
    config=tomllib.loads(config_path.read_text());validate(config)
    signature={'config':config,'code_sha256':file_digest(Path(__file__)),'user_agent':USER_AGENT}
    output.mkdir(parents=True,exist_ok=True)
    state_path=output/'state.json'
    if state_path.exists():
        state=json.loads(state_path.read_text())
        if state['signature']!=signature:raise ValueError('Changed crawl config/code: choose fresh output')
    else:
        state={'signature':signature,'started_at':utc(),'pending':[[title_key(s),0] for s in config['seeds']],
               'completed':{},'failures':{},'observed_edge_targets':[]}
    def checkpoint():
        temp=output/'state.json.tmp';temp.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');temp.replace(state_path)
    checkpoint();client=Client(output,config['edition']+'.wikipedia.org',config['delay_seconds'],config['max_requests'],config['max_response_bytes'])
    (output/'pages').mkdir(exist_ok=True);namespaces=set()
    # Independent HTML mode needs no API. Conservatively exclude colon titles.
    if config['mode'] in ('api','both'):
        site,_=client.api(meta='siteinfo',siprop='namespaces|namespacealiases')
        for ns in site['query']['namespaces'].values():
            if ns['id']!=0:
                namespaces.update(title_key(ns.get(k,'')).casefold() for k in ('name','canonical') if ns.get(k))
        namespaces.update(title_key(ns['alias']).casefold() for ns in site['query']['namespacealiases'] if ns['id']!=0)
    if config['mode'] in ('html','both'):client.robots()
    attempted=len(state['completed'])+len(state['failures'])
    while state['pending'] and attempted<config['max_pages']:
        title,depth=state['pending'][0];key=hashlib.sha256(title.encode()).hexdigest()[:24]
        path=output/'pages'/f'{key}.json'
        try:
            if path.exists():record=json.loads(path.read_text())
            else:
                record={'seed_or_discovered_title':title,'depth':depth,'collected_at':utc()}
                if config['mode'] in ('api','both'):record['api']=api_article(client,title)
                display=record.get('api',{}).get('title',title)
                if config['mode'] in ('html','both'):
                    url='https://'+client.host+'/wiki/'+parse.quote(display.replace(' ','_'),safe='')
                    raw,info=client.fetch(url,'html');html=parse_article(raw.decode('utf-8'),url,namespaces)
                    if not html['body_roots']:raise ValueError('No article body detected; do not treat as empty graph')
                    if config['mode']=='html':
                        for field in ('body_targets','all_article_targets'):html[field]=[t for t in html[field] if ':' not in t]
                        html['namespace_policy']='Conservative HTML-only mode excludes colon titles; may lose legitimate main-namespace titles.'
                    record['html']={**html,'request':info}
                if 'api' in record and 'html' in record:record['comparison']=compare(record['api'],record['html'])
                if config.get('historical_cutoff') and 'api' in record:
                    try:record['historical_api']=historical_article(client,record['api']['page_id'],config['historical_cutoff'])
                    except ValueError as exc:record['historical_error']=str(exc)
                write_json(path,record)
            targets=record.get('html',{}).get('body_targets',record.get('api',{}).get('targets',[]))
            state['completed'][title]={'artifact':str(path.relative_to(output)),'sha256':file_digest(path),'depth':depth}
            state['observed_edge_targets']=sorted(set(state['observed_edge_targets'])|set(targets))
            if depth<config['max_depth']:
                known=set(state['completed'])|set(state['failures'])|{t for t,d in state['pending']}
                state['pending'].extend([t,depth+1] for t in sorted(targets) if t not in known)
        except CrawlStop as exc:
            state['stop_reason']=str(exc);checkpoint();raise
        except (ValueError,error.HTTPError) as exc:
            state['failures'][title]={'error':str(exc),'depth':depth}
        state['pending'].pop(0);attempted+=1;checkpoint()
    state.pop('stop_reason',None);state['last_finished_at']=utc();checkpoint()
    report={'status':'bounded_complete','requested_pages':config['max_pages'],'completed_pages':len(state['completed']),
            'failed_pages':len(state['failures']),'frontier_remaining':len(state['pending']),
            'distinct_edge_target_titles':len(state['observed_edge_targets']),'http_requests_this_invocation':client.calls,
            'scope':'Crawl/extraction pilot, not recommendation evaluation; uncrawled frontier is boundary, not dangling.',
            'signature':signature,'comparisons':[],'historical_revisions':[]}
    for title,entry in state['completed'].items():
        record=json.loads((output/entry['artifact']).read_text())
        if file_digest(output/entry['artifact'])!=entry['sha256']:raise ValueError('Processed crawl artifact changed')
        if 'comparison' in record:report['comparisons'].append({'source_title':title,**record['comparison']})
        if 'historical_api' in record:
            h=record['historical_api'];report['historical_revisions'].append({k:h[k] for k in ('page_id','current_title','revision_id','revision_timestamp','cutoff')})
    (output/'summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',type=Path,default=Path('configs/crawl-pilot.toml'))
    p.add_argument('--output',type=Path,default=Path('data/raw/crawl/pilot-v1'));a=p.parse_args()
    report=run(a.config,a.output)
    print(json.dumps({k:v for k,v in report.items() if k not in ('signature','comparisons','historical_revisions')},indent=2))
