# Thuyết trình 12–15 phút và kịch bản demo

Dùng số từ `study-v3`, không dùng validation/toy scores làm test result. Đọc [REPORT](REPORT.md), [RESULT_TABLES](RESULT_TABLES.md) và [DEFENSE](DEFENSE.md) trước khi trình bày.

| Slide | Thời gian | Thông điệp và evidence | Speaker notes |
|---|---:|---|---|
| 1. Câu hỏi nghiên cứu | 0:45 | Khi nào hyperlink topology bổ sung cho click frequency? | Đề tài comparative analysis; không phát minh recommender mới |
| 2. Task và data limitations | 1:00 | Source u → Top-K trong outgoing candidates; aggregate monthly counts | Không users/sessions; PPR query-personalized; absent ≠ zero |
| 3. Data audit & chronology | 1:15 | Jan–Mar train / April val / May–June test; H01/03 độc lập | 200 queries,8.094 nodes,319.694 edges; candidate retention100%, intermediate outgoing retention30,82% |
| 4. EDA → model choice | 1:00 | [Concentration](generated/figures/10_concentration_and_drift.png), [boundary](generated/figures/02_graph_degree_boundary.png) | Median top1 share0,5001; phải có local Markov và báo sample limitation |
| 5. Model controls | 1:15 | Markov / PPR-H / PPR-C / weighted-H / fusion / N2V-H/W | Behavior-only là ranking signal, mọi model chung H eligibility. WH hơn H chỉ chứng minh clicks giúp graph |
| 6. Evaluation | 1:15 | Recall5/10/20, MRR10, NDCG10; full vs conditional; macro vs weighted | May127/200 nguồn có labels; coverage95,54%mass. Freeze trước test; paired source bootstrap |
| 7. Main results | 1:30 | [Main figure](generated/figures/04_main_comparison.png); Markov0,8991 vs fusion0,9034 | Δ0,00429,95%CI[−0,00076;0,01035]. Không gọi significant improvement. June weighted fusion giảm |
| 8. Vì sao? Ablation + diagnostics | 1:30 | [Validation](generated/figures/05_validation_sensitivity.png), [convergence](generated/figures/06_numerical_diagnostics.png) | Matched weighted N2V gain0,2142; PPR-H train-unobserved Recall0,2335 vs Markov0,0912. Coldstart n0/n1 không đủ |
| 9. Demo đối chiếu hai chiều | 2:30 | Ultimate Avengers, Tragacete,1944 | Xem workflow bên dưới; trình bày cả win/failure/coverage |
| 10. Kết luận và khả năng tái lập | 1:00 | [Cost](generated/figures/09_cost_accuracy.png), tests/manifests | Markov mạnh/rẻ; topology giúp một số tail transitions, chưa đủ reliable overall gain.72 tests;5600 re-evaluations; chưa full-Wikipedia/online test |

## Demo 2–3 phút

Mở `reports/generated/demo.html` bằng browser sau khi clone/tải repository; HTML offline, không cần server/API key/GPU. GitHub hiển thị source HTML, không render ứng dụng. Data và predictions được tạo bởi real pipeline, không hardcode các recommendation lists bằng tay.

1. Mở “Case studies”, chọn **Ultimate Avengers**. Giữ May và Full observable labels. Bốn cards là Markov/PPR-H/Node2Vec-H/fusion. Đọc training counts ở ba destinations đầu, so future evidence và phần tail. Fusion0,8887 vs Markov0,7583: topology giúp case này, chưa phải average effect.
2. Chọn **Tragacete**. Fusion0,7353 vs Markov0,8616. Xem Top-10 và future target *Parque Cinegético Experimental de El Hosquillo*. Câu hỏi cho người xem: topology có thể làm mất một target hữu ích ở phần tail như thế nào?
3. Chọn **1944**, xem các future targets ngoài candidates. Đổi denominator Full→Within candidates. Score đổi vì estimand, predictions không đổi; không được dùng conditional score để che coverage loss.
4. Đổi tháng June: counts/metrics thay đổi, **rankings giữ nguyên**. Đổi một card sang M5W hoặc PPR-C để so signal; raw scores khác scale, chỉ so order/metric giữa models.
5. Nếu còn thời gian, tìm **Danza posmoderna** để thấy training-unobserved Merce Cunningham, hoặc **Repollo relleno** để thấy Markov/PPR/fusion đều thất bại.

Nguồn không có observable labels hiển thị N/A; không diễn giải N/A là zero accuracy. Future table hiển thị tối đa30destinations, metrics dùng toàn bộ labels. Trang chỉ hỗ trợ200 frozen queries, không tự crawl bài người dùng nhập.

## Kiểm tra trước buổi bảo vệ

- Chạy `PYTHONPATH=src python3 -m wikinav.verify_bundle`; expected5600 evaluations verified.
- Mở HTML, thử case buttons, model/month/denominator selectors, search no-match và narrow viewport. **Browser QA chưa được agent thực hiện vì origin approval bị từ chối**; đây là bước rehearsal còn cần người trình bày kiểm tra trên browser của mình.
- Kiểm tra font Vietnamese, bảng không tràn và đường dẫn ảnh trong Markdown viewer.
- Không chạy download/build/training live trên sân khấu; thời gian245s là run trên máy đo, không cam kết mọi laptop.
- Nếu browser không chạy được, dùng [CASE_STUDIES](CASE_STUDIES.md) và bảng thật làm demo tĩnh; không dựng kết quả giả để thay thế.

## Câu kết luận nên dùng

“Trong mẫu lịch sử đã kiểm soát, local frequency là baseline rất mạnh. Topology giúp một số transitions chưa quan sát trong training, nhưng fusion chưa cho gain tổng thể đủ chắc chắn. Giá trị của đồ án là phép so sánh và audit có thể kiểm tra lại, kể cả khi model phức tạp không thắng.”
