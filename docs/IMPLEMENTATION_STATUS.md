# Trạng thái triển khai — 20/10/2026

## 1. Phạm vi đã hoàn thành

Đã triển khai **nền tảng correctness của P0**, với một workflow synthetic từ raw TSV đến predictions, ranking metrics và manifests. Chưa hoàn thành M1 dataset gate, pipeline Wikipedia thật hoặc toàn bộ P0 của đề tài. Bảy tài liệu kế hoạch vẫn là thiết kế đích, không phải mô tả tất cả chức năng hiện có.

| Thành phần | Hiện trạng | Giới hạn |
|---|---|---|
| Protocol/config | TOML; kiểm tra train < validation < test, snapshot/mapping ≤ cutoff, fingerprint | Ngày mapping trong config là yêu cầu, chưa là bằng chứng đã có historical mapping |
| Clickstream parser | UTF-8 TSV/TSV.gz, 4 trường, types, count int64, ngưỡng mặc định 11, line-size cap | Chưa audit file eswiki thật; không suy từ synthetic rằng schema release đã xác nhận |
| Prefix audit | Count/type summary, duplicates, scope, EOF/gzip status | Tối đa 100.000 dòng; có thể đọc thêm 1 record để xác định truncation; không representative |
| Normalization | Unicode NFC, underscore → space, giữ case/accents/literal `%`/`#` | Không phải redirect resolver; không tự URL-decode hoặc heuristic merge |
| Training bundle | Loại non-link/pseudo/unmapped/self-loops, ledger rows/mass, aggregate aliases/tháng, immutable counts | Nhận mapping lịch sử từ bên ngoài; tối đa 100.000 records |
| Hyperlink graph | Directed, immutable nodes/edges, provenance hash, candidates cố định, self-loop rejection | Reference graph ≤10.000 nodes/100.000 edges; chưa có WLG ingestion |
| Models | 9 scorers, shared ranking/tie policy, hyperparameter fingerprints | Config cố định cho correctness; chưa validation search |
| Metrics | Full/conditional Recall, MRR, log-gain NDCG, massRecall, ExpectedRR; macro/weighted; coverage | Observable-label metrics; không diễn giải missing là zero |
| Statistical API | Paired source bootstrap với CI percentile | Chưa wiring thành experiment CLI; source independence chỉ là approximation |
| Reproducibility | Input/config/code/model/candidate hashes; exclusive output; completion marker | Không thay thế dependency lock cho backend tương lai |
| Tests | 57 unit/integration tests đạt | Chưa CI remote; chưa cross-version/cross-platform |

## 2. Models và hành vi cần biết

| ID | Scoring/transition input | Hành vi |
|---|---|---|
| M0 | Global training inbound counts | Score chỉ trên candidates chung |
| M1 | Local training counts/total outgoing observed counts | Nếu không có eligible observed destination, backoff về M0; không thêm pseudo-click |
| M1B | Local counts + Dirichlet prior | `mu`, `eta`; prior phối uniform và global popularity có epsilon=1 |
| M2 | Candidate set | Uniform; tie bằng SHA256(seed, source, target) |
| M2D | In-degree của H | Không sử dụng click weights |
| M3 | Unweighted H | Source-seeded PPR, candidate filtering sau propagation |
| M4C | Training click graph C trên frozen V | Behavior-only transitions; hỗ trợ cạnh C ngoài H khi propagation |
| M4CH | C ∩ H | Control về support; thiếu observed click không được xem là measured zero |
| M6B | M1B + M3 | L1-normalize topology trên candidates rồi convex fusion; λ=1 là M1B, λ=0 là PPR order |

`fit(train, graph)` nhận `TrainBundle`, `score(source, candidates)` trả mapping target → finite score. `recommend(source, candidates, k, seed)` dùng cùng ranking helper. Caller phải truyền candidate set từ frozen graph; pipeline thực hiện điều này và evaluator từ chối prediction ngoài set.

PPR dùng power iteration trên dictionary sparse để làm **reference oracle**. Với damping `d`, trả vector khi absolute fixed-point L1 residual ≤ tolerance và ghi bound `residual / (1-d)`. Không dùng default tolerance nhân với số nodes. Dangling mass trở về source. Nếu hết iteration budget, solver báo `ConvergenceError`; runner ghi rõ fallback uniform và số query bị fallback, không âm thầm coi là solver thành công.

PPR reference mỗi source cần khoảng `O(I·(|V|+|E|))` phép tính; implementation còn có sorting overhead. Cache chỉ giữ candidate scores và diagnostics theo query, không giữ bảng dense source × mọi node. Giới hạn kích thước bảo vệ smoke/reference run, không phải cam kết thời gian chạy ở giới hạn tối đa.

## 3. Bằng chứng kiểm tra

Các lệnh đã chạy thành công:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests
PYTHONPATH=src .venv/bin/python -m wikinav toy-run --output results/toy-smoke
PYTHONPATH=src .venv/bin/python -m wikinav audit-clickstream tests/fixtures/toy/2018-01.tsv --month 2018-01 --max-rows 3
```

- **57 tests đạt** trên Python 3.13.13, macOS arm64, cả interpreter sẵn có và virtual environment riêng không cài dependencies.
- PPR được đối chiếu nghiệm analytic của two-cycle và directed chain có dangling node; residual được tính lại từ vector trả về.
- Metrics được kiểm tra bằng ví dụ tính tay, perfect ranking, randomized boundedness, out-of-candidate positives, empty candidate set và no-label cases.
- Integration thay test labels nhưng giữ nguyên train/H/config: `freeze.json` và `predictions.json` không đổi.
- Instrumented read kiểm tra `freeze.json` và `predictions.json` đã tồn tại trước lần đầu đọc test file.
- Hai lần chạy cùng input cho các artifacts deterministic giống nhau. `completion.json` có timestamp/timing riêng nên không yêu cầu byte-identical.
- Gzip bị cắt, raw duplicate, count overflow, malformed mapping, future snapshot, held-out rows trong fit, invalid ranking và overwrite output đều bị từ chối.

Smoke run ghi nhận **9 models, 6 query sources**. Fixture có 5 sources với future labels và 4 sources với eligible labels; 8 observed positive pairs, trong đó 5 pairs thuộc candidates; tổng label mass 119, eligible mass 72. Đây là giá trị **được thiết kế trong dữ liệu tổng hợp để kiểm thử denominator/coverage**, không phải thống kê Wikipedia và không cho phép kết luận model nào tốt hơn.

Artifacts cục bộ nằm ở `results/toy-smoke/` và bị `.gitignore` loại khỏi Git. Không cần commit output: fixtures, config và code đủ tái tạo run.

| Artifact | Nội dung kiểm chứng |
|---|---|
| `freeze.json` | Protocol, input/code/config/model hashes, queries, candidate hash, fixed settings |
| `predictions.json` | Rankings, candidate scores, status và fallback reason trước khi đọc test |
| `source_metrics.json` | Từng source, full/conditional metrics, labels/candidate counts và mass |
| `metrics.json` | Aggregation và coverage của từng model; synthetic flag |
| `coverage.json` | Training attrition ledger; held-out eligibility/out-of-universe ledger |
| `ppr_diagnostics.json` | Iterations, fixed-point residual, residual curve và error bound |
| `completion.json` | Run thành công, môi trường, elapsed time, test hash, output checksums |

## 4. Điều chỉnh kiến trúc so với kế hoạch

Khi triển khai reference layer, môi trường có Python nhưng chưa có NumPy/SciPy/Polars/pytest/Gensim; shell lúc đó không resolve được host tải dữ liệu. Vì vậy dùng standard library và `unittest` để có thể chạy, kiểm tra và review ngay.

Đây là quyết định triển khai theo giai đoạn:

1. Giữ mathematical contracts, candidate policy và metric oracles độc lập backend.
2. Thêm Polars/Parquet ingestion và SciPy CSR sau khi dependency/resource gate đạt.
3. Đối chiếu sparse backend với reference trên cùng toy graphs trước benchmark thật.
4. Khóa versions sau khi cài và test thành công; chưa tạo lockfile chứa version chưa kiểm tra.

TOML thay YAML ở core để đọc bằng `tomllib` có sẵn từ Python 3.11. Các interfaces và nội dung protocol không đổi. `pyproject.toml` khai báo package và console entry point; workflow đã kiểm tra dùng `PYTHONPATH=src`. Build/editable installation qua setuptools chưa được kiểm tra.

Các file chính:

```text
configs/eswiki_2018.toml
src/wikinav/
  cli.py           doctor, validate-config, audit-clickstream, toy-run
  config.py        temporal protocol và hashes
  data.py          parser, normalization, bounded training bundle
  graph.py         directed graph, candidates, transition rows
  models.py        reference scorers và PPR
  ranking.py       candidate restrictions và deterministic ties
  evaluation.py    metrics, aggregation, paired bootstrap
  pipeline.py      synthetic workflow và artifact freeze
  utils.py         canonical serialization/checksums/exclusive writes
tests/test_core.py
tests/fixtures/toy/
```

## 5. Blockers và thứ tự làm tiếp

| Ưu tiên | Việc tiếp theo | Điều kiện hoàn thành |
|---|---|---|
| P0 | Xác minh historical page/redirect inventory cho graph 2018-03-01 | Nguồn, timestamp, checksum, namespace/redirect semantics đủ để bảo vệ canonical join; nếu không có, chốt fallback theo kế hoạch |
| P0 | Audit real Clickstream và WikiLinkGraphs bằng mẫu giới hạn | Schema/header/delimiter/type/count được kiểm tra từ file; lưu manifest, không dùng prefix để ước lượng quality toàn graph |
| P0 | Thiết lập scalable dependencies và resource pilot | Lock versions thật; streaming/Parquet/CSR; đo RSS/time; đối chiếu reference |
| P0 | Canonical mapping + real-data pilot coverage/EDA | Ledger reconciliation, graph–click edge match, unobserved semantics, same candidates; chốt dataset go/no-go |
| P0 | Validation tuner và frozen experiment runner | Chỉ đọc train/validation khi chọn knobs; tự sinh sensitivity/diagnostic tables; khóa trước test thật |

Không tải full datasets, training Node2Vec hoặc chạy grid search trước các bước trên. Graph snapshot và node inventory phải độc lập held-out click transitions.

### Tình trạng truy cập

- Phiên ban đầu gặp lỗi DNS qua shell và lỗi `403 Resource not accessible by integration` khi ghi qua GitHub integration.
- Sau khi môi trường được cấp network access, kiểm tra lại ngày 20/10/2026 bằng Git CLI đã truy cập được `kongwoang/wikipedia-navigation-mining`. Remote chưa có refs tại lần kiểm tra trước initial commit. Sử dụng Git CLI để quản lý và push repository.
- Chưa tải/cài dependency từ mạng, chưa có real-data pilot. Kết nối GitHub thành công không xác nhận nguồn dữ liệu hoặc historical mapping đã truy cập/kiểm chứng được.
- Smoke run được tạo trước initial Git commit nên manifest dùng code-content hash. Khi bổ sung experiment runner thật, ghi cả commit SHA và dirty-worktree status bên cạnh content hash.

Dataset gate vẫn chưa hoàn tất. Không coi tests synthetic đạt là bằng chứng dữ liệu thật hoặc phương pháp thực nghiệm đã hợp lệ.
