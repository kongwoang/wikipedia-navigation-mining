# Data audit thực tế và protocol đã chốt

Audit thực hiện 20–21/10/2026, trước khi đọc validation/test labels cho study. Kết quả dưới đây thay thế các giả định tương ứng trong bản kế hoạch. Dataset vẫn là **Spanish Wikipedia Clickstream + historical editorial hyperlinks**, không cần fallback Wikispeedia.

Bằng chứng preparation được version-control tại [preparation manifest](evidence/preparation-study-v2.json) và [acquisition manifest](evidence/acquisition-eswiki-2018.json). Sau preparation, lần thử validation đã chạy một phần rồi dừng; [April audit](evidence/validation-april-2018.json) được lưu riêng. Không có final held-out benchmark. Mốc “trước validation/test” ở trên nói về quyết định preprocessing/sampling, không có nghĩa validation chưa từng được đọc.

## Các vấn đề thực sự tìm thấy

1. **Count threshold:** file Clickstream 2018-01..03 chứa `n=10`. Vì thế study dùng `minimum_published_count=10`; không giữ giả định `n>10` từ mô tả tổng quát. Core toy parser vẫn cho phép caller cấu hình threshold. Missing observations không là true negatives.
2. **Header:** graph `.csv.gz` thực tế có header và phân cách tab. Redirect history là CSV có quoting; parser chỉ định escape rõ ràng hoặc dùng `csv.reader`, không bỏ lỗi parse âm thầm.
3. **Raw duplicates:** mỗi training month có 4 duplicate-key groups, mỗi group 40 dòng. Trong tháng 01, target literal `????` xuất hiện ở các nhóm `Alfabeto_fenicio`, `Alfabeto`, `other-empty`, `other-internal`. Không tự suy ra title gốc hoặc cộng các dòng này. Policy khóa trước validation: quarantine **toàn bộ** duplicate raw key group, ghi row/mass ledger. Tháng 01/02/03 loại lần lượt 160 rows và 4.320/7.920/4.160 count mass trên mọi type; không diễn giải đó là số click thật bị mất chính xác.
4. **ResolvedRedirects không đủ tin cậy:** file tác giả cung cấp có 3.063.959 rows, chỉ 66 nonidentity positive targets và 37 dangling sentinels. `EEUU`, page ID 6333, revision 102860754, được giữ identity trong bảng; [nội dung revision lịch sử](https://es.wikipedia.org/w/index.php?title=EEUU&oldid=102860754&action=raw) cho thấy nó redirect đến `Estados Unidos`. Revision này chỉ dùng audit, không dùng live state để tạo features.
5. **Sửa từ raw history độc lập:** [Redirects history](https://cricca.disi.unitn.it/datasets/wikilinkgraphs-redirects/README.md) chứa event đúng của revision trên. Resolver mới lấy event có `(timestamp, revision_id)` lớn nhất không vượt `2018-03-01T00:00:00Z`; không tin thứ tự dòng, xử lý `#NOREDIRECT`, chuẩn hóa whitespace của redirect target, resolve chains, quarantine cycle/dangling/ambiguous. Dùng snapshot page inventory cho title→ID; không dùng clickstream để suy redirect.

Code tác giả tại [commit 1d38d3e, redirect_resolver.py](https://github.com/WikiLinkGraphs/wikipedia-graphsnapshot/blob/1d38d3e3191ef02199e0894157f0d16daaf3f73f/graphsnapshot/processors/redirect_resolver.py) có logic ghi trạng thái khi gặp event sau snapshot. Đây là một khả năng giải thích sai lệch; chưa chứng minh chính commit đó đã tạo file public. Không quy kết tất cả artifacts của tác giả sai từ một audit.

## Kết quả mapping và graph

| Đại lượng đo được | Giá trị |
|---|---:|
| Raw redirect events | 1.526.274 |
| Events sau cutoff bị loại | 292 |
| Latest states | 1.029.524 |
| Redirect nodes thuộc inventory | 986.492 |
| Redirect nodes giải được | 961.977 |
| Dangling pages quarantined | 24.515 |
| Mapping khác supplied resolved table | 986.434 |
| Canonical inventory sau sửa | 2.077.467 |
| Raw hyperlink edges | 38.348.163 |
| Canonical directed unique edges | 36.333.722 |
| Canonical training pairs Jan–Mar | 1.802.996 |
| Published training count mass được giữ | 246.733.682 |
| Training mass khớp H | 237.539.317 |

Redirect sources bị loại khỏi article graph; target redirects được map sang terminal page. Đồ thị vẫn chỉ chứa editorial links do WikiLinkGraphs trích, thiếu template-transcluded links. “Canonical inventory” nghĩa là inventory sau quy tắc lịch sử trên, không phải xác minh thủ công mọi trang là một content article hoàn chỉnh. Các limitations của history dump, title moves và extraction vẫn còn.

Node-match coverage trên training link mass vượt 99% ở cả ba tháng. H khớp khoảng 96,27% count mass đã canonicalize. Đây là kiểm tra training, không là kết quả future ranking.

## Sampling và resource gate

- Chọn trước validation: 50 sources mỗi nhóm training outgoing mass `{0, 1–99, 100–999, ≥1000}`, chỉ các source có full historical out-degree 5–500. Hash seed 2026; không chọn theo future labels.
- Query pool theo nhóm: 1.032.009 / 105.664 / 91.955 / 37.470. Mỗi nhóm sample 50; do đó macro average là **sample-conditional**, không ước lượng không chệch toàn eswiki.
- Lấy induced subgraph trên 200 queries và toàn bộ outgoing targets của chúng: **8.094 nodes, 319.694 edges**. Giữ toàn bộ historical outgoing candidates của query; các intermediate nodes mất boundary edges, nên PPR/Node2Vec là **sample-graph** methods.
- Các sampled nodes có tổng 1.037.139 outgoing edges trong H đầy đủ. Boundary loss phải được báo trong kết quả; không gọi subgraph PPR là full-graph PPR.
- Preparation thành công mất khoảng 27,8 giây trong lần đo này; chưa đo peak RSS của bước đó. Máy có 19.327.352.832 bytes RAM (~18 GiB). DuckDB giới hạn memory 4 GB; không dùng dense adjacency.
- Các lần preparation thất bại nằm trong ignored `data/interim/`; không có manifest thành công và không được dùng cho model.

## Những gì đã khóa trước test

[configs/study.toml](../configs/study.toml) xác định sampling, model grid, seeds, score/weighting ablations và temporal horizons. Train 01–03/2018; validation 04; test 05; fixed-model robustness 06. Không refit bằng validation. Node2Vec chọn knobs trên seed 17, rồi giữ knobs và báo seeds 29/43; không chọn best test seed. Đây là một giản lược so với lựa chọn trên mean nhiều validation seeds trong kế hoạch.

M0/Markov dùng global popularity từ full canonical training corpus. PPR-C và embeddings dùng training edges trong shared induced graph; graph methods không được truy cập label tương lai. History ablation giữ graph/query sample cố định nhưng tính lại local counts và global priors từ từng history window. Điều này đo hiệu ứng history trên mẫu đã khóa, không mô phỏng sample được chọn lại ở một cutoff cũ.

Các input checksums, sizes, licenses và URLs được ghi trong acquisition manifest; prepared artifact hashes, attrition ledger và config hash trong `data/processed/study-v2/manifest.json`. Runner khóa mọi predictions trước lần đầu đọc test labels; báo full và conditional denominators, không âm thầm bỏ future targets ngoài candidates.
