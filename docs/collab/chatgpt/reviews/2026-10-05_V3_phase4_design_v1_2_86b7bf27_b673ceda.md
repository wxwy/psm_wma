# V3 Phase4 Local-TTT corrected integration design v1.2 — GPT formal review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE4-DESIGN
- formal design root：86b7bf27cfc73ae308526a8bcac6961e89dbb228
- child/Gitlink：b673ceda5a9ff058abb31224b7006f2d87771ad2
- design：
  docs/build/PSM-WMA_V3_phase4_local_ttt_corrected_integration_design_v1.2_2026-10-05.md
- design SHA256：
  50c97ec55cca2f224fe16fce3c1e081bf1792073599785c7b5416a4718017339

## Verdict

APPROVE_PHASE4_DESIGN_V1_2
IMPLEMENTATION_BLOCKED_BY_PHASE3P5_REAL_PARITY

本 verdict 只确认 Phase4 v1.2 设计闭合、可作为后续实现 authority。
它不授权 cx 修改 Phase4 production，不授权 ds 执行 Phase4，不授权 GPU、训练、仿真或行为结论。

## Design review findings

1. V2 Local chronology 已恢复为唯一 authority：
   previous exact z0 + previous exact raw15 transition -> fast update -> current Local prefix -> current policy。

2. Local visual 已明确回到 V2：
   current exact z0 [48,H,W] -> adaptive_avg_pool2d(1,2) -> visual96；
   B1 mean/RMS、separate-camera latent、endpoint/floor mapping全部退出 corrected active route。

3. Phase3 raw sample是唯一 consumer/evidence capability：
   不再创建第三套 raw/cache/source reader；
   consumer payload 与 previous evidence 都从同一 RoboCasaExactWindowCachedDataset raw item派生。

4. segment geometry 正确：
   valid consumer = F-16；
   T仅控制 TBPTT；
   T16/T32均为真配置；
   segment boundary detach W_t 但不 reset memory。

5. planner/grouped geometry 正确：
   B_stream / active_ga / T 独立；
   cache实际 task membership；
   deterministic rank partition；
   stable slot / continuation / terminal rebind。

6. B_stream scan math正确：
   T串行，B rows并行；
   inner row MSE mean后求和；
   inner_lr不除B；
   scalar-vs-batched token/state/slow-gradient parity为 formal acceptance。

7. v1.1 的 FSDP blocker已闭合：
   adapter/grouped driver禁止读 W0 或调用 core.initial_state；
   all-fresh继续现有 state_in=None；
   all-continuation直接用 detached batched continuation state且不触碰 W0；
   mixed batch只在现有 FSDP-registered Cosmos3VFMNetwork.scan_local_memory 内调用一次 core.initial_state(B)，再按 continuation_mask out-of-place 选择 continuation/W0 rows。

8. 该 mixed-state设计保持正确 outer gradient：
   fresh rows保留 W0 gradient；
   continuation rows不回连 W0/上一TBPTT graph；
   all-continuation不人为构建 W0 zero-gradient graph，避免 weight-decay 语义漂移。

9. FSDP seam最小：
   允许最小修改 cosmos3_vfm_network.py 的现有 scan_local_memory signature/assembly；
   method name保持不变；
   parallelize_vfm_network.py不改，继续复用现有 register_fsdp_forward_method(model,"scan_local_memory")。

10. transaction边界正确：
    member可推进 candidate；
    live在 optimizer成功前保持不变；
    member/backward/nonfinite/later-GA/optimizer-skip均丢弃 candidate；
    成功只做单次 live引用发布。

11. Local prefix必须真实进入 native Cosmos action path；
    Phase4不修改 Phase3 video_latent policy path、memory_prefix/attention seam、trainer/DCP或 inference/eval。

## Current hard blocker

Phase3.5 formal child：
b673ceda5a9ff058abb31224b7006f2d87771ad2

source review已通过，但真实 parity execution当前是：

BLOCKED_ASSET_PATH

缺少执行环境显式提供：
- CACHE_ROOT：exact_window_v1 cache root
- SOURCE_ROOT：matching flat LeRobot v3 source root
- WAN_VAE_PATH：local Wan VAE file
- PARITY_OUT：fresh output json path

必须先完成：
1. authorized dry-run
2. real observational parity
3. owner/GPT freeze numeric tolerance（若尚未冻结）
4. thresholded REAL_PARITY_PASS

只有 REAL_PARITY_PASS 后，GPT 才会发送 Phase4 implementation authorization 给 cx。

## Governance

当前角色：
- Owner：最终裁决
- GPT：设计 / independent review / Gate
- cx：实现 / formal CPU-static tests / commit
- ds：execution / Evidence only；不得修代码

Phase4 implementation前不得：
- 猜资产路径
- 扫描训练服务器寻找历史 cache
- 用 B1 cache代替 exact-window cache
- 跳过 Phase3.5 parity
- 直接开始 Local production修改
