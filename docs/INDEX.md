# PSM-WMA Documentation Index

This repository intentionally keeps historical design, Gate and review material. Use the layers below instead of browsing all files alphabetically.

## Completed evaluation results

- **[RoboCasa365 Local-TTT / No-TTT 训练监控与配置归档](eval/training/robocasa365_v3/README.md)** — 真实训练配置/身份、Fresh/Resume历史、每100步Loss和梯度/Fast Weight/吞吐/显存曲线及Checkpoint保留策略；两组全分辨率逐步档案仍在服务器，GitHub只存已获准的小型摘要。
- **[RoboCasa365 Local-TTT 正式评测总报告（跨Checkpoint）](eval/reports/PSM-WMA_V3_RoboCasa365_Local_TTT_Evaluation_Report.md)** — 统一入口；R03 iter20000：454/900、SR 50.44%；R07 iter27700：580/900、SR 64.44%。包含18 Task的完整对比、Local-TTT Fast Weight证据、真实Batch/吞吐、语言覆盖差异及不可直接因果归因的说明。
- [R07 原始语言指令与900EP索引（138组）](eval/reports/2026-11-05_R07_900EP/instructions.md) — 全量原始Task+instruction分组、各组N/S/F/SR及成功/失败EP编号。
- [R07 机器可读审计归档](eval/reports/2026-11-05_R07_900EP/audit_summary.json) — 原始Run身份、900份结果校验、25,566次Replan、4,285个真实Native Batch、Online Fast State统计与源SHA；独立只读聚合。
- [R03 900EP 正式评测报告：Local-TTT iter20000](eval/reports/2026-11-04_R03_900EP/README.md) — 2026-11-04；18 Task × 50 EP，454/900成功，SR 50.4444%；配置、任务表现、性能、Local-TTT运行诊断、媒体与Core完整性、来源hash。
- [R03 全部139组原始语言指令及900 EP成功/失败索引](eval/reports/2026-11-04_R03_900EP/instructions.md) — 按精确Task+instruction统计N/S/F/SR，保留原文和逐组Episode编号；明确小样本及场景/目标混杂限制。
- [R03 机器可读汇总](eval/reports/2026-11-04_R03_900EP/audit_summary.json) — 已完成Run的只读数据归档；不授权新实验，不代表No-TTT增益、M8/B8或Resume已验证。

## G2 — technical survey and detailed design working draft

- **[G2 详细设计 v0.2：大实体场景图、Left 机器人视角与历史照片维护](build/PSM-WMA_G2_detailed_design_v0.2_2026-11-06.md)** — 当前补充与纠正：仅独立、通常固定且相对较大的实体进入 SG 并维护图片；小物件只保留语义关系/必要状态，不建专属图库；全部历史图必须来自原 robot0_agentview_left、合法相机高度与机器人可达配置，并保存拍摄机器人位姿。自然保留机械臂、按大实体/状态/可达视角维护有界代表图、事件触发区域上下文刷新等是讨论建议，尚未授权实施。
- [G2 详细设计 v0.1：空间记忆初始化、时序维护与历史视觉训练数据](build/PSM-WMA_G2_detailed_design_v0.1_2026-11-06.md) — 保留四种初始化×两种维护、**Full Map + MuJoCo GT Update 优先**、基图+状态增量+关系事件+时间索引等无冲突决定；其中自由相机、给所有对象补图等图像建议已由 v0.2 覆盖。
- [G2 技术调研报告 v1.0：技术路线比较与收敛](build/PSM-WMA_G2_technical_survey_v1.0.md) — 2026-11-02. Preserves the research comparisons, decision history, external evidence, nav_sg reuse rationale, and the Owner-confirmed G2 scope. This is a technical survey, not a detailed design, implementation acceptance, or training authorization.
- The Owner's 2026-11-06 corrections in v0.2 take precedence over conflicting v0.1 image-memory proposals. Confirmed decisions and proposed implementation choices remain separate. Existing G1/No-TTT production code, checkpoints, runtime contracts, historical frozen documents, and nav_sg PRs remain unchanged. No render/training/implementation authorization is implied by these docs-only updates.

## 1. Current truth — read these first

- **Phase3.5 numerical supplemental Gate (2026-10-08):** `build/PSM-WMA_V3_phase3p5_numeric_compatibility_gate_v1.0_2026-10-08.md` — bounded held-out 3-task/9-window threshold 0.0625 for pre/post/z0, OPEN until verified; current full-corpus 8×H100 fresh 1-optimizer-step authorized after snapshot10. No formal30k authorization.
- **Corrected V3 dataset acceptance receipt (tools-only):** `build/PSM-WMA_V3_dataset_acceptance_receipt_design_v0.1_2026-10-08.md` — offline draft/approve/verify tooling and Round-3 count audit. No threshold relaxation, no Phase1B fast-path override, no formal-training authorization.

- **Current Corrected V3 Phase 6 authority:** `build/PSM-WMA_V3_phase6_online_inference_eval_design_v1.1_2026-10-05.md` — Phase6A scratch, Encode1 thresholded parity, and no-policy real Online Local smoke are CLOSED on exact child `8c3800565f66cfbce2929264f1c2a7854137482e`. Production promotion is CLOSED on formal pair root `b04fc2d4f1b2685bf9fb0e2b0f6277674bd2f93c` / child `8c380056...`. GPU-readiness precheck is GREEN, but the current single 24GB RTX 4090 is not authorized for optimizer smoke. Next authorized execution is 8×H100 fresh iter0→iter1 when available.
- **Corrected V3 design authority:** `build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md` — Owner-confirmed latest Cosmos RoboCasa/raw15 host + V2 Local-TTT; cache-first shared composite latent; H_pred/R default16. Phase4/5/6 corrected implementation has been promoted to production child `8c380056...`.
- **Current Corrected V3 Phase 5 authority:** `build/PSM-WMA_V3_phase5_trainer_dcp_resume_design_v1.0_2026-10-05.md` — trainer/optimizer/DCP/resume scratch is CLOSED and included in production child `8c380056...`. Production-pair strict snapshot10 preflight PASS. Formal training remains unauthorized pending H100 readiness sequence.
- **Current Corrected V3 Phase 4 authority:** `build/PSM-WMA_V3_phase4_local_ttt_corrected_integration_design_v1.2_2026-10-05.md` — exact-window Local-TTT scratch is CLOSED and included in production child `8c380056...`; grouped B8/GA2/T16 and real no-policy Online Local evidence are green.
- **Current Corrected V3 Phase 3.5 authority / Owner refreeze:** `build/PSM-WMA_V3_phase3p5_real_cache_online_vae_parity_design_v1.1_2026-10-05.md` plus `build/PSM-WMA_V3_phase3p5_owner_refreeze_v1.0_2026-10-05.md` — CloseFridge parity is exact; the historical >=3 task classes / >=9 exact windows coverage requirement is no longer a production-promotion blocker and is deferred to a pre-formal-training supplemental Evidence Gate.
- **Current Corrected V3 Phase 3 authority:** `build/PSM-WMA_V3_phase3_cached_latent_sft_model_cache_hit_design_v1.0_2026-10-05.md` — GPT-frozen cache-driven SFT transport and optional OmniMoT cache-hit seam; inner collate Tensor and packed model list ABIs are distinct. This docs-only freeze does not implement Phase 3 or authorize ds/GPU, training or simulation.
- **Closed Corrected V3 Phase 2 authority:** `build/PSM-WMA_V3_phase2_raw15_state15_hpred16_design_v1.1_2026-10-05.md` — official raw15/state15 and H_pred16/VAE cache contract; closure review: `collab/chatgpt/reviews/2026-10-05_V3_phase2_closure_471b7fec_ce07cb6f.md`.
- **Closed Corrected V3 Phase 1B authority:** `build/PSM-WMA_V3_phase1b_cache_source_binding_design_v0.4_2026-10-05.md` — GPT-frozen cache-to-flat-source binding design; closure review `collab/chatgpt/reviews/2026-10-05_V3_phase1b_closure_d7aa5673_21e60d6e.md`.
- **V3 supersession:** earlier migration v1.0/v1.1 and their B1/iter500/current-frame/streaming execution Gates are historical and superseded by v3.0. Publishing v3.0 does not approve the existing child implementation or authorize training/evaluation.
- `../README.md` — project overview and entrypoints
- `../PROJECT_STATUS.md` — current SHA, readiness and validated metrics
- `current/architecture.md` — current system architecture
- `current/local_memory.md` — canonical Local Memory / TTT semantics
- `current/training.md` — train and resume workflow
- `current/evaluation.md` — LIBERO evaluation workflow
- `current/experiments.md` — current experiment matrix and evidence

For Corrected V3, read v3.0 first; conflicting older operational summaries do not override the Owner-confirmed design or the newest exact-pair review/handoff.

## 2. Canonical design authority

- `build/PSM-WMA_00_project_proposal_v1.4_frozen.md`
- `build/PSM-WMA_01_technical_survey_v1.7_frozen.md`
- `build/PSM-WMA_02_detailed_design_v2.1_frozen.md`
- `build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md`
- `build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.9.md`
- `build/PSM-WMA_Local_Memory_A2_delivery_runbook_2026-09-18.md`
- `build/PSM-WMA_V3_Local_TTT_on_latest_Cosmos_RoboCasa_detailed_design_v3.0_2026-10-04.md` — current Corrected V3 design authority; production conformance requires subsequent implementation and Evidence.
- `build/PSM-WMA_V3_migration_detailed_design_v1.1_2026-10-04.md` — historical B1/iter500 migration design, superseded by v3.0; not an execution authority.
- `build/PSM-WMA_G2_detailed_design_v0.2_2026-11-06.md` — current G2 image-memory constraints and maintenance proposal; v0.1 retains non-conflicting initialization/update and temporal-storage decisions.

## 3. Historical engineering record

`build/` also contains superseded versions, implementation designs, source audits, remediation plans and Gate runbooks. They are retained for provenance. A newer frozen/refrozen document or an explicit durable decision in `../MEMORY/DECISIONS.md` supersedes older conflicting text.

`collab/` contains agent inboxes, independent reviews, feedback and archives. It is useful for reconstructing why a decision was made, but it is **not** the recommended way to learn the current architecture.

## 4. Machine-readable evidence

- `../artifacts/CANONICAL.json` — authoritative pointers
- `../artifacts/g0/sync_a2_final_verification_2a9df880_v3.json` — engineering verifier
- `../artifacts/g0/a2_long_run_readiness_2a9df880/a2_long_run_readiness_v1.json` — long-run readiness verifier

## 5. Internal ledgers

- `../TODO.md` — current task queue
- `../SESSION.md` — execution / handoff ledger
- `../MEMORY/DECISIONS.md` — durable engineering decisions
- `../AGENTS.md` — agent collaboration and execution governance; Corrected V3 role overrides are recorded in v3.0 and the newest canonical handoff.

These files are operational infrastructure, not the project introduction.
