# Phạm vi thống nhất — Wikipedia Navigation Mining

**Quyết định hiện hành, 05/11/2026.** Tài liệu này là nguồn quyết định scope duy nhất, thay các roadmap mở rộng trước đây. [Planning cũ](PROJECT_PLAN_LEGACY.md) chỉ để truy nguyên. [Báo cáo chính](../reports/REPORT.md) và [kịch bản bảo vệ](../reports/PRESENTATION.md) diễn giải cùng một câu chuyện.

## 1. Một câu hỏi, một thông điệp

**Tên:** *Wikipedia Navigation Mining: When Do Hyperlinks Help Beyond Click History?*
**Tiếng Việt:** *Khai phá điều hướng Wikipedia: Khi nào cấu trúc liên kết bổ sung cho lịch sử truy cập?*

**Câu hỏi trung tâm:** Với bài đang đọc, cấu trúc hyperlink bổ sung gì ngoài tần suất chuyển trang đã quan sát khi xếp hạng bài tiếp theo?

**Insight có bằng chứng:** Hyperlink mô tả các đường đi có thể có; lịch sử clicks phản ánh những đường đi đã được sử dụng. Trong sample lịch sử này, local frequency là tín hiệu mạnh. Topology tìm được một số destinations chưa có published training count, nhưng kết hợp topology chưa cho gain tổng thể đáng tin cậy so với baseline behavior.

Đây là kết luận có điều kiện từ dữ liệu hiện có, không mục tiêu phải ép thí nghiệm đạt được. Nếu evidence mới thay đổi kết luận, sửa kết luận; không chọn model/subset để bảo vệ câu chuyện đã định.

Hai RQ chính:

- **RQ1:** Frequency, topology và kết hợp hai tín hiệu khác nhau thế nào trên cùng task/candidates/future labels?
- **RQ2:** Chênh lệch đó xuất hiện ở nguồn/transition nào, có ổn định và có đáng chi phí không?

Crawl là phần xây dựng và kiểm tra dữ liệu phục vụ lập luận: một hyperlink trong graph được lấy từ đâu và bị ảnh hưởng thế nào bởi preprocessing? Không tách thành đề tài thứ hai về content recommendation.

## 2. Task và giới hạn

Input: current article `u`. Output: Top-K destinations trong `C(u)`, outgoing editorial hyperlinks của graph lịch sử đã khóa. Scorer dùng training clicks và/hoặc independent H; nhãn là published next-month transitions. Graph có hướng; H weights là presence, C weights là aggregate counts.

Không có user IDs, sessions, impression counts. Không nhận user personalization, session prediction, exact next-click probabilities hoặc causal CTR uplift. Unobserved transitions không được coi là reliable negatives. PPR là source-seeded ranking, không user profile.

**Giữ eswiki 2018 và benchmark đã kiểm chứng.** Không đổi language/dataset để mở lại cuộc thi accuracy. Không dùng current crawl 2026 làm features cho labels 2018. Các tháng đã đọc không trở lại thành fresh holdout khi đổi cách viết báo cáo.

## 3. Quyết định giữ, chuyển và bỏ

| Thành phần | Quyết định cuối | Lý do |
|---|---|---|
| API + HTML crawling | **Giữ**; hoàn thiện extraction audit nhỏ | Tự thu thập dữ liệu, provenance, main-body/anchor extraction bám L04 |
| Historical Clickstream + independent H | **Giữ** làm benchmark chính | Có temporal protocol, labels và results tái kiểm tra được |
| Local Markov, PPR-H, HITS-global, Node2Vec-H, score fusion | **5 phương pháp ở phần chính** | Behavior, proximity, authority, representation và fusion; mỗi phương pháp một vai trò |
| Uniform và Global Popularity | **2 reference rows** | Cho biết mức baseline/candidate support; không cần 2 mục thuật toán dài |
| Weighted PPR / weighted Node2Vec | **Giữ trong ablation** | Tách click weights khỏi structure; không quảng bá thêm một họ thuật toán |
| Full-graph boundary và temporal results | **Giữ làm robustness evidence**, diễn giải ngắn | Kiểm tra lời giải thích PPR kém do graph bị cắt và tính ổn định |
| CycleRank, adaptive/tie-break, degree-null, extra panels, matrix fusion | **Phụ lục kỹ thuật; dừng phát triển thêm** | Đã có evidence; không cần để hiểu câu trả lời chính |
| Global PageRank mới, query-root HITS mới | **Bỏ khỏi backlog bản nộp** | Giải thích PageRank→PPR bằng lý thuyết hiện có; không cần thêm model để đủ slide |
| TF-IDF/BM25/LSI/content fusion, first-link/repetition rankers | **Bỏ khỏi scope hiện hành** | Chưa có compatible corpus/labels; mở thêm trục đánh giá làm loãng câu hỏi |
| Corpus 500–2.000 pages hoặc crawl toàn Wikipedia | **Bỏ mục tiêu số lượng** | Audit 20 pages quan trọng hơn volume; chỉ scale nếu audit phát hiện nhu cầu cụ thể |
| Community detection, sentiment, NER, CF, RNN, GNN/LLM | **Không thực hiện** | Không trả lời task hoặc thiếu đúng loại dữ liệu |
| New datasets, languages, new holdouts | **Không đặt trên đường hoàn thiện bản nộp** | Kết quả hiện có đủ cho comparative study có giới hạn; chưa cần mở nghiên cứu khác |

“Bỏ” là bỏ khỏi mục tiêu, backlog và câu chuyện chính. Code/results đã công bố và các script tái lập vẫn được giữ để audit; không xóa kết quả bất lợi hoặc làm hỏng frozen manifests. Việc chọn bảng chính là **biên tập sau thực nghiệm theo vai trò/môn học**, không protocol model selection mới; bảng 14 models đầy đủ vẫn truy cập được.

## 4. Mạch nội dung cố định

1. **Vấn đề:** một bài có nhiều links nhưng người đọc không chọn chúng như nhau.
2. **Dữ liệu:** crawl/parse cho thấy cách xây link graph; Clickstream cung cấp observed behavior. Giải thích rõ hai mốc thời gian.
3. **So sánh:** frequency vs topology vs fusion trên cùng candidates và temporal labels.
4. **Giải thích:** aggregate scores, unobserved-pair analysis, một win và một failure; phân biệt structural relevance với observed navigation.
5. **Kết luận:** topology có thông tin nhưng chưa chứng minh incremental benefit ổn định vượt behavior; giới hạn và chi phí rõ ràng.

Không dẫn dắt bằng danh sách 14 models, số triệu edges hoặc số tests. Các số này là evidence kỹ thuật hỗ trợ, không đóng góp trung tâm.

## 5. Bốn nhóm evidence cần có

| Nhóm | Evidence giữ ở bản chính | Trạng thái |
|---|---|---|
| Data quality | API/HTML same-revision comparison, một ví dụ body/all-context, agent extraction audit | Audit20pages/120occurrences đã có bằng agent; chưa có human gold |
| Main comparison | Bảng 7 rows; Recall@5/10/20, MRR@10, NDCG@10; fusion−behavior CI | Đã có frozen results; primary metric/protocol không đổi |
| Signal/condition analysis | Matched H vs weighted-H; validation lambda; train-observed/unobserved; macro/weighted; một win/một loss | Đã có; không gọi unobserved là cold-start, không suy causal effect |
| Robustness/diagnostics | May/June, rolling summary đúng comparator; full-H control; PPR residual, Node2Vec seeds/SGNS, cost | Đã có; detailed controls trong appendix |

Không cần thêm algorithm để hoàn thành bốn nhóm này. Bootstrap qua sources và temporal reuse có limitations; không nhân sample size theo clicks/configurations. Cases chỉ diễn giải, không thay average evidence.

## 6. Phần crawl: có vai trò rõ, không thêm claim chưa được kiểm định

API collector và HTML parser đã chạy thật 8 pages, kiểm tra 8/8 revision matches, 654 API edges/556 body edges / 1.028 occurrences. Đây là acquisition/extraction pilot. Crawl 2026 chưa làm input cho benchmark 2018; không ghép hai kết quả thành pipeline end-to-end cùng thời điểm.

Audit20source pages hoàn thành với seed rule khóa trước,20matched revisions,1.397API/1.049body edges sau correction. Agent đọc120fixed occurrences, phát hiện page indicator và authority icon bị nhận nhầm; raw archive giữ nguyên, explicit offline reparse lưu parser hash. [Audit](../reports/crawl/audit-v2/AUDIT.md) ghi annotations, trước/sau và limitations. API không là gold; unknown frontier không là true dangling.

Không có human adjudication hoặc held-out extraction accuracy. Đây là giới hạn công khai của bản nộp; không phát triển thêm corpus/models chỉ để che hạn chế. Nếu rubric yêu cầu toàn bộ recommendation data tự crawl, cần temporal design riêng; chưa thấy yêu cầu đó trong slide.

## 7. Hoàn thiện bản nộp và điểm dừng

1. **P0 — Extraction audit: đã làm**20pages,120agent-reviewed occurrences, sửa2context errors, raw-linked labels, hash manifests và portable audit verifier. Chưa claim human gold.
2. **P0 — Biên tập minh chứng: đã làm** báo cáo, kịch bản và deck10slides có charts/tables editable. Full grids/models giữ appendix. Deck preview được rà từng trang; đọc [QA](../reports/deliverables/README.md) để biết phạm vi kiểm tra.
3. **P0 — Tái kiểm tra: đã làm**108tests,2benchmark verifiers và crawl audit integrity checks. **Browser rehearsal còn cần người trình bày:** saved permission chặn origin ngày05/11. Không bypass để nhận đã UI QA. Hướng dẫn thao tác và bảng dự phòng ở [PRESENTATION](../reports/PRESENTATION.md).

Human review độc lập là bước nâng chất lượng nếu có reviewer, không được tự giả định hoàn thành. Không thêm GlobalPR/TF-IDF/corpus scale. **Điểm dừng:** kết luận có evidence, so sánh công bằng, limitations rõ và bộ tài liệu nộp được; không yêu cầu graph model phải thắng.

## 8. Một nguồn cho mỗi loại thông tin

- [PROJECT_PLAN](PROJECT_PLAN.md): scope và backlog hiện hành.
- [REPORT](../reports/REPORT.md): câu chuyện/báo cáo chính.
- [PRESENTATION](../reports/PRESENTATION.md): kịch bản bảo vệ chính.
- [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md): phần đã làm/chưa làm.
- [COURSE_ALIGNMENT](COURSE_ALIGNMENT.md): mapping kiến thức học phần; không tạo roadmap cạnh tranh.
- [RESEARCH_REPORT](../reports/RESEARCH_REPORT.md), [EXTENSION_RESULTS](../reports/EXTENSION_RESULTS.md), các planning cũ: tra cứu kỹ thuật/lịch sử.
- `RUN_PROTOCOL`, `EXTENSION_PROTOCOL`, manifests và frozen payloads: giữ nguyên bằng chứng thực nghiệm; tài liệu biên tập hiện tại không sửa lại protocol quá khứ.
