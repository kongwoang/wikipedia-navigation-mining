# Protocol thực thi đã khóa — study-v3

Người dùng chuyển sang hoàn thiện toàn dự án ngày 21/10/2026. Tài liệu này chốt các chi tiết thực thi trước lần mở held-out labels, thay các lựa chọn còn mở trong planning. Không thay research question để tìm kết quả tốt hơn.

## Dữ liệu và estimand

Train Jan–Mar 2018, validation April; May là test chính và June là fixed-model horizon. Không refit bằng April. H và redirect inventory/event cutoff: 01/03/2018 UTC. Sampling seed 2026, 50 queries mỗi nhóm outgoing training mass 0, 1–99, 100–999, ≥1000; chỉ full out-degree 5–500. Mẫu có 8.094 nodes, 319.694 edges và 200 queries; mọi graph method dùng chung induced H. Giữ đủ outgoing H candidates của query, không giữ mọi boundary edge của intermediate nodes. Global popularity dùng full canonical training corpus; local counts chỉ được chấm trên cùng candidates.

Full observable metrics giữ nhãn ngoài candidates; conditional metrics dùng eligible labels. Nguồn không có label là NA, không thay bằng nguồn khác. Báo số sampled/observable/conditional sources và candidate pair/mass coverage, cả theo nhóm. Đây là sample-conditional retrospective study, không population estimate hay deployable backtest theo publication time.

## Models, selection và numerical controls

- Global, local Markov, uniform và induced in-degree. Backoff grid μ={0,10,100,1000}, η={0,.5,1}.
- PPR-H, PPR-C, PPR-C∩H, smoothed-H với μ=100; damping {.15,.5,.85}. Weighted-H có `c(u,v)+100/d_H(u)` trên H, normalized từng row.
- Score fusion λ={0,.25,.5,.75,1}, dùng candidate-normalized backoff và PPR-H đã chọn. Matrix fusion trộn C∩H row probabilities với H, empty click rows fallback H; damping .5 cố định.
- HITS global trên induced H. A4 H/CH/WH cùng damping .5, WH μ=100, để phân biệt support loss với weighting.
- Node2Vec H/WH: dimensions {32,64}, (p,q)={(1,1),(.5,2),(2,.5)}, seed17 selection; 3 walks/node, length20, window5, 5 epochs, 5 negatives, SGNS workers1. Directed second-order convention kiểm tra cạnh next→previous. Same selected knobs với seeds29/43. A5 weighted matched giữ knobs/seed17 của H; không gọi tuned H/W comparison là weight-only ablation.
- Selection objective: validation macro full NDCG@10, log2(1+count) gain. Khi chênh ≤1e-15, giữ option đầu tiên trong grid khai báo. Không dùng runtime ngẫu nhiên làm tie breaker.
- PPR absolute L1 fixed-point residual ≤1e-8, max_iterations1000, dangling mass→source; bất kỳ solver failure hoặc nonfinite score/loss/vector đều dừng run, không loại riêng source/model hoặc lấy fallback tốt nhất theo test.
- HITS tolerance1e-10 trên L2 iterate difference, max2000; đây không phải cùng residual definition của PPR.

## Ablation và analysis cố định

A1–A6: signal, fixed support/damping, matched embedding weights, λ validation curve. A7 source bins như sampling; pair bins: train-unobserved, positive aggregate count<100, count≥100. Pair metrics dùng original full ranking, không rerank từng bin. A8 trailing1/2/3 months, giữ cutoff/H/query sample; recompute global/local priors, giữ best full-history knobs. A9 May/June cùng predictions, thêm common-source table để tách composition.

Primary paired contrast M6B−M1B trên macro full NDCG@10; source bootstrap2000, seed2026, percentile95% CI. PPR−Markov, WH−H và matched weighted−unweighted Node2Vec là secondary/descriptive. Subgroup CIs exploratory; không claim causal effect hoặc significance từ nhiều comparisons. Node2Vec n=3 seed variability khác source uncertainty.

Case selection: chọn source có chênh lớn nhất cho PPR gain, Markov gain, hybrid thắng cả hai, hybrid failure; chỉ nhận category khi chênh dương. Thêm many-links, low-traffic và một fixed-hash example còn lại. Đây là extreme diagnostic cases, không mẫu chứng minh average gain. Category không tồn tại được ghi riêng, không bịa case. Không dùng case selection để retune.

## Backend fix và freeze barrier

Gensim 4.4.0 có BLAS dot-pointer typedef `except -1`; giá trị -1 có thể hợp lệ. Installer `scripts/install_gensim_fix.py` tạo local version `4.4.0+wnm2`: đổi hai dot typedef sang `noexcept`, thêm negative-dot probe và dùng typed `scipy.linalg.cython_blas` wrappers cho scopy/saxpy/sdot/snrm2/sscal thay raw Fortran function-pointer casts. Upstream source SHA256 và supplementary fastss.pyx SHA256 cố định; regenerate Cython bằng 3.1.2 cho Python3.13, giữ upstream license. Không thay SGNS objective, walks hoặc ranking formula. Không dùng cache từ incomplete study-v1.

Run signature gồm algorithm hash, config/data hash, Python/dependency versions, lock hash và installer hash. Mọi model/ablation predictions cùng freeze manifest phải ghi xong **trước** lần đầu evaluator đọc May/June. Test results không được dùng để mở rộng grid. Completed run không overwrite. Preparation/audit artifacts từ các lượt trước được giữ; real-training smoke chỉ đọc training graph.

Acceptance trước test: toy tests, negative-dot regression, real graph finite-vector/loss smoke không native warning, validation candidate coverage có ledger. Final acceptance: required tables/figures/cases/report/demo tái tạo từ frozen artifacts, resource measurements và limitations rõ; không yêu cầu model phức tạp phải thắng.

Portability correction trước khi phân tích test: study-v2 đã kết thúc trên macOS, nhưng CI Linux thất bại ở negative-dot probe của backend wnm1. Không đọc test scores/cases để quyết định sửa. Study-v3 chạy lại nguyên grid trên wnm2; không dùng v2 làm final results hoặc chọn giữa v2/v3 theo accuracy. Native call interface thay đổi, không thay objective/split/hyperparameters.

Typed BLAS API tham chiếu: https://docs.scipy.org/doc/scipy/reference/linalg.cython_blas.html; build study khóa SciPy1.16.3, dùng đúng `int*` signatures từ installed cython_blas.pxd. Không tuyên bố hỗ trợ tùy ý SciPy ILP64/new major versions.
