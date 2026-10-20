# Wikipedia Navigation Mining

**Đã có core P0 chạy offline và 57 tests đạt. Chưa có benchmark trên Wikipedia thật.**

Tên đề xuất: **Topology-Aware Next-Article Ranking on Wikipedia: A Temporal Comparison of Click Frequency and Historical Hyperlink Structure**.

Dự án học phần nghiên cứu khi nào hyperlink topology bổ sung thông tin cho historical click frequency trong **source-conditioned next-article ranking**. Không tuyên bố user personalization hay session-aware prediction từ aggregate Clickstream.

## Chạy bản tham chiếu

Yêu cầu Python ≥3.11; đã kiểm tra bằng Python 3.13.13 trên macOS arm64. Core hiện tại chỉ dùng standard library, không cần GPU hoặc cài thư viện từ mạng. Chạy các lệnh sau tại thư mục gốc dự án:

```bash
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m wikinav doctor
PYTHONPATH=src .venv/bin/python -m wikinav validate-config
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m wikinav toy-run --output results/toy-smoke
```

`toy-run` yêu cầu thư mục output **chưa tồn tại**, tránh ghi đè một run cũ. Khi chạy lại, đổi thành `results/toy-smoke-02`. Fixtures hoàn toàn synthetic, gồm 6 nodes; lệnh này không tải dữ liệu hoặc đọc validation để tuning.

Đã có 9 scorers: Global Popularity, Local Markov, Backoff Markov, Uniform, In-degree, PPR-H, PPR-C, PPR trên `C ∩ H`, và score fusion. PPR dùng directed transitions, dangling → source và ghi convergence residual. Graph tham chiếu giới hạn 10.000 nodes/100.000 edges; đây chưa phải backend xử lý toàn bộ Wikipedia.

Mỗi run lưu `freeze.json`, `predictions.json`, `source_metrics.json`, `metrics.json`, `coverage.json`, `ppr_diagnostics.json` và `completion.json`. Train/graph/candidates/models được khóa và predictions được ghi **trước khi mở test labels**. Các artifacts đều ghi `data_kind=synthetic`, `benchmark_result=false`.

Các metrics gồm Recall@5/10/20, MRR@10, NDCG@10, massRecall và ExpectedRR, cùng macro/traffic-weighted aggregation, full/conditional denominators và candidate coverage. Không có labels quan sát được → `null`; có labels nhưng không có candidates → full metric bằng 0. Ngoài ra có paired bootstrap theo source trong Python API.

Audit một prefix Clickstream cục bộ:

```bash
PYTHONPATH=src .venv/bin/python -m wikinav audit-clickstream tests/fixtures/toy/2018-01.tsv --month 2018-01 --max-rows 3
```

Parser nhận TSV hoặc TSV.gz, kiểm tra 4 trường, type, count, duplicates và giới hạn dòng. Prefix audit không phải random sample, không xác nhận checksum/toàn vẹn toàn bộ file nếu chưa đọc hết. Ngưỡng count mặc định 11 phục vụ protocol đã chọn; release khác cần xác minh trước khi dùng.

Xem [trạng thái triển khai và việc còn lại](docs/IMPLEMENTATION_STATUS.md). Packaging qua `pip install` và các phiên bản Python khác chưa được kiểm chứng.

## Bộ tài liệu kế hoạch

| Tài liệu | Nội dung |
|---|---|
| [PROJECT_PLAN](docs/PROJECT_PLAN.md) | Executive assessment, 10 phần kế hoạch, research questions, scope, report/presentation/demo |
| [DATASET_FEASIBILITY](docs/DATASET_FEASIBILITY.md) | Nguồn đã xác minh, dataset decision, resource budget, preprocessing và blockers |
| [EXPERIMENT_DESIGN](docs/EXPERIMENT_DESIGN.md) | Formalization, models, temporal splits, candidates, metrics, tuning, ablations và leakage audit |
| [EDA_AND_ANALYSIS_PLAN](docs/EDA_AND_ANALYSIS_PLAN.md) | Figure inventory, EDA-to-decision mapping, error analysis và result tables |
| [IMPLEMENTATION_ROADMAP](docs/IMPLEMENTATION_ROADMAP.md) | Modules/interfaces, artifacts, dependency gate, tests, milestones 8 tuần |
| [LITERATURE_REVIEW](docs/LITERATURE_REVIEW.md) | Verified bibliography, literature matrix, positioning và baseline rationale |
| [RISKS_AND_DEFENSE](docs/RISKS_AND_DEFENSE.md) | Risk register, instructor feedback-to-action matrix, 25 defense questions |

## Quyết định chính

- Primary có điều kiện: **eswiki Clickstream tháng 01–05/2018 + WikiLinkGraphs 01/03/2018**; train 01–03, validation 04, test 05.
- Candidate setting chính: outgoing links trong historical editorial-link graph được khóa trước evaluation.
- Báo full observable denominator và conditional-candidate metrics cùng coverage; unobserved không đồng nghĩa zero-click.
- P0: strong popularity/Markov baselines, uniform/in-degree, PPR-H/PPR-C và score fusion. P1: fixed-support weighting, matrix fusion, Node2Vec H/W trên graph nhỏ chung, HITS và temporal robustness.
- Fallback: Wikispeedia, với scope đổi thành goal-directed game navigation.

**Chưa vượt dataset gate:** redirect/page metadata, schema thực tế, graph–click coverage và runtime/RAM cần được xác minh bằng pilot. Có file trong listing không đồng nghĩa đã kiểm tra toàn vẹn file hoặc hoàn tất matching.

Đọc [kế hoạch tổng thể](docs/PROJECT_PLAN.md) và [definition of done](docs/IMPLEMENTATION_ROADMAP.md). Các CLI trong tài liệu kế hoạch là thiết kế đích; chỉ các lệnh liệt kê ở README này đã được triển khai và kiểm tra.

Nguồn và facts được kiểm tra ngày **20/10/2026**; các giả định, ước lượng và điểm chưa xác minh được ghi riêng. Không có experimental improvement được khẳng định trước khi đo.
