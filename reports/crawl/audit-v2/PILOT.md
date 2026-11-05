# Crawl pilot: MediaWiki API và HTML

Đây là dữ liệu tự thu thập từ Wikipedia, không tải một graph dataset có sẵn. Pilot kiểm tra acquisition/extraction; chưa đánh giá model recommendation.

Hoàn thành **20 trang**, 20 cặp API/HTML khớp revision, 0 historical revisions trước cutoff. 0 trang không có revision phù hợp cutoff được ghi nhận, không lấy bản hiện tại thay thế.

Raw captures: 42 responses, 3,979,415 bytes; API graph 1397 edges, HTML body graph 1049 edges, 1936 link occurrences. Có 1263 target nodes chưa crawl/resolve; không coi chúng là dangling nodes.

| Source | API targets | HTML body targets | Body Jaccard | All-context Jaccard |
|---|---:|---:|---:|---:|
| Alexandr Zhapozhnik | 8 | 6 | 0.7500 | 1.0000 |
| Estación Experimental Pavlovsk | 16 | 10 | 0.6250 | 0.8750 |
| Punta Whymper | 26 | 12 | 0.4615 | 0.8846 |
| Challenger de Porto Alegre 2014 (dobles masculino) | 39 | 32 | 0.8205 | 0.8718 |
| Maravedí | 113 | 103 | 0.9115 | 0.9735 |
| Daniel Peter | 17 | 9 | 0.5294 | 1.0000 |
| Mando Conjunto de Canarias | 18 | 16 | 0.8889 | 1.0000 |
| Fernando Arias-Salgado | 31 | 22 | 0.7097 | 1.0000 |
| Col rellena | 55 | 47 | 0.8545 | 0.9273 |
| Ruslana | 147 | 101 | 0.6871 | 0.8639 |
| Remora | 36 | 8 | 0.2222 | 0.8889 |
| Augusto Ferrando | 39 | 30 | 0.7692 | 0.9487 |
| Morella Zuleta | 35 | 31 | 0.8857 | 1.0000 |
| Radio Futuro | 62 | 31 | 0.5000 | 1.0000 |
| May It Be | 123 | 90 | 0.7317 | 0.8943 |
| Principio de Aufbau | 14 | 10 | 0.7143 | 1.0000 |
| Joseph Kabila | 86 | 45 | 0.5233 | 0.8721 |
| Medici: Masters of Florence | 154 | 121 | 0.7857 | 0.8636 |
| Las metamorfosis | 213 | 174 | 0.8169 | 0.9108 |
| Elecciones generales de Guatemala de 2015 | 165 | 151 | 0.9152 | 0.9333 |

API links và body links đo hai phạm vi khác nhau: infobox/reference/template links có thể bị loại khỏi body graph. Jaccard thấp không tự chứng minh scraper sai hoặc một graph tốt hơn cho recommendation. Equal article revision cũng không bảo đảm templates/cache hoàn toàn đồng thời.

Seed/config gốc nằm trong provenance.json; max_depth=0. Thiết kế chọn mẫu riêng phải được dẫn từ protocol của run; đây không phải representative corpus. Offline reparse: True; số trang đổi extraction: 20.

Xem [thiết kế tích hợp](../../../docs/CRAWLING_EXTENSION.md) cho hướng mở rộng và temporal safeguards. Raw HTML/wikitext ở data/raw (Git-ignored), graph/features ở data/processed (Git-ignored); report lưu counts, provenance và URLs. Không nhập current graph vào benchmark2018.
