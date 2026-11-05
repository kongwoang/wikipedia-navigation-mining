# Định hướng đồ án theo học phần Web Mining — IT4868E

Ngày đối chiếu: **05/11/2026**. Nguồn chính: bộ 14 PDF, **733 trang**, người dùng cung cấp. [Danh mục và trang tham chiếu](COURSE_SLIDE_INDEX.md); [manifest nguồn](evidence/course-slides-manifest.json). Đây là đề xuất thu gọn và gắn kiến thức vào project đã có, không phải một benchmark mới đã chạy hoặc rubric chấm điểm của giảng viên.

## 1. Quyết định trọng tâm

**Lấy Link Analysis làm lõi; dùng crawl/HTML preprocessing để tạo và kiểm tra dữ liệu; dùng ranking evaluation, recommendation và visualization để trả lời một câu hỏi xuyên suốt.**

> Khi đang đọc một bài Wikipedia, lịch sử chuyển trang và cấu trúc hyperlink giúp xếp hạng bài tiếp theo như thế nào; lựa chọn cách trích xuất hyperlink ảnh hưởng ra sao đến dữ liệu mà các phương pháp graph sử dụng?

Tên dùng cho bản trình bày học phần: **Mining Wikipedia Navigation: Web Data Collection, Link Analysis, and Next-Article Ranking**. Tên tiếng Việt: **Khai phá điều hướng Wikipedia: Thu thập dữ liệu Web, phân tích liên kết và xếp hạng bài viết tiếp theo**. Tên nhấn mạnh các phần thực sự đã có; chưa tuyên bố crawled content cải thiện ranking.

Giữ nguyên task: input là article nguồn `u`, output là danh sách bài `v` trong outgoing candidate set đã chốt. `u` không phải user; nhãn là monthly aggregate transitions. Cạnh đã tồn tại trong candidate graph, nên nhiệm vụ là xếp hạng khả năng được truy cập, không phải dự đoán sự tồn tại của cạnh.

Ba câu hỏi đủ cho báo cáo chính:

1. **RQ1 — Dữ liệu Web:** API links và HTML body links khác nhau ở đâu; preprocessing giữ/bỏ những gì, chất lượng extraction được kiểm tra thế nào?
2. **RQ2 — Ranking:** Local frequency, graph authority/proximity và graph embeddings khác nhau thế nào khi cùng xếp hạng next articles?
3. **RQ3 — Kết hợp và điều kiện:** Thêm topology vào frequency có lợi ở nguồn/transition nào, có ổn định theo thời gian và đáng chi phí không?

Không mở thêm một đề tài sentiment, NER, community detection hoặc session recommendation. Áp dụng nhiều kiến thức bằng **một chuỗi quyết định có bằng chứng**, không bằng số chương hoặc số mô hình.

## 2. Ma trận kiến thức → hành động → bằng chứng

Ký hiệu L04/L05a/... được định nghĩa trong [slide index](COURSE_SLIDE_INDEX.md). Số trang là **trang PDF, bắt đầu từ 1**, gồm hai trang bìa.

| Kiến thức và trang | Áp dụng cụ thể | Thành phần / bằng chứng hiện có | Quyết định |
|---|---|---|---|
| L01 tr.13–14: KDD, preprocessing, post-processing | Từ raw captures/counts đến graph, ranking, đánh giá và diễn giải | `sources.py`, `study_data.py`, `analysis.py`, manifests | Khung mở bài; giải thích mỗi bước giải quyết lỗi gì |
| L01 tr.39; L04 tr.53: crawl, parse, index, retrieve | API collection + direct HTML crawling, cache, resume, provenance | `crawl.py`, `crawl_export.py`, pilot thật 8 trang | Giữ ở phần chính; graph adjacency là cấu trúc tra cứu links, chưa phải textual inverted index |
| L04 tr.24–30: fields, anchor text, main content, duplicates | Parse article body; tách infobox/reference; lưu anchor, section, occurrence, hash | 654 API edges, 556 body edges; raw parsing replay | Điểm kết nối mạnh nhất của phần crawl; cần manual extraction audit |
| L05a tr.6–8,24–33: directed adjacency, degree prestige, PageRank | Hai graph H/C, row normalization, dangling handling, power iteration, PPR | `graph.py`, `sparse_models.py`, convergence curves | Lõi lý thuyết; giải thích PPR là mở rộng PageRank theo nguồn |
| L05a tr.37–44: authority/hub, HITS | Authority comparator trên graph cố định | `hits_scores`, bảng HITS đã chạy | Giữ, gọi rõ **HITS-global**; không nhận đã triển khai query-root retrieval như slide |
| L05b tr.32–48: graph representation, Node2Vec, random walks, SGNS | Directed walks, p/q, embeddings và cosine ranking | `embeddings.py`, seed/weight controls, SGNS diagnostics | Giữ một đại diện ở bảng chính vì được dạy trực tiếp; weighted variant trong ablation |
| L04 tr.55–58: combine scores/ranks | Chuẩn hóa score trên cùng candidates rồi kết hợp behavior và PPR | `fusion`, `M6B_fusion`, sensitivity trên validation | Giữ một hybrid; không thêm mọi CombMIN/MAX/Borda chỉ để đủ slide |
| L08 tr.6,10,15,19: recommendation, sparsity, drift, ranking | Current article là context, next article là item; phân tích sparse sources và temporal drift | Source-conditioned task, rolling results, coverage | Liên hệ trực tiếp, nhưng không phải user-based CF |
| L02a tr.10–11,27: train/test, validation, overfit | Train quá khứ, validation chọn knobs, freeze trước test, kiểm tra drift | `RUN_PROTOCOL`, `EXTENSION_PROTOCOL`, freeze artifacts | Đã phù hợp slide; không cần random k-fold cho monthly aggregates |
| L02c tr.23–26,47,66–67: distances, normalization, PU | Jaccard cho extraction agreement; không đồng nhất unobserved với negative | Crawl comparison; label/censoring protocol | Dùng để biện luận giới hạn; không tự nhận đã xây PU learner |
| L03 tr.13–27,31–34: quantiles, boxplot, histogram, scatter | Traffic tail, degree vs traffic, per-source delta, nguồn sparse/dense | Figures hiện có, macro/weighted metrics | Mỗi hình phải dẫn đến quyết định hoặc giải thích lỗi |
| L04 tr.7,11–12,31–37: document query, TF-IDF, cosine, index | Một content baseline chỉ khi có text/candidates đúng thời gian | Hiện mới có text extraction; chưa có content ranking benchmark | P2 có điều kiện; không nằm trên critical path |
| L07 tr.5–8,13–27: IE, NER và relation extraction | Chỉ liên hệ ý tưởng schema và structured records | Parser lấy hyperlinks được khai báo trong HTML | Không gọi parser là NER, semantic relation extraction hoặc coreference |
| L09 tr.21–24,28–35: implicit feedback, query logs, bigram | Liên hệ local Markov với conditional frequency; hiểu giới hạn logs | Clickstream aggregate, không query sessions/impressions | Một đoạn discussion; không thêm ad CTR prediction |
| L02b; L06a/b/c: neural architectures, opinion mining | Có thể giải thích SGNS ở mức cần thiết, nhưng không có opinion task | Không có sentiment labels/users/sessions | Không xây CNN/RNN/sentiment model cho đủ chương |

## 3. Hai phần thực nghiệm liên quan nhưng không trộn thời gian

### A. Benchmark điều hướng lịch sử — đã có kết quả

Clickstream eswiki 2018, graph độc lập ngày 01/03/2018, shared candidates, temporal splits. Kết luận và dữ liệu giữ nguyên trong [báo cáo chính](../reports/REPORT.md), [bảng đầy đủ](../reports/RESULT_TABLES.md) và [rolling extension](../reports/EXTENSION_RESULTS.md).

Đây là evidence cho RQ2–RQ3. Mọi kết quả mới trên May–September đã xem phải được gọi là **exploratory/post-hoc**; không sửa protocol cũ để nhận là pre-specified. Có thể chỉnh cách trình bày vì bám môn học, nhưng phải công khai việc chọn một bảng rút gọn và giữ bảng đầy đủ để tránh che kết quả bất lợi.

### B. Data acquisition và extraction audit — pilot đã có, corpus lớn chưa có

API + HTML crawl tháng 10/2026 là evidence cho RQ1. Pilot có 8/8 cặp cùng revision; 6 historical revisions có trước cutoff. **Current HTML 2026 không được dùng để giải thích bằng số liệu định lượng hoặc dự đoán clicks2018.** Hai phần cùng cho thấy từ web page đến graph đến ranking, nhưng chưa tạo thành một thí nghiệm end-to-end trên cùng snapshot.

Giá trị của phần B phải được chứng minh bằng extraction quality, coverage, graph-definition sensitivity và provenance. Không lấy Jaccard API/HTML làm recommendation accuracy. Không dùng similarity với API làm gold accuracy vì API và body-only có phạm vi links khác nhau.

Nếu muốn nối crawl vào ranking trong một study chung, chỉ chọn **một** đường:

- Historical API wikitext trước cutoff + historical page-ID/redirect audit; parse direct links/text, không giả historical rendered DOM. Benchmark mới trên holdout cũ chỉ exploratory; confirmation cần protocol mới và labels chưa đọc.
- Current crawl được khóa trước tháng labels tương lai. Chờ release thật và xác minh coverage; không hứa có kết quả ngay trong lịch nộp.

**Khuyến nghị cho học phần:** hoàn thiện extraction audit rồi trình bày A+B minh bạch. Không để dependency chờ future labels làm chậm bản nộp. Chỉ nối hai phần nếu temporal gate thực sự đạt; nếu giảng viên yêu cầu toàn bộ ranking phải dùng data tự crawl thì đây là yêu cầu cần xác nhận riêng, không có rubric đó trong ZIP.

## 4. Bảng model gọn, mỗi model một vai trò

| Vai trò | Model / ID hiện có | Câu hỏi trả lời | Trạng thái và vị trí |
|---|---|---|---|
| Reference không có frequency | Uniform (`M2_uniform`) | Candidate availability và tie policy đã đem lại bao nhiêu? | Đã chạy; reference row |
| Reference behavior toàn cục | Global Popularity (`M0_global`) | Chỉ đẩy bài phổ biến có đủ không? | Đã chạy; reference row |
| Behavior theo nguồn | Local Markov (`M1_local`; backoff `M1B_backoff`) | Đếm transition có đủ mạnh không? | Đã chạy; dòng chính, giải thích fallback |
| Link authority | HITS-global (`HITS`) | Authority toàn cục có phù hợp next step không? | Đã chạy; dòng chính |
| Source proximity | PPR-H (`M3_ppr_h`) | Multi-step proximity bổ sung gì? | Đã chạy; dòng chính |
| Graph representation | Node2Vec-H (`M5H_node2vec`) | Neighborhood embedding có giữ thông tin hữu ích cho ranking không? | Đã chạy; dòng chính, seed range ở appendix |
| Hybrid | Calibrated fusion (`M6B_fusion`) | Ghép behavior và topology có cải thiện không? | Đã chạy; dòng chính, so với behavior parent |
| Control bổ sung nhỏ | Global PageRank-H, restart uniform | Khác biệt authority vs source-specific restart ở cùng graph là gì? | **Chưa có benchmark riêng**; P1, tối đa một dòng thêm |

Như vậy bản chính có **7 dòng đã có**, tối đa 8 nếu bổ sung PageRank. Không gọi 28 configurations là 28 algorithms. Local/backoff nếu cùng ranking có thể gộp hiển thị nhưng giữ kết quả và tên đầy đủ trong appendix; fusion dùng backoff nên paired comparison chính phải ghi đúng parent.

Node2Vec weighted/unweighted, PPR click/H/weighted-H là **matched ablations**, không cần thêm một đoạn motivation dài cho mỗi biến thể. In-degree, CycleRank, matrix fusion, adaptive/tie-break, panel controls và degree-null vẫn giữ ở repository/appendix; chỉ đem ra khi trả lời một câu hỏi cụ thể.

Global PageRank nếu làm: cùng H/candidates, `r = d P^T r + (1-d)q`, `q` uniform; dangling mass trả về `q`. PPR dùng `q=e_u`. Cố định cùng `d` trong paired control để tách restart; một comparison separately tuned nếu cần phải gắn nhãn khác. Không sửa frozen PPR solver để tạo lại kết quả cũ. Test trên graph nhỏ, residual/mass conservation, và đánh giá bổ sung chỉ exploratory trên holdout đã xem. Không cần thêm query-root HITS hoặc cả TF-IDF/BM25/LSI để lấp đầy bảng.

## 5. Năm nhóm experiment đủ mạnh

| Experiment | Giả thuyết / biến thay đổi | Giữ cố định | Evidence / trạng thái |
|---|---|---|---|
| E1 — Extraction scope | API/all-context/body-only khác vì context/filter/mapping | Cùng page ID/revision; đánh dấu mismatch, không silently drop | Pilot agreement đã có; manual audit và corpus cân bằng chưa có |
| E2 — Behavior vs graph | Local frequency, authority, proximity, embedding có thể tối ưu khác nhau | Sources, H timestamp, candidates, held-out labels, metric denominator | Dùng 7 models đã chạy; Recall@5/10/20, MRR@10, NDCG@10, macro/weighted |
| E3 — Signal ablation | Weighting/fusion thay đổi score do signal nào? | Graph support, damping hoặc embedding knobs/seed khi so weights | H vs weighted H; M1B vs PPR-H vs fusion, lambda validation-only; dùng matched ablations có sẵn |
| E4 — Điều kiện và độ bền | Gain/loss phụ thuộc sparsity, degree, history và tháng | Bins xác định từ train; same-source paired deltas; report coverage | Sparse/unobserved transitions, temporal results và paired CIs đã có; cold thiếu labels phải nói rõ |
| E5 — Chẩn đoán và chi phí | Solver/embedding chạy đúng, cấu hình hợp lý, không đổi accuracy lấy chi phí vô ích | Fixed hardware/run provenance; seeds, validation budget | PPR residual, Node2Vec SGNS/seed stability, cost/accuracy đã có |

E1 không có compatible future labels thì chỉ báo extraction/structure metrics, không đặt NDCG cạnh Jaccard như cùng một chất lượng. Body-vs-all ranking nếu làm cần cùng candidate union và explicit missing-edge handling; không cho mỗi phương pháp tự chọn candidates dễ hơn.

Giữ NDCG@10 làm primary metric đã khóa; **không đổi metric sau khi xem test**. Recall nối trực tiếp L04/L08; MRR và graded NDCG mở rộng để phản ánh thứ hạng và cường độ observed transitions. MAE/RMSE trong L08 thuộc rating prediction, không bắt buộc cho task này. Precision@K có thể bổ sung từ frozen rankings nếu cần giảng giải, nhưng phải gọi observable-label precision, định nghĩa denominator khi ít hơn K candidates; không gọi mọi unobserved item là true irrelevant.

## 6. Làm phần crawl có chiều sâu mà không phình phạm vi

Ưu tiên **20 source pages được audit**, rồi mới xét 100–200 sources. Các số này là mục tiêu mới, không phải số đã thu thập. Pilot 8 trang thiên về wrestling do BFS; không dùng nó để tuyên bố đại diện Wikipedia.

Protocol trước khi thu thêm:

1. Chọn seeds bằng train-only traffic/out-degree strata; khóa seed list, sampling rule và budget. Dùng round-robin hoặc quota giữa seeds thay vì để hub đầu chiếm frontier. Ghi đây vẫn là sample có chủ đích, không uniform sample của Wikipedia.
2. Với mỗi page, ghi URL, page ID/revision, time, raw hash, API continuation, redirects, status. Tách title normalization khỏi text tokenization; không lowercase article IDs tùy tiện.
3. Người kiểm tra đọc **raw HTML đã lưu**, gán nhãn toàn bộ eligible article-link occurrences của 20 source pages theo guideline: main body, infobox/navbox, references, redlinks, self/duplicate, fragment, namespace. Không dùng browser current page khác revision làm gold. Giữ failures/mismatches trong ledger.
4. Trên occurrences/edges đã gán nhãn, tính extraction precision/recall/F1 theo từng context và macro theo page; báo số page/links thật. Kiểm tra anchor/section/position agreement riêng. Audit một người phải công khai; nếu có hai người, double-label một phần và adjudicate.
5. Phân loại API-vs-HTML discrepancy: context scope, canonicalization, redlink/namespace, parser error, revision mismatch. API không mặc định là ground truth.
6. Export node/edge/features với `crawled`, `outgoing_unknown`, unresolved-ID flags. Graph boundary chưa crawl không phải dangling page thật. Không báo 575 exported nodes như 575 pages đã tải.

Đầu ra hữu ích: một bảng extraction audit, một coverage funnel, một hình paired API/body degree, và hai page examples. Điểm học thuật nằm ở **ảnh hưởng của preprocessing đến graph**, không ở việc crawl nhiều MB.

## 7. Những điều phải giải thích chuẩn khi bảo vệ

- **PageRank vs PPR:** L05a tr.26 chỉ rõ PageRank không phụ thuộc query. Việc đổi restart thành `e_u` là lý do dùng PPR cho current article. `d` là follow-link probability, `1-d` là restart; global popularity từ clicks không phải PageRank.
- **HITS:** slide có query → root set → expanded base set (tr.40–42); code hiện tại chạy authority trên fixed induced H. Báo đúng HITS-global; kết quả đó không chứng minh mọi query-dependent HITS đều kém.
- **Node2Vec:** p điều khiển return, q điều khiển outward/inward bias. Cần trình bày trọng số `1/p, 1, 1/q` rồi chuẩn hóa; không học thuộc “p nhỏ = BFS” như một định luật đầy đủ. Với p cố định, q lớn hạn chế đi xa; q nhỏ khuyến khích đi xa. Graph có hướng phải ghi convention; code dùng `next→previous` cho near test. [Bài gốc, mục 3.2](https://arxiv.org/html/1607.00653v1#S3.SS2).
- **Walks không phải sessions:** sequence trong Node2Vec là algorithm-generated walk, không hành trình thực của người đọc. Cosine hai node là score đối xứng; directed walks không tự biến cosine thành xác suất chuyển có hướng. Đây là hạn chế cần phân tích.
- **Negative sampling:** SGNS dùng noise samples để tối ưu embedding; điều này không chứng nhận training-unobserved next-click pairs là negative labels của benchmark.
- **PU:** L02c tr.66 có giả định positives được gắn nhãn ngẫu nhiên. Clickstream bị threshold theo count nên không được mặc nhiên áp dụng SCAR/correction của PU. Dùng insight “unlabeled ≠ negative”, không tuyên bố đáp ứng toàn bộ PU assumptions.
- **Jaccard:** L02c tr.24 diễn đạt dưới dạng distance; crawl report dùng set similarity `intersection/union`. Định nghĩa rõ, không lẫn `1-J` với `J`.
- **IE:** anchor/target đã khai báo trong markup; extracting edge không suy ra semantic predicate. L07 tập trung NER, relation extraction, coreference; project không nhận đã triển khai các bài toán này.
- **Index và graph:** CSR adjacency hỗ trợ truy cập neighbors, không đồng nghĩa inverted term index của L04. Nếu chưa có content retrieval thì không nhận đã xây search engine đầy đủ.
- **Temporal evaluation:** L02a tr.11 đã nêu dùng quá khứ để train khi dữ liệu theo thời gian. Đây là áp dụng trực tiếp slide, không cần ép random k-fold.
- **Adjacency/self-loops:** slide tr.7 có convention riêng; project dùng binary directed H và count-weighted C, self-loop policy công khai. Không sao chép hệ số 2 trên diagonal nếu không đúng định nghĩa graph đang dùng.
- **CTR/causality:** click counts không có denominator impressions/exposure, nên không tính CTR hay kết luận causal improvement. L08 A/B testing chỉ là future work; offline ranking chưa là online experiment.

## 8. Chỉ chọn hình phục vụ câu chuyện

| Hình / bảng | Điều người xem cần hiểu | Nguồn |
|---|---|---|
| Acquisition ledger + API/body paired counts | Mỗi graph edge đến từ đâu; lọc main content thay graph ra sao | Pilot hiện có; audit mới còn thiếu |
| Traffic concentration + degree/traffic scatter | Vì sao cần Markov mạnh và vì sao authority chưa chắc là navigation | `10_concentration_and_drift`, `03_topology_traffic` |
| Bảng 7 models + CI của hybrid−behavior | Kết quả tổng thể, uncertainty và sự công bằng | `RESULT_TABLES`, paired comparisons; bảng đầy đủ giữ appendix |
| Sparse/dense subgroup + một win/một failure | Topology hữu ích hoặc gây hại trong điều kiện nào | `08_source_sparsity`, `CASE_STUDIES`, `EXTENSION_CASES` |
| PPR residual + Node2Vec diagnostics | Thuật toán hội tụ/được tối ưu đúng mức nào | `06_numerical_diagnostics`, seed table |
| Temporal delta + cost | Kết luận có ổn định và khả thi không | Rolling CI figure; `09_cost_accuracy` |

Không cần graph visualization hàng nghìn nodes không đọc được, SOM, t-SNE hoặc community detection nếu không trả lời RQ. Full-graph boundary, degree-null và extra panels là evidence mạnh nhưng đặt appendix; khi cần chỉ một câu tóm tắt và dẫn nguồn.

## 9. Lộ trình điều chỉnh có giới hạn

Ước lượng dưới đây là effort đề xuất, không measured runtime; ưu tiên chất lượng evidence trước thêm model.

| Ưu tiên | Việc | Effort | Definition of done |
|---|---|---:|---|
| P0 — lượt review này | Giải nén, index slide, mapping, scope và outline học phần | Hoàn tất tài liệu trong lượt này | Có source/page references và phân biệt đã có/chưa có |
| P0 — tiếp theo | Audit extraction 20 pages, guideline và discrepancy taxonomy | 6–10 giờ | Raw-linked annotations, precision/recall và failure ledger; không lấy API làm gold |
| P0 — tiếp theo | Biên tập bản nộp/slide theo 3 RQ, bảng chính 7 models | 4–6 giờ | Kết quả không đổi; đầy đủ evidence, một win/một loss, giới hạn thời gian rõ |
| P1 | Một control Global PageRank vs PPR | 2–4 giờ | Toy oracle, same-d control, separate exploratory results; không sửa frozen bundle |
| P1 | Scale 100–200 audited-protocol sources khi cần | 4–8 giờ, chưa gồm chờ mạng | Sampling/redirect/coverage gates; không cần nếu audit nhỏ đã đủ chứng minh pipeline |
| P1 | Rehearsal demo và trả lời câu hỏi gắn slide | 2–3 giờ | 12–15 phút, mở đúng artifacts; browser interaction QA được thực hiện thực tế |
| P2 | Một TF-IDF cosine baseline trên historical text | Chỉ lập kế hoạch sau temporal/mapping gate | Cùng candidates, vocabulary/IDF theo corpus hợp lệ, missing-text coverage; không thêm đồng thời BM25/LSI/NN |

Nếu làm TF-IDF: `q` là document của article nguồn (L04 tr.7), `v` là candidate document; score cosine trên vector TF-IDF. Dùng Spanish preprocessing cho eswiki; text normalization không được đổi stable page IDs. Crawl cả candidate documents hoặc báo coverage/fallback, không chỉ crawl source rồi tuyên bố có content score cho mọi target. Có thể dùng sparse matrix; inverted index chỉ thêm khi cần truy vấn toàn corpus, không xây search service riêng để lấy điểm chương IR.

**Điểm dừng:** source/candidate/temporal audit rõ; crawler có evidence thật; 7-model comparison được giải thích; matched ablations + diagnostics + uncertainty; demo đáng tin cậy. Chưa cần GNN, additional datasets/languages, RNN, PU learner, classifier/LTR, CF, community algorithms hay distributed infrastructure.

## 10. Checklist học phần và mức độ hoàn thành

- [x] Có nguồn slide thật và map tới implementation, không suy đoán syllabus từ tên môn.
- [x] Task và giới hạn user/session được định nghĩa đúng.
- [x] PageRank-family, HITS và Node2Vec có implementation/results; phân biệt PPR với global PR chưa benchmark.
- [x] API và HTML crawler có real pilot, raw hashes/replay; chưa nhận đã có corpus lớn.
- [x] Ranking metrics, validation, convergence/seed diagnostics, ablation và temporal analysis đã có.
- [x] Có lý do không dùng sentiment/NER/CF/RNN dù xuất hiện trong slide.
- [ ] Manual extraction audit 20 pages và corpus cân bằng hơn.
- [ ] Bản report/deck học phần cuối cùng được biên tập theo outline mới; lượt này chỉ tạo định hướng và kịch bản.
- [ ] Visual/interaction rehearsal của demo; không lấy data checks thay browser QA.
- [ ] Global PR control nếu còn thời gian; không phải blocker để có đồ án đúng.

Đây là đồ án **thực nghiệm Web Mining có tự thu thập dữ liệu và kiểm chứng**, với literature review hỗ trợ. Giá trị bảo vệ là chỉ ra vì sao một tín hiệu/mô hình hữu ích hoặc không hữu ích trong một task cụ thể; không phải hứa rằng phương pháp phức tạp nhất sẽ thắng.
