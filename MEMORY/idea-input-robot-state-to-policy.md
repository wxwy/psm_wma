---
name: idea-input-robot-state-to-policy
description: 用户洞察：将机器人状态（state）输入给 policy 可能改善动作精度问题
metadata:
  type: project
---

**来源**：2026-08-25 用户在分析 libero_goal/libero_10 失败模式时提出。

**背景**：CFG 跨 suite 验证（#25）期间，用户逐 task 分析 baseline 失败原因：
- goal task_5 失败："太压住盘子导致不好移动"（动作精度问题）
- libero_10 task_3/9 失败："动作精度不够导致的偏差出现物品位置不到位影响后续动作"+"对关门、关抽屉这类动作理解不到位"

**洞察**：这些失败模式都是"动作执行精度"问题，与语言指令无关。CFG（语言引导增强）对此无效。

**用户建议**：**将机器人状态（state）也输入给模型**，让 policy 在生成动作时知道自己当前实际位置/姿态，避免过度移动、压住物体、动作偏差。

**状态**：待讨论（用户明确说"记下来，后面再讨论"）。

**Why**：动作精度问题在多个 suite（goal task_5、libero_10 task_3/9）的 baseline 上反复出现，是除"语言指令被忽略"之外的第二大失败模式。如果加 state 输入能让 task_5 / task_3/9 的 SR 提升，比 CFG 收益更直接。

**How to apply**：
- 当前 policy 输入：language + video（agentview + wrist）
- 提议输入：language + video + state（end-effector pose, gripper state, joint positions）
- 训练侧影响：`libero_lerobot_dataset.py` 已读 state（`observation.state` + `observation.states.*`），只需加 policy input 链路
- 评估侧：CFg 跨 suite 验证（#25）跑完后，下一轮评估应同步验证"加 state 输入"的对照

**关联**：
- [[cache-5suite-merge-build]] — 后续 cache build 可能需要新增 state tensor 编码
- [[libero-4in1-acceptance-handoff-20260824]] — 4in1 baseline
- [[overfit-iter200-eval-result]] — R05/R06 早期 overfit 也观察到"精度不够"问题