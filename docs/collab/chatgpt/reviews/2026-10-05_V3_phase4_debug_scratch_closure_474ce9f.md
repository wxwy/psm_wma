# V3 Corrected Phase4 Local-TTT debug scratch closure — GPT review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE4-DEBUG-SCRATCH
- production root（unchanged）：`7fc1fe12cb67e9f37f00f5bfcc049cdcff0ccbf8`
- production child/Gitlink（unchanged）：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- scratch implementation commit：`474ce9fd6ce848890a080ae9e2c568a0e2e0fb63`
- scratch validation marker（empty commit）：`aeab1763a97472afff654041043de3dbbec52e3b`
- frozen design authority：`docs/build/PSM-WMA_V3_phase4_local_ttt_corrected_integration_design_v1.2_2026-10-05.md`

## Verdict

`APPROVE_TO_CLOSE_PHASE4_DEBUG_SCRATCH`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

本 verdict 关闭的是 debug scratch implementation，不把 scratch SHA 推送/提升为 production child，不改变 root Gitlink，不授权 trainer/DCP/正式训练/仿真。

## Independent review findings

1. Phase4A exact-window Local chronology正确：
   - current consumer使用 Phase3 exact-window raw capability；
   - Local evidence严格为 previous exact z0 + previous raw15 action[1]；
   - S0 无 previous evidence / 无 Local prefix；
   - visual96逐值复用 V2 adaptive_avg_pool2d(1,2)；
   - segment 内 raw item去重读取，PAD不读 raw；
   - T16/T32 terminal geometry、stable slot、deterministic rank partition、candidate frontier均有测试覆盖。

2. Phase4B B_stream batched scan保持 row independence：
   - T串行、B并行；
   - row MSE mean后求和，inner_lr不除B；
   - scalar-vs-batched tokens/state/slow-grad/telemetry parity有明确测试；
   - K_local=1 exact zero init，K>1保持原 normal init；
   - telemetry改为 per-row，再汇总 sum/max/count；B=1 legacy telemetry有回归。

3. FSDP/model-owned mixed-state blocker已在实现中按 v1.2闭合：
   - adapter/grouped driver不读取 W0，不调用 core.initial_state；
   - all-fresh state_in=None；
   - all-continuation continuation_mask=None，测试明确禁止 initial_state 调用且 W0 grad=None；
   - mixed仅在现有 Cosmos3VFMNetwork.scan_local_memory 内 initial_state(B)，按 bool mask out-of-place选 continuation/W0；
   - fresh placeholder数值变化不影响 output/W0 gradient；
   - continuation row detached，不回连上一 TBPTT graph；
   - parallelize_vfm_network.py未修改。

4. Batched adapter保持 per-row capability/provenance/transaction：
   - 每 row独立 identity / transaction / pending capability；
   - sidecar state只进入 candidate；
   - member failure、later-GA failure、nonfinite、backward failure、optimizer skip/exception均不发布 live；
   - optimizer成功后单次引用切换发布 candidate frontier/sidecar/scheduler。

5. Grouped weighting与动态几何正确：
   - N_window按全部 active_ga member有效 consumer总数；
   - same-index native mean loss按 n_i/N_window加权，不额外除 active_ga；
   - T32/B3/GA3已有 synthetic proof；
   - independent strict real-data probe：B8/GA2/T16，10 episodes / 3032 windows，member_counts=(128,128)，N_window=256，scan_calls=2，native_calls=32；member1 S0 prefixes全None，member2 S0 continuation prefixes存在；optimizer成功后才发布 live。

6. native Local prefix/action path未改且旧 joint-autograd seam保持有效：
   - independent rerun local_memory_joint_segment_test.py：4 passed；
   - outer loss梯度到 encoder visual/action、slot_queries、W0、local_memory2llm、local_memory_modality_embed及host action path；reasoner保持frozen。

## Evidence

### Strict debug corpus
- cache：`/disk/rl/data/psm_wma_v3_debug_cache/target_atomic_closefridge_left_wrist_snapshot10`
- source：`/disk/rl/data/robocasa_v30/CloseFridge/20250816/lerobot`
- strict catalog：1 task / 10 episodes / 3032 exact windows
- latent shape：`[5,48,12,20]`
- corpus_digest：`aae2573c3b4b8123a060f737de49940259362e9b970111d0b60c2d89f8896df6`
- source_binding_digest：`dc56c44fa9feae8e7e534663ab1acfaa585f28410de7b983ea6cd87deddd35a4`

### Phase3.5 observational parity supporting debug use
ds Evidence：`/tmp/psm_wma_v3_phase3p5_ds_evidence_r3/`
- exact formal pair：`c8a921b38128ed7430577693e76c8f38d856599a / b673ceda5a9ff058abb31224b7006f2d87771ad2`
- CloseFridge episode 26，starts 0/128/257
- pre_crop / post_crop / z0 / temporal[0..4] 全部 exact_equal=true
- global_max_abs=0.0，global_mean_abs=0.0
- status=`OBSERVATIONAL_NO_THRESHOLD`
- 该证据只支持 debug cache同源性，不满足正式 3 task classes / 9 windows thresholded Gate。

### Independent tests
- final focused Phase4A/4B + strict real assets：`59 passed`
- Phase1A/1B/2/3 regression（启动前显式 HF_HUB_OFFLINE=1）：`166 passed`
- native joint prefix/action gradient regression：`4 passed`
- Ruff check：PASS
- Ruff format --check：9 files already formatted
- git diff --check：PASS
- scratch worktree：clean

说明：未预设 HF_HUB_OFFLINE 时，既有 Phase1B/Phase3 tests会在 teardown因测试自身新增该环境变量报错；在 unchanged formal child上可同样复现，因此不是 Phase4 regression。显式将 HF_HUB_OFFLINE=1作为测试启动环境后，整组166项回归全绿。

## Scope / remaining Gate

允许继续：
- 以本 scratch tree作为 Phase5 trainer/DCP/resume 的 source-audit / design reference；
- 继续 CPU/static/debug-only 构建。

仍禁止：
- 把 `474ce9f` 或 `aeab176` push/promote 成 production child；
- 修改 root Gitlink；
- 声称 Phase3.5 `REAL_PARITY_PASS`；
- 正式训练、DCP/resume Gate、sim/eval/SR结论。

Production promotion 仍需 Phase3.5 thresholded REAL_PARITY_PASS 或 Owner 对该 Gate 的显式重新冻结/豁免。
