# Wikipedia Navigation Mining

**Bộ kế hoạch nghiên cứu đã hoàn thiện; chưa có benchmark held-out hoàn chỉnh.** Repository cũng chứa code nền và audit dữ liệu từ các lượt làm việc trước. Lượt cập nhật 21/10/2026 tập trung hoàn thiện planning, không chạy thêm benchmark hoặc tải dữ liệu lớn.

Tên đề xuất: **Topology-Aware Next-Article Ranking on Wikipedia: A Temporal Comparison of Click Frequency and Historical Hyperlink Structure**.

Dự án nghiên cứu khi nào hyperlink topology bổ sung thông tin cho historical click frequency trong **source-conditioned next-article ranking**. Clickstream là aggregate counts; không tuyên bố user personalization hoặc session-aware prediction.

## Đọc kế hoạch

Bắt đầu từ [PROJECT_PLAN](docs/PROJECT_PLAN.md), gồm đủ 10 phần: executive assessment, formulation, dataset, experiments, EDA, architecture, roadmap, defense, risks và immediate actions.

| Tài liệu | Nội dung |
|---|---|
| [PROJECT_PLAN](docs/PROJECT_PLAN.md) | Research questions, scope, roadmap 8 tuần, acceptance, report/presentation/demo |
| [DATASET_FEASIBILITY](docs/DATASET_FEASIBILITY.md) | Dataset comparison, nguồn đã xác minh, primary/fallback, tài nguyên và blockers |
| [EXPERIMENT_DESIGN](docs/EXPERIMENT_DESIGN.md) | Formalization, model matrix, chronological split, candidates, metrics, tuning, A1–A9, leakage audit |
| [EDA_AND_ANALYSIS_PLAN](docs/EDA_AND_ANALYSIS_PLAN.md) | Mỗi chart gắn research question/decision; error analysis, sensitivity, tables |
| [IMPLEMENTATION_ROADMAP](docs/IMPLEMENTATION_ROADMAP.md) | Kiến trúc, interfaces, artifacts, tests, dependencies, milestones và definition of done |
| [LITERATURE_REVIEW](docs/LITERATURE_REVIEW.md) | 11 công trình, bibliography, comparison matrix và positioning |
| [RISKS_AND_DEFENSE](docs/RISKS_AND_DEFENSE.md) | Risk register, Feedback-to-Action Matrix và 25 câu hỏi bảo vệ |

[Planning review](docs/PLANNING_REVIEW.md) đối chiếu yêu cầu với deliverables. [Implementation status](docs/IMPLEMENTATION_STATUS.md) ghi phần thực sự đã có; tài liệu thiết kế không phải chứng nhận mọi thí nghiệm đã chạy.

## Quyết định chính

- Primary: eswiki Clickstream Jan–Mar 2018 train, April validation, May test; June là fixed-model temporal extension. Independent WikiLinkGraphs snapshot 01/03/2018.
- Ranking trên outgoing editorial hyperlinks được khóa trước evaluation; mọi model dùng cùng candidates và source sample.
- Báo Recall@5/10/20, MRR@10, NDCG@10 với full observable denominator và conditional denominator, macro/traffic-weighted aggregation, candidate coverage và paired uncertainty.
- P0: popularity/Markov/backoff, uniform/in-degree, PPR-H/PPR-C và score fusion. P1: fixed-support weighting, matrix fusion, Node2Vec H/W, HITS và temporal robustness. Không cần GPU.
- Fallback: Wikispeedia; phải đổi claim sang goal-directed game navigation.

[Data audit](docs/DATA_AUDIT.md) và [manifests nhỏ được version-control](docs/evidence/README.md) ghi nhận count bằng 10, raw duplicate groups và sai lệch supplied redirect mapping. Mẫu đã chuẩn bị có 200 queries, 8.094 nodes, 319.694 edges; giữ query candidates nhưng mất boundary edges ở intermediate nodes. Không gọi kết quả tương lai trên mẫu này là full-Wikipedia benchmark.

## Kiểm tra nhẹ, không tải dữ liệu

Core cần Python ≥3.11, dùng standard library. Môi trường đã kiểm tra là Python 3.13.13 trên macOS arm64. Chạy tại gốc repository:

```bash
python3 -m venv .venv
PYTHONPATH=src .venv/bin/python -m wikinav doctor
PYTHONPATH=src .venv/bin/python -m wikinav validate-config
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p test_core.py
PYTHONPATH=src .venv/bin/python -m wikinav toy-run --output results/toy-review
```

`toy-run` cần output directory chưa tồn tại. Fixtures là synthetic; không dùng điểm toy làm bằng chứng model tốt trên Wikipedia. Core có 57 tests. Trong môi trường study cục bộ hiện có, toàn suite gồm 69 tests đạt; study tests dùng tiny synthetic data, không đọc labels test thật. Môi trường chưa có scientific dependencies sẽ skip study tests, vì vậy phải đọc cả số skipped.

Core có 9 scorers, metric engine và freeze-before-test workflow. Sparse backend bổ sung DuckDB/Parquet, SciPy CSR, historical redirect resolver và experiment runner. Các thành phần này chưa có clean end-to-end benchmark certificate. Gensim phát sinh native warning trong lần thử Node2Vec thật; không dùng cache đó làm kết quả chính thức. Không chạy automation tải dữ liệu/training chỉ để xem planning.

Raw datasets, prepared graph, embeddings và model caches được Git-ignore. Manifests nhỏ chứa URLs, fingerprints và audit counters; không chứa credentials. Git CLI đã push được repository; lỗi quyền GitHub integration trước đó không còn là blocker cho cách dùng Git này.
