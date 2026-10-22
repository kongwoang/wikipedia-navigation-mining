# Wikipedia Navigation Mining

**Đã hoàn thiện implementation, thực nghiệm dữ liệu thật và toàn bộ gói nâng chất lượng.** Study gốc có 14 model chính/28 configurations; extension có 19 configurations mỗi rolling window, full-graph controls, degree-preserving null và query-panel sensitivity. Đây là comparative empirical study, không survey thuần hoặc population benchmark.

**Topology-Aware Next-Article Ranking on Wikipedia: A Temporal Comparison of Click Frequency and Historical Hyperlink Structure**

| Đọc / sử dụng | Nội dung |
|---|---|
| [Kết quả mở rộng mới nhất](reports/EXTENSION_RESULTS.md) | Full graph, ba tháng mới, CycleRank/adaptive/tie-break, null/panel controls và fallback analysis |
| [Cases mới](reports/EXTENSION_CASES.md) · [Demo rolling](reports/extensions/study-v2/demo.html) | Predictions thật qua ba lần refit; đối chiếu gain và fallback failure |
| [Báo cáo kết quả](reports/REPORT.md) | 17 phần: methodology, results, ablations, error analysis, limitations |
| [Bảng kết quả](reports/RESULT_TABLES.md) | Required ranking metrics, macro/weighted, full/conditional, CI, history/seeds |
| [Case studies](reports/CASE_STUDIES.md) | Bảy cases, Top-10 thật, train/future counts và scores |
| [Demo offline](reports/generated/demo.html) | Clone/tải HTML rồi mở trong browser; GitHub chỉ hiển thị source |
| [Tái lập](reports/REPRODUCIBILITY.md) | Quick verification và raw-to-model reproduction |
| [Thuyết trình](reports/PRESENTATION.md) · [Bảo vệ](reports/DEFENSE.md) | Outline12–15 phút, demo script,25 câu hỏi có evidence |
| [Trạng thái và kiểm chứng](docs/IMPLEMENTATION_STATUS.md) | Phạm vi hoàn tất, test/CI/provenance và giới hạn QA |
| [Kế hoạch nâng chất lượng](docs/QUALITY_IMPROVEMENT_PLAN.md) | Kế hoạch review và bảng đối chiếu các extensions đã hoàn thành |
| [Phân tích cơ chế bổ sung](reports/extensions/mechanism-v1/ANALYSIS.md) | Post-hoc decomposition từ frozen predictions; không thay kết quả hoặc protocol gốc |

Dữ liệu eswiki: Jan–Mar2018 train, April validation, May primary test và June fixed-model horizon. Independent hyperlink snapshot01/03/2018; mẫu200 queries,8.094 nodes,319.694 edges. Nhiệm vụ là **source-conditioned ranking**, không user personalization hoặc true-session prediction.

Kết quả chính: May macro full NDCG@10 của Markov **0,8991**, PPR-H **0,3126**, score fusion **0,9034**. Fusion−Markov Δ**0,00429**,95%CI**[−0,00076;0,01035]**: chưa có bằng chứng improvement đáng tin cậy. Topology giúp một số training-unobserved transitions nhưng không thắng frequency tổng thể. Cold-start thiếu labels để kết luận. Chi tiết/limitations trong báo cáo.

Extension đã xử lý full historical H **2.077.467 nodes/36.333.722 edges**; full-H PPR vẫn kém Markov trên sampled queries. Ba rolling test months July–September có 128/127/124 observable sources; tie-break−Markov Δ **+0,00804 / +0,00249 / −0,00043**, cả ba 95% CI chứa 0. Năm degree-matched rewired graphs cho thấy real topology có thông tin beyond degree, nhưng chưa chứng minh reliable net gain khi bổ sung vào Markov. [Protocol khóa trước holdout](docs/EXTENSION_PROTOCOL.md).

## Xem và kiểm tra nhanh — không tải dữ liệu lớn

Python≥3.11; verifier/core dùng standard library:

```bash
PYTHONPATH=src python3 -m wikinav.verify_bundle
PYTHONPATH=src python3 -m wikinav.verify_extensions
PYTHONPATH=src python3 -m unittest discover -s tests -p test_core.py
python3 scripts/build_report_tables.py
```

Mở `reports/generated/demo.html` trực tiếp bằng browser. Có200 frozen queries,14 models,2 test months và controls đổi source/model/denominator. Predictions đến từ pipeline thật; tháng khác chỉ đổi evidence/metrics. Agent chưa kiểm tra rendering/interactions trực tiếp vì browser origin approval bị từ chối; xem checklist rehearsal trong presentation.

Hai verifiers kiểm tra hashes và tính lại **5.600 lượt của study gốc + 28.600 lượt của extension**, cùng 19.600 extension rankings và 3.600 demo model views; **không retrain**. Đây là số lượt kiểm tra, không sample size độc lập. Full suite **86 tests** đạt cục bộ; core dùng standard library. [GitHub Actions](https://github.com/kongwoang/wikipedia-navigation-mining/actions) kiểm tra core Python 3.11/3.13, portable bundle và scientific backend Linux. CI không tải real datasets.

## Tái tạo toàn bộ thực nghiệm

Cần Python 3.13, C/C++compiler, RAM16–18 GB và dự trù10–20 GB disk. Raw download khoảng1 GB; không cần GPU:

```bash
sh scripts/reproduce.sh
sh scripts/reproduce_extensions.sh
```

Script cài pinned dependencies + audited Gensim compatibility build, kiểm tra tests/checksums, chuẩn bị data, chọn knobs trên validation, freeze predictions rồi evaluate test, sinh figures/tables/demo. Output mới nằm ở `results/reproduction/` và `reports/reproduced/`; không overwrite published bundle. [Hướng dẫn chi tiết](reports/REPRODUCIBILITY.md) mô tả overrides, native patch và giới hạn cross-platform repeatability.

Extension script tải thêm khoảng 112 MB compressed Clickstream, build full historical CSR từ data đã ingest và chạy từng stage tuần tự. [Evidence mới](docs/evidence/extension-final-verification.json) ghi provenance, resource cost và mức kiểm chứng.

Full original model run245,32 s/RSS~1,82GiB trên máy đo macOS arm64; số này không gồm download/ingestion/build và không cam kết thời gian trên máy khác. Preparation replay tạo lại bốn Parquet hashes giống hệt. Chưa chứng nhận full raw-to-model replication trên Linux.

## Kiến trúc

- `src/wikinav/`: core reference models/metrics, sparse CSR scorers, directed Node2Vec, historical redirects, acquisition/preprocessing, experiment/analysis/demo/verifier.
- `configs/`: TOML protocol/settings; `requirements-study.lock`: pinned scientific environment.
- `scripts/`: reproduction, audited native installer và Markdown evidence-table generator.
- `tests/`: analytic graph/metric oracles, leakage/temporal contracts, synthetic integration, backend regression và data-hash checks.
- `reports/generated/`: original frozen results, 11 figures, CSV tables, real-prediction demo và manifests.
- `reports/extensions/study-v2/`: 7 figures bổ sung, 11 CSV tables, 5 compressed frozen payloads, rolling demo và provenance.
- `extension_data/models/experiment.py`: full-graph export, controlled models và temporal test barrier; `verify_extensions.py` kiểm tra bundle bằng standard library.
- `data/`, `results/`, `.cache/`: raw/prepared/model artifacts Git-ignored; small audit evidence được version-control.

## Kế hoạch, protocol và nguồn

Bảy tài liệu planning được giữ để truy nguyên quyết định: [Project plan](docs/PROJECT_PLAN.md), [Dataset feasibility](docs/DATASET_FEASIBILITY.md), [Experiment design](docs/EXPERIMENT_DESIGN.md), [EDA/analysis](docs/EDA_AND_ANALYSIS_PLAN.md), [Implementation roadmap](docs/IMPLEMENTATION_ROADMAP.md), [Literature review](docs/LITERATURE_REVIEW.md), [Risks/feedback matrix](docs/RISKS_AND_DEFENSE.md).

[RUN_PROTOCOL](docs/RUN_PROTOCOL.md) chốt chi tiết thực thi trước phân tích test; [Data audit](docs/DATA_AUDIT.md), [Evidence](docs/evidence/README.md) và [Attributions](docs/ATTRIBUTIONS.md) ghi nguồn, hashes, xử lý redirects/duplicates, licenses. Missing clicks không phải reliable negatives. Boundary experiment nay đã chạy full historical graph; rolling/embeddings vẫn dùng induced context. Cả hai chỉ đánh giá các query panels đã mô tả, không suy rộng thành population performance.
