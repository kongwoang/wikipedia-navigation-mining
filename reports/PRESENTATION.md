# Thuyết trình 12–15 phút và demo nghiên cứu

Dùng [REPORT](REPORT.md) cho nền tảng và [EXTENSION_RESULTS](EXTENSION_RESULTS.md) cho kết luận mới nhất. Không trình bày19 configurations như19 thuật toán độc lập. Giữ detailed grids/seeds/required metrics trong appendix.

| Slide | Thời gian | Thông điệp và evidence | Điểm cần nói rõ |
|---|---:|---|---|
| 1. Câu hỏi nghiên cứu | 0:40 | Khi nào hyperlink topology bổ sung cho click frequency? | Empirical comparative study, không novelty claim |
| 2. Task và dữ liệu | 1:00 | Source u → ranked outgoing hyperlinks; published monthly counts | Không users/sessions; missing≠negative; PPR query-personalized |
| 3. Chronology và test barrier | 1:10 | Original Jan–March/April/May–June; ba rolling windows July–September | H01/03 cố định, test predictions freeze trước label read; extension protocol khóa trước new test |
| 4. EDA → thiết kế | 0:55 | Traffic concentration, sparse labels, boundary loss | Local Markov là baseline mạnh; giữ coverage/full denominator; cần boundary control |
| 5. Model families | 1:00 | Frequency, H-only, click-weighted walks, fusion, embeddings, cycle/tie controls | Mỗi model trả lời một câu hỏi; cùng candidates; graph scoring không tự là next-click probability |
| 6. Main ranking comparison | 1:05 | Original Markov0,8991/fusion0,9034; [rolling figure](extensions/study-v2/figures/01_rolling.png) | Đủ Recall/MRR/NDCG trong appendix; macro/weighted không luôn cùng thứ tự |
| 7. Uncertainty và temporal robustness | 1:05 | [Primary CIs](extensions/study-v2/figures/02_primary_intervals.png);128/127/124 observable sources | Ba tie−Markov CI chứa0; không equivalence claim, không nhân samples theo periods |
| 8. Graph có bị cắt quá mạnh? | 1:00 | [Full vs induced](extensions/study-v2/figures/03_boundary.png),36,3m H edges | Full-H PPR vẫn kém Markov ở sample; graph size không biến query sample thành population |
| 9. Structure hay chỉ degree? | 1:00 | [Degree-null](extensions/study-v2/figures/04_degree_null.png), [panels](extensions/study-v2/figures/05_query_panels.png) | Real H hơn5rewired draws, nhưng không causal/permutation significance;600 queries vẫn ít cold labels |
| 10. Demo: gain và failure | 2:15 | [Rolling demo](extensions/study-v2/demo.html); Strathclyde/Emperador Alejandro | Xem actual counts/ranks; giải thích fallback-policy change, không chỉ chọn win |
| 11. Diagnostics/cost/reproducibility | 1:00 | [Validation](extensions/study-v2/figures/06_validation.png),86tests, hashes, verifiers | PPR residual, seed variation; không fake Markov loss curve; stages CPU/laptop feasible |
| 12. Kết luận và giới hạn | 0:50 | Structure chứa thông tin nhưng chưa reliable incremental gain trên frequency | Không users/online/cold-start/population claims; đóng góp là controlled comparison và giải thích có evidence |

## Demo 2–3 phút

Clone/tải và mở `reports/extensions/study-v2/demo.html` bằng browser; GitHub chỉ hiển thị HTML source. Chạy offline, không server/API/GPU; sáu displayed models từ actual frozen results.

1. Tìm **Strathclyde**, chọn **2018-09**. So M1_local và topology_tie. *Glasgow* có19 future clicks, chưa published training count; Markov ngoài Top-10, tie-break rank4, NDCG0→0,4307. Count22 của *Reino de Strathclyde* vẫn đứng đầu: tie-break không đảo unequal positive counts.
2. Tìm **Emperador Alejandro**, chọn **2018-08**. Source không có eligible training clicks; M1 scores là global-popularity fallback. *Alejandro Magno* rank1 và *Reino de Macedonia* rank4; tie/PPR làm chúng rank3 và ngoài Top-10. NDCG Markov0,8822→tie0,3145. Adaptive cũng dùng PPR ở zero mass; fusion giữ được popularity order của hai targets này.
3. Nhấn mạnh đây là hai extreme cases chọn sau test để giải thích. Average primary CI vẫn chứa0. Không đưa fallback failure thành câu chuyện “graph luôn kém ở cold start”: chỉ2–3 zero-eligible-mass sources có labels mỗi rolling period.
4. Đổi tháng để thấy scope train/validation/test và predictions thay theo refit đã khóa. Khác demo gốc May/June: demo gốc chỉ đổi labels/metrics, predictions cố định.
5. Nếu cần giải thích candidate limitation, mở original `reports/generated/demo.html`, source **1944**, đổi Full→Within candidates. Score thay vì denominator, không phải model cải thiện.

Nguồn không có future labels hiển thị N/A, không zero accuracy. Raw score scales giữa models khác nhau; tie score là ordinal encoding. Demo hiển thịTop10/futureTop30, evaluation dùng toàn bộ observable labels.

## Rehearsal và fallback

- Chạy `PYTHONPATH=src python3 -m wikinav.verify_bundle` và `PYTHONPATH=src python3 -m wikinav.verify_extensions`.
- Mở cả hai HTML, kiểm tra source/model/month controls, no-match search, narrow viewport, font và table overflow. **Agent chưa thực hiện browser rendering/interaction QA do origin access bị từ chối**; data verification/JS syntax check không thay bước này.
- Không download/build/train live. Stage times là measured local batch cost, không SLA.
- Nếu browser không hoạt động, dùng [EXTENSION_CASES](EXTENSION_CASES.md) và [CASE_STUDIES](CASE_STUDIES.md) làm demo tĩnh với số thật.

## Các câu trả lời cần chuẩn bị trong appendix

[DEFENSE](DEFENSE.md) có answer/evidence matrix. Ưu tiên: PPR damping vs restart; bounded CycleRank cost; null graph invariants; tie-break khác fallback; count suppression; full vs conditional NDCG; overlapping windows/source bootstrap; tại sao không thêm GNN; topology có thông tin nhưng net incremental gain chưa chắc chắn.

Câu kết luận: “Local frequency là baseline rất mạnh. Full-graph và degree controls cho thấy structure đáng phân tích, nhưng thêm structure chưa tạo improvement tổng thể ổn định trong đánh giá này. Đóng góp của đồ án là phép so sánh, phân tích lỗi và framework có thể kiểm tra lại, kể cả khi phương pháp phức tạp không thắng.”
