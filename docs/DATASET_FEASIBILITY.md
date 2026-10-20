# Kiểm toán tính khả thi dữ liệu

Ngày kiểm tra: **20/10/2026**. Đây là planning; chưa tải dataset, chưa kiểm tra các dòng dữ liệu thật, chưa có kết quả thực nghiệm. “Đã xác minh” dưới đây nghĩa là đã đọc nguồn sơ cấp hoặc directory listing, không đồng nghĩa đã chạy pipeline.

## 1. Quyết định dữ liệu

**Primary có điều kiện:** Spanish Wikipedia (`eswiki`), Clickstream 2018-01 đến 2018-05 và WikiLinkGraphs snapshot **2018-03-01**. Train tháng 01–03, validation tháng 04, test tháng 05. Đây là historical retrospective benchmark, sử dụng graph được tái dựng về trạng thái lịch sử; không tuyên bố hệ thống đã có thể được triển khai với các file công bố sau đó ngay trong năm 2018.

Chọn `eswiki` vì chi phí file graph thấp hơn English và có đủ các tháng cần thiết. Ngôn ngữ không thay đổi công thức xếp hạng; phân tích định tính phải giữ nguyên title tiếng Tây Ban Nha, có chú giải tiếng Việt và kiểm tra nghĩa. Không suy rộng kết quả sang mọi Wikipedia. Nếu yêu cầu học phần bắt buộc English, thay edition trước khi mở test và áp dụng lại resource gate.

**Fallback:** Wikispeedia, với câu hỏi đổi thành xếp hạng bước đi trong trò chơi điều hướng có mục tiêu. Không trộn điểm số của hai dataset vào một bảng “cải thiện trên Wikipedia browsing”.

**Optional extension:** thêm một temporal window với Clickstream 2018-06, graph vẫn cố định, để kiểm tra độ ổn định. Chỉ làm sau khi primary pipeline hoàn chỉnh. Thí nghiệm sequence-aware trên Wikispeedia là hướng thay thế P2, không phải yêu cầu cộng thêm.

## 2. Bằng chứng về Clickstream

Nguồn [Meta-Wiki](https://meta.wikimedia.org/wiki/Research:Wikipedia_clickstream) mô tả bốn trường `prev`, `curr`, `type`, `n`: các cặp referrer–resource được tổng hợp theo tháng. `link` là cặp bài có hyperlink; `other` là điều hướng nội bộ không được xác định là link; `external` là referral bên ngoài. Tài liệu mô tả loại bỏ cặp có **10 quan sát trở xuống**, nên kiểm tra kỳ vọng `n > 10`, không viết `n >= 10`. Có xử lý redirect ở upstream và khác biệt giữa các release lịch sử. Dữ liệu không cung cấp user/session hay thời điểm từng click.

Từ đó, thiết kế đề xuất chỉ dùng `type=link`; các type khác được thống kê rồi tách khỏi target. Đây là bài toán conditional on an observed internal-link transition, không dự đoán người đọc có tiếp tục đọc hay thoát trang. Không thể tính CTR triển khai thực tế khi thiếu impressions/exposure.

[README chính thức](https://dumps.wikimedia.org/other/clickstream/readme.html) ghi CC0. Danh sách ngôn ngữ trong README không đầy đủ so với một số release; phải dựa trên listing và nội dung file được chọn, không hardcode số ngôn ngữ.

| File đã thấy trong listing | Vai trò | Bytes nén |
|---|---|---:|
| [clickstream-eswiki-2018-01.tsv.gz](https://dumps.wikimedia.org/other/clickstream/2018-01/) | Train | 35,123,848 |
| [clickstream-eswiki-2018-02.tsv.gz](https://dumps.wikimedia.org/other/clickstream/2018-02/) | Train | 33,883,323 |
| [clickstream-eswiki-2018-03.tsv.gz](https://dumps.wikimedia.org/other/clickstream/2018-03/) | Train | 37,221,600 |
| [clickstream-eswiki-2018-04.tsv.gz](https://dumps.wikimedia.org/other/clickstream/2018-04/) | Validation | 37,817,594 |
| [clickstream-eswiki-2018-05.tsv.gz](https://dumps.wikimedia.org/other/clickstream/2018-05/) | Test | 39,037,289 |
| [clickstream-eswiki-2018-06.tsv.gz](https://dumps.wikimedia.org/other/clickstream/2018-06/) | P1 temporal robustness | 36,221,902 |

Năm file chính cộng **183,083,654 bytes**, khoảng 183.1 MB decimal. Số row, unique node, link pair, tổng click và dung lượng giải nén: **chưa đo**, không lấy thống kê English năm khác thay thế. Listing có thời điểm xuất bản sau tháng quan sát; benchmark tháng liền nhau không mô phỏng publication latency. Một deployment backtest phải dùng `available_at` và thêm gap, được mô tả trong [protocol](EXPERIMENT_DESIGN.md).

## 3. Graph độc lập: đã biết và chưa biết

[Zenodo record 2539424](https://zenodo.org/records/2539424) liệt kê `eswiki.wikilink_graph.2018-03-01.csv.gz`, khoảng **477.4 MB** nén, MD5 `9f56ab28f123837c1f998d313d676b09`; có file SHA512 riêng. File English cùng snapshot khoảng 2.4 GB. Không tải toàn bộ archive nhiều ngôn ngữ/năm.

[README của tác giả](https://zenodo.org/records/2539424/files/README.md?download=1) xác nhận file đuôi `.csv.gz` thực chất **tab-separated**, với `page_id_from`, `page_title_from`, `page_id_to`, `page_title_to`; title có dấu cách. License CC BY 4.0. Parser phải kiểm tra delimiter và header thực tế trước khi chạy.

[Bài WikiLinkGraphs, Table 3 và phần preprocessing](https://arxiv.org/html/1902.04298) báo cáo snapshot Spanish có **3,034,113 nodes, 38,348,163 edges**, English có **13,685,337 nodes, 163,380,007 edges**. Đây là số raw có redirect nodes, không phải số content articles sau xử lý. Graph được trích từ revision history, bỏ template-transcluded links; redirect được giải theo snapshot nhưng redirect nodes vẫn còn. Độ đầy đủ của page/title inventory và bảng `ResolvedRedirects` cần kiểm tra tại pilot.

Các hệ quả thiết kế:

- Gọi graph là **historical editorial-link graph**. Một cặp `type=link` không khớp graph không tự động là lỗi Clickstream: có thể do template, link mới, move, redirect hoặc extraction.
- Không thêm test edges để “sửa” coverage. Không dùng live Wikipedia API để canonicalize historical features.
- Không nhận diện redirect bằng heuristic `in_degree=0, out_degree=1`: bài thật cũng có thể có cấu trúc đó.
- Ưu tiên lấy bảng redirect/page cùng thời điểm từ tài liệu supporting data của tác giả; xác minh URL truy cập, schema, checksum, provenance trước khi dùng. **Chưa xác nhận được artifact phụ này trong phiên planning.**
- Nếu thiếu redirect metadata: giữ graph raw để traversal, chỉ nhận query/candidate qua phép khớp canonical title rõ ràng theo bảng đã khóa; ghi lại alias/ambiguous nodes. Không gọi đó là canonical article graph hoàn chỉnh. Nếu không thể bảo đảm candidate là bài hợp lệ, không vượt gate primary.
- Một edge list không chứng minh bao phủ các isolated articles. Node universe phải ghi rõ là endpoint inventory hay page inventory; báo cáo thiếu coverage tương ứng.

## 4. SQL/XML dump như phương án khác

Có thể dựng graph bằng `page`, `pagelinks`, `redirect`, và với schema mới có `linktarget`. `pl_from` là page ID nguồn; target ID cần join theo schema đúng release. Namespace nguồn/đích phải bằng 0, bỏ redlinks, giải redirect rồi deduplicate. [Manual:pagelinks](https://www.mediawiki.org/wiki/Manual:Pagelinks_table) và [Manual:linktarget](https://www.mediawiki.org/wiki/Manual:Linktarget_table) cho thấy schema đã thay đổi; không viết parser cố định dựa vào tutorial cũ.

SQL có lợi cho topology của rendered links; XML/wikitext đơn thuần không tự tái hiện template expansion. Reconstruction từ full history còn phải xử lý deleted pages và lịch sử đổi tên. Chưa xác minh được bộ dump SQL lịch sử đồng bộ 2018 đang tải được, nên **không chọn SQL/XML làm critical path**, không lấy dump hiện tại ghép với test 2018.

Nếu chuyển sang snapshot mới: chọn toàn bộ train/validation/test sau mốc graph phù hợp, xác minh lại file release, schema và download budget. Đổi dataset strategy phải xảy ra trước test freeze; không chọn strategy theo điểm test.

## 5. So sánh dữ liệu

| Tiêu chí | Clickstream eswiki + WLG (primary) | Clickstream enwiki + WLG | SQL/XML + Clickstream | Wikispeedia |
|---|---|---|---|---|
| Granularity | Count cặp theo tháng + graph tĩnh | Như primary | Như primary, tự trích graph | Path từng lượt chơi |
| Nodes/edges | Raw WLG 3,034,113 / 38,348,163; click graph chưa đo | Raw WLG 13,685,337 / 163,380,007 | Chưa chọn snapshot, chưa biết | 4,604 / 119,882 |
| Labels | Future observable `link` counts | Như primary | Như primary | Bước tiếp theo, completed/abandoned |
| Session/user | Không | Không | Clickstream vẫn không | Có paths; không tự suy ra user profile |
| Graph | Có, editorial links | Có, lớn hơn | Tùy dump/schema/extraction | Có graph đi kèm |
| Time | Monthly counts; snapshot 01/03/2018 | Như primary | Phải đồng bộ snapshot | Timestamp/path theo header cần đọc |
| Preprocessing | Title/redirect, censorship, temporal join | Tương tự, tốn tài nguyên hơn | Cao nhất; SQL joins hoặc revision parser | Thấp hơn; backtracking/termination |
| Storage đã biết | ~660.5 MB nén primary, chưa tính metadata | Graph ~2.4 GB; tháng 03 ~333.4 MB, không suy tổng | Chưa ước lượng do chưa chọn file | Gói paths+graph 9.5 MB |
| Memory | Sparse; xem budget dưới | Dễ vượt budget qua title joins/walks | Cần benchmark parser/join | Rất phù hợp laptop |
| Validity | Natural aggregate traffic, censoring; graph cũ/thiếu template | Tương tự, không tự tăng validity vì lớn | Tốt nếu timing và extraction đúng | Goal-directed game, selection bias |
| Reproducibility | URL + checksum + manifest + cố định parser | Như primary | Khó hơn nếu archive không còn | Artifact nhỏ, schema trong header |
| Project suitability | Khuyến nghị có gate | P2 khi đủ RAM/thời gian | Không ưu tiên trong 6–8 tuần | Fallback chắc về quy mô |

Số liệu Wikispeedia từ [SNAP](https://snap.stanford.edu/data/wikispeedia.html): 51,318 finished paths, 24,875 unfinished paths. Gameplay yêu cầu đi từ source đến target qua hyperlink, khác browsing tự nhiên.

## 6. Resource budget: tính toán, không phải benchmark

Môi trường thực sự đã kiểm tra: macOS Darwin arm64; Python 3.13.13; GitHub CLI 2.95.0; filesystem báo khoảng 576 GiB còn trống. Đọc RAM/CPU bằng `sysctl` bị chặn; **chưa biết RAM/CPU khả dụng**. Không có dependency project hay GPU requirement. Giả định lập kế hoạch: máy CPU, 16 GB RAM; nếu thực tế thấp hơn, giảm pilot.

Với `N=3,034,113`, `M=38,348,163` raw Spanish, CSR int32 indices + float32 values + int64 indptr cần:

`4M + 4M + 8(N+1) = 331,058,216 bytes ≈ 0.331 GB`.

Đây chỉ là **một** matrix, chưa có transpose, các matrix khác, buffers, title dictionary, Python overhead hay sort/joins. Float64 thay float32 tăng thêm `4M` bytes. Dùng dense float32 cần `4N²`, khoảng **36.8 TB**, không chấp nhận. Count aggregation dùng int64 để tránh overflow.

| Thành phần | Ước lượng theo công thức / giới hạn đề xuất | Quyết định |
|---|---|---|
| Raw download primary | 183.1 MB click + 477.4 MB graph ≈ 660.5 MB | Không download trong planning |
| Disk làm việc | Dự trù 10–20 GB, chưa đo; streaming không giữ nhiều bản text giải nén | Đo bytes thực, dừng nếu dự phóng >20 GB |
| RAM pipeline | Hard budget đề xuất 8 GB peak RSS trên máy 16 GB | Partitioned joins, giới hạn batch |
| PPR chính xác | Một source: `I × (M+N)` work; S sources nhân S | Không all-pairs; pilot timing trước |
| PPR score cache | `S×N` float64 rất lớn; 1,000 sources ~24.3 GB | Chỉ lưu candidate scores/residuals, giải tuần tự/batch nhỏ |
| Node2Vec full raw | Hai embedding tables d=64: `8Nd ≈ 1.55 GB`, chưa vocab/walks | Không đồng nghĩa fit dưới 8 GB |
| Walk corpus full | r=10, L=40 → ~1.21 tỷ tokens; tối thiểu int32 ~4.85 GB | Không chạy full Node2Vec mặc định |
| Node2Vec pilot | Cap 50k nodes, 1M edges; r=5, L=20 → ≤5M tokens | Train trên graph nhỏ cố định; mọi comparator cùng graph |

Không dự đoán “chạy mất X phút” khi chưa đo throughput. Pilot phải báo parse rows/s, RSS, PPR source-time theo degree, walk tokens/s và thời gian một epoch. Dùng công thức để dự phóng, thêm safety factor 2 cho runtime/memory; full batch vượt 8 giờ thì thu nhỏ số query hoặc bỏ P1, không giảm correctness âm thầm.

## 7. Pipeline dự kiến và manifest

1. **Ingest:** manifest URL, edition, period, content timestamp, release timestamp, fetched_at, license, remote checksum và local SHA256; byte counts; read-only raw.
2. **Validate schema:** UTF-8, đúng bốn cột, delimiter, header/comments, allowed type, n int64 >0; threshold audit chỉ sau khi xác nhận schema release. Quarantine row lỗi, không tự sửa n.
3. **Duplicate audit:** duplicate raw `(month,prev,curr,type)` là bất thường cần điều tra; không tự double-count. Nhiều row trở thành một pair sau canonicalization thì SUM theo mapping provenance. Across months: SUM các count **được công bố**, không ước lượng phần bị suppress.
4. **Title normalization:** giữ raw title; Unicode NFC, thống nhất spaces/underscores có test; không lowercase toàn bộ, không xóa dấu. URL decoding chỉ khi xác minh nguồn mã hóa; không decode lặp. Fragment chỉ strip khi đó là link target có fragment, không sửa title mù quáng.
5. **Redirect:** mapping theo historical cutoff, chain/cycle checks, log ambiguous mapping; giữ bảng nguồn và version. Không gọi current API để chữa test mismatches.
6. **Filtering:** pseudo-referrers `other-*`, non-main namespace theo metadata chứ không chỉ dấu `:`, self-loops theo policy chung loại khỏi task, redirect-only nodes theo metadata. Report row và click mass từng bước.
7. **Match:** one-to-one normalized titles → page IDs; bảng unmatched với reason. Không fuzzy match tự động. Label không khớp được ghi out-of-universe, không được tạo feature mới.
8. **Stable IDs:** sort `(edition,page_id)` từ snapshot/mapping được khóa, ánh xạ contiguous node_id; hash mapping. Không dùng title hash Python không ổn định.
9. **Graph artifacts:** deduplicated directed binary H; C raw behavior edges và C∩H; CSR, metadata dtype/shape, out-degree, dangling mask. Không lưu dense.
10. **Temporal partition:** giữ nguyên month; fit-only aggregation; validation/test labels trong partition riêng. Graph hash và node-map hash không đổi khi đọc test.
11. **Coverage ledger:** số nguồn, pair, click mass, matched nodes, matched links, excluded self-loops, out-of-candidate, failed model outputs.
12. **Save:** Parquet tables + sparse `.npz` + JSON/YAML manifest, transform versions, seeds, checksums, artifact lineage.

## 8. Sampling, pilot và fallback gate

Tiny graph: 6–8 nodes có directed cycle, hub, dangling node, redirect alias, self-loop, một hyperlink không có observed clicks và một test-only observed transition. Counts là synthetic, dán nhãn rõ.

Pilot thật: chọn source bằng hash seed từ **train + graph**; bắt đầu 100 queries, tăng 1,000 nếu tài nguyên cho phép. Không chọn query vì nó có nhiều test positives. Full graph có thể giữ cho PPR; chỉ giảm số query, không gọi query sampling là graph sampling.

Cho Node2Vec, dựng induced subgraph từ seed chọn trước test và bounded expansion trên H. Cap chỉ dựa vào resource/train/graph; giữ đủ outgoing candidates cho **core sources** hoặc báo boundary coverage. Tất cả M0–M6 trong bảng Node2Vec chạy cùng node set, edge set, candidates, queries. Report độ lệch degree/traffic và edge cut so với graph đầy đủ. Không dùng kết quả sample như ước lượng không chệch toàn Wikipedia.

**Gate hết tuần 1:**

- Có download URL/checksum, parser mẫu chạy đúng, graph timestamp trước validation/test.
- Không có mapping sai đã biết; ambiguous titles quarantined. Khuyến nghị yêu cầu ≥95% train/validation observed click mass khớp node; đây là ngưỡng chất lượng thiết kế, chưa phải kết quả.
- Candidate link coverage không có một ngưỡng phổ quát: nếu validation mass coverage <70% thì chỉ được tiếp tục với claim “within historical editorial-link candidates”, trình bày full denominator và xem xét fallback. Không sửa threshold sau test.
- Xác định được redirect policy, giải thích node universe và template omission.
- Pilot RSS/runtime trong budget. Nếu thất bại trong 3–5 ngày làm việc: chuyển Wikispeedia; hoặc giữ Clickstream behavior-only và **đổi research question**, không gọi click-derived graph là independent topology.

## 9. Protocol riêng cho Wikispeedia nếu cần

Đọc header trước khi viết parser. Replay back-button marker bằng stack, lưu actions; chỉ lấy forward hyperlink actions cho task link-following, báo tỷ lệ loại back/stop/timeout. Giữ cả completed và unfinished paths, stratify kết quả theo outcome. Không dùng goal làm feature trong source-only benchmark; goal-aware model là task khác.

Split theo timestamp **ở cấp whole path** nếu header xác nhận timestamp hợp lệ; chọn chronological 60/20/20 path blocks, không tách steps cùng path qua các tập. Nếu có định danh người chơi đáng tin cậy, báo overlap và thêm grouped sensitivity; không hứa user-disjoint trước khi xem schema. Không đủ time metadata thì dùng deterministic path-grouped split và gọi đúng là non-temporal fallback.

Graph static game là môi trường có sẵn cho mọi lượt. Labels lấy từ transitions trong held-out paths; bootstrap theo path/player nếu có, không coi từng step là mẫu độc lập. Đóng góp của fallback là comparative navigation study trong game; không kiểm tra được monthly censoring hay natural Wikipedia drift.

## 10. Những việc còn cần xác minh

| Vấn đề | Trạng thái | Bước xác minh |
|---|---|---|
| Schema/header thật các file 2018 | Documentation-only | Đọc bounded sample sau khi bắt đầu implementation |
| Count suppression đúng từng release | Theo docs, chưa audit file | Min/count histogram, upstream code/version nếu bất thường |
| Canonical nodes và redirect artifact | **Blocker có điều kiện** | Tải metadata nhỏ từ supporting archive, kiểm tra provenance |
| WLG vs Clickstream candidate coverage | Chưa biết | Join train/validation và coverage ledger |
| Số canonical node/edge | Chưa biết | Recount sau xử lý; không dùng raw node count làm article count |
| RAM/CPU thực và dependency wheels | Chưa biết | Environment smoke test; không giả định Python 3.13 tương thích mọi package |
| File còn tải được toàn vẹn | Listing có, chưa download | Checksum + gzip integrity |
| Fallback paths header | Chưa đọc | Small package inspection khi cần |
