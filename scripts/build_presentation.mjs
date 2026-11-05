/** Editable academic deck. Requires the optional bundled Artifact Tool runtime.
 * Set ARTIFACT_MODULES, PRESENTATION_SKILL_DIR, RUNTIME_PYTHON, RUNTIME_NODE_MODULES.
 * Run presentation_data.py first. Does not train, alter frozen evidence or use network.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const runtime=process.env.ARTIFACT_MODULES, skill=process.env.PRESENTATION_SKILL_DIR;
if(!runtime||!skill||!process.env.RUNTIME_PYTHON) throw new Error('Set documented optional presentation runtime paths');
const {Presentation,PresentationFile}=await import(pathToFileURL(path.join(runtime,'@oai/artifact-tool/dist/artifact_tool.mjs')));
const {applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')));
const out=path.join(root,'.cache/deck-build');await fs.mkdir(out,{recursive:true});
const D=JSON.parse(await fs.readFile(path.join(out,'data.json'),'utf8'));
const P=Presentation.create({slideSize:{width:1280,height:720}});
P.theme.defaultFont='Arial';
const C={navy:'#122B40',teal:'#087F8C',gray:'#566674',light:'#ECF2F4',line:'#D3DEE4',orange:'#A94D2D',white:'#FFFFFF'};
const repo='https://github.com/kongwoang/wikipedia-navigation-mining/blob/main/';
function text(s,str,x,y,w,h,size=27,color=C.navy,bold=false){
 const t=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 t.text=str;t.text.style={typeface:'Arial',fontSize:size,color,bold};return t;
}
function rule(s,x,y,w,color=C.line){s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:2},fill:color,line:{fill:'none',width:0}});}
function slide(title,kicker,source,notes){
 const s=P.slides.add();s.background.fill=C.white;
 text(s,kicker.toUpperCase(),56,28,1130,30,18,C.teal,true);
 text(s,title,56,76,1165,112,43,C.navy,true);
 rule(s,56,660,1168);text(s,source,56,676,1080,25,15,C.gray);
 text(s,String(P.slides.items.length).padStart(2,'0'),1170,674,55,28,19,C.teal,true);
 s.speakerNotes.text=notes;return s;
}
function table(s,values,x,y,width,height,widths,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,columnWidths:widths,values});
 t.borders.assign({fill:C.white,width:2,style:'solid'});
 for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
  const z=t.getCell(r,c);z.fill=r===0?C.navy:r%2===0?'#F5F8F9':C.light;
  z.text.style={typeface:'Arial',fontSize:size,color:r===0?C.white:C.navy,bold:r===0||c===0};
 }
 return t;
}
function bar(s,categories,values,x,y,w,h,opts={}){
 const ch=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},
 categories,series:[{name:opts.series||'Giá trị',values:values.map(v=>Number(v.toFixed(8))),fill:C.teal,points:opts.colors?.map((fill,idx)=>({idx,fill}))}],
 hasLegend:false,barOptions:{direction:opts.horizontal?'bar':'column',grouping:'clustered',gapWidth:75},
 xAxis:{textStyle:{fontSize:22,fill:C.gray},majorGridlines:null,line:{fill:C.line,width:1},...(opts.horizontal?{min:0,max:opts.max||1}: {})},
 yAxis:{textStyle:{fontSize:22,fill:C.gray},majorGridlines:{fill:C.line,width:1},numberFormatCode:opts.percent?'0%':opts.integer?'0':opts.max===.3?'0.00':'0.0',...(!opts.horizontal?{min:0,max:opts.max||1}: {})},
 dataLabels:{showValue:true,position:'outEnd',numberFormatCode:opts.percent?'0.0%':opts.integer?'0':'0.0000',textStyle:{fontSize:23,fill:C.navy,bold:true}},
 chartFill:C.white,plotAreaFill:C.white});
 applyPresentationChartFont(ch,{fontFamily:'Arial'});return ch;
}
const fmt=n=>n.toFixed(4).replace('.',',');
let s=slide('Khi nào hyperlinks giúp xếp hạng\nbài tiếp theo tốt hơn lịch sử clicks?','IT4868E  •  Wikipedia Navigation Mining','Phạm vi: source-conditioned ranking trên eswiki 2018',
`0:45. Mở bằng bài toán: nhiều links khả dụng nhưng người đọc không chọn đều. Input current article u, output Top-K outgoing candidates. Không có users/sessions. Hai RQ: tín hiệu nào hiệu quả và hiệu quả ở đâu. Nguồn: ${repo}docs/PROJECT_PLAN.md`);
text(s,'Một bài viết. Nhiều đường đi khả dụng.',56,226,1120,55,36,C.navy,true);
text(s,'Hyperlinks mô tả cấu trúc lựa chọn.\nClick history ghi nhận lựa chọn đã được quan sát.',56,307,1080,100,31);
rule(s,56,443,1168);
text(s,'RQ1',56,480,110,45,28,C.teal,true);text(s,'Frequency, topology và fusion khác nhau thế nào?',178,480,1020,60,28);
text(s,'RQ2',56,561,110,45,28,C.teal,true);text(s,'Khác biệt xuất hiện ở đâu, ổn định đến mức nào?',178,561,1020,60,28);
s=slide('Hai graph biểu diễn hai loại thông tin','Dữ liệu và task','H: WikiLinkGraphs 01/03/2018. C: published Clickstream counts.',
`1:00. H độc lập với future clicks. Directed edges vì u→v không suy v→u. Censoring: missing count không là zero. Behavior-only nói scoring signal, cùng candidate eligibility H. ${repo}reports/REPORT.md §2–3; ${repo}docs/DATA_AUDIT.md`);
table(s,[['Hyperlink graph H','Transition graph C'],['u → v: có hyperlink','u → v: có published transition'],['Weight: link presence','Weight: aggregate count c(u,v)'],['Availability / structure','Observed navigation']],56,205,1168,264,[584,584],27);
text(s,'C(u) = outgoing links của u trong H đã khóa',56,509,1120,56,32,C.teal,true);
text(s,'Xếp hạng destination trong cùng C(u). Không có user IDs hoặc sessions.',56,589,1168,48,25);
s=slide('Tự crawl cho thấy “link” phụ thuộc ngữ cảnh','Web Content Mining  •  L04','20 trang, 05/11/2026. Audit/provenance: reports/crawl/audit-v2/',
`1:15. Crawler API+HTML tự thu, seeds khóa theo train traffic/degree, không test. 20/20 revisions khớp, 42 responses. HTML graph sau sửa. 120 sampled occurrences, agent review không human gold. Hai lỗi indicator + authority icon, 38TP/2FP trước, 38TP/0FP sau trên cùng sample; không held-out accuracy. Raw giữ nguyên, explicit reparse. 2026 không đưa vào2018prediction. ${repo}reports/crawl/audit-v2/AUDIT.md`);
bar(s,['API links','HTML body'],[D.crawl.api_edges,D.crawl.html_edges],56,214,585,360,{max:1600,integer:true,series:'Directed edges'});
text(s,'20 / 20',720,211,475,72,55,C.teal,true);
text(s,'cặp API–HTML khớp revision',720,294,480,70,27);
text(s,'Rà 120 occurrences:\nphát hiện 2 lỗi context',720,389,480,90,30,C.navy,true);
text(s,'Parser agreement ≠ semantic correctness',720,507,470,90,26,C.orange,true);
text(s,'Crawl 2026 phục vụ extraction audit. Benchmark ranking giữ dữ liệu lịch sử 2018.',56,605,1168,43,24,C.gray);
s=slide('Clicks tập trung khiến Markov là baseline mạnh','EDA dẫn đến thiết kế','Nguồn: training_concentration.csv và graph_statistics.json. Chỉ dùng train.',
`1:00. Median top1/top5 share trên ${D.concentration.sources} sources có published training observations. Không tổng quát toàn traffic do suppression. 90,26% H edges không có published train counts, không đồng nghĩa zero. Spearman degree-popularity0.7066 mô tả graph sample, không causal. Vì vậy baseline counts mạnh và cần phân tích unobserved, macro/weighted. ${repo}reports/generated/tables/training_concentration.csv`);
bar(s,['Top-1','Top-5'],[D.concentration.median_top1,D.concentration.median_top5],56,228,585,340,{max:1.15,percent:true,series:'Median outgoing click share'});
text(s,'Median observed outgoing share',56,190,590,40,25,C.gray);
text(s,'90,26%',720,228,465,70,54,C.teal,true);
text(s,'H edges không có\npublished training count',720,314,470,88,29);
text(s,'Phải tách nhóm unobserved\nvà kiểm tra macro / weighted.',720,447,470,100,28,C.navy,true);
text(s,`Concentration: ${D.concentration.sources} sources có quan sát. Missing count không xác nhận zero clicks.`,56,605,1168,42,24,C.gray);
s=slide('Mỗi phương pháp kiểm tra một loại tín hiệu','Web Structure Mining  •  L05','Cùng candidates. Tuning chỉ dùng April. Full 14-model results giữ ở appendix.',
`1:30. Markov count row-normalization selected μ0; fallback if no eligible counts. HITS-global a∝AᵀAa, không query root HITS. PPR source restart, d0.15 selected, dangling mass vềsource. Node2vec directed x→t convention, cosine symmetric, d32 p0.5 q2 seed17. Fusion candidates normalized λ0.5 selectedApril. Uniform deterministichash, global counts source-agnostic. ${repo}reports/REPORT.md §3`);
table(s,[['Phương pháp','Tín hiệu / score','Câu hỏi kiểm tra'],['Markov / backoff','c(u,v) / Σ c(u,x)','Lịch sử tại source mạnh đến đâu?'],['HITS-global','Authority trên H','Authority có hợp next step?'],['PPR-H','Walk restart tại u','Proximity có giúp xếp hạng?'],['Node2Vec-H','Directed walks, cosine','Representation có thêm ích lợi?'],['Fusion','λ·behavior + (1−λ)·PPR','Có gain ngoài behavior parent?']],56,205,1168,345,[300,405,463],24);
text(s,'Reference baselines: Uniform và Global Popularity',56,592,1168,48,27,C.gray);
s=slide('Cùng candidates, đúng thứ tự thời gian','Evaluation  •  L02','Primary contrast: fusion − Markov/backoff. Paired source bootstrap, 2.000 resamples.',
`1:15. 200 train-selected queries;127May,122June have observablelabels. H2018-03-01 precedestrainend. Future labels ngoài C vẫn trongfull denominator; không silentlydiscard. NDCG gainlog2(1+n), khôngexpgainagain. Recall5/10/20, MRR10 secondary. CI approximate conditional on sources, graphdependence. Knobs freezedbeforetest. ${repo}docs/RUN_PROTOCOL.md`);
table(s,[['Jan–Mar 2018','April','May','June'],['Train counts','Validation','Primary test','Fixed-model horizon']],56,205,1168,126,[350,240,280,298],27);
text(s,'Primary: macro full NDCG@10',56,382,1120,50,32,C.teal,true);
text(s,'Graded relevance: log₂(1 + future count)\nFull denominator giữ cả positives ngoài candidates.',56,454,1120,90,28);
text(s,'Báo thêm Recall@5/10/20, MRR@10, coverage và traffic-weighted metrics.',56,584,1168,60,26);
s=slide('Fusion tăng rất ít và CI vẫn chứa 0','Kết quả chính  •  May 2018','Macro full NDCG@10, 127 observable sources. CSV và paired bootstrap trong generated/.',
`1:15. Bảng7models là biên tập theo role sau experiments, không modelselectionmới. Values exactCSV. Fusion difference ${D.primary.difference}; CI ${D.primary.ci95.join(',')}. Chưa chứng minh reliable improvement, không chứng minh equivalence. June macroMarkov.8899fusion.8936, trafficweightedMarkov.9251fusion.9178. ${repo}reports/generated/tables/metrics.csv; ${repo}reports/generated/paired_comparisons.json`);
bar(s,D.metrics.map(x=>x.label),D.metrics.map(x=>x['ndcg@10']),45,194,770,408,{horizontal:true,max:1.08,series:'NDCG@10',colors:D.metrics.map(x=>x.model==='M1B_backoff'?C.navy:x.model==='M6B_fusion'?C.teal:'#A9BAC4')});
text(s,'Δ = +0,00429',865,220,355,60,37,C.teal,true);
text(s,'95% CI\n[−0,00076; 0,01035]',865,306,355,100,28);
text(s,'June weighted:\nMarkov 0,9251\nFusion 0,9178',865,452,355,130,28,C.orange,true);
text(s,'Primary comparison với behavior parent. Không chọn aggregation có lợi để tuyên bố thắng.',56,613,1168,40,23,C.gray);
s=slide('Lợi ích cục bộ có thể đi cùng ranking bị giảm','Error analysis  •  Giữ nguyên original rankings','May unobserved: 117 pairs, 53 sources, mass 2.020. Cases chọn sau test để giải thích.',
`2:15. ChartRecall10 nhómtrainingunobserved, khôngreranksubset. PPR.2335vsMarkov.0912;fusion.0991. Descriptive not significance. Demo May Full, Danza posmoderna7754838:trainDanza62;future44plusMerce16,MercePPR/fusionrank5Markovoutside10. NDCG.6805→.8764,N2V0. Tragacetefusion.7353vsMarkov.8616. Showactualcountsandrank notjustscore. ${repo}reports/CASE_STUDIES.md; ${repo}reports/generated/tables/transition_sparsity.csv`);
bar(s,['Markov','PPR-H','Fusion'],['M1B_backoff','M3_ppr_h','M6B_fusion'].map(m=>Number(D.sparsity.find(x=>x.model===m)['macro_recall@10'])),56,235,568,304,{max:.3,series:'Unobserved Recall@10'});
text(s,'Recall@10: training-unobserved pairs',56,188,600,42,25,C.gray);
text(s,'Danza posmoderna',711,216,510,48,32,C.teal,true);
text(s,'Merce Cunningham thiếu train count.\nPPR / fusion đưa lên rank 5.',711,276,510,84,26);
text(s,'Tragacete',711,411,510,46,32,C.orange,true);
text(s,'NDCG Markov: 0,8616\nNDCG fusion: 0,7353',711,473,510,84,28);
text(s,'Demo: cùng source, cùng May, cùng full denominator. Cases không thay average evidence.',56,604,1168,48,24,C.gray);
s=slide('Controls giúp phân biệt lỗi tính toán và giới hạn tín hiệu','Ablation, convergence và cost','Đọc chi tiết: REPORT §5–7, diagnostics và EXTENSION_RESULTS.',
`1:15. Không manufacturelossMarkov. PPRresidual1e−8 solver, SGNSdiagnosticlegit not rankingloss,3seedsN2VH.4371±.0128 notCI. A4 fixed d.5 Δ.6085, A5matched Δ.2142; clickweightshelpwalks notproveHbeatsMarkov. FullH fixedsettingsPPR.3126→.3220 stillbelow.8991. Originalrun245.32sec1.82GiB excludesdataingestion; noonlineSLA. Rolling tie−M1 contrast different, appendix only. ${repo}reports/REPORT.md §7`);
table(s,[['Control','Quan sát','Diễn giải'],['Matched H / weighted-H','Thêm counts giúp walks','Weighting không chứng minh H hơn Markov'],['Full-H context','PPR 0,3126 → 0,3220','Graph boundary chưa giải thích hết gap'],['PPR residual / SGNS / seeds','Diagnostics đã lưu','Hội tụ không đảm bảo ranking tốt']],56,211,1168,280,[335,370,463],24);
text(s,'Chi phí original model run: 245,32 s, peak RSS ≈ 1,82 GiB',56,533,1168,50,29,C.teal,true);
text(s,'Không gồm download / ingestion. Rolling extensions dùng contrast riêng, giữ ở appendix.',56,606,1168,42,24,C.gray);
s=slide('Topology có ích ở một số trường hợp,\nnhưng chưa chứng minh gain tổng thể ổn định','Kết luận  •  Đóng góp và giới hạn','Report, code, frozen predictions, raw manifests và audit annotations đều có trong repository.',
`0:45. Contributions: courseconnected acquisition audit and comparativeframework, no newalgorithmnovelty. Scope1languagehistoricalsample censoredlabels, graphboundary, no user/session, coldMay0Jun1 insufficient. Currentcrawl2026 separate. Agent120occurrences nothumangold. Browser origin blocked, offlineverifiers pass; do not claimUIQA. End on counts strongconditionaltopologyanduncertainty. ${repo}reports/REPORT.md; ${repo}reports/crawl/audit-v2/AUDIT.md`);
text(s,'Đóng góp',56,232,400,48,32,C.teal,true);
text(s,'Tự thu thập và audit link extraction.\nSo sánh công bằng trên cùng future labels.\nGiải thích cả gain, loss và uncertainty.',56,299,1120,143,30);
rule(s,56,479,1168);
text(s,'Giới hạn',56,509,260,48,30,C.orange,true);
text(s,'Một language / historical sample, censored counts.\nCrawl 2026 tách biệt, audit bằng agent, chưa có human gold.',320,509,900,103,27);
await fs.writeFile(path.join(out,'source-data.json'),JSON.stringify(D,null,2));
for(const [i,sl] of P.slides.items.entries()){
 const png=await P.export({slide:sl,format:'png',scale:1});
 await fs.writeFile(path.join(out,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
 const layout=await sl.export({format:'layout'});await fs.writeFile(path.join(out,`slide-${i+1}.layout.json`),await layout.text());
}
const candidate=path.join(out,'candidate.pptx');await(await PresentationFile.exportPptx(P)).save(candidate);
const final=path.resolve(process.env.PRESENTATION_OUTPUT||path.join(root,'reports/deliverables/Wikipedia_Navigation_IT4868E.pptx'));
const result=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:final,
 pythonExecutable:process.env.RUNTIME_PYTHON,
 integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...[2,5,6,9].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:10,requiredNativeTableOwnerSlides:[2,5,6,9],requiredNativeChartOwnerSlides:[3,4,7,8],
 materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,
 receiptPath:path.join(out,'validation.json')});
console.log(JSON.stringify(result));
