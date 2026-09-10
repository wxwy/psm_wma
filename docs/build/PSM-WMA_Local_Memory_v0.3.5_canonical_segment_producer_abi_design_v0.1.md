# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer ABI 设计 v0.1

**日期**：2026-09-10
**状态**：docs-only remediation；须三方同 SHA 批准后才可审计或实现
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-ABI-DESIGN`

## 1. 缺口、authority 与范围

本文件修复已批准 P1/P2 间的唯一 ABI 缺口：`CanonicalProductionSegmentRequest` 只含 logical `[B_stream,T]` `SegmentBatch`，但 Cosmos `_pack_input_sequence()` 需要 stream-major 的 `SequencePlan`、`GenerationDataClean`、text indexes 和 input timesteps。不得把 opaque `SegmentBatch.consumer_payload` 直接传入 packer，也不得回落 `_get_training_inputs()`、旧 row-wise route、`TTTLifecycle`、active wiring 或 v0.5 sidecar 作为隐式转换器。

authority 为 addendum v0.3.5、canonical production integration P0 source audit v0.3、P1 ABI design v0.2/v0.3。旧 `production_integration_implementation_design_v0.5` 的 adapter/sidecar/trainer contract 不在本 Gate 的实现 authority 内；如后续复用，须独立明示并重新审核。

本文件仅授权下一阶段 docs-only source audit；不授权 child 代码、真实 data/cache/checkpoint I/O、CUDA/GPU、torchrun、训练、评测、推理、配置/optimizer/checkpoint 或 LIBERO4IN1。

## 2. 冻结 producer 输入与输出

producer 的输入必须区分 collate 已存在的 raw/native row 与 model-owned materialization；producer 不读 loader/cache，也不重建或前移 tokenization、clean generation payload、CP cache/broadcast 或 noise schedule：

```text
member: exact MicrobatchPlanMember
segment: exact SegmentBatch [B_stream,T]
raw_rows: tuple[CanonicalRawNativeRow | None, ...]  # logical [B,T] 同形，PAD=None
```

每个 non-PAD `CanonicalRawNativeRow` 只持有 collate 真正保留的 opaque raw/native fields（例如 raw data payload、已存在的 `sequence_plan` metadata、text source/ids 与可选 S0 Local-absent witness）及 `(slot_id, episode_id, source_digest, consumer_step)`。它不得声明持有 `GenerationDataClean`、model-generated `input_text_indexes` 或 diffusion timestep；identity 必与 `member` chronology 和 `SegmentBatch` 完全相等。

固定生命周期为：先按 member/segment stream-major gather valid raw rows；随后**一次**调用现有 model-side preparation chain，在模型内继续执行 `_load_and_tokenize_text_data()`、`build_sequence_plans_from_data_batch()`、`get_data_and_condition()` 与现有 CP handling；再由既有 model noise-level seam 生成 diffusion timesteps，最后调用 `_pack_input_sequence()`。producer 只冻结 gather identity/order/Local prefix，绝不改变这些模型侧语义或把 timestep 移到上游。

producer 输出不可变 `CanonicalNativeConsumerBatch`：

```text
sequence_plans: tuple[SequencePlan, ...]
raw_rows: tuple[CanonicalRawNativeRow, ...]
local_prefixes: tuple[Tensor | None, ...]
identities: tuple[(slot, episode, step), ...]
actual_n_valid: int
```

输出顺序唯一为 stream-major `flat(b,t)=b*T+t` 的 valid gather；只可由 `NativeConsumerBatch.from_segment(...)` 的 payload/prefix/identity 与同一 logical index 的 native row 共同导出。PAD 永不输出；S0 输出一个 native row 且 prefix 是 `None`。`actual_n_valid` 仅为输出 cardinality，必须等于 frozen `member.planned_n_valid`。

## 3. source audit 必答项

下一个 audit 必须对现有 child 给出 `file:line`：

1. `joint_dataloader` 实际保留哪些 raw fields与最小 immutable raw-row extraction seam；不得要求它产生 clean payload、tokenized indexes 或 timestep；
2. gathered rows 如何一次进入现有 model-side `_prepare_training_data()`/`_get_training_inputs()`，分别映射 `GenerationDataClean`、tokenized indexes、CP payload handling；若现有输入 shape 不可安全组装，明确最小新增 builder 的路径和白名单；
3. 既有 model noise-level seam 如何在 preparation 后生成 diffusion timesteps，并与 `_pack_input_sequence()`、`_compute_losses()` 的 consumer/auxiliary split 保持一次语义；
4. S0 absent prefix 与 PAD exclusion 从 producer 到 packer 的逐字段证明；
5. foreign/reconstructed/stale member、row identity/count mismatch 的 pre-forward zero-mutation rejection；
6. No-Local path 不构造 producer，保持原 input/loss/GA 语义。

任何一项要求读取真实 cache、变更 collate/packer/dataset 或无法保持 native loss scaling，audit 必须 `REQUEST_CHANGES` 并另起 design Gate。

## 4. 后续实现边界与验收

仅在该设计三方批准、随后 source audit 三方批准、再有新的 implementation design 后，才可实现 producer。实现 design 必冻结精确文件白名单、row dataclass 的 concrete field types、clean-row batching builder、model native-forward/loss split、trainer single-scaled-backward 与 GradScaler disposition。

CPU/static implementation 的最低验收：`B=2,T=3` 含 S0/non-S0/PAD 的 identity/order/count、opaque object identity、PAD 零 native row、S0 None prefix、foreign/count mismatch pre-forward zero mutation、No-Local parity。不得以 synthetic loss 或旧 row-wise witness 代替 native input ABI。

请求唯一 verdict：

```text
APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_ABI
```
