# Bổ sung dữ liệu tự crawl: API, HTML và cấu trúc trang

Ngày 29/10/2026. Người dùng yêu cầu thực hiện **cả API collection lẫn HTML crawling**. Phần nghiên cứu2018 và các frozen results được giữ nguyên; crawler là nhánh dữ liệu mới. Pilot đã chạy thật, không chỉ là proposal: [kết quả pilot](../reports/crawl/pilot-v2/PILOT.md).

## 1. Hướng nghiên cứu được khuyến nghị

Giữ Clickstream làm nguồn **observed navigation labels**, tự crawl article content và link structure để tạo thêm explanatory features. Crawl trang công khai không cho biết ai đã click từ bài nào sang bài nào; không thể thay Clickstream bằng một lượt BFS rồi gọi đó là hành vi người dùng.

Câu hỏi mở rộng: **ngoài click frequency và topology, vị trí/ngữ cảnh của hyperlink có giúp giải thích hoặc xếp hạng next-article destinations không?** Đây là liên kết trực tiếp giữa phần Web Mining tự xây và nghiên cứu đã có.

Tên mở rộng có thể là *Mining Wikipedia Navigation from Clickstream, Hyperlink Structure, and Crawled Page Content*. Chỉ đổi title/report chính sau khi feature experiment có kết quả; chưa quảng bá current pilot là accuracy improvement.

| Nguồn | Tự thu thập gì? | Vai trò | Không cung cấp |
|---|---|---|---|
| MediaWiki Action API | Page IDs, current revisions, outgoing main-namespace link titles, wikitext, historical revisions trước cutoff | Metadata, graph extraction, provenance, historical content | Individual clicks/sessions; vị trí visual trên trang |
| HTML `/wiki/Title` | Nội dung article body, link occurrences, anchor text, section, document order, paragraph index, infobox/reference context | Page-structure features, kiểm tra phạm vi graph, demo evidence | Click counts, viewport exposure, historical HTML2018 |
| Published Clickstream | Aggregate transition counts | Labels và behavior baselines | Article content, DOM, user identities |

API là tự thu thập qua structured interface. HTML mode tải trang rồi tự parse bằng `html.parser.HTMLParser`; không dùng API trả sẵn HTML thay cho bộ HTML crawler.

## 2. Hai trục thời gian phải tách biệt

### Current collection: API + HTML

Thu thập current API response và canonical HTML, lưu request timestamps, revision IDs và raw bytes. Chỉ tính extraction-agreement metrics khi page ID và revision ID khớp. Khác revision thì giữ record và gắn mismatch, không quy chênh lệch cho parser.

Ngay cả cùng article revision, template changes và cache lag có thể tạo khác biệt. Crawl trong một khoảng thời gian không phải snapshot nguyên tử. Current graph/content **không được làm features cho labels2018**.

### Historical API collection

Dùng `prop=revisions`, `rvstart=cutoff`, `rvdir=older`, `rvlimit=1`, kiểm tra returned timestamp≤cutoff. API hỗ trợ tìm revisions theo thời gian. [MediaWiki Revisions documentation](https://www.mediawiki.org/wiki/API:Revisions).

Lưu raw historical wikitext, không render lại rồi gọi đó là HTML của2018. Đúng article revision chưa đủ bảo đảm historical template expansion. Vấn đề này được xử lý chuyên biệt trong [WikiHist.html](https://arxiv.org/abs/2001.10256), vì vậy không giả định remote rendering hiện nay tái tạo historical exposure.

Pilot lấy history của page identity đã resolve hiện tại. Trước khi nhập vào benchmark, phải đối chiếu `page_id` với historical mapping có sẵn; current title/current redirect không được tự thay historical title/redirect. Historical-missing phải giữ missing indicator, không lấp bằng current content. Hai trang phát hiện ở BFS không có historical revision trước cutoff đã được ghi lỗi riêng.

## 3. Implementation đã có

- `src/wikinav/crawl.py`: bounded serial transport, raw cache, resumable state, current API collector, direct HTML collector, historical revision collector, HTML extraction và revision comparison.
- `src/wikinav/crawl_export.py`: kiểm tra hashes, replay API pagination/HTML parser từ raw captures không gọi mạng, xuất graphs/features và report.
- `configs/crawl-pilot.toml`: edition, mode `api|html|both`, seeds, depth/page/request/byte budgets, delay, historical cutoff.
- `tests/test_crawl.py`: offline fixtures, pagination/revision errors, URL/namespace filtering, cutoff checks, access/rate controls, raw replay, unknown frontier, resume, hai collectors chạy độc lập.

Dùng standard library, chưa thêm Scrapy/browser automation/dependency khoa học. Direct HTML được parse offline; không chạy JavaScript của trang. Code mới không thay algorithm files đã tạo frozen benchmark.

### Chạy pilot

```bash
PYTHONPATH=src python3 -m wikinav.crawl \
  --config configs/crawl-pilot.toml \
  --output data/raw/crawl/my-pilot

PYTHONPATH=src python3 -m wikinav.crawl_export \
  --raw data/raw/crawl/my-pilot \
  --processed data/processed/crawl/my-pilot \
  --report reports/crawl/my-pilot

PYTHONPATH=src python3 -m unittest discover -s tests -p test_crawl.py -v
```

Muốn chạy từng cách: sao chép config và đổi `mode="api"` hoặc `mode="html"`, dùng output mới. `html` chạy độc lập không gọi API; do thiếu namespace inventory, mode này loại bảo thủ mọi title có dấu `:`, có thể mất một số main-namespace titles hợp lệ. `both` dùng namespace metadata/aliases để phân loại chính xác hơn.

Chạy lại cùng config/code/output sẽ dùng raw cache và state. Thay config/code phải dùng output mới; không trộn protocol trong một crawl. HTTP request budget áp dụng mỗi invocation; page budget giới hạn toàn crawl. Record lỗi terminal được giữ, không tự thay source bằng trang dễ crawl hơn. Responses redirects không được tự follow; HTTP redirects trở thành lỗi cần audit.

### Raw artifacts và provenance

`raw/<url_sha256>.body` + metadata JSON: URL, status, bytes, SHA256, fetched_at, Content-Type, ETag/Last-Modified nếu có. `pages/*.json`: structured API/HTML records, occurrences và historical wikitext. `state.json`: signature, completed/failed sources và frontier. Raw content không commit vào Git.

Cache là archive của một run, không cam kết là nội dung mới nhất mỗi lần resume. Pilot-v2 tái sử dụng một phần captures từ interrupted pilot-v1; final transport thêm pause5s sau API response chậm hơn1s. Capture times và record hashes giữ nguyên; export replay đã xác minh lại parsing.

### Processed artifacts

| File | Trường chính | Ngữ nghĩa |
|---|---|---|
| `nodes.jsonl` | node_id, title, page_id, crawled, outgoing_unknown | Target chưa resolve có ID dựa trên title; không giả canonical page ID |
| `api_edges.jsonl` | source, target, target_title, weight=1 | API main-namespace link presence; có thể khác body graph |
| `html_edges.jsonl` | source,target,occurrence_count,first_body_link_position,first_section,in_lead | Link repetition là editorial signal, không click-frequency weight |
| `occurrences.jsonl` | href,anchor_text,section,paragraph_index,excluded_context,redlink | Giữ evidence ở mức occurrence, không chỉ deduplicate edges |
| `pages.jsonl` | title,text,article_url,api_revision,html_revision | Text/context phục vụ feature extraction sau này |
| `manifest.json` | config/code signature, hashes, summary | Audit và replay |

Known crawled source aliases được gom theo page ID; duplicate source–target pairs sau mapping được gộp, API presence giữ weight1, HTML occurrence counts cộng lại và giữ first position sớm nhất. Target còn lại chưa được canonicalize đầy đủ; namespace/existence/redirect coverage là việc cần làm trước model training. Frontier chưa crawl là **unknown outgoing neighborhood**, không phải out-degree0. Self-edges được bỏ khi xuất graph, raw occurrences vẫn giữ để audit.

## 4. Pilot thực tế và ý nghĩa

Pilot giới hạn8 trang, depth1, tối đa80 network requests mỗi invocation. Năm seeds lấy deterministic hash từ original train-defined query panel; không dùng test rankings/labels để chọn seeds.

Kết quả: 8/8 cặp API–HTML cùng revision,654 API edges,556 HTML body edges,1.028 occurrences;6 historical revisions phù hợp cutoff.26 cached responses tổng1.423.505bytes. Graph export575 nodes nhưng chỉ8 source pages đã crawl;567 unresolved target nodes không phải567 trang đã tải.

Với *Municipio de Cumberland (condado de Adams)*, API có33 target titles, HTML body13; all-context HTML agreement=1.0, body agreement≈0.394. Khác biệt phù hợp với việc loại infobox/reference context. Không tự coi body-only tốt hơn: infobox links có thể hữu ích cho navigation và phải được kiểm tra bằng ablation.

Pilot thiên về wrestling do thứ tự BFS và seed đầu nhiều links. Nó chứng minh pipeline hoạt động, **chưa là corpus representative** và chưa chứng minh ranking improvement. Khoảng1,4MB là bytes đã đo cho pilot, không ngoại suy tuyến tính thành thời gian/RAM cho toàn Wikipedia.

## 5. Thiết kế thí nghiệm tiếp theo

| Experiment | Hypothesis | Controls | Metrics / evidence | Trạng thái |
|---|---|---|---|---|
| API vs HTML extraction | Different link scope làm graph khác nhau | Same page/revision; all-context vs body-only | Jaccard, extra/missing titles, manually audited examples | Pilot đã có |
| Body vs all article contexts | Loại structural boxes thay topology/recommendations | Same sources và shared candidate union; coverage riêng từng method | Degree/components, rank overlap; ranking metrics chỉ khi có compatible labels | Chưa chạy |
| First-link / lead-link baseline | Link document order có thông tin ngoài uniform/degree | Eligible candidates cố định; feature chỉ từ snapshot hợp lệ | Recall/MRR/NDCG, source groups | Chưa implement/evaluate |
| Link repetition baseline | Repeated mention có ích hơn một binary edge | Presence vs occurrence count, cùng support | Ranking quality và hub/popularity analysis | Features đã xuất; model chưa chạy |
| Click + structural features | Local counts bỏ sót prominence/context | Markov + controlled fusion; validation-only tuning | Paired source deltas, matched feature ablations | Chưa chạy |
| Historical content model | Article text/context bổ sung semantics | Historical cutoff, audited mapping, frozen feature vocabulary | BM25/TF-IDF baseline nếu có lý do; compare conventional models | Chưa chạy |

Không dùng DOM document order như measured click exposure. Không dùng API-vs-HTML Jaccard như accuracy recommendation. Không lấy Clickstream missing pairs làm reliable negatives.

### Hai đường evaluation hợp lệ

1. **Đường gần với project hiện tại:** historical wikitext trước cutoff, parse direct links/text bằng parser có tests; historical mapping giữ nguyên. Các tháng May–September đã được phân tích nên model mới trên đó là exploratory. Muốn confirmation phải khóa model/feature protocol rồi xác minh một tháng chưa đọc; chưa xác nhận availability và chưa tải tháng mới trong lượt này.
2. **Đường current HTML:** freeze crawl kết thúc trước evaluation month; dùng Clickstream tương lai khi release có thật. Thời gian chờ release là dependency thực tế. Nếu chưa có labels phù hợp, chỉ báo crawl/graph/feature EDA, không lấy labels2018 để tạo benchmark giả.

Không cần bỏ bộ dữ liệu sẵn có: mỗi nguồn đóng vai trò khác nhau. Crawl cho content/structure, Clickstream cho observed behavior, historical independent graph cho benchmark đã chốt.

## 6. Mở rộng có kiểm soát

P0 đã hoàn thành: hai collectors, raw provenance/cache, bounded BFS, parser/features, historical revision fetch, unit tests, real pilot, raw replay và graph export.

P1 kế tiếp: kiểm tra thủ công ít nhất20 trang thuộc nhiều loại; khóa selectors/filter policy; resolve target IDs/redirects theo đúng thời gian; sau đó thu100–200 source pages có sampling protocol rõ. Với HTML current, cân bằng quota giữa seeds/strata hoặc round-robin frontier để hạn chế việc một hub chiếm budget. Không gọi BFS sample là uniform random sample.

P1 modeling: chọn một câu hỏi structural feature; triển khai First-Link và repetition baselines trước learned model. Khóa feature/candidate/split policy trước fresh labels. Báo retained source/candidate coverage, không chỉ metrics của subset dễ map.

P2: mở context lên500–2.000 pages nếu pilot sau audit cho phép; đó là budget đề xuất, chưa là số đã crawl. Không crawl toàn Wikipedia khi dump đã đáp ứng topology task. Authentication/quota setup cần được xem trước khi tăng request volume đáng kể.

Definition of done cho **crawl-based study** rộng hơn: corpus và temporal manifest được khóa; target mapping audited; candidate boundary ghi rõ; ít nhất một conventional structural baseline và matched ablation; compatible future labels hoặc honest graph-only scope; reproducible parsing và actual result tables. Pilot hiện tại chưa được gọi là đã hoàn tất stage này.

## 7. Truy cập và attribution

Crawler dùng User-Agent có project URL, một request tại một thời điểm, tối thiểu1s giữa requests; pause5s sau API request mất>1s; `maxlag=5`, Retry-After/backoff có giới hạn, dừng khi401/403 thay vì đổi identity/proxy. HTML kiểm tra robots và chỉ lấy `/wiki/Title` không query parameters; không crawl `oldid` HTML. Đây là lựa chọn bám [Wikimedia Robot policy](https://wikitech.wikimedia.org/wiki/Robot_policy), [API etiquette](https://www.mediawiki.org/wiki/API:Etiquette) và [rate limits](https://www.mediawiki.org/wiki/Wikimedia_APIs/Rate_limits), đã kiểm tra ngày29/10/2026; giới hạn server có thể thay đổi.

Wikipedia article text không mang license CC0 của Clickstream. Lưu article URL/revision và attribution; kiểm tra license của nội dung trước redistribution. Xem [Content reuse](https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse). Không thu ảnh/media trong pilot. Published report chỉ có counts, source titles, provenance và URLs; raw HTML/wikitext ở thư mục Git-ignored.
