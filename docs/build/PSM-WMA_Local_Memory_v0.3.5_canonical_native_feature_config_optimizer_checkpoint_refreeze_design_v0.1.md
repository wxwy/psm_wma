# PSM-WMA v0.3.5 Canonical Native Feature / Config / Optimizer / Checkpoint Refreeze 设计 v0.1

**日期**：2026-09-11  
**状态**：docs-only；须本文件 formal root/child 三方同 SHA 批准后才可进入下一份 CPU/static implementation design。  
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-NATIVE-FEATURE-CONFIG-OPTIMIZER-CHECKPOINT-REFREEZE-DESIGN`

## 1. 前置、范围与后续顺序

前置 closure 为 `420fc259d938d12f41c7f42d7b6aaec8076eb0f3` / `f49f568923555fe15efe546925cbe6cc9140170e` 的三方 `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_NATIVE_PRODUCTION_RUNTIME_CPU_STATIC`。本 Gate 位于 canonical CPU/static runtime 后、single-GPU smoke design 前；不得跳过本 refreeze，也不得前置 sidecar、matched smoke 或正式训练。

本轮仅冻结 config、registered slow owner、optimizer membership 和 **in-memory** slow-only restore 合同。禁止 child 修改、真实 data/cache/checkpoint I/O、DCP、CUDA/GPU、torchrun、native forward/loss/backward、optimizer/scheduler step、sidecar、训练、评测、推理、LIBERO4IN1。

## 2. 版本化 config identity

`LocalMemoryConfig` 与 `OmniMoTModelConfig` 的 exact identity 必须包含且仅包含：positive non-bool `ttt_tbptt_steps`（默认 16）、finite positive non-bool `ttt_inner_lr`（默认 0.1）、positive non-bool `k_local`、`local_evidence_feature_version=causal_visual96_executed_action10_v1`、`local_fast_state_dtype=fp32`、`local_runtime_resume_mode=slow_only_no_mid_episode_resume`。未知、遗漏、legacy field、bool 伪装、非 canonical feature/dtype/resume 或漂移值都 fail closed；不得作 migration/warm-start。

`K_local` 是配置项而非永久 1；inventory/projector 必须按 actual `K_local` token 语义维持逐 token `32 -> 2048`，不得把 slot 数折叠成 hidden dim 或借旧 recurrent runtime 默认值推导。

## 3. 唯一 slow owner、inventory 与 selectors

唯一 registered owner 为 `net.local_memory_runtime.evidence_encoder` 和 `net.local_memory_runtime.ttt_core`，且 canonical adapter 必须 `is`-bound 到这两个对象；旧 `local_history_runtime`、`recurrent_backend`、`StatelessLocalReplayReadout` 不能成为 active-TTT trainable owner、selector target 或 alias。

slow inventory 必须 exact-cover：evidence encoder 全部参数；`ttt_core` 的 `w0_fast_in_weight/bias`、`w0_fast_out_weight/bias`、K/Q/V projections、`slot_queries`；`local_memory2llm.*` 和 `local_memory_modality_embed`。四个 `w0_fast_*` 是 registered slow W-bar-0 seed，尽管名称含 fast；`ContinualTTTFastState`、frontier、pending scan/native/commit/retry/suffix、transaction/receipt、cursor/queue/RNG/grad 永不得成为 Parameter、optimizer member 或 payload key。

selectors 必须以 evidence/core/projector/modality 四个 exact prefixes 对该 inventory 无遗漏、无重叠地 cover；所有 member 必须 requires-grad、object identity 唯一，optimizer 只接受 exact同对象/同组 schema。

## 4. Preflight-first slow-only restore

payload 只允许 versioned in-memory mapping（config、base identity、ordered slow tensors、optimizer/scheduler schema+state、iteration/resume identity），不得含 runtime/sidecar key。唯一顺序：

```text
stage/decode clone -> validate config/base/inventory/tensor/optimizer/scheduler/iteration
-> validate fresh/quiescent runtime admission -> copy existing registered objects once
```

所有 fallible checks 必须在首个 live mutation 前完成；reject 后 slow tensors、optimizer state/groups、scheduler、iteration、registered object identity、adapter/frontier/pending authority byte/object-for-object 不变。严禁创建/替换 module 或 Parameter，严禁 post-mutation rollback。

admission 仅允许 fresh/quiescent runtime：committed frontier W_fast、pending capability、open transaction/recovery receipt 或 nonterminal pre-restore authority均 pre-mutation reject；不得 clear/rebind/destroy 来规避。成功后 adapter/frontier 为空且仍 `is`-bound；只允许之后 fresh episode clone restored W-bar-0，首轮不支持 mid-episode resume。

## 5. 下一 CPU/static design 的验收

必须冻结 direct witnesses：config serialization/invalid drift；registered owner/adaptor identity；exact selector/inventory及 fast-state absence；valid in-memory round trip；late optimizer/scheduler/owner defect的零 mutation；每类 live runtime authority 的 quiescent admission reject；fresh success 的 empty frontier/exact binding；runtime/sidecar key reject。所有 fixture 都是小型内存 module/tensor/optimizer/scheduler，非 public training/checkpoint backend。

## 6. Verdict

请求唯一 verdict：

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_NATIVE_FEATURE_CONFIG_OPTIMIZER_CHECKPOINT_REFREEZE
```

或 `REQUEST_CHANGES(file:line)`。批准只允许创建并审核下一份 CPU/static implementation design，不授权 child 实现或真实执行。
