"""Standalone offline research demo generated from frozen real-model artifacts."""

import json
from pathlib import Path


def build(folder: Path):
    payload=json.loads((folder/'demo_data.json').read_text())
    encoded=json.dumps(payload,ensure_ascii=False).replace('<','\\u003c')
    html=TEMPLATE.replace('__PAYLOAD__',encoded)
    (folder/'demo.html').write_text(html,encoding='utf-8')


TEMPLATE='''<!doctype html>
<html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wikipedia Navigation · Frequency × Topology</title>
<style>
:root{color-scheme:light;--ink:#18313a;--muted:#526d76;--accent:#117b83;--line:#dbe5e8;--paper:#f3f7f8}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.5 system-ui,sans-serif}
header{background:#123b46;color:white;padding:30px max(24px,calc((100vw - 1400px)/2));border-bottom:6px solid #64c5be}
header p{max-width:950px;color:#d0e7ea;margin:8px 0}h1{font-size:30px;line-height:1.2;margin:4px 0 14px}
.eyebrow{font-size:12px;letter-spacing:2px;color:#94dbd4;text-transform:uppercase}
main{max-width:1450px;margin:auto;padding:24px}h2{font-size:19px;margin:0 0 12px}h3{font-size:16px;margin:0}
.card{background:white;border:1px solid var(--line);border-radius:12px;padding:20px;box-shadow:0 2px 4px #123b4605}
.controls{display:flex;flex-wrap:wrap;gap:15px;align-items:end}label{display:block;font-size:12px;font-weight:650;color:var(--muted)}
input,select{font:inherit;border:1px solid #a8bcc4;border-radius:7px;padding:9px;background:white;color:var(--ink);max-width:100%}
input{width:220px}#source{min-width:300px}.stats{display:flex;flex-wrap:wrap;gap:10px;margin:15px 0}.stat{background:#e5f1f2;border-radius:8px;padding:10px 16px}.stat b{font-size:21px;display:block}
.note{font-size:12px;color:var(--muted);margin:12px 0}.grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:20px 0}
.tag{display:inline-block;border-radius:15px;background:#e0f2ed;color:#165d4f;padding:2px 8px;font-size:11px}.missing{background:#fff0df;color:#8c5111}
table{width:100%;border-collapse:collapse;font-size:12px}th{text-align:left;font-size:11px;color:var(--muted);font-weight:600;background:#f7fafb}td,th{padding:8px 6px;border-bottom:1px solid #edf1f2}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}td.title{max-width:260px;overflow-wrap:anywhere}.metric{font-size:12px;color:var(--accent);padding:10px 0;font-weight:650}
details{margin-top:15px}summary{cursor:pointer;font-weight:650}.case{display:inline-block;margin:3px;padding:5px 10px;border:1px solid var(--line);border-radius:6px;background:white;cursor:pointer;color:var(--accent)}
footer{color:var(--muted);font-size:12px;padding:24px 0}.scroll{overflow:auto}button:focus,select:focus,input:focus{outline:3px solid #79c9d3;outline-offset:2px}
@media(max-width:850px){.grid{grid-template-columns:1fr}main{padding:12px}h1{font-size:24px}#source{min-width:0;width:100%}.controls>div{flex:1 1 220px}}
</style>
<header><div class="eyebrow">Wikipedia Navigation Mining · Historical study</div><h1>Khi nào topology bổ sung thông tin cho click frequency?</h1>
<p>So sánh dự đoán đã khóa của các model thật trên cùng outgoing candidates. Click counts thuộc Spanish Wikipedia 2018; graph là mẫu lấy từ snapshot 01/03/2018.</p></header>
<main><section class="card"><div class="controls">
<div><label for="search">Tìm bài trong 200 nguồn đã chọn</label><input id="search" type="search" placeholder="Nhập tên bài…"></div>
<div style="flex:1"><label for="source">Source article</label><select id="source"></select></div>
<div><label for="month">Held-out period</label><select id="month"></select></div>
<div><label for="denom">Mẫu số đánh giá</label><select id="denom"><option value="all">Full observable labels</option><option value="conditional">Within candidates</option></select></div></div>
<div class="stats" id="stats"></div><p class="note">Train: tháng 01–03/2018 · Validation: tháng 04 · Test: tháng 05–06. Thay tháng chỉ đổi evidence/metrics hiển thị, không thay predictions. Dấu “—” là không có count quan sát được, không chứng minh zero clicks.</p>
<details><summary>Case studies được chọn sau test để phân tích</summary><div id="cases"></div><p class="note">Các cases minh họa lỗi và khác biệt; không đại diện cho hiệu quả trung bình.</p></details></section>
<section class="grid" id="models"></section>
<section class="card"><h2>Future destination distribution & candidate coverage</h2><p class="note">Danh sách này dùng held-out labels để kiểm tra dự đoán, không làm input cho model. Target ngoài candidates vẫn nằm trong full denominator.</p><div class="scroll"><table><thead><tr><th>Destination</th><th>Hyperlink candidate</th><th class="num">Train count</th><th class="num">Future count</th><th class="num">Future mass share</th></tr></thead><tbody id="truth"></tbody></table></div></section>
<footer>Source-conditioned ranking, không phải user personalization. PPR/Node2Vec chạy trên induced sample graph; query candidates được giữ đầy đủ nhưng intermediate nodes mất boundary edges. Đây là offline retrospective evaluation, không phải deployed A/B test. Data: Wikimedia Clickstream (CC0), WikiLinkGraphs và supporting data (CC BY 4.0).</footer></main>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
const data=JSON.parse(document.getElementById('payload').textContent),$=id=>document.getElementById(id);
const esc=x=>String(x).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=x=>x==null?'N/A':Number(x).toFixed(4), count=x=>x?Number(x).toLocaleString('vi-VN'):'—';
const active=['M1B_backoff','M3_ppr_h','M5H_node2vec','M6B_fusion'];
function populate(){const prev=$('source').value,query=$('search').value.toLocaleLowerCase();const qs=data.queries.filter(q=>q.title.toLocaleLowerCase().includes(query));$('source').innerHTML=qs.map(q=>`<option value="${esc(q.id)}">${esc(q.title)}</option>`).join('');if(qs.some(q=>q.id===prev))$('source').value=prev;render()}
function render(){const q=data.queries.find(q=>q.id===$('source').value);if(!q){$('models').innerHTML='<p>Không có nguồn phù hợp.</p>';$('truth').innerHTML='';$('stats').innerHTML='';return}
const month=$('month').value,denom=$('denom').value;const truth=Object.entries(q.destinations).filter(([id,d])=>d.future[month]>0).sort((a,b)=>b[1].future[month]-a[1].future[month]);const mass=truth.reduce((s,[id,d])=>s+d.future[month],0),eligible=truth.reduce((s,[id,d])=>s+(d.hyperlink?d.future[month]:0),0);
$('stats').innerHTML=[['Candidates',q.degree],['Training outgoing mass',count(q.traffic)],['Observed future pairs',truth.length],['Candidate mass coverage',mass?(100*eligible/mass).toFixed(1)+'%':'N/A']].map(([label,v])=>`<div class="stat">${esc(label)}<b>${esc(v)}</b></div>`).join('');
$('models').innerHTML=active.map((model,slot)=>{const pred=q.predictions[model],metrics=q.metrics[month][model][denom];return `<article class="card"><label for="model${slot}">Model ${slot+1}</label><select id="model${slot}" data-slot="${slot}">${data.models.map(m=>`<option ${m===model?'selected':''}>${esc(m)}</option>`).join('')}</select><div class="metric">NDCG@10 ${fmt(metrics['ndcg@10'])} · Recall@10 ${fmt(metrics['recall@10'])} · MRR@10 ${fmt(metrics['mrr@10'])}</div><div class="scroll"><table><thead><tr><th>#</th><th>Destination</th><th class="num">Train</th><th class="num">Future</th><th class="num">Score</th></tr></thead><tbody>${pred.ranked.slice(0,10).map((id,i)=>{const d=q.destinations[id];return `<tr><td>${i+1}</td><td class="title">${esc(d.title)}</td><td class="num">${count(d.train_count)}</td><td class="num">${count(d.future[month])}</td><td class="num">${Number(pred.scores[id]).toPrecision(4)}</td></tr>`}).join('')}</tbody></table></div></article>`}).join('');
document.querySelectorAll('[data-slot]').forEach(select=>select.addEventListener('change',event=>{active[Number(event.target.dataset.slot)]=event.target.value;render()}));
$('truth').innerHTML=truth.slice(0,30).map(([id,d])=>`<tr><td class="title">${esc(d.title)}</td><td><span class="tag ${d.hyperlink?'':'missing'}">${d.hyperlink?'Có':'Ngoài candidates'}</span></td><td class="num">${count(d.train_count)}</td><td class="num">${count(d.future[month])}</td><td class="num">${(100*d.future[month]/mass).toFixed(1)}%</td></tr>`).join('')||'<tr><td colspan="5">Không có future label quan sát được cho source này.</td></tr>';
}
$('month').innerHTML=data.months.map(m=>`<option>${m}</option>`).join('');
$('cases').innerHTML=data.cases.map(c=>`<button class="case" data-id="${esc(c.source)}">${esc(c.reason)} · ${esc(c.title)}</button>`).join('');
document.querySelectorAll('[data-id]').forEach(button=>button.addEventListener('click',()=>{$('search').value='';populate();$('source').value=button.dataset.id;render()}));
$('search').addEventListener('input',populate);['source','month','denom'].forEach(id=>$(id).addEventListener('change',render));populate();
</script></html>'''


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path('reports/generated'))
    build(p.parse_args().folder)
