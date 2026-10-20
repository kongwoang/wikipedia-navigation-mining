# Literature review và định vị học thuật

Kiểm tra nguồn ngày **20/10/2026**. Ưu tiên full text của tác giả, publisher và dataset repository. Năm publication được phân biệt với arXiv submission, upload date hay search-engine crawl date. Đây là focused review, không tuyên bố systematic review đầy đủ.

## 1. Literature comparison matrix

Các liên kết L1–L11 bên dưới dẫn tới nguồn sơ cấp. “Khác dự án” là phân tích của nhóm, không phải claim của tác giả.

| Paper | Năm | Dataset | Task | Algorithms | Metrics / đánh giá đã xác minh | Main contribution | Khác dự án |
|---|---:|---|---|---|---|---|---|
| L1 Wikipedia Reader Navigation: When Synthetic Data Is Enough | 2022 | Real private logs và public/private click-derived walks, 8 editions | So synthetic với real; next-article và downstream tasks | Random walks, Markov order 2 cho next-article, representations | MRR next-article; semantic Spearman; topic F1 | Kiểm tra synthetic data như approximation | Ta không có real sessions; temporal source-only ranking |
| L2 What Makes a Link Successful on Wikipedia? | 2017; preprint 2016 | English hyperlink/HTML và February 2015 transitions | Giải thích link use, Markov hypotheses, global navigation popularity | Hurdle mixed-effects, Bayesian Markov priors, weighted PageRank | Model evidence; Spearman với inbound transitions | Kết nối link properties và navigation | Không cùng next-month PPR candidate-ranking protocol |
| L3 CycleRank, or there and back again: personalized relevance scores from cyclic paths on directed graphs | 2020 | Wikipedia link graph, February 2018 Clickstream và See-Also | Source-conditioned relevance | CycleRank, PPR và graph-ranking variants | Kendall τ trên observed click targets; See-Also ranking; runtime | Cyclic-path relevance, xem xét hub dominance | Ta thêm strong local-frequency baseline và temporal holdout |
| L4 Evaluating Link-based Recommendations for Wikipedia | 2016 | Wikipedia links/text, See-Also, Clickstream | Related-article recommendation | CoCit, CPA, Lucene MoreLikeThis | MAP@10 See-Also; click-share metric gọi CTR@1/5/10 | So link-based với text-based recommendations | Ta chốt candidates trước labels, không tối ưu trên test collection |
| L5 A Large-Scale Characterization of How Readers Browse Wikipedia | 2023; preprint 2021 | English server logs, không phải public session dataset | Characterization browsing/navigation paths | Descriptive/statistical analyses, path reconstruction | Distributions/structural comparisons, không main Top-K benchmark | Làm rõ tính đa dạng của natural browsing | Ta chỉ thấy aggregate observed transitions |
| L6 Extracting Semantics from Random Walks on Wikipedia: Comparing Learning and Counting Methods | 2016 workshop; portal ghi upload 2021 | Wikipedia structure và navigation-derived paths | Semantic relatedness | DeepWalk-style learning và co-occurrence counting | Abstract xác nhận relatedness evaluation; exact metric/split cần full-text check | So embeddings/counting và nguồn walks | Semantic relatedness không bảo đảm next-click utility |
| L7 node2vec: Scalable Feature Learning for Networks | 2016 | Social, biological, collaboration graphs | Node representation, classification, link prediction | Biased second-order walks + skip-gram | Micro/Macro-F1; link AUC | Flexible neighborhood sampling | Không chứng minh cosine phù hợp directed next-article ranking |
| L8 Human Wayfinding in Information Networks | 2012 | Wikispeedia goal-directed paths | Human wayfinding và target inference từ prefix | Human Markov model, ranking/logistic models, TF-IDF comparator | Target accuracy, cumulative reciprocal rank, sibling precision | Phân tích cách người tìm đường và suy mục tiêu | Target cuối hành trình khác article kế tiếp; gameplay khác natural browsing |
| L9 DeepWalk: Online Learning of Social Representations | 2014 | Social networks | Network representation/classification | Truncated walks + Skip-Gram | Micro/Macro-F1 | Learn embeddings từ walk contexts | Là phương pháp nền, không direct navigation benchmark |
| L10 WikiLinkGraphs: A Complete, Longitudinal and Multi-Language Dataset of the Wikipedia Link Networks | 2019 | Historical Wikipedia revision-derived graphs | Dataset construction | Link extraction, redirect resolution | Graph statistics/data comparisons | Historical independent graph resource | Không phải recommendation algorithm hoặc evidence về gain |
| L11 Topic-Sensitive PageRank | 2002 | Web graph/topic categories | Query-sensitive web ranking | Topic-biased PageRank | Search relevance evaluation | Biased restart for contextual importance | Dự án seed bằng một article, không topic classifier/user profile |

## 2. Verified bibliography

**L1.** Akhil Arora, Martin Gerlach, Tiziano Piccardi, Alberto García-Durán, Robert West. *Wikipedia Reader Navigation: When Synthetic Data Is Enough*. WSDM 2022. DOI **10.1145/3488560.3498496**. [Author full text](https://dlab.epfl.ch/people/aarora/pub/Arora-Gerlach-Piccardi-GarciaDuran-West_WSDM-22.pdf), [arXiv full text](https://arxiv.org/html/2201.00812), [code](https://github.com/epfl-dlab/wikinav-approx).

**L2.** Dimitar Dimitrov, Philipp Singer, Florian Lemmerich, Markus Strohmaier. *What Makes a Link Successful on Wikipedia?* WWW 2017. DOI **10.1145/3038912.3052613**. [Author proceedings PDF](https://dimitardimitrov.info/documents/fp0410-dimitrov.pdf), [2016 preprint](https://arxiv.org/abs/1611.02508).

**L3.** Cristian Consonni, David Laniado, Alberto Montresor. *CycleRank, or there and back again: personalized relevance scores from cyclic paths on directed graphs*. Proceedings of the Royal Society A **476**, 20190740, 2020. DOI **10.1098/rspa.2019.0740**. [Full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC7544349/).

**L4.** Malte Schwarzer, Moritz Schubotz, Norman Meuschke, Corinna Breitinger, Volker Markl, Bela Gipp. *Evaluating Link-based Recommendations for Wikipedia*. JCDL 2016, pp. 191–200. DOI **10.1145/2910896.2910908**. [Archived published paper](https://d-nb.info/1163536415/34).

**L5.** Tiziano Piccardi, Martin Gerlach, Akhil Arora, Robert West. *A Large-Scale Characterization of How Readers Browse Wikipedia*. ACM Transactions on the Web **17**(2), Article 11, 2023. DOI **10.1145/3580318**. [Publisher](https://doi.org/10.1145/3580318), [preprint](https://arxiv.org/abs/2112.11848).

**L6.** Alexander Dallmann, Thomas Niebler, Florian Lemmerich, Andreas Hotho. *Extracting Semantics from Random Walks on Wikipedia: Comparing Learning and Counting Methods*. Wiki workshop at ICWSM **2016**, pp. 33–40. DOI **10.1609/icwsm.v10i2.14831**. [Publisher record](https://ojs.aaai.org/index.php/ICWSM/article/view/14831). Portal tự sinh citation năm 2021 nhưng issue là “Vol. 10 No. 2 (2016)”; dùng năm workshop và ghi khác biệt metadata, không đoán đó là nghiên cứu 2021.

**L7.** Aditya Grover, Jure Leskovec. *node2vec: Scalable Feature Learning for Networks*. KDD 2016. [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC5108654/), [Stanford project](https://snap.stanford.edu/node2vec/), [arXiv](https://arxiv.org/abs/1607.00653).

**L8.** Robert West, Jure Leskovec. *Human Wayfinding in Information Networks*. WWW 2012. [Author paper](https://cs.stanford.edu/~jure/pubs/wayfinding-www12.pdf), [dataset](https://snap.stanford.edu/data/wikispeedia.html).

**L9.** Bryan Perozzi, Rami Al-Rfou, Steven Skiena. *DeepWalk: Online Learning of Social Representations*. KDD 2014. [Paper record](https://arxiv.org/abs/1403.6652).

**L10.** Cristian Consonni, David Laniado, Alberto Montresor. *WikiLinkGraphs: A Complete, Longitudinal and Multi-Language Dataset of the Wikipedia Link Networks*. ICWSM 2019. [Publisher](https://ojs.aaai.org/index.php/ICWSM/article/view/3257), [full text](https://arxiv.org/html/1902.04298), [dataset DOI 10.5281/zenodo.2539424](https://zenodo.org/records/2539424).

**L11.** Taher H. Haveliwala. *Topic-Sensitive PageRank*. WWW 2002. [Stanford paper](https://ilpubs.stanford.edu/573/1/2002-6.pdf), [author publications](https://www.taherh.org/publications).

**Baseline bổ sung:** Jon M. Kleinberg. *Authoritative Sources in a Hyperlinked Environment*. Journal of the ACM **46**(5), 1999; có bản conference SODA 1998. [Author bibliography](https://www.cs.cornell.edu/home/kleinber/kleinber.html), [published text](https://www.cs.cmu.edu/afs/cs/project/pscico-guyb/realworld/www/papers/kleinberg.pdf). Dùng làm nền cho HITS, không trộn hai năm thành hai thuật toán.

Không tự điền DOI/page ranges còn thiếu. Các bibliography entries này đủ trích dẫn; bổ sung BibTeX từ publisher khi viết report, kiểm tra lại author order và edition.

## 3. Prior work gần nhất và điều cần học

**L2 đã kết hợp behavior và structural information.** Vì vậy không được claim “đầu tiên kết hợp clicks với graph”. Nhóm có thể kiểm tra các giả thuyết tương tự dưới temporal ranking protocol khác; không suy rằng weighted global PageRank result của L2 chứng minh PPR sẽ thắng local Markov.

**L3 rất gần source-conditioned relevance.** Paper đánh giá click ranking trên tập observed destinations và dùng Kendall τ. Thiết kế của ta cần full eligible candidate universe và held-out future labels để đo missed destinations; đây là khác biệt protocol, không phải bằng chứng algorithmic novelty.

**L4 gần bài toán recommendation và cung cấp baseline motivation.** Section 4.1 tune CPA trên collection dùng đánh giá và không đặt temporal prediction như mục tiêu. Ta không sao chép cách chọn hyperparameter đó sang held-out predictive claims. “CTR” trong paper là offline click-share proxy, không chứng minh uplift của hệ thống mới.

**L1 liên quan trực tiếp synthetic navigation và first-order limitation.** Kết quả downstream của paper không cấp phép gọi walks sinh từ aggregate counts là “sessions người dùng thực”. Code repository cũng ghi không chia sẻ navigation sequences sử dụng trong công trình cho công chúng. Không đưa private data vào dependencies.

**L5 và L8 giới hạn external validity.** Một bên natural browsing, một bên đi tìm goal được chỉ định. Mọi fallback phải giữ khác biệt về mục tiêu hành động và sampling population.

**L6/L7/L9 làm rõ mục đích embedding.** “Representations tốt” cho semantics/classification không tự kéo theo tốt cho next-article ranking. Đó là hypothesis M5 phải kiểm tra, không là lý do bỏ strong frequency baseline.

## 4. Rationale cho baseline được chọn hoặc loại

| Approach | Quyết định | Lý do trong scope |
|---|---|---|
| First-order Markov / local popularity | P0 bắt buộc, raw và backoff | Phù hợp thông tin hiện có, baseline mạnh trực tiếp |
| PPR | P0 | Query-conditioned multi-step topology với công thức/solver kiểm chứng được |
| Destination in-degree | P0 | Kiểm tra structural global popularity với chi phí thấp |
| HITS-global | P1 khuyến nghị | Dễ bổ sung authority comparator; không tuyên bố đây là query-local HITS |
| Query-local HITS | P2 | Root/base set construction có thể thay candidates/context; cần fairness protocol thêm |
| CycleRank | P2 | Rất liên quan hub bias, nhưng bounded cycle enumeration thêm engineering; không bắt buộc để trả lời frequency-vs-topology |
| DeepWalk | Control p=q=1 trong Node2Vec | Tránh thêm backend khi random-walk pipeline đã có; ghi rõ khác SGNS/walk settings |
| CoCit/CPA | CoCit P2; CPA ngoài core | Co-citation có thể xét từ H, CPA cần link positions; thiếu dữ liệu đó trong edge list |
| ItemKNN | Không dùng standard user-item CF | Không có users; nếu làm co-navigation similarity phải gọi article–article và định nghĩa counts, không giả user matrix |
| BERT/FastText/GNN | Không thuộc core | Thêm content/complexity không cần cho RQ hiện tại |
| Learning-to-rank | P2 | Censored labels và temporal cross-fitting cần giải quyết trước |

Không loại HITS vì một paper nói nó kém; lựa chọn scope dựa trên chi phí và câu hỏi. Nếu PPR chỉ hơn uniform mà không hơn in-degree/HITS thì không được kết luận multi-step relevance hữu ích.

## 5. Positioning và claim rules

Đóng góp mục tiêu: **một khung thí nghiệm có thể tái lập để so sánh frequency, topology và fusion, với temporal labels, thống nhất candidates, coverage accounting, sparsity analysis và computational cost**.

Những điều chỉ được viết sau thí nghiệm:

- Model nào thắng trên metric/subgroup nào, cùng CI và denominator.
- Topology có bổ sung predictive information hay chỉ lặp lại popularity.
- Fusion có đáng chi phí trong setting lịch sử đã chọn.
- Embeddings có đóng góp hay không với directed one-step target.

Không dùng “novel hybrid”, “user-personalized”, “state of the art”, “causal improvement”, “real sessions recovered” nếu evidence không đáp ứng.

## 6. Reading backlog có giới hạn

P0: đọc kỹ methods/evaluation L1–L4 và dataset L10; lưu section pointers vào report notes. P1: lấy full text L6 để xác minh exact metric/split trước khi so sánh chi tiết; xem negative sampling và directed semantics L7; đọc path parser/header L8 nếu fallback.

L6 hiện chỉ metadata/abstract đã xác minh qua publisher; chưa được dùng để khẳng định con số, exact benchmark hay effect size. Một số URL PDF/HTML trả lỗi truy cập trong phiên; đã dùng bản full text của tác giả khi có. Nếu vẫn thiếu, giữ ô “chưa xác minh”, không suy từ abstract.

Không tái tạo toàn bộ benchmark của các paper: khác dataset/split/task nên không đặt score của họ cạnh score của ta như head-to-head. Mục tiêu review là định hướng thiết kế và giới hạn claim.
