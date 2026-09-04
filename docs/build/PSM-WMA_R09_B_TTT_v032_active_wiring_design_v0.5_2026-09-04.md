# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.5

**状态**：v0.4 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.4（root `fba72be`）获 ChatGPT `388dd41`、Kimi、MM 三方 REQUEST_CHANGES，收敛于：lag 积压跨 segment/terminal 时 meta-gradient 的保全、SCALER_SKIP 的 chronology 连续性、terminal-during-lag 状态机。v0.4 已获接受部分逐条继承：raw 顺延队列方向、真实三态 optimizer 事务接缝、skip 抑制 scheduler、exception=process-fatal、pre-write witness、梯度 supersede 声明、disabled parity、config/owner/selector/checkpoint 边界。

## 1. 统一顺延/重试状态机：惰性 segment 成形（三方 HIGH/MEDIUM 合并整改）

核心冻结：**segment 只在 live transaction 内成形；顺延队列中的行永远不构成 segment、不关闭、不 materialize**。由此 v0.4 的两个 HIGH 在结构上消失。

- **顺延队列**（wiring 层、graph-free、per-owner FIFO）：元素为 `(raw evidence, source_timestep, terminal_hint)`。进入条件：无可用 open transaction 吸收该行——即前一 segment 已 BACKWARD_OK 未 publish，或上次事务被 skip-abort 待重试。
- **队列中行的 read**：该行的 window 使用最后 committed state 产生 prefix（v0.3/v0.4 已冻结的 lag 语义）；不建图、不推进 candidate。显式冻结：这些 window 不向 Local 慢参数提供梯度，其数值 read 滞后于自己的 timestep——这是 publication lag 的既定事务语义，非 stale-read 缺陷。
- **flush 时机**：`resolve_transaction` 之后的**下一个 micro-batch 的 forward 接缝**（on_before_forward）：先按队列顺序 `begin()`（`pending.base_state` = 当时最后 committed state）+ 逐行 `admit()`，再处理本 window 自身的行。自此该 segment 处于 open transaction，中间行 read transaction-local detached candidate（v0.2 §1 不变）。
- **segment 关闭只发生在 live window**：队列行被 admit 后按 admission 顺序每满 `ttt_tbptt_steps` 关闭一个 segment；closing 总是落在某个 live micro-batch（该 window 的 materialize 建 witness 图、其 task loss 提供该 segment 唯一一次 meta-gradient，结构与非 lag 路径完全一致）。因此**任意 `ttt_tbptt_steps`×`grad_accum_iter` 对齐（含 lag ≥ segment_steps）都不丢失 meta-gradient**——被推迟的行只是稍后成形，其 segment 的 closing 仍在 live window 发生。
- **terminal-during-lag（Kimi MEDIUM-1 / MM 条款）**：episode 最后一行携带 `terminal_hint=True` 入队。含该行的 segment 在 flush 后成形，materialize 时按 terminal remainder 关闭；`finish(terminal=True)` 的 commit 同样走两阶段门（optimizer step 成功才 publish）；**reset 延迟到该 terminal segment publish 之后**执行（owner epoch+1）。旧 epoch 的队列行全部在 reset 前 admit 完毕（它们是 terminal segment 的行）；新 episode 的行在 reset 后才以新 epoch begin——顺延队列的 FIFO 序保证二者不交错。authority 的 stale-epoch 拒绝（`runtime_authority.py:117`）因此永不误触发。
- **验收（CPU/static）**：`segment=3 × grad_accum=2/4/5/7`（含 lag≥N）、`16×16`、terminal-during-lag 组合，断言：无 admission failure、无丢失行、owner-global timestep 连续、每个成形 segment 恰好一次 witness backward、terminal 短段 publish 后才 reset、epoch 归属正确、无 stale read（lag 语义豁免内）、无 double write。

## 2. SCALER_SKIP 重试：行保留 + 顺延重排（ChatGPT HIGH-2 整改，Option C 变体）

- SCALER_SKIP 时：不 publish（slow 侧被 scaler 跳过、scheduler 不推进）；未发布 candidate 作废（从未可见）；**失败 segment 的 raw 行由 wiring 层保留并整体放回顺延队列前端**（序保持），authority `abort()` 丢弃 pending 不产生空洞——下一 live window 的 flush 会把这些行重新 `begin/admit`，`source_timestep` 从最后 committed 值继续，连续性保持。
- 被跳过的 closing backward 的 meta-gradient 不重放旧图（图已随 backward 释放）；该 segment 在重试中于**新的 live closing window** 重新 materialize/关闭，meta-gradient 由该 window 的 task loss 提供——与正常路径"仅 closing window 提供 meta-gradient"的结构一致。fast/slow 原子性：skip 时两侧都无进展；重试成功时 witness 建图与 optimizer 成功 publish 同一事务。
- **验收**：真实接缝驱动 SCALER_SKIP spy：失败 segment 行不丢失、下一个被接受的 `source_timestep` 连续、失败事务对后续 window 不可见、后续行不插队（FIFO）、无 fast commit 无对应 slow step；重试 closing 的 slow-param 梯度与新鲜参考 scan 逐元素相等。

## 3. Trainer 接缝细化（Kimi 非阻塞备注转为冻结条款）

`scheduler.step()` 位于 `_optimizer_step()` 体内（`trainer/__init__.py:527`），外层包裹无法撤回已推进的 scheduler。冻结：允许的最小 trainer diff 为 `_optimizer_step` **体内**在 found-inf 判定之后、`scheduler.step()` 之前设闸——skip 时不调用 `scheduler.step()`，并在同一位置产生恰好一次 `resolve_transaction(SUCCESS/SCALER_SKIP/EXCEPTION)`。范围声明相应精确化为"`_optimizer_step` 体内的 skip 闸 + 结果回调"，`local_ttt_enabled=False` 时零行为变化（含 scheduler 行为逐位不变）。

## 4. 继承与范围

v0.3 §1（pre-write witness 语义与 T≥17/terminal 验收）、§3（Local 梯度目标 supersede 声明）、v0.2 §3（disabled parity 四判据）、v0.1 §2/§3/§5/§6 逐条继承不变。允许文件集合不变：`model_config.py`、`action_policy_libero_edge_all.py`、`omni_mot_model.py`、`local_evidence.py`、`production_runtime_adapter.py`、`runtime_authority.py`、`trainer/__init__.py`（仅 §3 闸与回调）+ 一个新 lifecycle callback 模块与相邻测试。本 v0.5 仍不授权实现、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.5 为准；其余条款继承 v0.4/v0.3/v0.2/v0.1 及其引用的 production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
