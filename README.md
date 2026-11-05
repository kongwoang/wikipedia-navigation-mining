# Wikipedia Navigation Mining

**When Do Hyperlinks Help Beyond Click History?**
Đồ án Web Mining — IT4868E. Xếp hạng bài tiếp theo dựa trên article đang đọc, không có user/session personalization.

**Thông điệp chính:** hyperlink mô tả các đường đi có thể có; lịch sử clicks phản ánh những đường đi đã được sử dụng. Trong sample lịch sử này, local frequency là baseline mạnh. Topology giúp tìm một số destinations chưa có published training count, nhưng chưa tạo gain tổng thể đáng tin cậy khi kết hợp với behavior.

## Đọc theo thứ tự

1. [Phạm vi và backlog đã thống nhất](docs/PROJECT_PLAN.md).
2. [Báo cáo chính: câu hỏi → dữ liệu → so sánh → insight](reports/REPORT.md).
3. [Kịch bản bảo vệ](reports/PRESENTATION.md) và [demo từ predictions thật](reports/generated/demo.html).
4. [Trạng thái thực tế](docs/IMPLEMENTATION_STATUS.md) và [tái lập](reports/REPRODUCIBILITY.md).

[Đối chiếu slide môn học](docs/COURSE_ALIGNMENT.md) · [Danh mục14 PDF/733 trang](docs/COURSE_SLIDE_INDEX.md).

## Phạm vi cô đọng

- **Thu thập và kiểm tra dữ liệu:** MediaWiki API + HTML crawler, raw cache/revisions, main-body links/anchor/context extraction.
- **So sánh chính:** Markov, HITS-global, PPR-H, Node2Vec-H và score fusion; Uniform/Global Popularity là2 reference baselines.
- **Giải thích:** matched weighting ablations, training-unobserved transitions, một gain/một failure, temporal uncertainty và cost.

Benchmark eswiki 2018 đã hoàn tất: Jan–Mar train, April validation, May primary test, June fixed-model horizon; independent H 01/03/2018. Có200 sampled sources,127/122có observable labels ở May/June. May macro full NDCG@10: Markov 0,8991; PPR-H0,3126; fusion 0,9034. Fusion−behavior Δ0,00429,95% CI [−0,00076;0,01035]: chưa xác nhận reliable improvement.

**Nhánh crawl mới chỉ ở mức pilot:**8 pages,654 API edges,556 HTMLbody edges,1.028 occurrences. Current crawl 2026 không dùng làm features cho labels 2018. Manual extraction audit 20 pages còn thiếu; chưa có recommendation experiment dùng crawled features. [Pilot và provenance](reports/crawl/pilot-v2/PILOT.md) · [Cách chạy crawler](docs/CRAWLING_EXTENSION.md).

Không thêm model/dataset để mở rộng số lượng. CycleRank/adaptive/null/panel experiments đã có được giữ làm phụ lục; Global PR mới, content ranking, sentiment/NER/CF/RNN không còn backlog bản nộp.

## Kiểm tra nhanh

Python≥3.11, không tải real datasets hoặc retrain:

```bash
PYTHONPATH=src python3 -m wikinav.verify_bundle
PYTHONPATH=src python3 -m wikinav.verify_extensions
PYTHONPATH=src python3 -m unittest discover -s tests -p test_core.py
```

Mở `reports/generated/demo.html` trực tiếp để xem frozen rankings. Data verification không thay browser interaction QA; rehearsal vẫn cần thực hiện. [Reproduction guide](reports/REPRODUCIBILITY.md) chứa lệnh raw-to-model, dependencies, CPU/RAM requirements và giới hạn cross-platform.

## Phụ lục và bằng chứng đầy đủ

[Bảng 14 models](reports/RESULT_TABLES.md) · [Cases](reports/CASE_STUDIES.md) · [Báo cáo kỹ thuật đầy đủ](reports/RESEARCH_REPORT.md) · [Robustness extensions](reports/EXTENSION_RESULTS.md) · [Defense](reports/DEFENSE.md) · [Attributions](docs/ATTRIBUTIONS.md).

Bảng chính rút gọn theo vai trò/môn học sau thực nghiệm; toàn bộ kết quả vẫn được giữ. Source code, tests và frozen artifacts không bị xóa khi thu gọn cách trình bày. `docs/PROJECT_PLAN.md` là nguồn scope duy nhất; các protocol cũ tiếp tục ghi đúng lịch sử các lần chạy.
