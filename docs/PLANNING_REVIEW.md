# Review bàn giao planning — 21/10/2026

> **Lưu trữ planning:** các trạng thái “chưa chạy”, blockers và effort dưới đây phản ánh thời điểm thiết kế. Implementation và real study hiện đã hoàn tất trong scope đã chốt; xem [trạng thái hiện hành](IMPLEMENTATION_STATUS.md), [frozen protocol](RUN_PROTOCOL.md) và [báo cáo kết quả](../reports/REPORT.md). Không dùng proposal như chứng nhận experiment đã chạy.

## Kết luận và phạm vi

Bộ kế hoạch đáp ứng phạm vi university course project: một task source-conditioned có định nghĩa toán học, independent historical topology, strong behavioral baselines, held-out temporal labels, controlled ablations và analysis có thể bảo vệ. **Không cần hybrid hoặc Node2Vec thắng để dự án có giá trị.**

Đây là review của deliverable planning. Chưa chứng nhận toàn bộ implementation, empirical conclusions, final report, trained demo hay clean reproduction. Code/audit có sẵn được kiểm tra để kế hoạch phản ánh repository thực tế; không xóa hoặc triển khai lại chúng. Không chạy thêm real benchmark trong lượt này.

## Đối chiếu yêu cầu với tài liệu

| Yêu cầu | Bằng chứng trong deliverable | Trạng thái planning / điều còn mở |
|---|---|---|
| 10 phần trả lời theo thứ tự | PROJECT_PLAN phần 1–10 | Đủ; README dẫn vào master plan |
| Task A/B/C, query personalization | PROJECT_PLAN phần 2; EXPERIMENT_DESIGN mục 1 | Chọn A; B/C ngoài scope |
| V, H, C, weights, probabilities, scores | EXPERIMENT_DESIGN mục 1, 3–6 | Công thức và inputs/outputs được định nghĩa |
| Candidate setting và denominator | EXPERIMENT_DESIGN mục 2, 8 | Frozen outgoing H; full + conditional, no-label NA |
| So sánh 3 nguồn dữ liệu | DATASET_FEASIBILITY mục 2–5, 9 | Clickstream/WLG primary; Wikispeedia fallback có đổi task |
| Nguồn, release, sizes, timestamps | DATASET_FEASIBILITY; DATA_AUDIT; evidence/ | Phân biệt listing/paper/raw/canonical counts; không lấy English thay Spanish |
| Temporal independent topology | EXPERIMENT_DESIGN mục 7, 11 | H 01/03/2018; train 01–03, val04, test05; June horizon |
| Resource feasibility | DATASET_FEASIBILITY mục 6; DATA_AUDIT | Có CSR/walk/PPR formulas, sample thật; chưa có peak RSS toàn pipeline |
| Pipeline 14 bước và quality ledger | DATASET_FEASIBILITY mục 7; IMPLEMENTATION_ROADMAP mục 4 | Có schema, normalization, redirects, IDs, graph, splits, manifests |
| EDA có question/plot/decision | EDA_AND_ANALYSIS_PLAN mục 2 | E01–E16; phân biệt sample/full graph |
| M0–M6, rationale và costs | EXPERIMENT_DESIGN mục 3–6 | P0/P1 rõ; không gọi pure PPR-C là hybrid |
| Hai hybrid designs | EXPERIMENT_DESIGN mục 5 | Matrix interpolation và normalized score fusion |
| Node2Vec direction/weights/SGNS | EXPERIMENT_DESIGN mục 6; IMPLEMENTATION_STATUS mục 4 | Gate backend chưa đạt; A5 chỉ áp dụng khi có cả H/W |
| Required metrics và aggregation | EXPERIMENT_DESIGN mục 8 | Recall5/10/20, MRR10, log-gain NDCG10, macro/weighted; massRecall/ExpectedRR riêng |
| Statistical analysis | EXPERIMENT_DESIGN mục 10 | Paired source bootstrap, seeds, temporal limitations; không hứa significance |
| A1–A9 hypotheses và controls | EXPERIMENT_DESIGN mục 9 | Signal/support/weight/sparsity/history/horizon contrasts |
| Tuning/convergence diagnostics | EXPERIMENT_DESIGN mục 4, 6, 10; EDA R04–R15 | Không manufacture loss cho Markov/PPR |
| Systematic error analysis | EDA_AND_ANALYSIS_PLAN mục 4–5 | 6–8 cases, wins/losses hoặc ghi không có; alternatives và evidence |
| Literature 8 named papers | LITERATURE_REVIEW L1–L8 | Titles/metadata có primary links; exact metrics/splits L6 chưa full-text verified |
| Prior work và novelty | LITERATURE_REVIEW mục 3–5 | L2/L3/L4 gần task; không claim novel click+graph combination |
| Architecture/interfaces/tests | IMPLEMENTATION_ROADMAP mục 2–5; IMPLEMENTATION_STATUS | Reuse existing code; mathematical oracles, temporal integrity và no-leakage tests |
| Milestones M1–M8 | IMPLEMENTATION_ROADMAP mục 7 | Goal/tasks/dependencies/outputs/DoD/effort/risks cho mỗi mốc |
| MVP/full/P2 scope | PROJECT_PLAN phần 7; IMPLEMENTATION_ROADMAP mục 8 | Optional work không trên critical path |
| Report 17 sections, presentation/demo | PROJECT_PLAN phần cuối | Nội dung/toán/figures/pitfalls/defense; demo đọc real model artifacts |
| Risk register và feedback matrix | RISKS_AND_DEFENSE mục 1–2 | Severity, likelihood, detection, mitigation, fallback; feedback→component→evidence→question |
| ≥15 defense questions | RISKS_AND_DEFENSE mục 3 | 25 questions/answers và evidence dự kiến, không bịa findings |
| GitHub delivery | README và Git history | Publish documents qua Git CLI; raw/model cache không commit |

## Những quyết định cần giữ nhất quán

1. **Behavior-only là scoring-only:** mọi model vẫn có cùng H-derived candidates. Claim đúng là topology trong propagation/fusion có thêm ích lợi ngoài eligibility hay không; không nói behavior model hoàn toàn không dùng graph ở cả hệ thống.
2. **Candidate ceiling:** perfect order trong C vẫn có thể có full NDCG <1. Pair coverage, mass coverage và full/conditional scores phải đọc cùng nhau; không tự loại unreachable positives.
3. **PPR gần Markov ở damping thấp:** với graph C, phần mass một bước tăng vai trò khi damping nhỏ; kết quả gần local ranking không tự chứng minh multi-hop useful. Bảng tuned và fixed-damping control có vai trò khác nhau.
4. **Fixed-support smoothing:** với một source, cộng uniform prior trên outgoing links không đổi thứ tự raw counts nếu chỉ xét một bước. Gain của weighted PPR phải được phân tích qua propagation/backoff/support, không gán cho một phép cộng constant.
5. **Sample inference:** giữ toàn bộ outgoing candidates của 200 queries không có nghĩa giữ mọi đường đi của PPR. Boundary loss ở intermediate nodes thay stationary scores và walk contexts. Phải ghi rõ induced graph trong title/caption của results.
6. **No observable labels:** một stratum có nhiều sampled queries nhưng ít future observable sources không cho phép ước lượng đáng tin cho cả stratum. Luôn báo U, Q_all, Q_C, N mỗi bin và tỷ lệ no-label.
7. **Cold source khác new article:** T_train=0 trong frozen inventory có thể do suppression; article ngoài inventory không có historical candidate set. Không gộp hai loại vào một accuracy score.
8. **Timing:** event-time split retrospective không mô phỏng data publication latency; graph tái dựng/công bố sau giai đoạn 2018 chỉ hỗ trợ historical study, không historical deployment claim.
9. **Node2Vec optional:** backend không hợp lệ là lý do dừng M5, không là negative empirical result. “Model không cải thiện” chỉ được kết luận sau training/evaluation hợp lệ.
10. **Run incomplete không là benchmark:** cache validation không thay freeze/completion/test artifacts; không chọn lọc score tốt từ run bị dừng.

## Claim–evidence map

| Claim được phép viết hiện tại | Evidence | Claim chưa được phép |
|---|---|---|
| Có kế hoạch đầy đủ và phạm vi rõ | 7 docs và bảng traceability trên | Toàn bộ project implementation đã xong |
| Sample graph đã chuẩn bị từ H độc lập/train | preparation manifest và DATA_AUDIT | Sample representative toàn Wikipedia |
| Dữ liệu Jan–Apr thực tế có count10 | training/validation type summaries | Suppression rule giống mọi tháng/ngôn ngữ |
| Mapping supplied cần sửa theo audit | Revision example + raw history + mapping audit | Resolver mới là ground truth hoàn hảo |
| Core/tiny study tests đạt | 69 tests ngày 21/10; 57 core | Real-data training/CI/cross-platform đã validated |
| Có rationale cho so behavior/topology/hybrid | Formal task/model/ablation matrix | Topology/hybrid cải thiện accuracy |
| Literature đã có related comparisons | L1–L11 primary references | Đây là thuật toán graph recommendation mới |

## Self-review theo 5 chiều

| Chiều | Nhận xét có thể kiểm tra | Điều kiện trước report cuối |
|---|---|---|
| Problem/positioning | Input và target rõ; không users/sessions; scope course project | Abstract/title phải giữ source-conditioned và sample scope |
| Methodology | Same candidates, chronological counts, independent H, strong baselines | Đối chiếu spec/config/code, tie/failure policy và freeze |
| Evidence/experiments | Hypotheses/controls/metrics/uncertainty đã thiết kế | Có real test tables, diagnostics, actual costs; hiện chưa có |
| Writing/interpretation | Vietnamese chủ đạo, English terminology chuẩn; claims có nguồn | Không biến plausible explanation thành causal proof |
| Reproducibility | Small audit manifests/versioned code/toy tests có sẵn | Dependency gate, clean rerun, trained-artifact demo và checksums |

## Bàn giao và thứ tự tiếp theo

Planning không bị chặn bởi việc chưa có benchmark: benchmark thuộc phase sau. Các unresolved items đã có gate, owner theo module, detection và fallback trong roadmap/risk register. Exact metrics của L6 chỉ cần xác minh thêm trước khi sử dụng để so sánh chi tiết; không có số liệu từ L6 được đưa vào hypothesis hoặc acceptance.

Năm bước development tiếp theo nằm ở [IMPLEMENTATION_STATUS mục 5](IMPLEMENTATION_STATUS.md#5-năm-việc-tiếp-theo-khi-chuyển-sang-development). Chỉ chuyển từ planning sang execution thực nghiệm theo scope đã thống nhất; không dùng quota còn lại để mở rộng model list hoặc chạy test trước khi protocol đạt gate.
