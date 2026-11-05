# Kịch bản trình bày theo IT4868E — 12–15 phút

Ngày 05/11/2026. Đây là **outline mới**, chưa phải slide deck đã render hoặc demo UI mới. Dùng [đối chiếu học phần](../docs/COURSE_ALIGNMENT.md) và [trang slide nguồn](../docs/COURSE_SLIDE_INDEX.md). [Kịch bản nghiên cứu cũ](PRESENTATION.md) giữ làm tài liệu sâu; các frozen results không thay đổi.

## Thông điệp xuyên suốt

“Từ trang Web và logs tổng hợp, chúng em xây graph có provenance, so sánh frequency với các phương pháp Link Analysis đã học, rồi kiểm tra khi nào topology có ích. Crawl cho thấy cách trích xuất links làm thay đổi graph; benchmark lịch sử cho thấy graph information chưa tạo gain tổng thể ổn định vượt frequency.”

Không nói “đã crawl graph2026 để dự đoán clicks2018”. Crawl pilot và historical benchmark là hai phần kiểm chứng khác thời điểm; temporal limitation phải xuất hiện ngay khi giới thiệu dữ liệu.

## 12 slide được đề xuất

| Slide | Thời gian | Nội dung / evidence | Liên hệ môn |
|---|---:|---|---|
| 1. Bài toán và câu hỏi | 0:45 | Article nguồn → ranked next articles; 3 RQ data/ranking/conditions | L01 KDD; L08 recommendation |
| 2. Dữ liệu và thời gian | 1:00 | Clickstream counts ≠ sessions; H2018 độc lập; API/HTML2026 là acquisition audit riêng | L02a tr.11; L08 tr.50–51 |
| 3. Tự thu thập API + HTML | 1:15 | Một cached page, URL/revision/hash, HTML parse, anchors/sections; 8-page pilot có thật | L04 tr.28,53 |
| 4. Preprocessing thay graph thế nào? | 1:00 | Cumberland: API33 targets, body13; all-context agreement1.0. Giải thích body filter; không coi agreement là accuracy | L04 tr.28–30 |
| 5. EDA dẫn đến model choices | 1:00 | Click concentration → Markov; degree≠traffic → authority comparator; sparsity → fallback | L03 scatter/distribution; L05 degree |
| 6. Các họ model | 1:30 | Reference uniform/global; Markov; HITS-global; PPR; Node2Vec; normalized fusion | L05a tr.26–44; L05b tr.32–48; L04 tr.55–58 |
| 7. Thiết kế đánh giá | 1:00 | Same candidates, temporal train/val/test, NDCG primary; Recall/MRR, macro/weighted, coverage | L02a tr.11; L04 tr.20–23; L08 tr.19 |
| 8. Kết quả chính và uncertainty | 1:15 | Bảng rút gọn 7 models; Markov0.8991, fusion0.9034; ΔCI chứa0. Bảng đầy đủ trong appendix | Evaluation, không chạy đua model count |
| 9. Ablation và diagnostics | 1:15 | H vs weighted H; validation lambda; PPR residual; Node2Vec SGNS/seed variation | L05 power iteration/SGNS; L02 validation |
| 10. Một win và một failure | 2:00 | Demo actual frozen predictions; Strathclyde và Emperador Alejandro; giải thích counts và fallback | Recommendation + visualization |
| 11. Temporal robustness và giới hạn | 1:00 | Rolling CIs chứa0; sparse/cold sample size; current crawl không có future labels tương thích | L08 drift; L02c unlabeled≠negative |
| 12. Đóng góp và kết luận | 0:45 | Reproducible collection/evaluation, công bằng, kết luận có điều kiện. Bước tới: extraction audit, không thêm neural models | KDD: useful/understandable knowledge |

Tổng khoảng **13 phút 45 giây**. Nếu chỉ có 10 phút: gộp slide3–4, rút slide9 còn một convergence figure, demo một case và giữ failure ở bảng. Không bỏ temporal limitation hoặc uncertainty để dành chỗ cho nhiều thuật toán hơn.

## Demo chứng minh điều gì?

### 1. Dữ liệu đến từ trang Web thật — khoảng 45 giây

Dùng [pilot report](crawl/pilot-v2/PILOT.md), `source_comparison.csv` và raw records local. Chọn Cumberland: chỉ ra khác biệt body/all contexts, cùng revision, anchor/section/occurrence. Không download live; không giả raw captures là current page mới nhất. Hiện chưa có UI tích hợp crawl inspector, nên có thể mở report và structured record song song.

Không dùng page này để khẳng định HTML prominence gây ra navigation2018. Chỉ nói preprocessing quyết định edge universe. Nếu đã hoàn thành manual audit sau lượt review này, thay số pilot bằng số audit thực, có manifest mới; không sửa lịch sử pilot.

### 2. Graph có thể giúp hoặc gây hại — khoảng 75 giây

Mở [rolling demo](extensions/study-v2/demo.html), dùng script và số liệu trong [EXTENSION_CASES](EXTENSION_CASES.md):

- Strathclyde, September: training-unobserved destination Glasgow được topology tie-break đưa lên; count ties và graph có vai trò.
- Emperador Alejandro, August: zero-eligible-count fallback của M1 dùng global popularity; topology methods có thể làm tệ hơn. Đây còn là **fallback-policy difference**, không chỉ hiệu ứng tie-breaking.

Hai case là extreme examples chọn sau test để diễn giải. Average CIs vẫn chứa0. `topology_tie` là appendix mechanism model, không thay hybrid chính chỉ vì có case đẹp. Nếu cần minh họa trực tiếp Markov/PPR/Node2Vec/fusion, dùng [demo gốc](generated/demo.html) và [CASE_STUDIES](CASE_STUDIES.md), không tự chuyển các con số của rolling sang demo gốc.

Browser interaction/visual QA vẫn cần rehearsal thực tế; portable-data checks chưa chứng nhận giao diện. Không mở network download hoặc training trong buổi bảo vệ.

## Appendix giới hạn và thứ tự ưu tiên

1. Bảng đầy đủ14 models, metric definitions, candidate coverage và macro/weighted; công khai bảng chính là subset trình bày.
2. PageRank→PPR equation; HITS-global vs query-root HITS; Node2Vec p/q, directed convention, SGNS noise≠behavioral negatives.
3. Full vs induced graph; boundary không giải thích hết khoảng cách PPR–Markov.
4. Degree-null, extra panels, CycleRank/adaptive/tie-break: trả lời câu hỏi sâu, không thuyết trình toàn bộ nếu không được hỏi.
5. Raw manifests, test/reproduction instructions, extraction-audit ledger khi đã có.

## 10 câu hỏi gắn trực tiếp kiến thức học phần

| Câu hỏi | Trả lời cần có | Evidence |
|---|---|---|
| Vì sao chọn đề tài này cho Web Mining? | Có raw Web acquisition, markup preprocessing, directed link analysis và ranking evaluation trong một workflow | L01 tr.14,39; L04 tr.28,53; source modules |
| Tự crawl mang thêm gì nếu đã có dump? | Anchor/context/occurrences và audit extraction scope; không tạo thêm human click labels | Crawl pilot, field schema |
| Có phải đã làm Information Extraction chương7? | Chỉ structured HTML extraction; chưa NER, semantic relation extraction/coreference | L07 tr.5–8,13–27 vs parser outputs |
| Sao PPR khác PageRank đã học? | Restart distribution `e_u` thay uniform; phù hợp source-conditioned context | L05a tr.26,29; solver |
| HITS của em có bước root/base set không? | Không; đây là fixed-graph authority comparator, gọi HITS-global | L05a tr.40–42; `hits_scores` |
| Tại sao Node2Vec cần thiết? | Có trong L05b; kiểm tra representation của neighborhoods so với explicit graph ranking, không giả sẽ thắng | L05b tr.32–48; seed/matched-weight results |
| Vì sao không chạy session RNN/CF? | Không có session order/user-item matrix; source article không phải user | L08 tr.16,24,50–51; dataset schema |
| Tại sao không MAE/RMSE? | Dự đoán ranking chứ không explicit rating; Recall có ngay trong L04/L08; MRR/NDCG bổ sung rank/gain sensitivity | L04 tr.20–23; L08 tr.19; metric tests |
| Missing clicks có thể thành negatives không? | Không; thresholded positives không thỏa mặc định random selection của PU | L02c tr.47,66; suppression discussion |
| Hybrid không thắng thì đóng góp ở đâu? | Collection/provenance, controlled comparisons, ablation, diagnostics và lý giải giới hạn có evidence | Frozen tables/CIs và error analysis; không tự nhận novelty thuật toán |

## Tự kiểm tra trước nộp

- Không nhận corpus100–200pages, manual audit, Global PageRank hoặc TF-IDF đã chạy nếu chưa có artifacts.
- Không đưa current crawl features vào historical ranking table.
- Caption phân biệt nguồn kiến thức slide, kết quả measured và planned experiment.
- Mọi major figure trả lời một RQ; giải thích được gain và failure.
- Dùng nguồn/manifest hiện hành cho số tests, không sao chép số cũ86 từ outline nghiên cứu trước crawler; audit ngày29/10 ghi104 tests, không phải lượt này rerun104 tests.
- Không có grading rubric riêng trong bộ ZIP; độ dài/bố cục trên là đề xuất, không nhận là yêu cầu chính thức của giảng viên.
