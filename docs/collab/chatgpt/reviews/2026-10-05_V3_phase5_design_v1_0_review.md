# V3 Corrected Phase5 trainer/DCP/resume design v1.0 — GPT formal review

- 日期：2026-10-05
- Gate：V3-CORRECTED-PHASE5-DESIGN
- production root before docs freeze：`da7ef0c2c0de2dadf21e4c017a30458d78f2a678`
- production child/Gitlink：`b673ceda5a9ff058abb31224b7006f2d87771ad2`
- Phase4 scratch reference：`474ce9fd6ce848890a080ae9e2c568a0e2e0fb63`
- design：`docs/build/PSM-WMA_V3_phase5_trainer_dcp_resume_design_v1.0_2026-10-05.md`

## Verdict

`APPROVE_PHASE5_DESIGN_V1_0_FOR_SCRATCH_IMPLEMENTATION`

`PRODUCTION_PROMOTION_STILL_BLOCKED_BY_PHASE3P5_THRESHOLDED_REAL_PARITY`

本 verdict 允许 cx 在独立 scratch/debug worktree 上实现 Phase5 CPU/static contracts；不允许改 production child/Gitlink，不授权正式 GPU 训练。

## Review findings

1. 当前 H3-C/H3-D/H3-F 骨架可复用：native trainer callbacks、scaler-aware optimizer success、candidate/live publication、DCP dataloader callback、strict same-job resume均有价值。
2. historical trainer仍绑定 `robocasa_grouped_segment` / Stage-A binder，并硬编码 GA2；必须切到 Phase4 `ExactWindowRankPlanner / ExactWindowSegmentProducer` 并使 active_ga 动态。
3. upstream `ImaginaireTrainer.train` 已支持任意 `config.trainer.grad_accum_iter`，因此 Phase5只需令其精确等于 planner.active_ga，并在 subclass中对最后 member执行 optimizer。
4. historical resume schema包含固定8 slots、active_GA=2、policy chunk32、consumer33与旧 `CatalogFrontier`，必须以 incompatible corrected v2 schema取代；H_pred16 / frames17 / dynamic B/T/GA/K必须进入 profile。
5. native DCP `checkpoint/dcp.py` 已同时保存 model/optim/scheduler/trainer(grad_scaler+iteration+RNG)/dataloader(rank pkl)，无需新增 checkpoint 系统，应保持零 diff。
6. FSDP `scan_local_memory` 已通过现有 `register_fsdp_forward_method` 注册，Phase5不得新增第二 scan method或修改 parallelize_vfm_network.py。
7. optimizer inventory继续采用 generation + Local slow / reasoner frozen；Local总参数量必须从实际K/profile派生，不能把 historical K4 count 165312当成所有配置的绝对值。
8. all-continuation窗口允许 W0.grad=None；不得为了 inventory/finite检查制造零梯度，否则会改变 AdamW weight-decay语义。
9. same-job restore必须两阶段验证后单引用发布 live；任何 iteration/cache/source/config/profile/frontier/scheduler/sidecar mismatch都必须零 live mutation。
10. historical H3F formal observer固定32 fwd/bwd只适用于T16/GA2/full member；corrected observer必须从plan valid_count几何计算预期 callback 数。
11. current 24GB 4090 host只用于 CPU/static/debug；正式 readiness/kill-resume Gate留到后续训练服务器。

## Implementation authorization

cx 可从 Phase4 scratch tree继续：
- 修改 frozen design §24 允许的 trainer/resume/test/新 corrected launcher 文件；
- 必要时只增加 ExactWindow planner 的 non-mutating public frontier validator；
- 运行 CPU/static/regression；
- 只做 scratch commit，不push、不promote。

禁止：
- 修改 `checkpoint/dcp.py`
- 修改 `parallelize_vfm_network.py`
- 修改 Phase1A/1B/2/3 data contracts
- 修改 inference/server/eval
- 启动正式训练

实现完成后形成新的 scratch implementation SHA，再由 GPT fresh review。
