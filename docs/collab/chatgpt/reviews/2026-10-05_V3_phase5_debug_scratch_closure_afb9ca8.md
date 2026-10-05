# V3 Corrected Phase5 trainer/DCP/resume debug scratch closure — GPT review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE5-DEBUG-SCRATCH
- production root/design authority：`a5f84f075b1076ecfbc37817675a5516c4fb5f48`
- production child/Gitlink（unchanged）：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase4 scratch parent marker：`aeab1763a97472afff654041043de3dbbec52e3b`
- final Phase5 scratch implementation/test SHA：`afb9ca8d9f8ec080518a838f56a681073eb4b495`
- frozen design：`docs/build/PSM-WMA_V3_phase5_trainer_dcp_resume_design_v1.0_2026-10-05.md`

## Verdict

`APPROVE_TO_CLOSE_PHASE5_DEBUG_SCRATCH`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

`GPU_READINESS_NOT_AUTHORIZED`

本 verdict 只关闭 Phase5 trainer / optimizer / DCP / resume 的 CPU/static/debug scratch implementation。不得将 scratch SHA 直接提升为 production child，不改变 root Gitlink，不授权正式 GPU readiness、训练、sim/eval 或 SR 结论。

## Independent review findings

1. Phase5A trainer 已切到 corrected exact-window authority：
   - `ExactWindowRankPlanner / ExactWindowSegmentProducer` 为唯一 active planner/producer；
   - historical `robocasa_grouped_segment / Stage-A binder / materialize_member` 已退出 corrected trainer；
   - `active_ga` 动态绑定 `config.trainer.grad_accum_iter`，GA1/2/3 均有测试；
   - CP!=1 fail-closed；
   - grouped native batch 不再硬编码 B<=8，terminal 小 batch 合法。

2. optimizer/scaler transaction 与 Phase4 candidate/live 语义一致：
   - 最后 GA member 才 unscale / finite-check / optimizer；
   - present selected gradients 必须全有限，但不要求每个 selected parameter 每 window 都有 grad；
   - all-continuation W0.grad=None 合法，没有制造零梯度；
   - scaler skip 不推进 scheduler，且 `GroupedLocalMemoryWindow.finish(False)` 不发布 candidate；
   - optimizer exception / later-GA failure 同样保持 live 不变；
   - 成功 optimizer 后才发布 candidate，再 zero-grad。

3. optimizer inventory 已改为实际模型精确 allowlist：
   - generation：`moe_gen/time_embedder/vae2llm/llm2vae/action2llm/llm2action/action_modality_embed`，其中 `language_model.*_moe_gen` 属 generation pathway；
   - Local：encoder/core、`local_memory2llm`、`local_memory_modality_embed`；
   - reasoner、tokenizer/VAE 与其它参数必须 frozen；
   - K1/K4/K8 的实际 Local 参数数由模型派生，不再依赖 historical K4 固定总数。

4. Phase5B corrected resume schema 已闭合：
   - format 升级为 incompatible `psm_v3_corrected_grouped_local_v2`；
   - profile 绑定实际 rank/world_size/seed/B/GA/T/K/Local dims/inner_lr，并冻结 action64/H_pred16/frames17；
   - snapshot 只允许 successful optimizer publication 后且 iteration>=1；
   - cache manifest/corpus/source binding/config/profile 全部进入 restore identity；
   - dynamic slot IDs = rank*b_stream+local_slot；
   - terminal slot 禁止 fast state，continuation slot 必须有 detached finite fp32 CPU fast state；
   - restore 在 off-live candidate 上完成全部验证，最后单次 `window._live = candidate`，所有 corrupt/mismatch 失败保持 live identity 不变；
   - uninterrupted 与 save/restore 后 next-plan/loss/gradient parity 有测试。

5. DCP integration 复用现有 checkpoint authority，没有修改 `checkpoint/dcp.py`：
   - same-job strict resume 要求 model/optim/scheduler/trainer/dataloader 五组完整，并要求本 rank `dataloader/rank_N.pkl`；
   - official base DCP fresh warm-start 使用 `load_training_state=False`，不要求 Local rank-pkl；
   - same-job 不允许用 Local skip 掩盖缺失；
   - zero-step checkpoint 明确拒绝。

6. trigger/resume offset 与 upstream trainer 契约一致：
   - `GroupedTriggerLoader(max_iter, active_ga)` 总 microsteps = max_iter*active_ga；
   - upstream `_resume_dataloader_fetch_count` 在 CP=1 返回 iteration*grad_accum_iter；
   - `set_start_iteration(fetched)` 因此以 raw microstep 偏移恢复，不重放 completed GA member。

7. corrected Phase5 config authority 已闭合：
   - semantic digest 包含 cache manifest/corpus/source binding、raw15/state15/H16、T/B/GA/K、Local dims、optimizer/schedule/mesh；
   - Edge config 与 base DCP model metadata 以内容 SHA256 进入 digest；
   - absolute cache/source/output path 不进入 semantic digest，路径迁移保持 digest；
   - model witness 内容变化会改变 digest。

8. tokenizer contract 保持 Phase2 authority：
   - 不修改/放宽 Phase2 validator；
   - runtime tokenizer 使用 manifest 完整 `encode_exact_durations=[17,61,73]`，不是 historical `[33]` 或退化 `[17]`；
   - DictConfig 写回后通过 `OmegaConf.to_container` 的 plain view 再做严格 validator；
   - mismatched duration/chunk map fail-closed。

9. process-global HF offline 行为按 Phase1B 保持不变：
   - `_ensure_hf_hub_offline` 会同步设置 env、huggingface_hub constant 和 per-process applied flag；
   - 因此 Phase5 不做只恢复 env 的错误“清理”；测试启动时显式 `HF_HUB_OFFLINE=1` 以避免 conftest 将既有 process-global contract 误报为测试泄漏。

## Real debug preflight

strict cache：
`/disk/rl/data/psm_wma_v3_debug_cache/target_atomic_closefridge_left_wrist_snapshot10`

matching source：
`/disk/rl/data/robocasa_v30/CloseFridge/20250816/lerobot`

model assets：
- Edge：`/disk/rl/models/Cosmos3-Edge-Policy-DROID`
- base DCP：`/disk/rl/models/Cosmos3-Edge-Policy-DROID-dcp`
- Wan VAE：`/disk/rl/models/wan22_vae/Wan2.2_VAE.pth`

结果：
- strict catalog = 1 task / 10 episodes / 3032 exact windows；
- latent = fp32 `[5,48,12,20]`；
- Phase1A -> Phase1B -> Phase2 -> Phase3 cached path可读；
- Phase5 real snapshot10 preflight：`1 passed`；
- 未加载训练模型、未运行 optimizer、未启动 GPU training。

支持性 Phase3.5 observational Evidence：
- CloseFridge episode 26，starts 0/128/257；
- pre_crop / post_crop / z0 / temporal 全部 exact_equal=true；
- global_max_abs=0.0；
- 仅证明 debug cache 同源，不构成正式 thresholded parity Gate。

## Independent tests

最终 scratch `afb9ca8`：
- Phase5 focused trainer/resume/config：`72 passed, 1 skipped`；
- optional real Phase5 snapshot10 preflight：单独 `1 passed`；
- comprehensive Phase4 + Phase5 + Phase1A/1B/2/3 + joint/native Local + DCP regression：`319 passed, 3 skipped`；
- 3 skips 均为未注入真实资产时的 optional smoke；对应真实 Phase4/Phase5 smoke 已单独通过；
- Ruff check：PASS；
- Ruff format --check：15 files formatted；
- py_compile：PASS；
- git diff --check：PASS；
- forbidden diff：空（`checkpoint/dcp.py`、`parallelize_vfm_network.py`、Phase1A/1B/2/3 data、inference/server/eval 均未改）。

## Scope / remaining Gate

CLOSED：
- Phase4 debug scratch；
- Phase5 trainer/optimizer/DCP/resume CPU/static/debug scratch。

仍 OPEN：
1. Phase3.5 thresholded production parity：要求至少 3 task classes / 9 exact windows；当前只有单 task observational exact parity。
2. production promotion：scratch commits 尚未进入 production child/Gitlink。
3. GPU readiness：正式训练服务器上的 fresh 1 iter -> 3 iter+save -> kill/resume -> readiness10 尚未执行。
4. formal training / simulator / eval / SR：未授权。

允许下一步：
- 保持 production child/Gitlink 不变；
- 先完成 Phase3.5 thresholded parity 或由 Owner 显式重新冻结该 production Gate；
- Gate 关闭后，形成 production promotion candidate，再单独做 fresh review；
- promotion 后才进入 Phase5 GPU readiness Gate。


## Final Evidence Supplement — 2026-10-05

Formal scratch target **未变化**：`afb9ca8d9f8ec080518a838f56a681073eb4b495`。按审核规范，本段仅补强 Evidence，**不重新进行技术审核，原 verdict 不变**。

在固定 scratch SHA、显式注入 strict real assets 后，独立最终矩阵：

- comprehensive Phase4 + Phase5 trainer/resume/launcher + Phase1A/1B/2/3 + joint/native Local + DCP regression：**334 passed, 0 failed, 0 skipped**；
- strict real Phase5 snapshot10 preflight：**1 passed**；
- strict real Phase4 B8 / GA2 / T16 probe：PASS（`member_counts=(128,128)`，`N_window=256`，`scan_calls=2`，member1 S0 无 prefix，member2 S0 continuation present，optimizer success 后才 publish）；
- Ruff check / Ruff format --check / py_compile / git diff --check：PASS；
- forbidden-file diff：空。

因此此前 review 中的 `319 passed, 3 skipped` 为较早 evidence；本 supplement 以 **334 passed, 0 skipped** 作为更强最终 CPU/static/debug 证据。

Verdict remains:

`APPROVE_TO_CLOSE_PHASE5_DEBUG_SCRATCH`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

`GPU_READINESS_NOT_AUTHORIZED`
