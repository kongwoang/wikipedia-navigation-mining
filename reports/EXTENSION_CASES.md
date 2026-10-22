# Extension case studies

Chọn sau test theo extreme delta đã công bố, để kiểm tra failure mechanisms; không dùng cases để chọn model hoặc đại diện average effect. Full tables/rankings có trong portable payload.

## Tie-break gain lớn nhất trong ba windows: Strathclyde · 2018-09

Source `4339600`; 35 candidates; 1 observable future pairs. Train: 2018-05, 2018-06, 2018-07; validation 2018-08.

| Model | Full NDCG@10 |
| --- | --- |
| CycleRank | 0.0000 |
| M1_local | 0.0000 |
| M3_ppr_h | 0.5000 |
| M6B_fusion | 0.4307 |
| adaptive_fusion | 0.4307 |
| topology_tie | 0.4307 |

### M1_local

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Reino de Strathclyde | 22 | unobserved | 22.000000 |
| 2 | Hamilton (Escocia) | unobserved | unobserved | 0.000000 |
| 3 | Organización territorial de Escocia | unobserved | unobserved | 0.000000 |
| 4 | Autoridad unitaria | unobserved | unobserved | 0.000000 |
| 5 | West Dunbartonshire | unobserved | unobserved | 0.000000 |
| 6 | Siglo XI | unobserved | unobserved | 0.000000 |
| 7 | North Lanarkshire | unobserved | unobserved | 0.000000 |
| 8 | Partido Laborista (Reino Unido) | unobserved | unobserved | 0.000000 |
| 9 | East Kilbride | unobserved | unobserved | 0.000000 |
| 10 | Dumbarton | unobserved | unobserved | 0.000000 |

### topology_tie

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Reino de Strathclyde | 22 | unobserved | 35.000000 |
| 2 | Escocia | unobserved | unobserved | 34.000000 |
| 3 | Gaélico escocés | unobserved | unobserved | 33.000000 |
| 4 | Glasgow | unobserved | 19 | 32.000000 |
| 5 | Organización territorial de Escocia | unobserved | unobserved | 31.000000 |
| 6 | 1996 | unobserved | unobserved | 30.000000 |
| 7 | 1975 | unobserved | unobserved | 29.000000 |
| 8 | Renfrewshire | unobserved | unobserved | 28.000000 |
| 9 | South Lanarkshire | unobserved | unobserved | 27.000000 |
| 10 | Stirling | unobserved | unobserved | 26.000000 |

### M6B_fusion

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Reino de Strathclyde | 22 | unobserved | 0.756749 |
| 2 | Escocia | unobserved | unobserved | 0.009163 |
| 3 | Gaélico escocés | unobserved | unobserved | 0.008223 |
| 4 | Glasgow | unobserved | 19 | 0.008111 |
| 5 | Organización territorial de Escocia | unobserved | unobserved | 0.008075 |
| 6 | 1996 | unobserved | unobserved | 0.007731 |
| 7 | 1975 | unobserved | unobserved | 0.007429 |
| 8 | Renfrewshire | unobserved | unobserved | 0.007371 |
| 9 | South Lanarkshire | unobserved | unobserved | 0.007318 |
| 10 | Stirling | unobserved | unobserved | 0.007250 |

### adaptive_fusion

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Reino de Strathclyde | 22 | unobserved | 0.047941 |
| 2 | Escocia | unobserved | unobserved | 0.035863 |
| 3 | Gaélico escocés | unobserved | unobserved | 0.032184 |
| 4 | Glasgow | unobserved | 19 | 0.031746 |
| 5 | Organización territorial de Escocia | unobserved | unobserved | 0.031606 |
| 6 | 1996 | unobserved | unobserved | 0.030257 |
| 7 | 1975 | unobserved | unobserved | 0.029075 |
| 8 | Renfrewshire | unobserved | unobserved | 0.028848 |
| 9 | South Lanarkshire | unobserved | unobserved | 0.028643 |
| 10 | Stirling | unobserved | unobserved | 0.028376 |

Evidence: **Glasgow** có future count 19, published train count unobserved; Markov rank ngoài Top-10, tie-break rank 4, fusion rank 4.

Điểm cần đối chiếu: giữ nguyên các unequal positive counts ở tie-break; xem target hữu ích bị đưa ra/vào Top-10 trong nhóm equal-count. Với adaptive, đọc local count và kiểm tra thứ tự thay đổi; absence của count không phải negative label. Không suy nguyên nhân hành vi người đọc từ một ranking failure.

## Tie-break loss lớn nhất trong ba windows; đồng thời là adaptive failure lớn nhất: Emperador Alejandro · 2018-08

Source `4245731`; 19 candidates; 2 observable future pairs. Train: 2018-04, 2018-05, 2018-06; validation 2018-07.

| Model | Full NDCG@10 |
| --- | --- |
| CycleRank | 0.0000 |
| M1_local | 0.8822 |
| M3_ppr_h | 0.3145 |
| M6B_fusion | 0.8822 |
| adaptive_fusion | 0.3145 |
| topology_tie | 0.3145 |

### M1_local

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Alejandro Magno | unobserved | 12 | 18689.000000 |
| 2 | Período helenístico | unobserved | unobserved | 13104.000000 |
| 3 | Alejandría | unobserved | unobserved | 11435.000000 |
| 4 | Reino de Macedonia | unobserved | 10 | 9089.000000 |
| 5 | Alejandro III de Rusia | unobserved | unobserved | 6767.000000 |
| 6 | Alejandro II de Rusia | unobserved | unobserved | 5973.000000 |
| 7 | Alejandro I de Rusia | unobserved | unobserved | 5198.000000 |
| 8 | Zar | unobserved | unobserved | 4335.000000 |
| 9 | Emperador romano | unobserved | unobserved | 4201.000000 |
| 10 | Emperador | unobserved | unobserved | 3364.000000 |

### topology_tie

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Alejandro Severo | unobserved | unobserved | 19.000000 |
| 2 | Emperador romano | unobserved | unobserved | 18.000000 |
| 3 | Alejandro Magno | unobserved | 12 | 17.000000 |
| 4 | Alejandro II de Rusia | unobserved | unobserved | 16.000000 |
| 5 | Alejandro III de Rusia | unobserved | unobserved | 15.000000 |
| 6 | Domicio Alejandro | unobserved | unobserved | 14.000000 |
| 7 | Alejandro I de Rusia | unobserved | unobserved | 13.000000 |
| 8 | Zar | unobserved | unobserved | 12.000000 |
| 9 | Alejandro III (emperador de Bizancio) | unobserved | unobserved | 11.000000 |
| 10 | Emperador | unobserved | unobserved | 10.000000 |

### M6B_fusion

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Alejandro Magno | unobserved | 12 | 0.073641 |
| 2 | Período helenístico | unobserved | unobserved | 0.064575 |
| 3 | Alejandría | unobserved | unobserved | 0.062040 |
| 4 | Reino de Macedonia | unobserved | 10 | 0.058756 |
| 5 | Alejandro III de Rusia | unobserved | unobserved | 0.056295 |
| 6 | Alejandro II de Rusia | unobserved | unobserved | 0.055245 |
| 7 | Alejandro I de Rusia | unobserved | unobserved | 0.053866 |
| 8 | Emperador romano | unobserved | unobserved | 0.053210 |
| 9 | Zar | unobserved | unobserved | 0.052550 |
| 10 | Emperador | unobserved | unobserved | 0.050741 |

### adaptive_fusion

| Rank | Destination | Published train count | Future count | Score |
| --- | --- | --- | --- | --- |
| 1 | Alejandro Severo | unobserved | unobserved | 0.054487 |
| 2 | Emperador romano | unobserved | unobserved | 0.054104 |
| 3 | Alejandro Magno | unobserved | 12 | 0.053523 |
| 4 | Alejandro II de Rusia | unobserved | unobserved | 0.053415 |
| 5 | Alejandro III de Rusia | unobserved | unobserved | 0.053290 |
| 6 | Domicio Alejandro | unobserved | unobserved | 0.053188 |
| 7 | Alejandro I de Rusia | unobserved | unobserved | 0.053065 |
| 8 | Zar | unobserved | unobserved | 0.052968 |
| 9 | Alejandro III (emperador de Bizancio) | unobserved | unobserved | 0.052893 |
| 10 | Emperador | unobserved | unobserved | 0.052420 |

**Cơ chế chính:** source không có published eligible training mass. M1_local scores ở bảng là target global popularity, không source-specific click count. Tie-break/adaptive bỏ fallback popularity để dùng topology, làm giảm NDCG trong case này. Vì vậy failure này là khác biệt fallback policy, không phải đảo thứ tự positive local counts.

Evidence: **Alejandro Magno** có future count 12, published train count unobserved; Markov rank 1, tie-break rank 3, fusion rank 1.

Evidence: **Reino de Macedonia** có future count 10, published train count unobserved; Markov rank 4, tie-break rank ngoài Top-10, fusion rank 4.

Điểm cần đối chiếu: giữ nguyên các unequal positive counts ở tie-break; xem target hữu ích bị đưa ra/vào Top-10 trong nhóm equal-count. Với adaptive, đọc local count và kiểm tra thứ tự thay đổi; absence của count không phải negative label. Không suy nguyên nhân hành vi người đọc từ một ranking failure.
