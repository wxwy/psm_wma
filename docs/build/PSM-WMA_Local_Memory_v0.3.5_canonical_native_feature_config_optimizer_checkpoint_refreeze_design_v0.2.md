# PSM-WMA v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze 设计 v0.2

**日期**：2026-09-11
**状态**：docs-only remediation；须本文件 formal root/child 三方同 SHA 批准后才可进入下一份 CPU/static implementation design。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`

**supersedes**：v0.1 的 §2 与 §4--§5；v0.1 的范围、唯一 slow owner、inventory、fresh/quiescent admission 与禁止范围继续有效。若冲突，以本文件为准。

## 1. 前置与边界

前置 closure 为 `420fc259d938d12f41c7f42d7b6aaec8076eb0f3` / `f49f568923555fe15efe546925cbe6cc9140170e` 的三方 `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC`。本 Gate 位于 canonical CPU/static runtime 后、single-GPU smoke design 前；不得跳过 refreeze，也不得前置 sidecar、matched smoke 或正式训练。

本轮只冻结 versioned identity 与 **in-memory** slow-only restore 合同。禁止 child 修改、真实 data/cache/checkpoint I/O、DCP、CUDA/GPU、torchrun、native forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理、LIBERO4IN1。

除显式标注为动态 progress 的字段外，所有 identity mapping 都必须以 UTF-8、递归 key 排序、无 NaN/Infinity 的 canonical JSON 序列化并 SHA-256；saved mapping、expected mapping、其 digest 和 schema key set 必须全部 exact match。缺失、未知、重复语义、类型漂移或 digest 漂移均在首个 live mutation 前 reject。

## 2. FeatureConfigIdentity：构造 ABI 必须完整冻结

payload 的 `config_identity` 是 versioned exact mapping，版本为 `canonical_native_local_ttt_config_v2`，仅允许下列键：

```text
schema,
local_memory_enabled, local_memory_dim,
local_history_enabled, local_history_backend,
local_history_evidence_dim, local_history_state_enabled,
local_ttt_enabled, enable_input_bias,
ttt_tbptt_steps, ttt_inner_lr, k_local,
local_evidence_feature_version, local_fast_state_dtype,
local_runtime_resume_mode
```

active-TTT 首轮的 resolved value 必须同时满足：`local_memory_enabled=true`、`local_memory_dim=32`、`local_history_enabled=true`、`local_history_backend="ttt_fast_weight"`、`local_ttt_enabled=true`、`local_history_evidence_dim` 为正整数、`local_history_state_enabled=false`、`enable_input_bias` 为严格 bool；`ttt_tbptt_steps` 是 positive non-bool int（默认 16）、`ttt_inner_lr` 是 finite positive non-bool scalar（默认 0.1）、`k_local` 是 positive non-bool int，且 feature/dtype/resume 分别为 `causal_visual96_executed_action10_v1`、`fp32`、`slow_only_no_mid_episode_resume`。

`enable_input_bias` 必须作为 projector ABI identity，而非依赖迟到的 tensor shape 判断：它决定 `local_memory2llm` 是否有 bias。`local_memory_dim=32` 与每 token `32 -> 2048` projector ABI 共同冻结；`K_local` 记录实际 resolved slot 数，绝不将 slot 数折叠进 hidden dimension。当前 child 的兼容核若只接受 `k_local=1`，则 identity 必须如实记录 `1`；任何放宽为 multi-slot 的实现须经新的 ABI/implementation Gate，不得以 restore migration 隐式放宽。

未知、遗漏、legacy、bool 伪装、非 canonical value，或 expected active config 任一 drift 都 fail closed；不得依赖后来 inventory/tensor 不匹配、也不得 warm-start/migrate。

## 3. BaseIdentity：不可由调用者猜测

`base_identity` 是 versioned exact mapping，版本为 `canonical_native_local_ttt_base_v1`，仅允许：

```text
schema, child_git_revision, canonical_model_config_sha256,
checkpoint_source_fingerprint, manifest_sha256, source_sha256
```

- `child_git_revision` 由当前 checked-out child 的 full reachable Git SHA 取得；不得由 payload 调用者任意填充。
- `canonical_model_config_sha256` 是完整 resolved `FeatureConfigIdentity` canonical JSON 的 SHA-256。
- `checkpoint_source_fingerprint` 是版本化、不可为空的 canonical source descriptor digest；其 descriptor 至少含 source kind、immutable source identifier 与 source-manifest digest，禁止路径、时间戳或调用者临时标签代替。
- `manifest_sha256` 与 `source_sha256` 分别是 canonical manifest 与已审计 source-input descriptor 的 SHA-256；本 Gate 声称 manifest/source lineage 时二者不可未知、空值或省略。

base identity 由 checkpoint/manifest owner 在 staging 前从已冻结 inputs 派生，并与 payload 内 mapping exact 比较；restore API 不得提供 generic default（例如仅 `{"schema": ...}`），也不得接受 caller-chosen non-empty mapping 作为 canonical identity。没有真实 I/O 的 CPU/static fixture 可以使用 synthetic、内容可复算的 descriptor/digest，但不得伪称其为生产 asset identity。

## 4. Optimizer / scheduler / iteration identity 与 staged 原子性

`optimizer_identity` 与 `scheduler_identity` 均为 payload 的必需 versioned mappings；任一训练对象存在时不可为 `None`，不存在时二者必须都是 explicit `null`。

`optimizer_identity` 必须 exact freeze：

1. optimizer fully-qualified class name；
2. ordered param-group names，且每组的 ordered canonical slow member names 与 registered object identity 一一对应；
3. 每组完整 typed hyperparameter mapping（除 `params` 外的所有键和值），并禁止未知/缺失/重排；
4. 每个 member 的 allowed optimizer-state key set；每个 state value 的 scalar 或 tensor 语义，tensor 相对 member 的 exact shape、dtype 与 device class，及 scalar 的 exact type；
5. optimizer progress identity（每 member 的 `step`，及其与 global `iteration` 的一致性规则）。

`scheduler_identity` 必须 exact freeze：scheduler fully-qualified class name、immutable construction/config mapping、allowed state-key set 与每个 state value 的 scalar/tensor schema、dynamic progress fields、以及它们同 optimizer progress 和 payload `iteration` 的 exact relation。实现 design 必须把该 relation 写成可执行的单一 predicate；不得以“loadable”或“字段存在”代替一致性。若 scheduler 不存在，禁止携带 scheduler state；若存在，class/config/state/progress 中任一 drift 都 reject。

唯一顺序为：

```text
decode/clone in-memory payload
  -> validate FeatureConfigIdentity + BaseIdentity
  -> validate exact slow inventory/tensors
  -> construct detached shadow optimizer/scheduler and validate all identities/state/progress
  -> validate fresh/quiescent runtime admission
  -> copy existing registered tensors once, then load already-validated live optimizer/scheduler state
```

所有 fallible checks（包括 shadow load 后的 class/group/hyperparameter/state/progress relation）必须在第一个 live tensor、optimizer group/state、scheduler state 或 iteration mutation前完成。reject 后 registered tensor bytes、optimizer groups/state、scheduler state、iteration、Parameter/module/adapter identity、frontier/pending authority 必须 byte/object-for-object 不变；禁止 post-mutation rollback、创建/替换 module 或 Parameter。

## 5. 继承的 owner、inventory 与 runtime admission

唯一 registered owner 仍为 `net.local_memory_runtime.evidence_encoder` 与 `net.local_memory_runtime.ttt_core`，canonical adapter 必须 `is`-bound；exact inventory、四个 slow `w0_fast_*` seed、K/Q/V、slot queries、projector、modality embed 与 runtime-fast-state exclusion 按 v0.1 §3 不变。

restore 仅允许 fresh/quiescent runtime：任何 committed frontier `W_fast`、pending scan/native-forward/commit/retry/suffix capability、open transaction/recovery receipt 或 nonterminal pre-restore authority 都 pre-mutation reject。成功后 adapter/frontier 为空且仍 exact bound；只允许随后 fresh episode clone restored `W_bar_0`，不支持 mid-episode resume。

## 6. 下一 CPU/static design 的直接验收 witness

下一 implementation design 必须冻结并实现小型 in-memory witnesses：

1. 每个 FeatureConfigIdentity activation/backend/dimension/bias/TTT field 的 missing、unknown、type/value drift 都在 zero live mutation 前 reject；
2. `base_identity` 的 schema、child revision、model-config digest、source fingerprint、manifest/source digest 各自 drift/missing 都 reject，generic caller mapping 不能通过；
3. optimizer class、ordered group/member、任何 hyperparameter、state-key/schema/shape/dtype/device、per-member step 与 iteration drift 各自 zero-mutation reject；
4. scheduler class/config/state/progress 或 scheduler--optimizer--iteration relation drift 各自 zero-mutation reject；
5. valid exact staged round trip 后，registered objects不替换、slow bytes/optimizer/scheduler/iteration 一次性更新；
6. 每类 live runtime authority 的 quiescent rejection，以及 fresh success 的 empty frontier/exact adapter binding；
7. payload runtime/sidecar key reject，且 `ContinualTTTFastState`/frontier 无 registered alias。

所有 fixture 必须是内存 module/tensor/optimizer/scheduler；不是 public training/checkpoint backend，仍不执行真实 I/O、forward/backward 或 step。

## 7. Verdict

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许创建并审核下一份 CPU/static implementation design，不授权 child 实现或任何真实执行。
