# Case studies — bằng chứng từ predictions thật

Cases chọn theo protocol sau test để giải thích, không dùng tuning. Mọi bảng ở May 2018. “—” nghĩa không có published count; không phải reliable zero. Top-10 chỉ chứa shared historical candidates.

## Danza posmoderna — PPR_gain

ID `7754838`; out-degree **18**; full outgoing published training mass **62**.

Training chỉ quan sát Danza contemporánea (62). May có thêm Merce Cunningham (16); PPR đưa target này lên Top-10 trong khi tie-order của Markov không làm được. Đây là minh họa topology xếp hạng phần chưa có count, không chứng minh mọi rare source đều được lợi.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 0.6805 | 0.5000 |
| M3_ppr_h | 0.8764 | 1.0000 |
| M5H_node2vec | 0.0000 | 0.0000 |
| M6B_fusion | 0.8764 | 1.0000 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| Danza contemporánea | 62 | 44 | 73.33% | Có |
| Merce Cunningham | — | 16 | 26.67% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Danza contemporánea | 62 | 44 | 1.0000 |
| 2 | Posmodernidad | — | — | 0.0000 |
| 3 | Posestructuralismo | — | — | 0.0000 |
| 4 | Contact improvisación | — | — | 0.0000 |
| 5 | Videodanza | — | — | 0.0000 |
| 6 | Modernismo | — | — | 0.0000 |
| 7 | Bailarín | — | — | 0.0000 |
| 8 | Danza | — | — | 0.0000 |
| 9 | Deconstrucción | — | — | 0.0000 |
| 10 | Ironía | — | — | 0.0000 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Danza contemporánea | 62 | 44 | 0.0082 |
| 2 | Danza | — | — | 0.0081 |
| 3 | Bailarín | — | — | 0.0075 |
| 4 | Posmodernidad | — | — | 0.0073 |
| 5 | Merce Cunningham | — | 16 | 0.0073 |
| 6 | Alwin Nikolais | — | — | 0.0073 |
| 7 | Posestructuralismo | — | — | 0.0072 |
| 8 | Deconstrucción | — | — | 0.0072 |
| 9 | Roland Barthes | — | — | 0.0072 |
| 10 | Hiperrealidad | — | — | 0.0072 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Contact improvisación | — | — | 0.9735 |
| 2 | Posestructuralismo | — | — | 0.9249 |
| 3 | Hiperrealidad | — | — | 0.9157 |
| 4 | Ironía | — | — | 0.9121 |
| 5 | Deconstrucción | — | — | 0.8741 |
| 6 | Videodanza | — | — | 0.8588 |
| 7 | Trisha Brown | — | — | 0.8505 |
| 8 | Roland Barthes | — | — | 0.8365 |
| 9 | Duke University Press | — | — | 0.7711 |
| 10 | Posmodernidad | — | — | 0.7685 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Danza contemporánea | 62 | 44 | 0.5312 |
| 2 | Danza | — | — | 0.0311 |
| 3 | Bailarín | — | — | 0.0288 |
| 4 | Posmodernidad | — | — | 0.0278 |
| 5 | Merce Cunningham | — | 16 | 0.0277 |
| 6 | Alwin Nikolais | — | — | 0.0277 |
| 7 | Posestructuralismo | — | — | 0.0273 |
| 8 | Deconstrucción | — | — | 0.0273 |
| 9 | Roland Barthes | — | — | 0.0273 |
| 10 | Hiperrealidad | — | — | 0.0273 |

## Remora — Markov_gain

ID `2205329`; out-degree **12**; full outgoing published training mass **120**.

Remora remora có 63 training clicks và 31 May clicks, đứng đầu Markov. PPR ưu tiên Animalia/Pez và để target này ngoài Top-10. Pattern phù hợp giả thuyết hub bias; ta không có dữ liệu exposure để suy nguyên nhân hành vi.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 1.0000 | 1.0000 |
| M3_ppr_h | 0.0000 | 0.0000 |
| M5H_node2vec | 1.0000 | 1.0000 |
| M6B_fusion | 1.0000 | 1.0000 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| Remora remora | 63 | 31 | 100.00% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Remora remora | 63 | 31 | 0.5250 |
| 2 | Echeneidae | 42 | — | 0.3500 |
| 3 | Rémora | 15 | — | 0.1250 |
| 4 | Perciformes | — | — | 0.0000 |
| 5 | Acanthopterygii | — | — | 0.0000 |
| 6 | Pez | — | — | 0.0000 |
| 7 | Theodore Gill | — | — | 0.0000 |
| 8 | Animalia | — | — | 0.0000 |
| 9 | Actinopterygii | — | — | 0.0000 |
| 10 | Chordata | — | — | 0.0000 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Animalia | — | — | 0.0119 |
| 2 | Pez | — | — | 0.0118 |
| 3 | Echeneidae | 42 | — | 0.0118 |
| 4 | Chordata | — | — | 0.0117 |
| 5 | Actinopterygii | — | — | 0.0115 |
| 6 | Perciformes | — | — | 0.0114 |
| 7 | Carlos Linneo | — | — | 0.0111 |
| 8 | Acanthopterygii | — | — | 0.0110 |
| 9 | Georges Cuvier | — | — | 0.0108 |
| 10 | Theodore Gill | — | — | 0.0108 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Remora remora | 63 | 31 | 0.9744 |
| 2 | Rémora | 15 | — | 0.9605 |
| 3 | Actinopterygii | — | — | 0.9559 |
| 4 | Acanthopterygii | — | — | 0.9556 |
| 5 | Perciformes | — | — | 0.9545 |
| 6 | Echeneidae | 42 | — | 0.9539 |
| 7 | Georges Cuvier | — | — | 0.9066 |
| 8 | Animalia | — | — | 0.8683 |
| 9 | Chordata | — | — | 0.8610 |
| 10 | Pez | — | — | 0.8471 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Remora remora | 63 | 31 | 0.3024 |
| 2 | Echeneidae | 42 | — | 0.2185 |
| 3 | Rémora | 15 | — | 0.1019 |
| 4 | Animalia | — | — | 0.0442 |
| 5 | Pez | — | — | 0.0436 |
| 6 | Chordata | — | — | 0.0434 |
| 7 | Actinopterygii | — | — | 0.0424 |
| 8 | Perciformes | — | — | 0.0421 |
| 9 | Carlos Linneo | — | — | 0.0410 |
| 10 | Acanthopterygii | — | — | 0.0406 |

## Ultimate Avengers — Hybrid_gain

ID `4515299`; out-degree **30**; full outgoing published training mass **405**.

Ba destinations có training counts vẫn ở đầu fusion. Topology thay đổi phần đuôi chưa có count, giúp đưa thêm future targets vào Top-10. So bảng dưới để thấy gain không đến từ thay candidate set; đây là case được chọn vì gain lớn nhất, không phải average effect.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 0.7583 | 0.5000 |
| M3_ppr_h | 0.2981 | 0.5000 |
| M5H_node2vec | 0.3717 | 0.5000 |
| M6B_fusion | 0.8887 | 0.8333 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| Ultimate Avengers 2 | 287 | 284 | 51.54% | Có |
| The Ultimates (cómic) | 95 | 178 | 32.30% | Có |
| Next Avengers: Heroes of Tomorrow | 23 | 35 | 6.35% | Có |
| The Ultimates | — | 25 | 4.54% | Có |
| Henry Pym | — | 19 | 3.45% | Có |
| Betty Ross | — | 10 | 1.81% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Ultimate Avengers 2 | 287 | 284 | 0.7086 |
| 2 | The Ultimates (cómic) | 95 | 178 | 0.2346 |
| 3 | Next Avengers: Heroes of Tomorrow | 23 | 35 | 0.0568 |
| 4 | Mark Millar | — | — | 0.0000 |
| 5 | Cartoon Network | — | — | 0.0000 |
| 6 | Avispa (cómic) | — | — | 0.0000 |
| 7 | Grey DeLisle | — | — | 0.0000 |
| 8 | Lions Gate Entertainment | — | — | 0.0000 |
| 9 | Hulk | — | — | 0.0000 |
| 10 | Capitán América | — | — | 0.0000 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Marvel Comics | — | — | 0.0048 |
| 2 | Hulk | — | — | 0.0048 |
| 3 | Capitán América | — | — | 0.0047 |
| 4 | Iron Man | — | — | 0.0047 |
| 5 | Ultimate Avengers 2 | 287 | 284 | 0.0046 |
| 6 | Superhéroe | — | — | 0.0046 |
| 7 | Henry Pym | — | 19 | 0.0045 |
| 8 | The Ultimates | — | 25 | 0.0045 |
| 9 | Avispa (cómic) | — | — | 0.0045 |
| 10 | Viuda Negra (cómic) | — | — | 0.0045 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Grey DeLisle | — | — | 0.9796 |
| 2 | The Ultimates (cómic) | 95 | 178 | 0.9694 |
| 3 | Película de animación | — | — | 0.9677 |
| 4 | Ultimate Thor | — | — | 0.9611 |
| 5 | Ultimate Nick Fury | — | — | 0.9573 |
| 6 | Directamente para video | — | — | 0.9557 |
| 7 | Marvel Studios | — | — | 0.9545 |
| 8 | Henry Pym | — | 19 | 0.9541 |
| 9 | Avispa (cómic) | — | — | 0.9495 |
| 10 | Next Avengers: Heroes of Tomorrow | 23 | 35 | 0.9398 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Ultimate Avengers 2 | 287 | 284 | 0.3716 |
| 2 | The Ultimates (cómic) | 95 | 178 | 0.1337 |
| 3 | Next Avengers: Heroes of Tomorrow | 23 | 35 | 0.0449 |
| 4 | Marvel Comics | — | — | 0.0181 |
| 5 | Hulk | — | — | 0.0179 |
| 6 | Capitán América | — | — | 0.0178 |
| 7 | Iron Man | — | — | 0.0176 |
| 8 | Superhéroe | — | — | 0.0171 |
| 9 | Henry Pym | — | 19 | 0.0171 |
| 10 | The Ultimates | — | 25 | 0.0170 |

## Tragacete — Hybrid_failure

ID `119152`; out-degree **18**; full outgoing published training mass **91**.

Fusion giữ ba vị trí đầu như Markov nhưng thay phần đuôi: Parque Cinegético Experimental de El Hosquillo có 12 future clicks và không có published training count. Topology có thể đẩy một candidate hữu ích xuống dưới Top-10; đây là lý do không giả định fusion luôn thắng.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 0.8616 | 1.0000 |
| M3_ppr_h | 0.3140 | 0.6667 |
| M5H_node2vec | 0.9079 | 1.0000 |
| M6B_fusion | 0.7353 | 0.6667 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| Río Cuervo | 68 | 26 | 54.17% | Có |
| Parque Cinegético Experimental de El Hosquillo | — | 12 | 25.00% | Có |
| Parque natural Serranía de Cuenca | 11 | 10 | 20.83% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Río Cuervo | 68 | 26 | 0.7473 |
| 2 | Serranía Alta | 12 | — | 0.1319 |
| 3 | Parque natural Serranía de Cuenca | 11 | 10 | 0.1209 |
| 4 | Instituto Nacional de Estadística (España) | — | — | 0.0000 |
| 5 | Cañada real | — | — | 0.0000 |
| 6 | Municipio (España) | — | — | 0.0000 |
| 7 | Ciudad Encantada | — | — | 0.0000 |
| 8 | Comunidad autónoma | — | — | 0.0000 |
| 9 | Parque Cinegético Experimental de El Hosquillo | — | 12 | 0.0000 |
| 10 | Tajo | — | — | 0.0000 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Provincia de Cuenca | — | — | 0.0079 |
| 2 | España | — | — | 0.0077 |
| 3 | Cuenca (España) | — | — | 0.0075 |
| 4 | Castilla-La Mancha | — | — | 0.0074 |
| 5 | Parque natural Serranía de Cuenca | 11 | 10 | 0.0074 |
| 6 | Instituto Nacional de Estadística (España) | — | — | 0.0074 |
| 7 | Tajo | — | — | 0.0074 |
| 8 | Ciudad Encantada | — | — | 0.0073 |
| 9 | Río Cuervo | 68 | 26 | 0.0072 |
| 10 | Júcar | — | — | 0.0072 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Río Cuervo | 68 | 26 | 0.9669 |
| 2 | Parque natural Serranía de Cuenca | 11 | 10 | 0.9321 |
| 3 | Provincia de Cuenca | — | — | 0.8836 |
| 4 | Serranía Alta | 12 | — | 0.8618 |
| 5 | Júcar | — | — | 0.8378 |
| 6 | Tajo | — | — | 0.8002 |
| 7 | Cañada real | — | — | 0.7807 |
| 8 | Cuenca (España) | — | — | 0.7678 |
| 9 | Teruel | — | — | 0.7501 |
| 10 | Parque Cinegético Experimental de El Hosquillo | — | 12 | 0.7237 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Río Cuervo | 68 | 26 | 0.4011 |
| 2 | Serranía Alta | 12 | — | 0.0930 |
| 3 | Parque natural Serranía de Cuenca | 11 | 10 | 0.0885 |
| 4 | Provincia de Cuenca | — | — | 0.0300 |
| 5 | España | — | — | 0.0293 |
| 6 | Cuenca (España) | — | — | 0.0285 |
| 7 | Castilla-La Mancha | — | — | 0.0282 |
| 8 | Instituto Nacional de Estadística (España) | — | — | 0.0280 |
| 9 | Tajo | — | — | 0.0280 |
| 10 | Ciudad Encantada | — | — | 0.0276 |

## 1944 — Many_links

ID `9972`; out-degree **485**; full outgoing published training mass **1247**.

1944 có 485 candidates, tạo nhiều cạnh tranh ở Top-10. Các future destinations 1945/1947/1943 không thuộc historical candidate set. Full metrics giữ những labels này; score thấp hơn không hoàn toàn do ranker. PPR ưu tiên các country hubs trong khi local counts giữ các destinations cụ thể.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 0.7118 | 0.3913 |
| M3_ppr_h | 0.1301 | 0.0435 |
| M5H_node2vec | 0.1097 | 0.0870 |
| M6B_fusion | 0.7159 | 0.3913 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| 1945 | 390 | 147 | 25.70% | Không |
| 1947 | 91 | 57 | 9.97% | Không |
| Segunda Guerra Mundial | 51 | 33 | 5.77% | Có |
| 1943 | 87 | 33 | 5.77% | Không |
| 1941 | 76 | 31 | 5.42% | Không |
| Premio Nobel | 20 | 27 | 4.72% | Có |
| 1946 | 54 | 20 | 3.50% | Không |
| Grupo de Ejércitos H | 16 | 19 | 3.32% | Có |
| Día D | 48 | 19 | 3.32% | Có |
| Accidente ferroviario de Torre del Bierzo de 1944 | 51 | 19 | 3.32% | Có |
| Claus von Stauffenberg | 52 | 18 | 3.15% | Có |
| Terremoto de San Juan de 1944 | — | 16 | 2.80% | Có |
| Constitución de la Unión Soviética | — | 15 | 2.62% | Có |
| Siglo XX | — | 14 | 2.45% | Không |
| Calendario gregoriano | 38 | 14 | 2.45% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Claus von Stauffenberg | 52 | 18 | 0.0974 |
| 2 | Accidente ferroviario de Torre del Bierzo de 1944 | 51 | 19 | 0.0955 |
| 3 | Segunda Guerra Mundial | 51 | 33 | 0.0955 |
| 4 | Día D | 48 | 19 | 0.0899 |
| 5 | Calendario gregoriano | 38 | 14 | 0.0712 |
| 6 | Batalla de Monte Castello | 32 | 13 | 0.0599 |
| 7 | Auschwitz | 25 | — | 0.0468 |
| 8 | Batalla de Eniwetok | 24 | 12 | 0.0449 |
| 9 | Operación Cobra | 23 | 10 | 0.0431 |
| 10 | Operación Bagration | 21 | 13 | 0.0393 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Estados Unidos | — | — | 0.0005 |
| 2 | Segunda Guerra Mundial | 51 | 33 | 0.0005 |
| 3 | España | — | — | 0.0004 |
| 4 | Reino Unido | — | — | 0.0004 |
| 5 | Francia | — | — | 0.0004 |
| 6 | Argentina | — | — | 0.0004 |
| 7 | Alemania | — | — | 0.0004 |
| 8 | Unión Soviética | — | — | 0.0003 |
| 9 | Londres | — | — | 0.0003 |
| 10 | París | — | — | 0.0003 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Wolfram von Richthofen | — | — | 0.7987 |
| 2 | Días de gloria | — | — | 0.7711 |
| 3 | Tōru Emori | — | — | 0.7616 |
| 4 | Reinhold Messner | — | — | 0.7579 |
| 5 | Batalla de Monte Castello | 32 | 13 | 0.7568 |
| 6 | Gaslight | — | — | 0.7506 |
| 7 | Batalla de Eniwetok | 24 | 12 | 0.7478 |
| 8 | Alfred Hitchcock | — | — | 0.7465 |
| 9 | 2.ª División Blindada (Francia) | — | — | 0.7359 |
| 10 | Mischa Hillesum | — | — | 0.7344 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Claus von Stauffenberg | 52 | 18 | 0.0497 |
| 2 | Segunda Guerra Mundial | 51 | 33 | 0.0495 |
| 3 | Accidente ferroviario de Torre del Bierzo de 1944 | 51 | 19 | 0.0488 |
| 4 | Día D | 48 | 19 | 0.0460 |
| 5 | Calendario gregoriano | 38 | 14 | 0.0367 |
| 6 | Batalla de Monte Castello | 32 | 13 | 0.0310 |
| 7 | Auschwitz | 25 | — | 0.0244 |
| 8 | Batalla de Eniwetok | 24 | 12 | 0.0235 |
| 9 | Operación Cobra | 23 | 10 | 0.0225 |
| 10 | Operación Bagration | 21 | 13 | 0.0207 |

## Repollo relleno — Low_traffic

ID `1875596`; out-degree **36**; full outgoing published training mass **10**.

Chỉ 10 published training clicks đến Gołąbki; May quan sát Dolma (15), chưa thấy trong training. Markov/PPR/fusion đều miss Top-10, embedding-H tìm được Dolma. Chọn source vì low traffic, không đổi knobs riêng cho case.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 0.0000 | 0.0000 |
| M3_ppr_h | 0.0000 | 0.0000 |
| M5H_node2vec | 0.3562 | 1.0000 |
| M6B_fusion | 0.0000 | 0.0000 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| Dolma | — | 15 | 100.00% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Gołąbki | 10 | — | 1.0000 |
| 2 | Vitis | — | — | 0.0000 |
| 3 | Cebada | — | — | 0.0000 |
| 4 | Raíz alimenticia | — | — | 0.0000 |
| 5 | Salsa de tomate | — | — | 0.0000 |
| 6 | Kasha | — | — | 0.0000 |
| 7 | Crema agria | — | — | 0.0000 |
| 8 | Especia | — | — | 0.0000 |
| 9 | Salsa (gastronomía) | — | — | 0.0000 |
| 10 | Seta comestible | — | — | 0.0000 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Carne | — | — | 0.0049 |
| 2 | Cereal | — | — | 0.0044 |
| 3 | Yogur | — | — | 0.0043 |
| 4 | Arroz | — | — | 0.0040 |
| 5 | Allium cepa | — | — | 0.0039 |
| 6 | Verdura | — | — | 0.0038 |
| 7 | Carne de cerdo | — | — | 0.0038 |
| 8 | Especia | — | — | 0.0037 |
| 9 | Allium sativum | — | — | 0.0037 |
| 10 | Carne de cordero | — | — | 0.0037 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Gołąbki | 10 | — | 0.9743 |
| 2 | Salsa de tomate | — | — | 0.9513 |
| 3 | Vinagreta | — | — | 0.9506 |
| 4 | Mermelada de arándano rojo | — | — | 0.9376 |
| 5 | Grano integral | — | — | 0.9363 |
| 6 | Dolma | — | 15 | 0.9319 |
| 7 | Carne de buey | — | — | 0.9291 |
| 8 | Crema agria | — | — | 0.9274 |
| 9 | Raíz alimenticia | — | — | 0.9269 |
| 10 | Sarma | — | — | 0.9251 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Gołąbki | 10 | — | 0.5132 |
| 2 | Carne | — | — | 0.0183 |
| 3 | Cereal | — | — | 0.0164 |
| 4 | Yogur | — | — | 0.0159 |
| 5 | Arroz | — | — | 0.0151 |
| 6 | Allium cepa | — | — | 0.0145 |
| 7 | Verdura | — | — | 0.0143 |
| 8 | Carne de cerdo | — | — | 0.0143 |
| 9 | Especia | — | — | 0.0140 |
| 10 | Allium sativum | — | — | 0.0139 |

## Th1 — Fixed_hash_example

ID `7145962`; out-degree **22**; full outgoing published training mass **410**.

Th1 là case chọn bằng stable hash, tránh chỉ kể extreme wins. Markov/fusion giữ các targets có training counts; thứ tự May khác training ở IL-2 và Linfocito T CD4+. Improvement nhỏ ở đây không đủ chứng minh gain ổn định.

| Model | Full NDCG@10 | Recall@10 |
| --- | --- | --- |
| M1B_backoff | 0.8923 | 0.7778 |
| M3_ppr_h | 0.3854 | 0.4444 |
| M5H_node2vec | 0.5206 | 0.6667 |
| M6B_fusion | 0.8973 | 0.7778 |

### Future distribution (tối đa 15 targets lớn nhất)

| Target | Train count | Future count | Future share | Candidate |
| --- | --- | --- | --- | --- |
| Th2 | 160 | 106 | 27.46% | Có |
| Linfocito T CD4+ | 53 | 71 | 18.39% | Có |
| IL-2 | 90 | 60 | 15.54% | Có |
| Th17 | 48 | 49 | 12.69% | Có |
| Interleucina-12 | 46 | 39 | 10.10% | Có |
| Factor de necrosis tumoral | 13 | 21 | 5.44% | Có |
| Complejo mayor de histocompatibilidad | — | 17 | 4.40% | Có |
| Citocina | — | 13 | 3.37% | Có |
| Célula presentadora de antígeno | — | 10 | 2.59% | Có |

### M1B_backoff — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Th2 | 160 | 106 | 0.3902 |
| 2 | IL-2 | 90 | 60 | 0.2195 |
| 3 | Linfocito T CD4+ | 53 | 71 | 0.1293 |
| 4 | Th17 | 48 | 49 | 0.1171 |
| 5 | Interleucina-12 | 46 | 39 | 0.1122 |
| 6 | Factor de necrosis tumoral | 13 | 21 | 0.0317 |
| 7 | Célula presentadora de antígeno | — | 10 | 0.0000 |
| 8 | Linfocito T | — | — | 0.0000 |
| 9 | Virus | — | — | 0.0000 |
| 10 | Óxido de nitrógeno (II) | — | — | 0.0000 |

### M3_ppr_h — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Citocina | — | 13 | 0.0077 |
| 2 | Macrófago | — | — | 0.0072 |
| 3 | Linfocito T | — | — | 0.0067 |
| 4 | Antígeno | — | — | 0.0067 |
| 5 | Virus | — | — | 0.0066 |
| 6 | Linfocito T CD4+ | 53 | 71 | 0.0066 |
| 7 | Interleucina-12 | 46 | 39 | 0.0064 |
| 8 | Factor de transcripción | — | — | 0.0064 |
| 9 | Célula dendrítica | — | — | 0.0063 |
| 10 | Complejo mayor de histocompatibilidad | — | 17 | 0.0063 |

### M5H_node2vec — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Interleucina-18 | — | — | 0.9885 |
| 2 | Célula NK | — | — | 0.9853 |
| 3 | Th2 | 160 | 106 | 0.9829 |
| 4 | Th17 | 48 | 49 | 0.9793 |
| 5 | Complejo mayor de histocompatibilidad | — | 17 | 0.9783 |
| 6 | Mycobacterium | — | — | 0.9757 |
| 7 | Interleucina-12 | 46 | 39 | 0.9735 |
| 8 | Linfocito T CD4+ | 53 | 71 | 0.9703 |
| 9 | Célula dendrítica | — | — | 0.9696 |
| 10 | Célula presentadora de antígeno | — | 10 | 0.9660 |

### M6B_fusion — Top-10

| Rank | Target | Train | Future | Score |
| --- | --- | --- | --- | --- |
| 1 | Th2 | 160 | 106 | 0.2168 |
| 2 | IL-2 | 90 | 60 | 0.1306 |
| 3 | Linfocito T CD4+ | 53 | 71 | 0.0882 |
| 4 | Th17 | 48 | 49 | 0.0803 |
| 5 | Interleucina-12 | 46 | 39 | 0.0791 |
| 6 | Factor de necrosis tumoral | 13 | 21 | 0.0382 |
| 7 | Citocina | — | 13 | 0.0278 |
| 8 | Macrófago | — | — | 0.0260 |
| 9 | Linfocito T | — | — | 0.0241 |
| 10 | Antígeno | — | — | 0.0240 |

Các raw scores không cùng scale giữa các model. Chỉ M6B trộn sau candidate normalization. [Demo](generated/demo.html) cho phép đổi month/model/denominator; trên GitHub cần tải HTML về rồi mở.
