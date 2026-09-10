# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Source Audit v0.2

**日期**：2026-09-10
**状态**：docs-only remediation；须三方同 SHA 批准后才可进入下一 implementation design
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-SOURCE-AUDIT`
**Supersedes**：v0.1（仅 raw-row extraction/carrier source map；其余 v0.1 source findings 保持有效）
**前置 authority**：producer ABI v0.2（`c57e77c/36bf3b2`）

## 1. 审计范围与 v0.1 整改

v0.1 正确证明 collate 可保留 raw/native fields，却错误地把 field availability 推论为已存在 `CanonicalGatheredRawBatch.raw_rows` carrier。本版本明确 current repository truth：**raw-row carrier 当前不存在**。本审计只定位未来 design 可引入 carrier 的最小 source boundary；不把 future mechanism 写成 current ABI，也不授权 child 实现。

除本节与 §2.2 的 carrier map 外，v0.1 对 canonical scan/gather、ordinary legacy injection、CP、packer、noise/loss、S0/PAD 与 No-Local 的 source findings 完整保留。

## 2. v0.2 source map

### 2.1 Collate fields：必要但不足

`cosmos_framework/data/generator/joint_dataloader.py:128-207,793-821` 证明 current collate/packed dataloader 可保留 `text_token_ids`、`video`、`action`、`sequence_plan` 等 raw/native values及其 list nesting；它不 materialize `GenerationDataClean`、model-generated text indexes 或 timestep。此处只证明 future raw-row schema 的可用输入，不证明 row 已被 canonical request/segment 携带。

### 2.2 Current carrier truth与唯一可审计 capture boundary

- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:26-33`：`CanonicalProductionSegmentRequest` 仅含 scheduler/plan/transaction/member/member_index/`SegmentBatch`，没有 `data_batch`、raw-row tuple 或 typed raw-row capability。
- `cosmos_framework/model/generator/mot/local_memory_segment.py:27-84`：`SegmentBatch.consumer_payload` 的 declared type 是 `tuple[tuple[Any | None,...],...]`；它只验证 `[B,T]` cardinality 与 valid/PAD presence，未声明或证明 collate-row object/field identity。
- fixtures 的 payload 可为 strings (`canonical_segment_production_adapter_test.py:30-44`) 或 arbitrary objects (`local_memory_segment_adapter_test.py:61-66`)，进一步证明 current `Any` contract 不能视作 exact collate-row carrier。
- `cosmos_framework/model/generator/omni_mot_model.py:1425-1429` 是 current process 中最后一个同时持有 live collated `data_batch` 与 resolved canonical request 的 source boundary：它解析 request 后立即调用 `_canonical_production_segment_forward(canonical_request, iteration)`。
- `_canonical_production_segment_forward()` 在同文件 `:1394-1400` 只接收 `(request, iteration)`，因而 current branch 在此已经不再拥有 `data_batch`。

结论：未来 carrier 的唯一最小**可引入** owner boundary 是 `training_step()` `:1425-1429` 的 canonical diversion 前；当前 source 没有 actual capture/association mechanism，且不得假称已经存在。后续 implementation design 必冻结一个 typed immutable `CanonicalRawRowCarrier` 在该边界如何与 exact request 的 `member`、`segment_batch` 和 later `result.gathered` 绑定：

```text
same request object
same member object / row chronology
same SegmentBatch object and logical [B,T] validity mask
same gathered stream-major identities and actual_n_valid
raw rows never derive prefixes; prefixes only carry result.gathered.local_prefixes
```

若 later design 无法从这个 model/producer seam 建立上述 association，而需要改 dataloader/collate/dataset/packer，则必须 fail closed 并另起相应 design Gate。

### 2.3 Canonical prefix authority、order、S0/PAD

- `canonical_segment_production_adapter.py:112-145` scans registered encoder/core and produces exactly one `result.gathered`.
- `canonical_segment_adapter_scheduler.py:293-321` derives `NativeConsumerBatch` via `SegmentBatch.gather_consumers()` and checks frozen identities/count.
- `local_memory_segment.py:64-106` validates valid/PAD payload rules, loops row-major/stream-major, skips PAD, and permits `None` Local only for valid S0.

Therefore future `CanonicalRawRowCarrier` must not manufacture/reconstruct Local prefixes; only the exact scan/gather result may supply them.

### 2.4 Legacy edge、safe materialization、prefix packer、CP、noise/loss

- `_prepare_training_data()` in `omni_mot_model.py:1008-1053` unconditionally invokes `_inject_local_history()` at `:1027`; enabled TTT reaches legacy `_ttt_local_memory_tokens()` / `TTTLifecycle` at `:1100-1150`.
- ordinary non-CP `_get_training_inputs()` calls that routine at `:1295-1299`; ordinary CP owner calls/caches/broadcasts it at `:1305-1327`. Neither is a canonical-safe materialization seam.
- model plan retrieval/construction is `sequence.py:1209-1264`; text conversion is `omni_mot_model.py:1948-1970`; clean materialization starts `:4157`; Local prefix is packed only at `packers.py:244-255`, with shape/cardinality constraints in `sequence.py:163-171,920-924,1082-1086`.
- timesteps/noise/packer/loss remain post-preparation model-owned at `omni_mot_model.py:1448-1605,1778+`.

The future implementation design must specify safe non-Local factoring, one prefix adaptation, and an explicit CP policy. It must not reuse ordinary injection or CP payload, write `data_batch["local_memory"]`, move timesteps/noise/loss upstream, or change native scaling.

### 2.5 No-Local

`_canonical_production_request_from_batch()` `omni_mot_model.py:134-152` returns `None` only for the strict no-marker disabled case; `training_step()` `:1425-1439` then keeps the ordinary path. The new carrier must be absent on that path.

## 3. Required next design boundary

The next docs-only implementation design may freeze only:

1. typed `CanonicalRawRowCarrier` introduction at `training_step()` canonical diversion, with exact object/row/identity binding to request/member/segment/gather;
2. model-owned safe preparation factoring and one Local-prefix adaptation; and
3. CP disposition (initial fail-closed or separately specified canonical-safe payload/broadcast contract).

It may not authorize implementation, change dataloader/collate/dataset/packer/config/optimizer/checkpoint/loss scaling, or broaden real I/O/CUDA/GPU/torchrun/training/evaluation/inference/LIBERO4IN1 scope.

## 4. Audit verdict request

```text
APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_IMPLEMENTATION
```

or `REQUEST_CHANGES(file:line)`.
