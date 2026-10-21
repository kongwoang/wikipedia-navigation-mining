# Trạng thái thực tế — 21/10/2026

## 1. Phân biệt planning và thực nghiệm

Bảy tài liệu planning đã có đầy đủ nội dung yêu cầu. Repository cũng đã có code, datasets cục bộ và một lần thử validation từ các lượt trước; không mô tả repository là rỗng hoặc chưa từng tải dữ liệu. **Chưa hoàn tất benchmark held-out, report kết quả thật hoặc demo đã kiểm chứng trên real predictions.**

Trong lượt hoàn thiện planning này: kiểm tra repository, đọc manifests đã có, chạy tiny tests, sửa tài liệu và push. Không tải thêm raw datasets, không mở test labels thật và không chạy lại expensive experiments.

## 2. Những gì có bằng chứng

| Thành phần | Trạng thái | Bằng chứng / giới hạn |
|---|---|---|
| Planning | Hoàn thiện | 7 docs, 10 phần master plan, feedback matrix, 25 defense questions |
| Core reference | Đã kiểm tra | 57 tests; directed graph, aggregation, PPR analytic oracle, ranking metrics, no-leakage, synthetic pipeline |
| Sparse data pipeline | Đã có code và preparation artifact | DuckDB/Parquet, historical redirects, train-only sampling, SciPy CSR; manifest đính kèm |
| Full test suite | 69 tests đạt ngày 21/10 | Python 3.13.13/macOS arm64; tiny synthetic data; không phải real benchmark |
| Historical mapping | Đã dựng lại từ raw event history | Supplied resolved targets không dùng trực tiếp; có dangling/title-move/extraction limitations |
| Real-data sample | Đã chuẩn bị | 200 queries; 8.094 nodes; 319.694 edges; không full-graph PPR |
| Validation | Đã chạy một phần, chưa benchmark-ready | `results/study-v1` có cache và validation audit; run chưa hoàn tất |
| Node2Vec | Chưa qua real-data gate | Native warning của Gensim; toy embedding tests pass không đủ |
| Held-out evaluation | Chưa có artifact hoàn chỉnh | Không có `freeze.json`, `test_results.json`, `completion.json` của real study-v1 ở lần kiểm tra này |
| Report/demo/CI | Chưa xác minh hoàn chỉnh | Có code/draft cục bộ, không tuyên bố real-model demo hoặc CI đã pass |
| Git publishing | Git CLI hoạt động | Remote main trước lượt này là `de87341`; dùng commit cập nhật docs tiếp theo |

## 3. Kiến trúc hiện có và môi trường

Core `src/wikinav/{config,data,graph,models,ranking,evaluation,pipeline,utils}.py` tách mathematical contracts và orchestration. Backend study có `sources.py`, `redirects.py`, `study_data.py`, `sparse_models.py`, `embeddings.py`, `experiment.py`, `analysis.py`. Không cần tái cấu trúc thành hàng chục package rỗng để khớp cây đề xuất trong roadmap.

- Python 3.13.13, macOS arm64; RAM ~18 GiB. Không yêu cầu GPU.
- Ingestion dùng DuckDB embedded thay Polars; không có database server.
- Config TOML đọc bằng `tomllib`; tests dùng `unittest`.
- Scientific environment cục bộ có NumPy 2.3.5, SciPy 1.16.3, Gensim 4.4.0, DuckDB 1.5.6. Lockfile đang có thay đổi thử nghiệm chưa được coi là production-ready.
- Packaging/editable install, cross-platform CI và clean full reproduction chưa được xác nhận.

Lệnh kiểm tra đã chạy trong lượt này:

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
```

Kết quả: `Ran 69 tests ... OK`. Test integration dùng raw fixtures tổng hợp; một số log in `validation NDCG=...` thuộc fixture, không phải benchmark Wikipedia. Không trích chúng vào report kết quả.

## 4. Các gate còn mở

### Backend Node2Vec

Lần thử study-v1 gặp `Exception ignored in: 'gensim.models.word2vec_inner.our_dot_float'` và bị dừng trước held-out evaluation. Local Gensim source có typedef BLAS dot dùng `except -1 nogil`; đó là đầu mối cần kiểm tra vì dot product có thể hợp lệ bằng -1. Chưa có patched build và regression test chứng minh nguyên nhân/fix hoàn chỉnh. Không gọi hạ NumPy/SciPy version là đã sửa lỗi.

Khi vào development: ưu tiên upstream fix hoặc audited patch có pinned source/hash/build instructions; kiểm tra negative-dot regression, finite vectors/loss, stderr và repeatability. Nếu không xử lý trong budget, loại **cả** M5H/M5W và A5 trước test, ghi lý do. P0 frequency/topology/PPR/fusion vẫn trả lời research question; không chuyển dataset chỉ vì optional embedding backend lỗi.

### Protocol/code consistency

- Config study dùng 200 stratified queries và shared induced graph; thay các con số pilot đề xuất trong kế hoạch, không suy rộng population average.
- Runner hiện chọn option đầu tiên khi validation metric bằng nhau; specification ban đầu đề xuất runtime rồi simplicity. Phải chốt policy và manifest trước test.
- Solver failure policy, convergence tolerance và history controls cần review cùng evaluator. Không tự loại failed sources.
- Validation audit có node mapping ledger nhưng chưa thay thế candidate pair/mass coverage table trên query sample.
- Giữ `study-v1` là incomplete diagnostic run; không dùng làm final benchmark, không trộn cache khi code/dependency signature khác. Run mới cần output mới và provenance.

### Trạng thái working tree khi bàn giao planning

Các thay đổi code/dependency từ lượt trước được giữ nguyên để không mất công việc: `.gitignore`, `requirements-study.lock`, `src/wikinav/analysis.py`, `src/wikinav/experiment.py`, `.github/`, `scripts/`, `src/wikinav/demo.py`. Chúng chưa được đưa vào commit tài liệu này và chưa được quảng bá là pipeline hoàn chỉnh. Git history đã có code nền ở `96fb16e` và `de87341`.

## 5. Năm việc tiếp theo khi chuyển sang development

1. **P0 — Review/freeze protocol:** đối chiếu spec/config/runner, ghi model-selection tie, candidate/failure rules, independent graph provenance; kiểm tra validation candidate coverage. Done: một protocol manifest không còn policy mâu thuẫn.
2. **P0/P1 — Chốt environment:** kiểm chứng sparse backend và giải quyết/loại Node2Vec theo gate; pin dependency và provenance. Done: tiny regression tests đạt và backend được chọn có smoke evidence phù hợp.
3. **P0 — Hoàn tất train/validation diagnostics:** EDA theo inventory, coverage/boundary tables, PPR residual, hyperparameter/history curves, timing/RSS. Done: mỗi model có rationale và resource budget; chưa đọc test để tuning.
4. **P0 — Freeze rồi evaluate một lần:** lưu config/code/data hashes và predictions trước khi evaluator mở May/June labels; xuất common-source metrics, full/conditional coverage, paired bootstrap. Done: completion manifest và tables tái lập được; run thất bại không trộn vào kết quả.
5. **P0 — Phân tích và bảo vệ:** viết report 17 sections, 6–8 systematic cases, limitations/negative results, presentation/demo đọc real artifacts; clean rerun. Done: claim–evidence review đạt, không có fabricated findings.

Hoàn thành planning không đồng nghĩa hoàn thành các bước development này. Các mốc 6–8 tuần trong roadmap là effort dự kiến, không phải lịch chạy đã diễn ra.
