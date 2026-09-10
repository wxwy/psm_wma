# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Source Audit v0.1

**日期**：2026-09-10
**状态**：docs-only source audit；须三方同 SHA 批准后才可进入下一 implementation design
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-SOURCE-AUDIT`
**前置 authority**：producer ABI v0.2（`c57e77c/36bf3b2`）

## 1. 审计范围与结论

本审计只读 root 与 current child source，回答 producer ABI v0.2 §3 的六项。结论是：现有 source 已有 raw collate、canonical scan/gather、native packer-prefix 和 post-preparation noise/loss 的可复用事实；但**没有**可被 canonical branch 直接调用的 Local-neutral preparation helper。ordinary `_prepare_training_data()` 与 `_get_training_inputs()` 均必然触及 legacy Local injection，不能作为 safe seam。

下一步只能起一个新的 docs-only implementation design，冻结对 `omni_mot_model.py` 的最小 model-owned factoring/builder、canonical Local-prefix 的唯一写入位置和 CP ownership。不得在本审计后直接实现，亦不得改 dataloader、collate、packer、dataset、loss scaling 或 runtime scope。

## 2. v0.2 §3 source map

### 2.1 Raw-row extraction：collate 已有事实，producer 不应改 collate

- `cosmos_framework/data/generator/joint_dataloader.py:128-150` 的 `custom_collate_fn()` 明确把 `text_token_ids`、`video`、`action`、`sequence_plan`、`sound`、`local_memory` 等作为 list-collate keys。
- `:152-207` 只保留 sparse `sound` / `local_memory` 的 `None` placeholder，其他可选缺项不保留；因此 future raw-row builder 只能拷贝当前 row 实有 fields，不能要求 collate 合成 `GenerationDataClean`、text indexes、timestep 或缺失的 modality。
- packed dataloader 的单样本/累积形状由同文件 `:793-821` 固定：multi-item keys 是 `list[list[Tensor]]`，metadata（含 `sequence_plan`）为 flat `list[element]`，tensor-origin fields 为 `list[Tensor(1,...)]`。

结论：`CanonicalGatheredRawBatch.raw_rows` 可以是 opaque collate-truth row snapshot；其 `sequence_plan` 只能是可选 raw metadata，绝不是 producer-owned model plan。无需改 dataloader/collate。

### 2.2 Canonical prefix authority、order 与 count

- canonical activation 在 `cosmos_framework/model/generator/omni_mot_model.py:134-152` 先于 ordinary training preparation 解析 exact request；enabled canonical mode 与 legacy marker 冲突即拒绝。
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:112-145` 的 `CanonicalProductionAdapter.scan()` 使用已注册 encoder/core 的 `scan_segment_masked_encoded_many(..., create_graph=True)`，并唯一生成 `result.gathered`。
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:293-321` 的 `NativeConsumerBatch.from_segment()` 唯一调用 `SegmentBatch.gather_consumers()`；`:313-320` 对 identities 和 `member.planned_n_valid` 做精确 equality。

结论：future producer 不得由 raw rows 重建 prefix；`CanonicalGatheredRawBatch.local_prefixes`、identities 和 cardinality 只能携带这个 exact `result.gathered` 的同一对象/顺序事实。S0/PAD 的具体排除和 `None` prefix 已是 gather contract，future implementation 仅验证和传播。

### 2.3 Legacy edge 与 canonical-safe preparation seam

- ordinary `_prepare_training_data()` 在 `omni_mot_model.py:1008-1053` 依次调用 text extraction (`:1021`)、plan construction (`:1022-1026`)、**无条件** `_inject_local_history()` (`:1027`)、`get_data_and_condition()` (`:1029-1033`) 和 `memory_init_training()` (`:1034`)。
- `_inject_local_history()` 的 enabled TTT branch 在 `:1100-1112` 调用 `_ttt_local_memory_tokens()`，写入 `data_batch["local_memory"]` 并修改 `SequencePlan.has_local_memory`；`:1128-1150` 又懒建 legacy `TTTLifecycle`。
- ordinary `_get_training_inputs()` non-CP 在 `:1295-1299` 调用上述 routine；CP owner slot 同样在 `:1305-1316` 调用、缓存并 broadcast 其包含 legacy-produced Local fields 的 payload。故 canonical branch 不得通过任一 ordinary wrapper 复用它。

结论：safe seam 当前**不存在**，但 native non-Local statements可被 model-owned factoring 重用。唯一可接受的后续设计是把 `:1021-1026`、`:1029-1053` 的 non-Local preparation semantics 提取/组织成 canonical-safe builder；它必须显式绕过 `:1027`，且 canonical branch 不得调用 `_inject_local_history()` 或 `_ttt_local_memory_tokens()`。

### 2.4 Model-prepared batch、single Local-prefix write 与 packer

- plan construction/retrieval 的唯一 native helper 是 `data/generator/sequence_packing/sequence.py:1209-1264`：现有 `data_batch["sequence_plan"]` 则返回，缺失时按 raw vision/image batch size 构建 default plan。
- `_load_and_tokenize_text_data()` 从 existing `data_batch["text_token_ids"]` 生成 list-of-list indexes（`omni_mot_model.py:1948-1970`）；`get_data_and_condition()` 从 raw batch materialize `GenerationDataClean`（`:4157-4218` 起）。
- native packer 在 `data/generator/sequence_packing/packers.py:76-145` 要求 plans、text indexes、clean data 与 CPU timestep；`:244-255` 是唯一 Local-prefix assembly：当 `plan.has_local_memory` 为真时从 dense `gen_data_clean.x0_tokens_local_memory` 消费一个 prefix，否则写入 `None`。
- `sequence.py:163-171` 验证每个 prefix 是 `[K_local,D_local]` 或 `None`；`:920-924` 仅当存在 token 时形成 prefix object；`:1082-1086` 强制 prefix list 与 packed sample count 相等。

结论：future safe builder 必须在 model-built/validated plan 与 `get_data_and_condition()` 的 output 已同一 gathered order 时，恰一次设置 `SequencePlan.has_local_memory` 并构造 dense `x0_tokens_local_memory`（只含 non-`None` prefix）。不得写 ordinary `data_batch["local_memory"]`；S0 retains a plan row with `has_local_memory=False`，PAD no row。

### 2.5 CP owner 与 post-preparation noise/loss

- ordinary CP cache/broadcast uses `_pack_training_payload()` / `_unpack_training_payload()` (`omni_mot_model.py:1212-1265`) and `_get_training_inputs()` (`:1301-1327`); it serializes plans, clean data and memory info. Because its owner-preparation source is legacy-contaminated, it cannot be shared by canonical until a later design specifies a parallel canonical-safe CP payload/owner contract.
- the model's existing timestep owner is `training_step()` `:1448-1527`; pack occurs at `:1529-1536`; noising at `:1586-1597`; native loss begins `_compute_losses()` `:1778-1828`. These remain post-prepared model operations and must not move into producer.

结论：future implementation design must choose one explicit CP policy: fail closed when CP is enabled, or define a separate canonical-safe CP payload/broadcast branch in the approved whitelist. It cannot reuse ordinary CP payload. Timestep/noise/packer/loss ownership remains model-side and post-preparation.

### 2.6 No-Local parity

`_canonical_production_request_from_batch()` at `omni_mot_model.py:141-152` is already a strict split: only `local_ttt_enabled=False` without any Local marker returns `None`; `training_step()` `:1425-1439` then takes the untouched ordinary path. Future canonical builder must be reachable only after a non-`None` canonical request; No-Local must not construct producer or canonical-safe payload.

## 3. Required next design boundary

The next design must be limited to:

1. a model-owned canonical-safe preparation API in `omni_mot_model.py`, with an exact input schema from `CanonicalProductionScanResult.gathered` plus collate-truth raw rows;
2. a single Local-prefix adaptation from gathered authority into model-built plans / dense clean Local list, with S0/PAD and identity/count assertions;
3. explicit CP disposition (fail-closed first, or a separate canonical-safe payload/broadcast contract); and
4. native post-preparation reuse without changing timestep/noise/packer/loss/GA semantics.

It must not include child implementation, dataloader/collate/packer/dataset changes, runtime sidecar, optimizer/config/checkpoint changes, real I/O, CUDA/GPU, torchrun, training, evaluation, inference or LIBERO4IN1.

## 4. Audit verdict request

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_IMPLEMENTATION
```

or `REQUEST_CHANGES(file:line)`.
