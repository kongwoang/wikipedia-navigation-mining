# Kiến trúc triển khai và roadmap 8 tuần

**Roadmap thiết kế, cập nhật trạng thái 21/10/2026.** Một phần đã triển khai trong repository; các tên module/lệnh bên dưới vẫn là kiến trúc đích, không phải tất cả đều executable. [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md) phân biệt phần đã kiểm tra và phần chưa hoàn tất; bảo tồn core hiện có, không tạo scaffold thay thế.

## 1. Audit repository và môi trường

Audit ban đầu ngày 20/10/2026 (lịch sử, không phải trạng thái hiện tại):

- Workspace ban đầu trống, không `.git`, README, source, config, dependency lock hay dữ liệu.
- GitHub `kongwoang/wikipedia-navigation-mining` có default branch dự kiến `main`; API trả repository empty và branch list rỗng khi kiểm tra.
- macOS arm64, Python 3.13.13; GitHub CLI 2.95.0. `importlib.find_spec` không thấy Polars, Pandas, NumPy, SciPy, NetworkX, igraph, Gensim, pytest, matplotlib hoặc torch trong interpreter hiện tại.
- Filesystem báo ~576 GiB free; RAM/CPU query bị sandbox chặn, nên không ghi cấu hình phần cứng suy đoán.
- Shell truy cập GitHub lỗi DNS; GitHub connector đọc repository được nhưng thao tác tạo README bị từ chối **403 “Resource not accessible by integration”**. Chưa có remote commit được tạo trong phiên planning; local documents không đồng nghĩa một Git checkout hay push thành công. Cần kết nối GitHub có quyền ghi repository để publish.

Ngày 21/10, Git CLI đã truy cập và push được remote; local `main` đã đồng bộ commit `de87341` trước lần cập nhật tài liệu này. Máy có 19.327.352.832 bytes RAM (~18 GiB); `.venv` Python 3.13.13 chạy được 69 tests. Code thực tế dùng DuckDB/Parquet và SciPy CSR thay Polars; không cần chuyển backend chỉ để khớp sơ đồ đề xuất. Gensim chưa đạt real-data training gate dù toy tests pass. Không lấy tests pass làm bằng chứng benchmark hoàn thành.

Kế hoạch không cần GPU. Development dùng venv và dependency lock riêng; không thay global Python. Trong lượt hoàn thiện planning này không tải thêm datasets hoặc chạy benchmark.

## 2. Repository structure đề xuất

```text
wikipedia-navigation-mining/
├── README.md
├── pyproject.toml
├── dependency lock (chọn một: uv.lock hoặc equivalent)
├── .gitignore
├── configs/
│   ├── dataset/eswiki_2018.yaml
│   ├── dataset/wikispeedia.yaml
│   ├── models/
│   └── experiments/{pilot,primary,ablation}.yaml
├── data/
│   ├── raw/                 # gitignored, immutable
│   ├── interim/             # gitignored, normalized partitions
│   ├── processed/           # gitignored, tables/CSR
│   └── manifests/           # nhỏ, versioned, không chứa credentials
├── src/wikinav/
│   ├── data/                # ingest/schema/titles/redirects/splits
│   ├── graph/               # build/transitions/candidates/sampling
│   ├── models/              # popularity/markov/ppr/node2vec/hybrid
│   ├── evaluation/          # relevance/metrics/runner/bootstrap/audit
│   ├── analysis/            # eda/plots/cases/tables
│   ├── utils/               # config/seeds/hashing/logging
│   └── cli.py
├── scripts/                 # orchestration mỏng, không duplicate logic
├── tests/
│   ├── fixtures/
│   ├── unit/
│   └── integration/
├── notebooks/               # chỉ gọi package functions
├── experiments/             # config registry, freeze manifests
├── results/
│   ├── tables/
│   ├── figures/
│   └── predictions/         # lớn: gitignored
├── docs/                    # 7 planning documents
└── reports/                 # report sources/demo guide
```

Chỉ tạo thư mục khi có việc tương ứng. Không cần empty scaffold hàng chục files ngay đầu. README phải phân biệt planning assets với code đã chạy.

## 3. Tool decisions và dependency gate

| Component | Lựa chọn | Vì sao / điều kiện |
|---|---|---|
| Ingestion/aggregation | Polars lazy/chunked + Python stdlib gzip | Giảm in-memory strings; test streaming behavior của pinned version |
| Small summaries | Pandas optional | Chỉ khi tiện plotting, không thêm vào critical path nếu Polars đủ |
| Storage | Parquet, schema + partition month/type | Columnar scan, count dtype rõ, read only columns cần |
| Sparse graph/math | NumPy + SciPy CSR/CSC | Không dense adjacency; float64 reference solver |
| Small graph oracle | NetworkX | Toy/test và visual subgraph, tránh full graph object overhead |
| Full components/stats | SciPy csgraph; igraph optional | Benchmark conversion/memory trước khi chọn |
| Node2Vec | Audited sampler + Gensim Word2Vec | Directed/weighted semantics rõ; không dùng thư viện mặc định symmetrize |
| Plotting | matplotlib + seaborn optional | Scientific figures và tables export |
| Tests/config | pytest, YAML parser hoặc TOML stdlib | Ít infrastructure, config validation |
| Experiment log | JSONL + immutable run directories | Đủ cho course project; không cần tracking server |
| Demo | Streamlit P1 hoặc CLI/notebook P0 | Đọc real artifacts; không production web deployment |
| PyTorch | Không bắt buộc | Không có neural architecture cần đến nó |

Chọn Python 3.11/3.12 nếu hệ dependency chưa hỗ trợ ổn định interpreter 3.13 hiện có; **chưa pin một version package chưa được smoke-test**. Khi development: resolve một environment, lock transitive deps, chạy toy PPR và one-epoch SGNS test nếu có Node2Vec. Kiểm tra license khi port code reference. Ghi BLAS/thread versions để giải thích floating-point variability.

Các technical APIs cần kiểm tra theo official docs/version pin: [SciPy sparse](https://docs.scipy.org/doc/scipy/reference/sparse.html), [Polars](https://docs.pola.rs/), [NetworkX pagerank](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html), [Gensim Word2Vec](https://radimrehurek.com/gensim/models/word2vec.html). Đường dẫn là đầu mối verification khi implement; không thay thế benchmark thực tế.

## 4. Contracts giữa các module

### 4.1 Data artifacts

| Artifact | Schema chính | Invariant |
|---|---|---|
| `nodes.parquet` | node_id, page_id, title_raw, title_canonical, snapshot, namespace, is_redirect/source_of_flag | node_id contiguous, page_id unique theo edition |
| `mapping_audit.parquet` | raw_title, mapped_id, rule, mapping_version, status | Không ambiguous auto-merge |
| `clicks/month=...` | source_id/label-key, target_id/label-key, type, count int64, observed bool | Count tổng hợp đúng; unmapped labels giữ ledger |
| `hyperlinks.parquet` | source_id,target_id,snapshot_id | Directed, unique edge; no inferred test edges |
| `graph_H.npz` | binary CSR | shape=(N,N), indices sorted |
| `graph_C_train.npz` | count CSR | Train only, nonnegative int64 |
| `query_registry.parquet` | source_id, stratum, inclusion_probability, selection_seed | Hash trước held-out labels |
| `candidate_registry` | source_id, candidate offsets/IDs, hash | Same candidates mọi models |
| `coverage_ledger.parquet` | stage, reason, source/pair/mass totals | Reconcile raw→filtered, exclusions không chồng lấn |
| `predictions.parquet` | run_id, split, source_id,target_id,rank,score,model,status | Candidate restriction, no duplicate targets |
| `source_metrics.parquet` | run_id,source_id,metric,estimand,value,label_mass | Recompute aggregate không cần rerun model |

Label-key ngoài V tồn tại chỉ trong evaluator/coverage ledger; không append node IDs vào model vì đọc test. Missing external title giữ normalized raw key đủ phân biệt, không fuzzy-canonicalize bằng tương lai.

### 4.2 Model interface

```python
# Pseudocode interface, chưa implement
model.fit(train: TrainBundle, graph: GraphBundle | None, config: ModelConfig)
model.score(source_id: int, candidates: CandidateView) -> ScoreVector
model.recommend(source_id: int, k: int, candidates: CandidateView) -> RankedList
model.save(artifact_dir)
model.load(artifact_dir)
```

TrainBundle không có validation/test labels. GraphBundle có snapshot/hash/ID map/support/dangling policy. CandidateView không cho model tự đổi candidates. ScoreVector cùng thứ tự với candidates, finite values hoặc documented sentinel; RankedList có score/tie rule/status.

`fit` có thể chỉ build counts/cache matrices đối với nonparametric model; không giả có optimizer. PPR `score` có thể lazy-compute source vector rồi chỉ cache candidates. `score_batch` optional với iterator, không trả dense S×N. Hybrid đọc component scores đã normalize chung C.

Evaluator sở hữu labels và aggregation; model không đọc file paths test. Tách `prepare/train/tune/freeze/predict/evaluate/analyze` thành stages. `predict` có thể chạy trước mở test labels, giúp audit mạnh hơn.

### 4.3 Config và run manifest

Dataset config: edition, URLs, periods, timestamps, expected schema, mapping policy, graph support, filtering, self-loop, query sample, budget.

Model config: formula variant, δ/μ/η/λ, solver precision, Node2Vec knobs, fallback, tie seed. Experiment config: train/val/test, candidate setting, metrics/gains, aggregation, ablation controls, seeds, max trials.

Run manifest: run_id, code commit, config digest, package lock hash, hardware/OS, start/end, input/output hashes, seed list, peak RSS, wall-time, status/failure reason. Artifacts immutable; overwrite tạo version/run mới. Logs không cần usernames/credentials và không chứa raw user data.

CLI dự kiến: `wikinav ingest`, `prepare`, `audit`, `eda`, `fit`, `tune`, `freeze`, `predict`, `evaluate`, `report`. Tên lệnh chỉ trở thành README instructions sau khi implement và test.

## 5. Test plan với toy answers

Không có cần neural training test cho popularity/PPR. Các tests ở đây nhằm phát hiện lỗi direction, denominator, leakage và silent filtering.

| Test | Fixture / expected result | Lỗi ngăn chặn |
|---|---|---|
| Direction | A→B tồn tại, B→A không; reachable/candidates khác nhau | Accidental undirected conversion |
| Aggregation | Hai canonicalized records A→B counts 3 và 4 →7; duplicate raw rows bị flag trước SUM | Double counting và alias collisions |
| Normalization | A→B=3,A→C=1 → .75,.25; empty row tagged dangling | Row/column nhầm, integer division |
| Known PPR | Hai-cycle A↔B, restart A, δ=.5 → r_A=2/3,r_B=1/3 | Sai damping/restart/direction |
| Dangling | A→B, B không outgoing; restart A | Mass conservation, no NaN |
| Residual | Reference nghiệm nhỏ bằng linear solve vs iterative | Stop criterion không đúng |
| Candidate restrictions | Scores cao cho D ngoài C vẫn không được return | Candidate mismatch |
| Ties | Equal scores + fixed SHA seed → cùng ranking dù row order thay | File-order/title bias |
| Metrics oracle | Fixture bên dưới | Sai MRR/IDCG/weighted metrics |
| Empty labels | Source no observable labels → NA + ledger, không âm thầm score=1 | Metric inflation |
| Empty candidates | Future label có nhưng C empty → full metric0, conditional NA | Coverage bị ẩn |
| K boundaries | Candidate count<K, K=1/10/20; no duplicate/padding | Denominator/minK errors |
| Temporal integrity | Inject tháng05 vào train → audit fail | Future count leakage |
| Artifact lineage | Shuffle/replace test labels không đổi train/H/query hash | Indirect test-based graph/sample |
| Graph independence | Build_H không có click partition dependency | Click-derived H |
| Redirect | Chain, cycle, ambiguous names, spaces/Unicode | Incorrect collapse/future resolver |
| M6 endpoints | λ=1 matches M1B order, λ=0 matches M3 order | Fusion normalization |
| Matrix endpoints | λ=0 H; λ=1 click-H with documented fallback | Gọi nhầm pure behavior |
| Node2Vec direction/weights | Tiny asymmetric graph, analytical next-step probabilities; statistical tolerance | Backend symmetrization/ignored weights |
| Reproducibility | Deterministic models exact hash; stochastic seed/threads controlled + tolerance | False bitwise reproducibility |

**Metric fixture độc lập với real-data suppression:** C(A)={B,C,E}, ranking=[C,B,E], future counts B=3,D=1. D outside C.

- Recall_all@2=1/2; binary RR@2=1/2.
- MassRecall_all@2=3/4; ExpectedRR_all@2=(3/4)/2=3/8.
- Gain log2(1+y): g(B)=2,g(D)=1.
- DCG_all@2=2/log2(3); IDCG_all@2=2+1/log2(3).
- NDCG_all@2=`[2/log2(3)]/[2+1/log2(3)]`; conditional NDCG_C@2=`1/log2(3)`.
- Pair candidate coverage=1/2; mass candidate coverage=3/4.

Count 1/3 ở fixture là synthetic, không qua production threshold assertion. Test phải tách raw ingestion contract với metric unit inputs.

Integration smoke: tiny raw TSV → canonical mapping → H/C → M0/M1/M3/M6 → predictions → metrics/table → identical rerun. Thêm một malformed row, duplicate raw row, unmapped future target để kiểm tra failure/ledger. Không tải full data trong CI; real-data pilot manual có manifest.

## 6. Thứ tự triển khai bắt buộc

1. Viết task/config schemas và toy evaluation oracle.
2. Ingestion/schema/mapping/coverage; xác minh H độc lập.
3. Candidate provider, temporal split, query registry.
4. Metrics, aggregation và leakage audit.
5. M0/M1/M1B/M2/M2D.
6. PPR reference rồi sparse production solver, M4C/M4C∩H.
7. M6B + cached tuning; validation curves và freeze.
8. Test run P0, ablation/error analysis; không chờ Node2Vec để có complete baseline project.
9. P1 M4H/M6A và Node2Vec/HITS khi resource gate cho phép; scope này phải quyết định trước final test comparison.
10. Automated report tables/demo và clean rerun.

Trong thực tế, quyết định có P1 ở tuần4; nếu chưa chọn thì P0 freeze tuần5. Không nhìn P0 test rồi thêm P1 chỉ vì muốn thắng, trừ khi ghi exploratory và dùng holdout mới.

## 7. Milestones: tasks, dependencies, effort, risks, done

Effort dưới đây là **person-hours ước lượng**, không measured runtime. Target 8 tuần, khoảng 112–144 giờ core; P1 có thể cần thêm 20–30 giờ hoặc giảm breadth. Nếu chỉ có 6 tuần: giữ P0 và gộp report/demo, cắt P1 trước khi cắt validation/error analysis.

| Milestone / time | Goal & implementation tasks | Dependencies | Outputs | Acceptance / definition of done | Effort | Risks / fallback |
|---|---|---|---|---|---:|---|
| M1 tuần1, P0 | Finalize task; verify metadata/samples/redirects; environment; resource pilot plan | Không | Protocol v1, data manifest, gate memo | Snapshot and schema understood; redirect policy defensible; dataset go/no-go signed in log | 12–16h | Missing metadata → Wikispeedia; không kéo dài quá tuần1 |
| M2 tuần2, P0 | Ingest, normalize, map IDs, graph/splits, coverage; EDA E01–E12 core | M1 | Parquet/CSR, tests, attrition/EDA tables | Counts reconcile, graph hash independent, no future features; RSS within gate | 18–22h | String joins OOM → partition; low coverage → narrowed claim/fallback |
| M3 tuần3, P0 | Candidates, all metrics, M0–M2D, validation tuner | M2 và toy oracle | Baseline validation table, source metrics | Hand-calculated tests pass; same candidates/Q; strong Markov tuned | 14–18h | Metric bug → dừng graph experiments để sửa |
| M4 tuần4, P0/P1 | Exact toy PPR, sparse H/C solvers, residual/latency; embedding pilot gate | M3 | PPR artifacts/diagnostics; P1 decision | Convergence verified; runtime projected; no dense all-pairs; M5 support audited nếu nhận | 16–20h | Expensive PPR → fewer preselected queries/validated approximation |
| M5 tuần5, P0/P1 | M6B fusion, λ search; optional M4H/M6A; lock test manifest | M4 | Validation sensitivity, freeze.json | Endpoints exact, normalization fixed, configs/seeds preregistered | 12–16h | Weak hybrid → retain endpoint, không test-tune |
| M6 tuần6, P0/P1 | Core ablations, history/sparsity, primary test, bootstrap; P1 temporal/embeddings | M5 freeze | Main/conditional/paired tables, uncertainty | No audit failure; common Q; all planned P0 contrasts; omissions explained | 16–20h | Too many runs → cache/fewer P1, không bỏ negative runs |
| M7 tuần7, P0 | Error cases, evidence-to-RQ map, report figures/limitations | M6 | Report draft, 6–8 cases | Claims supported, failures analyzed, no false novelty/personalization | 14–18h | Result không đẹp → negative result discussion có evidence |
| M8 tuần8, P0 | Clean setup/rerun, README, real model demo, defense rehearsal | M7 | Reproducibility bundle, presentation/demo | Fresh environment reproduces main table within declared tolerance; 20 Q&A rehearsed | 10–14h | Dependency/drift → lock/cache checksums; demo offline artifacts thật |

Tổng theo bảng: 112–144h. Với P1, chọn ngân sách thực tế sau M1/M4; không cam kết “full Wikipedia Node2Vec” trong số giờ trên.

## 8. Scope gates

**P0 essential:** correctness, data validity, basic EDA, strong baselines, H/C PPR, score hybrid, five required ranking metrics, coverage, core A1–A4/A6–A8, uncertainty, cases/report/demo.

**P1 recommended:** fixed-support weighted H, matrix fusion, HITS-global, Node2Vec H/W on shared small graph, normalization sensitivity, one extra temporal window. A5 chỉ hoàn thành khi cả M5H và M5W có; nếu bỏ Node2Vec, báo scope reduction rõ.

**P2 optional:** CycleRank, full English, larger candidate universe, sequence-aware task, LTR. Không nằm trên critical path; không cài infra để chuẩn bị cho chúng.

## 9. Reproducibility definition of done

- Fresh checkout + environment lock tạo được toy pipeline và pilot với documented commands.
- Dataset URLs/checksums/license, transformation hashes và split periods lưu đủ.
- Không hardcoded absolute filesystem paths; project root/data root từ config/env.
- No raw huge data, credentials hoặc arbitrary generated binaries trong Git.
- Main results tạo tự động từ predictions; report tables không manual edits.
- Deterministic model result order reproducible; floating precision/threads/seeds được ghi.
- Empty/missing/nonconverged samples hiện trong ledger, không biến mất.
- README phân biệt primary/fallback, retrospective benchmark/deployment, full/subgraph results.
- Test labels không tồn tại trong model inputs; leakage audit pass.
- Artifact sizes/costs measured được thay cho assumptions ở planning.
