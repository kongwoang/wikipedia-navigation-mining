# Nâng chất lượng học thuật — review ngày 22/10/2026

> **Cập nhật hoàn tất 22/10/2026:** toàn bộ nhóm thí nghiệm dưới đây đã được thực hiện theo [EXTENSION_PROTOCOL](EXTENSION_PROTOCOL.md): full graph, ba rolling windows, tie-break, degree null, query panels, CycleRank và adaptive fusion. Xem [kết quả thực tế](../reports/EXTENSION_RESULTS.md). Availability blockers/effort bên dưới là lịch sử tại thời điểm review, không trạng thái hiện hành. Original study-v3 vẫn giữ nguyên.

Mục tiêu là tăng sức thuyết phục khi giảng viên hỏi **“vì sao kết quả như vậy, có đáng tin và tái lập được không?”** Không thể bảo đảm điểm số khi chưa biết rubric. Giữ nguyên study-v3; mọi analysis mới sau khi xem May/June được ghi exploratory, và mọi model mới cần validation/fresh holdout phù hợp.

## 1. Đánh giá thẳng bản hiện tại

Điểm mạnh: task đúng, graph độc lập, chronological split, baseline Markov mạnh, coverage accounting, model/metric tests, reproducibility, honest negative results và case evidence. Đây là empirical comparative study có literature review, không survey thuần hoặc novel-model paper.

Điểm yếu quan trọng nhất không phải ít baseline:

1. **Boundary loss:** graph models dùng induced graph chỉ giữ 30,82% outgoing edges của sampled nodes. Giữ query candidates 100% không giữ toàn bộ random-walk process. Kết luận “PPR kém” cần giới hạn hoặc replication trên graph lớn/full.
2. **Effective sample:** 200 queries nhưng chỉ 127/122 có May/June labels; cold bin 0/1. Tăng nominal query count không tự tạo representative evaluation.
3. **Temporal breadth:** hai test months với cùng predictions chỉ là horizon check, chưa rolling-origin retraining.
4. **Mechanism:** bảng 14 models chưa đủ giải thích topology giúp gì ngoài popularity hoặc tie breaking. Nhiều variants thuộc cùng family; không quảng bá là 14 independent algorithms.
5. **Primary effect:** fusion gain nhỏ, source CI chứa 0; cần giải thích và kiểm chứng, không mở thêm grid đến khi có score đẹp.

Một đồ án chỉn chu cần câu chuyện: **local frequency bảo toàn lựa chọn đã quan sát; topology có thể xử lý một phần ranking uncertainty, nhưng propagation/hubs có thể làm hỏng các lựa chọn đó.** Đây là hypothesis được current evidence gợi ý, chưa universal conclusion.

## 2. Cải tiến đã thực hiện ngay: giải thích hai loại sai số

[Phân tích bổ sung](../reports/extensions/mechanism-v1/ANALYSIS.md) dùng nguyên frozen predictions, không training hoặc tải raw data mới.

- Phân rã NDCG theo targets có/không có published training count, giữ full per-source IDCG.
- Phân rã tổng gap thành candidate limitation và ranking regret bằng same-candidate oracle.
- Kiểm tra 747 non-NA decompositions bằng stored scores, lưu full precision/per-source evidence và source bootstrap intervals.

May, PPR−Markov có **−0,600714** từ train-observed targets và **+0,014236** từ train-unobserved targets. Fusion−Markov tương ứng **+0,000356** và **+0,003938**. Đây là câu trả lời “why” cụ thể hơn “model A cao hơn B”. Cả overall/component gain của fusion vẫn có CI chứa 0.

Candidate-oracle macro NDCG là 0,970325 May và 0,954363 June. Oracle chỉ dùng diagnostics, không nằm trong competitive model table và tuyệt đối không trở thành candidate generator dùng future labels.

## 3. Các thí nghiệm ưu tiên theo giá trị học thuật

| Ưu tiên | Thí nghiệm | Câu hỏi được giải quyết | Controls bắt buộc | Evidence / acceptance | Effort dự kiến, chưa đo |
|---|---|---|---|---|---|
| P0 | Frozen-output mechanism/ceiling decomposition | Gain/loss đến từ phần nào? | Original rankings, full IDCG, unchanged query set | Additive identity; model≤oracle; post-hoc label | Đã làm |
| P0 | Graph boundary sensitivity | PPR kém vì model hay do graph bị cắt? | Cùng queries/candidates/counts/knobs, chỉ đổi context graph | Coverage invariance, retention, rank overlap, quality/cost theo graph size | 1–2 ngày engineering/pilot |
| P0 | Fresh temporal confirmation | Kết luận có sống ngoài May/June đã xem không? | Freeze protocol trước parsing holdout; candidate chronology | New-period metrics/coverage/CI, no retuning on test | 1–2 ngày nếu data accessible |
| P1 | Markov + topology tie-break | Cần fusion thực sự hay chỉ xử lý count ties? | Strict count order preserved; cùng PPR/candidates | Compare Markov/hash, Markov/PPR tie-break, fusion; tail/head contribution | 0,5–1 ngày |
| P1 | Degree-preserving topology null | Tín hiệu từ cấu trúc cụ thể hay chỉ degree/hubs? | Giữ query outgoing edges, nodes, degrees; chỉ rewire other H edges | Degree/candidate assertions, multiple null seeds, descriptive deltas | 1–2 ngày |
| P1 | Query-sample sensitivity | Kết luận phụ thuộc 200 nguồn đã chọn không? | Train-only sampling; tách query variation khỏi graph variation | Per-stratum N/coverage, variability between panels | 0,5–1 ngày sau graph audit |
| P2 | CycleRank | Cyclic relevance có giảm hub dominance không? | Directed semantics, same candidates, validated implementation | Comparison PPR/Markov/indegree, runtime, failure cases | 1–3 ngày tùy implementation |
| P2 | Adaptive fusion | Có nên tin topology theo độ chắc chắn của local counts? | Chỉ train-derived features; validation; fresh test | Strong controls, frozen gating rule, no novelty claim | Sau các controls trên |

Effort là ước lượng một người đã có codebase, không thời gian đã thực thi. Không bắt buộc chạy mọi hàng để dự án đạt chất lượng. Gói khuyến nghị là decomposition + boundary + temporal + tie-break; giữ rewiring/CycleRank ngoài critical path nếu budget thiếu.

## 4. Boundary audit: ưu tiên mở context, không đổi bài toán

Trước hết giữ đúng 200 sources hiện có và outgoing candidate hashes. Không tăng cả số queries và graph size trong một experiment rồi quy chênh lệch cho topology.

**Phương án ưu tiên:** pilot full historical H PPR-H trên 10 queries được chọn bằng train-only stable hash, trước khi xem quality mới. Full H đã được ingest có 36.333.722 edges và 2.077.467 canonical nodes. Với float64 values và int32 indices/indptr, riêng một CSR cần xấp xỉ **444 MB** (decimal), chưa gồm transpose, COO construction, title/index mapping, solver vectors, DuckDB và temporary copies. Đây là lower-level storage calculation, không peak RSS claim.

Đo construction RSS/time và per-query solve time trước khi quyết định chạy 200 queries. Resource gates đề xuất cần khóa trước chạy: peak process RSS≤8 GiB; projected scoring≤30 phút; nếu không đạt thì dùng nested context graphs theo budget, ghi rõ vẫn chưa full-graph. Không cần fit full-graph Node2Vec cho experiment này.

So tối thiểu Markov, PPR-H và score fusion; PPR-C/WH thêm nếu budget cho phép. Baseline local/global scores từ full training corpus giữ nguyên, knobs từ original validation giữ nguyên cho sensitivity. Với nested samples, U0⊂U1⊂U2 phải được tạo chỉ từ historical H bằng deterministic expansion/node selection; không bổ sung edges theo test positives.

Báo: graph V/E, retained outgoing fraction, query candidate invariance, per-source rank overlap, NDCG delta vs U0, residual, peak RSS và runtime. Larger graph không tự chứng minh convergence tới full answer; chỉ full H hoặc validated approximation mới cho phép gọi full-graph PPR. Nếu PPR vẫn kém ở context lớn, kết luận mạnh hơn; nếu đổi nhiều, report phải nhận boundary sampling là yếu tố quan trọng.

## 5. Temporal confirmation: không tái sử dụng test cũ như chưa xem

May/June study-v3 đã dùng phân tích và phát sinh hypotheses. Các model/control được thiết kế bây giờ không được gọi “pre-registered” trên cùng hai tháng đó.

**Availability check ngày 22/10:** [official August2018 index](https://dumps.wikimedia.org/other/clickstream/2018-08/) liệt kê `clickstream-eswiki-2018-08.tsv.gz`, 38.059.784 bytes. Đây mới là directory listing; chưa tải/parse hoặc xác minh raw checksum/schema. July/September directory requests và direct archive HEAD trả HTTP403 trong môi trường này; chưa coi hai tháng đó accessible. Không nói đã có rolling data khi chỉ đoán URL.

Nếu July/August/September đều xác minh được, khóa trước một rolling protocol:

| Window | Train | Validation | Test |
|---|---|---|---|
| W1 | Mar–May | June | July |
| W2 | Apr–June | July | August |
| W3 | May–July | August | September |

Toàn bộ models/grid/query policy/graph policy/metric/contrast phải được khóa trước W1 test read. Việc July trở thành validation trong W2 là chronological advancing-origin hợp lệ **khi không thay protocol theo W1 score**. Mỗi window ghi predictions trước đọc test của window đó. Không coi windows là độc lập: overlaps và source reuse cần per-window reporting, không nhân số samples giả tạo.

Giữ H01/03 cố định giúp kiểm soát topology nhưng cũng làm snapshot ngày càng cũ; ghi rõ “fixed-topology rolling evaluation”, báo candidate coverage từng kỳ. Không dùng newer graph chứa future edges để cứu coverage.

**Fallback nếu chỉ August xác minh/tải được:** train Jan–Mar, validation April, August fresh test cho một bộ controls đã khóa. Đây là out-of-time confirmation/horizon, **không rolling-origin**. May/June dùng descriptive diagnostics; không lấy August để chọn λ. Nếu August có quá ít observable queries/coverage, công bố bất định và giới hạn, không thay panel bằng nguồn chọn theo August clicks.

Không download lớn hoặc mở holdout mới trong lượt review này. Gate tiếp theo là checksum/schema/acquisition verification và signed-off-by-code immutable protocol; không cần một quy trình xin phép thủ công mới cho thao tác đã được user ủy quyền.

## 6. Baseline bổ sung đáng làm nhất: topology tie-break

Định nghĩa order bằng tuple giảm dần `(published local count, PPR-H score)`; stable hash chỉ phá remaining ties. Giữ positive count order, kể cả khi topology thích target ít clicks hơn; topology chỉ quyết định giữa equal-count candidates, gồm nhóm no-observed-count. Source có zero eligible counts dùng toàn bộ PPR order; so với documented fallback của Markov, không giấu khác biệt cold behavior.

So với ba controls trên cùng candidates:

1. Existing Markov + stable-hash ties.
2. Markov + topology tie-break.
3. Existing probability score fusion.

Câu hỏi: fusion đang thêm useful reranking giữa unequal counts, hay phần lớn hiệu quả chỉ là thay arbitrary tie ordering? Decomposition hiện tại gợi ý câu hỏi này, **không chứng minh** đáp án. Báo changes trong count-tie groups, số positive-count order inversions của fusion, contribution theo observed/unobserved targets và errors bị tạo mới. Không thêm hyperparameters không cần thiết; PPR knobs dùng validation như cũ.

Nếu tie-break rẻ và tương đương/hơn fusion trên fresh test, đó là kết luận có ích dù phương pháp đơn giản. Nếu fusion tốt hơn, cần chỉ ra nó sửa unequal-count order ở đâu. Không claim đây là thuật toán mới.

## 7. Null topology control và adaptive model — làm khi đủ thời gian

**Null control:** hoán đổi directed endpoints `(a→b,c→d)` thành `(a→d,c→b)` với a,c không là query sources; từ chối self-loops/duplicates. Giữ full in/out-degree sequence, query outgoing candidates và node IDs. Chỉ so H-only PPR và fusion với behavioral component cố định; không re-intersect click support hoặc đổi click weights theo rewired H, vì sẽ thêm confounding khác.

Chạy số seeds nhỏ khóa trước (ví dụ5), báo successful swaps/mixing diagnostics và degree/candidate equality. Null graph có thể đổi connectivity, đó là một phần structural perturbation. Không gọi đây là causal experiment trên human navigation, hoặc formal permutation p-value nếu chưa thiết lập null/mixing hợp lệ. Real H hơn degree-matched null sẽ củng cố vai trò cấu trúc cụ thể; không hơn cũng là finding cần báo.

**Adaptive fusion (P2):** λ(u)=N_u/(N_u+τ), với N_u là eligible published training mass, τ chọn validation. Count suppression làm N_u là imperfect confidence proxy; source degree/entropy cũng là hypotheses chứ không guaranteed fixes. So với fixed λ, tie-break và WH smoothing, vì WH đã có dạng trust thay theo row count. Không coi một công thức adaptive đơn giản là novelty đủ mạnh hoặc mặc định sẽ tăng score.

**CycleRank (P2):** [paper gốc](https://pmc.ncbi.nlm.nih.gov/articles/PMC7544349/) nghiên cứu cyclic-path relevance và hub dominance trên directed graph. Nó phù hợp RQ hơn thêm GNN tùy ý. Cần kiểm tra bounded-cycle implementation và cost trên chính graph; không chuyển performance/speed claims từ paper sang dataset này. Giữ đúng scoring semantics, không gọi một two-hop heuristic là CycleRank.

## 8. Làm báo cáo dễ đánh giá cao hơn

- Main text trình bày vài model families đại diện; appendix giữ đủ14configs và28runs. Nói rõ M1/M1B đồng hạng ở selected setting, không dùng nhiều variant để tạo cảm giác breadth giả.
- Mỗi RQ có một câu trả lời và một figure/table: RQ1 frequency vs structure; RQ2 observed/unobserved trade-off; RQ3 stability/cost/boundary.
- Thêm candidate-ceiling decomposition để tách ranking quality khỏi historical coverage. Oracle phải gắn nhãn diagnostic, không baseline triển khai.
- Main result table có paired delta/CI, counts và một practical interpretation; không chỉ bold max score.
- Literature matrix thêm cột “protocol khác gì và ta học gì”, không so scores khác datasets như head-to-head. Bibliography hiện có đã đủ nền; review không thay evidence.
- Demo mở đầu bằng một câu hỏi, cho thấy một win, một failure và một coverage limit. Dùng counts/rank deltas giải thích; không chỉ làm recommender gallery.
- Chuẩn bị slide “Điều chưa chứng minh”: cold-start, causal benefit, user personalization, full-Wikipedia performance. Biết giới hạn là năng lực nghiên cứu, không một lỗi cần che.

## 9. Definition of done cho bản nâng cấp

1. Giữ nguyên original study-v3 và provenance; extensions có output/protocol riêng.
2. Boundary experiment giữ candidates và đủ resource/convergence logs; nếu full H không chạy được thì report đúng scope.
3. Có ít nhất một fresh future evaluation nếu acquisition/schema gate đạt; nếu không, chỉ gọi additions exploratory, không claim confirmation.
4. Tie-break/control hypotheses được khóa trước fresh test; cùng evaluator và candidate contracts.
5. Mọi claim trong Abstract/Conclusion map được tới evidence; lời giải thích không bị viết thành causal fact.
6. Main report vẫn đọc được trong thời gian học phần; detail nằm appendix. Không cần thêm model nếu nó không trả lời câu hỏi mới.

### Self-review và thứ tự thực thi

- **Contribution:** ưu tiên mechanistic analysis + robust comparisons, không inflated algorithm count.
- **Clarity:** cùng definitions và denominator, tách old confirmed protocol khỏi post-hoc hypotheses.
- **Strength:** primary CI chứa0 vẫn được giữ; không power chase sau test.
- **Completeness:** boundary và fresh-period checks quan trọng hơn thêm neural baseline.
- **Soundness:** train-only construction, independent H, same candidates và label-exposure history được audit.

Thứ tự đề xuất: **decomposition (đã có) → freeze extension protocol → boundary resource pilot → tie-break control → fresh temporal evaluation → report/demo refinement**. Chỉ thêm degree-null/CycleRank khi không làm mất thời gian dành cho các bước trên.
