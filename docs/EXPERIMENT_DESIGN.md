# Thiết kế thí nghiệm và hợp đồng đánh giá

Protocol v1 đề xuất, 20/10/2026. Chưa có kết quả. Mọi quyết định cần khóa trước khi mở test được đánh dấu trong phần 11. Đọc cùng [dataset audit](DATASET_FEASIBILITY.md).

**Cập nhật 21/10:** đây là specification; không phải mọi sensitivity/ablation đã được triển khai. [Config study hiện có](../configs/study.toml) chọn 200 queries (50 mỗi stratum 0/1–99/100–999/≥1000 training mass), degree 5–500 và induced outgoing closure 8.094 nodes/319.694 edges. Mọi graph method trong bảng study phải dùng subgraph này; global popularity vẫn tính từ toàn corpus train. Node2Vec dự kiến chọn knobs bằng seed 17, báo thêm seeds 29/43 với knobs cố định. Các lựa chọn đó thay thế đề xuất sample size/quartiles/seed-selection bên dưới cho run này; xem [DATA_AUDIT](DATA_AUDIT.md). Lần thử validation chưa hoàn tất, chưa có test results.

**Gate trước benchmark:** reviewer phải đối chiếu config/code với specification, đặc biệt tie trong model selection (runner hiện giữ option đầu tiên khi metric bằng nhau, còn mục 7.2 đề xuất runtime rồi simplicity), scope của history ablation và fallback khi solver lỗi. Chốt một policy deterministic và ghi vào manifest trước test; không mô tả policy chưa thực thi như đã chạy. A5 chỉ bắt buộc khi báo Node2Vec; có thể bỏ cả cặp M5H/M5W trước test nếu backend không qua gate.

## 1. Task và ký hiệu

Chọn **Task A: source-conditioned next-article ranking**. Input chỉ là article hiện tại, không có chuỗi `u1,…,ut` (Task B) hay danh tính/lịch sử user (Task C). Điều kiện của target là đã có điều hướng nội bộ thuộc `type=link`; không mô hình hóa stop/external search.

- `t0`: cuối training period. `tH ≤ t0`: thời điểm trạng thái graph.
- `V`: canonical article IDs trong node inventory đã khóa trước validation/test; nếu chỉ có endpoint inventory phải ghi rõ.
- `GH=(V,EH)`: directed editorial-link graph tại `tH`. `AH[u,v]=1` khi có hyperlink u→v. Self-loops loại khỏi task và graph model theo một policy chung.
- `c_m(u,v)`: count **được công bố** ở tháng m sau xử lý. Nếu không có row, đặt numerical value 0 để lưu sparse nhưng giữ observation flag; đó không phải tuyên bố true zero.
- `c_tr(u,v)=Σ_{m∈train} c_m(u,v)`.
- `GC=(V,EC,c_tr)`: behavior graph với c_tr>0, cả các mapped edges ngoài EH. `GC∩H` là biến thể support-restricted, phải đặt tên khác.
- `T_u=Σ_v c_tr(u,v)` và `d_H(u)=|N_H⁺(u)|`.
- `P_C[u,v]=c_tr(u,v)/T_u` nếu T_u>0; row rỗng xử lý theo từng model, không ngầm thêm graph information.
- `P_H[u,v]=AH[u,v]/d_H(u)` khi d_H(u)>0.
- Source context là u; candidate set chính `C(u)=N_H⁺(u)\{u}`, lọc canonical articles hợp lệ tại snapshot.
- `y_m(u,v)` là future observable count tháng validation/test. `R_all(u)={v:y(u,v)>0}` gồm cả out-of-vocabulary labels trong evaluation ledger. `R_C(u)=R_all(u)∩C(u)`.
- Scorer `sθ(u,v;D_tr,GH)` tạo total order `π_u` trên C(u); labels tương lai không là input của scorer.

Training objective khác nhau: M0/M1 ước lượng frequency; PPR giải fixed point; Node2Vec tối ưu skip-gram objective trên training graph; hybrid chọn coefficient trên validation ranking metric. Validation chọn cấu hình theo macro NDCG@10 định nghĩa dưới đây. Test chỉ đo generalization sau freeze.

Đây không phải generic link prediction: trong setting chính link tồn tại là điều kiện ứng viên, target là **future observed usage**. Không lấy non-edge random negatives rồi báo link AUC như next-article accuracy.

## 2. Candidates, sources và estimands

### 2.1 Primary setting

Xếp hạng toàn bộ outgoing links từ graph **đã đóng băng**; không dùng current links của tháng test. Tất cả models dùng chính xác cùng `C(u)`, kể cả M0. Không negative sampling trong evaluation. Khi |C|<K, trả đủ |C|, không pad bằng bài ngoài tập.

Ưu điểm: sát hành động click một link có sẵn; full ranking theo degree thay vì hàng triệu items; dễ kiểm soát fairness. Hạn chế: graph là historical editorial graph, có thể thiếu template/new links và không đại diện đầy đủ exposure. Không gọi đây là mọi next-article destination trên Wikipedia.

P2 all-known-articles setting: `C_all(u)=V\{u}`; cùng label universe, full candidate ranking hoặc retrieval+rerank có báo retrieval recall. Không so điểm trực tiếp với primary như thể độ khó bằng nhau. ANN và sampled candidate metrics không thuộc P0.

### 2.2 Source universe trước labels

`U` xác định từ canonical graph inventory và train. Lưu hash danh sách trước khi đọc validation/test. Pilot 100 sources, benchmark dự kiến 1,000 sources; tăng chỉ sau resource gate và **trước** test.

Nếu cần stratified query sample: chia theo train traffic quartiles trong nhóm T_u>0, cộng nhóm T_u=0; chia thêm degree thấp/cao nếu đủ mẫu. Sample seed 2026, lưu inclusion probabilities và quota. Đừng chọn nguồn vì nó “có ≥5 test links”. Main macro trên sample được gọi là **sample-conditional macro**; muốn suy ra population average phải dùng design weights, không tráo hai estimands. Traffic-weighted score trên sample cũng không đại diện total Wikipedia traffic.

`Q_all={u∈U: Σ_v y(u,v)>0}`: chỉ nguồn có observable held-out link label mới có thể đánh giá. `U\Q_all` ghi “no observable label”, không suy ra không có navigation. Không thay U bằng nguồn khác để bù thiếu label. `Q_C={u∈Q_all:|R_C(u)|>0}` dùng cho conditional analysis. Cả hai danh sách dùng chung cho mọi model.

Sources ngoài V hay mới xuất hiện sau cutoff: ghi outside-universe coverage trên full release; không gán historical feature từ tương lai. Cold source **trong V**, T_u=0, vẫn có thể dùng topology; khác new article ngoài V.

### 2.3 Coverage và failures

Mỗi split báo:

- |U|, |Q_all|, |Q_C|; sources/clicks không có label hoặc ngoài V.
- Số distinct future pairs, observed click mass trước/sau node matching và candidate restriction.
- Pair candidate coverage `Σ_u |R_C(u)| / Σ_u |R_all(u)|`.
- Click candidate coverage `Σ_{u,v∈C(u)} y(u,v) / Σ_{u,v} y(u,v)`.
- Per-source candidate coverage cùng macro/traffic-weighted average.
- Số empty candidate lists, failed scores, nonconverged PPR, OOV embeddings và fallback counts.

Mẫu số full-release coverage tách khỏi mẫu số sampled-query coverage. Candidate coverage là ceiling theo observations, không phải coverage của tất cả clicks thực tế.

Primary table dùng **full observable denominator** trên Q_all, với unreachable destination rank=∞. Conditional table chỉ đánh giá Q_C, relevance và IDCG restricted C. Phải đặt hai table cạnh nhau. Model không được tự loại nguồn thất bại: retry numerical issue có log; nếu vẫn thất bại dùng fallback chung M2 hoặc empty list theo config và report, không chọn fallback theo test.

## 3. Model matrix

Ký hiệu chi phí: N=|V|, M_H=|EH|, M_C=|EC|, D=|C(u)|, S=queries, I=iterations, d=embedding dim, r=walks/node, L=walk length, w=context window, k_neg=negative samples, E=epochs. Ranking top K bằng partial selection + stable ties, thường O(D + K log K), full sort O(D log D).

| Model / priority | Input, signal → output | Công thức / knobs | Cost profile | Motivation, strength / failure |
|---|---|---|---|---|
| M0 P0 Global Most-Popular | Train link counts → destination score | `g(v)=Σ_x c_tr(x,v)`; restrict C | Fit O(M_C), O(N) memory; score O(D) | Strong global demand control; bỏ qua source intent, head bias |
| M1 P0 Local Markov | Train counts → local preference | `s=c_tr(u,v)/T_u`; T_u=0 → M0; if all eligible scores zero → M0 | O(M_C), CSR O(N+M_C); O(D) | Optimal empirical frequency order for observed source distribution; drift/sparse unseen failure |
| M1B P0 Smoothed/backoff Markov | Train only scores + shared candidate restriction | Formula bên dưới; μ,η | Như M1 | Competitive baseline, không tạo baseline yếu cho hybrid |
| M2 P0 Uniform Hyperlink | Candidate IDs only → equal scores | `1/D`; tie by fixed cryptographic hash | O(D); no fit | Isolate eligibility, không chứa preference |
| M2D P0 In-degree | H → target structural popularity | `s=d_H⁻(v)` | O(M_H), O(N); O(D) | Kiểm tra gain PPR có chỉ do hubs không |
| M3 P0 PPR-H | H, restart at u → r_u(v) | damping δ, residual ε, max_iter | Exact O(SI(M_H+N)); sequential memory O(M_H+N) | Structural multi-step paths; hubs, proximity≠next-click |
| M4C P0 PPR-C | Pure train click graph → r_u(v) | P_C, same solver | O(SI(M_C+N)); sparse | Behavioral diffusion only; **không** gọi hybrid |
| M4C∩H P0 controlled variant | Click weights only on EH → r | Same δ as paired M3 | Sparse | Cùng candidate, nhưng support bị mất khi count absent; cần M4H để tách effect |
| M4H P1 PPR-smoothed-H | EH + train click weights on EH → r | `w=c+μ/d_H`; μ>0 | O(SI(M_H+N)) | Giữ support H; thiếu count vẫn có prior mass; biased prior có thể gây dilution |
| M5H/M5W P1 Node2Vec | H / same H weighted → cosine score | d,r,L,p,q,w,E,seeds | Walk/SGNS budget ở mục 6 | Fast scoring after fit; symmetric proximity có thể lệch task |
| M6B P0 Score fusion | M1B + M3 candidate-normalized → score | λ∈[0,1] | M3 prep + O(D) | Transparent signal mixture; có thể cộng noise/duplicate popularity |
| M6A P1 Matrix fusion | P_C∩H + P_H → PPR score | λ,δ | O(SI(M_H+N)) | Combine signals at every step; khác late fusion |
| HITS-global P1 | H → authority `a` | `a∝Aᵀh`, `h∝Aa`, L2 normalize | O(I M_H), O(M_H+N) | Cheap established ranking control; không query-personalized |

Shared candidate restriction dùng H cho mọi model; vì thế “behavior-only” nghĩa **scoring features only**, không nghĩa candidate retrieval độc lập topology. Full support C variant tồn tại để tách graph/scoring signal, không dùng để đổi candidates.

### 3.1 Markov và smoothing không vô nghĩa

Với D>0, đặt `g_C(v)=(g(v)+ε_g)/Σ_{x∈C(u)}(g(x)+ε_g)`, ε_g=1 là fixed tiny prior; `b_u(v)=(1−η)/D+ηg_C(v)`. Dùng:

`q_B(v|u)=[c_tr(u,v)+μ b_u(v)]/[T_C(u)+μ]`, `T_C(u)=Σ_{x∈C(u)} c_tr(u,x)`.

Nếu μ=0,T_C=0, fallback g_C. Nếu μ>0,T_C=0, q_B=b_u. μ∈{0,10,100,1000}, η∈{0,0.5,1}; coarse 12 configs. Raw M1 vẫn báo riêng.

Uniform additive smoothing không đổi thứ hạng các count khác nhau; không giả rằng tuning một constant uniform sẽ tự tạo ranking improvement. Backoff/global prior mới có thể đổi order. Ghi rõ raw zero chỉ là unobserved. Các normalization này trên C được dùng nhất quán trong scoring, không thay số đếm gốc.

### 3.2 Ties và uniform baseline

Total order: score giảm dần, sau đó `SHA256(seed || source_id || target_id)` tăng dần; không dùng title alphabet hay Python `hash()`. Tie-break không nhìn train/test relevance. Cùng rule cho mọi model; M2 là một deterministic permutation, không phải preference model.

P1: thêm expected random Recall@K hoặc 20 tie seeds để chỉ rõ variance của uniform; đó không phải stochastic training. D=0 trả empty; D≤K có thể làm Recall trivial, nên báo degree bins.

## 4. PPR: định nghĩa, numerical correctness, scaling

Với row-stochastic matrix P và row vector r:

`r_u = (1−δ)e_u + δ r_u P^(u)`, `0<δ<1`.

`P^(u)` bằng P với mọi dangling row thay bằng e_u. Traverse **u→v** theo outgoing links; column vector implementation dùng transpose đúng một lần. Restart probability=1−δ. Query source bị loại khỏi recommendation nhưng không bị loại khỏi random walk. Với PPR-H nguồn có candidates trực tiếp đều reachable; với PPR-C có thể có candidate zero-score.

Khởi tạo r0=e_u; kiểm tra sum≈1, nonnegative. Stop dựa trên **absolute L1 residual** `||r−[(1−δ)e_u+δrP^(u)]||1 ≤ ε`; max_iter safety 200 rồi tối đa 1,000 nếu needed. Bound error `||r−r*||1 ≤ residual/(1−δ)`. Không dùng mặc định `N*tol` của library rồi gọi là ε tuyệt đối; [NetworkX pagerank documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html) phải đối chiếu khi làm oracle.

Giá trị δ đề xuất {0.15,0.5,0.85}; ε {1e−6,1e−8} kiểm tra numerical stability trên pilot. ε/max_iter là accuracy controls, không tune để tăng test score. Report residual, iterations, top-K stability và runtime theo δ. Chọn δ theo validation; dùng δ cố định chung trong controlled weighting ablation, ngoài bảng best-tuned per-model.

Full per-source exact sparse iteration là reference, có thể quá chậm ở hàng nghìn sources. Gate: 100 source pilot, dự phóng S×median và p95 time; nếu >8 giờ cho một config, giảm query count trước test hoặc dùng approximate forward-push với residual certificate. Approximation phải so với exact trên cùng pilot và báo score error/top-K overlap; không đổi solver giữa models mà không kiểm tra.

Không materialize S×N score matrix; cache only candidate scores, graph hash, δ, ε, source ID. Không cắt 2-hop graph rồi gọi kết quả là full-graph PPR. Nếu graph bị sample, bảng riêng có boundary report.

### 4.1 Weighted PPR và support

- **M4C:** positive train clicks trên GC, missing pairs không là edges; dangling→restart. Graph hoàn toàn behavior-derived.
- **M4C∩H:** chỉ phần train counts khớp EH. Dùng để xem effect mismatch/support.
- **M4H:** trên mỗi edge EH, `w(u,v)=c_tr(u,v)+μ/d_H(u)`, μ>0; chuẩn hóa row. Missing public counts có prior, không được phát biểu có exactly μ/d clicks thật. Nếu T_C=0, chuyển thành P_H row. Đây là hybrid graph thật.

M3 vs M4C khác cả support lẫn weights; **không** dùng riêng cặp này để kết luận gain do weighting. M3 vs M4H có cùng positive support; μ và δ được kiểm soát.

## 5. Hai hybrid designs

**A — Transition interpolation:** trên H, định nghĩa `P_C^H` bằng normalized train counts khớp H; row không có observed eligible clicks thì **explicit fallback P_H**. `Pλ=λP_C^H+(1−λ)P_H`. M6A là PPR trên Pλ, không chỉ lấy row u của Pλ.

Các row sum=1 trừ dangling, được xử lý restart chung. λ=0→M3. λ=1→PPR-click-on-H **có topology fallback ở zero-traffic rows**, nên không đồng nhất với pure M4C. Báo tỷ lệ row/mass dùng fallback. Direct one-step blend với uniform trên C thường giữ nguyên thứ tự positive local counts; không trình bày nó như một graph model mạnh nếu không có multi-step.

**B — Score fusion:** q_B từ M1B và `q_H(v|u)=r_H,u(v)/Σ_{x∈C}r_H,u(x)`. `sλ=λq_B+(1−λ)q_H`. Nếu sum PPR candidate=0 hoặc solver fail dùng uniform và log. λ=1→M1B; λ=0→M3 ranking, verified by tests.

L1 normalization cho nonnegative scores là default dễ giải thích, **không** chứng minh calibrated click probability. P1 normalization ablation: rank-percentile fusion; softmax temperature chỉ nếu dùng cosine component, tune validation riêng. Không cộng raw counts và PPR probabilities trực tiếp. Fixed coefficients α+β=1 đủ cho P0; tránh thêm target popularity lần nữa khi M1B đã có.

LTR P2: cần cross-fitting temporal train folds để tạo feature không tự nhìn labels; pair unobserved không được gắn confident negative. Nếu chưa có treatment censored labels và weight protocol rõ thì không thêm logistic/tree model.

## 6. Node2Vec specification và gate

Nguồn [paper](https://arxiv.org/abs/1607.00653), [reference implementation](https://github.com/aditya-grover/node2vec) hỗ trợ directed/weighted tùy flags. **Đã kiểm tra code** [transition logic](https://raw.githubusercontent.com/aditya-grover/node2vec/master/src/node2vec.py): lựa chọn outgoing neighbors, nhân edge weight và điều chỉnh return/in-out bias; nhánh gần previous node kiểm tra `has_edge(next,previous)`. Đó là convention directed cụ thể, không được âm thầm thay bằng undirected distance.

Định nghĩa dự kiến khi previous=t,current=v,next=x:

`Pr(x|t,v) ∝ w(v,x) b_pq(t,x)`,

với b=1/p nếu x=t; b=1 nếu x→t tồn tại; b=1/q nếu không. First step ∝w(v,x). Ghi convention trong config/test; snapshot reference code SHA tại implementation, port cần license attribution. Dừng walk ở dangling, không tạo artificial hyperlink bằng restart token.

M5H weights=1 trên H. M5W dùng cùng EH và prior μ như M4H; **không xóa missing-count edges**, nên A5 kiểm soát support. Một pure click-only Node2Vec là model thứ ba P2, không gộp vào topology-only.

Skip-gram negative sampling objective dự kiến:

`max Σ_(i,j)∈contexts [log σ(z_i·z'_j) + Σ_{a=1}^{k_neg} E_n log σ(−z_i·z'_n)]`.

Negative samples phục vụ embedding objective, **không** tương đương nhãn “user không click”. Context window symmetric làm proximity embeddings không bảo đảm direction-specific preference. Default recommendation `cos(z_u,z_v)` là explicit proximity baseline trên candidate outgoing; nêu nhược điểm symmetry. Source–context dot product chỉ P2: cần xác minh context direction và train objective phù hợp, không lấy dot khác rồi gọi directed predictor.

Baseline config: d=64, r=5, L=20, p=q=1, window=5, epochs=5, negative=5, min_count=1, sg=1, sample=0. Pin mọi nondefault và package version. p=q=1 là control tương ứng first-order walk; không tuyên bố bản sao DeepWalk hoàn toàn nếu sampling/SGNS khác.

Search tối đa 12 configs: d {32,64}; (p,q) {(1,1),(0.5,2),(2,0.5)}; pilot chọn một cặp r/L nhỏ rồi so (5,20) với (10,40) cho top candidates. Window {5,10} chỉ sau coarse search, không Cartesian product mọi knob. Giữ k_neg/epochs là fixed initial choices; nếu cần thay, version protocol và chọn bằng validation.

Chi phí approximate: tokens T≤NrL; context updates O(E T w (k_neg+1)d). Second-order alias precomputation có thể O(Σ_v d_in(v)d_out(v)) memory, không chỉ O(M). Chọn on-the-fly/bounded cache sampler cho graph lớn hoặc giảm graph theo gate. Embedding storage hai tables float32 ~8Nd bytes, cộng optimizer/vocab.

Chỉ chạy trên shared subgraph cap 50k nodes/1M edges ban đầu. Bảng đó phải rerun **M0–M6** trên cùng graph/candidates/query set; không so M5 subgraph với M3 full graph rồi đổ lỗi thuật toán.

Optimization diagnostics: [Gensim Word2Vec](https://radimrehurek.com/gensim/models/word2vec.html) có `compute_loss`, callbacks và `get_latest_training_loss`. Xác minh semantics cumulative/reset của version đã pin bằng fixture; ghi per-epoch delta nếu có ý nghĩa, không lấy cumulative loss tăng làm divergence. Đo token count, throughput, validation rank metric và embedding norm distribution; held-out walk loss là auxiliary, không phải next-click loss. Nếu backend không cung cấp loss đáng tin, nói rõ và dùng validation/time/seed diagnostics; không tạo curve giả.

Seeds {17,29,43}; tune coarse bằng một seed, rerun finalists trên ba seeds validation; freeze cấu hình rồi báo cả ba test runs. Để kiểm thử repeatability có thể workers=1; production multi-thread ghi nondeterminism, không hứa bitwise repeatability.

## 7. Temporal protocol

### 7.1 Primary fixed-model evaluation

| Artifact | Thời gian được phép |
|---|---|
| H, canonical mapping | Snapshot 2018-03-01, không sửa bằng future titles |
| Train behavior/features | 2018-01, 02, 03 |
| Validation labels/tuning | 2018-04 |
| Test labels | 2018-05, chỉ evaluator đọc sau freeze |
| Optional fixed-horizon test | 2018-06 |

Train may precede/follow tH trong cùng training window; tH vẫn trước validation. Counts training ngoài H giữ trong behavior graph, log match rate. Newly created articles ngoài historical V không được thêm vào training topology chỉ vì xuất hiện test.

Không refit bằng validation trong primary table: giữ rõ một training model so với future tháng 05. P1 deployment-style refit train 01–04 test05 phải là **bảng khác**, hyperparameters chọn từ split trước; không trộn với primary. Publication dates tạo độ trễ: primary là retrospective event-time benchmark, không deployable next-month backtest. Nếu cần strict available-at protocol, train các file available trước cutoff; validation phải available trước test start, thêm gap hoặc lùi tháng. WLG phát hành sau 2018 cũng được khai báo retrospective reconstruction.

Rolling P1: window W1 train01–03/val04/test05; W2 train02–04/val05/test06. W2 là rolling deployment sử dụng tháng05 làm validation **sau khi đã hoàn tất W1**, chỉ nếu quy trình tuning đã khóa trước mọi test. Kết quả W1 không được dùng redesign algorithm. Hai windows overlap, không coi là independent replicates.

Farther-horizon A9: model train01–03 và hyperparameters val04 cố định; so test05 vs test06. Không gọi việc đó là learning curve. Tách snapshot aging và demand drift trong discussion vì không hoàn toàn phân biệt được khi chỉ một H.

### 7.2 Validation objective

Primary selection = sample macro `NDCG_all@10` với gain log1p và Q_all(validation). Tie selection: runtime thấp hơn, rồi cấu hình đơn giản hơn, theo rule đã khóa. Không chọn λ theo subgroup test. Subgroup policies nếu muốn phải fit/tune trên validation và báo là model mới.

Training-size studies cùng cutoff cuối tháng03: chỉ03, 02–03, 01–03. Giữ H, C, U và test months cố định. Khi mở rộng history, tập observed edges thay đổi do censoring; không khẳng định đó là randomized data-size effect. Count thinning không tái tạo public suppression nên không P0.

## 8. Metrics chính xác

Đặt `K_u=min(K,|C(u)|)`, ranked items π_u(1…K_u), `rank_u(v)=∞` nếu v không được trả về. Với Q_all, tất cả denominators bên dưới tính trên R_all trừ khi có hậu tố `_C`.

### 8.1 Binary relevance

`Recall_all@K(u)=Σ_{i≤K_u}1[π_u(i)∈R_all(u)] / |R_all(u)|`.

Required K={5,10,20}. Đo bao phủ unique future observable destinations; cho head/tail observed edges trọng số như nhau. Không mô tả như expected fraction of individual clicks.

`RR_all@10(u)=1/min{i≤10:π_u(i)∈R_all(u)}`, bằng 0 nếu không có hit.

`MRR@10=mean_u RR@10(u)`. Đo vị trí hit đầu; bỏ qua các relevant items sau hit và tần suất. Khi nhiều relevant outgoing links, có thể dễ đạt cao; phải đọc cùng Recall/NDCG. Binary HitRate@K=`1[Recall@K>0]` chỉ supplementary, không thay Recall.

### 8.2 Graded relevance

Gain mặc định `g_u(v)=log2(1+y(u,v))`; unobserved gain=0 **cho evaluator**, không phải true irrelevance.

`DCG_all@10(u)=Σ_{i=1}^{min(10,|C|)} g_u(π_u(i))/log2(i+1)`.

`IDCG_all@10(u)` sắp **tất cả R_all**, kể cả absent candidates, theo gain và lấy top10. `NDCG_all=DCG/IDCG`. Đây là end-to-end observable-ranking metric, có thể không đạt 1 vì candidate limitation. Q_all bảo đảm IDCG>0.

Conditional `NDCG_C` dùng IDCG từ R_C, chỉ trên Q_C; conditional Recall denominator |R_C|. Không thay denominator full thành conditional mà giữ tên.

Linear gain y là P1 sensitivity để thấy ảnh hưởng head traffic; không dùng `2^y−1` vì count lớn và không cần exponential amplification. NDCG đo graded order, không probability calibration.

### 8.3 Click-weighted/event-proxy metrics

`MassRecall_all@K(u)=Σ_{i≤K_u} y(u,π_u(i))/Y_u`, `Y_u=Σ_v y(u,v)`.

`ExpectedRR_all@10(u)=Σ_v [y(u,v)/Y_u] × 1[rank_u(v)≤10]/rank_u(v)`.

Đây là expectation khi rút một transition từ **published aggregate mass**, không reconstruction user sessions. ExpectedRR khác binary RR của first relevant item; không đặt cùng tên MRR. MassRecall không đồng nghĩa online CTR.

### 8.4 Aggregation, coverage, runtime

Macro `M_macro=Σ_{u∈Q} M_u/|Q|`; traffic-weighted `M_weighted=Σ_u Y_u M_u/Σ_u Y_u`. Cho click-mass Recall, weighted aggregate đúng bằng fraction published clicks được hit trong query sample; traffic-weighted binary Recall không phải cùng đại lượng đó. Report per-source rows để tính lại.

Catalog coverage@K=`|∪_u topK(u)| / |∪_u C(u)|`; bổ sung query service coverage=`#u có nonempty output / |U|`. Đây là diversity/service metrics, khác ground-truth candidate coverage ở mục 2. Latency p50/p95 theo source với cold/warm cache tách riêng; prep time và peak RSS được ghi.

MAP optional không cần trong P0 vì Recall/MRR/NDCG đã đủ câu hỏi; thêm metric phải có mục đích và định nghĩa denominator rõ, không “metric shopping”.

## 9. Ablation matrix

Không giả định improvement dương. Cùng split/candidates/queries/solver precision; “best tuned” và “controlled setting” là hai bảng riêng.

| ID / priority | Hypothesis | Independent variable | Controls / models | Subset & metric | Giá trị phân tích |
|---|---|---|---|---|---|
| A1 P0 | Local history đã đủ cho stable high-traffic sources | Behavior scoring | M0/M1/M1B/M4C, common C | All, macro NDCG + MassRecall | Mốc mạnh trước graph |
| A2 P0 | Structure chứa preference information | Topology scorer | M2/M2D/M3, cùng H và C | All/low traffic, all metrics | Tách eligibility, hubs, multi-step |
| A3 P0 | Hai signals bổ sung | Inclusion of H score | M1B vs M3 vs M6B; λ endpoints | All + train sparsity, paired Δ NDCG | Câu trả lời trực tiếp RQ1 |
| A4 P0/P1 | Transition weights ảnh hưởng ranking | Uniform vs observed vs smoothed weights | P0 M3/M4C∩H; P1 M4H **fixed support**, same δ | Common queries, NDCG/MassRecall, support counts | Không nhầm support và weight effect |
| A5 P1 | Weighted walks giúp embeddings | Weights only, fixed EH | M5H/M5W, same d,p,q,walk budget, seeds | Same subgraph; macro NDCG, ExpectedRR | Nếu không chạy M5 thì ghi “not applicable”, không giả đủ full scope |
| A6 P0 | Fusion có vùng tradeoff, endpoint có thể tốt nhất | λ={0,.25,.5,.75,1}, refine ±.1 | Frozen components/normalization | Validation main+strata; test only locked λ | Không tune curve trên test |
| A7 P0 | Gain thay đổi theo sparse/unseen | Train frequency / traffic bins | Models frozen; no rerank within bins | Pair-bin Recall/MassRecall + source-bin metrics | Phân biệt true rare và train-unobserved |
| A8 P0 | More history giúp stability hoặc gây stale counts | 1/2/3 trailing train months | Same H,C,U,cutoff; fixed-param primary + retuned P1 | Validation curves; locked test panel | Data-efficiency, không fake training loss |
| A9 P1 | Gain giảm theo horizon | Test05 vs06, fixed model | Train01–03, val04, same H,C,U | Macro/weighted NDCG, paired sources + all-source panels | Robustness, snapshot aging caveat |
| A10 P1 | Global authority giải thích PPR gain | Scorer | M2D/HITS-global/M3 | All + hub bins | Trả lời “why not HITS” |
| A11 P1 | Fusion phụ thuộc scaling | L1 vs percentile | Same components, λ tuned val separately | Macro NDCG, runtime | Role of normalization |

A7 source bins dùng thresholds/quantiles từ train, zero là nhóm riêng. Pair bins: `unobserved all train months`, observable low (positive count ≤train median), medium, high (>train p90); các thresholds fit trên training positive pairs. Với release eswiki đã audit, có thể thêm per-month **10–20** band để xem gần suppression threshold, không gọi “all rare transitions”. Count cộng ba tháng không có cùng ý nghĩa với count một tháng; ghi cả số tháng pair được quan sát khi diễn giải low-frequency group.

Pair-bin Recall tính numerator relevant items trong bin xuất hiện ở **original full ranking**, denominator các future observed targets thuộc bin; không lọc candidates theo bin rồi rerank. NDCG theo pair bin chỉ auxiliary với gain mask và IDCG tương ứng, phải giải thích không cùng estimand main table.

## 10. Statistical analysis và diagnostics

Primary comparison preregister M6B−M1B trên macro NDCG_all@10. Paired bootstrap 2,000 resamples của source IDs, giữ cặp model predictions; percentile 95% CI của mean difference. Bootstrap weighted metrics bằng resample sources rồi tính lại numerator/denominator, không bootstrap individual aggregate “click events”.

Sources liên kết trong graph và cùng chịu event/news nên không hoàn toàn độc lập; CI là query-level uncertainty approximation. Nếu claims rộng: thêm temporal windows và graph-community/block sensitivity khi có partition trước test. Không coi 2 overlapping windows là đủ để suy luận population temporal significance.

Node2Vec báo seed mean/std và từng seed; source bootstrap trong mỗi seed hoặc hierarchical seed/source bootstrap, nói rõ seed n=3 nhỏ. Không nhân 3 seeds×1,000 queries thành 3,000 independent observations. Multiple comparisons exploratory; nếu cần formal tests, paired permutation/sign-flip có giả định exchangeability và Holm correction cho family đã khai báo. Không viết “statistically significant” chỉ vì điểm trung bình cao hơn.

Required diagnostics: Markov backoff μ/η validation surface; δ vs accuracy/runtime; PPR L1 residual vs iteration; history length vs metric; λ sensitivity; degree vs source latency; Node2Vec loss diagnostics **nếu backend hợp lệ** và validation metric/seed stability. Không có epoch/loss cho frequency estimation hoặc PPR fixed-point solution.

Tuning budget: M1B 12 cheap configs; M3 3 δ values; M4C/M4H bắt đầu δ chung M3, thêm 2 values nếu budget; μ weighted {10,100,1000}; M6B 5 λ + tối đa 2 refine; M6A P1 tối đa 5 λ với δ locked; Node2Vec tối đa 12 configs + finalist seeds. Cache candidate scores để λ search không chạy lại PPR. Sau coarse-to-fine freeze không mở rộng search vì test không đẹp.

## 11. Leakage audit và freeze checklist

| Kiểm tra | Cách phát hiện tự động / review | Action khi fail |
|---|---|---|
| Test clicks trong features | Manifest role/path guard; thay test labels không đổi trained artifact hash | Block, rebuild |
| H dựng từ test edges | Parent lineage của H chỉ graph dump; checksum before/after label load | Block, quay lại graph source |
| Temporal overlap | Month sets disjoint, max train < val < test | Block |
| Hyperparameter tuning trên test | Tuning logs chỉ validation split; freeze.json tạo trước test run | Invalidate claimed held-out result |
| Test-based node/query sampling | Source-list lineage train/H only; regenerate hash không cần test | Block |
| Future redirects | Mapping timestamp ≤cutoff, no live API dependency | Quarantine/rebuild mapping |
| Candidates khác nhau | Per-source candidate hash shared across models | Block comparison |
| Model-specific exclusion | Same Q list; failures/fallback ledger | Rerun common evaluator |
| Graph sampling thay support | Subgraph ID và coverage lưu từng run | Tách bảng; không mixed comparison |
| Label-derived transformations | Gains chỉ evaluator; feature normalization fitted train | Block |
| Duplicate months/files | Source SHA/month uniqueness, row audit | Correct ingestion |

Freeze artifact gồm: dataset hashes, mapping/graph/query/candidate hashes, source sample rule, metric/gain/empty-label/tie policies, models and knobs, seeds, numerical tolerance, inference approximation, tuning objective, test periods, list planned ablations, code commit. Bug được tìm sau test cần log và rerun tất cả affected models; một lần test đã xem không còn “pristine”, không che giấu history.

## 12. Required result tables

1. Data attrition + node/pair/mass/candidate coverage.
2. Primary full-denominator metrics mọi models, sample sizes, latency/RSS.
3. Conditional-candidate metrics cùng models.
4. Paired Δ against M1B, 95% CI và win/tie/loss rates.
5. Signal/support/weight ablations.
6. Source/pair strata với counts và uncertainty.
7. Validation tuning + convergence + history curves.
8. Node2Vec same-subgraph table nếu applicable.
9. Temporal robustness nếu applicable, không giả p-value từ 2 months.
10. Case-study table giữ raw counts, rank, degree, eligibility và limitations.
