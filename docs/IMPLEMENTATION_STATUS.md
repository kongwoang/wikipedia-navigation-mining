# Trạng thái hiện hành — scope thống nhất 05/11/2026

[PROJECT_PLAN](PROJECT_PLAN.md) là scope/backlog duy nhất; [REPORT](../reports/REPORT.md) là báo cáo chính; [PRESENTATION](../reports/PRESENTATION.md) là kịch bản bảo vệ. Các bản planning và quality roadmap cũ chỉ để truy nguyên.

## Đã hoàn thành và được giữ làm bằng chứng

| Thành phần | Trạng thái / evidence |
|---|---|
| Historical benchmark | Eswiki 2018, 200 sampled queries, independent H01/03, temporal protocol; [bảng đầy đủ](../reports/RESULT_TABLES.md) |
| Năm phương pháp chính + hai references | Markov, HITS-global, PPR-H, Node2Vec-H, fusion; Uniform/Global; scores đã freeze |
| Ablation/diagnostics | Matched weighting, validation grids/history, SGNS/PPR curves, seeds, coverage, macro/weighted, paired CIs |
| Technical extensions | Full H 36.333.722 edges, rolling July–September, degree-null/panels, CycleRank/adaptive/tie; giữ appendix, dừng mở rộng |
| API + HTML acquisition | Audit20pages,1.397API /1.049body edges,1.936occurrences,20matched revisions; [audit](../reports/crawl/audit-v2/AUDIT.md). Pilot8pages giữ riêng |
| Extraction quality |120fixed occurrences agent-reviewed,2context errors được sửa; labels/raw hashes/offline reparse. Chưa có human gold |
| Presentation |10slides,4editable charts,4editable tables,10speaker notes; final-file render và package/data checks pass. [Deck/QA](../reports/deliverables/README.md) |
| Reproducibility | Raw hashes, preparation replay, portable verifiers, pinned dependencies, CI; [hướng dẫn](../reports/REPRODUCIBILITY.md) |
| Course alignment / biên tập | Review 14 PDF / 733 trang; thống nhất 2 RQ, bảng 7 rows, report/demo cùng models; đây là documentation update, không experiment mới |

## Phần chưa thể xác nhận

1. **Visual/interaction rehearsal của HTML demo:** CUA ngày05/11 từ chối localhost origin bởi saved user permission. Không bypass. Portable checks không thay UI QA; người trình bày cần tự mở demo theo [checklist](../reports/PRESENTATION.md).
2. **Human extraction adjudication / held-out audit:** chưa có;120labels hiện tại là agent review và cùng sample dùng sửa parser. Không nhận population accuracy.
3. **Native Office compatibility và cuộc bảo vệ thử có người:** chưa thực hiện. PPTX đã render/import lại và rà10trang;12–14phút là time budget.

Crawled features chưa được evaluate cho recommendation; current crawl 2026 không đưa vào benchmark 2018. Corpus lớn / Global PR / content models không còn là việc cần làm để hoàn thành scope.

## Verification và lineage

- Historical audit29/10: [crawl verification](evidence/crawl-verification.json) ghi 104 local tests (18 crawl tests), raw parsing replay, resume 0 network requests. Đây là record lần chạy trước, không nhận lượt biên tập này đã rerun full suite.
- Lượt hoàn thiện05/11: **108tests pass** (22crawl tests);2portable benchmark verifiers, crawl report verifier và presentation evidence verifier pass. [Verification record](evidence/final-submission-verification.json). Không retrain hoặc đổi frozen benchmark.
- Original verifier: 5.600 source×model×period evaluations; extension: 28.600 evaluations / 19.600 ranking checks / 3.600 demo views. Đây là check counts, không sample size độc lập và không retrain.
- Original model code `9b1f28ba90e21591afb23ed65c5fd0a17f4195d2`; extension protocol `35d308f`, algorithm bytes khớp `1b48689`. [Extension audit](evidence/extension-final-verification.json), [pretest correction](evidence/extension-pretest-correction.json).
- Benchmark/test payloads/protocols giữ nguyên khi thu gọn project. Bảng chính là subset biên tập sau thực nghiệm; full results vẫn được link.
- Không claim full population, current Wikipedia, users, causal CTR, cold-start solution hoặc clean full Linux raw-to-model replication.

## Kết luận được bảo vệ

Original fusion−behavior May Δ0,00429, 95%CI[−0,00076;0,01035]; June cũng chứa 0. PPR-H tìm một số training-unobserved destinations nhưng chưa có reliable net gain khi kết hợp. Full-H control không đảo ngược khoảng cách với Markov ở sample; rolling tie-break CIs là contrast khác, không thay CI fusion. Cases gốc dùng Danza posmoderna và Tragacete để giải thích gain/loss.
