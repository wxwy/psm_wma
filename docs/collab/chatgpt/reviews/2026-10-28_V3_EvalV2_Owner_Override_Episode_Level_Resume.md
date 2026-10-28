# Owner Override — Evaluation V2 必须 Episode 级恢复（取代 Task 整项重跑）

- 日期：2026-10-28
- **用户直接决定**：`Episode 37 中断 就应该从 Episode 37 重新测`。
- 上一轮 Design Gate formal pair：Root `dc750f8e258d10a33e7a195cf907926b1c98bd7f` / Child+Gitlink `746c5cf2f2324104a62fb71510343aa40d3976c5`；作者 Evidence `23f2d3a1fda08b9c8214c22b12fbb0592c578dcd`。
- 上一轮 `REQUEST_CHANGES` Review：`docs/collab/chatgpt/reviews/2026-10-28_V3_RoboCasa_EvalV2_r1_dc750f8e_746c5cf2_design_review.md`。
- **本文件是 Owner 修改冻结需求的补充裁决，不是新的 formal design SHA 的 Code/Design Gate，且不升级/改变前一轮 `REQUEST_CHANGES` verdict。** 在前一报告里认可的 `Task-level restart` 建议在此显式 **WITHDRAWN / SUPERSEDED**。保留原始报告不篡改审核历史；Codex 下一版必须按此新要求修订设计。

## 1. 新的硬性恢复合同

以 `Task=OpenCabinet`、逻辑 `ep_037` 中断为例（0-based）：

1. `ep_000 … ep_036` 已通过 **Core Episode** 原子提交的 `success` 或 `behavioral_failure` 必须直接保留、复用，禁止移动到 `abandoned`、禁止再仿真、禁止重算模型输出。
2. `ep_037` 若未产生有效 Core Result，必须从这个逻辑 Episode 独立重试；上次异常 Attempt 保留于独立诊断空间，不覆盖、不遗失错误证据。
3. `ep_038 … ep_049` 继续正常评测，最终每个逻辑 Episode 唯一计入一个有效 `success/failure`，共50个，全部 Task 共900个。
4. `behavioral_failure` 是正常有效结果，**不能以失败为由反复重试求成功**。只有 Core 无效/中断才重试；媒体缺失/损坏不能导致重试或改写 SR。
5. Pending、Invalid 和 Process Error 明确区分。若 Episode 执行完成但因非媒体 Core cleanup/验收失败而 Invalid，重试同一 logical Episode；已有效提交的前缀不受影响。Crash before vs after atomic commit 必须区分。
6. 新900命名空间从零开始，不读取/迁移旧431原始文件；原始 Source/Model/Local/动作核心 ABI、Environment `_check_success` 权威和 C 视频独立原则继续冻结。

## 2. 必须解决采样一致性（禁止伪装官方连续随机流）

现有 Child 的旧 native 协议为：一个 Task 建一个 env，`seed=0`，中间真实 `env.step()`，连续50次 `env.reset()`。**重新 new env(seed=0) 再调用 reset 一次不能凭空还原第37次的场景随机状态**，仅跳过前36次 reset 也未被证明与有动作执行的 RNG 流等价。

为了实现上述 Owner Hard Requirement，下一轮 Codex 设计必须明确选择并证明下列**其中一个**场景恢复机制：

A. **推荐实现：从 Fresh ep0 开始使用版本化的 Per-Episode deterministic scene protocol。** 全部900个 Episode 的场景种子依据固定实验 Base Seed、Task、logical Episode Index 及 Sampler Version 通过稳定 SHA256 派生；Episode 0～49 全部遵守同一采样机制（不得仅中断时给 ep37 临时派生 seed）。记录 `scene_seed`、可核对 scene identity、真实 `environment_reset`、Policy sampler RNG 与 Local Session 的重置契约，须以真实 robosuite/RoboCasa 实际支持的 Seed/Reset 方式接线并验收。若无法在共享 Env 中确保独立 per-episode scene seed 切换，则以独立新 Env reset/构造方式获得可证明的同一 Episode 场景；可优化进程/模型 Server 复用，但不得损害随机状态隔离。**这种设计是 NEW benchmark/sampler version，不能宣称等价 RoboCasa 旧的 literal-seed Task-continuous50 protocol。** 必须所有被比较模型使用相同 `task,episode` 场景集合并冻结 before rollout。
B. **若目标必须保留原 official Task-continuous reset 协议**：实现真实 episode 边界的完整可恢复状态快照/重放（所有影响后继 scene 的 Env RNG、Simulator/controller 状态、Policy sampler RNG，以及有作用的 Local session 状态），逐项实证新进程恢复后的 ep37/38… 与未中断连续执行的同 Scene identity/Action/Local chronology；仅靠 seed0 或重复 reset 不算实现。若无法证明，则不能同时声称「精确历史 RNG 连续性」与「ep37-only resume」。

对当前新900工作，优先推荐 A（效率、简单、Episode 级重试），并将与原官方连续复位口径的区别列入 `manifest.json` 和最终报告。任何改变场景分布、复位顺序、Policy RNG 生命周期必须随新的版本化科学协议冻结及通过真实 Canary，不可仅靠合成 FakeEnv 测试宣布等价。

## 3. 对前一 Design Findings 的调整

- **D3 HIGH — NEW REQUIREMENT / prior recommendation superseded**：
  - 当前 r1 `tools/v3/episode_eval_v2_prototype/contract.py:14-15,62-85`、`tools/v3/episode_eval_v2_prototype/store.py:223-321`、`tools/v3/episode_eval_v2_prototype/scene_test.py:77-94` 与设计 §6 选择 `restart_incomplete_task_from_literal_seed_v1`、整 Task Archive+重跑，不满足 Owner 明确的 Episode37-only Resume。
  - **Acceptance**：新 `r2` formal design 使用清晰版本化 per-episode outcome/scene/retry ledger；在 `ep_037` 中断后，证明 ep0..36 内容/哈希/inode 不变且绝不执行，ep37 以固定原计划 scene identity 重试，ep38..49 正常继续；多次重试无 scene cherry-picking，真实 seed 固定与 Worker/GPU/Scheduling 无关；对 post-core-commit crash、media-only error、invalid Local、进程 error、主进程重启、并发重复写入给出 fail-closed 行为。
- **D1 HIGH 仍 OPEN，需按 Episode/Attempt 级恢复范围修订**：历史 process_errors 仍不可永久污染新有效执行；错误必须绑定对应 `(Task, logical Episode, attempt/stream, process)`，新合法 Episode attempt 完成并核查所有权清理后，旧错误不再永久阻止 clean qualification，同时保留不可变原始诊断。若发生非 Episode 级不安全运行环境故障，阻止不安全复用/提交。
- **D2 MEDIUM 仍 OPEN，需为 Episode claim/start 及 Task initial claim 设计 crash-safe 原子初始化**：不能因为首次创建 `Task` 状态与 `episodes/` 目录之间中断就永远 BLOCKED；不能覆盖老有效 Episode。

## 4. Gate 与权限

- 前 formal design pair `dc750f8e/746c5cf2` 未变，因此**不再重复技术审核**，前 Design verdict `REQUEST_CHANGES` 保留。
- Codex 需在隔离 branch 提交 **新的** r2 design/prototype SHA，按 D1/D2/D3 做增量审核；不得原样实施 r1 的 Task-level 重跑。
- C 方案仍为环境 `_check_success` 决定 SR，生成/回放视频仅诊断；新 run Public Task/Episode layout、原始视频单份保存及不自动 ffmpeg/video_view、模型/训练不变。
- 本 Owner Override 仅修改下一轮设计标准，**不授权** 合并 V3、真实 DCP、GPU/Server/Simulator、Canary/900 rollouts、删除历史431或干预现有训练。
