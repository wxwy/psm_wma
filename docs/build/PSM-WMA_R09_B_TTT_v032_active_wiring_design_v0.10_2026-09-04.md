# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.10

**状态**：v0.9 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.9（root `36ee7cf`）获 Kimi、MM 双方 `APPROVE_TO_IMPLEMENT` 与 ChatGPT `60ca10a` REQUEST_CHANGES（HIGH-1：external-backward 成功谓词未执行继承的非有限 loss abort 合同）。v0.9 其余部分全部获接受：arm/observe/mark external-backward 生命周期、authority 新增公开转移的合法性、单 backward 计数与异常 abort 路由位置、允许范围扩增。本 v0.10 仅补齐有限性谓词。

## 1. 有限 backward 谓词（ChatGPT HIGH-1 整改）

冻结：armed closing 事务在 `BACKWARD_OK` 之前必须通过**两个**独立证据，缺一 fail-closed：

1. **有限性证据**：`mark_external_backward(owner, *, loss: torch.Tensor)` 新增必传参数——该 micro-batch 的**未缩放 native loss** 张量（trainer `training_step` 返回值，缩放前；缩放因子为有限正数，检查未缩放值与检查缩放后值等价，显式选择前者）。authority 内执行 `torch.isfinite(loss.detach()).all()`（含标量/逐元素），非有限（NaN/±Inf）→ 拒绝并触发 abort，不置 `BACKWARD_OK`、不 commit。
2. **遍历证据**：`witness_leaf.grad is not None`（v0.9 已冻结）。

顺序：先有限性、后遍历证据，均失败即 abort。该谓词与后续 GradScaler `SCALER_SKIP` 明确区分：本谓词判定的是 closing backward 本身的合同有效性（Option B 语义下，有限且成功的 closing backward 即使随后被 skip 也已合法 commit）；skip 只影响 slow 侧步进。

**实现位置**：loss 值由 lifecycle callback 在 trainer backward 接缝取得（`on_before_backward(model, loss, iteration)` 已携带 loss；记录后于 `on_after_backward` 传入 mark）。trainer 改动仍为 v0.9 冻结的最小集合（backward 区 try/except + 既有 callback 接缝），无新增 trainer 路径。

## 2. 验收（CPU/static，驱动真实 trainer 顺序）

1. 有限 closing loss + 单次成功 backward → witness 遍历证据成立 → `BACKWARD_OK` → 恰好一次 commit；
2. NaN loss → abort、无 `BACKWARD_OK`、无 commit、committed 快照逐位不变；
3. +Inf/-Inf loss → 同样 fail-closed；
4. 有限 backward 后 GradScaler skip → fast commit 保持有效，Local 四组 `.grad` 清零、scheduler 不推进（Option B 既定语义）；
5. backward 抛异常 → abort 后原异常原样 re-raise；
6. `witness_leaf.grad is None` 但 loss 有限 → 拒绝且不 commit（两证据独立性）。

## 3. 继承与范围

v0.9 全部条款逐条继承（单阶段 commit、lag 派生机制移除、terminal/skip 语义、pre-write witness、disabled parity、config/owner/selector/checkpoint 边界、允许文件集合含 `runtime_authority.py` 的 `mark_external_backward` 与 `trainer/__init__.py` 最小接缝）。本 v0.10 仍不授权实现之外的任何真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.10 为准；其余条款继承 v0.9–v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
