# PSM-WMA R09-B TTT v0.3.2 C5A chronology-owner / segment / backward 设计 v0.2

**日期**：2026-09-04  
**状态**：design-only；实现前必须三方同 SHA 审核  
**上游权威**：`PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.2.md`  
**前置关闭 Gate**：C2、C3、C4、C5 单步 fast-state synthetic CPU contract

## 1. 目的与边界

C5A 为 C5 单步变换增加独立的 chronology owner。它只冻结并验证“哪个 owner 在哪个 episode/segment 的哪个 transition 允许推进一次 state，以及该 segment 何时作为一个完整 backward 原子单元提交”。本 Gate 不实现 Cosmos forward/packer/attention、optimizer/config/checkpoint、GPU、真实数据或训练。

C5 的 `ContinualTTTFastStateTransition` 保持原样：它只接受一个已经通过 C5A admission 的 `[B,256]` causal evidence，不声称能识别重复、乱序、future 或 GT provenance。

## 2. Owner 与 transition identity

生产入口不得让调用者直接传入可任意替换的 `state_in`。每个 active owner 持有唯一 runtime record：

```text
owner_key:        不可复用的 episode/rollout owner 标识
owner_epoch:      reset 后递增的 epoch
episode_step:     单调递增的 completed control-timestep 编号
segment_id:       当前 TBPTT segment 标识
segment_offset:   [0, N) 的 segment 内偏移
state:            C5 fast state（唯一可写副本）
```

一行的 admission key 为 `(owner_key, owner_epoch, episode_step)`；segment key 为 `(owner_key, owner_epoch, segment_id, segment_offset)`。owner_key 不得使用 batch row、HTTP request id 或时间戳代替。owner record 只能由 owner registry 创建、持有和销毁；任何 batch 重排、跨 owner state substitution 或直接构造 state 的调用都必须 fail closed。

## 3. Admission、重试与乱序

每个 transition 在进入 C5 前必须提供只读 admission envelope：

```text
owner_key, owner_epoch, episode_step,
segment_id, segment_offset,
evidence_digest, evidence_complete, causal_visible
```

其中 `evidence_digest` 是对已完成 `[B,256]` evidence 及其 source timestep 的稳定摘要；`evidence_complete=true` 且 `causal_visible=true` 是硬门。future evidence、未完成 observation、GT future action、history tensor、摘要不匹配均拒绝。

owner registry 按以下规则处理：

1. 新 key 必须恰为 `episode_step == last_step + 1`，且 segment offset 与 `segment_id` 一致；否则在调用 C5 前失败。
2. 已完成 key 的重试只有在 envelope 全部 identity 相同且 `evidence_digest` 相同才允许返回已缓存的数值结果；不得再次调用 C5 或写入 state。相同 identity 但 digest 不同直接拒绝。
3. `episode_step < last_step`、segment offset 回退/跳跃、owner_epoch 不匹配、跨 owner 使用 state 均拒绝且不改变 registry/state。
4. done/reset 创建新 `owner_epoch`，清空旧 segment ledger，并从 learned W0、step=0、offset=0 开始；旧 epoch 的迟到重试永久拒绝。

## 4. Segment materialization 与 backward 原子性

`ttt_tbptt_steps=N` 为正整数，默认 16。owner 必须先在纯内存 segment buffer 中按 offset 收集恰好 `N` 个 admitted transition（最后一个 segment 可按设计明确的 terminal remainder 规则结束），每个 entry 保存 identity、digest、输入、C5 输出 token 和 state carry。

在 segment 未完整 materialize 前，禁止向 trainer 暴露需要 `backward()` 的 loss；禁止跨两个 immediate microbatch 携带未 detach 的 graph。segment 完整后，trainer 在同一 atomic unit 内执行 outer loss 与一次 `backward(create_graph=True)`，成功后才提交 owner 的 state/ledger；失败、异常或重复 backward 必须丢弃临时 segment，不得部分推进 owner。N-th transition 的当前 token 仍先从更新后的 state 读取，再按 C5 规则对下一段 carry 做 row-selective detach。

## 5. 生产/推理接缝冻结

后续实现必须提供唯一 owner API（名称在实现 Gate 固定）：`admit_transition`、`append_segment`、`commit_segment`、`abort_segment`。C5 primitive 只作为内部一步调用。任何现有 `LocalHistoryRuntime` window replay、裸 `state_in` 注入或绕过 admission 的调用路径都必须 fail closed。inference 可复用相同 identity/owner 规则，但不在本 Gate 授权接入。

## 6. CPU 验收矩阵

仅在本设计获三方 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_C5A_CHRONOLOGY_OWNER_SEGMENT_CPU` 后，才允许新增 owner/segment 的合成 CPU 实现与测试，至少覆盖：

- 新 transition 严格单调推进；重复同 digest replay 不二次 write，digest 冲突拒绝；
- backward/out-of-order、segment offset 跳跃、跨 owner/epoch substitution、迟到旧 epoch 全部 fail-before-C5；
- evidence_complete/causal_visible/digest/source-timestep 缺失或失配拒绝；history/future/GT 输入拒绝；
- N=1、N=3、N=16 segment 完整 materialization；terminal remainder 规则及计数一致；
- segment 未完成不得 backward；commit 成功一次，abort/异常不推进 state；重复 backward/commit 拒绝；
- owner registry 的唯一 state ownership、batch row permutation、reset+invalid 隔离；
- C5 slow-parameter 梯度在完整 segment backward 中可达，跨 segment carry 按 N 截断；fast state 不进入 `named_parameters()`。

最低证据为定向 CPU pytest、实现文件 `py_compile`、child/root `git diff --check`，并记录每个拒绝分支在 C5 kernel 前发生。该 Gate 仍不授权 C6/C7/C8/C9、真实 I/O、GPU、torchrun、训练、评测、推理、P4/P5、B2-T 或 LIBERO4IN1。
