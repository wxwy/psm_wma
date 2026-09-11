# PSM-WMA v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint CPU/static Implementation 设计 v0.2

**日期**：2026-09-11
**状态**：docs-only remediation；待同 SHA 三方审核。
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-CPU-STATIC-IMPLEMENTATION-DESIGN`

**supersedes**：v0.1 §3 中 `FeatureConfigIdentity` 的 key-count 表述，以及 v0.1 §4 第 1 项的相同计数歧义。v0.1 其余白名单、contract、witness、禁止范围与 verdict 继续 binding。

## 1. Exact FeatureConfigIdentity key set

implementation 必须使用 **exactly 15-key** versioned `FeatureConfigIdentity` mapping：`schema` 加下列 **14 个 non-schema fields**，无第 16 键、无隐含 key：

```text
schema,
local_memory_enabled,
local_memory_dim,
local_history_enabled,
local_history_backend,
local_history_evidence_dim,
local_history_state_enabled,
local_ttt_enabled,
enable_input_bias,
ttt_tbptt_steps,
ttt_inner_lr,
k_local,
local_evidence_feature_version,
local_fast_state_dtype,
local_runtime_resume_mode
```

这个 key set 与已批准 composite refreeze v0.2 §2 完全相同。任何缺失、未知、重复语义或第 16 键均为 pre-mutation reject；不得把 `schema` 另算为附加 field。所有 14 个 non-schema field 的 exact active-TTT value/type validation、`k_local=1` current compatibility、canonical JSON/SHA-256 discipline 与 BaseIdentity/optimizer/scheduler/progress contract 均按 v0.1+approved composite designs 不变。

## 2. Witness wording correction

v0.1 §4 第 1 项替换为：定向 test 必须覆盖这个 exact 15-key mapping（`schema` + 14 non-schema fields）的 valid canonical mapping，及每个 field 的 missing/unknown/type/value/bias/backend/dimension drift zero-live-mutation reject。test 不得期待、接受或生成第 16 个 identity key。

## 3. Verdict

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。批准仍只允许 v0.1+v0.2 复合的两个 child 文件 synthetic CPU/static implementation；不授权真实 I/O、DCP、CUDA/GPU、torchrun、native forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理或 LIBERO4IN1。
