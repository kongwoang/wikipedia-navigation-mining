# Trạng thái hoàn thiện — 21/10/2026

Người dùng đã chuyển từ planning sang yêu cầu hoàn thiện toàn project. Scope đã thực hiện là **bounded university study trên real eswiki data**, không full-Wikipedia deployment. Bản planning trước đây được giữ để truy nguyên; trạng thái hiện hành ở đây và [báo cáo](../reports/REPORT.md).

| Thành phần | Trạng thái / bằng chứng |
|---|---|
| Bảy planning documents | Đủ scope, dataset/literature matrices, protocol, roadmap, feedback/risk/defense |
| Acquisition |9 raw artifacts pinned SHA256; source checksum validation; không commit rawdata |
| Data pipeline | Historical redirect cutoff, duplicate quarantine, main namespace, shared candidates, train-only sampling; manifest |
| Fresh preparation replay |4 Parquet files byte-identical, full counters identical: [evidence](evidence/preparation-replay.json) |
| Core/scientific correctness |72 local tests pass; core 57, scientific 14, acquisition 1; tiny fixtures, không fake benchmark |
| Native embedding backend | Gensim4.4.0+wnm2, typed SciPyBLAS, negative-dot regression, real finite-vector/loss smoke; Linux CI pass ở model-code commit9b1f28b |
| Frozen real study | `study-v3` complete,14 main models/28totalconfigurations; full validation grid,freeze-before-test,May/June |
| Models | Global/local/backoff/uniform/indegree,PPR-H/C/CH/WH,matrix/scorefusion,HITS,N2V-H/W |
| Evaluation | Required ranking metrics, full/conditional, macro/weighted, coverage, paired sourceCI, source/pair groups,3embeddingseeds |
| Ablations | A1–A9; fixed damping/support A4, matched knobs A5, history1/2/3months, fixed-model horizon/common sources |
| Analysis/report |11 scientific figures PNG/SVG, automated CSV/Markdown tables,7 deep cases,17-section report |
| Demo | Offline HTML from frozen real scores/labels;14 models,200 queries,2months; data/metric verified |
| Browser QA | **Chưa thực hiện được**: localhost origin gate từ chối. Không workaround; rehearsal checklist và static case fallback đã có |
| Presentation/defense | Markdown outline12–15 phút,2–3 phútdemo,25 evidence-backed answers |
| Reproducibility | Pinned lock/build/source hashes, clean-output script, bundle SHA verifier;5600main-model re-evaluations verified |
| Publication | Git main; [Actions](https://github.com/kongwoang/wikipedia-navigation-mining/actions) chứa status theo commit; không suy CI fixtures là full real-data rerun |

## Kết luận thực nghiệm đã chốt

May Markov macro full NDCG0,8991, fusion0,9034; Δ0,00429 và95%CI[−0,00076;0,01035]. Chưa reliable hybrid improvement. Pure H topology kém local frequency; weighted walks tốt hơn unweighted controls. Topology giúp một số training-unobserved targets; cold-start thiếu labels (May0/June1observable sources). June traffic-weighted fusion thấp hơn Markov. Báo đầy đủ cả positive/negative observations.

## Scope/limitations còn lại, không che giấu thành việc đã hoàn tất

- 200train-stratifiedqueries;8.094 nodes/319.694 edges; intermediate outgoing retention30,82%. Không full-graphPPR/population claim.
- Fixed model May/June, chưa rolling-origin retraining hay cross-language replication.
- Local full run +fresh preparation replay+portable re-evaluation+Linux tinyCI; chưa clean full raw-to-model replication trên Linux.
- Browser UI rendering/interactions cần rehearsal sau khi người dùng mở HTML; policy đã chặn agent truy cập origin.
- CycleRank/CoCit, directed embedding scoring, fullgraph và true sessions làP2extensions; không nằm trên critical path của completed course study.

## Code lineage

Frozen model code commit`9b1f28ba90e21591afb23ed65c5fd0a17f4195d2`; freeze ghi`git_dirty=true`, algorithm digest riêng được so lại với commit. Final packaging thêm acquisition integrity, presentation/analysis/report/CI; không sửa thuật toán hoặc tuning sau test. [Final verification](evidence/final-verification.json) ghi checks. study-v1 incomplete và study-v2 backend-portability run không dùng làm final results; lịch sử trong [RUN_PROTOCOL](RUN_PROTOCOL.md).
