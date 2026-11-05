"""Check deck identity and chart values against frozen study evidence, without Office."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
from presentation_data import build,ROOT

def verify():
    root=ROOT/'reports/deliverables';data=json.loads((root/'source-data.json').read_text())
    if data!=build():raise ValueError('Slide data no longer matches source evidence')
    for name,digest in json.loads((root/'manifest.json').read_text())['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Changed deliverable: '+name)
    expected=[[data['crawl']['api_edges'],data['crawl']['html_edges']],
              [data['concentration']['median_top1'],data['concentration']['median_top5']],
              [x['ndcg@10'] for x in data['metrics']],
              [float(next(x for x in data['sparsity'] if x['model']==m)['macro_recall@10']) for m in ['M1B_backoff','M3_ppr_h','M6B_fusion']]]
    ns={'c':'http://schemas.openxmlformats.org/drawingml/2006/chart'}
    with zipfile.ZipFile(root/'Wikipedia_Navigation_IT4868E.pptx') as z:
        slides=[n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',n)]
        charts=sorted(n for n in z.namelist() if re.fullmatch(r'ppt/slides/charts/chart\d+\.xml',n))
        notes=[n for n in z.namelist() if re.fullmatch(r'ppt/notesSlides/notesSlide\d+\.xml',n)]
        if len(slides)!=10 or len(notes)!=10 or len(charts)!=4:raise ValueError('Deck structure differs')
        for name,values in zip(charts,expected):
            actual=[float(x.text) for x in ET.fromstring(z.read(name)).findall('.//c:ser/c:val//c:pt/c:v',ns)]
            if actual!=[round(x,8) for x in values]:raise ValueError('Chart value mismatch: '+name)
    return {'status':'verified','slides':10,'native_charts':4,'notes':10,'scope':'File hashes and native chart values vs source artifacts; not native Office execution or HTML demo QA.'}
if __name__=='__main__':print(json.dumps(verify(),indent=2))
