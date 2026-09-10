# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer ABI 设计 v0.2

**日期**：2026-09-10
**状态**：docs-only remediation；须三方同 SHA 批准后才可审计或实现
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-ABI-DESIGN`
**Supersedes**：v0.1（仅本 Gate 的 producer/model materialization lifecycle；其余已冻结的范围、不变量和禁止项保持不变）

## 1. 缺口、authority 与范围

本文件关闭 v0.1 把「复用 native 非 Local materialization 语义」误表述为可直接调用 ordinary `_prepare_training_data()` / `_get_training_inputs()` 的歧义。现有 child 中 `_prepare_training_data()` 在 tokenization 与 `SequencePlan` construction 后无条件执行 `_inject_local_history()`；当 `local_ttt_enabled=True` 时，后者进入 legacy `_ttt_local_memory_tokens()`。canonical branch 因而不得直接调用、包装调用或经由 CP ordinary path 间接调用上述任一 flow，只要该 flow 会执行这两个 legacy Local side effect。

authority 为 addendum v0.3.5、canonical production integration P0 source audit v0.3、P1 ABI design v0.2/v0.3 和 v0.1 中未被本文件 supersede 的不变量。旧 `production_integration_implementation_design_v0.5` 的 adapter/sidecar/trainer contract 不在本 Gate 的实现 authority 内；如后续复用，须独立明示并重新审核。

本文件仅授权下一阶段 docs-only source audit；不授权 child 代码、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、训练、评测、推理、配置/optimizer/checkpoint 或 LIBERO4IN1。

## 2. 两阶段 ABI 与唯一 owner

canonical producer 只产生 pre-model 的 gathered raw bundle；它不产生、缓存或模拟 model materialization：

```text
CanonicalRawNativeRow
  raw/native collate truth fields
  optional collated sequence_plan metadata
  text source/ids
  optional S0 Local-absent witness
  identity = (slot_id, episode_id, source_digest, consumer_step)

CanonicalGatheredRawBatch
  raw_rows: tuple[CanonicalRawNativeRow, ...]
  local_prefixes: tuple[Tensor | None, ...]
  identities: tuple[(slot, episode, step), ...]
  actual_n_valid: int
```

输入仍是 exact `MicrobatchPlanMember`、exact logical `[B_stream,T]` `SegmentBatch` 与同形 raw rows（PAD=`None`）。non-PAD row 只可持有 collate 真正保留的 opaque raw/native fields；它不得声明持有 `GenerationDataClean`、model-generated `input_text_indexes`、model-built `SequencePlan` 或 diffusion timestep。若 collate 原本已有 `sequence_plan` metadata，它仅是 raw-row metadata，不构成 canonical producer 产出的 model plan。

输出顺序唯一为 stream-major `flat(b,t)=b*T+t` 的 valid gather。PAD 永不输出；S0 输出一个 raw row 且 prefix 是 `None`。`actual_n_valid` 必等于 frozen `member.planned_n_valid`。foreign/reconstructed/stale member、row identity 或 cardinality mismatch 均必须 pre-forward zero-mutation reject。

`CanonicalGatheredRawBatch` 之后必须由**尚待 source audit 精确定位并在后续 implementation design 冻结**的 canonical-safe model materialization seam 消费。该 seam 只复用 ordinary native 的非 Local 语义：tokenization、`GenerationDataClean` materialization、正常 `SequencePlan` construction、`get_data_and_condition()`、memory initialization 与 CP 语义；它绝不执行 `_inject_local_history()` 或 `_ttt_local_memory_tokens()`，也不创建第二个 Local token source 或第二次 TTT state transition。

该 model seam 的产物才可称为 `CanonicalModelPreparedBatch`：

```text
CanonicalModelPreparedBatch
  input_text_indexes: list[list[int]]
  sequence_plans: list[SequencePlan]        # model-built or model-validated
  gen_data_clean: GenerationDataClean
  memory_info / data_resolutions / vae_pixel_shapes
  local_prefixes: tuple[Tensor | None, ...] # identity-aligned gathered input
  identities / actual_n_valid
```

在 plan construction 与 `get_data_and_condition()` 的精确相对位置未经 audit 不得臆定。audit 必须证明 canonical `local_prefixes` 只在这个 safe seam 中一次映射为 native Local-prefix input / `SequencePlan.has_local_memory`，并保持 S0=`None`；不得借 ordinary injection 写入 `data_batch["local_memory"]`。

diffusion timestep 继续只能在 model-prepared batch 之后、现有 noise-level seam 生成；随后才允许 `_pack_input_sequence()` 与 native `_compute_losses()` 的 consumer/auxiliary split。producer 和 raw bundle 均不得生成或携带 timestep。

## 3. source audit 必答项

下一个 audit 必须对现有 child 给出 `file:line`，不得把下面问题留给实现者临时决定：

1. `joint_dataloader` 实际保留哪些 raw fields，以及最小 immutable raw-row extraction seam；不得要求 collate 产生 clean payload、tokenized indexes、model-built plan 或 timestep。
2. ordinary `_prepare_training_data()` / `_get_training_inputs()` 的哪一条精确调用边会触及 `_inject_local_history()` / `_ttt_local_memory_tokens()`；canonical path 如何明确避开该边，同时映射其非 Local native preparation semantics。若安全 seam 需要新 builder/factoring，给出最小文件路径、调用 owner、CP ownership 与拟议白名单。
3. canonical-safe seam 如何从 `CanonicalGatheredRawBatch` 产生 `CanonicalModelPreparedBatch`：`SequencePlan` 的 construction/validation、`local_prefixes` 一次映射、`GenerationDataClean`、text indexes、`get_data_and_condition()` 与 memory initialization 的精确顺序。若 collated metadata 不足，audit 必须 `REQUEST_CHANGES`，不得以 legacy injection 补齐。
4. model noise-level seam 如何在 preparation 后生成 diffusion timesteps，并与 `_pack_input_sequence()`、`_compute_losses()` 的 consumer/auxiliary split 保持一次语义。
5. S0 absent prefix、PAD exclusion、stream-major order、identity/cardinality 和 pre-forward zero-mutation 从 raw bundle 至 packer 的逐字段证明。
6. No-Local path 不构造 producer，保持原 input/loss/GA 语义。

任何一项要求读取真实 cache、变更 collate/packer/dataset、无法维持 CP/native loss scaling，或需要绕过以上 legacy exclusion，audit 必须 `REQUEST_CHANGES` 并另起 design Gate。

## 4. 后续实现边界与验收

仅在本设计三方批准、随后 source audit 三方批准、再有新的 implementation design 后，才可实现 producer 或 canonical-safe materialization seam。implementation design 必冻结精确文件白名单、raw-row concrete fields、safe-builder/factoring contract、Local-prefix write location、model native-forward/loss split、trainer single-scaled-backward 与 GradScaler disposition。

CPU/static implementation 的最低验收：`B=2,T=3` 含 S0/non-S0/PAD 的 identity/order/count、opaque object identity、PAD 零 raw/native row、S0 None prefix、foreign/count mismatch pre-forward zero mutation、single Local-prefix write、ordinary legacy injection zero-call 与 No-Local parity。不得以 synthetic loss 或旧 row-wise witness 代替 native input ABI。

请求唯一 verdict：

```text
APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_ABI
```
