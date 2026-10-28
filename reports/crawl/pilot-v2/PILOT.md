# Crawl pilot: MediaWiki API và HTML

Đây là dữ liệu tự thu thập từ Wikipedia, không tải một graph dataset có sẵn. Pilot kiểm tra acquisition/extraction; chưa đánh giá model recommendation.

Hoàn thành **8 trang**, 8 cặp API/HTML khớp revision, 6 historical revisions trước cutoff. 2 trang không có revision phù hợp cutoff được ghi nhận, không lấy bản hiện tại thay thế.

Raw captures: 26 responses, 1,423,505 bytes; API graph 654 edges, HTML body graph 556 edges, 1028 link occurrences. Có 567 target nodes chưa crawl/resolve; không coi chúng là dangling nodes.

| Source | API targets | HTML body targets | Body Jaccard | All-context Jaccard |
|---|---:|---:|---:|---:|
| Tag Team Championship | 191 | 186 | 0.9738 | 0.9843 |
| Zapoteca | 8 | 8 | 1.0000 | 1.0000 |
| Ruslana | 147 | 102 | 0.6939 | 0.8639 |
| Municipio de Cumberland (condado de Adams) | 33 | 13 | 0.3939 | 1.0000 |
| Hotel, dulce hotel | 22 | 10 | 0.4545 | 0.9545 |
| 2 Cold Scorpio | 62 | 51 | 0.8226 | 0.9516 |
| AEW Women's World Tag Team Championship | 50 | 49 | 0.9600 | 1.0000 |
| AEW World Tag Team Championship | 141 | 139 | 0.9787 | 1.0000 |

API links và body links đo hai phạm vi khác nhau: infobox/reference/template links có thể bị loại khỏi body graph. Jaccard thấp không tự chứng minh scraper sai hoặc một graph tốt hơn cho recommendation. Equal article revision cũng không bảo đảm templates/cache hoàn toàn đồng thời.

Seed sampling: năm nguồn từ original train-defined panel, thứ tự SHA256(`crawl-pilot-v1:` + source ID), rồi depth1 BFS deterministic. Frontier thiên về wrestling vì seed đầu có nhiều links và budget nhỏ; đây là pilot kỹ thuật, không representative corpus.

Xem [thiết kế tích hợp](../../../docs/CRAWLING_EXTENSION.md) cho hướng mở rộng và temporal safeguards. Raw HTML/wikitext ở data/raw (Git-ignored), graph/features ở data/processed (Git-ignored); report lưu counts, provenance và URLs. Không nhập current graph vào benchmark2018.
