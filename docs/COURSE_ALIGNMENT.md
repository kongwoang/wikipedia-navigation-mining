# Liên hệ học phần IT4868E trong phạm vi đã thống nhất

Ngày 05/11/2026. Đã review 14 PDF / 733 trang từ bộ slide người dùng cung cấp; [inventory và trang nguồn](COURSE_SLIDE_INDEX.md), [manifest](evidence/course-slides-manifest.json). Không có rubric assignment riêng trong ZIP.

**Scope/backlog duy nhất:** [PROJECT_PLAN](PROJECT_PLAN.md). Mapping dưới đây giải thích những kiến thức phục vụ câu hỏi “topology bổ sung gì ngoài click history?”, không tạo thêm yêu cầu chạy algorithms để đủ chương. Đề xuất trước đây về Global PR/TF-IDF hoặc scale corpus đã được bỏ khỏi backlog bản nộp.

| Kiến thức | Trang PDF | Áp dụng thực chất | Không nhận quá mức |
|---|---|---|---|
| KDD/data quality | L01 tr.13–14,39–46 | Raw acquisition → preprocessing → graph → ranking → evaluation | Không dùng volume/model count thay insight |
| Web preprocessing/crawling | L04 tr.24–30,53 | API + HTML, anchor/context/main body, cache/hash, extraction audit | Current crawl không thay historical benchmark hoặc chứng minh ranking gain |
| Graph ranking | L05a tr.6–8,24–44 | Directed H/C, row normalization, PPR residual, HITS authority | PPR source-seeded khác global PR; fixed-H HITS khác query-root HITS |
| Graph representation | L05b tr.32–48 | Directed Node2Vec, p/q, SGNS, cosine, seeds | Walks không là human sessions; cosine không là directed click probability |
| Score fusion | L04 tr.55–58; L02c tr.25–26 | Normalize behavior/PPR trên candidates rồi weighted sum | Không chạy mọi rank-fusion variant trong slide |
| Validation/evaluation | L02a tr.10–11,27; L04 tr.20–23; L08 tr.19 | Temporal splits, validation knobs, Recall/MRR/NDCG, macro/weighted | Rating MAE/RMSE không bắt buộc cho ranking; không random split monthly counts |
| Recommendation | L08 tr.6,10,15,50–58 | Context = current article, sparsity/drift, next-item ranking | Không có users/sessions để chạy CF/RNN; source article không phải user |
| Visualization | L03 tr.13–27,31–34 | Traffic concentration, degree–traffic, paired/subgroup deltas | Không thêm SOM/community hairball không trả lời RQ |
| Missing observations/PU | L02c tr.47,66–67 | Unlabeled ≠ negative; kiểm tra suppression bias | Count-threshold selection không mặc định thỏa SCAR; không claim PU learner |
| IE/opinion/query mining | L07 tr.5–8,13–27; L06; L09 tr.21–35 | Dùng để giải thích ranh giới input/labels | HTML parsing không là NER/semantic RE; không thêm sentiment/ads/session task |

BFS của crawler quyết định sample và coverage; biased walks của Node2Vec tạo training contexts. Hai thứ cùng dùng graph nhưng khác mục đích, không nhầm frontier sampling với model hyperparameters.

Chi tiết Node2Vec: `p` điều khiển return, `q` điều khiển outward bias; giải thích bằng các trọng số 1/p, 1, 1/q và normalization, không học thuộc một khẩu hiệu BFS/DFS. Jaccard trong slide L02c tr.24 là distance; report crawl dùng similarity intersection/union. Text normalization nếu có khác stable article-ID mapping.

**Trọng tâm bảo vệ:** Link Analysis + Web preprocessing + ranking evaluation; ML/Visualization hỗ trợ tính đúng và diễn giải. Thể hiện các kiến thức này trong một chuỗi lập luận; không cần phủ toàn bộ syllabus bằng model mới.
