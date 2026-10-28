"""Offline oracles for HTML extraction, temporal identity and bounded transport."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch
from urllib.error import HTTPError

from wikinav.crawl import (Client,CrawlStop,article_target,parse_article,api_article,
    historical_article,compare,validate,run)

BASE='https://es.wikipedia.org/wiki/Source'
HTML='''<html><script>{"wgRevisionId":12,"wgArticleId":1}</script>
<a href="/wiki/Outside">Outside</a><div class="mw-parser-output">
<table class="infobox"><tr><td><a href="/wiki/Box">Box</a></td></tr></table>
<p>A <a href="/wiki/Alpha#History"><b>Alpha</b> &amp; more</a>.</p>
<h2>History</h2><p><a href="/wiki/Alpha">Again</a><br><a href="/wiki/Beta">Beta</a></p>
<sup class="reference"><a href="/wiki/Reference">ref</a></sup>
<a href="https://evil.example/wiki/Bad">bad</a><a href="/wiki/Categor%C3%ADa:Test">cat</a>
<a href="/wiki/Red" class="new">red</a></div></html>'''

def revision(revid=12):return {'revid':revid,'timestamp':'2017-01-01T00:00:00Z','slots':{'main':{'content':'[[Alpha]]'}}}
def response(links,continuation=None,revid=12):
    x={'query':{'pages':[{'pageid':1,'ns':0,'title':'Source','revisions':[revision(revid)],'links':[{'ns':0,'title':t} for t in links]}]}}
    if continuation:x['continue']=continuation
    return x,{'sha256':'fixture'}


class CrawlTests(unittest.TestCase):
    def test_html_body_context_position_and_repetition(self):
        p=parse_article(HTML,BASE,{'categoría'})
        self.assertEqual(p['body_targets'],['Alpha','Beta'])
        self.assertEqual(p['all_article_targets'],['Alpha','Beta','Box','Reference'])
        eligible=[r for r in p['occurrences'] if not r['excluded_context'] and not r['redlink']]
        self.assertEqual([r['body_link_position'] for r in eligible],[0,1,2])
        self.assertEqual(eligible[0]['anchor_text'],'Alpha & more')
        self.assertEqual(eligible[1]['section'],'History')
        self.assertEqual(eligible[2]['paragraph_index'],2)
        self.assertEqual(p['revision_id'],12)
        self.assertEqual(p['page_id'],1)

    def test_url_origin_fragment_namespace_and_case(self):
        self.assertEqual(article_target('/wiki/Star_Trek:_Voyager#x',BASE,{'categoría'}),'Star Trek: Voyager')
        for u in ['#local','javascript:alert(1)','https://evil.example/wiki/A','//en.wikipedia.org/wiki/A','/wiki/A?action=edit','/wiki/Categor%C3%ADa:X']:
            self.assertIsNone(article_target(u,BASE,{'categoría'}))
        self.assertEqual(article_target('/wiki/iPhone',BASE,set()),'iPhone')

    def test_missing_dom_is_not_an_empty_crawled_graph(self):
        self.assertEqual(parse_article('<p>Access denied</p>',BASE,set())['body_roots'],0)

    def test_revision_mismatch_has_no_agreement_metric(self):
        a={'title':'Source','targets':['Alpha'],'revision_id':99,'page_id':1}
        h=parse_article(HTML,BASE,{'categoría'})
        self.assertIsNone(compare(a,h)['body_jaccard'])
        a['revision_id']=12
        self.assertEqual(compare(a,h)['body_jaccard'],.5)

    def test_api_pagination_and_duplicate_target(self):
        c=Mock();c.api.side_effect=[response(['Alpha'],{'continue':'||','plcontinue':'next'}),response(['Alpha','Beta'])]
        a=api_article(c,'Source')
        self.assertEqual(a['targets'],['Alpha','Beta'])
        self.assertEqual(c.api.call_args.kwargs['plcontinue'],'next')

    def test_api_repeated_continuation_fails(self):
        c=Mock();c.api.return_value=response(['Alpha'],{'plcontinue':'same'})
        with self.assertRaisesRegex(ValueError,'Repeated'):api_article(c,'Source')

    def test_api_revision_change_during_pagination_fails(self):
        c=Mock();c.api.side_effect=[response(['Alpha'],{'plcontinue':'next'}),response(['Beta'],revid=13)]
        with self.assertRaisesRegex(ValueError,'Revision changed'):api_article(c,'Source')

    def test_historical_cutoff_and_identity(self):
        c=Mock();c.api.return_value=response([])
        self.assertEqual(historical_article(c,1,'2018-03-01T00:00:00Z')['revision_id'],12)
        with self.assertRaisesRegex(ValueError,'cutoff'):historical_article(c,1,'2016-01-01T00:00:00Z')
        with self.assertRaisesRegex(ValueError,'identity'):historical_article(c,2,'2018-01-01T00:00:00Z')

    def test_transport_budget_and_origin(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=Client(Path(tmp),'es.wikipedia.org',max_requests=0)
            with self.assertRaisesRegex(CrawlStop,'budget'):c.fetch('https://es.wikipedia.org/w/api.php','api')
            with self.assertRaisesRegex(ValueError,'origin'):c.fetch('https://example.com/x','api')
            with self.assertRaisesRegex(CrawlStop,'robots'):c.fetch(BASE,'html')

    def test_cache_tampering_rejected_without_network(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            c=Client(Path(tmp),'es.wikipedia.org');url='https://es.wikipedia.org/w/api.php'
            key=hashlib.sha256(url.encode()).hexdigest();base=Path(tmp)/'raw'
            (base/f'{key}.body').write_bytes(b'changed')
            (base/f'{key}.json').write_text(json.dumps({'sha256':'wrong'}))
            with self.assertRaisesRegex(ValueError,'Cached body changed'):c.fetch(url,'api')
            self.assertEqual(c.calls,0)

    def test_forbidden_is_not_retried(self):
        with tempfile.TemporaryDirectory() as tmp,patch('wikinav.crawl.time.sleep'):
            c=Client(Path(tmp),'es.wikipedia.org');c.opener=Mock()
            c.opener.open.side_effect=HTTPError(BASE,403,'Forbidden',{},None)
            with self.assertRaisesRegex(CrawlStop,'no access-control bypass'):c.fetch('https://es.wikipedia.org/w/api.php','api')
            self.assertEqual(c.opener.open.call_count,1)

    def test_respects_long_retry_after_without_waiting(self):
        with tempfile.TemporaryDirectory() as tmp,patch('wikinav.crawl.time.sleep'):
            c=Client(Path(tmp),'es.wikipedia.org');c.opener=Mock()
            c.opener.open.side_effect=HTTPError(BASE,429,'Rate limit',{'Retry-After':'120'},None)
            with self.assertRaisesRegex(CrawlStop,'resume later'):c.fetch('https://es.wikipedia.org/w/api.php','api')
            self.assertEqual(c.opener.open.call_count,1)

    def test_fixture_end_to_end_and_resume(self):
        class FakeClient:
            calls=0
            host='es.wikipedia.org'
            def __init__(self,*a):pass
            def robots(self):return {}
            def api(self,**kwargs):
                if 'meta' in kwargs:return {'query':{'namespaces':{'0':{'id':0,'name':''},'14':{'id':14,'name':'Categoría'}},'namespacealiases':[]}},{}
                return response(['Alpha','Beta'])
            def fetch(self,*a):return HTML.encode(),{'sha256':'fixture'}
        with tempfile.TemporaryDirectory() as tmp,patch('wikinav.crawl.Client',FakeClient):
            root=Path(tmp);config=root/'c.toml';out=root/'out'
            config.write_text('edition="es"\nmode="both"\nmax_pages=1\nmax_depth=1\nmax_requests=5\nmax_response_bytes=20000\ndelay_seconds=1.0\nseeds=["Source"]\nhistorical_cutoff="2018-03-01T00:00:00Z"\n')
            r=run(config,out);self.assertEqual(r['completed_pages'],1);self.assertEqual(r['frontier_remaining'],2)
            self.assertTrue(r['comparisons'][0]['matched_revision'])
            self.assertEqual(run(config,out)['completed_pages'],1)
            config.write_text(config.read_text().replace('max_pages=1','max_pages=2'))
            with self.assertRaisesRegex(ValueError,'Changed crawl'):run(config,out)

    def test_slow_api_sets_five_second_next_pause(self):
        with tempfile.TemporaryDirectory() as tmp,patch('wikinav.crawl.time.sleep'),patch('wikinav.crawl.time.monotonic',side_effect=[10.,10.,12.]):
            c=Client(Path(tmp),'es.wikipedia.org');r=Mock();r.read.return_value=b'{}';r.status=200;r.headers={}
            manager=Mock();manager.__enter__=Mock(return_value=r);manager.__exit__=Mock(return_value=False)
            c.opener=Mock();c.opener.open.return_value=manager
            c.fetch('https://es.wikipedia.org/w/api.php','api')
            self.assertEqual(c.next_delay,5.)

    def test_rejects_nonfinite_delay_and_naive_cutoff(self):
        import tomllib
        cfg=tomllib.loads(Path('configs/crawl-pilot.toml').read_text())
        cfg['delay_seconds']=float('nan')
        with self.assertRaises(ValueError):validate(cfg)
        cfg['delay_seconds']=1.;cfg['historical_cutoff']='2018-03-01'
        with self.assertRaisesRegex(ValueError,'timezone'):validate(cfg)

    def test_raw_replay_export_preserves_unknown_frontier(self):
        import io
        from wikinav.crawl_export import export
        class Reply(io.BytesIO):
            status=200
            headers={}
        site={'query':{'namespaces':{'0':{'id':0,'name':''},'14':{'id':14,'name':'Categoría'}},'namespacealiases':[]}}
        bodies=[json.dumps(site).encode(),b'User-agent: *\nAllow: /wiki/\n',json.dumps(response(['Alpha','Beta'])[0]).encode(),HTML.encode()]
        with tempfile.TemporaryDirectory() as tmp,patch('wikinav.crawl.time.sleep'),patch('urllib.request.OpenerDirector.open',side_effect=lambda *a,**kw:Reply(bodies.pop(0))):
            root=Path(tmp);cfg=root/'c.toml'
            cfg.write_text('edition="es"\nmode="both"\nmax_pages=1\nmax_depth=1\nmax_requests=4\nmax_response_bytes=20000\ndelay_seconds=1.0\nseeds=["Source"]\n')
            run(cfg,root/'raw')
            summary=export(root/'raw',root/'processed',root/'report')
            self.assertTrue(summary['raw_parsing_replay_verified'])
            self.assertEqual(summary['html_edges'],2)
            self.assertEqual(summary['html_occurrences'],6)
            self.assertEqual(summary['unresolved_target_nodes'],2)
            self.assertEqual(summary['frontier_remaining'],2)

    def test_collectors_can_run_independently(self):
        import io
        class Reply(io.BytesIO):
            status=200
            headers={}
        site={'query':{'namespaces':{'0':{'id':0,'name':''}},'namespacealiases':[]}}
        for mode in ('api','html'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp,patch('wikinav.crawl.time.sleep'):
                bodies=([json.dumps(site).encode(),json.dumps(response(['Alpha'])[0]).encode()] if mode=='api' else [b'User-agent: *\nAllow: /wiki/\n',HTML.encode()])
                root=Path(tmp);cfg=root/'c.toml'
                cfg.write_text(f'edition="es"\nmode="{mode}"\nmax_pages=1\nmax_depth=0\nmax_requests=2\nmax_response_bytes=20000\ndelay_seconds=1.0\nseeds=["Source"]\n')
                with patch('urllib.request.OpenerDirector.open',side_effect=lambda *a,**kw:Reply(bodies.pop(0))):
                    result=run(cfg,root/'raw')
                self.assertEqual(result['completed_pages'],1)
                record=json.loads(next((root/'raw/pages').glob('*.json')).read_text())
                self.assertIn(mode,record)
                self.assertNotIn('html' if mode=='api' else 'api',record)

    def test_known_aliases_collapse_without_losing_occurrence_count(self):
        from wikinav.crawl_export import collapse_edges
        rows=[{'source':'1','target':'2','target_title':'Alias','occurrence_count':2,'first_body_link_position':5,'first_section':'Later','in_lead':False},
              {'source':'1','target':'2','target_title':'Canonical','occurrence_count':1,'first_body_link_position':0,'first_section':'lead','in_lead':True}]
        edge=collapse_edges(rows,'occurrence_count')[0]
        self.assertEqual(edge['occurrence_count'],3)
        self.assertEqual(edge['first_body_link_position'],0)
        self.assertEqual(edge['target_titles'],['Alias','Canonical'])
        api=[{'source':'1','target':'2','target_title':'Alias','weight':1},{'source':'1','target':'2','target_title':'Canonical','weight':1},{'source':'2','target':'1','target_title':'Reverse','weight':1}]
        self.assertEqual(len(collapse_edges(api)),2)
        self.assertEqual(collapse_edges(api)[0]['weight'],1)
