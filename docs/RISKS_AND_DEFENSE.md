# Risk register, phản hồi giảng viên và chuẩn bị bảo vệ

> **Lưu trữ planning:** các trạng thái “chưa chạy”, blockers và effort dưới đây phản ánh thời điểm thiết kế. Implementation và real study hiện đã hoàn tất trong scope đã chốt; xem [trạng thái hiện hành](IMPLEMENTATION_STATUS.md), [frozen protocol](RUN_PROTOCOL.md) và [báo cáo kết quả](../reports/REPORT.md). Không dùng proposal như chứng nhận experiment đã chạy.

Planning 20/10/2026. Xác suất là assessment định tính trước pilot, không phải frequency đo được. Severity: **C**=critical/blocker, **H**=high, **M**=medium. Likelihood: H/M/L. Chủ sở hữu các mitigation là người phụ trách module tương ứng trong roadmap; với một sinh viên thì cùng một người nhưng checklist vẫn tách vai trò.

**Cập nhật 21/10 — risks đã gặp:** D4 (supplied redirect mapping sai lệch), D8 (ngưỡng count/header khác giả định), D9 (duplicate raw groups), M12 (boundary loss khi sampling) và E6 (Gensim native warning) đã xảy ra, không còn chỉ là xác suất dự báo. [DATA_AUDIT](DATA_AUDIT.md) ghi cách xử lý dữ liệu và bằng chứng; [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md) ghi backend blocker. Mapping dựng lại vẫn cần giới hạn về title moves/extraction; Node2Vec chưa được coi là validated trên dữ liệu thật. Các câu trả lời bảo vệ phía dưới là câu trả lời thiết kế, chưa phải kết luận thực nghiệm.

## 1. Risk register

| ID | Risk | Severity / likelihood | Impact | Detection | Mitigation | Fallback |
|---|---|---|---|---|---|---|
| D1 | Không có real sessions/users | H / chắc chắn với Clickstream | Sai task/claim | Schema audit | Source-only task, query-personalized wording | Wikispeedia cho sequence question, đổi claim |
| D2 | Privacy suppression | H / H | Missing≠negative, biased recall | Threshold docs + count histogram | Observable-label estimand, separate low/unobserved groups | Báo limitation; không reconstruct missing events |
| D3 | Missing held-out labels | H / H | Nguồn không đánh giá được | Q_all vs U ledger | Common eligible Q, count no-label, no substitute sources | Thu hẹp inference population |
| D4 | Redirect/title mismatch | C / M | Sai joins và fake cold start | Collision/unmatched audit | Snapshot mapping, no current API, no fuzzy auto-match | Exact-match subset có ledger hoặc fallback dataset |
| D5 | Hyperlink snapshot future/misaligned | C / M | Leakage hoặc invalid environment | Timestamp/lineage assertion | Historical H trước evaluation, frozen mapping | Re-date all splits hoặc Wikispeedia |
| D6 | Graph thiếu template/new links/isolates | H / H | Candidate ceiling thấp | Pair/mass coverage, inventory audit | Historical editorial-link wording, full+conditional metrics | Narrow setting hoặc SQL snapshot nếu xác minh được |
| D7 | Graph built from test clicks | C / M | Không còn độc lập topology | Parent manifest / hash | H constructor chỉ đọc independent dump | Rebuild; không có H → behavior-only đổi title |
| D8 | Schema thay theo release | H / M | Parse sai/counted sai | Delimiter/types/min counts/sample | Versioned schema validation | Chọn verified release |
| D9 | Duplicate raw/canonical pairs | H / M | Frequency bias | Duplicate keys + mass reconciliation | Flag raw duplicates, sum canonical collisions đúng | Re-ingest |
| D10 | Archive inaccessible/corrupt | H / M | Không tái lập | HTTP/checksum/gzip | Manifest + hashes, bounded verification | Wikispeedia small archive |
| M1 | Invalid negative sampling | H / M | Chấm model bằng false negatives | Review label/negative creation | Full candidate ranking, censoring flag | Bỏ LTR/link-AUC experiment |
| M2 | Unfair candidate sets/exclusions | C / M | So sánh vô nghĩa | Per-source hashes, Q diff | Shared provider, failure policy | Rerun toàn bộ shared evaluator |
| M3 | Metric chỉ thưởng popularity | H / H | Che long-tail failure | Macro vs weighted divergence | Binary+graded+mass metrics, train strata | Giới hạn claim head/tail |
| M4 | Node2Vec không giúp next-step | M / M | Tốn thời gian nhưng không gain | Validation + directed tests + seeds | Treat as hypothesis, shared subgraph controls | Giữ negative result hoặc bỏ P1 trước test |
| M5 | Hybrid lặp popularity | H / M | Gán nhầm value cho topology | M0/M2D controls, A3/A4 | Compare tuned M1B; normalize; endpoints | Chọn Markov nếu phù hợp |
| M6 | PPR personalization bị hiểu sai | H / M | Overclaim user behavior | Terminology review | Restart-at-article definition | Rename source-conditioned ranking |
| M7 | Temporal evaluation quá ít | H / M | Kết luận không bền | Split registry | One extra window/horizon P1 | Nói rõ single historical split |
| M8 | Exposure/position bias | H / H | Offline usage≠intrinsic relevance | L2 motivation; thiếu impression fields | Không claim causal/user satisfaction | Chỉ predictive historical ranking |
| M9 | Test dùng tuning/EDA/sample | C / M | Held-out invalid | Freeze time, config lineage | Test-only evaluator, predictions trước labels | Holdout mới; mark exploratory |
| M10 | Bootstrap coi sources độc lập hoàn toàn | M / H | CI quá tự tin | Dependence review | Paired source bootstrap caveat; temporal/block sensitivity | Descriptive intervals, không significance claim |
| M11 | Publication lag bị bỏ qua | M / H | Retrospective bị gọi deployment | available_at vs event_month | Explicit retrospective protocol | Lagged split nếu cần deployable claim |
| M12 | Sampling đổi topology | H / M | Biased paths/coverage | Boundary edges + degree CDF | Full H query sample; separate subgraph table | Scale back claims |
| E1 | Graph/title join vượt RAM | H / M | OOM, không hoàn tất | Pilot RSS/projection | CSR, partitioned joins, bounded batches | Smaller edition/sample hoặc fallback |
| E2 | Per-source PPR quá chậm | H / H | Không tune/evaluate kịp | 100-query timing/residual | Cache, fewer preselected queries, validated approximation | Essential smaller benchmark |
| E3 | Node2Vec walks/aliases quá lớn | H / H | Memory/time blow-up | Tokens budget, Σdin·dout estimate | Small shared graph, on-demand sampler, streamed corpus | Drop P1 M5 pair |
| E4 | Preprocessing không tái lập | H / M | Counts/IDs thay đổi | Hash rerun | Deterministic mapping, immutable manifests | Rebuild from raw verified data |
| E5 | Tuning quá rộng | M / H | Trễ report/analysis | Trial/time budget | Coarse-to-fine, cached scores, fixed grid | Cắt optional knobs/models |
| E6 | Package/backend khác semantics | H / M | Weighted/directed bị bỏ | Tiny asymmetric graph tests | Pin version, audit flags/code, oracle | Small custom audited adapter |
| E7 | PPR không hội tụ hoặc tol sai | H / M | Results numerical artifacts | Absolute residual and exact oracle | Bound error/max_iter log | Retry precision; documented common fallback |
| A1 | Baseline yếu hoặc thiếu rationale | H / M | Instructor phản biện fairness | Model/RQ matrix | Raw+tuned Markov, uniform, indegree; HITS plan | Thêm cheap control trước test |
| A2 | Ablation thay nhiều factors | H / M | Không quy gain đúng tín hiệu | Config diff/support hash | Fixed support/solver/candidates | Report confounded contrast honestly |
| A3 | Error analysis hời hợt | H / M | Không trả lời “why” | Case evidence checklist | Wins/losses, counts/degrees/rank deltas | Giảm models, tăng depth |
| A4 | Thiếu validation diagnostics | H / M | Không chứng minh model selection | Tuning logs/curves | Residual/history/λ/seed plots | Không manufacture epoch loss |
| A5 | EDA không liên quan method | M / M | Report trang trí | Figure→decision mapping | EDA inventory có action | Bỏ decorative charts |
| A6 | Overclaim novelty/personalization | H / M | Sai academic positioning | Literature/claim review | Comparative framework scope | Rewrite title/abstract |
| A7 | So dataset khác như cùng task | H / M | Invalid external validity | Report table dataset/task tags | Separate Wikispeedia game results | Đổi report scope |
| A8 | Lịch dự án thiếu thời gian report | H / M | Có code nhưng không defend được | Weekly DoD review | P0-first, reserve weeks7–8 | Bỏ P1/P2 trước khi bỏ analysis |

Critical fail ở D4/D5/D7/M2/M9 không chỉ được ghi limitation: phải dừng comparison bị ảnh hưởng, sửa data/protocol và rerun. Risk quality thấp nhưng không leakage có thể được chấp nhận với narrowed claim và evidence.

## 2. Feedback-to-Action Matrix

| Instructor concern | Project design decision | Implementation component | Evidence / figure trong report | Câu hỏi bảo vệ |
|---|---|---|---|---|
| “Problem statement?” | Task A, conditional link transition, historical candidates | Config schema/task contract | Formal V,H,C,R,s và split table | Input/target chính xác là gì? |
| “Motivation of architecture?” | Mỗi model gắn RQ, không GNN vì danh tiếng | Model registry | Model–signal matrix | Vì sao PPR/Node2Vec? |
| “Why conventional baseline?” | M0, raw/tuned M1, uniform, indegree | Baseline adapters | Main table và μ/η tuning | Baseline có bị cố tình yếu? |
| “Why not HITS?” | HITS-global P1; query-local HITS ngoài core | HITS adapter optional | Cost/performance + scope explanation | HITS so gì với PPR? |
| “Comparison to related works” | Verified matrix, task/split khác nhau | Bibliography/report notes | L1–L11 matrix | Đề tài khác CycleRank thế nào? |
| “Missing validation loss” | Tách estimator/fixed-point/SGNS | Tuning and solver logger | PPR residual, history curves, legitimate SGNS loss | Model này có training loss không? |
| “Learning curve / k-fold” | Temporal validation, history curve, rolling P1 | Split registry | Accuracy vs history/horizon | Vì sao không random k-fold? |
| “No grid search” | Coarse-to-fine budget từng model | Config-driven tuner | Validation grid và chosen config | Chọn λ/δ thế nào? |
| “Ablation two-stage model” | A1–A6 signal/support/weight controlled | Ablation runner/config diff | Endpoint, fixed-support comparisons | Gain do component nào? |
| “Effect of normalization” | L1 fusion default, percentile P1 | Fusion normalizer | Normalization sensitivity | Vì sao cộng score được? |
| “EDA relation to method?” | Mỗi plot có decision | EDA/report scripts | E02→macro, E03→Markov, E10→coverage | EDA thay đổi protocol gì? |
| “Class imbalance/per-class” | Source traffic và pair sparsity strata | Group metrics | Macro/weighted, tail bins N/CI | Ai được lợi, ai bị hại? |
| “Why more data worsens?” | Trailing 1/2/3 month control | History-window runner | Drift+history curve | Stale counts hay overfit? |
| “Confidence analysis” | Paired bootstrap + seed variation | Statistics module | Δ CI, win/loss source plot | Kết luận ổn định không? |
| “Edge representation?” | Directed sparse H and C, int64 counts | Graph builder | Matrix toy, row sums, dtype table | Có giữ direction không? |
| “Output/loss suitable ranking?” | Score per candidate, metric oracle | Shared scorer/evaluator | Formula + hand-computed fixture | Output có là probability? |
| “How combine graph/other score?” | M6A matrix vs M6B normalized score | Hybrid adapters | Endpoint tests/λ curve | Hai fusion khác ở đâu? |
| “How PageRank improves authority?” | Không mặc định improves; indegree/HITS controls | M2D/M3/HITS | Hub bias and held-out ranking | Authority có tương đương navigation? |
| “Superficial results” | 6–8 systematic win/loss cases | Case selector + report | Future distributions, counts, rank delta | Model thua vì điều gì? |
| “Reproducibility?” | Manifests, versions, clean rerun | CLI/locks/tests | Run registry/checksums | Tái tạo bảng chính thế nào? |

Không áp feedback “BERT/FastText/neurons” vào dự án máy móc. Với graph ranking, câu hỏi tương ứng là input/output/transition/scoring/cost; không cần neural architecture để có đồ thị learning curve.

## 3. Defense questions và câu trả lời dự kiến

Đây là câu trả lời về **thiết kế**. Chỗ cần empirical evidence phải thay bằng kết quả thật sau thí nghiệm, không nói “đã chứng minh” ở planning.

### Q1. Vì sao đây là next-article recommendation, không phải link prediction?

Candidate links đã biết tại historical snapshot. Model xếp hạng destination theo usage quan sát trong tháng tương lai, không dự đoán edge tồn tại hay xuất hiện. Ground truth là count, không binary graph adjacency. Evidence: task contract, C(u), candidate tests và full denominator metrics trong `EXPERIMENT_DESIGN`.

### Q2. Vì sao dùng directed graph?

Khả năng đi u→v không đòi v→u; counts và outgoing candidates có hướng. Symmetrize sẽ tạo hành động không có trong môi trường và đổi random walks. Evidence: toy A→B test, E06 degree/reciprocity và directional transition audit.

### Q3. Edge weights biểu diễn thế nào?

H là binary directed edges từ nguồn độc lập; C là int64 published training counts; P row-normalized. M4H thêm prior mass trên H và vẫn giữ count gốc riêng. Missing sparse value 0 là storage convention, không true zero. Evidence: graph manifest, row-sum tests và formulas.

### Q4. Vì sao cần PPR nếu đã có Markov?

Markov chỉ dùng outgoing training usage của nguồn; PPR chia sẻ thông tin qua nhiều hops, có khả năng giúp sparse sources. Đây là hypothesis; PPR cũng có thể bị hubs và không đúng next-step intent. Evidence cần có: M1B vs M3/M6B, A7, R06/R09, cases C1/C2.

### Q5. Vì sao chọn Node2Vec?

Để kiểm tra proximity representation từ walks có bổ sung cho direct frequency và diffusion không, với scoring rẻ sau fit. Không dùng vì “deep learning tốt hơn”; cosine symmetry là limitation. Evidence: M5H/M5W cùng support, seeds, validation/time curves và case analysis. Nếu không qua resource gate thì bỏ P1.

### Q6. Topology đóng góp gì ngoài counts?

Nó cung cấp links chưa có observable history và cấu trúc nhiều bước. Chỉ kết luận useful khi controlled hybrid vượt tuned behavior baseline trên common C/Q với uncertainty phù hợp; nếu không, topology chỉ giúp eligibility hoặc không thêm predictive value. Evidence: A2/A3/A4/A7 và M2D control.

### Q7. “Personalized” nghĩa gì?

PPR restart ở article u, nên là query/source-personalized relevance. Không có user ID/profile/session trong main task. Evidence: model input interface, e_u definition và dataset schema.

### Q8. Vì sao không chỉ dùng HITS?

HITS-global là authority comparator P1, còn PPR có restart theo nguồn. HITS gốc có query/root-set variants; không gọi global authority là đúng mọi variant. Với scope nhỏ, indegree P0 kiểm soát global structural popularity, HITS thêm nếu đủ thời gian. Evidence: HITS/PPR row trong model matrix, A10, literature L11/baseline reference.

### Q9. Làm sao biết improvement do graph information?

Giữ dataset, candidates, queries, score normalization và tuning budget tương đương; so λ endpoints và fixed-support weights. In-degree/HITS giúp phân biệt generic hub effect. Dù vậy observational ablation chỉ hỗ trợ predictive contribution, không causal human behavior. Evidence: config diff, A3/A4/A6, paired Δ.

### Q10. Ngăn data leakage thế nào?

Train-only counts; H độc lập có timestamp; frozen mapping/query/C; tuner chỉ đọc validation; test chỉ evaluator sau freeze. Thay test labels không đổi training artifacts. Evidence: manifests/lineage hashes, month assertions, candidate hash tests, freeze log.

### Q11. Xử lý unobserved/low-frequency edges?

Giữ observation flag; không gọi là reliable negative. Markov backoff và M4H prior là assumptions để chấm điểm, không điền “true clicks”. A7 tách observable low counts và train-unobserved nhưng test-visible. Evidence: E01/E11, missingness policy và subgroup counts.

### Q12. Vì sao Recall, MRR và NDCG?

Recall đo unique relevant destination coverage; MRR đo hit đầu; NDCG đo graded ranking theo future count đã transform. MassRecall/ExpectedRR bổ sung traffic expectation. Mỗi metric có bias nên dùng nhiều góc nhìn với macro/weighted, không chọn metric thắng sau test. Evidence: formula/oracle fixture, main/conditional table.

### Q13. Vì sao chronological splits?

Target là future navigation; random row split trong monthly aggregates làm lẫn thời gian và không kiểm tra drift. Chronological split tránh feature nhìn future counts nhưng vẫn phải audit graph/mapping. Evidence: timeline, disjoint months tests, E12, A9 nếu chạy.

### Q14. Learning curves hoặc convergence diagnostics ở đâu?

Markov không có epochs/loss; dùng validation vs history và μ/η. PPR dùng L1 residual vs iterations và δ/runtime. Node2Vec dùng backend-supported SGNS loss/validation metrics, kiểm tra loss accumulation trước. Evidence: R04–R08/R12, solver logs; không manufacture neural-style curves.

### Q15. Nếu hybrid kém thì làm gì?

Báo kết quả, xem λ validation, redundancy/popularity/drift và failures; không sửa λ bằng test. Có thể khuyến nghị Markov do tốt/rẻ hơn. Evidence: λ endpoints, C4, source strata, cost table. Negative result không làm project thất bại nếu protocol đúng.

### Q16. Complexity PPR và Node2Vec?

Exact PPR S queries là O(SI(M+N)), graph memory O(M+N) nếu giải tuần tự; không lưu dense all-pairs. Node2Vec walk tokens≤NrL, SGNS O(E NrL w(k_neg+1)d); alias memory có thể tăng theo Σdin·dout. Evidence: resource formula, pilot measured RSS/time, cap/subgraph manifest.

### Q17. Dataset đại diện real human navigation đến đâu?

Clickstream phản ánh aggregate requests đã lọc và suppress, không toàn bộ sequences hay exposure. Historical Spanish edition giới hạn thời gian/ngôn ngữ; Wikispeedia là gameplay có goal. Evidence: dataset limitations, L1/L5/L8, coverage ledger. Không tuyên bố đại diện mọi user.

### Q18. EDA ảnh hưởng methodology cụ thể thế nào?

Traffic imbalance dẫn tới macro+weighted; concentration dẫn tới strong local baseline; degree/traffic mismatch dẫn tới hub controls; low coverage dẫn tới full/conditional reporting; monthly changes dẫn tới history/temporal tests. Đây là mapping dự kiến, sẽ cập nhật bằng findings thật. Evidence: EDA inventory và evidence-to-decision table.

### Q19. Kết luận ổn định không?

Sẽ báo paired source-level CI, seed variability, strata và temporal windows nếu đủ. Sources và months không hoàn toàn độc lập nên không claim significance quá mức. Nếu CI rộng hoặc direction đổi theo month, kết luận là không ổn định trong budget dữ liệu. Evidence: paired Δ, A9, seed table.

### Q20. Contribution chính là gì?

Một comparative framework và phân tích có kiểm soát về click frequency/topology trong next-article ranking, cùng code/data manifests tái lập. Không claim thuật toán graph mới. Evidence: report RQ answers, ablations, reproducibility bundle; novelty statement đối chiếu L2/L3/L4.

### Q21. Test destination không nằm trong candidates thì sao?

Rank=∞, đóng góp 0 numerator và vẫn nằm trong full denominator/IDCG; conditional metrics là bảng phụ riêng. Unknown title/node không được tạo feature mới. Evidence: metric fixture có D ngoài C, coverage ledger và R03.

### Q22. Có thể gọi offline click share là CTR không?

Không như online CTR vì không có impressions của recommendation system và không biết exposure propensities. Dùng tên MassRecall/observed click coverage; không suy user uplift. Evidence: metric glossary và threats-to-validity.

### Q23. Dùng graph lịch sử xuất bản sau thời điểm đánh giá có leakage không?

Content phải tái dựng đúng cutoff và không dùng thông tin structural tương lai; đó là retrospective content-time benchmark. Nó không mô phỏng availability của artifact ở năm đó. Redirect/title reconstruction vẫn cần audit. Evidence: content_at/available_at manifest và protocol disclaimer.

### Q24. Tại sao không random k-fold cho confidence?

Random folds phá mục tiêu temporal generalization và có thể để tháng sau dự đoán tháng trước. Dùng temporal validation/rolling P1, bootstrap trên evaluation units để quantify conditional uncertainty. Evidence: split registry và statistical analysis.

### Q25. Nếu có nhiều relevant items, MRR có che lỗi không?

Có: chỉ cần một hit sớm là RR cao dù misses hầu hết future mass. Vì thế dùng Recall/NDCG/MassRecall và phân biệt ExpectedRR với first-hit RR. Evidence: metric toy fixture và source distribution plots.

## 4. Defense evidence checklist

| Bằng chứng | P0/P1 | Điều kiện hoàn thành |
|---|---|---|
| Formal task và candidate policy | P0 | Giảng viên phân biệt được input/label/candidate |
| Data source/date/hash và attrition | P0 | Có audit trail từ raw tới graph/count |
| Tiny graph numerical examples | P0 | Direction, normalization, PPR, metrics tính tay khớp |
| Strong baseline validation | P0 | Có μ/η và fallback evidence |
| PPR residual/δ/time | P0 | Không chỉ một accuracy number |
| Signal/support/weight ablation | P0/P1 | Mỗi contrast khai báo biến thay đổi |
| Macro/weighted/full/conditional tables | P0 | Mẫu số và sample size rõ |
| Paired uncertainty + cases | P0 | Có failures, không chỉ wins |
| Node2Vec H/W seed diagnostics | P1 | Bắt buộc nếu report có claim về embeddings |
| Temporal extra window | P1 | Nếu bỏ phải hạn chế robustness claim |
| Clean run và real-model demo | P0 | Không hardcoded recommendations |

## 5. Adversarial self-review trước nộp

1. **Contribution:** câu trả lời RQ nào mới trong experiment này? Nếu chỉ “model A cao hơn”, thêm stratified explanation hoặc giới hạn claim.
2. **Clarity:** mỗi score/metric có một định nghĩa duy nhất? Tìm các từ “personalized”, “zero”, “CTR”, “session”, “novel” và rà lại context.
3. **Strength:** đã tune strong baseline ngang mức hợp lý chưa? Có cost evidence để biện hộ model phức tạp không?
4. **Completeness:** có coverage, ablation, validation, uncertainty và negative cases? Nếu thiếu, cắt optional algorithm để hoàn tất.
5. **Soundness:** có model nào nhìn future counts/edges/redirects? Nếu có, invalid experiment phải sửa, không chỉ thêm limitation.

Kết quả review ghi `pass`, `needs revision`, `needs experiment` kèm artifact pointer. Ở planning, empirical rows vẫn là `needs experiment`; không đánh dấu pass trước khi chạy.
