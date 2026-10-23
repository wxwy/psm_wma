# V3 Flexible Episode Resume — 第一阶段设计／隔离原型独立审核

日期：2026-10-23（CST）。
**VERDICT: `REQUEST_CHANGES`** — 仅限第一阶段 Design + isolated Prototype Gate；未审核也未修改未来生产实现。

## A. 精确身份和证据范围

- Formal **Design/Prototype Root**: `44f0953ac75591d7e60394df6337a6ed133f3f08`。
- Formal **Child/Gitlink**: `813a550dab5d6b5b5e3be90d38bb97527956b4dc`（未变）。
- Owner frozen request: `cc7820bee1a73bd2bb2078cb7f00239944f66d37`，`docs/collab/chatgpt/requests/2026-10-23_Codex_V3_RoboCasa_flexible_episode_resume_contract.md`。
- Reviewed baseline: `cc7820bee1a73bd2bb2078cb7f00239944f66d37`；作者标出的既有生产实现 Root `e6a970caba4bdc77f7d9b56a6a8fbcdafe57f1e0`。
- 审核时 V3 docs/evidence HEAD `562373cc2f8a6b7c4bf4d0599db9e001f1345ba1`（提交 handoff、证据与 Inbox；**非 formal design SHA**）。
- 作者文档 `docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r1.md`、交接 `docs/collab/codex/reviews/2026-10-23_flexible_episode_resume_design_author_handoff.md`。
- 作者 Gate `docs/collab/codex/evidence/2026-10-23_flexible_episode_resume_design_author_cpu/gate.json` 报告 **161 passed、0 failure/error/skip，Ruff/format/syntax PASS**；GPT 独立查看源代码、测试与证据索引，**未独立执行这161项 CPU 测试**。与基线比较，仅新增设计、prototype、SESSION/TODO；`scripts/`、Child/Gitlink、configs、vendor 均未改变。无真实 DCP、GPU、Kitchen 或生产 Resume 测试。

## B. 正确方向（当前保留）

1. `model_identity` 四项硬不变：checkpoint 字节身份、num_steps、action_horizon、guidance；差异明确 old/new，禁止同目录混合。
2. tasks/episodes/seed 取本次 invocation；`old3/request5` 补2、`old8/request5` 只计前5，历史原位保留；跨任务集合可扩缩。
3. 原始 `EpisodeRef` / Source digest / Attempt 不被强行改写为新 digest；Local-TTT closed-frontier、每集 JSONL、媒体按**原政策**校验；旧视频 none→all 不强制重跑、缺口按当前策略报告。
4. 旧 seed family 与新请求 seed、实际传环境的 effective_seed 分开，mixed/unknown 被标注；当前 Worker 错误不能被“已完成数量足够”吞掉；`.run.lock`、重验时序和 no-write-on-mismatch 方向正确。
5. 作者清楚限定非生产 prototype 和后续独立实现 Gate；不把 synthetic CPU 证据冒充真实闭环验证。

## C. 当前 blocker

### HIGH-01 — 新的逐集 Seed 方案未把「全新任务的既有官方采样协议」与「续测缺集」隔离

- **位置**：`docs/collab/codex/designs/2026-10-23_V3_RoboCasa_flexible_episode_resume_design_r1.md:104-119,133-143`；`tools/v3/episode_resume_prototype/scene_sampling.py:22-49,52-90`；现存 Child `cosmos_framework/simulation/robocasa/closed_loop_eval.py:184-213,593-599,627-651`（Gitlink 813a550d）。
- **根因与证据**：当前正式新评测的语义是每个 Task 用用户的 literal `seed` 创建一次环境，然后同一实例按顺序 reset 多个 Episode；Child 源码甚至明确记录“same test-scene sequence”。候选设计却笼统指定每个“new Episode”用 `SHA256(requested_seed, task, logical_slot)` 的 **derived effective_seed** 新建环境、仅 reset 一次。一旦这种路径接管首次 `--resume=false` 评测，或 4→18 扩任务时的新 Task，**即使用户仍指定 seed=0，也会换掉正常首跑所用的场景序列**，RoboCasa 的 benchmark/已有 4task×5 的场景可比性不再成立。标记 `MIXED_SAMPLING_PROTOCOL` 无法代替避免非 Resume 行为回归。
- **违约**：本 Gate 授权的是 Resume 灵活复用，不是默许无 Resume 的标准新评测改变 Scene seed/reset 协议。Owner 请求的 seed 是可控实验输入，不能默认将所有新集的 literal 环境 seed 变为派生数且只靠日志告警。
- **验收条件**：在设计中明确分流并提交 CPU 行为证据：① 全新 Run、当前任务此前0集的新 Task 仍走既有的 Task级环境构造+相同 literal seed+连续 resets（或另行获得 Owner 对“修改全新评测场景协议”的明确授权和独立新 benchmark 身份）；② 只有真正补缺的 Episode 在不能恢复历史 RNG 时使用独立派生 seed，保留 source physical→logical 映射及醒目的 mixed-protocol 标注；③ task 扩张4→18，新增加的14 Task 在正常全新执行时不被无意改成另一种采样协议；④ fake-env 计数和场景序列负例分别覆盖 fresh 5ep、fresh added Task、partial3→5、seed changes。禁止改模型/Local-TTT/action path。

### MEDIUM-02 — 旧 Attempt `COMPLETE` 标记与证据矛盾时仍当作正常闭合集摄入，未显式标注破损完成声明

- **位置**：`tools/v3/episode_resume_prototype/episode_evidence.py:247-261,420-526`；`tools/v3/episode_resume_prototype/episode_evidence_test.py:30-33,106-122,210-222,237-246`；现存 Root `scripts/robocasa_eval_results.py:299-350,446-451`。
- **根因与复现依据**：测试有意构造 `attempt.json.status=COMPLETE`、原定5集但仅两个 Episode end，甚至无 `process_cleanup.json`，且断言摄入这2集成功。可是当前生产 `finish_attempt` 只有完整 `validate_attempt`（exact5集、有序进度、进程组 cleanup、原策略媒体等）通过后才可提交 `COMPLETE`。该测试文件构造的是**不可能由合法 v1 COMPLETE 产生的矛盾状态**。按 Episode 层面复用历史 `RUNNING/FAILED` 闭合前缀是对的；但一个损坏的 COMPLETE 声明不应在未明确指出完整性矛盾时被当作正常 COMPLETE 来源。
- **违约**：Owner 要求原证据不可篡改、旧腐败证据有明确诊断、Resume 不得以错误的完成证明计算正式 COMPLETE/SR。
- **验收条件**：冻结 `COMPLETE marker contradiction` 的策略：对于原标为 COMPLETE 的 attempt，核对它自身必须具有原 protocol.trials 所宣称的完整进度、结果和进程 cleanup 证明；矛盾时明确 `CORRUPT_LEGACY_COMPLETE_MARKER`／`INCONSISTENT_COMPLETE_ATTEMPT`，不得仍称为正常已验证 COMPLETE。可选择 fail-closed 停止该来源，或提出 **显式、隔离、醒目标记的异常 salvage**（由 Owner 批准），但不能静默降级；`RUNNING/FAILED` 中的闭合 Episode 应继续可正常复用。补 `COMPLETE 2/5`／缺 cleanup／合法 COMPLETE 5/5 对照测试。

### MEDIUM-03 — 非连续历史槽位缺少自动 recovery authority 时会跳过失败槽，错把更高新槽当补缺

- **位置**：`tools/v3/episode_resume_prototype/plan.py:194-224`；`tools/v3/episode_resume_prototype/plan_test.py:105-119,316-329`；设计 `...design_r1.md:84-92`。
- **根因与可推导例子**：`build_plan` 只在调用者明确提供可选 `pending_slots` 时才优先重试。若已验证逻辑槽位为 `{0,1,3,4}`、失败/丢失的 reservation 为槽 `2`，请求5集、`pending_slots` 在恢复／迁移时未重建，则 `reused=4`、`new=1`，`next_slot=5`，实际计划新槽 `5` 而非重试 `2`；逻辑缺口留存且新增为第六个逻辑编号，可能掩盖失败 reservation 与 episode 来源。当前测试只验证显式提供 pending 的情况；没有 crash/rebuild 后 sparse-history 负例。
- **违约**：冻结契约要求不借用半集、未完成 reservation 优先重试、logical source slot 稳定、crash 后可重建而非依赖丢失的内存参数。
- **验收条件**：在设计中指定权威来源（持久 reservation catalog + 原进度诊断）与 crash 恢复重建算法；推导的 pending 与显式 pending 合并后确定性重试，遇不可判定/冲突不得静默跳过。补 `{0,1,3,4}/request5/missing2`、重启不带 `pending_slots`、同槽重试新 attempt、缩小后再次扩大的 CPU 用例。原文件不改写，原引用不重号。

## D. 非阻断落实项（第二阶段实现 Gate 要求）

- 全 DCP payload SHA 在新身份/锁前后多次读取可能造成显著磁盘 I/O。请记录真实 checkpoint 只读扫描的预算和进度，再决定高频 Resume 复用缓存方式；不能将缓存当作历史未知 hash。
- 重做新 summary 的权威发现方式：旧根目录 `screening_summary.json` 不被覆写时，需要明确指向最新 `_invocations/<id>/resume_report.json`／当前视图的只增索引，防止用户按旧路径误读“任务完成数”。这属于输出可用性，不得改写历史 v1 摘要。
- 161项是作者 synthetic/prototype Gate；后续必须有新的 Root/Child implementation SHA、完整 CLI→锁→source/episode validator→新 Worker/Local-TTT→summary CPU fake-server行为 Gate 及 DS 独立 CPU验收。新 Video policy 缺失仅标缺口，不生成历史视频；四参不匹配在任何写与 GPU 前报错；真实 GPU/仿真只归 Owner。

## E. 判定和边界

**`REQUEST_CHANGES` — 当前第一阶段设计 Gate 不批准直接冻结并进入生产改造。**

这是**设计语义和 CPU fixture** 的窄范围整改，现有生产脚本及 Child 并无此 Gate 新增 defect，当前迭代无须修改模型、权重、Vendor、Local-TTT 或运行中的评测/G1。Codex 回应以上三个 blocker，更新设计与原型负例形成新精确 design SHA / 原 Child Gitlink，再送 GPT 增量复审；不需要重复无关的161项测试。

本 verdict **不授权** 修改运行中的工作树、不授权真实环境修复/模型加载、GPU、仿真、训练或正式 Resume 启动。
