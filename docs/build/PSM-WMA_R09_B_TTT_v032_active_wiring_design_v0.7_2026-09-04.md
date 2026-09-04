# PSM-WMA R09-B TTT v0.3.2 active Cosmos/trainer wiring design v0.7

**状态**：v0.6 superseded；待三方同 SHA 设计审核。仅冻结 active wiring contract，不授权实现、GPU 或训练。
**基线**：v0.6（root `0612502`）获 ChatGPT `06f899c`、Kimi、MM 三方 REQUEST_CHANGES。ChatGPT HIGH-1 裁定 fast-state-only commit 在 active-wiring Gate 内重定义已冻结的 C5A/production authority 事务语法（`commit()` 要求 `BACKWARD_OK`），不可接受；本 v0.7 按其选项 ① 整改——所有 committed 非空 segment 仍经冻结的 witness-bound backward 达到 `BACKWARD_OK`，不新增任何 authority 提交路径。v0.6 已获接受部分逐条继承：cap/连续 run 双不变量、per-owner flush、skip 行保留队首、scheduler 体内闸、`.grad` 清零、三态接缝、exception=process-fatal、pre-write witness、disabled parity、config/owner/selector/checkpoint 边界。v0.6 的 fast-only commit 方向（含 Kimi/MM 的 fast-only queue 互斥条款）整体撤销。

## 1. Lag 不变量与 per-owner flush（继承 v0.6 §1，不变）

- fail-closed 校验：`grad_accum_iter ≤ ttt_tbptt_steps`（config composition）+ 同 owner window 连续 run（runtime）。
- 普通顺延积压 `q ≤ N-1`，队列行永不在队列中凑满 segment；flush 只在该 owner 的下一个 live window 的 forward 接缝发生（FIFO begin/admit，base=当时最后 committed state），含队列行的 segment 由 live 行填满——closing 总是 live window，q=N-1 时 flush window 即 closing 且 read 取自 witness 图。

## 2. Terminal-during-lag：remainder 丢弃 + reset（ChatGPT HIGH-1 整改之一）

- episode 最后一行携带 `terminal_hint` 入队。若其在 lag 中（前序 segment BACKWARD_OK 未 publish 或待重试）：该 episode 已结束，remainder 行永远不会有同 owner 的后续 live window 作为 witness 载体。冻结语义：**顺延队列中的 terminal remainder 行直接丢弃，不 admit、不 commit**；它们从未进入 authority（wiring 层队列状态），因此不触碰 C5A 事务语法；其 fast-state 贡献随 episode 结束失去意义（owner 随即 reset）。
- 顺序：`resolve_transaction(SUCCESS)` publish 前序 segment 后立即 `reset`（owner epoch+1）；若前序事务被 skip-abort，则先按 §3 规则处理重入行——若 episode 已结束（队列中含 terminal_hint），重入行同样无载体，一并丢弃后 reset。新 episode 的行在 reset 后以新 epoch begin。
- 验收：terminal-during-lag 下无 commit 调用、reset 顺序与 epoch 归属正确、authority 无 pending 残留、FIFO 中旧 epoch 行不泄漏到新 epoch。

## 3. SCALER_SKIP 重试：以下一个同 owner live window 为载体（ChatGPT HIGH-1 整改之二；Kimi/MM 互斥条款由本机制替代）

- 失败 segment 的 N 行保留并放回顺延队列前端（FIFO、timestep 连续、无空洞——v0.6 已获接受）。
- 重试关闭：该 owner 的下一个 live window 的 forward 接缝内，`begin()` + 按序 admit 这恰好 N 行 → segment 立即满 → 在**该 live window 的 forward 中 materialize 建 witness 图**；该 window 的 task loss 经其 witness read（read 在重试行全部 write 之后、自身行 write 之前，因果合法）向重试 segment 提供恰好一次 meta-gradient。该 window 自身的行随后 admit 进下一 segment（中间行，detached write）。
- 由此 C5A 语法完整保持：每个 committed 非空 segment 都经 witness-bound backward 达到 `BACKWARD_OK`，`commit()` 的 BACKWARD_OK 门不变，`runtime_authority.py` 零新增提交路径。重试 segment 的"closing window"显式重定义为**重放完成所在的 live window**——这是对"closing window 提供 meta-gradient"目标的精确新规则（ChatGPT HIGH-2 选项 C），不改变 live 关闭 segment 的既有语义。
- fast/slow 原子性：重试 segment 的 publish 仍走两阶段门（其 witness backward 成功 + 后续 `resolve_transaction(SUCCESS)`）；再次 skip 则再次重入队首，episode 内可重复；若 retry 期间 episode 结束（terminal_hint 入队），按 §2 丢弃 + reset。
- `.grad` 清零（MM MEDIUM-2）保留：`resolve_transaction(SCALER_SKIP)` 回调内清零四组 Local slow 参数 `.grad`，spy 断言 skip 后/下一 backward 前为 None。

## 4. 验收矩阵（CPU/static，真实接缝驱动）

- cap 校验：`accum > N` fail-closed（含 N=3×accum=7）；`16×16` 通过。连续 run 校验：非连续同 owner 注入 fail-closed。
- 精确 trace：`N=3 × accum=2/3`：FIFO timestep、segment 边界、witness 图的 task loss 来源、单 pending 合法、每 segment 恰好一次 meta-gradient、无跨 episode loss、无 double write、reset 顺序。
- terminal-during-lag：丢弃 + reset 语义（§2 全部断言）。
- skip 重试：行不丢失、FIFO 不插队、重试 segment 在 owner 下一 live window 以 witness 关闭、其 slow 梯度与该 window 的新鲜参考 scan 逐元素相等、`.grad` 清零 spy、两次连续 skip 的重排正确、skip+terminal 组合的丢弃/reset 语义。
- 反向断言：authority 不存在任何无 `BACKWARD_OK` 的 commit 路径（静态检查 + spy）。

## 5. 继承与范围

v0.3 §1（pre-write witness 与 T≥17/terminal 验收）、v0.2 §3（disabled parity 四判据）、v0.1 §2/§3/§5/§6 逐条继承；v0.3 §3 梯度 supersede 声明由本 v0.7 §2/§3 的精确规则替代。允许文件集合：v0.6 集合**移除** `runtime_authority.py` 的 commit 路径变更（零改动），其余不变——`model_config.py`、`action_policy_libero_edge_all.py`、`omni_mot_model.py`、`local_evidence.py`（pre-write witness 路径）、`production_runtime_adapter.py`、`trainer/__init__.py`（仅体内闸与回调）+ 一个新 lifecycle callback 模块与相邻测试。本 v0.7 仍不授权实现、真实 checkpoint I/O、GPU/CUDA/torchrun、训练/评测/推理、P4/P5、B2-T、LIBERO4IN1；推理接线仍属后续独立 Gate。

冲突时以本 v0.7 为准；其余条款继承 v0.6/v0.5/v0.4/v0.3/v0.2/v0.1 及其引用的 C5A design v0.6、production runtime contract design v0.3、config/optimizer/checkpoint design v0.2。
