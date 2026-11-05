# Danh mục slide IT4868E và trang đối chiếu

Đối chiếu ngày **05/11/2026** từ ZIP do người dùng cung cấp: **14 PDF / 733 trang**. Đây là inventory nội dung học phần dùng để định hướng đồ án, không phải rubric chấm điểm.

Archive: `Web Mining - IT4868E-20261105T032711Z-1-001.zip`.
SHA-256: `8ad3ecd52d8f92e27d9aa4f379e3c584a1c54b99f9eca5365ce2bbd198e09259`.

Đã giải nén và kiểm tra hash từng file. Đường dẫn yêu cầu `/Web-Mining/Slide20261` không ghi được vì root filesystem macOS read-only; bản giải nén thực nằm ở thư mục `Slide20261` cạnh thư mục `project` trong thư mục môn học hiện có. Đường dẫn đầy đủ được báo cho người dùng trong phiên làm việc; repository không phụ thuộc đường dẫn tuyệt đối đó.

Đã trích text toàn bộ PDF để tra cứu, xem agenda/chủ đề của tất cả files và đọc các phần liên quan trực tiếp; kiểm tra ảnh trang bìa và các trang quan trọng có nội dung dạng ảnh. Không nhận đã OCR/kiểm chứng từng công thức trong toàn bộ733trang. Hai trang đầu của L01 là bìa HUST và trang trang trí, không chứa rubric. Không thấy file assignment/rubric riêng trong archive.

**Quy ước:** trang là số trang PDF từ1, tính cả bìa. Dùng tên file làm định danh vì một số title nội bộ ghi nhầm số lecture (ví dụ L04 ghi Lecture01); không suy ra thứ tự môn từ lỗi title. Các PDF/full-text/rendered pages chỉ lưu local, không đưa slide học phần lên GitHub.

| Mã | File | Số trang | Trang đối chiếu | Vai trò khi review |
|---|---|---:|---|---|
| L01 | `16-9-en-L01-Intro.pdf` | 47 | 13–14,39–46 | KDD, dữ liệu Web, crawling, động học và giới hạn dữ liệu |
| L02a | `16-9-en-L02-MachineLearning-01.pdf` | 55 | 8–12,27,32 | Task/metric, validation, temporal splitting, overfit, smoothing |
| L02b | `16-9-en-L02-MachineLearning-02.pdf` | 52 | 4–18,31–51 | FNN/RNN/LSTM/ensemble: nền tảng tham khảo; không tạo thêm prediction task |
| L02c | `16-9-en-L02-MachineLearning-03.pdf` | 68 | 23–26,47–67 | Distance/Jaccard, normalization, Positive–Unlabeled và selection assumption |
| L03 | `16-9-en-L03-DataVisualization.pdf` | 44 | 13–27,31–34 | Thống kê, quantiles, boxplot, histogram, scatter |
| L04 | `16-9-en-L04-InformationRetrieval.pdf` | 64 | 7,11–12,20–30,31–37,53–58 | Document query, VSM, metrics, HTML/main-content/anchors, index, rank fusion |
| L05a | `16-9-en-L05-LinkAnalysis-01.pdf` | 45 | 6–8,22–33,37–44 | Graph, centrality/prestige, PageRank, convergence, HITS root/base graph |
| L05b | `16-9-en-L05-LinkAnalysis-02.pdf` | 52 | 4–31,32–51 | Community algorithms; Node2Vec/SGNS/p–q/graph representations |
| L06a | `16-9-en-L06-OpinionMining-01.pdf` | 41 | 5–25,26–31 | Opinion/sentiment; Word2Vec background, không phải task chính |
| L06b | `16-9-en-L06-OpinionMining-02.pdf` | 58 | 4–16,17–32,33–57 | Aspect/sentiment, Twitter/forums, active learning: ngoài scope |
| L06c | `16-9-en-L06-OpinionMining-03.pdf` | 39 | 4–26,27–38 | Entity assignment, comparative opinions: ngoài scope |
| L07 | `16-9-en-L07-InformationExtraction.pdf` | 66 | 5–8,13–27,28–45,46–65 | NER, relation extraction, distant supervision, coreference; không đồng nhất HTML parsing |
| L08 | `16-9-en-L08-RecommendationSystems.pdf` | 59 | 6,10,15–24,30–35,49–58 | Recommendation, metrics, CF/MF, implicit feedback và session constraints |
| L09 | `16-9-en-L09-OnlineAd-QueryMining.pdf` | 43 | 21–24,28–35 | Feedback/logs, query preprocessing và n-gram: liên hệ giới hạn, không thêm ads task |

## Đọc theo mục tiêu của đồ án

1. **L04 tr.28,53 + L05a tr.26–33:** nối crawling/preprocessing với graph ranking.
2. **L05a tr.37–44 + L05b tr.32–48:** HITS và Node2Vec, phân biệt đúng biến thể implementation.
3. **L02a tr.11 + L04 tr.20–23 + L08 tr.19:** temporal validation và retrieval/ranking metrics.
4. **L04 tr.55–58 + L02c tr.25–26:** fusion, score scales và normalization.
5. **L03 tr.13–27 + L08 tr.15:** phân bố traffic, sparsity/drift và error analysis.
6. **L02c tr.47,66–67 + L08 tr.50–58:** unlabeled≠negative; điều kiện để được gọi session recommendation.

[PROJECT_PLAN](PROJECT_PLAN.md) quyết định scope/backlog; [COURSE_ALIGNMENT](COURSE_ALIGNMENT.md) chỉ đối chiếu kiến thức; [COURSE_PRESENTATION](../reports/COURSE_PRESENTATION.md) là kịch bản12–15phút. [Manifest](evidence/course-slides-manifest.json) chứa filename, page count, checksum và phạm vi kiểm chứng để đối chiếu lại đúng bộ slide.
