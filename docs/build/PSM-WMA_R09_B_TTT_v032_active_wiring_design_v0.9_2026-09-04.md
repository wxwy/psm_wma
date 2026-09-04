# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.9

**状态**：v0.8 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.8（root `778272d`）获 Kimi、MM 双方 `APPROVE_TO_IMPLEMENT` 与 ChatGPT `f5e830f` REQUEST_CHANGES（HIGH-1：无合法单次 backward 接缝使 authority 在 `on_after_backward` commit 前达到 `BACKWARD_OK`）。v0.8 其余部分全部获三方接受：单阶段 commit（Option B）、lag 派生机制移除、terminal remainder 在自身 live window 关闭、skip 语义、pre-write witness、disabled parity、config/owner/selector/checkpoint 边界。本 v0.9 仅补齐 ChatGPT 指定的 external-backward 生命周期接缝。

## 1. External-backward 生命周期（ChatGPT HIGH-1 整改，采用其选项 b）

冻结精确接缝（每 micro-batch 恰好一次 backward 不变；`BACKWARD_OK -> commit` 语法不变；无私有 phase 改写）：

- **arm（forward 内，closing window）**：segment 满 N / terminal remainder 触发 materialize 后，lifecycle callback 记录该 owner 为 "armed external-backward"（仅此标记，非 authority phase 变更）。
- **observe/mark（on_after_backward）**：trainer 已完成其唯一一次 `loss_scaled.backward()`。lifecycle callback 对每个 armed owner 调用 authority 新增的 `mark_external_backward(owner)`：校验 phase==`MATERIALIZED_PENDING` 且 `witness_leaf.grad is not None`（证明 trainer 的 backward 实际遍历了 witness 图）→ phase 置 `BACKWARD_OK`；任一校验失败 → raise（由 callback 转为 abort）。随后 `commit()`；terminal 时 commit 后 `reset`。
- **失败/abort 接缝**：trainer 的 `loss_scaled.backward()` 区域包一层最小 try/except——异常时先调用 lifecycle `abort_open_segments()`（candidate 精确回滚到最后 committed state、pending 清空、armed 标记清除）再原样 re-raise。`local_ttt_enabled=False` 时该 try/except 零行为变化。
- **非 closing window**：无 arm、无 mark、无 commit——authority 状态机不变。

## 2. 允许实现范围的相应扩增（ChatGPT 验收要求）

允许文件集合扩增/精确化：`runtime_authority.py` **重新纳入**（仅新增 `mark_external_backward` 公开转移与 `_loss_reaches`/witness-leaf grad 校验；`commit()` 的 BACKWARD_OK 门与其余语义零改动）；`trainer/__init__.py` 的范围从"仅 `_optimizer_step` 体内闸"扩为"体内 skip 闸 + `resolve_transaction` 回调 + `loss_scaled.backward()` 的 try/except abort 路由"，均为最小 diff 且 disabled 路径逐位不变。其余文件集合不变：`model_config.py`、`action_policy_libero_edge_all.py`、`omni_mot_model.py`、`local_evidence.py`（pre-write witness）、`production_runtime_adapter.py` + 一个新 lifecycle callback 模块与相邻测试。

## 3. 验收（CPU/static，驱动真实 trainer 顺序）

- 每 micro-batch 恰好一次 backward（spy 计数）；closing loss 实际到达 witness（`witness_leaf.grad is not None`）；phase 仅在成功 backward 后变为 `BACKWARD_OK`；`on_after_backward` commit 恰好一次；非 closing window 无 mark/commit。
- backward 抛错：无 commit、committed 快照逐位不变、candidate 回滚逐位相等、异常原样传播。
- terminal remainder 与同一路径（arm→mark→commit→reset）一致。
- `witness_leaf.grad is None`（未遍历）时 `mark_external_backward` 拒绝且 commit 不发生。
- 继承 v0.8 §3 其余验收（N=1/3/16/terminal 时序、无 lag 断言、skip 语义、`.grad` 清零、disabled parity 四判据、BACKWARD_OK 外无 commit 路径反向断言）。

## 4. 继承与范围

除 §1/§2 外，v0.8 全部条款逐条继承。本 v0.9 仍不授权实现之外的任何真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.9 为准；其余条款继承 v0.8–v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
