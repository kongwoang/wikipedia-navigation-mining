# Audit extraction: 20 trang, hai phương thức thu thập

Ngày 05/11/2026. Đây là dữ liệu **tự crawl** bằng MediaWiki API và HTML, kiểm tra Web Content/Structure Mining; không dùng current crawl làm topology cho test Clickstream 2018.

## Chọn mẫu trước khi thu

[Protocol](../../../docs/evidence/crawl-audit-protocol.json) khóa 20 source IDs dựa trên traffic strata và hyperlink out-degree của panel train 2018: 4 strata × 5 degree blocks, chọn SHA256 trong từng block. Không dùng test outcome để chọn trang, không thay trang thất bại. Depth 0, 20 seeds, tối đa 100 requests, serial delay 1,5 giây; đây là sample có chủ đích bao phủ strata, không đại diện toàn Wikipedia. Khi crawl, title có thể đổi: Repollo relleno được resolve thành Col rellena.

## Thu thập và đối chiếu

- 20/20 trang thành công, 20/20 cặp API/HTML khớp article revision; 42 cached responses, 3.979.415 decoded bytes. Thời gian UTC và raw hashes nằm trong [provenance](provenance.json).
- Sau sửa: API graph **1.397 edges**, HTML body graph **1.049 edges**, **1.936 article-link occurrences** ở mọi ngữ cảnh được giữ. Hai graph khác phạm vi, không phải hai phép đo cùng ground truth.
- 1.283 nodes được xuất, trong đó 1.263 targets chưa crawl/resolve outgoing. Chúng là **unknown**, không được coi là dangling. Không dùng graph sample này để suy đặc tính toàn mạng.
- Gzip có giới hạn ở cả wire bytes và decoded bytes; User-Agent có URL project, robots/rate limit/Retry-After được xử lý. Chính sách tham chiếu: [Wikimedia Robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy).
- Không fetch historical revisions trong audit này. Khớp revision không đảm bảo template/cache cập nhật đồng thời; anchor position là document order, không phải viewport exposure.

## Hai lớp kiểm tra và lỗi thực sự tìm được

1. **Differential DOM audit**: parser production standard-library HTMLParser được so với BeautifulSoup + html5lib (cài riêng bằng requirements-audit.lock). Tất cả article-link occurrence multisets và body target sets của 20 trang đồng ý trước và sau sửa. Đây là kiểm tra implementation, không phải chứng cứ rằng định nghĩa body đúng.
2. **Rà ngữ cảnh bởi agent**: [120 occurrences cố định](../../../docs/evidence/crawl-audit-review-pool.json), mỗi trang 2 body, 2 excluded, 1 outside, 1 ineligible nếu có; thiếu stratum thì bù bằng hash. Agent đọc anchor, ancestry và ngữ cảnh; [nhãn và lý do](../../../docs/evidence/crawl-audit-labels.json) được lưu. Đây **không phải human gold**, không có người gán nhãn độc lập hay inter-annotator agreement.

| Trên cùng 120 occurrences | TP | FP | TN | FN |
|---|---:|---:|---:|---:|
| Trước sửa | 38 | 2 | 80 | 0 |
| Sau sửa | 38 | 0 | 82 | 0 |

Hai lỗi: `4199047:47` (Estación Experimental Pavlovsk) là link Coordenadas trong page indicator phía trên article, dù có nested `mw-parser-output`; `2205329:137` (Remora) là icon Wikispecies trong authority-control linked-project block. Parser trước đó nhận cả hai là body. Đã loại indicator roots và loại authority/linked-project blocks khỏi eligible body. Link Wikispecies thông thường ở list nội dung vẫn được giữ: chính **context**, không target title, quyết định inclusion.

Precision trên sample thay đổi 38/40 → 38/38; không gọi đây là “độ chính xác 100% trên Wikipedia”. Sample không đồng đều, cùng agent vừa review vừa sửa, và được tái sử dụng sau sửa; đây là regression evidence, **không có held-out extraction accuracy**. Cần người review độc lập và sample mới nếu muốn ước lượng accuracy. Hai parser cùng sai policy trước sửa là ví dụ vì sao differential agreement không thay được semantic review.

## Provenance và tái chạy

Raw captures cùng records ban đầu vẫn ở `data/raw/crawl/audit-v1/` (Git-ignored). Không sửa chúng. Export sau sửa nằm `data/processed/crawl/audit-v2/`; `--reparse` là lựa chọn tường minh, lưu original crawl signature và parser SHA256 mới. Vì kết quả extraction thay đổi, `raw_parsing_replay_verified=false` là **đúng và có chủ đích**; raw hashes và API pagination replay vẫn được xác minh. Strict export mặc định sẽ từ chối parser khác.

```sh
PYTHONPATH=src python3 -m wikinav.crawl_export --raw data/raw/crawl/audit-v1 --processed data/processed/crawl/audit-recheck --report reports/crawl/audit-recheck --reparse
PYTHONPATH=src .audit-venv/bin/python scripts/audit_crawl.py --raw data/raw/crawl/audit-v1 --out .cache/audit-recheck --review-pool docs/evidence/crawl-audit-review-pool.json
```

Tạo `.audit-venv` riêng và cài `requirements-audit.lock` nếu cần differential audit; core crawler không cần các dependency đó. Output directories phải mới. Raw HTML không commit: clone sạch kiểm tra report manifest và annotations được, nhưng không replay raw nếu chưa có captures. Crawl lại ở ngày khác có thể khác revisions; đó là collection mới, không bit-identical reproduction. Text/anchors theo Wikipedia article licensing/history (CC BY-SA), khác Clickstream CC0.

## Bài học gắn với môn học

L04: crawl, main-content extraction, anchor/context features và data quality. L05: graph xây từ output extraction cần định nghĩa edge rõ. L02: kiểm tra đúng target và giới hạn của evaluation. Insight cần trình bày: **API links, article-body links và observed clicks là ba đại lượng khác nhau**; không thể thay thế lẫn nhau mà không đổi câu hỏi nghiên cứu.
