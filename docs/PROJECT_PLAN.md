# Kế hoạch dự án Wikipedia Navigation Mining

**Trạng thái:** kế hoạch hoàn thiện, cập nhật 21/10/2026. Repository đã có code nền và audit dữ liệu từ các lượt trước; chưa có benchmark held-out hoàn chỉnh. Mọi “giả thuyết” là điều cần kiểm định. Phạm vi bàn giao hiện tại là planning, không coi roadmap bên dưới là danh sách công việc đã hoàn thành. Xem [trạng thái thực tế](IMPLEMENTATION_STATUS.md) và [bằng chứng audit](DATA_AUDIT.md).

**Tên đề xuất:** *Topology-Aware Next-Article Ranking on Wikipedia: A Temporal Comparison of Click Frequency and Historical Hyperlink Structure*.

Tên nhấn mạnh ranking theo article nguồn, dữ liệu lịch sử và tín hiệu so sánh. Nếu dùng fallback, đổi sang *Comparing Behavioral and Topological Signals for Next-Step Ranking in Wikispeedia*.

## Phần 1 — Executive assessment

Đề tài có chất lượng học thuật tốt nếu trọng tâm là **khi nào topology bổ sung thông tin cho frequency**. Một kết quả hybrid không thắng Markov vẫn có giá trị nếu thiết kế công bằng, phân tích đủ và tái lập được. Giá trị đóng góp nằm ở comparative framework, không nằm ở số lượng thuật toán hay novelty chưa chứng minh.

Rủi ro khái niệm lớn nhất:

1. Clickstream không cho phép nhận diện lịch sử từng người; chỉ làm **source-conditioned ranking**.
2. Count không công bố không phải true zero; toàn bộ metrics đánh giá observable traffic bị censor.
3. PPR đo multi-step proximity, không tự là xác suất next-click; Node2Vec similarity cũng không mặc nhiên là directed transition preference.
4. Historical graph không phải toàn bộ rendered hyperlink exposure; candidate coverage có thể giới hạn điểm hơn model.
5. Nếu graph lấy từ held-out clicks thì thí nghiệm topology mất tính độc lập.
6. Chọn chỉ queries/candidates mà model làm tốt có thể làm score đẹp giả tạo.

Những giới hạn dữ liệu được xác minh tại [DATASET_FEASIBILITY](DATASET_FEASIBILITY.md); nghiên cứu liên quan ở [LITERATURE_REVIEW](LITERATURE_REVIEW.md). Không đưa tuyên bố về causal effect hoặc online user satisfaction từ offline counts.

## Phần 2 — Formulation được khuyến nghị

**Problem statement:** Cho một bài Wikipedia nguồn `u`, lịch sử transition counts chỉ đến training cutoff và một graph hyperlink độc lập có timestamp không sau cutoff, xếp hạng các bài trong tập outgoing editorial links đã biết của `u`, sao cho thứ hạng phù hợp với các transition được công bố trong tháng tương lai. Báo cả chất lượng trong candidate set và phần nhu cầu quan sát được nằm ngoài candidate set.

| Research question | So sánh quyết định | Bằng chứng phải có |
|---|---|---|
| RQ1: Topology có bổ sung thông tin ngoài frequency không? | Tuned Markov vs topology-only vs hybrid, cùng candidates | Main metrics, paired Δ CI, matched ablations |
| RQ2: Lợi/hại xuất hiện ở loại nguồn nào? | Sparse/dense traffic, low/high out-degree, train-unobserved edges | Stratified curves và case studies |
| RQ3: Multi-step graph ranking có hơn thông tin link đơn giản không? | Uniform, destination in-degree, PPR; PPR-H vs PPR-C∩H | Controlled weighting/support ablations |
| RQ4: Lợi ích có bền theo thời gian và chi phí không? | History size, farther test horizon, runtime/accuracy | Validation curves, temporal panel, cost table |
| RQ5, P1: Embeddings có thích hợp với next-step ranking không? | Node2Vec H vs fixed-support weighted H | Same-subgraph comparator table, seed variability |

**Trong phạm vi:** một edition, monthly aggregate labels, directed sparse graph, CPU-first, simple baselines, PPR và fusion có giải thích, reproducibility.

**Ngoài phạm vi:** true user personalization, session reconstruction từ counts, causal online uplift, end-to-end sequence modeling từ synthetic sessions, neural architecture competition. Không GNN/Transformer/LLM. LTR là P2 và cần label/censoring design riêng.

PPR “personalized” nghĩa restart về query article; không nghĩa personalized theo user. Không dự đoán edge có tồn tại: candidate edges đã biết và target là mức sử dụng tương lai.

## Phần 3 — Dataset decision

Primary có điều kiện: **eswiki Clickstream 2018-01…05 + WikiLinkGraphs 2018-03-01**, lịch sử train 01–03, val 04, test 05. Graph nhỏ hơn English, các file được xác minh tồn tại trong listing. Chọn giai đoạn lịch sử để có topology độc lập có provenance thay vì ghép graph hiện tại với click quá khứ.

Audit đã xác nhận schema và metadata lịch sử, đồng thời phát hiện supplied redirect mapping không đủ tin cậy; mapping được dựng lại từ raw redirect history. Training mass khớp H khoảng 96,27%. Mẫu đã chuẩn bị có 200 queries, 8.094 nodes và 319.694 edges, giữ đầy đủ outgoing candidates của query nhưng mất boundary edges ở intermediate nodes. Do đó chỉ có thể kết luận về **sample-graph ranking**, không full Wikipedia graph. Benchmark, validation candidate coverage và resource gate cho toàn bộ models chưa hoàn tất; Node2Vec còn lỗi backend cần xử lý. Xem [DATA_AUDIT](DATA_AUDIT.md), [dataset strategy](DATASET_FEASIBILITY.md) và fallback Wikispeedia nếu cần.

## Phần 4 — Experimental design

| Mức | Models | Vai trò |
|---|---|---|
| P0 | M0 Global Popularity, M1 Local Markov, M1B tuned backoff | Baselines hành vi mạnh, tránh so với baseline yếu |
| P0 | M2 Uniform Hyperlink, M2D In-degree | Tách candidate availability và global topological popularity |
| P0 | M3 PPR-H, M4C PPR-click | Tách structural proximity và behavioral diffusion |
| P0 | M6B calibrated score fusion | Hybrid tối thiểu, endpoints kiểm chứng được |
| P1 | M4H positive-smoothed weighted H, M6A matrix interpolation | Fixed-support weighting và khác biệt fusion |
| P1 | M5H/M5W Node2Vec trên cùng graph nhỏ | Unweighted/weighted embedding ablation bắt buộc nếu đưa Node2Vec vào báo cáo |
| P1/P2 | HITS-global P1, CycleRank P2 | Authority comparator; cyclic relevance nếu đủ thời gian |

Mọi model dùng chung candidate provider và evaluation source list. Primary selection metric là macro NDCG@10, gain `log2(1+future_count)`. Báo Recall@5/10/20, binary MRR@10, NDCG@10, cùng click-mass Recall và event-weighted reciprocal rank. Macro và traffic-weighted aggregate là hai cột khác nhau.

Thiết kế đầy đủ, công thức, tuning, ablations A1–A9 và leakage gates ở [EXPERIMENT_DESIGN](EXPERIMENT_DESIGN.md). Không triển khai metric trước khi chốt IDCG denominator, empty-positive policy, tie-breaking và candidate failure handling.

## Phần 5 — EDA và analysis

EDA phải quyết định model/evaluation: concentration → Markov baseline; sparse sources → backoff; degree/traffic mismatch → kiểm tra hub bias; low graph coverage → giới hạn claim; monthly drift → temporal split; source imbalance → macro + weighted.

Ưu tiên 12–16 figures có tác dụng rõ ràng hơn hàng chục graph đẹp nhưng khó đọc. Chỉ EDA train/graph và diagnostic validation trước freeze; test EDA sau predictions đã khóa. Inventory, required tables và quy tắc chọn case ở [EDA_AND_ANALYSIS_PLAN](EDA_AND_ANALYSIS_PLAN.md).

## Phần 6 — Kiến trúc

Audit ban đầu ngày 20/10 ghi nhận workspace trống. Khi tiếp tục ngày 21/10, repository đã có Git, configs, package `src/wikinav`, fixtures và tests; phải bảo tồn cấu trúc đó. Không có `AGENTS.md` trong các đường dẫn đã kiểm tra. Không dựng lại repository hoặc coi nó còn trống.

Package dự kiến `src/wikinav/` với `data`, `graph`, `models`, `evaluation`, `analysis`, `utils`; configs tách dataset/model/experiment; artifacts Parquet/CSR/JSON; notebooks chỉ exploration. Một shared candidate provider, một metric engine, model adapters không được đọc test.

Backend hiện có dùng DuckDB embedded cho ingestion/Parquet joins, NumPy/SciPy CSR, matplotlib và `unittest`; core reference dùng standard library. Gensim dành cho Node2Vec P1 và chưa đạt gate training thật. Polars, NetworkX, seaborn và igraph là lựa chọn thay thế nếu có nhu cầu đo được, không cài thêm chỉ vì nằm trong đề xuất ban đầu. Không cần PyTorch/GPU hoặc database server.

API, manifests, tests và compatibility gate ở [IMPLEMENTATION_ROADMAP](IMPLEMENTATION_ROADMAP.md).

## Phần 7 — Roadmap, đầu ra và acceptance

Giả định một sinh viên chính, 12–18 giờ/tuần, 8 tuần; thay đổi effort sau pilot. Không coi optional extension là điều kiện để project complete.

| Tuần | Milestone | Ưu tiên | Deliverable / acceptance |
|---|---|---|---|
| 1 | M1 task + dataset feasibility | P0 | Dataset manifest; graph/title/candidate gate có kết luận; protocol frozen |
| 2 | M2 pipeline + EDA | P0 | Reproducible artifacts, coverage ledger, train EDA, toy tests |
| 3 | M3 baselines + evaluation | P0 | M0–M2D, hand-verified metrics, identical candidates, validation table |
| 4 | M4 graph ranking | P0/P1 | PPR-H/C correctness và residuals; Node2Vec chỉ nếu resource gate đạt |
| 5 | M5 fusion + tuning | P0/P1 | M6B và endpoints; validation curves; frozen model registry |
| 6 | M6 ablation + uncertainty | P0/P1 | A1–A4/A6–A8 core; A5 nếu có embeddings; held-out results |
| 7 | M7 interpretation + report | P0 | 6–8 case studies, report tables, limitations |
| 8 | M8 reproducibility + defense | P0 | Clean rerun, result hashes, real-model demo, defense rehearsal |

**MVP complete:** primary hoặc fallback hợp lệ; M0/M1/M1B/M2/M2D/M3/M4C/M6B; một held-out temporal split (hoặc documented fallback split), toàn bộ required metrics, coverage, core signal/weight/history ablations, paired source-level uncertainty, tuning diagnostics, 6 cases, report/demo có provenance.

**Recommended full:** thêm M4H/M6A, Node2Vec H/W trên cùng manageable graph, HITS-global, một additional temporal window và sensitivity của normalization.

**P2:** CycleRank, English replication, sequence-aware fallback extension, lightweight LTR. Chọn tối đa một, chỉ sau full core hoàn tất.

**Acceptance toàn dự án:** không có serious leakage; tất cả counts/metrics có denominator rõ; model failures không bị loại riêng; scripts tái tạo main tables; uncertainty và negative results được báo; mỗi claim lớn có figure/table/test. Không đặt acceptance bằng một mức tăng accuracy tưởng tượng.

## Phần 8 — Instructor-defense checklist

- [ ] Problem statement phân biệt ranking/edge prediction/session/user.
- [ ] Mỗi model có hypothesis; tuned Markov được giữ làm strong baseline.
- [ ] Graph nguồn độc lập và mốc thời gian có artifact chứng minh.
- [ ] Edge direction, weights, normalization, dangling, candidates giải thích bằng toy example.
- [ ] Baseline uniform tie policy và metric oracle được kiểm thử.
- [ ] Convergence/data-efficiency thay learning curve không thích hợp.
- [ ] A1–A9 có scope; lý do bỏ optional model được ghi trước test.
- [ ] Macro/weighted và cold/sparse/hub groups có sample sizes.
- [ ] Coverage ngoài candidate được công bố; missing không gọi negative.
- [ ] Negative result và chi phí có phân tích.
- [ ] Related work không bị dùng để tuyên bố novelty hoặc dự đoán gain.
- [ ] 20 câu hỏi phản biện có bằng chứng dự kiến trong [RISKS_AND_DEFENSE](RISKS_AND_DEFENSE.md).

## Phần 9 — Risk assessment

Stop-the-line risks: graph có future information, test counts vào features, candidate/source selection theo test, hoặc không chứng minh graph độc lập. Dừng experiment và rebuild artifacts; không chữa bằng disclaimer.

Resource risks xử lý bằng sparse matrices, bounded query evaluation, streaming và separate Node2Vec subgraph. Dataset failure dẫn đến fallback có đổi problem statement. Coverage thấp có thể là finding; không “sửa” bằng thêm edges từ test. Detailed register và feedback-to-action matrix ở [RISKS_AND_DEFENSE](RISKS_AND_DEFENSE.md).

## Phần 10 — Năm việc đầu tiên khi chuyển sang development

Danh sách này là trình tự khởi đầu ban đầu; một phần đã có trong repository. Khi tiếp tục development, dùng năm việc còn lại ở [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md#5-năm-việc-tiếp-theo-khi-chuyển-sang-development), tránh chạy lại ingestion hoặc mở test không cần thiết.

1. **Khóa protocol v1:** edition, months, graph snapshot, candidate policy, query sampling seed, metrics, P0/P1 scope và release-lag disclaimer trong config/manifest.
2. **Environment smoke test:** xác nhận RAM/CPU; thử lock dependencies trên Python 3.11/3.12 hoặc 3.13 nếu wheels tương thích; không cài mọi graph library cùng lúc.
3. **Metadata + bounded sample audit:** đọc schema thật và redirect/page artifact; ghi hash, delimiter, title normalization; quyết định primary go/no-go.
4. **Viết toy fixtures + evaluation tests trước model:** direction, censoring flag, no-future, IDCG, empty candidates, uniform ties.
5. **Pilot train/validation pipeline:** graph/title join, source sample, coverage/RSS/runtime và 4–6 EDA plots; quyết định kích thước chạy chính trước khi truy cập test labels.

## Kế hoạch báo cáo học thuật

Mỗi hàng là một section cần viết sau khi có evidence; không điền kết quả giả vào Abstract/Conclusion.

| Section | Nội dung / toán cần có | Table/figure | Sai lầm cần tránh | Câu hỏi phản biện |
|---|---|---|---|---|
| 1 Abstract | Task, dataset, methods, findings thật, limitation | Không bắt buộc | Hứa hybrid thắng | Kết luận nào có evidence? |
| 2 Introduction | Motivation frequency vs topology, RQ | Một ví dụ source có nhiều links ít clicks | Gọi personalization | Vì sao bài toán có ích? |
| 3 Problem Statement | V, H, C, candidates, labels, score | Task contract table | Trộn link prediction | Model nhận thông tin gì? |
| 4 Related Work | Dataset/task/metric distinctions | Literature matrix | So sánh score khác protocol | Gần paper nào nhất? |
| 5 Dataset | Months, licenses, censoring, sizes measured | Manifest summary, attrition | Dùng raw nodes thành articles | Đã loại bao nhiêu dữ liệu? |
| 6 EDA | Distributions và decisions | E01–E12 | Chỉ plot đẹp | EDA thay đổi gì? |
| 7 Graph Construction | Direction, redirect, support, normalized rows | Toy graph/table, coverage | Dùng test edges | H có độc lập không? |
| 8 Methodology | Model formulas/hyperparameters | Model matrix | PPR score=next-click probability | Vì sao cần multi-step? |
| 9 Experimental Setup | Splits, queries, candidates, seeds, budget, metrics | Timeline, metric definitions | Không rõ denominator | Có công bằng không? |
| 10 Baseline Comparison | All required metrics, cost, coverage | Main table + paired Δ | Chỉ global best | Markov có được tune không? |
| 11 Hyperparameter/Convergence | λ, damping, residuals, history curves | Validation sensitivity | Test tuning; fake loss | Hội tụ khác accuracy thế nào? |
| 12 Ablation | A1–A9 applicable | Controlled contrast matrix | Thay nhiều biến một lúc | Gain do signal nào? |
| 13 Error Analysis | Selected wins/losses, no causal certainty | Case distributions + rankings | Cherry-pick chỉ wins | Hybrid thua ở đâu? |
| 14 Discussion | Answer từng RQ, tradeoffs | Evidence-to-RQ map | Correlation→causation | Dùng model nào trong thực tế? |
| 15 Limitations | Censoring, exposure, historical graph, language | Threats matrix | Vờ có sessions | Kết luận có áp dụng hiện tại? |
| 16 Conclusion/Future Work | Finding trong phạm vi, 1–2 extensions | Không thêm result mới | Novelty không chứng minh | Contribution chính? |
| 17 Reproducibility | Version, config/hash, commands, hardware | Run manifest, test summary | Hardcoded paths | Người khác rerun thế nào? |

## Presentation và demo

Presentation 12–15 phút, khoảng 10 slides: (1) task/RQ; (2) dữ liệu và giới hạn; (3) timeline/candidates; (4) EDA motivation; (5) baselines/models; (6) metrics + fairness; (7) main results thật; (8) ablation/sensitivity; (9) failure cases và resource tradeoff; (10) contribution/limitations. Appendix: formulas, manifests, tests, literature, detailed defense.

Demo local bằng Streamlit hoặc CLI + notebook view, không cần production hosting. Chọn source trong query registry, xem cùng candidate set và Top-10 M1/M3/M5 nếu có/M6; hiển thị train counts, hyperlink eligibility, component score, ranking delta và future distribution **chỉ ở evaluation view**. Slider λ dùng frozen component scores; λ tối ưu phải đánh dấu là validation-selected, không cho demo trở thành test tuning.

Demo phải đọc artifact model/prediction đã tính, run_id và graph hash; không hardcode bảng recommend. Chế độ sparse/high-degree source giúp trả lời “vì sao thứ hạng khác nhau?”. Nếu offline cache, ghi rõ cache từ model nào và seed nào; không giả vờ tính online.

## Self-review và claim–evidence contract

| Chiều rà soát | Câu hỏi | Trả lời ở planning / bằng chứng còn thiếu |
|---|---|---|
| Contribution | Có cần thuật toán mới? | Không; comparative reproducible study. Chưa có empirical finding |
| Clarity | Task/labels có thống nhất? | Source-only, monthly observable relevance; xem protocol |
| Experimental strength | Có baseline đủ mạnh? | M1B tuned + M0 + simple topology; chưa có scores |
| Completeness | Có robustness và ablation? | Đã thiết kế, chưa chạy; scope phân P0/P1 |
| Soundness | Graph có future leakage? | Nguồn độc lập có timestamp; redirect/data integrity cần M1 gate |

Claim: “Topology giúp nhóm ít dữ liệu” | Evidence: A7 + paired CI + cases | **Chưa kiểm định**.

Claim: “Hybrid tốt hơn Markov” | Evidence: held-out main table, fixed candidates, strong baseline | **Chưa kiểm định, không phải lời hứa**.

Claim: “Chạy được trên máy sinh viên” | Evidence: measured RSS/runtime và clean rerun | **Resource budget hợp lý nhưng còn pilot**.
