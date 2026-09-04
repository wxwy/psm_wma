# PSM-WMA R09-B TTT v0.3.2 C5A chronology-owner / segment / backward 设计 v0.6

**日期**：2026-09-04  
**状态**：design-only；实现前必须三方同 SHA 审核  
**替代**：v0.5；恢复 v0.4 已冻结的 admission、permutation 与 digest 约束

## 1. 正式路径与边界

R09-B C5A 路径固定为 `immutable completed-causal source → LocalEvidenceEncoder → E_t[B,256] → C5 K/V update + Q read_many → [B,K_local,32]`。R08 `StatelessLocalReplayReadout` 仅作独立 control baseline，在 C5A/TTT materialization 调用次数必须为零；不作为 C5 输入或第二 readout。仅授权 owner/segment synthetic CPU 实现与测试，禁止生产/runtime、Cosmos 接线、GPU、真实 I/O、训练、评测、推理、P4/P5、B2-T、LIBERO4IN1。

## 2. Admission、digest 与拒绝语义

R08 capability 仅认证 owner/source identity、source_timestep、immutable source payload/handle、`provenance_class=R08_COMPLETED_CAUSAL`。C5A registry 是唯一 chronology authority。canonical source key 为 `S=(owner_key, source_identity, source_timestep, source_digest)`，S 必须在 chronology 分配/C5 调用前查询 pending ledger 与 committed reverse index；命中同 S 返回 replay，冲突 digest 拒绝，未见 S 才分配 chronology。

digest 必须使用固定 little-endian length-prefix 序列化 owner/source identity、source_timestep、dtype、shape 与 contiguous immutable source bytes 后 SHA-256；参数相关 encoded E 不参与 digest。C5A 验证 capability 与 source handle 字节/输入行逐字节绑定及 digest 等值。

裸 dict、caller booleans、复制/篡改 capability 字段、伪造 digest、history/future/GT 输入、owner/envelope/state 错配、跨 owner/epoch、乱序/跳步均在 C5 前拒绝。按 owner identity gather/scatter，batch row permutation 必须结果等价；row mismatch 必须拒绝。

## 3. 事务、重算与 replay

`COLLECT_RAW` 只保存 immutable source/capability/S，不保存 graph-bearing E；`MATERIALIZE_PENDING` 在 atomic segment 中重算 Encoder→E_t[B,256]，再执行 C5。outer 使用普通 `backward()`，inner 使用 `create_graph=True`；evidence encoder 与 C5 slow/Q/K/V/slot/W0 梯度有限非零可达。pending/committed replay 均零额外 C5 write；committed 项为 detached/cloned value/shape/presence 数值记录，`grad_fn is None`，P 销毁后仍可用。失败/abort/重复提交保持 C 不变且无跨 segment graph。

## 4. Segment、terminal 与验收

`N>0` 默认16；非 terminal 恰好 N，terminal `r=0` 无 backward、`0<r<N` 单一 atomic backward 后 commit/detach、`r=N` 完整提交；失败仅旧 epoch retry。CPU 测试必须显式覆盖：stateless spy=0 与 C5 输入 `[B,256]`；所有 hostile admission 拒绝；digest canonical/逐字节绑定；batch permutation 等价与 row mismatch 拒绝；S lookup-before-allocation（含 chronology advance 后 committed replay 零写）；pending/committed no-graph replay；事务回滚；N=1/3/16、terminal r=0..N、reset 与 fast state 不在 `named_parameters()`。实现前须获得 literal `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU`。
