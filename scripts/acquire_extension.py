"""Acquire opaque July--September bytes from Wikimedia's documented mirror."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wikinav.utils import file_digest
ROOT=Path('data/raw/eswiki')
SIZES={'2018-07':36083360,'2018-08':38059784,'2018-09':37187782}
def one(item):
    month,size=item; name=f'clickstream-eswiki-{month}.tsv.gz';p=ROOT/name
    url=f'https://dumps.wikimedia.your.org/other/clickstream/{month}/{name}'
    if not p.exists():
        part=p.with_suffix('.gz.part')
        subprocess.run(['curl','-fLsS','--retry','2','--max-time','600','--max-filesize','50000000',url,'-o',str(part)],check=True)
        if part.stat().st_size!=size:raise ValueError('Unexpected archive size')
        part.rename(p)
    if p.stat().st_size!=size:raise ValueError('Archive size changed')
    return {'month':month,'file':name,'url':url,'bytes':size,'sha256':file_digest(p),'license':'CC0','upstream_checksum':None}
with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(one,SIZES.items()))
manifest={'source_reference':'https://phabricator.wikimedia.org/T415193','parsed_labels':False,'files':rows}
p=ROOT/'extension-acquisition.json'
if p.exists() and json.loads(p.read_text())!=manifest:raise ValueError('Immutable acquisition manifest differs')
p.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(manifest,indent=2))
