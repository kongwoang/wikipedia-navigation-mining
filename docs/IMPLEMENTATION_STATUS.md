# Trạng thái hiện hành — scope thống nhất 05/11/2026

[PROJECT_PLAN](PROJECT_PLAN.md) là scope/backlog duy nhất; [REPORT](../reports/REPORT.md) là báo cáo chính; [PRESENTATION](../reports/PRESENTATION.md) là kịch bản bảo vệ. Các bản planning và quality roadmap cũ chỉ để truy nguyên.

## Đã hoàn thành và được giữ làm bằng chứng

| Thành phần | Trạng thái / evidence |
|---|---|
| Historical benchmark | Eswiki 2018, 200 sampled queries, independent H01/03, temporal protocol; [bảng đầy đủ](../reports/RESULT_TABLES.md) |
| Năm phương pháp chính + hai references | Markov, HITS-global, PPR-H, Node2Vec-H, fusion; Uniform/Global; scores đã freeze |
| Ablation/diagnostics | Matched weighting, validation grids/history, SGNS/PPR curves, seeds, coverage, macro/weighted, paired CIs |
| Technical extensions | Full H 36.333.722 edges, rolling July–September, degree-null/panels, CycleRank/adaptive/tie; giữ appendix, dừng mở rộng |
| API + HTML acquisition | Pilot 8 pages, 654 API / 556 body edges, 1.028 occurrences, 8 matched revisions; [pilot](../reports/crawl/pilot-v2/PILOT.md) |
| Reproducibility | Raw hashes, preparation replay, portable verifiers, pinned dependencies, CI; [hướng dẫn](../reports/REPRODUCIBILITY.md) |
| Course alignment / biên tập | Review 14 PDF / 733 trang; thống nhất 2 RQ, bảng 7 rows, report/demo cùng models; đây là documentation update, không experiment mới |

## Chưa hoàn thành

1. **Manual extraction audit 20 pages**, annotations và precision/recall theo context. Pilot 8 pages không đủ để claim representative corpus hoặc extraction accuracy.
2. **Visual/interaction rehearsal** của HTML demo. Portable data/metric checks không thay UI QA; trước đó browser origin access bị từ chối.
3. **Deck render / cuộc bảo vệ thử** theo Markdown kịch bản hiện hành.

Crawled features chưa được evaluate cho recommendation; current crawl 2026 không đưa vào benchmark 2018. Corpus lớn / Global PR / content models không còn là việc cần làm để hoàn thành scope.

## Verification và lineage

- Audit 29/10: [crawl verification](evidence/crawl-verification.json) ghi 104 local tests (18 crawl tests), raw parsing replay, resume 0 network requests. Đây là record lần chạy trước, không nhận lượt biên tập này đã rerun full suite.
- Original verifier: 5.600 source×model×period evaluations; extension: 28.600 evaluations / 19.600 ranking checks / 3.600 demo views. Đây là check counts, không sample size độc lập và không retrain.
- Original model code `9b1f28ba90e21591afb23ed65c5fd0a17f4195d2`; extension protocol `35d308f`, algorithm bytes khớp `1b48689`. [Extension audit](evidence/extension-final-verification.json), [pretest correction](evidence/extension-pretest-correction.json).
- Benchmark/test payloads/protocols giữ nguyên khi thu gọn project. Bảng chính là subset biên tập sau thực nghiệm; full results vẫn được link.
- Không claim full population, current Wikipedia, users, causal CTR, cold-start solution hoặc clean full Linux raw-to-model replication.

## Kết luận được bảo vệ

Original fusion−behavior May Δ0,00429, 95%CI[−0,00076;0,01035]; June cũng chứa 0. PPR-H tìm một số training-unobserved destinations nhưng chưa có reliable net gain khi kết hợp. Full-H control không đảo ngược khoảng cách với Markov ở sample; rolling tie-break CIs là contrast khác, không thay CI fusion. Cases gốc dùng Danza posmoderna và Tragacete để giải thích gain/loss.
