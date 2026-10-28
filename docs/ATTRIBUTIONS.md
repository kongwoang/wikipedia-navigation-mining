# Data và dependency attribution

## Data

- **Wikipedia Clickstream** — Wikimedia Foundation; Ellery Wulczyn và Dario Taraborelli. Aggregate public data theo CC0, theo [README chính thức](https://dumps.wikimedia.org/other/clickstream/readme.html). Dùng edition eswiki, Jan–Jun2018. Published counts không phải individual sessions, và không đầy đủ low-frequency traffic.
- **WikiLinkGraphs** — Cristian Consonni, David Laniado, Alberto Montresor. Snapshot eswiki01/03/2018 và supporting redirect/page artifacts. Dataset [Zenodo DOI 10.5281/zenodo.2539424](https://zenodo.org/records/2539424), CC BY4.0. Pipeline thay đổi dữ liệu bằng canonicalization, quarantine, deduplication và induced-subgraph sampling; không phân phối các transformations như raw graph nguyên bản.
- **Wikispeedia** — Robert West và Jure Leskovec, [SNAP dataset](https://snap.stanford.edu/data/wikispeedia.html). Chỉ là fallback trong kế hoạch; không dùng để tính kết quả benchmark này.

Raw archives không nằm trong Git. URLs, fingerprints và nguồn checksum nằm trong `docs/evidence/`; prepared/frozen manifests đi kèm report bundle. Title tiếng Tây Ban Nha giữ nguyên để đối chiếu nguồn, không tự dịch thành node ID khác.

## Software

Project dùng Python standard library, DuckDB, NumPy, SciPy, matplotlib và Gensim; versions trong `requirements-study.lock`. Các libraries được cài ngoài repository và giữ license của từng distribution. Không tái cấp phép dependency bằng license của project.

Gensim source thuộc LGPL2.1; installer giữ copyright/license notices, lấy source từ upstream với SHA256 và chỉ tạo local build trong `.cache/`. Source transformation được công khai trong `scripts/install_gensim_fix.py`: typed SciPy BLAS wrappers, exception declarations và regression probe. Không commit native wheel hoặc upstream source archive. Source link và hash đủ để kiểm tra đúng bản đã sửa; đây không phải official Gensim release.

Thuật toán/tham khảo học thuật được dẫn trong [LITERATURE_REVIEW](LITERATURE_REVIEW.md). Project không claim phát minh PPR, HITS, Node2Vec hoặc ý tưởng kết hợp click/graph.

## Live crawl / historical revision collection — 29/10/2026

MediaWiki Action API và canonical es.wikipedia.org HTML là nguồn tự thu thập, riêng với Clickstream. Article text theo license tại trang nguồn (thường CC BY-SA4.0), không tự gắn CC0. Raw captures lưu URL, revision ID, timestamp, SHA256; không publish article text/images trong repository. Processed text nếu redistribution cần giữ attribution và license phù hợp; xem [Wikimedia Content reuse](https://www.mediawiki.org/wiki/Wikimedia_APIs/Content_reuse). Pilot report chứa factual counts/provenance và source URLs.
