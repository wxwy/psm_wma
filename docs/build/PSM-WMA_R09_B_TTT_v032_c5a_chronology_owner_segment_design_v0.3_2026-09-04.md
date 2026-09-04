# PSM-WMA R09-B TTT v0.3.2 C5A chronology-owner / segment / backward 设计 v0.3

**日期**：2026-09-04  
**状态**：design-only；实现前必须三方同 SHA 审核  
**上游权威**：`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`  
**前置关闭 Gate**：C2、C3、C4、C5 单步 fast-state synthetic CPU contract  
**替代**：v0.2 仅作为历史草案；本文件对事务、provenance、terminal remainder 和梯度语义作完整冻结

## 1. 目的与边界

C5A 为 C5 单步变换增加独立的 chronology owner，冻结 transition admission、exactly-once replay、唯一 state ownership、segment materialization 与 backward 原子提交。本 Gate 不实现 Cosmos forward/packer/attention、optimizer/config/checkpoint、GPU、真实数据或训练。

C5 仍只是内部单步 primitive：它只接受 C5A 已批准的单个 `[B,256]` causal evidence，不声称能识别重复、乱序或 provenance。C5A 实现前必须重新获得本文件对应 root/child 的三方同 SHA 审核。

## 2. 受信 provenance admission

外部调用者不得自填 `evidence_complete`、`causal_visible` 或 digest。R08 completed-causal-evidence materializer 是唯一受信 producer，向 C5A 发放不可变 `AdmissionCapability`（CPU 合成测试使用同等不可伪造的 registry-owned object）；裸 dict、复制字段、history/future/GT 输入和伪造布尔值均拒绝。

capability 的每个逻辑 owner 行包含：

```text
owner_key, owner_epoch, episode_step,
segment_id, segment_offset, source_timestep,
evidence_shape=[256], evidence_dtype,
evidence_digest, provenance_class=R08_COMPLETED_CAUSAL
```

`source_timestep` 是显式字段，且必须由 producer capability 绑定。digest 采用 owner-local canonical serialization：按固定 little-endian length-prefix 编码上述 identity、source_timestep、dtype、shape 和该行 contiguous evidence bytes，再做 SHA-256；digest 是每个逻辑 owner 行一个值，不覆盖无关 batch 行。C5A 只验证 registry 签发的 capability、digest 与输入行逐字节匹配，并按 identity gather/scatter；batch row permutation 不改变 owner 结果，owner/envelope/state 错配在 C5 前拒绝。

## 3. 两阶段 owner state machine

每个 registry owner 只有一个已提交记录 `C`，以及至多一个待提交 segment transaction `P`：

```text
C = {owner_key, epoch, committed_state, last_step,
     committed_segment_cursor, committed_replay_ledger}
P = {base_snapshot=C, pending_state, pending_cursor,
     pending_identity_digest_ledger, pending_replay_cache,
     raw_entries, materialized_entries, phase}
```

`C` 是唯一对外可见的权威状态；C5 只能修改 `P.pending_state`。打开 segment 时 `P` 从精确 `C` 快照开始，`segment_id` 与 offset 从 committed cursor 确定性递增。segment 未提交时，新的 admission 对比 `P.pending_cursor`，而不是旧的 `C.last_step`。

phase 严格为 `COLLECT_RAW → MATERIALIZE_PENDING → BACKWARD_OK → COMMIT`，或 `ABORTED`：

1. `COLLECT_RAW` 只保存已验证 capability、per-owner evidence 和 identity，不创建 autograd graph；未满 segment 不向 trainer 暴露 loss。
2. `MATERIALIZE_PENDING` 在同一 segment 原子单元内依次调用 C5，更新仅存在于 `P`；同一 pending key+同 digest 命中 `P.pending_replay_cache`，零次额外 C5 write。已提交 key 命中 `C.committed_replay_ledger` 时只返回 committed 缓存结果；两种 replay 不得混淆。
3. segment 完整或受信 terminal remainder 后，trainer 在同一 atomic unit 对 outer task loss 调用普通 `backward()`（`create_graph=False`）。C5 inner update 内部仍按已批准 core 使用 `create_graph=True` 以保留 meta-gradient。
4. backward 成功进入 `BACKWARD_OK` 后，只允许一次 `COMMIT`：原子提升 pending terminal state/cursor/ledger 到 `C`，然后销毁 `P`。异常、失败 backward、重复 backward、重复 commit 或 abort 都销毁 `P`，且 `C` 数值、bytes、cursor、ledger 完全不变。

owner registry 独占创建/持有/销毁 state；裸 `state_in`、跨 owner substitution、batch row 位置作为 owner、绕过 capability/admission 的调用均 fail closed。

## 4. identity、重试、epoch 与 segment 规则

新 transition 必须满足 `episode_step == pending_or_committed_last_step + 1`，且 `(segment_id, segment_offset)` 连续。pending 中同 identity+同 digest 只 replay；同 identity 异 digest、回退/跳跃、owner/epoch 失配、旧 epoch 迟到重试均拒绝且不调用 C5。done/reset 不能清除有未提交 transaction 的旧 epoch：必须先 terminal commit 或 abort；成功 terminal commit 后才递增 epoch、清空旧 ledger，并以 W0/step=0/offset=0 创建新 epoch。

## 5. terminal remainder 的冻结状态机

令 `N=ttt_tbptt_steps>0`（默认 16）。

- 非 terminal segment 必须收集恰好 `N` 个 transition；不足 `N` 时强行 commit/backward 一律拒绝。
- 受信 terminal signal 允许 `0<r<N` 的 partial remainder 进入 `MATERIALIZE_PENDING`，以长度 `r` 的单一 atomic unit 做一次 ordinary outer backward；成功后提交该旧 epoch 的最终 state，按 C5 规则对 carry detach，随后才递增 epoch并清空旧 ledger。
- `r=N` 按完整 segment 规则提交并随后结束旧 epoch；`r=0` 不执行 backward，直接在无 pending transaction 时关闭旧 epoch并递增 epoch。terminal signal 到达前不得假定 remainder 可提交。
- terminal materialization/backward 失败只允许 abort/retry 同一旧 epoch；不创建新 epoch、不推进 committed cursor。terminal remainder 的 identity 固定为旧 epoch 的 `segment_id` 与 offsets `[0,r)`；新 epoch 第一段从 offset 0、全新 epoch 开始。

## 6. CPU implementation gate（仅设计授权）

只有本文件获三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU` 后，才允许新增 owner/segment synthetic CPU 实现和相邻测试。必须覆盖：

- capability 伪造/布尔篡改/digest、source timestep、history/future/GT 与 batch row mismatch 全部在 C5 前拒绝；per-owner digest 与 row permutation 等价；
- `N=3` 在 collect、materialize、backward 前后失败均不改变 committed state/cursor/ledger；pending retry 同 digest 零 write，冲突 digest 拒绝；
- backward/out-of-order/offset 跳跃/跨 owner/epoch substitution、重复 backward/commit、abort/异常隔离；
- `N=1`、完整 `N=3/16`、terminal `r=1..N-1`、`r=N`、`r=0`、非 terminal short reject 及 terminal failure/retry；
- ordinary outer backward 与 inner create-graph 梯度语义：完整 segment 对 Q/K/V/slot/W0 的梯度有限可达，commit/abort 后无跨 segment graph；
- owner registry 唯一 state ownership、reset 顺序、fast state 不在 `named_parameters()`。

最低证据为定向 CPU pytest、实现文件 `py_compile`、child/root `git diff --check`，并记录每个拒绝分支在 C5 kernel 前发生。该 Gate 不授权 C6/C7/C8/C9、真实 I/O、GPU、torchrun、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。
