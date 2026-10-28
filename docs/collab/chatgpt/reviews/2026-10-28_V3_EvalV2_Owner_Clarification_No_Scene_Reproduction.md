# Owner clarification — Episode 级 Resume 不要求原场景复现

日期：2026-10-28。**Owner 最新明确要求：「如何保证 Episode 37 的场景采样可复现？不用复现。」**

## 当前冻结要求（优先级高于此前建议）

- **强制 Episode 级进度恢复**：`Episode 37` 中断 / 没有有效 Core Result 时，保留已原子提交的 `ep_000…ep_036` 成功或正常行为失败结果，重新执行逻辑 `ep_037`，后续执行 `ep_038…ep_049`。不要求从 Episode0 重跑整个 Task。
- **不要求恢复被中断 Episode 的原场景**：不恢复 MuJoCo/robosuite RNG 快照、不重放前36个 Episode、不保证重试的 Scene ID、物体位置或初始化状态与原 ep37 相同。失败/无效尝试可以重新采样一个新的合法 Task 场景。
- **不要强制全900 Episode 采用独立固定哈希 Seed 或每 Episode 新建环境**。前文件提出的 A/B 二选一（固定每集确定性场景或完全 RNG 快照重放）**被 Owner 此次澄清明确撤销为强制前提**；这个强制条件可能平白改变科学采样协议并增加工程负担。
- 初始未中断 Task 可以继续使用原有 `task seed + 单环境连续 env.reset()` 协议。遇到中断的 Task 从剩余 Episode 起使用重新创建的正常仿真环境/新采样 Stream；不需要维持与旧 Stream 的精确 RNG 连续性。新 Stream 可执行多个后续 Episode 的连续 Reset，无需每 Episode 重建。**须实际记录 Stream/Attempt/有效 Seed/场景采样模式/逻辑 Index/Resume 边界**，不要将混合 Stream 的50集冒称“单一连续50 Reset”或“与未中断 RNG 序列逐场景等价”。恢复段若采用新 Seed，要记录其产生与固定规则；不要不经核验只用原 `seed=0` 重置并默许重复旧场景为 Episode37。
- **只重试未获得有效 Core 结果的 Episode**（Interrupted、Invalid、无完整原子提交）。正常 `behavioral_failure` 也是有效结果，必须计入 SR，不能为了更好表现换场景。媒体写入失败、缺视频或无法解码不是核心无效，不重测、不影响环境 `_check_success()`。
- `ep_037` 的失败 Attempts/过程错误独立保留并可诊断，不覆盖/修改有效前缀。若已成功原子提交 ep37 而后仅进程或媒体路径发生错误，不能重复该 Episode；对真实未完成核心 cleanup 的情形按 Core Invalid 规则处理。既有有效结果不丢弃。
- 最终报告明确同一 Task 可能是多个仿真 Stream 的接续采样结果，而不是精确连续同一 RNG 流；此为新评测协议明确事实，必要时进行可比性/采样偏差说明。此设计目标是 **900个有效 Task Episode 样本的任务成功率**，非固定场景逐样本重放。真正需要 matched scenes 的另一个 Benchmark Gate 可另行制定。
- 旧431 Episode 不迁移，C 方案取消评测主链路自动 ffmpeg 严格解码、视频仅诊断，结构 Task→Episode，模型/训练/动作/Local 算法不变。

## 取代关系（append-only 决策历史）

- 上一 r1 Design Formal Pair：Root `dc750f8e258d10a33e7a195cf907926b1c98bd7f` / Child `746c5cf2f2324104a62fb71510343aa40d3976c5`，Verdict `REQUEST_CHANGES`；**formal pair 没变化，绝不重新技术审核或升级 Gate**。
- 原 r1 GPT 审核对 `whole-Task restart` 的认可已被 Owner 的「从 Episode37 续测」撤回。
- `docs/collab/chatgpt/reviews/2026-10-28_V3_EvalV2_Owner_Override_Episode_Level_Resume.md` 中 §2 的 A/B 恢复要求（特别是 mandatory deterministic per-episode scenes）**再由本次澄清明确 SUPERSEDED**。保留原文作为历史，不应令 Codex 按较早要求做不必要的 RNG 恢复；本文件与最新 `CODEX_INBOX.md` 优先。
- D1（过程故障可核验地分范围关闭）、D2（首次 Claim 崩溃可恢复）仍然保留；D3 修改为「Episode-level progress Resume + new-scene allowed」**而不是固定原场景可复现**。

## 对下一版设计验收示例

真实或隔离 State Gate 应构造 `Task T`，先提交 ep0..36（包含正常失败），ep37 异常且无合法 Core Commit → 关闭旧 Session 和所有权进程，创建新仿真 Stream/Attempt，合法采样并完成 ep37，接着完成 ep38..49；核验前37个有效结果的 SHA/字节/inode 未变化、无一次重执行，最终50个逻辑索引唯一且全部有 Core 结果、invalid attempts 不进入 SR 也不抹除。场景身份与原 ep37 不必相同，且必须记录原/新采样 Stream 边界。测试 post-commit crash、媒体失败、行为失败、跨 Worker 重启均不重复有效 Episode。

下一步 Codex 先提交相应 r2 design/prototype **新 formal SHA**，供 GPT 对 D1/D2/D3 增量复审；不代表当前 V3 已有生产实现，也不授权合并 V3 或启动真实 GPU/900 Episodes。
