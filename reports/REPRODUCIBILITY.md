# Tái lập và kiểm tra kết quả

## Kiểm tra nhanh không cần dữ liệu lớn

```bash
PYTHONPATH=src python3 -m wikinav.verify_bundle
PYTHONPATH=src python3 -m unittest discover -s tests -p test_core.py
open reports/generated/demo.html
```

Verifier dùng standard library, kiểm tra SHA256 của bundle và tính lại metrics từ candidate sets, frozen scores/rankings và future labels đi kèm demo. Đây là **re-evaluation của predictions**, không phải retraining từ raw datasets. HTML chạy offline; không có API key hoặc model server.

## Tái tạo từ raw data

Yêu cầu Python 3.13, C/C++ compiler (macOS Command Line Tools hoặc GCC/Clang trên Linux), `git`, `curl`; khoảng 1 GB raw download, nên dự trù 10–20 GB disk và máy RAM16–18 GB. DuckDB memory limit4GB không phải peak RSS toàn process. Không cần GPU.

```bash
sh scripts/reproduce.sh
```

Script tạo `.venv`, cài pinned dependencies, build patched Gensim, chạy tests, xác minh/tải data nếu thiếu, prepare graph rồi chạy validation/freeze/test và analysis/demo. Raw acquisition gồm sáu tháng Clickstream, graph và hai metadata artifacts; raw files không nằm trong Git. Existing files được kiểm tra bytes/upstream checksum nếu có và acquisition manifest. Không xóa dữ liệu hoặc overwrite completed experiments.

Default reproduction output là `results/reproduction/` và `reports/reproduced/`, tách khỏi published bundle. Muốn chạy một lần mới, chọn đường dẫn chưa tồn tại:

```bash
WIKINAV_RUN_DIR=results/reproduction-02 WIKINAV_REPORT_DIR=reports/reproduced-02 sh scripts/reproduce.sh
```

Same seed và workers1 giúp repeatability; không hứa bitwise identity giữa BLAS/compiler/OS. So config, sampling/graph/count hashes, selected settings, predictions/metrics trước khi so elapsed time. Bootstrap seed cố định. Preparation manifest chứa elapsed time nên SHA của cả manifest có thể khác dù artifact contents giống.

## Native dependency patch

`scripts/install_gensim_fix.py` build Gensim `4.4.0+wnm2` từ checksum-pinned upstream sdist. Hai BLAS dot pointer declarations đổi từ `except -1` sang `noexcept`; -1 là giá trị dot hợp lệ. Dùng typed SciPy Cython BLAS API để tránh raw-pointer ABI assumptions trên Linux/macOS. Có regression probe qua chính dispatch dùng training. Source distribution thiếu `fastss.pyx`, được bổ sung từ release-tag URL có SHA256 cố định; mọi Cython extension được regenerate với Cython3.1.2 để tương thích Python 3.13. Giữ nguyên LGPL notices, không commit wheel/binary.

Đây là local compatibility patch, không phải upstream release hoặc thay đổi thuật toán Node2Vec. Các source URLs/hash, build-tool versions và wheel fingerprint ở [build evidence](../docs/evidence/gensim-build-wnm2.json). Backend smoke trên graph thật chỉ đọc training data, ghi finite vectors/loss, không native warning. Không tái sử dụng cache của incomplete `study-v1`.

## Artifact lineage và thay đổi sau test

[RUN_PROTOCOL](../docs/RUN_PROTOCOL.md) khóa policy; `freeze.json` ghi code/config/data/dependency hashes và selected settings. Predictions hoàn thành trước evaluator đọc May/June. `completion.json` là marker của experiment, `bundle_manifest.json` là checksum của portable report bundle. Code của analysis/report có thể được sửa để trình bày hoặc sửa lỗi hiển thị; không đổi selected models/labels để tìm score tốt hơn.

Không gọi rerun cùng held-out set là một kiểm định độc lập. Nếu sửa thuật toán sau khi xem test, phải ghi exploratory hoặc dùng holdout mới. CI chỉ chạy tiny synthetic correctness checks; không tải real dataset hoặc xác nhận replication full benchmark.

## Bằng chứng thực thi của bản bàn giao

- Final model code: `9b1f28ba90e21591afb23ed65c5fd0a17f4195d2`. [Verification record](../docs/evidence/final-verification.json) so byte contents của tám algorithm files với commit và so signature/config/protocol/lock/native installer với freeze. Freeze ghi dirty tree trung thực; acquisition/docs có thay đổi trong khi model chạy.
- [Fresh preparation replay](../docs/evidence/preparation-replay.json): từ cùng pinned raw files sang thư mục mới, bốn Parquet hashes và full counters giống hệt. Đây không phải model retraining.
- [Measured runtime](../docs/evidence/final-runtime.json): final validation/test run245,32 s; maximum RSS~1,82GiB trên macOS arm64. Không gồm download/preparation/build/report.
- Full local suite72 tests không skip; core 57 tests dùng standard library. CI Linux ở model commit đã pass; latest CI status xem [Actions](https://github.com/kongwoang/wikipedia-navigation-mining/actions).
- Portable bundle re-evaluation:14 main models×200 queries×2months =5600 lượt.28 configurations được báo trong CSV; verifier không retrain hoặc tính lại mọi ablation từ raw.
- Raw acquisition hiện kiểm tra **pinned SHA256 cho cả chín files**, kể cả file đã tồn tại có đúng size. Không chỉ tin kích thước hoặc filename.

Muốn sinh lại Markdown tables/cases từ portable bundle:

```bash
python3 scripts/build_report_tables.py
```

Browser QA chưa thực hiện được do origin access bị từ chối; người trình bày cần mở offline HTML để rehearsal theo [presentation checklist](PRESENTATION.md). Data/rank/metric verification đã pass không thay thế visual/interaction QA.
