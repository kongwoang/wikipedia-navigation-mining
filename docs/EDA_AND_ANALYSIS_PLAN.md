# EDA, phân tích kết quả và thiết kế hình/bảng

> **Lưu trữ planning:** các trạng thái “chưa chạy”, blockers và effort dưới đây phản ánh thời điểm thiết kế. Implementation và real study hiện đã hoàn tất trong scope đã chốt; xem [trạng thái hiện hành](IMPLEMENTATION_STATUS.md), [frozen protocol](RUN_PROTOCOL.md) và [báo cáo kết quả](../reports/REPORT.md). Không dùng proposal như chứng nhận experiment đã chạy.

Planning ngày 20/10/2026. Không có hình từ dữ liệu thật trong giai đoạn này. Plot inventory dưới đây chỉ định câu hỏi, dữ liệu, cách đọc và quyết định; không dự đoán trước distribution hoặc improvement.

## 1. Nguyên tắc

EDA trước model chỉ đọc **train + independent graph**. Validation dùng kiểm tra pipeline/tuning có ghi log. Test EDA, future distribution và failure cases chỉ sau khi predictions/config được khóa.

Mỗi figure có caption nêu dataset/split, population, denominator, N sources/pairs, scale, filtering, uncertainty và limitation. Histograms/CCDF log scale giữ zero bin riêng; không log(0) rồi xóa rows. Missing published edges được gắn “unobserved”, không “zero clicks”.

Scientific plots xuất SVG/PDF và PNG bằng matplotlib/seaborn, nguồn aggregate table CSV/Parquet lưu kèm. Không cần force-directed hairball của hàng triệu nodes, 3D charts hoặc t-SNE nếu không trả lời câu hỏi.

## 2. Inventory EDA

| ID / priority | Research question | Dữ liệu cần | Plot / statistics | Cách diễn giải có điều kiện | Quyết định model/evaluation |
|---|---|---|---|---|---|
| E01 P0 | Count công bố phân bố thế nào, có discontinuity ở threshold? | Train c_m và observation flag | CCDF + histogram log bins, min/max theo tháng | Heavy tail hay threshold discontinuity phải được đo; không suy phần censored | Low-frequency bands, integer/schema validation |
| E02 P0 | Source traffic bất cân bằng mức nào? | T_u train | Lorenz curve, traffic share top1/10%, CCDF | Head dominance có thể làm weighted metric che lỗi tail | Macro + weighted; source stratification |
| E03 P0 | Bao nhiêu destinations chiếm phần lớn traffic mỗi source? | Normalized local train counts | Distribution top1/top5/top10 mass, cumulative mass curve | Tập trung cao ủng hộ strong Markov baseline; không đảm bảo future stability | Tuning backoff, lựa chọn K |
| E04 P0 | Source có ít alternatives hay ít observable evidence? | Unique observed outdegree, H degree, T_u | Scatter/hexbin và marginal hist | Tách low traffic khỏi low candidate degree | Degree×traffic bins; cold source definition |
| E05 P0 | Inbound và outbound traffic liên hệ thế nào? | Train incoming/outgoing count totals | Hexbin log1p, rank correlation | Article được đọc nhiều chưa chắc tạo nhiều next clicks | M0 popularity rationale, hub bias |
| E06 P0 | Graph degree phân bố, in/out khác nhau ra sao? | H after redirect policy | In/out CCDF, zero-degree proportions | Directed asymmetry cần giữ, không suy graph vô hướng | Directed walks, sparse storage, high-degree time caps |
| E07 P0 | Có fragmentation/dangling ảnh hưởng ranking? | H CSR | SCC/WCC size distribution, largest component share, dangling % | PPR vẫn tồn tại nhờ restart; component affects reachable candidates | Solver policy, isolate handling, no largest-SCC-only silent filtering |
| E08 P1 | Reciprocal edges/cycles có phổ biến? | H | Reciprocity=`# directed edges có reverse/M`, theo degree bins | Reciprocal structure có thể giải thích local relevance, không causal | Cân nhắc CycleRank P2; directed Node2Vec convention |
| E09 P0 | Degree có đồng nghĩa click popularity? | H degrees + train inbound traffic | Hexbin, Spearman với bootstrap source/node units phù hợp | Correlation không đồng nghĩa rank utility; inspect discordant nodes | M2D baseline và PPR hub analysis |
| E10 P0 | Observed clicks và independent edges khớp đến đâu? | C/H join, mapping reasons | Stage-wise attrition bars; pair và mass coverage cạnh nhau | Thiếu node, thiếu edge, template/new-link khác nhau | Go/no-go; conditional vs full denominator |
| E11 P0 | Hyperlinks thiếu observable training clicks mức nào? | EH join c_tr | Fraction unobserved theo source degree/traffic | Không diễn giải fraction này là “unused links” | Positive prior M4H, A7 |
| E12 P0 | Navigation ổn định giữa các tháng train? | c_01,c_02,c_03 | Observed-edge overlap; weighted overlap; JSD trên common sources, riêng new/vanished mass | Drift và censoring đều có thể gây thay đổi | Chronological split; history windows |
| E13 P1 | Hub recommendations liên quan traffic hay topology? | Train top degree/inbound + predictions validation | Top-20 target frequency table; overlap/scatter | Hub dominance có thể là hợp lý hoặc generic failure, cần labels | M2D/HITS comparison, case choice |
| E14 P2 | Khoảng cách graph thay đổi theo source degree? | Train-selected sources và H | Sampled directed BFS distance CDF + unreachable fraction | Sample paths khác all-pairs distances; boundary bias nếu sampled H | Có cần multi-step/short walks; không tính APSP |
| E15 P0 | Title/redirect normalization làm mất/gộp gì? | Raw→canonical mapping ledger | Counts by reason, examples, collision table | Collision không được che bằng fuzzy matching | Mapping corrections trước freeze |
| E16 P1 | Subgraph Node2Vec có đại diện cho graph chính? | H full/subgraph, selected U | Degree/traffic CDF overlay, boundary edge/candidate mass | Sampled graph bias phải được nêu | Separate experiment table và scope of inference |

JSD chỉ dùng train monthly published distributions với zero-fill trên union observed support, ghi đó là distribution của counts công bố; smoothing nếu có phải cố định, không dùng để “phục hồi” censored mass. Outgoing concentration có thể bị inflated khi missing low counts.

SCC/WCC trên full H dùng sparse/igraph, không NetworkX object graph nếu vượt RAM. Nếu chỉ chạy sample thì ghi mẫu rõ; không báo sampled SCC như property toàn Wikipedia.

## 3. Result diagnostics và sensitivity plots

| ID / priority | Câu hỏi / biến | Controls | Plot / metric | Kết luận được phép |
|---|---|---|---|---|
| R01 P0 | Main model khác nhau bao nhiêu? | Same Q,C,split | Dot/interval plot macro NDCG; table toàn bộ required metrics | Difference trên observed benchmark |
| R02 P0 | Gain có bị head sources chi phối? | Same predictions | Macro vs weighted metrics cạnh nhau | Traffic imbalance liên quan reporting |
| R03 P0 | Candidate ceiling giới hạn chất lượng? | Same labels | Full vs conditional scores + coverage | Model quality và coverage phải phân biệt |
| R04 P0 | Backoff thay local Markov thế nào? | Same train/val | μ×η validation heatmap, zero-source panel | Tune baseline công bằng |
| R05 P0 | PPR hội tụ và ổn định Top-K? | Same source/damping | L1 residual vs iteration; top10 overlap to exact solution | Numerical convergence, không training loss |
| R06 P0 | Damping đổi proximity/hub bias? | Same solver precision | δ vs NDCG/runtime; hub recommendation frequency | Tradeoff depth/accuracy/cost |
| R07 P0 | λ có region đáng tin hay endpoint tốt nhất? | Frozen M1B/M3 | Validation NDCG/MassRecall vs λ; subgroup panels | Chọn λ bằng validation; test điểm locked duy nhất |
| R08 P0 | More train history giúp hay gây stale evidence? | Same cutoff,H,C,U | 1/2/3 months vs validation metrics | Data-efficiency/history effect, không iid sample-size causal effect |
| R09 P0 | Hybrid có giúp sparse sources? | Bin thresholds train-only | Paired Δ NDCG box/CI theo traffic×degree, sample N | Benefit/harm heterogeneity, không blanket gain |
| R10 P0 | Train-unobserved pairs có được tìm ra? | Full unchanged rankings | Pair-bin Recall/MassRecall bars | Newly observable không đồng nghĩa genuinely new links |
| R11 P1 | Weighting walks có hữu ích? | Same H/p,q/budget/seeds | M5H vs M5W paired plot, mean±seed std | Signal effect under fixed support |
| R12 P1 | Embedding training có vấn đề? | Fixed walk corpus/version | Legitimate loss delta nếu có, validation metrics, norms, tokens/s | Optimization diagnostics; loss không đồng nhất task quality |
| R13 P1 | Kết luận thay đổi theo test horizon? | Frozen primary models | Months05/06 panel, same-source và all-source views | Temporal sensitivity trong hai tháng cụ thể |
| R14 P0 | Accuracy có đáng chi phí? | Same machine/sources | NDCG vs prep seconds, latency p95, RSS | Model selection practical, chưa có online SLA |
| R15 P1 | Normalization ảnh hưởng hybrid? | Same components, val-tuned λ | L1 vs percentile table/plot | Gain có phụ thuộc score scaling |

Không cần đưa tất cả 31 chart vào main report. Main text ưu tiên E02/E03/E06/E10/E12, R01–R10/R14; chuyển audit histograms và P1 vào appendix. Một figure có thể gồm 2–3 panels với chung câu hỏi.

## 4. Error analysis có quy tắc chọn case

Chọn **6–8 sources** sau khi freeze. Quy tắc category định trước; trong mỗi category lấy một source bằng seeded hash trong nhóm có độ chênh metric đủ để quan sát, không chỉ lấy extreme outlier đẹp. Thêm một fixed random source để kiểm tra cherry-picking. Ghi “không tìm thấy” nếu category không xuất hiện, không tạo ví dụ giả.

| Case | Điều kiện thực nghiệm | Hypothesis giải thích cần kiểm tra |
|---|---|---|
| C1 Markov thắng PPR | ΔNDCG(M1B−M3)>0, stable head traffic | One-step click concentration không khớp multi-step centrality |
| C2 PPR thắng Markov | ΔNDCG(M3−M1B)>0, low train traffic | Topology đưa candidates có future observable use lên cao |
| C3 Hybrid thắng cả hai | Δ với cả M1B,M3>0 | Complementary ranks, không chỉ duplicate popularity |
| C4 Hybrid thua baseline | M6B<M1B | Diffusion noise, over-smoothing, validation/test drift |
| C5 Hub dominance | Nhiều global high-degree targets trong top10 | Generic destinations hấp thụ score; kiểm tra relevant thật |
| C6 Low observable traffic / cold source | T_u=0 hoặc low bin | Backoff/candidate prior chi phối; không coi absence là no interest |
| C7 Many competing links | d_H high bin | Candidate difficulty, latency và concentration khác nhau |
| C8 Train-unobserved future transition | c_tr=0,y_test>0 | Newly visible, suppression hay graph mismatch; tránh giải thích certainty |

Mỗi case lưu:

- Title nguyên bản, source ID, graph timestamp, d_in/d_out, component, candidate count.
- T_u, observed training unique transitions và monthly distribution.
- Bar chart future distribution, phần outside candidate màu riêng; low/unobserved gắn label.
- Top-10 từng model: candidate ID/title, rank, raw score, normalized component scores, train count, future count, EH eligibility.
- Rank delta và short paths đóng góp khả dĩ cho PPR nếu có thể trích từ H; nói “plausible structural explanation”, không post-hoc causal proof.
- Node2Vec cosine, embedding availability và seed; không suy semantic meaning từ 2D plot.
- Một đoạn “evidence supports”, một đoạn “alternative explanations”: exposure/layout, template omission, news, censoring hoặc stale graph.

Không dùng current article content để xác nhận chắc sự kiện/links năm 2018. Nếu cần giải thích semantic/historical context, dùng historical revision được ghi timestamp hoặc đánh dấu chưa kiểm chứng.

## 5. Những kết quả bất lợi cần giải thích

**More history làm kém:** kiểm tra nguồn traffic thay đổi, tháng seasonal/event, censoring được cộng dồn, changing eligible mass và stale counts. So fixed parameters với retuned validation variant; không kết luận “overfitting” khi model chỉ cộng counts.

**PPR kém Markov:** có thể next-hop intent không được multi-hop proximity phản ánh, hoặc PPR chưa hội tụ, graph mismatch, hub attraction. Thứ tự kiểm tra: correctness → candidates → numerical precision → model assumption.

**Node2Vec không cải thiện:** kiểm tra token/degree coverage, directed bias convention, norms, seeds, cosine symmetry, context window, support mismatch. Nếu vẫn không giúp, giữ negative result; không thêm neural model chỉ để thắng.

**Hybrid thua:** λ có thể quá ưu tiên topology, score scaling chưa phù hợp, hoặc hai signals redundant. Báo λ=1 endpoint và validation selection; không đổi λ sau test. Deployment recommendation có thể là Markov.

**Macro tăng nhưng weighted giảm:** nhiều low-traffic sources được lợi nhưng head traffic bị hại. Không gộp thành “overall improves”; xác định objective người đọc/source là gì.

**Conditional cao nhưng full thấp:** candidate coverage bottleneck. Không ca ngợi ranker mà bỏ structural incompleteness.

## 6. Tables và report artifacts

| Artifact đề xuất | Rows / columns | Nguồn và checks |
|---|---|---|
| `dataset_summary.csv` | Month/type/count/pair/nodes, raw/filtered | Manifests, int64 totals reconcile |
| `coverage_ledger.parquet` | Stage/reason/sources/pairs/mass | Không double-count exclusion reasons |
| `graph_stats.csv` | Graph ID/N/M/degree/SCC/WCC/reciprocity | Namespace/redirect policy logged |
| `main_results.csv` | Model/split/estimand/metric/value/N/CI | Shared evaluator only |
| `paired_comparisons.csv` | Model pair/metric/Δ/CI/win-loss | Common sources, paired bootstrap |
| `ablation_results.csv` | A-ID/controlled vars/treatment/metrics | Config diff kiểm tra chỉ biến cho phép |
| `subgroup_results.csv` | Group definition/train boundaries/N/metrics | Không dùng test-derived bins |
| `tuning_results.parquet` | Trial/config/val metric/time/status | Không chứa test metric trong search |
| `solver_diagnostics.parquet` | Source/δ/iteration/residual/time | Correct absolute residual |
| `runtime.csv` | Hardware/run/stage/RSS/cold-warm latency | Same hardware; no fabricated timings |
| `case_studies.parquet` | Source/model/target/rank/counts/eligibility | Models thật, frozen run IDs |

Plots tái tạo từ tables, không manually copy numbers. Figure filenames có ID và split; config/hash trong sidecar metadata. Main report cần một evidence-to-RQ table, không chỉ list charts.

## 7. Acceptance criteria cho analysis

- Có connection cụ thể từ ít nhất một EDA finding tới mỗi major design choice.
- Required metrics đủ và denominator/censoring/coverage ghi rõ.
- Có positive/negative cases hoặc ghi không tìm thấy; không hứa cả bốn model-win patterns sẽ tồn tại.
- Có paired uncertainty và sample sizes; không gọi correlated sources hoàn toàn độc lập.
- Mọi significant-performance claim có protocol/test/CI phù hợp; descriptive correlation không được gọi causal.
- Giảng viên có thể đọc một case và tự lần từ raw counts → candidate → score → rank → metric.
