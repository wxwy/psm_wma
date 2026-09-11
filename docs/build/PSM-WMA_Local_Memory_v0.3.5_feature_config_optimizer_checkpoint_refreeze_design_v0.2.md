# PSM-WMA Local Memory v0.3.5 Feature / Config / Optimizer / Checkpoint Refreeze Design v0.2

**日期**：2026-09-11

**状态**：docs-only remediation；待同 SHA 三方审核。

**supersedes**：v0.1 的 restore、runtime admission、semantic inventory sections；其余 config identity、逐 token `[B,K,32] -> [B,K,2048]`、禁止范围与验收口径继续有效。

## 1. Restore 必须是 preflight-first 原子事务

slow restore 的唯一允许顺序为：

```text
decode/stage in-memory payload
  -> validate every fallible contract
  -> validate fresh/quiescent runtime admission
  -> apply to existing registered objects exactly once
```

在第一处 live mutation 之前，preflight 必须已验证：versioned config serialization、base model identity、ordered/name-bound slow inventory key set、每个 tensor shape/dtype、optimizer parameter-object/group schema与 staged state、scheduler schema/state、global iteration/resume identity，以及 payload 不含任何 forbidden runtime key。preflight 不得创建/替换 Local module 或 Parameter object。

任何 reject 必须发生在第一处 registered slow tensor、projector/modality tensor、optimizer state/group、scheduler state、global iteration、registered object identity 或 runtime authority mutation之前；拒绝后上述所有对象和字节状态都与调用前相同。first CPU/static implementation 禁止选择 post-mutation rollback 语义。

## 2. slow-only restore admission

`slow_only_no_mid_episode_resume` 的唯一首轮 admission 是 **fresh/quiescent runtime**。在 preflight 之前或之中，restore 必须拒绝下列任一仍 live 的 authority：

- frontier 已持有 committed continuation `W_fast`；
- pending scan/native-forward/commit/retry/suffix capability；
- open canonical transaction、recovery receipt 或任何 pre-restore scheduler/runtime ownership；
- 任何由 pre-restore encoder/core 派生且尚未 terminal/committed 的 adapter state。

此拒绝同样必须 pre-mutation，slow 与 runtime 两侧均保持不变。首轮不允许 checkpoint code 隐式 clear/rebind/destroy live runtime authority。成功 restore 后 adapter/frontier 必须可证明为空，且继续 `is`-bound 到 exact registered encoder/core objects；随后仅 fresh episode 可以 clone restored `W_bar_0` seed。

## 3. v0.3.5 TTT semantic role 到 concrete ABI 的规范映射

以下是唯一可用于 selector/inventory/checkpoint 的现有 `ContinualTTTLocalMemoryCore` mapping：

| 语义角色 | registered concrete parameter keys |
| --- | --- |
| learned slow `W_bar_0` seed | `w0_fast_in_weight`, `w0_fast_in_bias`, `w0_fast_out_weight`, `w0_fast_out_bias` |
| `theta_K` | `key_proj.weight`, `key_proj.bias` |
| `theta_Q` | `query_proj.weight`, `query_proj.bias` |
| `theta_V` | `value_proj.weight`, `value_proj.bias` |
| slot query bank | `slot_queries` |

含 `fast` 的四个 `w0_fast_*` 是 **registered slow seed parameters**，必须进入 checkpoint/selector；它们不等同于 runtime `ContinualTTTFastState`。runtime fast state 只存在于 adapter frontier 的未注册 carrier，永不成为 named parameter、optimizer member 或 slow payload key。evidence encoder 的全部 named parameters、上述 core keys、per-token projector 与 modality embed 共同构成 exact slow inventory。

## 4. 强制 CPU/static witness 增补

除 v0.1 §6 外，下一 implementation design 必须冻结下列 direct tests：

1. 构造 tensor/config 合法但 late optimizer/scheduler/owner 不合法的 staged payload；restore reject 后逐 tensor、optimizer state/group、scheduler、iteration、object identity byte/object-for-object 不变。
2. 预先 seed committed frontier 与每种 pending authority；slow restore 必须 pre-mutation reject，slow/runtime snapshots均不变。
3. fresh/quiescent admission 成功后 frontier 为空、adapter仍引用 exact restored registered encoder/core。
4. 对 §3 每个 concrete key 证明 semantic slow role、selector/checkpoint membership；并证明 `ContinualTTTFastState`/frontier 无 registered alias。

## 5. 请求 verdict

请回复 `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC` 或 `REQUEST_CHANGES(file:line)`。批准仍仅授权下一份 CPU/static implementation design；不授权 child 实现、真实 I/O、GPU、optimizer step、sidecar、训练或 LIBERO4IN1。
