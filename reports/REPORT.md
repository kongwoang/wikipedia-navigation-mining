# Wikipedia Navigation Mining: When Do Hyperlinks Help Beyond Click History?

**Khai phá điều hướng Wikipedia: Khi nào cấu trúc liên kết bổ sung cho lịch sử truy cập?**
Báo cáo chính học phần IT4868E, thống nhất nội dung ngày 05/11/2026. Đây là bản biên tập từ các thực nghiệm đã có; không phải một run hoặc protocol mới. [Scope hiện hành](../docs/PROJECT_PLAN.md), [báo cáo kỹ thuật đầy đủ](RESEARCH_REPORT.md), [bảng 14 models](RESULT_TABLES.md) và [robustness extensions](EXTENSION_RESULTS.md) giữ khả năng kiểm tra toàn bộ evidence.

Mạch lập luận: vấn đề điều hướng → nguồn dữ liệu và graph → so sánh tín hiệu → giải thích gain/loss → giới hạn và kết luận.

## 1. Tóm tắt và câu hỏi nghiên cứu

**Local click frequency là tín hiệu mạnh; topology bổ sung một số gợi ý nhưng chưa tạo gain tổng thể đáng tin cậy trong sample này.** Đồ án nghiên cứu source-conditioned next-article ranking trên Wikipedia tiếng Tây Ban Nha. Benchmark dùng monthly Clickstream 2018 và independent historical hyperlink graph; mọi phương pháp dùng chung candidates và temporal split. Tháng05 có 127 nguồn với observable labels: Markov đạt macro full NDCG@10=0,8991, PPR-H=0,3126 và score fusion=0,9034. Chênh fusion−behavior là0,00429 với 95% CI [−0,00076;0,01035]. Trên transitions chưa có published training count, PPR tìm được nhiều positives hơn Markov ở một số phép đo; lợi ích cục bộ đó không đủ chứng minh improvement chung. API+HTML crawler có pilot thật để kiểm tra việc trích xuất link graph, nhưng current crawl 2026 được giữ riêng khỏi benchmark 2018. Đóng góp là một phép so sánh và giải thích có thể kiểm tra lại, không phải thuật toán mới hay mô hình cá nhân hóa người dùng.

**Một bài có nhiều links không có nghĩa người đọc chọn chúng như nhau.** Hyperlink cho biết đường đi khả dụng theo định nghĩa graph; click history cho biết những chuyển trang đã quan sát. PPR/HITS/Node2Vec đo các khía cạnh cấu trúc khác nhau, còn evaluator hỏi destination nào sẽ được truy cập từ một source cụ thể. Vì vậy, graph model có thể hợp lý về structural relevance nhưng vẫn xếp hạng navigation kém hơn local counts.

Hai câu hỏi xuyên suốt:

- **RQ1:** Frequency, topology và sự kết hợp khác nhau thế nào trên cùng task, candidates và future labels?
- **RQ2:** Lợi/hại xuất hiện ở nguồn/transition nào; có ổn định và có đáng chi phí không?

Prior work đã nghiên cứu navigation và kết hợp structural/behavioral signals; đồ án không claim ý tưởng fusion mới. [Literature matrix](../docs/LITERATURE_REVIEW.md) ghi paper/task/dataset và khác biệt. Không so điểm từ dataset khác như head-to-head. [Mapping học phần](../docs/COURSE_ALIGNMENT.md) giải thích lý do giữ HITS, PPR, Node2Vec, preprocessing và ranking evaluation.

## 2. Dữ liệu: link được trích xuất và chuyển trang được quan sát

**Graph definition là một phần của phương pháp, không chỉ là bước đọc file.** API collector và direct HTML crawler lưu raw bytes, hashes, page IDs/revisions, pagination, anchors/section/occurrences; HTML parser phân biệt main body với infobox/navbox/references. Cache/resume và raw parsing replay giúp truy nguyên edge đến dữ liệu gốc. [Thiết kế crawler](../docs/CRAWLING_EXTENSION.md), [pilot](crawl/pilot-v2/PILOT.md).

Pilot current crawl có 8 pages,8/8 API–HTML revision matches, 654 API edges,556 body edges và 1.028 occurrences. Với *Municipio de Cumberland (condado de Adams)*, API có 33 target titles, body-only có 13; all-context agreement=1,0. Đây là bằng chứng phạm vi extraction khác nhau, không phải bằng chứng body-only tốt hơn hoặc API là gold. Manual extraction audit 20 pages còn thiếu;8 pages thiên về wrestling không phải representative corpus. Export 575 nodes cũng không có nghĩa 575 pages đã crawl: 567 targets chưa resolve.

**Benchmark ranking dùng dữ liệu lịch sử tương thích thời gian.** Clickstream cung cấp `prev,curr,type,n`; chỉ giữ `type=link`, aggregate counts, không users/sessions/impressions. H lấy độc lập từ WikiLinkGraphs 01/03/2018; training Jan–Mar, validation April, primary test May, June dùng cùng predictions để kiểm tra horizon. Các raw-source references, checksums và redirect audit ở [DATA_AUDIT](../docs/DATA_AUDIT.md) và [ATTRIBUTIONS](../docs/ATTRIBUTIONS.md).

| Thành phần | Phạm vi thực tế |
|---|---|
| Query sample | 200 sources,50 mỗi train-traffic stratum; out-degree 5–500; chọn chỉ từ historical/train data |
| Ranking context chính | Induced H:8.094 nodes,319.694directed edges; giữ 100% query outgoing candidates |
| Boundary limitation | Chỉ30,82%outgoing edges của mọi sampled node được giữ; full-H control được báo riêng |
| May evaluation | 127 observable sources,1.172 label pairs,62.768 published clicks; candidate-mass coverage95,54% |
| June evaluation | 122 observable sources,1.277 label pairs,63.809 published clicks; candidate-mass coverage94,07% |

Current crawl 2026 **không tạo features cho labels 2018**. Hai phần minh họa acquisition/extraction và historical prediction ở hai thời điểm; chưa phải một end-to-end recommendation experiment trên corpus tự crawl. Historical wikitext của 6pilot pages không tự biến thành historical HTML/DOM. Đồ án giữ giới hạn này công khai, thay vì ghép timestamps không hợp lệ.

EDA training giải thích baseline selection: median observed top-1 outgoing share≈0,5001 và top-5 share=1 trên các nguồn có training observations. Counts tập trung làm Local Markov thành đối thủ mạnh. Những tỷ lệ này bị suppression ảnh hưởng, không mô tả toàn bộ clicks thực. [Concentration](generated/figures/10_concentration_and_drift.png) và [degree–traffic](generated/figures/03_topology_traffic.png) là hai hình chính; không cần vẽ toàn graph như một hairball.

## 3. Task và các tín hiệu so sánh

Gọi \(G_H=(V,E_H)\) là independent directed hyperlink graph, \(c_T(u,v)\) là published training count và \(G_C\) là graph weighted bởi counts đó. Với current article\(u\), xếp hạng \(C(u)=N_H^+(u)\setminus\{u\}\). Missing counts nghĩa **unobserved**, không xác nhận zero hoặc irrelevant. Shared H candidates là điều kiện chung: “behavior-only” nói về scoring signal, không có nghĩa model đó không dùng candidate eligibility từ H.

**Năm phương pháp giải thích năm vai trò**, cùng hai reference baselines:

| Model | Score / motivation | Giới hạn cần nhớ |
|---|---|---|
| Uniform, reference | Mọi candidate bằng điểm, deterministic hash ties | Candidate/tie reference; không có frequency signal |
| Global Popularity, reference | Tổng inbound training counts của destination | Bỏ qua current source |
| Markov / selected backoff | Local counts được row-normalize; eligible-count-empty thì global fallback | Targets chưa có count khó phân biệt; validation có tuning backoff |
| HITS-global | Authority từ iteration \(a\propto A^TAa\) trên fixed H | Không thực hiện query-root/base-set retrieval như HITS trong slide |
| PPR-H | Source-seeded random walk trên uniform outgoing H | Multi-step proximity không phải xác suất next click |
| Node2Vec-H | Directed biased walks → SGNS embeddings → cosine\((z_u,z_v)\) | Symmetric cosine dù walks directed; objective không trực tiếp tối ưu future clicks |
| Score fusion | \(s=\lambda b+(1-\lambda)\widehat{r}_u\), hai score chuẩn hóa trên candidates | Có thể kéo tail lên hoặc làm đảo ranking đúng; phải so với behavior parent |

Với PPR, \(r_u=d(P_H^Tr_u+e_u\sum_{x\in D}r_u(x))+(1-d)e_u\), trong đó \(D\) là các dangling nodes và hàng tương ứng của \(P_H\) bằng0; dangling mass được trả về source. `d` là continuation probability; restart là`1-d`. Dừng power iteration khi fixed-point L1 residual≤10⁻⁸, giới hạn 1.000 iterations; solver failure không được silently bỏ query. Global PageRank là trường hợp restart uniform để giải thích lý thuyết; không bổ sung benchmark mới chỉ để tăng model count.

Node2Vec chọn next\(x\) từ current\(v\), previous\(t\) với trọng số\(w(v,x)\alpha_{pq}(t,x)\): `1/p` khi quay lại, `1` khi `x→t` tồn tại, `1/q` trường hợp còn lại; sau đó normalize. Walk dừng ở dangling node. SGNS noise samples là công cụ tối ưu embedding, không phải behavioral negative labels. Directed convention, training diagnostics và chi phí ở [báo cáo kỹ thuật](RESEARCH_REPORT.md).

Tuning chỉ dùng April: PPR damping∈{0,15;0,5;0,85}; fusionλ∈{0;0,25;0,5;0,75;1}; Node2Vec dimension 32/64 và3 cặp (p,q). Selected H dùngdamping 0,15, fusion λ = 0,5; Node2Vec-H dimension 32,p0,5,q2,seed17; seeds 29/43 giữ knobs. Fixed walks 3/node, length 20,window 5,epochs 5,negatives 5. Markov/backoff chọn μ = 0 nên hai baseline cho cùng rankings ở study gốc. Grid đầy đủ và smoothing/fallback contracts ở [RUN_PROTOCOL](../docs/RUN_PROTOCOL.md) và [selected parameters](generated/tables/selected_parameters.csv).

## 4. Đánh giá công bằng

**Primary metric là macro full NDCG@10 đã khóa trước test.** Với published positive set\(R_u\), ranked list\(v_i\) và future counts\(n(u,v)\):

\[
Recall@K=|\{v_1,\ldots,v_K\}\cap R_u|/|R_u|,
\quad MRR@10=1/\min\{i\le10:v_i\in R_u\},
\]

MRR bằng0 nếu không có positive trongTop-10. NDCG dùng

\[
DCG@10=\sum_{i\le10}\frac{\log_2(1+n(u,v_i))}{\log_2(i+1)},\qquad NDCG=DCG/IDCG.
\]

IDCG sắp toàn bộ observable positives, kể cả ngoài candidates. Không áp dụng exponential gain lần nữa. Recall@5/10/20 đo coverage positives, MRR first-hit và NDCG mức ưu tiên graded counts. Cả ba chỉ phản ánh published labels và chịu exposure/suppression bias, không đo user satisfaction.

Macro cân đều nguồn; traffic-weighted cân theo full observed source mass. Conditional metrics chỉ xét eligible positives, luôn báo tách với full. Nguồn không có labels là NA, không gán0; không thay nguồn thiếu nhãn bằng nguồn có nhãn sau test. Coverage ledger giữ mất mát mapping/candidates.

Primary contrast là **M6B_fusion−M1B_backoff**, paired source bootstrap2.000 resamples, seed2026, percentile95% CI. Source dependence trong cùng graph và overlapping windows hạn chế suy rộng. Secondary subgroup contrasts exploratory. Candidate mapping, H, sampling và knobs không đọc future counts; predictions freeze trước test evaluation. Protocol và frozen artifacts không thay đổi trong lần biên tập này.

## 5. Kết quả: structure có thông tin, nhưng frequency vẫn là baseline mạnh

**Bảng chính rút gọn theo vai trò học thuật sau thực nghiệm**, không thay pretest model selection. Các phương pháp có score cao/thấp bị lược khỏi phần trình bày vẫn có trong [bảng 14 models đầy đủ](RESULT_TABLES.md). Bảng dưới là May 2018, full observable macro,127 sources; số đọc trực tiếp từ [CSV](generated/tables/metrics.csv).

| Model | Recall@5 | Recall@10 | Recall@20 | MRR@10 | NDCG@10 |
|---|---:|---:|---:|---:|---:|
| Uniform | 0.1825 | 0.3547 | 0.5677 | 0.3463 | 0.2518 |
| Global Popularity | 0.1310 | 0.2818 | 0.5135 | 0.2436 | 0.2008 |
| Markov / selected backoff | 0.6436 | 0.7748 | 0.8658 | 0.9539 | 0.8991 |
| HITS-global | 0.1228 | 0.2138 | 0.4382 | 0.1553 | 0.1401 |
| PPR-H | 0.2314 | 0.4122 | 0.6123 | 0.4161 | 0.3126 |
| Node2Vec-H | 0.3301 | 0.5457 | 0.7153 | 0.5582 | 0.4510 |
| Score fusion | 0.6516 | 0.7811 | 0.8602 | 0.9541 | 0.9034 |

Primary fusion−behavior May Δ = 0,004294,95% CI [−0,000758;0,010352]; June Δ = 0,003730,95% CI [−0,000194;0,009947]. Cả hai chứa 0: **chưa chứng minh reliable improvement**, không chứng minh hai phương pháp tương đương hoặc topology vô ích. [Paired comparisons](generated/tables/paired_bootstrap.csv).

Macro không kể hết câu chuyện. June Markov NDCG 0,8899 và fusion 0,8936; traffic-weighted tương ứng0,9251 và0,9178. Fusion tăng trung bình theo nguồn nhưng giảm khi cân observed traffic. Vì vậy không chọn một aggregation đẹp hơn để tuyên bố thắng toàn diện.

### Tại sao vẫn cần topology trong phân tích?

**Topology giúp phân biệt một số destinations mà local counts không phân biệt được.** Trong May, nhóm training-unobserved có 117 future pairs trên 53 sources, mass2.020. Giữ nguyên ranking đầy đủ rồi chỉ đo recall trên nhóm này: Markov Recall@10=0,0912, PPR-H=0,2335, fusion=0,0991. Đây là descriptive subset evidence, không significance claim và không rerank riêng nhóm targets. [Sparsity table](generated/tables/transition_sparsity.csv).

Lợi ích đó có giới hạn: fusion không giữ toàn bộ recall gain của PPR trên nhóm unobserved, trong khi có thể làm giảm thứ hạng các transitions đã có counts. “Unobserved edge” cũng khác “cold source”: cold sources có 0 observable labels ở May,1 ở June; không đủ evidence nói topology giải quyết cold start.

### Ablation tách clicks khỏi structure

| Phép so sánh | Kết quả May | Điều được phép kết luận |
|---|---|---|
| PPR-H vs weighted-H, cùng damping 0,5/supportH | ΔNDCG≈+0,6085 khi thêm click weights | Click weights hữu ích cho walk trong control này; không chứng minh topology hơn Markov |
| Node2Vec-H vs matched weighted-H, cùng d32 / p / q/seed | Δ≈+0,2142;95% CI [0,1668;0,2593] | Weighting cải thiện embedding tại matched settings |
| M1B vs H-only vs score fusion | Primary gain nhỏ, CIs chứa 0 | Incremental value trên strong behavior baseline chưa chắc chắn |

Selected Node2Vec-H/W có khác dimension nên không dùng tuned-score gap làm weight-only ablation. Lambda sensitivity chỉ dùng validation. [Sensitivity](generated/figures/05_validation_sensitivity.png) và [matched comparisons](generated/tables/paired_bootstrap.csv) giữ đầy đủ controls.

## 6. Hai trường hợp giúp hiểu kết quả

**Danza posmoderna cho thấy topology bổ sung gợi ý khi thiếu published counts.** Training chỉ có Danza contemporánea 62 clicks; May có thêm Merce Cunningham 16 clicks. Markov bỏ target mới khỏiTop-10; PPR/fusion đưa lênrank 5. NDCG Markov 0,6805, PPR/fusion 0,8764. Node2Vec-H ở case này đạt0: embedding không tự động tốt hơn explicit graph ranking.

**Tragacete cho thấy kết hợp tín hiệu có thể làm hỏng ranking đang tốt.** Fusion giảm NDCG từMarkov 0,8616 xuống0,7353 khi topology thay phần tail. Đây là failure của đúng hybrid trong bảng chính, không lấy failure của một variant khác để thay thế. [Counts, candidates và Top-10 của cả hai cases](CASE_STUDIES.md).

Hai cases chọn sau test theo rule để giải thích, không ước lượng average performance. Không suy nguyên nhân bằng tin tức hoặc ý định người dùng chưa được quan sát. *Remora* là backup case khi cần minh họa broad hubs khác next-step preference: Markov 1,0, PPR 0,0; không đưa thêm nhiều examples vào phần chính.

## 7. Kiểm tra độ vững, hội tụ và chi phí

**PPR kém không chỉ do graph bị cắt.** Full-H control giữ candidates và damping, mở context lên 2.077.467 nodes/36.333.722 edges: May PPR 0,3126→0,3220, vẫn thấp hơn Markov 0,8991 trên sampled queries. Đây là exploratory control ở fixed settings, không bằng chứng mọi PPR đều kém. [Full-graph evidence](EXTENSION_RESULTS.md).

Ba rolling windows July–September là protocol riêng, giữ tại appendix. Primary contrast của extension là **topology_tie−M1_local**, cả ba CIs chứa 0; không lấy chúng làm CI của score fusion. Extension gồm fallback-policy change và source reuse, nên không trộn với original fusion estimand. Kết quả hỗ trợ sự thận trọng khi diễn giải topology augmentation, không tạo một số score gộp giữa các protocols.

**Solver hội tụ khác với model dự đoán tốt.** Giữ [PPR residual/Node2Vec SGNS curves](generated/figures/06_numerical_diagnostics.png), [seed variation](generated/tables/embedding_seed_stability.csv) và [runtime/accuracy](generated/figures/09_cost_accuracy.png). PPR dùng fixed-point residual; SGNS epoch deltas chỉ là auxiliary optimization diagnostics. Markov không có epoch loss; dùng history-size/temporal curves. Node2Vec-H May mean ± SD qua 3 seeds0,4371±0,0128 không phải generalization CI.

Original full model run đo245,32 s, peak RSS≈1,82 GiB trên máy macOS đã ghi provenance, không gồm download/build/ingestion; không suy online SLA hoặc full-graph embedding cost. Extra degree-null/query panels/CycleRank có thể trả lời phản biện sâu nhưng không cần để hiểu kết luận chính.

## 8. Kết luận và phần còn thiếu

**Bài học chính là phân biệt đường đi khả dụng với lựa chọn đã quan sát.** Counts trực tiếp nắm bắt một tín hiệu quan trọng cho next-article ranking. Topology cung cấp một số gợi ý ở vùng thiếu counts, nhưng usefulness cục bộ và graph sophistication chưa đủ để xác nhận lợi ích tổng thể khi kết hợp. Quyết định dùng mô hình phải xét conditional gains/losses, uncertainty và cost.

Kết luận giới hạn ở một language/time period, train-stratified sample, censored labels và graph/mapping policy đã mô tả. Không claim user personalization, causal effect, cold-start solution, population performance hoặc graph không bao giờ hữu ích. Full data/code vẫn được công bố để kiểm tra cả kết quả bất lợi.

Phần cần hoàn thiện cho bản nộp là manual extraction audit 20 pages và rehearsal giao diện demo. Corpus lớn, content recommendation và thêm algorithms không nằm trong scope hiện hành. Nếu chưa có audit thì giữ pilot-only label; không quảng bá crawl 2026 đã cải thiện ranking2018.

## 9. Tái lập và tự kiểm tra lập luận

[REPRODUCIBILITY](REPRODUCIBILITY.md) ghi dependencies, raw-to-model instructions và giới hạn. Chạy hai verifier để re-evaluate frozen artifacts; đây không phải retrain. Test-count/status theo [IMPLEMENTATION_STATUS](../docs/IMPLEMENTATION_STATUS.md), không lấy một con số tests cũ làm headline của đóng góp.

| Claim | Evidence | Status |
|---|---|---|
| Local behavior mạnh hơn topology-only trong sample | Same-candidate main table | Supported, sample-conditional |
| Topology tìm thêm một số training-unobserved destinations | A7 original-ranking recall, Danza case | Supported descriptively; không causal/significance claim |
| Fusion chưa reliable net gain | May/June paired CIs, June weighted reversal | Supported; không equivalence claim |
| Preprocessing thay link scope | Same-revision API/body pilot | Supported về agreement; chưa manual extraction accuracy |
| Current crawl giúp prediction2018 | Không có compatible experiment | **Không claim** |

Self-review năm chiều: **contribution** là comparative insight và reproducible evidence; **clarity** dùng2 RQ và7 rows; **experimental strength** giữ strong baseline/negative results; **evaluation completeness** giữ required metrics, controls, diagnostics/coverage và ghi extraction audit còn thiếu; **method soundness** giữ temporal separation, shared candidates và label-censoring caveats. Không giải quyết một hạn chế bằng cách giấu nó ở appendix.
