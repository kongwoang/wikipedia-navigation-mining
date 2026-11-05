# Kịch bản bảo vệ thống nhất — 12–14 phút

**Wikipedia Navigation Mining: When Do Hyperlinks Help Beyond Click History?**
Bản chính ngày 05/11/2026. [Deck PPTX 10 slides](deliverables/Wikipedia_Navigation_IT4868E.pptx) có native editable charts/tables và speaker notes; [QA/lineage](deliverables/README.md). Dùng cùng 2 RQ, 5 phương pháp + 2 references và kết luận trong [REPORT](REPORT.md); [PROJECT_PLAN](../docs/PROJECT_PLAN.md) là scope duy nhất.

## Người nghe cần nhớ một điều

“Hyperlinks cho biết đường đi khả dụng; historical clicks cho biết những đường đi đã được sử dụng. Trong dữ liệu này, frequency rất mạnh. Topology bổ sung một số gợi ý khi thiếu counts, nhưng hybrid chưa chứng minh gain tổng thể ổn định.”

Không mở đầu bằng số algorithms, số triệu edges hoặc số tests. Những con số đó chứng minh phạm vi/kỹ thuật sau khi người nghe hiểu câu hỏi.

## Mười slide, mỗi slide một thông điệp

| Slide | Phút | Thông điệp | Evidence / điều phải nói |
|---|---:|---|---|
| 1. Tại sao cần xếp hạng links? | 0:45 | Một article có nhiều links, người đọc không chọn như nhau | Source-conditioned task; không user/session claim |
| 2. Hai nguồn tín hiệu | 1:00 | H là availability/structure, C là observed behavior | Directed graph, independent H 2018, published/censored counts |
| 3. Tự thu thập và preprocessing | 1:15 | Link graph phụ thuộc cách parse trang | Audit20pages: API1.397 vs body1.049edges; 20matched revisions; agent tìm2context errors trong120occurrences;2026tách2018 |
| 4. EDA dẫn đến giả thuyết | 1:00 | Traffic concentration khiến Markov là baseline phải vượt | Concentration + degree–traffic scatter; không suy unobserved=zero |
| 5. Các phương pháp có vai trò gì? | 1:30 | Frequency, authority, proximity, embedding và fusion | Markov/HITS-global/PPR/Node2Vec/fusion; Uniform/Global làm references; shared candidates |
| 6. Đánh giá để kết luận đúng | 1:15 | So cùng future labels, không chọn test winner | Chronology, validation, full vs conditional, macro/weighted, primary CI |
| 7. Kết quả tổng thể | 1:15 | Local counts mạnh; fusion gain nhỏ/chưa chắc chắn | Bảng 7 rows; May 0,8991→0,9034; paired CI chứa 0; June weighted reversal |
| 8. Topology giúp gì và gây hại ở đâu? | 2:15 | Conditional usefulness khác aggregate benefit | A7 unobserved recall + Danza gain/Tragacete loss trong demo gốc |
| 9. Có phải thuật toán chạy sai/graph quá nhỏ? | 1:15 | Chẩn đoán và controls hỗ trợ diễn giải có giới hạn | PPR residual/SGNS/seeds; full-H control; rolling là protocol khác; cost |
| 10. Kết luận, giới hạn và đóng góp | 0:45 | Quyết định dựa trên signal/evidence, không độ phức tạp model | Sample/censoring/cold limitations, agent audit chưa là human gold, reproducible comparison |

Tổng 12 phút 15 giây; dành 1–2 phút buffer. Bảng 14 models và detailed grids ở appendix, không thêm slide chỉ để liệt kê một thuật toán đã chạy. Không đem CycleRank/tie-break thành nhân vật chính của một câu chuyện về score fusion.

## Demo chính: dùng đúng models và đúng thời điểm

Mở [demo gốc](generated/demo.html), tháng May 2018, metric denominator **Full**. Chỉ hiển thị/giải thích `M1B_backoff`, `M3_ppr_h`, `M5H_node2vec`, `M6B_fusion`; UI vẫn có các models khác để audit, không cần click hết. Không đổi tháng để tìm case đẹp hơn.

1. **Danza posmoderna**: training chỉ có Danza contemporánea 62 clicks; future Merce Cunningham 16 clicks. Markov ngoài Top-10, PPR/fusion rank 5. NDCG 0,6805→0,8764. Mở count columns để chỉ ra graph phân biệt targets thiếu published counts; Node2Vec-H không tìm được positives ở case này.
2. **Tragacete**: fusion NDCG 0,7353 thấp hơn Markov 0,8616. So tail destinations, counts và scores. Đừng nói topology luôn giúp unobserved links hoặc coi mọi missing count là irrelevant.
3. Kết lại bằng average CI chứa 0: hai cases giải thích cơ chế, không chứng minh average improvement. Cases được chọn sau test theo rule để minh họa.

[CASE_STUDIES](CASE_STUDIES.md) có exact tables; nếu UI lỗi thì dùng bảng này, không hardcode lại predictions. **Remora** là backup khi được hỏi hub bias: PPR 0, Markov 1; không thay Tragacete vì Remora không phải fusion failure.

Crawl demo mở [audit report](crawl/audit-v2/AUDIT.md), [annotation4199047:47](../docs/evidence/crawl-audit-labels.json) và raw/structured record đã cache nếu có: page indicator có nested `mw-parser-output` nhưng nằm ngoài article body. Giải thích vì sao hai parsers cùng đồng ý vẫn cùng sai policy. Agent review120occurrences không phải human gold. Không nối current crawl với clicks2018 để minh họa causal effect.

## Appendix chuẩn bị, không thuyết trình tuần tự

- Metric definitions, same-candidate/full-denominator contract và bảng Recall/MRR/NDCG cần có.
- PageRank→PPR, HITS-global khác query-root HITS, Node2Vec p/q/SGNS/directed convention.
- Matched H/weighted-H controls: clicks giúp walks không đồng nghĩa topology hơn frequency.
- Full-H, rolling, degree-null/panels; nhắc comparator của rolling CI là tie−M1, không fusion−M1B.
- Source/data hashes, code/tests và reproduction; không biến số tests thành kết luận nghiên cứu.

[DEFENSE](DEFENSE.md) giữ ngân hàng câu hỏi rộng; chỉ ôn các phần hỗ trợ 2 RQ trước. [COURSE_ALIGNMENT](../docs/COURSE_ALIGNMENT.md) chỉ trang kiến thức trong slide.

## Rehearsal và tiêu chí đạt

- Chạy hai portable verifiers theo [REPRODUCIBILITY](REPRODUCIBILITY.md); không train/download live.
- Tự mở HTML, kiểm tra tìm source, chọn models/month, full/conditional controls và overflow. Browser interaction/visual QA vẫn chưa được xác nhận trong evidence hiện có.
- Kể được một gain/một loss bằng actual counts/ranks trong 2 phút; không chỉ đọc score.
- Nói rõ current crawl2026 là extraction audit,20pages/120occurrences đã làm bằng agent; chưa có human adjudication và held-out accuracy.
- Kết luận phân biệt “chưa chứng minh improvement” với “hai model tương đương” hoặc “topology vô ích”.

## Handoff khi không thể thao tác browser

Ngày05/11/2026, CUA từ chối mở `http://127.0.0.1:8765/demo.html` vì saved user permission blocks origin. Không thử browser khác, raw CDP hoặc workaround. Hai portable verifiers đã kiểm tra payloads/ranks/metrics; chúng không chứng minh DOM interactions hay visual layout đúng.

Người trình bày tự mở `reports/generated/demo.html`, làm hai cases trên, đổi May/June và Full/Conditional rồi kiểm tra source/model controls, bảng counts và overflow. Nếu lỗi UI, dùng [CASE_STUDIES](CASE_STUDIES.md) làm bảng evidence dự phòng và ghi nhận lỗi, không thêm predictions hardcoded. Chưa ghi nhận một cuộc bảo vệ thử có người trình bày hoặc thời lượng đo thực tế; 12–14phút là time budget của kịch bản.
