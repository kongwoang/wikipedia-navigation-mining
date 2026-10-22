"""Render Vietnamese tables, evidence-backed prose and cases from the sealed bundle."""
import argparse,csv,json,os
from pathlib import Path

def build(folder,output):
    output.mkdir(parents=True,exist_ok=True)
    rel=Path(os.path.relpath(folder,output)).as_posix()
    def link(path):return f'{rel}/{path}'
    def rows(name):return list(csv.DictReader((folder/'tables'/f'{name}.csv').open()))
    def f(v,n=4):return 'N/A' if v in ('',None) else f'{float(v):.{n}f}'
    metrics=rows('metrics');coverage=rows('coverage');contrasts=rows('contrasts');summary=json.loads((folder/'summary.json').read_text())
    def value(study,month,model,agg='macro'):
        return next(r for r in metrics if (r['study'],r['month'],r['model'],r['aggregation'],r['denominator'])==(study,month,model,agg,'all'))
    def mdtable(headers,body):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,row))+' |' for row in body])
    months=summary['windows'];models=['M0_global','M1_local','M1B_backoff','M2_uniform','M2D_indegree','M3_ppr_h','M4C_ppr_c','M4H_ppr_wh','M6B_fusion','topology_tie','adaptive_fusion','CycleRank','HITS']
    text=['# Kết quả mở rộng: kiểm tra cấu trúc, thời gian và cơ chế','',
          'Bổ sung ngày 22/10/2026. Original `study-v3` giữ nguyên. Extension run `extensions-v2` hoàn thành; bản `extensions-v1` dừng do lỗi SQL alias trước khi đọc July test. Đây là empirical comparative study, không survey thuần và không đề xuất thuật toán mới.','',
          '## 1. Câu trả lời chính','',
          'Historical local frequency vẫn là baseline mạnh. Mở graph đến toàn bộ historical canonical inventory không làm PPR-H vượt Markov trên các query panels được chọn. Cấu trúc liên kết thật có ích hơn các graph giữ degree nhưng đã hoán đổi cạnh; tuy vậy, “topology có thông tin” không đồng nghĩa “thêm topology sẽ cải thiện một baseline behavior mạnh”. Primary contrast tie-break−Markov trên ba tháng mới chưa có interval nào loại trừ 0.','',
          'Phần mới hoàn thành mọi nhóm thí nghiệm của quality plan: full-graph boundary, ba rolling windows, topology tie-break, năm degree-preserving perturbations, hai query panels bổ sung, bounded CycleRank và adaptive fusion. Không tăng số model để thay thế việc giải thích kết quả.','',
          '## 2. Protocol, dữ liệu và phạm vi kết luận','',
          'H/redirects cố định tại 01/03/2018. W1 train Mar–May/validation June/test July; W2 train Apr–June/validation July/test August; W3 train May–July/validation August/test September. Protocol và grids khóa trước khi parse July–September labels. Từng window lưu predictions + SHA256 trước test read; previous test trở thành future validation theo chronology đã định. Không chọn best-test seed hoặc thay grid sau W1.','',
          'Ba archives mới tải từ Your.org mirror được Wikimedia infrastructure tracker ghi nhận; origin trả 403. Bytes và local SHA256 đã lưu/pin, không gọi chúng là publisher-issued checksums. Schema/mapping audits đi cùng từng tháng. [Nguồn mirror](https://phabricator.wikimedia.org/T415193).','',
          'Boundary/null/panels dùng May–June đã xem nên là exploratory. July–September là new-period confirmation theo protocol mới, không phải external preregistration. Full H có **2.077.467 canonical nodes, 36.333.722 edges**; rolling/CycleRank/Node2Vec vẫn dùng original induced context **8.094 nodes, 319.694 edges**. Full-graph processing không biến 200/600 sampled queries thành population benchmark.','',
          'Models rolling: 13 configurations trước embeddings, cộng 2 embedding graph variants × 3 seeds = 19 configurations mỗi window. Đây không phải 19 thuật toán độc lập. Same candidate sets, full/conditional denominators, macro/traffic weighting và log-gain NDCG giữ nguyên.','',
          '## 3. Rolling results và primary contrast','',
          mdtable(['Configuration','July NDCG','August NDCG','September NDCG'],[[model]+[f(value('rolling',m,model)['ndcg@10']) for m in months] for model in models]),'',
          f"![Rolling comparison]({link('figures/01_rolling.png')})",'',
          'Tất cả số trong bảng là macro full NDCG@10 trên observable sources. Không thay N/A bằng 0. Required Recall@5/10/20, MRR@10, NDCG@10 và traffic-weighted/conditional variants có trong CSV đầy đủ.','',
          mdtable(['Test','Observable / 200','Pair coverage','Click-mass coverage','Tie−Markov Δ','Paired 95% CI'],[[m,next(r['q_all'] for r in coverage if (r['study'],r['month'],r['model'])==('rolling',m,'M1_local')),f(next(r['pair_candidate_coverage'] for r in coverage if (r['study'],r['month'],r['model'])==('rolling',m,'M1_local'))),f(next(r['mass_candidate_coverage'] for r in coverage if (r['study'],r['month'],r['model'])==('rolling',m,'M1_local'))),f(next(r['difference'] for r in contrasts if r['month']==m and r['contrast']=='topology_tie - M1_local'),6),'['+f(next(r['ci_low'] for r in contrasts if r['month']==m and r['contrast']=='topology_tie - M1_local'),6)+', '+f(next(r['ci_high'] for r in contrasts if r['month']==m and r['contrast']=='topology_tie - M1_local'),6)+']'] for m in months]),'',
          f"![Primary intervals]({link('figures/02_primary_intervals.png')})",'',
          'Cả ba CI chứa 0: chưa có reliable improvement của topology tie-break trên từng window; đây cũng không phải kiểm định equivalence. Primary comparator là unsmoothed M1_local. Secondary contrasts so M1B_backoff; hai baseline khác nhau trong August nên không trộn các delta này. Overlapping windows/source reuse không phải independent replications; không gộp 379 nguồn-tháng thành 379 người dùng độc lập. Có **115 sources** có observable labels ở cả ba tháng, báo riêng trong common-source table.','',
          mdtable(['Model','July weighted NDCG','August weighted NDCG','September weighted NDCG'],[[model]+[f(value('rolling',m,model,'traffic_weighted')['ndcg@10']) for m in months] for model in ['M1_local','M1B_backoff','M4H_ppr_wh','M6B_fusion','topology_tie','adaptive_fusion']]),'',
          '## 4. Graph boundary: thay context, giữ candidates và knobs','',
          mdtable(['Model','May induced','May full','June induced','June full'],[[model]+[f(value('boundary-'+g,m,model)['ndcg@10']) for m in ['2018-05','2018-06'] for g in ['induced','full']] for model in ['M1_local','M3_ppr_h','M4C_ppr_c','M4H_ppr_wh','M6B_fusion','topology_tie','adaptive_fusion']]),'',
          f"![Boundary control]({link('figures/03_boundary.png')})",'',
          'PPR-H tăng 0,00939 May và 0,01195 June khi mở context, nhưng paired CIs đều chứa 0. Markov giữ nguyên chính xác; fusion giảm nhẹ. Full-H PPR còn xa Markov, nên boundary loss không đủ giải thích khoảng cách trên sample này. Chỉ kiểm tra H damping0,15 và fixed fusionλ0,5, không chứng minh mọi PPR hyperparameter hoặc mọi query population đều kém. C/WH full-context cũng giữ damping0,15. Adaptiveτ chọn April riêng từng context, vì vậy adaptive row là so system-level, không pure context-only control.','',
          'Pilot không dùng labels: 10 hash-selected original queries, projected200-query solve109,09s và peakRSS1,38GiB, qua gate8GiB/30min. Full H CSR uint8 chiếm189.978.482bytes; đây là storage của một matrix, không process RSS. Whole boundary stage435,82s/maxRSS2,20GiB; rolling385,53s/1,77GiB; null74,26s/1,55GiB. Các stages chạy đồng thời trên macOS arm64 nên wall times không là isolated latency benchmark; không gồm downloads, native build hoặc report.','',
          '## 5. Degree-preserving topology control','',
          'Mỗi seed101–105 hoàn thành1.549.180 accepted directed double-edge swaps; giữ mọi in/out-degree, query outgoing candidates và node IDs, cấm duplicates/self-loops. Edge overlap còn khoảng13,3–13,4%. Degree/candidate invariants được assert; không suy finite swaps đã tạo uniform/mixed equilibrium distribution.','']
    nullbody=[]
    for m in ['2018-05','2018-06']:
        for prefix,model in [('null_ppr','M3_ppr_h'),('null_fusion','M6B_fusion')]:
            vals=[float(r['ndcg@10']) for r in metrics if r['study']=='null' and r['month']==m and r['model'].startswith(prefix) and r['denominator']=='all' and r['aggregation']=='macro']
            nullbody.append([m,model,f(value('boundary-induced',m,model)['ndcg@10']),f(min(vals)),f(max(vals))])
    text += [mdtable(['Month','Model','Real induced H','Null min','Null max'],nullbody),'',f"![Degree control]({link('figures/04_degree_null.png')})",'',
             'Real H cao hơn cả năm rewired draws trong các hàng này. Kết quả hỗ trợ vai trò của wiring beyond degree đối với PPR; không phải causal effect của hyperlinks lên hành vi người dùng, cũng không formal permutation p-value. Fusion trên null không vượt Markov: chỉ thêm graph-shaped noise không tái tạo gain nhỏ của real topology.','',
             '## 6. Query-panel sensitivity và cold labels','',
             'Hai panels2027/2028 lấy disjoint với panel2026, mỗi panel50 nguồn trong mỗi train-defined traffic stratum. Context đều là cùng full H; chọn nguồn chỉ từ historical/training information. Không thay nguồn vắng test labels bằng nguồn có nhãn.','']
    panelbody=[]
    groups=rows('panel_strata')
    for m in ['2018-05','2018-06']:
        for panel in ['2026','2027','2028']:
            cov=next(r for r in coverage if (r['study'],r['month'],r['model'])==('panel-'+panel,m,'M1_local'))
            cold=next(r for r in groups if (r['panel'],r['month'],r['stratum'],r['model'])==('panel-'+panel,m,'0','M1_local'))
            panelbody.append([m,panel,cov['q_all'],cold['observable']]+[f(value('panel-'+panel,m,model)['ndcg@10']) for model in ['M1_local','M3_ppr_h','M6B_fusion']])
    text += [mdtable(['Month','Panel','Observable/200','Cold observable/50','Markov','PPR-H','Fusion'],panelbody),'',f"![Panels]({link('figures/05_query_panels.png')})",'',
             'Mức PPR thay đổi theo sample, nhưng trong cả sáu panel-month comparisons Markov vẫn cao hơn PPR-H. Đây là sensitivity evidence, không confidence interval cho toàn Wikipedia. Cold-start vẫn quá ít observable labels để khẳng định hiệu quả.','',
             '## 7. CycleRank, adaptive fusion và embedding stability','',
             'CycleRank implementation đếm exact simple directed cycles qua source, chỉ length2/3, cộng exp(−length) cho nodes trên cycle; không gọi đây là unrestricted CycleRank. Validation chọn k3 ở cả ba windows. Nó cao hơn PPR-H khoảng0,24–0,26 NDCG nhưng vẫn kém Markov rõ rệt. Thiết kế bám [CycleRank, or There and Back Again](https://pmc.ncbi.nlm.nih.gov/articles/PMC7544349/); không chuyển benchmark claims của paper sang đồ án.','',
             'Adaptive fusion dùng λ(u)=Neligible/(Neligible+τ), τ chọn validation trong10/100/1000. Nó không thắng đều: August thấp hơn cả local và selected backoff. Published count mass chỉ là confidence proxy bị censorship, không độ chắc chắn được hiệu chuẩn. Không tiếp tục thử τ trên test để sửa thất bại này.','',
             f"![Validation sensitivity]({link('figures/06_validation.png')})",'',
             mdtable(['Test','Embedding graph','Mean NDCG (3seeds)','Sample SD','Min','Max'],[[r['month'],r['mode'],f(r['mean']),f(r['sample_sd']),f(r['min']),f(r['max'])] for r in rows('embedding_seeds')]),'',
             'H dimension32, WH dimension64 dùng knobs đã chọn trong study gốc. Vì architectures khác, bảng rolling không là matched-knob causal weighting ablation; matched A5 của study-v3 mới giữ knobs bằng nhau. Không chọn seed cao nhất và không gọi ba seeds là CI về human behavior. Loss/convergence diagnostics từng configuration được lưu; không tạo giả training loss cho PPR hoặc Markov.','',
             '## 8. Cơ chế: bảo toàn count order có đủ không?','',
             'Tie-break giữ mọi unequal local-count order; topology chỉ phá equal-count ties. Trong toàn bộ600 query-months, audit Top-20 không thấy count-order inversion của tie-break. Positive future targets được phân observed/unobserved theo từng training window; hai phần DCG dùng cùng full IDCG nên cộng đúng thành NDCG, không cộng hai metric với mẫu số khác nhau.','',
             f"![Mechanism]({link('figures/07_mechanism.png')})",'',
             'July tie-break−Markov gồm +0,002951 từ training-observed và +0,005092 từ training-unobserved targets. September phần unobserved là−0,000879, lấn át +0,000447 observed; không thể kết luận topology luôn cứu tail. PPR-H có thêm một ít unobserved contribution nhưng mất nhiều observed contribution. Đây là evidence cho trade-off, không causal attribution hoặc reliable-negative classification. Các component CIs là exploratory, không lấy một interval thuận lợi giữa nhiều contrasts làm main discovery.','',
             '## 9. Reproducibility, demo và điều chưa chứng minh','',
             f"[Portable evidence]({link('bundle_manifest.json')}) lưu5 gzip JSON payloads, frozen scores/rankings/labels, original prediction hashes và chronology logs. Standard-library verifier tính lại28.600 source×model×period evaluations, kiểm tra19.600 rankings và3.600 model views của [demo rolling]({link('demo.html')}). Totals có những query/model lặp lại giữa panel/control tables; không phải sample size nghiên cứu. Đây là re-evaluation, không retraining từ raw.86 tests đạt cục bộ; CI kiểm tra core/scientific contracts và cả hai bundles.",'',
             'Demo mới cho đổi source/tháng/model để thấy refit theo thời gian; demo gốc May/June giữ predictions cố định. Cả hai hiển thị future labels như evidence, không input. Browser interaction/rendering QA vẫn chưa thực hiện được do origin access từng bị từ chối; không coi data/JS syntax checks là browser QA. Có case tables tĩnh làm fallback.','',
             'Giới hạn: no sessions/users; censored labels; exposure bias; snapshot cũ dần; 200 sources cho rolling,600 cho panel controls; source-bootstrap chỉ là approximation vì graph dependence; overlapping periods; null chưa có mixing theorem; không population/causal/online/cross-language claims. Full model reproduction trên Linux chưa được chứng nhận, dù tiny scientific CI có kiểm tra native backend.','',
             'Chạy `sh scripts/reproduce_extensions.sh` để tái tạo vào output mới. Kiểm tra nhanh: `PYTHONPATH=src python3 -m wikinav.verify_extensions`.','',
             '## 10. Evidence index','',
             mdtable(['Artifact','Câu hỏi kiểm tra'],[[f"[{name}.csv]({link('tables/'+name+'.csv')})",question] for name,question in [('metrics','Toàn bộ required metrics / macro-weighted / full-conditional'),('coverage','Mẫu số, label mass/pairs và discarded coverage'),('contrasts','Effect sizes và paired source intervals'),('selected_parameters','Knobs chọn bằng validation'),('validation_trials','Tất cả tried settings và measured fit/score cost'),('panel_strata','Số nguồn có nhãn ở từng panel/traffic stratum'),('common_sources','115 sources chung, tránh đổi cohort ngầm'),('embedding_seeds','Variability, không best-test seed'),('source_mechanism','Per-source additive contribution và count-order audit'),('mechanism_summary','Observed/unobserved deltas và exploratory CIs')]]),'']
    fallback=rows('fallback_groups')
    text += ['## 11. Fallback-policy audit (post-hoc)','','Tie-break chỉ là thay tie policy khi source có published eligible count. Nếu source không có count eligible, M1_local dùng global-popularity fallback, còn topology_tie và adaptive dùng PPR. Vì vậy primary contrast gồm cả fallback-policy change ở nhóm này; không gán toàn bộ delta cho equal-count tie breaking.','',mdtable(['Test','Train eligible mass','Queries','Observable','Tie−local Δ','95% CI'],[[r['month'],r['group'],r['queries'],r['observable'],f(r['delta_vs_local'],6),'['+f(r['ci_low'],6)+', '+f(r['ci_high'],6)+']' if r['ci_low'] else 'N/A'] for r in fallback if r['model']=='topology_tie']),'','Nhóm này định nghĩa từ counts training của mỗi window, không đồng nhất với original Jan–March cold stratum. Subgroup được thêm sau test để giải thích, không trở thành primary contrast mới. Nhóm quá nhỏ không cho cold-start conclusion.','']
    (output/'EXTENSION_RESULTS.md').write_text('\n'.join(text))
    # Case selection is explicitly post-hoc and balanced; no cherry-picked average claim.
    demo=json.loads((folder/'demo_data.json').read_text())['queries']
    eligible=[q for q in demo if q['models']['M1_local']['ndcg'] is not None]
    gap=lambda q:q['models']['topology_tie']['ndcg']-q['models']['M1_local']['ndcg']
    picks=[('Tie-break gain lớn nhất trong ba windows',max(eligible,key=gap)),('Tie-break loss lớn nhất trong ba windows',min(eligible,key=gap))]
    adaptive=lambda q:q['models']['adaptive_fusion']['ndcg']-q['models']['M1_local']['ndcg']
    worst=min(eligible,key=adaptive)
    if any(q['id']==worst['id'] and q['month']==worst['month'] for _,q in picks):
        picks=[(reason+'; đồng thời là adaptive failure lớn nhất' if q['id']==worst['id'] and q['month']==worst['month'] else reason,q) for reason,q in picks]
    else:picks.append(('Adaptive failure lớn nhất',worst))
    ct=['# Extension case studies','', 'Chọn sau test theo extreme delta đã công bố, để kiểm tra failure mechanisms; không dùng cases để chọn model hoặc đại diện average effect. Full tables/rankings có trong portable payload.','']
    for reason,q in picks:
        ct += [f"## {reason}: {q['title']} · {q['month']}",'',f"Source `{q['id']}`; {q['candidates']} candidates; {q['future_pairs']} observable future pairs. Train: {', '.join(q['scope']['train'])}; validation {q['scope']['validation']}.",'',mdtable(['Model','Full NDCG@10'],[[m,f(v['ndcg'])] for m,v in q['models'].items()]),'']
        for model in ['M1_local','topology_tie','M6B_fusion','adaptive_fusion']:
            p=q['models'][model]
            ct += [f'### {model}','',mdtable(['Rank','Destination','Published train count','Future count','Score'],[[i,q['targets'][t]['title'],q['targets'][t]['train'] or 'unobserved',q['targets'][t]['future'] or 'unobserved',f(p['scores'][t],6)] for i,t in enumerate(p['ranked'],1)]),'']
        mass=next(r['eligible_train_mass'] for r in rows('source_mechanism') if r['month']==q['month'] and r['source']==q['id'] and r['model']=='M1_local')
        if float(mass)==0:
            ct += ['**Cơ chế chính:** source không có published eligible training mass. M1_local scores ở bảng là target global popularity, không source-specific click count. Tie-break/adaptive bỏ fallback popularity để dùng topology, làm giảm NDCG trong case này. Vì vậy failure này là khác biệt fallback policy, không phải đảo thứ tự positive local counts.','']
        truth=sorted([(t,d) for t,d in q['targets'].items() if d['future']>0],key=lambda x:-x[1]['future'])[:3]
        for t,d in truth:
            positions={m:(v['ranked'].index(t)+1 if t in v['ranked'] else 'ngoài Top-10') for m,v in q['models'].items()}
            ct += [f"Evidence: **{d['title']}** có future count {d['future']}, published train count {d['train'] or 'unobserved'}; Markov rank {positions['M1_local']}, tie-break rank {positions['topology_tie']}, fusion rank {positions['M6B_fusion']}.",'']
        ct += ['Điểm cần đối chiếu: giữ nguyên các unequal positive counts ở tie-break; xem target hữu ích bị đưa ra/vào Top-10 trong nhóm equal-count. Với adaptive, đọc local count và kiểm tra thứ tự thay đổi; absence của count không phải negative label. Không suy nguyên nhân hành vi người đọc từ một ranking failure.','']
    (output/'EXTENSION_CASES.md').write_text('\n'.join(ct))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,default=Path('reports/extensions/study-v2'));p.add_argument('--output',type=Path,default=Path('reports'));a=p.parse_args();build(a.folder,a.output)
