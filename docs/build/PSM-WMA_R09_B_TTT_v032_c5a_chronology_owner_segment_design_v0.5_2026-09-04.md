# PSM-WMA R09-B TTT v0.3.2 C5A chronology-owner / segment / backward 设计 v0.5

**日期**：2026-09-04  
**状态**：design-only；实现前必须三方同 SHA 审核  
**替代**：v0.4；响应 ChatGPT/Kimi v0.4 的 HIGH-A/HIGH-B

## 1. 边界与正式 C5A 路径

C5A 仅授权 owner/segment synthetic CPU 实现及测试；不授权生产接线、Cosmos forward/packer/attention、配置/优化器/checkpoint/trainer/inference、GPU、真实 I/O、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。

正式 R09-B 路径固定为：

```text
immutable completed-causal source
  -> R08 LocalEvidenceEncoder
  -> E_t [B,256]
  -> C5 project K/V + fast-state update + Q read_many
  -> local tokens [B,K_local,32]
```

R08 `StatelessLocalReplayReadout` 是独立 control baseline，在 C5A/TTT materialization 中调用次数必须为零；它不得作为 C5 输入或在 TTT 前增加第二个 readout。`E_t` rematerialize 在 segment atomic unit 内启用 grad，使 evidence encoder 与 C5 slow/Q/K/V/slot/W0 均可由 outer ordinary `backward()` 获得有限非零梯度；inner update 仍 `create_graph=True`。

## 2. admission、唯一 chronology 与 source-key 预查

R08 capability 仅认证 `owner_key`、source identity、`source_timestep`、immutable source payload/handle、source digest 与 `R08_COMPLETED_CAUSAL` provenance；C5A owner registry 是唯一 chronology 权威，负责绑定 epoch/episode_step/segment_id/offset。

定义 canonical source key：`S=(owner_key, source_identity, source_timestep, source_digest)`。每次 admission 必须严格按以下顺序执行：

1. 在任何 chronology 分配或 C5 调用前，以 S 查询 pending source ledger 与 committed reverse source index；
2. pending/committed 命中同 S 时返回已绑定的 replay 数值（pending 可带图但不得再次写，committed 必须 detached/cloned、`grad_fn is None`），不分配新 step/segment/offset；同 source identity+timestep 的异 digest 直接拒绝；
3. 仅完全未见过的 S 才由 C5A registry 分配下一 chronology binding，并进入 C5。

提交记录必须保留 `S -> chronology/cache` reverse index，即使 P 销毁后仍能查到；每项 committed cache 含 detached cloned result、digest、shape/presence metadata，value-equal 且零 C5 write。

## 3. 事务、回滚与 terminal

每个 owner 只有 committed `C` 与至多一个 pending `P`。`COLLECT_RAW` 只保存 immutable source/capability/S，不保存 graph-bearing E；`MATERIALIZE_PENDING` 重算 Encoder→E_t→C5；`BACKWARD_OK` 后一次性 promote state/cursor/ledger/replay+reverse-index 并销毁 P。失败、abort、重复 commit/backward 均丢弃 P 且 C 不变；commit/abort 后无跨 segment graph。

`N>0`（默认16）：非 terminal 必须 N 条；terminal `r=0` 直接结束旧 epoch，`0<r<N` 作为单一 atomic outer backward 后 commit/detach，`r=N` 按完整段；失败仅旧 epoch retry，非 terminal short/乱序/跳步/owner 或 epoch mismatch 在 C5 前拒绝。

## 4. CPU gate 验收

实现前必须获得 literal `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU`。测试覆盖：stateless readout spy=0、C5 输入 `[B,256]`、evidence encoder/C5 slow 梯度、S lookup-before-allocation（含 committed replay after chronology advances、异 digest conflict）、pending/committed no-write/no-graph replay、事务回滚、N=1/3/16 与 terminal r=0..N、owner/epoch mismatch、reset 顺序和 fast state 不在 `named_parameters()`。最低证据为定向 CPU pytest、py_compile、双仓 diff-check；其他执行范围仍全部禁止。
