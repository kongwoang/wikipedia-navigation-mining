# Bảng kết quả từ frozen study-v3

Sinh bằng `python3 scripts/build_report_tables.py`. Số làm tròn 4 chữ số trong bảng chính; CSV giữ precision gốc. Không dùng bảng test để chọn hyperparameters.

## 2018-05 — full observable, macro

| Model | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 |
| --- | --- | --- | --- | --- | --- |
| M0_global | 0.1310 | 0.2818 | 0.5135 | 0.2436 | 0.2008 |
| M1_local | 0.6436 | 0.7748 | 0.8658 | 0.9539 | 0.8991 |
| M1B_backoff | 0.6436 | 0.7748 | 0.8658 | 0.9539 | 0.8991 |
| M2_uniform | 0.1825 | 0.3547 | 0.5677 | 0.3463 | 0.2518 |
| M2D_indegree | 0.0959 | 0.1964 | 0.4336 | 0.1506 | 0.1321 |
| M3_ppr_h | 0.2314 | 0.4122 | 0.6123 | 0.4161 | 0.3126 |
| M4C_ppr_c | 0.6496 | 0.7816 | 0.8734 | 0.9539 | 0.9018 |
| M4CH_ppr_ch | 0.6496 | 0.7807 | 0.8710 | 0.9539 | 0.9009 |
| M4H_ppr_wh | 0.6594 | 0.7827 | 0.8698 | 0.9543 | 0.9039 |
| M6B_fusion | 0.6516 | 0.7811 | 0.8602 | 0.9541 | 0.9034 |
| M6A_matrix | 0.6440 | 0.7721 | 0.8643 | 0.9535 | 0.8936 |
| HITS | 0.1228 | 0.2138 | 0.4382 | 0.1553 | 0.1401 |
| M5H_node2vec | 0.3301 | 0.5457 | 0.7153 | 0.5582 | 0.4510 |
| M5W_node2vec | 0.4779 | 0.6462 | 0.7731 | 0.8032 | 0.6719 |

## 2018-06 — full observable, macro

| Model | recall@5 | recall@10 | recall@20 | mrr@10 | ndcg@10 |
| --- | --- | --- | --- | --- | --- |
| M0_global | 0.1300 | 0.2947 | 0.5047 | 0.2238 | 0.1964 |
| M1_local | 0.6437 | 0.7665 | 0.8605 | 0.9508 | 0.8899 |
| M1B_backoff | 0.6437 | 0.7665 | 0.8605 | 0.9508 | 0.8899 |
| M2_uniform | 0.1716 | 0.3338 | 0.5441 | 0.3282 | 0.2379 |
| M2D_indegree | 0.0876 | 0.1995 | 0.4202 | 0.1468 | 0.1272 |
| M3_ppr_h | 0.2247 | 0.3954 | 0.6139 | 0.4144 | 0.3055 |
| M4C_ppr_c | 0.6441 | 0.7679 | 0.8677 | 0.9508 | 0.8899 |
| M4CH_ppr_ch | 0.6441 | 0.7686 | 0.8677 | 0.9508 | 0.8893 |
| M4H_ppr_wh | 0.6473 | 0.7723 | 0.8639 | 0.9467 | 0.8914 |
| M6B_fusion | 0.6440 | 0.7778 | 0.8689 | 0.9518 | 0.8936 |
| M6A_matrix | 0.6404 | 0.7646 | 0.8565 | 0.9467 | 0.8830 |
| HITS | 0.1092 | 0.2159 | 0.4322 | 0.1484 | 0.1341 |
| M5H_node2vec | 0.3514 | 0.5157 | 0.6882 | 0.5380 | 0.4404 |
| M5W_node2vec | 0.5076 | 0.6616 | 0.7625 | 0.8172 | 0.6861 |

## Denominator và traffic weighting — NDCG@10

Conditional traffic-weighted dùng **full source label mass** để cân nguồn; chỉ nguồn có eligible label được đưa vào conditional average.

| Tháng | Model | Full macro | Conditional macro | Full weighted | Conditional weighted |
| --- | --- | --- | --- | --- | --- |
| 2018-05 | M1B_backoff | 0.8991 | 0.9259 | 0.9597 | 0.9710 |
| 2018-05 | M3_ppr_h | 0.3126 | 0.3220 | 0.3883 | 0.3924 |
| 2018-05 | M4H_ppr_wh | 0.9039 | 0.9310 | 0.9609 | 0.9723 |
| 2018-05 | M6B_fusion | 0.9034 | 0.9305 | 0.9617 | 0.9731 |
| 2018-05 | M5H_node2vec | 0.4510 | 0.4639 | 0.4674 | 0.4721 |
| 2018-05 | M5W_node2vec | 0.6719 | 0.6912 | 0.7324 | 0.7411 |
| 2018-06 | M1B_backoff | 0.8899 | 0.9314 | 0.9251 | 0.9391 |
| 2018-06 | M3_ppr_h | 0.3055 | 0.3186 | 0.3503 | 0.3550 |
| 2018-06 | M4H_ppr_wh | 0.8914 | 0.9330 | 0.9246 | 0.9386 |
| 2018-06 | M6B_fusion | 0.8936 | 0.9352 | 0.9178 | 0.9319 |
| 2018-06 | M5H_node2vec | 0.4404 | 0.4619 | 0.4545 | 0.4613 |
| 2018-06 | M5W_node2vec | 0.6861 | 0.7178 | 0.7294 | 0.7399 |

## Primary contrast — số nguồn thắng/hòa/thua

M6B−M1B, full NDCG@10; tie tolerance 1e-12, chỉ nguồn có observed labels.

| Tháng | N | Thắng | Hòa | Thua |
| --- | --- | --- | --- | --- |
| 2018-05 | 127 | 18 | 95 | 14 |
| 2018-06 | 122 | 17 | 93 | 12 |

## Paired source bootstrap

| month | contrast | delta | ci_low | ci_high | sources |
| --- | --- | --- | --- | --- | --- |
| 2018-05 | A4_WH - A4_H | 0.6084672159072654 | 0.5625143474374096 | 0.6527629703592565 | 127 |
| 2018-05 | A5_weighted_matched - M5H_node2vec | 0.21423255289455606 | 0.16678017220371422 | 0.25930924874834466 | 127 |
| 2018-05 | M3_ppr_h - M1B_backoff | -0.5864785100876931 | -0.6312993307563715 | -0.539853762293471 | 127 |
| 2018-05 | M6B_fusion - M1B_backoff | 0.0042937389686346205 | -0.0007576595419197886 | 0.010351920091248112 | 127 |
| 2018-06 | A4_WH - A4_H | 0.6078268042545804 | 0.5572547640561242 | 0.6552776174919204 | 122 |
| 2018-06 | A5_weighted_matched - M5H_node2vec | 0.2338485836996559 | 0.18218631697036847 | 0.2826507390236943 | 122 |
| 2018-06 | M3_ppr_h - M1B_backoff | -0.5844077235602734 | -0.6300844345108768 | -0.5360708571040942 | 122 |
| 2018-06 | M6B_fusion - M1B_backoff | 0.0037297810994734336 | -0.0001937516873340616 | 0.009946713010666432 | 122 |

## A8 — trailing history, full macro NDCG@10

| Tháng | Model | 1 tháng | 2 tháng | 3 tháng |
| --- | --- | --- | --- | --- |
| 2018-05 | Markov | 0.8338 | 0.8641 | 0.8991 |
| 2018-05 | Backoff | 0.8338 | 0.8641 | 0.8991 |
| 2018-05 | Fusion | 0.8358 | 0.8647 | 0.9034 |
| 2018-06 | Markov | 0.8381 | 0.8751 | 0.8899 |
| 2018-06 | Backoff | 0.8381 | 0.8751 | 0.8899 |
| 2018-06 | Fusion | 0.8448 | 0.8800 | 0.8936 |

## A7 — train-unobserved transitions, original rankings

Tập con được xác định bằng train counts; không rerank sau khi biết future labels. Missing train counts có thể do suppression.

| Tháng | Model | Sources | Pairs | Mass | Macro Recall@10 | Mass Recall@10 |
| --- | --- | --- | --- | --- | --- | --- |
| 2018-05 | M1B_backoff | 53 | 117 | 2020 | 0.0912 | 0.0416 |
| 2018-05 | M3_ppr_h | 53 | 117 | 2020 | 0.2335 | 0.1629 |
| 2018-05 | M6B_fusion | 53 | 117 | 2020 | 0.0991 | 0.0861 |
| 2018-05 | M5H_node2vec | 53 | 117 | 2020 | 0.2193 | 0.1426 |
| 2018-05 | M5W_node2vec | 53 | 117 | 2020 | 0.1876 | 0.1450 |
| 2018-06 | M1B_backoff | 39 | 334 | 10061 | 0.0131 | 0.0118 |
| 2018-06 | M3_ppr_h | 39 | 334 | 10061 | 0.1606 | 0.0219 |
| 2018-06 | M6B_fusion | 39 | 334 | 10061 | 0.0771 | 0.0084 |
| 2018-06 | M5H_node2vec | 39 | 334 | 10061 | 0.1117 | 0.0358 |
| 2018-06 | M5W_node2vec | 39 | 334 | 10061 | 0.1432 | 0.0410 |

## Seed variability — auxiliary, không phải source CI

| month | model | seeds | mean | std_sample | min | max |
| --- | --- | --- | --- | --- | --- | --- |
| 2018-05 | M5H_node2vec | 17,29,43 | 0.43708113868528625 | 0.012759757087649285 | 0.4259278590677604 | 0.4509953240720822 |
| 2018-05 | M5W_node2vec | 17,29,43 | 0.674183343627362 | 0.01054160129229492 | 0.6649577769418148 | 0.685673048323736 |
| 2018-06 | M5H_node2vec | 17,29,43 | 0.4380234359029811 | 0.0022058428481019827 | 0.4360135252806763 | 0.4403833587924476 |
| 2018-06 | M5W_node2vec | 17,29,43 | 0.6851625818463095 | 0.0025752255606022014 | 0.6822587892306071 | 0.6871692556065893 |

## Coverage

| month | queries | q_all | q_conditional | label_pairs | label_mass | eligible_pairs | eligible_mass | mass_candidate_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2018-05 | 200 | 127 | 126 | 1172 | 62768 | 1089 | 59966 | 0.9553594188121336 |
| 2018-06 | 200 | 122 | 119 | 1277 | 63809 | 1167 | 60025 | 0.9406980206553934 |

## Nhóm nguồn theo traffic — observability

| Tháng | Nhóm | Sampled | Observed | Conditional | Future mass |
| --- | --- | --- | --- | --- | --- |
| 2018-05 | cold | 50 | 0 | 0 | 0 |
| 2018-05 | high_>=1000 | 50 | 50 | 50 | 54793 |
| 2018-05 | low_<100 | 50 | 29 | 28 | 805 |
| 2018-05 | mid_<1000 | 50 | 48 | 48 | 7170 |
| 2018-06 | cold | 50 | 1 | 1 | 12 |
| 2018-06 | high_>=1000 | 50 | 49 | 49 | 46786 |
| 2018-06 | low_<100 | 50 | 24 | 22 | 552 |
| 2018-06 | mid_<1000 | 50 | 48 | 47 | 16459 |

## Selected configurations

| model | parameters |
| --- | --- |
| A4_CH | {"damping": 0.5, "mode": "CH", "mu": 100.0} |
| A4_H | {"damping": 0.5, "mode": "H", "mu": 100.0} |
| A4_WH | {"damping": 0.5, "mode": "WH", "mu": 100.0} |
| A5_weighted_matched | {"dimension": 32, "p": 0.5, "q": 2.0, "seed": 17} |
| A8_M1B_backoff_1month | {"eta": 0.0, "months": ["2018-03"], "mu": 0.0} |
| A8_M1B_backoff_2month | {"eta": 0.0, "months": ["2018-02", "2018-03"], "mu": 0.0} |
| A8_M1_local_1month | {"months": ["2018-03"]} |
| A8_M1_local_2month | {"months": ["2018-02", "2018-03"]} |
| A8_fusion_1month | {"eta": 0.0, "months": ["2018-03"], "mu": 0.0} |
| A8_fusion_2month | {"eta": 0.0, "months": ["2018-02", "2018-03"], "mu": 0.0} |
| HITS | {} |
| M0_global | {} |
| M1B_backoff | {"eta": 0.0, "mu": 0.0} |
| M1_local | {} |
| M2D_indegree | {} |
| M2_uniform | {} |
| M3_ppr_h | {"damping": 0.15, "mode": "H", "mu": 100.0} |
| M4CH_ppr_ch | {"damping": 0.15, "mode": "CH", "mu": 100.0} |
| M4C_ppr_c | {"damping": 0.15, "mode": "C", "mu": 100.0} |
| M4H_ppr_wh | {"damping": 0.15, "mode": "WH", "mu": 100.0} |
| M5H_node2vec | {"dimension": 32, "p": 0.5, "q": 2.0, "seed": 17} |
| M5H_node2vec_s29 | {"dimension": 32, "p": 0.5, "q": 2.0, "seed": 29} |
| M5H_node2vec_s43 | {"dimension": 32, "p": 0.5, "q": 2.0, "seed": 43} |
| M5W_node2vec | {"dimension": 64, "p": 0.5, "q": 2.0, "seed": 17} |
| M5W_node2vec_s29 | {"dimension": 64, "p": 0.5, "q": 2.0, "seed": 29} |
| M5W_node2vec_s43 | {"dimension": 64, "p": 0.5, "q": 2.0, "seed": 43} |
| M6A_matrix | {"damping": 0.5, "lambda": 0.75} |
| M6B_fusion | {"lambda": 0.5} |


Bảng runtime, subgroup intervals, graph statistics, training distributions và toàn bộ metrics nằm trong [generated/tables](generated/tables/).
