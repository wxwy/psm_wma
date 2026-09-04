# PSM-WMA R09-B TTT v0.3.2 C5A chronology-owner / segment / backward 设计 v0.4

**日期**：2026-09-04  
**状态**：design-only；实现前必须三方同 SHA 审核  
**上游权威**：`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md` 与 R08 causal evidence contract  
**替代**：v0.3；本文件响应 ChatGPT v0.3 review 的 HIGH-1、MEDIUM-2、MEDIUM-3

## 1. 目的与边界

C5A 为 C5 单步 primitive 增加唯一 chronology owner、受信 evidence admission、exactly-once replay、segment materialization 与 backward 原子提交。本 Gate 仅授权 owner/segment synthetic CPU 实现和相邻测试；不授权 Cosmos forward/packer/attention、配置/优化器/checkpoint/trainer/inference、GPU、真实 I/O、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。

## 2. 受信 admission 与唯一 chronology

R08 completed-causal-evidence materializer 是唯一受信 producer，发放不可变 `AdmissionCapability`。capability 只认证 `owner_key`、`source_timestep`、source identity、immutable source payload handle、source/evidence digest 和 `provenance_class=R08_COMPLETED_CAUSAL`；不再携带 `owner_epoch`、`episode_step`、`segment_id` 或 `segment_offset`。裸 dict、caller booleans、复制字段、history/future/GT 输入、伪造 digest 均拒绝。

C5A owner registry 是 chronology 的唯一权威：它在 admission 后分配并绑定 `owner_epoch/episode_step/segment_id/segment_offset`，并向 materializer 返回该绑定；R08 不独立分配 chronology。capability 的 digest 使用固定 little-endian length-prefix 对 owner/source identity、source timestep、dtype/shape 与 immutable source bytes 做 SHA-256。若只能提供 stable source handle，则 handle 指向不可变字节快照；参数相关的 encoded `E_t` 不作为 admission digest。

## 3. 两阶段事务与证据 rematerialization

每个 owner 只有已提交记录 `C` 与至多一个 pending transaction `P`：

```text
C = {owner_key, epoch, committed_state, last_step,
     committed_segment_cursor, committed_replay_ledger}
P = {base_snapshot=C, pending_state, pending_cursor,
     pending_identity_digest_ledger, pending_replay_cache,
     raw_source_entries, materialized_entries, phase}
```

`COLLECT_RAW` 只保存受信 immutable source payload/handle、capability、owner identity 和 digest，不保存 graph-bearing `E_t` 作为训练值；不创建 autograd graph，也不向 trainer 暴露 loss。`MATERIALIZE_PENDING` 在 segment atomic unit 内从冻结 source 重新调用 trainable `LocalEvidenceEncoder + readout`（在当前参数快照下），再执行 C5 inner K/V update/readout 和 outer task path。实现必须冻结 admission→materialization 的 evidence-encoder 参数版本，或证明 immutable source digest 不依赖参数；不得因重算而改变 admission 身份。

slow evidence encoder 与 Q/K/V/slot/W0 的 outer 梯度必须在 materialization→ordinary outer `backward()` 路径有限、非零、有限可达；C5 inner update 保持 `create_graph=True`，outer backward 使用 `create_graph=False`。segment commit/abort 后不得保留 graph-bearing source、pending output 或跨 segment引用。

phase 严格为 `COLLECT_RAW → MATERIALIZE_PENDING → BACKWARD_OK → COMMIT` 或 `ABORTED`。pending 同 identity+digest 只 replay 且零额外 C5 write；已提交 replay 只返回 committed graph-free cache。backward 成功后一次性提升 state/cursor/ledger/cache 并销毁 P；失败、异常、重复 backward/commit、abort 均完整丢弃 P，C 不变。

## 4. replay cache 与 segment/terminal 规则

`C.committed_replay_ledger` 的每项是显式 graph-free 数值记录：`owner/epoch/segment/offset + digest + detached cloned result + shape/presence metadata`。pending cache 仅在 commit 时逐项 detach/clone 后原子提升；提交后 replay 必须 value-equal、`grad_fn is None`、不触发 C5 write，并在 P 销毁后仍可用。

`N=ttt_tbptt_steps>0`（默认16）。非 terminal 必须恰好 N 条；terminal `r=0` 无 backward 直接结束旧 epoch，`0<r<N` 以长度 r 单一 atomic unit ordinary backward 后 commit/detach，再递增 epoch，`r=N` 按完整段；terminal 失败仅 abort/retry 旧 epoch。非 terminal short、乱序、跳步、跨 owner/epoch、digest 冲突和旧 epoch 迟到均在 C5 前拒绝。

## 5. CPU implementation gate

仅在本文件获三方同 SHA `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU` 后，才允许新增 owner/segment synthetic CPU 实现及测试。测试必须覆盖 chronology 单一权威握手、source rematerialization 梯度（含 evidence encoder）、pending/committed replay 脱图与零写、事务回滚、N=1/3/16、terminal `r=0..N`、伪造 admission、batch permutation、owner/epoch mismatch、reset 顺序及 fast state 不在 `named_parameters()`。最低证据为定向 CPU pytest、py_compile、双仓 diff-check；仍禁止所有 runtime/生产接线和训练路径。
