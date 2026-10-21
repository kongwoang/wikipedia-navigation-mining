"""Render auditable Markdown tables/cases from the published frozen bundle."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'reports/generated'
OUT = ROOT / 'reports'
read = lambda name: json.loads((BUNDLE / name).read_text())
rows = list(csv.DictReader((BUNDLE / 'tables/metrics.csv').open()))
summary = read('summary.json')
payload = read('demo_data.json')
models = summary['main_models']

def table(headers, values):
    def cell(v):
        if isinstance(v, float):
            return f'{v:.4f}'
        return str(v).replace('|', '\\|').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(map(cell, headers)) + ' |',
                      '| ' + ' | '.join('---' for _ in headers) + ' |'] +
                     ['| ' + ' | '.join(map(cell, row)) + ' |' for row in values]) + '\n'

def metric(month, model, denom='all', aggregation='macro'):
    return next(r for r in rows if (r['month'], r['model'], r['denominator'], r['aggregation']) ==
                (month, model, denom, aggregation))

def csvtable(name, columns):
    rs = list(csv.DictReader((BUNDLE / 'tables' / name).open()))
    return table(columns, [[r[c] for c in columns] for r in rs])

parts = ['# Bảng kết quả từ frozen study-v3\n',
         'Sinh bằng `python3 scripts/build_report_tables.py`. Số làm tròn 4 chữ số trong bảng chính; CSV giữ precision gốc. Không dùng bảng test để chọn hyperparameters.\n']
for month in payload['months']:
    cols = ['recall@5', 'recall@10', 'recall@20', 'mrr@10', 'ndcg@10']
    parts += [f'## {month} — full observable, macro\n',
              table(['Model'] + cols, [[m] + [float(metric(month, m)[c]) for c in cols] for m in models])]
parts += ['## Denominator và traffic weighting — NDCG@10\n',
          'Conditional traffic-weighted dùng **full source label mass** để cân nguồn; chỉ nguồn có eligible label được đưa vào conditional average.\n',
          table(['Tháng','Model','Full macro','Conditional macro','Full weighted','Conditional weighted'],
                [[mo,m] + [float(metric(mo,m,d,a)['ndcg@10']) for d,a in
                           [('all','macro'),('conditional','macro'),('all','traffic_weighted'),('conditional','traffic_weighted')]]
                 for mo in payload['months'] for m in ['M1B_backoff','M3_ppr_h','M4H_ppr_wh','M6B_fusion','M5H_node2vec','M5W_node2vec']])]
parts += ['## Primary contrast — số nguồn thắng/hòa/thua\n',
          'M6B−M1B, full NDCG@10; tie tolerance 1e-12, chỉ nguồn có observed labels.\n']
wins = []
for mo in payload['months']:
    differences = [q['metrics'][mo]['M6B_fusion']['all']['ndcg@10']-q['metrics'][mo]['M1B_backoff']['all']['ndcg@10']
                   for q in payload['queries'] if q['metrics'][mo]['M1B_backoff']['all']['ndcg@10'] is not None]
    wins.append([mo,len(differences),sum(x>1e-12 for x in differences),sum(abs(x)<=1e-12 for x in differences),sum(x< -1e-12 for x in differences)])
parts += [table(['Tháng','N','Thắng','Hòa','Thua'],wins),'## Paired source bootstrap\n',
          csvtable('paired_bootstrap.csv',['month','contrast','delta','ci_low','ci_high','sources'])]
parts += ['## A8 — trailing history, full macro NDCG@10\n',
          table(['Tháng','Model','1 tháng','2 tháng','3 tháng'],
                [[mo,label]+[float(metric(mo,f'A8_{prefix}_{n}month')['ndcg@10']) for n in (1,2)]+[float(metric(mo,base)['ndcg@10'])]
                 for mo in payload['months'] for label,prefix,base in [('Markov','M1_local','M1_local'),('Backoff','M1B_backoff','M1B_backoff'),('Fusion','fusion','M6B_fusion')]])]
parts += ['## A7 — train-unobserved transitions, original rankings\n',
          'Tập con được xác định bằng train counts; không rerank sau khi biết future labels. Missing train counts có thể do suppression.\n']
rs=list(csv.DictReader((BUNDLE/'tables/transition_sparsity.csv').open()))
parts += [table(['Tháng','Model','Sources','Pairs','Mass','Macro Recall@10','Mass Recall@10'],
                [[r['month'],r['model'],r['sources'],r['pairs'],r['mass'],float(r['macro_recall@10']),float(r['mass_recall@10'])]
                 for r in rs if r['edge_group']=='unobserved' and r['model'] in ['M1B_backoff','M3_ppr_h','M6B_fusion','M5H_node2vec','M5W_node2vec']]),
          '## Seed variability — auxiliary, không phải source CI\n',
          csvtable('embedding_seed_stability.csv',['month','model','seeds','mean','std_sample','min','max']),
          '## Coverage\n',csvtable('coverage.csv',['month','queries','q_all','q_conditional','label_pairs','label_mass','eligible_pairs','eligible_mass','mass_candidate_coverage']),
          '## Nhóm nguồn theo traffic — observability\n']
rs=list(csv.DictReader((BUNDLE/'tables/group_coverage.csv').open()))
parts += [table(['Tháng','Nhóm','Sampled','Observed','Conditional','Future mass'],
                [[r[c] for c in ['month','group','sampled_sources','observable_sources','conditional_sources','label_mass']]
                 for r in rs if r['axis']=='traffic']),
          '## Selected configurations\n',csvtable('selected_parameters.csv',['model','parameters']),
          '\nBảng runtime, subgroup intervals, graph statistics, training distributions và toàn bộ metrics nằm trong [generated/tables](generated/tables/).\n']
(OUT/'RESULT_TABLES.md').write_text('\n'.join(parts))

narratives = {
'PPR_gain':'Training chỉ quan sát Danza contemporánea (62). May có thêm Merce Cunningham (16); PPR đưa target này lên Top-10 trong khi tie-order của Markov không làm được. Đây là minh họa topology xếp hạng phần chưa có count, không chứng minh mọi rare source đều được lợi.',
'Markov_gain':'Remora remora có 63 training clicks và 31 May clicks, đứng đầu Markov. PPR ưu tiên Animalia/Pez và để target này ngoài Top-10. Pattern phù hợp giả thuyết hub bias; ta không có dữ liệu exposure để suy nguyên nhân hành vi.',
'Hybrid_gain':'Ba destinations có training counts vẫn ở đầu fusion. Topology thay đổi phần đuôi chưa có count, giúp đưa thêm future targets vào Top-10. So bảng dưới để thấy gain không đến từ thay candidate set; đây là case được chọn vì gain lớn nhất, không phải average effect.',
'Hybrid_failure':'Fusion giữ ba vị trí đầu như Markov nhưng thay phần đuôi: Parque Cinegético Experimental de El Hosquillo có 12 future clicks và không có published training count. Topology có thể đẩy một candidate hữu ích xuống dưới Top-10; đây là lý do không giả định fusion luôn thắng.',
'Many_links':'1944 có 485 candidates, tạo nhiều cạnh tranh ở Top-10. Các future destinations 1945/1947/1943 không thuộc historical candidate set. Full metrics giữ những labels này; score thấp hơn không hoàn toàn do ranker. PPR ưu tiên các country hubs trong khi local counts giữ các destinations cụ thể.',
'Low_traffic':'Chỉ 10 published training clicks đến Gołąbki; May quan sát Dolma (15), chưa thấy trong training. Markov/PPR/fusion đều miss Top-10, embedding-H tìm được Dolma. Chọn source vì low traffic, không đổi knobs riêng cho case.',
'Fixed_hash_example':'Th1 là case chọn bằng stable hash, tránh chỉ kể extreme wins. Markov/fusion giữ các targets có training counts; thứ tự May khác training ở IL-2 và Linfocito T CD4+. Improvement nhỏ ở đây không đủ chứng minh gain ổn định.'}
cs=['# Case studies — bằng chứng từ predictions thật\n',
    'Cases chọn theo protocol sau test để giải thích, không dùng tuning. Mọi bảng ở May 2018. “—” nghĩa không có published count; không phải reliable zero. Top-10 chỉ chứa shared historical candidates.\n']
byid={q['id']:q for q in payload['queries']}
for case in payload['cases']:
    q=byid[case['source']]
    cs += [f"## {q['title']} — {case['reason']}\n",
           f"ID `{q['id']}`; out-degree **{q['degree']}**; full outgoing published training mass **{q['traffic']}**.\n",
           narratives[case['reason']]+'\n',
           table(['Model','Full NDCG@10','Recall@10'],[[m,q['metrics']['2018-05'][m]['all']['ndcg@10'],q['metrics']['2018-05'][m]['all']['recall@10']] for m in ['M1B_backoff','M3_ppr_h','M5H_node2vec','M6B_fusion']])]
    truth=[d for d in q['destinations'].values() if d['future']['2018-05']]
    total=sum(d['future']['2018-05'] for d in truth)
    cs += ['### Future distribution (tối đa 15 targets lớn nhất)\n',
           table(['Target','Train count','Future count','Future share','Candidate'],
                 [[d['title'],d['train_count'] or '—',d['future']['2018-05'],f"{d['future']['2018-05']/total:.2%}",'Có' if d['hyperlink'] else 'Không']
                  for d in sorted(truth,key=lambda x:-x['future']['2018-05'])[:15]])]
    for model in ['M1B_backoff','M3_ppr_h','M5H_node2vec','M6B_fusion']:
        pred=q['predictions'][model]
        cs += [f'### {model} — Top-10\n',
               table(['Rank','Target','Train','Future','Score'],
                     [[i,q['destinations'][t]['title'],q['destinations'][t]['train_count'] or '—',q['destinations'][t]['future']['2018-05'] or '—',float(pred['scores'][t])]
                      for i,t in enumerate(pred['ranked'][:10],1)])]
cs += ['Các raw scores không cùng scale giữa các model. Chỉ M6B trộn sau candidate normalization. [Demo](generated/demo.html) cho phép đổi month/model/denominator; trên GitHub cần tải HTML về rồi mở.\n']
(OUT/'CASE_STUDIES.md').write_text('\n'.join(cs))
print('Wrote reports/RESULT_TABLES.md and reports/CASE_STUDIES.md')
