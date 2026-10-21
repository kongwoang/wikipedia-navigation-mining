# Câu hỏi bảo vệ — trả lời dựa trên kết quả thật

Đọc cùng [Feedback-to-Action Matrix](../docs/RISKS_AND_DEFENSE.md). Các câu trả lời dưới đây giới hạn ở final study-v3, không dùng giả định trong planning như experimental facts.

| # | Câu hỏi khó | Câu trả lời | Evidence cần mở |
|---|---|---|---|
| 1 | Vì sao next-article ranking, không link prediction? | Candidates đã là historical hyperlinks. Labels là future observed transitions; output sắp thứ tự next destinations, không binary existence của edge. | [Report §3](REPORT.md#3-problem-statement), shared candidates hash |
| 2 | Vì sao directed graph? | Link u→v không suy v→u; navigation/source conditioning và dangling treatment phụ thuộc direction. Symmetrization làm thay transition process. | [Method §8](REPORT.md#8-methodology), directed-edge unit tests |
| 3 | Edge weights lưu thế nào? | CSR H nhị phân; C chứa tổng published Jan–Mar counts; normalize từng row; WH dùng c·1_H+100P_H. Không dense adjacency. | `sparse_models.transitions`, data manifest, A4 |
| 4 | Vì sao PPR thay vì chỉ Markov? | Để kiểm tra multi-step topology trên candidates chưa có count. Kết quả PPR-H kém Markov tổng thể; không kết luận phải triển khai PPR. | [Main table](RESULT_TABLES.md), A7, Danza case |
| 5 | Vì sao Node2Vec? | Kiểm tra biased walk neighborhood representations có hữu ích cho one-step ranking hay không. Cosine có limitation symmetric; weighted variant tốt hơn H nhưng vẫn dưới Markov. | [Matched A5](generated/tables/paired_bootstrap.csv), seed table |
| 6 | Topology mang thêm gì ngoài clicks? | Một số training-unobserved destinations được đưa lên Top-10: May PPR-H Recall0,2335 vs Markov0,0912 trong tập con đó. Hybrid overall CI chứa0 nên chưa chứng minh net gain chắc chắn. | [A7](generated/tables/transition_sparsity.csv), primaryCI |
| 7 | Personalization nghĩa gì? | Restart seed là article hiện tại, query personalization. Không có user identifier/profile; không user-personalized/session-aware claim. | [Problem](REPORT.md#3-problem-statement), source documentation |
| 8 | Sao không HITS/CycleRank? | Có HITS-global và in-degree comparator. Query-local HITS/CycleRank đòi thêm context/cycle policy; là extension ngoài core, không loại vì giả định chúng kém. | [Literature rationale](../docs/LITERATURE_REVIEW.md), full14 model table |
| 9 | Làm sao biết gain do graph information? | Chung candidates/splits; đối chiếu behavior-only scorer, H-only và fusion. Fixed-support/damping A4, matched-knob A5 tránh confound. Không causal attribution hoặc gọi WH−H là gain topology beyond Markov. | [Ablation §12](REPORT.md#12-ablation-studies) |
| 10 | Chặn leakage thế nào? | H độc lập, redirect cutoff, train-only sample, April tuning, hashed predictions hoàn tất trước May/June read. Không graph dựng từ held-out transitions, không test-based node selection. | [Protocol](../docs/RUN_PROTOCOL.md), freeze/completion, temporal tests |
| 11 | Missing/low-frequency edges xử lý sao? | Published absence bị censored, không reliable negative. WH giữ H support; evaluator báo observable labels/coverage. Source không labels là NA; test target ngoài candidates vẫn ở full denominator. | [Data audit](../docs/DATA_AUDIT.md), metrics tests |
| 12 | Vì sao Recall/MRR/NDCG? | Recall đo coverage positives, MRR first successful recommendation, log-gain NDCG thêm count/rank. MRR dễ bão hòa nên thêm mass recall/expectedRR, macro và weighted. | [Definitions §9](REPORT.md#9-experimental-setup), analytic tests |
| 13 | Vì sao chronological split? | Dự báo future từ past; random aggregate-row split không mô phỏng event-time prediction. H cũ hơn test; không refit bằng April. Publication-time backtest vẫn là limitation. | Timeline, [Protocol](../docs/RUN_PROTOCOL.md) |
| 14 | Learning curves ở đâu? | Markov/PPR không epoch training. Có PPR residual, validation sensitivity, history-size/time-cost curves; N2V SGNS epoch-loss deltas là auxiliary, không click loss. | Figures05–07,09,11 |
| 15 | Hybrid kém baseline thì sao? | Báo đúng. June weighted NDCG fusion0,9178 < Markov0,9251; Tragacete là failure. Không retune trên test để cứu model; baseline có thể là lựa chọn cuối phù hợp hơn. | [Weighted tables](RESULT_TABLES.md), [cases](CASE_STUDIES.md) |
| 16 | Complexity và runtime? | PPR Q queries O(QT(E+V)); CSR memory O(E+V). N2V walk tokens rVL và SGNS theo window/negatives/dim; materialization/cache có overhead. Run sample245s/RSS~1,82GiB, không full graph estimate. | [Cost](generated/figures/09_cost_accuracy.png), runtime evidence |
| 17 | Dataset đại diện người dùng thật tới đâu? | Natural aggregate published transitions, không true sessions. Một edition/time/sample có suppression/exposure bias; Wikispeedia goal-directed không được đánh đồng, cũng không dùng vào kết quả. | [Limitations §15](REPORT.md#15-limitations-and-threats-to-validity) |
| 18 | EDA thay đổi thiết kế thế nào? | Concentration→strong local baseline; tails→stratification/macro-weighted; boundary→sample claim; unobserved H edges→fixed-support weighting; drift→time split/history test. | [EDA §6](REPORT.md#6-exploratory-data-analysis) |
| 19 | Kết luận ổn định không? | Two-month primary CIs đều chứa0; common117 sources kiểm soát composition một phần, embedding3 seeds. Chưa nhiều rolling origins hoặc independent language replication. | [Temporal table](generated/tables/temporal_common_sources.csv), seed/CI tables |
| 20 | Đóng góp chính? | Data audit, transparent controlled comparison, reproducible framework và phân tích negative/uncertain results. Không novel fusion/SOTA claim. | [Report Abstract/Discussion](REPORT.md) |
| 21 | Graph nhỏ như vậy có làm sai PPR? | Có thể. Query candidates giữ100%, nhưng intermediate edges chỉ giữ30,82%; transition/paths thay đổi. Không suy full-Wikipedia performance; cần boundary-controlled replication để mở scope. | [Boundary figure](generated/figures/02_graph_degree_boundary.png), graph stats |
| 22 | Cold-start benefit có bằng chứng? | Chưa.50 cold queries chỉ0 May / 1 June có labels; n1 không đủ uncertainty estimate. Không thay sources sau test để tạo subgroup thuận lợi. | [Group coverage](generated/tables/group_coverage.csv) |
| 23 | Counts có10 sao docs nói threshold khác? | Policy theo actual release audit; giữ valid n≥10 của files này. Duplicate groups được quarantine, không tự sum. README/meta historical wording không thay actual schema/mincount evidence. | [Data audit](../docs/DATA_AUDIT.md), manifests |
| 24 | Tại sao Gensim patched, có thay thuật toán không? | Local compatibility fix dot exception sentinel và BLAS interface, không SGNS/walk objective. Pinned sources, preserved license, negative-dot regression, finite-loss/vector smoke và Linux CI. wnm1 run không được chọn theo accuracy. | [Repro guide](REPRODUCIBILITY.md), build evidence, protocol history |
| 25 | Làm sao tin số trong demo/report? | Bundle SHA256 +5600 main-model re-evaluations từ actual scores/labels; analytic metric tests; generated Markdown tables. Verifier dùng shared metric engine nên không thay independent tests. UI chưa qua live QA vì browser policy từ chối origin. | `wikinav.verify_bundle`, [Final verification](../docs/evidence/final-verification.json) |

## Những câu tuyệt đối không nên nói

- “Hybrid cải thiện có ý nghĩa thống kê”: primary intervals chứa0.
- “Không có edge nghĩa là không ai click”: suppression và mapping losses.
- “PPR cá nhân hóa theo user”: chỉ seed current article.
- “Node2Vec loss thấp hơn chứng minh recommendation tốt hơn”: objective/corpus khác.
- “Benchmark trên toàn Wikipedia” hoặc “200 independent users”: sample graph/articles.
- “CI đã tái lập toàn bộ benchmark từ raw trên Linux”: CI tiny fixtures + portable evaluation.
- “Demo đã được kiểm tra trực tiếp trên browser”: quyền origin đã bị từ chối; cần local rehearsal.

Nếu bị hỏi ngoài evidence, trả lời rõ “chưa kiểm chứng trong scope này” và chỉ ra experiment cần làm; không tự dự đoán numerical gain.
