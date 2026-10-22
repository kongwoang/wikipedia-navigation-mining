"""No-label full-H resource gate, using ten preselected original queries."""
import json
from pathlib import Path
import resource
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from wikinav.extension_data import load_full
from wikinav.extension_models import PreparedPPR
from wikinav.utils import digest,write_json
freeze=json.loads(Path('reports/generated/freeze.json').read_text())
queries=sorted(freeze['queries'],key=lambda s:digest([2026,s]))[:10]
start=time.perf_counter();data=load_full(Path('data/processed/full-extension'),queries)
solver=PreparedPPR(data.adjacency);prep=time.perf_counter()-start;diagnostics=[]
for s in data.queries:
 _,info=solver.solve(s,.15);diagnostics.append(info);print(data.ids[s],info,flush=True)
rss=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform!='darwin':rss*=1024
maximum=max(r['seconds'] for r in diagnostics)*200
result={'query_ids':queries,'selection':'stable hash of original query IDs; no labels','preparation_seconds':prep,
        'diagnostics':diagnostics,'max_rss_bytes':rss,'projected_200_seconds_conservative':maximum,
        'pass':rss<=8*1024**3 and maximum<=1800,'nodes':len(data.ids),'edges':data.adjacency.nnz}
write_json(Path('data/processed/full-extension/pilot.json'),result)
print(json.dumps(result,indent=2))
if not result['pass']:raise SystemExit('Full-H resource gate failed; use documented fallback')
