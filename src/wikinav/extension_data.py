"""Read-only historical full-graph export and isolated extension label ingestion."""
import gc
import json
from pathlib import Path
import resource
import time
import duckdb
import numpy as np
from scipy import sparse
from .study_data import StudyData, literal, click_table
from .utils import file_digest, write_json


def build_full(prepared, output):
    if (output/'manifest.json').exists():
        manifest=json.loads((output/'manifest.json').read_text())
        if manifest['prepared_manifest_sha256']!=file_digest(prepared/'manifest.json'):raise ValueError('Prepared input changed')
        for name,h in manifest['artifacts'].items():
            if file_digest(output/name)!=h:raise ValueError('Full artifact changed')
        return manifest
    output.mkdir(parents=True,exist_ok=False);start=time.perf_counter()
    con=duckdb.connect(str(prepared/'study.duckdb'),read_only=True)
    con.execute("SET memory_limit='1GB'");con.execute('SET threads=2')
    ids=con.execute('SELECT id FROM pages WHERE id=canonical ORDER BY id').fetchnumpy()['id']
    np.save(output/'ids.npy',ids)
    report={}
    for name,query in [('H','SELECT s,t FROM h ORDER BY s,t'),('C','SELECT s,t,n FROM train ORDER BY s,t')]:
        print('full export',name,flush=True)
        rows=con.execute(query).fetchnumpy()
        si=np.searchsorted(ids,rows['s']);ti=np.searchsorted(ids,rows['t'])
        if not np.array_equal(ids[si],rows['s']) or not np.array_equal(ids[ti],rows['t']):raise ValueError('Unknown canonical ID')
        weights=rows['n'] if name=='C' else np.ones(len(si),dtype=np.uint8)
        a=sparse.csr_matrix((weights,(si.astype(np.int32),ti.astype(np.int32))),shape=(len(ids),len(ids)))
        del rows,si,ti,weights;gc.collect()
        sparse.save_npz(output/(name+'.npz'),a)
        report[name]={'nodes':len(ids),'edges':a.nnz,'csr_bytes':a.data.nbytes+a.indices.nbytes+a.indptr.nbytes}
        del a;gc.collect()
    con.close()
    result={'prepared_manifest_sha256':file_digest(prepared/'manifest.json'),'graphs':report,
            'seconds':time.perf_counter()-start,'max_rss_native_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            'artifacts':{p.name:file_digest(p) for p in output.iterdir() if p.is_file()}}
    write_json(output/'manifest.json',result);return result


def load_full(folder, source_ids, h=None):
    ids=np.load(folder/'ids.npy')
    adjacency=sparse.load_npz(folder/'H.npz') if h is None else h
    counts=sparse.load_npz(folder/'C.npz')
    q=np.searchsorted(ids,np.array(source_ids,dtype=np.int64))
    if not np.array_equal(ids[q],np.array(source_ids,dtype=np.int64)):raise ValueError('Unknown query')
    features={'out_degree_full':np.diff(adjacency.indptr),
              'in_degree_full':np.asarray(adjacency.sum(axis=0)).ravel(),
              'traffic':np.asarray(counts.sum(axis=1)).ravel(),
              'popularity':np.asarray(counts.sum(axis=0)).ravel()}
    strings=[str(i) for i in ids]
    return StudyData(strings,[],adjacency,counts,list(map(int,q)),features,
                     json.loads((folder/'manifest.json').read_text()))


def source_panels(prepared, original_ids):
    con=duckdb.connect(str(prepared/'study.duckdb'),read_only=True)
    panels={'2026':list(original_ids)};seen=list(original_ids)
    for seed in (2027,2028):
        exclusion=','.join(str(int(i)) for i in seen)
        rows=con.execute(f'''SELECT s FROM
            (SELECT *,row_number() OVER(PARTITION BY stratum ORDER BY
             sha256(concat('{seed}',':',s::VARCHAR)),s) sample_rank
             FROM query_pool WHERE s NOT IN ({exclusion}))
             WHERE sample_rank<=50 ORDER BY s''').fetchall()
        panel=[str(s) for s, in rows]
        if len(panel)!=200 or set(panel)&set(seen):raise ValueError('Invalid disjoint panel')
        panels[str(seed)]=panel;seen.extend(panel)
    con.close();return panels


class PeriodStore:
    """Isolated DB: old canonical mapping immutable; call period only when authorized by stage."""
    def __init__(self, prepared, raw, path):
        self.raw=raw;self.prepared=prepared
        self.con=duckdb.connect(str(path));self.con.execute("SET memory_limit='1GB'")
        self.con.execute('SET threads=2');self.con.execute("SET TimeZone='UTC'")
        self.con.execute(f'ATTACH {literal(prepared/"study.duckdb")} AS historical (READ_ONLY)')
        self.con.execute('CREATE OR REPLACE TEMP VIEW titlemap AS SELECT * FROM historical.titlemap')
        self.con.execute('CREATE TABLE IF NOT EXISTS months(month VARCHAR,s BIGINT,t BIGINT,n BIGINT)')
        self.con.execute('CREATE TABLE IF NOT EXISTS loaded(month VARCHAR PRIMARY KEY,audit VARCHAR)')
        self.audits={}

    def period(self, month, query_ids):
        existing=self.con.execute('SELECT audit FROM loaded WHERE month=?',[month]).fetchone()
        if existing:
            audit=json.loads(existing[0])
            if audit['input_sha256']!=file_digest(self.raw/f'clickstream-eswiki-{month}.tsv.gz'):raise ValueError('Raw period changed')
        else:
            path=self.raw/f'clickstream-eswiki-{month}.tsv.gz'
            # Transaction keeps parsed monthly counts and audit atomic.
            self.con.execute('BEGIN TRANSACTION')
            try:
                audit=click_table(self.con,path,10,'quarantine');audit['input_sha256']=file_digest(path)
                self.con.execute(f'''INSERT INTO months SELECT {literal(month)},source,target,sum(n)
                    FROM matched WHERE type='link' AND source IS NOT NULL AND target IS NOT NULL
                    AND source!=target GROUP BY source,target''')
                self.con.execute('CREATE TABLE IF NOT EXISTS labels(month VARCHAR,s BIGINT,target VARCHAR,n BIGINT)')
                self.con.execute(f'''INSERT INTO labels SELECT {literal(month)},source,
                    CASE WHEN target IS NULL THEN concat('oov:',curr) ELSE target::VARCHAR END,sum(n)
                    FROM matched WHERE type='link' AND source IS NOT NULL AND (target IS NULL OR source!=target)
                    GROUP BY source,target,curr''')
                self.con.execute('INSERT INTO loaded VALUES (?,?)',[month,json.dumps(audit)])
                self.con.execute('COMMIT')
            except Exception:
                self.con.execute('ROLLBACK');raise
        self.audits[month]=audit
        query=','.join(str(int(i)) for i in query_ids)
        rows=self.con.execute(f'SELECT s,target,sum(n) FROM labels WHERE month=? AND s IN ({query}) GROUP BY s,target',[month]).fetchall()
        labels={}
        for s,t,n in rows:labels.setdefault(str(s),{})[t]=int(n)
        return labels,audit

    def training(self, data, months):
        for month in months:self.period(month,[data.ids[data.queries[0]]])
        condition=','.join(map(literal,months))
        rows=self.con.execute(f'SELECT s,t,sum(n) n FROM months WHERE month IN ({condition}) GROUP BY s,t').fetchnumpy()
        ids=np.array(data.ids,dtype=np.int64);order=np.argsort(ids);sorted_ids=ids[order]
        si=np.searchsorted(sorted_ids,rows['s']);ti=np.searchsorted(sorted_ids,rows['t'])
        sm=si<len(ids);tm=ti<len(ids)
        sm[sm]&=sorted_ids[si[sm]]==rows['s'][sm];tm[tm]&=sorted_ids[ti[tm]]==rows['t'][tm]
        use=sm&tm
        counts=sparse.csr_matrix((rows['n'][use],(order[si[use]],order[ti[use]])),shape=data.adjacency.shape)
        pop=dict(self.con.execute(f'SELECT t,sum(n) FROM months WHERE month IN ({condition}) GROUP BY t').fetchall())
        traffic=dict(self.con.execute(f'SELECT s,sum(n) FROM months WHERE month IN ({condition}) GROUP BY s').fetchall())
        features={**data.features,'popularity':np.array([pop.get(int(i),0) for i in data.ids]),
                  'traffic':np.array([traffic.get(int(i),0) for i in data.ids])}
        return StudyData(data.ids,data.titles,data.adjacency,counts,data.queries,features,data.manifest)

    def close(self):self.con.close()


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,default=Path('data/processed/study-v2'))
    p.add_argument('--output',type=Path,default=Path('data/processed/full-extension'))
    a=p.parse_args();print(json.dumps(build_full(a.prepared,a.output),indent=2))
