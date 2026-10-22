# Trạng thái bàn giao — 22/10/2026

Đã hoàn thành implementation, nghiên cứu dữ liệu thật và toàn bộ quality-improvement extensions trong scope học phần. Đây là **empirical comparative study có literature review**, không survey thuần, không production recommender hoặc population benchmark. Bảy planning documents được lưu để truy nguyên; trạng thái hiện hành ở đây.

| Thành phần | Bằng chứng hoàn tất |
|---|---|
| Planning / literature / defense | Bảy tài liệu thiết kế, verified literature matrix, feedback-to-action, risk register, câu hỏi bảo vệ |
| Data | Historical H/redirect cutoff01/03/2018, Clickstream Jan–Sep2018, schema/mapping/duplicate audits; 12 pinned raw fingerprints |
| Preprocessing | Train-only stratified sampling, candidate integrity, sparse artifacts/manifests; original preparation replay byte-identical bốn Parquets |
| Original study-v3 | 14 main configurations/28 total runs, April tuning; frozen predictions trước May/June evaluation |
| Full-graph boundary | 2.077.467 nodes/36.333.722 H edges; pilot qua gate; original candidates giữ nguyên; H/C/WH và fusion controls |
| Rolling-origin extension | Ba windows July/August/September, 19 configurations mỗi window; protocol/grids khóa trước test labels |
| Structural controls | Năm degree-preserving rewired H, query rows protected; hai disjoint query panels thêm400 queries trên cùng full H |
| Model extensions | Topology tie-break, adaptive fusion, exact bounded CycleRank length2/3; diagnostics/tuning/three embedding seeds |
| Analysis | Original11 + extension7 scientific figures PNG/SVG; required metrics, coverage, paired CIs, common-source, fallback/observed-unobserved analysis |
| Case studies | Bảy original cases và hai extension cases sâu, gồm gain và fallback failure; real counts/rankings |
| Correctness | **86 local tests pass, không skip**: core57, study14, acquisition1, extension10, portable extension verification4 |
| Portable evidence | Original5600 + extension28600 metric evaluations; extension19600 ranking checks và3600 demo model views |
| Reproduction | Pinned dependencies/native patch; `reproduce.sh`, `reproduce_extensions.sh`; raw-to-model và re-evaluation phân biệt rõ |
| Demo | Original14 models/200 queries/2months; extension6 displayed models/200 queries/3rolling months, offline HTML từ actual predictions |
| Browser QA | **Chưa thực hiện được** do origin access bị từ chối trước đó; không workaround. Static/data checks không thay visual/interaction rehearsal |
| Publication | Code, reports, portable artifacts; [GitHub Actions](https://github.com/kongwoang/wikipedia-navigation-mining/actions) kiểm tra từng pushed commit |

## Kết luận thực nghiệm

Markov là strong baseline. Original fusion−Markov May Δ0,00429,95%CI[−0,00076;0,01035]. Full-H PPR vẫn thấp hơn Markov ở các sampled panels; graph boundary loss không đủ giải thích khoảng cách. Real topology tốt hơn degree-matched rewired controls, nhưng topology thêm vào behavior chưa cho reliable net gain: primary tie-break−Markov rolling Δ+0,00804/+0,00249/−0,00043, cả ba CI chứa0.

Case **Emperador Alejandro** cho thấy zero-count fallback có ý nghĩa: global popularity có thể thắng PPR; không quy toàn bộ thay đổi cho count ties. Cold nhóm vẫn thiếu labels. Macro/weighted có thể đổi thứ tự model; báo cả hai.

## Phạm vi chưa được chứng minh

- Full-graph processing không đồng nghĩa population evaluation: rolling200 queries, query-panel controls600; một language/time period.
- Full graph chỉ dùng boundary/panel subset models; Node2Vec/CycleRank/rolling vẫn dùng induced context.
- Chưa có true users/sessions, causal online uplift, current-Wikipedia hoặc independent language replication.
- Local raw pipeline + preparation replay + portable verification + Linux tiny CI; chưa full real-data raw-to-model replication trên Linux.
- Browser rendering/interactions cần người trình bày rehearsal; đây là giới hạn QA còn lại, không giấu thành bước đã hoàn tất.

## Lineage và đầu vào đọc báo cáo

- Original model code `9b1f28ba90e21591afb23ed65c5fd0a17f4195d2`; original predictions/bundle không thay đổi.
- Extension protocol commit `35d308f`; algorithms sau sửa SQL alias trước holdout khớp bytes commit `1b48689`. Freeze ghi commit đang có lúc chạy, kèm exact per-file hashes; record không phải external preregistration.
- `extensions-v1` dừng trước July test; lỗi SQL alias được sửa/test trước run `extensions-v2`. [Pretest correction](evidence/extension-pretest-correction.json) ghi loaded months chỉ Mar–June.
- [Extension verification](evidence/extension-final-verification.json): source hashes, runtime/RSS, tests, bundle checks. Report-only fallback analysis giữ nguyên cả năm frozen payload hashes.
- Đọc [báo cáo chính](../reports/REPORT.md), [kết quả mở rộng](../reports/EXTENSION_RESULTS.md), [cases mới](../reports/EXTENSION_CASES.md) và [tái lập](../reports/REPRODUCIBILITY.md).
