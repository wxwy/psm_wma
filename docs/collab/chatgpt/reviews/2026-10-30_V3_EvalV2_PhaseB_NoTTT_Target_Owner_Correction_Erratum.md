# ERRATUM — V3 EvalV2 Phase B：Owner 明确目标是接替 No-TTT 评测，不是验证 Local-TTT

- 日期：2026-10-30（CST）。
- 原真实执行 Formal Root `7c74dc26ac4837f193727ecf847b9b64554c18b2` / Child+Gitlink `53c3c95202e14d3b72d236eee6899a80acf82989`，**未改生产源码**。此文是 Owner 对目标的直接澄清和此前错误审核路线的更正，**不是新的实现或 Code Gate**。
- 被更正的先前 Review：`docs/collab/chatgpt/reviews/2026-10-30_V3_EvalV2_PhaseB_Canary_7c74dc26_53c3c952_TTT_Checkpoint_Compatibility_Evidence_Gate.md`。
- Owner 当前明确：**“我们就是接替nottt，为什么要强制要求是local-ttt？”** 实际目标是让 **EvalV2 接替 No-TTT 评测链路**，在 No-TTT checkpoint 上检查同一GPU多Sim并发、native B=2推理、Episode lifecycle、resume/隔离及结果/视频证据。
- **纠错结论**：先前“换 Local-TTT checkpoint / 输入 checkpoint 选错 / 不是生产能力问题”的推荐和结论 **RETRACTED**。NoTTT checkpoint 是这次用户目标的预期输入；当前 EvalV2 PhaseB 的 TTT-only 执行要求是对 NoTTT 用例的**production capability/scope blocker**，不是应该靠替换目标模型消除的 Gate。原F5-P1存储修复的 `APPROVE_CODE` 不变。
- **新真实 Canary Gate：`REQUEST_CHANGES` — `BLOCKED_NOTTT_PHASE_B_UNSUPPORTED`。** 对上述旧实现 SHA 的事实不重审，只因Owner澄清用途而修正先前审查建议/验收方向。不将该校正理解为 LocalTTT 路径自身已有功能的回归或要求移除 TTT 功能。

## 独立源码核对：为什么仅删 required 校验不能解决

1. Root `scripts/eval_robocasa_18task_queue.py:257-284` 的 `server_argv()` 无条件传 `--local-memory-mode required`，Root `scripts/robocasa_eval_v2/runtime.py:143-198` 的 Phase B 调用该入口并追加原有 transaction batch options。
2. Child `cosmos_framework/scripts/action_policy_server_robocasa.py:623-663,894-930` 必须 required，并且 `k_local=4/local_dim=32`；`robocasa_local_memory_policy.py:74-97` 要求真实 `model.net.local_memory_runtime`；`robocasa_session_transactions.py:150-167` 直接要求 `adapter.memory` 存在；`robocasa_v2/contract.py:72-92` 当前 Protocol 固定 LocalTTT required。
3. Child `robocasa_session_transactions.py:308-348,379-398` 对成功响应/重复请求依赖 `adapter.snapshot.responses` / `snapshot.fast` 与 Local consumer frontier；Child `robocasa_batch_transactions.py:190-279` 每批调用 `adapter.prepare`、`commit_many`、`status`，归档响应也归 Local snapshot 管理。
4. Child `action_policy_server_robocasa.py:1231-1258` 的 `_transaction_batch()` 无条件收集 `_local_memory_prefixes=tuple(self.local_memory_adapter.prefixes(u)[0]...)`；Child `simulation/robocasa/eval_v2_transactions.py:23-69` 的 `PolicyTransport` 当前总用 `AssignedLocalMemoryClient` 和 Local evidence。**不只是CLI一行**。

## 修正后的最小实现/验收范围（移交Codex、尚待新源码 Gate）

- **显式 NoTTT / LocalTTT policy mode**：PhaseB的并发/Batch能力应与模型是否有 Local-TTT 解耦。NoTTT 使用 `off`，根据已固定/可追溯模型配置明确选择；缺少或矛盾的模型/配置必须fail-closed，禁止静默自动fallback。将模式纳入不可变评测 Manifest/Run identity；不混合不同模型/协议的Episode结果。
- **最小复用现有 Session/Batched Transaction owner**，让 NoTTT 能继续使用真实Slot lease、generation、response replay、ACK、bounded deadline、B=2 merge、End/cleanup；NoTTT 的防重复/响应缓存属事务身份账本，**不可伪造fast-weight/Local prefix或要求 `local_memory_runtime`**。在已验证的当前观测+state数据路径上原样调用 Model native batch一次，Local prefix应缺席/disabled而非借LocalTTT模型。
- **保留原 LocalTTT required 旧合同与测试，不做广泛架构重写**；必要的变更仅限 Root EvalV2 mode/config/manifest/launcher/runtime及Child ActionServer/事务/Sim薄层（实际文件由Codex只读审计后缩小），新旧两模式的Batch总量/Session隔离、模型输入/输出/恢复和原版Local严格fail closed行为均需CPU增量负例。
- 下一次真实验收仍然是 Owner 原定 **NoTTT checkpoint、1 GPU、2 Sims、B=2、CloseFridge/OpenCabinet 各2 Episode**；需要显示实测 native batch size2、4条有效结果、MP4/显存/延迟与owned-only cleanup。不能偷换为LocalTTT checkpoint；不自动扩大到900。
- 原F5-P1持久化Bug **CLOSED**，其 Code Gate `APPROVE_CODE` 保留；新NoTTT PhaseB能力 `OPEN`，需Codex新正式Exact Root+Child实现后GPT narrow fresh review。原本仅带 NoTTT 的失败输出不能充当恢复成功或性能结论。

此为纠错和实施方向边界，未宣称具体生产代码已变更或测试通过。
