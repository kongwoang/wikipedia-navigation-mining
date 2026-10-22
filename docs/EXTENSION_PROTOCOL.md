# Extension protocol v1 — frozen before July–September label parsing

Ngày 22/10/2026. User yêu cầu thực hiện toàn bộ quality-improvement plan. Original study-v3 và May/June scores không thay đổi. Phần boundary/null/query diagnostics trên May/June là post-hoc exploratory; July–September là new-period evaluation theo protocol dưới đây, không chọn mô hình bằng test scores.

## Data và chronology

Independent H/redirect cutoff01/03/2018 giữ nguyên. Clickstream Jan–June đã có; July/August/September lấy từ Your.org mirror do origin trả403. Mirror được ghi nhận trong Wikimedia infrastructure tracker https://phabricator.wikimedia.org/T415193 . Lưu URL,bytes,SHA256; không có upstream checksum thì nói rõ local fingerprint, không tự gọi verified publisher hash. Opaque acquisition không parse labels.

Giữ original200queries cho boundary/rolling; query candidates là toàn bộ outgoing H đã khóa. Ba rolling windows: train Mar–May/valJune/testJuly; trainApr–June/valJuly/testAugust; trainMay–July/valAugust/testSeptember. Không thay models/grid/candidate policy sau test đầu tiên; previous test có thể thành future train/validation theo chronology đã khóa. Báo từng window và common-source metrics; không coi overlapping windows là independent trials.

## Models / tuning

Original-context extension: Markov/backoff (μ0,10,100,1000;η0,.5,1); PPR-H/C/WH (δ.15,.5,.85; WHμ100); fixed-score fusion λ0,.25,.5,.75,1. Topology tie-break rank tuple(count,PPRscore,stablehash) giữ thứ tự mọi unequal local counts. Adaptive fusion λ(u)=eligible_train_mass/(eligible_train_mass+τ),τ10,100,1000; τ chọn validation. Source no clicks dùng topology cho adaptive/tie-break; không gọi reliable cold-start evidence nếu thiếu labels. Global/uniform/indegree/HITS dùng làm controls. CycleRank giới hạn simple directed cycles length≤k,k2/3; score mỗi node sum exp(−length); exact bounded enumeration, không gọi approximate two-hop heuristic. N2V-H/W dùng selected original knobs (H d32/W d64,p.5,q2,seeds17/29/43,walks3,length20,window5,epochs5,negative5) cho rolling robustness; không mở embedding grid sau old test.

Selection mỗi rolling window: validation macro full log-gain NDCG@10; tie≤1e−15 first declared option. Full/conditional macro/weighted metrics giữ nguyên evaluator. Predictions của tất cả models trong window phải lưu trước đọc test month đó. Không dùng best-test seed.

## Boundary / resource controls

Build canonical full H CSR và C từ existing historical tables, giữ original candidates. Full-H PPR resource pilot10originalqueries chọn stable hash; peak RSS≤8GiB và extrapolated200-query scoring≤30min. Nếu vượt gate dùng deterministic nested graph≤50k nodes/3m edges và report scope; không thay theo accuracy. Khi fullH qua gate: H-only PPR ởδ.15 (original selected) so original inducedH; Markov, fusionλ.5, tie-break, adaptiveτ chọn April; thêm fullC/WH tạiδ.15 nếu resource gate cho phép. Original counts/global priors không đổi khi mở graph. Same δ/λ không retune theo May/June. Báo rank overlap, same candidates, graph size/retention,residual,cost và quality delta.

## Null và query controls

Degree-preserving directed double-edge swaps trên original inducedH: chỉ rewire edges có source không phải query; giữ node inventory,in/outdegrees và query outgoing edges. Seeds101–105; target5×modifiable_edges accepted swaps, cap100×edges attempts. Cấm selfloops/duplicates. Nếu target không đạt vẫn report actual swaps, không gọi mixed equilibrium. Chỉ PPR-Hδ.15 và fixed λ.5 fusion; behavior/candidates giữ nguyên. Descriptive null ensemble, không causal/permutation significance claim.

Hai query panels bổ sung seeds2027/2028:50 mỗi original train-defined traffic stratum,outdegree5–500,loại sources đã chọn ở panels trước. FullH context cố định cho tất cả panels (nếu fullH gate không đạt: không claim tách query khỏi graph sampling). Models Markov,fullH-PPRδ.15,fusionλ.5,tie-break; May/June analysis exploratory. Common candidate semantics; không lấy nhãn để chọn nguồn/thay cold queries.

## Statistics / failure policy

Primary new-period contrast: topology tie-break−Markov trên full macro NDCG@10. Secondary fusion/adaptive/CycleRank/embeddings và boundary/null contrasts descriptive. Paired source bootstrap2000seed2026,per-window intervals; groupn<2 không CI. Report effect sizes và sources/coverage, không p-hack hoặc kết luận equivalence từ CI chứa0. Solver residual≤1e−8,max1000; any failure dừng affected run, không drop riêng source. Hash protocol/code/raw/prepared artifacts; immutable per-stage caches chỉ reuse khi signature khớp. Numerical implementation changes sau test phải ghi audit và không chọn theo accuracy.

## Deliverables

Extension modules/tests, independent manifests, boundary/full graph diagnostic, null ensemble, two query panels, three rolling windows, updated report/presentation/defense và scripts. Không cần fullgraph Node2Vec/CycleRank: rolling model comparison trên original fixed graph, boundary experiment chỉ subset model có explicit scope. Không làm current Wikipedia/session/causal claims.
