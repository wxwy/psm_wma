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

## G2 — canonical dataflow design, earlier drafts, optional visual research
- **[G2 详细设计 v1.0：连接归属驱动的上下／四墙正交视图](build/PSM-WMA_G2_detailed_design_v1.0_2026-11-07_root_affiliation_orthographic_wall_views.md)** — **最新视图候选**：Floor 支撑/包含链及其子物件进入俯视；非 Floor 链进入含天花板背景的仰视；每面墙仅展示该墙的直接/间接连接链。明确连接**可递归传递归属**、跨 Floor/Wall/Ceiling 建筑根不可自动传播、连接≠接近、机器人握持例外；推荐四墙正交立面优先于房间中心 45°×8 透视，同时记录真机 nav_sg 墙面实例分割/关系能力的现有缺口。仍未执行渲染。

- **[G2 详细设计 v0.9：整屋上下正交图与房间锚点验收](build/PSM-WMA_G2_detailed_design_v0.9_2026-11-07_house_bev_room_anchor_acceptance.md)** — 最新候选验证：统一整屋 XY 正交投影、Left 实际世界高度作为分割起点；Room.center 附近自由位置候选与低分辨率视角覆盖评分；固定房间轴 0°，试 45°×8、FOV/pitch 自适应；2Hz 彩色背景与高频 SG 的版本/过期内容分离。先单 Episode 审图，通过后再批量 L2/L3。仅为设计，尚未执行。

- **[G2 彩色点云、10Hz 更新与 3DGS 对比源码审计](build/PSM-WMA_G2_colored_pointcloud_10Hz_vs_3DGS_audit_2026-11-07.md)** — **新增已验证源码事实**：nav_sg 自带 ColorCloudMap<PointXYZRGB> 真实 RGB-D 颜色体素融合，区别于 ObjectMap3D<PointXYZ> 及按 ID 伪彩；真机/仿真彩色云默认发布2Hz，G2 当前 offline 回放禁用。审计全量复制发布、仅最新帧异步队列、动态 voxel 擦除缺口、10Hz 真机性能 Gate，与 3DGS 快渲染但优化较贵的文献对比。v0.8 的“缺少 RGB 融合”旧表述已纠正。当前**无实测10Hz结论**。

- **[G2 详细设计 v0.8：仿真—真机空间视图可生成性约束](build/PSM-WMA_G2_detailed_design_v0.8_2026-11-07_sim_real_renderability_contract.md)** — **最新硬性约束**：所有进入 Cosmos 的 Lower/Upper BEV、房间方向图及其他空间视图，都必须能由真实 nav_sg 三维地图产物经同一 Renderer 生成；MuJoCo 仅代替 GT 数据源。区分已实现 XYZ/Occupancy 与尚缺的 RGB 外观融合、未知/遮挡 mask、共同 L2/L3 ABI 和真机可生成性 Gate；覆盖旧文档中“MuJoCo 能渲染就能用”的过强假设。仅为设计。

- **[G2 详细设计 v0.7：上下正交 BEV 与自适应房间规范视角](build/PSM-WMA_G2_detailed_design_v0.7_2026-11-07_orthographic_bev_canonical_views.md)** — **最新讨论修正**：顶部 perspective 是房间固定备选；优先上下正交几何投影，**不另建 Costmap/Traversability 标签**；方向图是只借鉴 Left 高度的共光心**规范虚拟相机**，FOV/pitch 可调，45°×8 只是初始采样而非保证覆盖。提出 Room 几何中心→自由空间候选→低分辨率可见性评价→必要时加角度/俯仰/第二锚点的自动流程。覆盖 v0.6 的对应旧表述，仍为待验证设计。

- **[G2 详细设计 v0.6：分层正交 BEV + 房间中心方向视图](build/PSM-WMA_G2_detailed_design_v0.6_2026-11-06_layered_bev_room_directional_views.md)** — **最新视图方案讨论**：主 BEV 优先空间位置/可通行性，讨论 Left 高度上下正交分层与高位透视对照；每房间在有效锚点按世界/房间绝对方向每 45° 生成 8 张 Left 参数视图，90° 4 张为子集；严格区分 room canonical view 与真实机器人历史 Left，全部可选视图均需 L2/L3 cache。尚未冻结选型或执行。

- **[G2 详细设计 v0.5：可渲染三维空间地图→真实视觉 BEV](build/PSM-WMA_G2_detailed_design_v0.5_2026-11-06_renderable_spatial_bev.md)** — **最新可视化输入约束**：BEV 必须从真实三维几何/纹理/材质渲染，不能由节点名称/坐标画示意图；SG 负责实体与关系，不是 RGB 渲染源。记录 nav_sg 原生 PointXYZ/SG 缺失渲染资产的接口差距、MuJoCo 正交顶视参考、遮挡策略与 L2/L3 缓存绑定。覆盖 v0.4 中可能被理解为“简化语义绘图即可”的建议；尚未实施。


- **[G2 详细设计 v0.4：空间视图及 Latent Cache](build/PSM-WMA_G2_detailed_design_v0.4_2026-11-06_spatial_view_latent_cache.md)** — **当前训练数据缓存设计草案**：对 Full Map + MuJoCo GT 预生成 BEV 和可选房间方向/三视图，并独立缓存冻结视觉编码器 latent；按状态/视图内容去重，严格绑定既有 G1 accepted cache corpus 与真实帧时序；Global Spatial Encoder 保持可训练。具体视图和模型接线待确认，不授权构建/训练。


- **[G2 详细设计 v0.3：nav_sg 原生数据流与 MuJoCo GT 替换边界](build/PSM-WMA_G2_detailed_design_v0.3_2026-11-06_navsg_mujoco_dataflow.md)** — **当前优先设计**。用户最新修正：SG 构建阶段不再按“大而固定”筛除对象；大小/重要性筛选留到 Cosmos BEV/空间读出。明确原生几何/占据→RoomPipeline、YOLOE/SigLIP→ObjectMap3D→SGManager 与 G2 on/inside 证据链，区分 MuJoCo GT 占据导入、GT 实例/状态导入和缺失的 GT 关系适配层。当前只讨论 Full Map + MuJoCo GT Update，没有代码、训练或仿真授权。
- **[历史视觉记忆专项技术调研：OPTIONAL](build/PSM-WMA_G2_historical_visual_memory_OPTIONAL_survey_v1.0_2026-11-06.md)** — 独立研究比较与备选实现依据。历史多视角图库**不是**当前 Full-GT 主线前置条件。调查中的“大实体有图库”只记录为历史备选设定，不约束当前 SG 构建。
- [历史 Left 图像自动采集/维护备选方案](build/PSM-WMA_G2_Left_history_capture_automation_proposal_v0.1_2026-11-06.md) — 备选设计材料，不代表现在要实现。
- [G2 详细设计 v0.2：历史阶段大实体/Left 视角方案](build/PSM-WMA_G2_detailed_design_v0.2_2026-11-06.md) — **部分已被 v0.3 覆盖**；其中“只有大实体进入 SG”的早期约束已撤销。不能用 v0.2 限制 G2 的对象入图。
- [G2 详细设计 v0.1：初始化×更新与时序数据](build/PSM-WMA_G2_detailed_design_v0.1_2026-11-06.md) — 继续继承四种初始化×两种维护和基图+状态增量+关系事件+时间索引等不冲突原则；部分历史图像设想已降级备选。
- [G2 技术调研报告 v1.0：路线来源与机制比较](build/PSM-WMA_G2_technical_survey_v1.0.md) — 保留早期背景，不覆盖后来的 Owner 设计调整。
- 历史 V3/G1/Local-TTT frozen 文档、现有生产数据、nav_sg PR 与训练/评测任务均未因本轮文档调整而变更。

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
- `build/PSM-WMA_Local_Memory_v0.3.5_active_route_member_shape_refreeze_design_v0.3.md`
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
