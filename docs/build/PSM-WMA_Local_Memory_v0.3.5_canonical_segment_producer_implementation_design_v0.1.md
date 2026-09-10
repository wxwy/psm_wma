# PSM-WMA Local Memory v0.3.5 Canonical Segment Producer Implementation 设计 v0.1

**日期**：2026-09-10
**状态**：docs-only design；须三方同 SHA 批准后才可进行 CPU/static child implementation
**Gate**：`G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`
**前置 authority**：producer source audit v0.2（`10d84a5/36bf3b2`）

## 1. Scope 与 fail-closed boundary

当前 child 没有生产性 `SegmentBatch` builder，也没有 raw-row carrier；`MicrobatchPlanMember` 不保存 collated batch index。故本 Gate 只授权一个 CPU/static bridge：用显式 typed carrier 在 model canonical diversion 处证明 immutable binding、legacy-zero-call、CP fail-closed 与 native prefix contract。它不授权真实 producer、raw-row materialization、native forward/loss、scheduler commit、真实 I/O 或训练。

任何缺少 typed carrier、carrier 与 request/member/segment/gather 不同一、CP enabled、raw-row payload 缺失或无法形成 safe prepared batch，必须在 scan、legacy injection、packer、forward、backward 前 fail closed；不得以 `SegmentBatch.consumer_payload: Any`、ordinary `_prepare_training_data()` / `_get_training_inputs()`、active wiring、row-wise route 或 v0.5 sidecar 补救。

## 2. 最小 child 白名单与 owner

仅允许修改：

1. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py`：新增 immutable carrier/binding validator；不改 `SegmentBatch`、scheduler 或 scan semantics；
2. `cosmos_framework/model/generator/omni_mot_model.py`：在 `training_step()` canonical diversion 捕获 typed carrier，CP hard-stop，传入 canonical forward；新增只读/无 Local side effect的 prepared-boundary validator，保持 native forward hard-stop；
3. `cosmos_framework/model/generator/mot/canonical_segment_production_adapter_test.py`：carrier object/identity/cardinality/foreign rejection CPU fixtures；
4. `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py`：model diversion、CP reject、legacy injection/token function zero-call、No-Local parity CPU fixtures。

禁止新增/改动 dataloader、collate、dataset、packer、config、optimizer、trainer、checkpoint、runtime sidecar、loss/noise/timestep 或其他 child 文件。

## 3. Typed carrier contract

在 adapter module 定义 frozen `CanonicalRawRowCarrier`，由 canonical producer（此 Gate 的 CPU fixture；非 dataloader）在 model diversion前附加到 `data_batch` 的新 exact marker key。它至少包含：

```text
request: CanonicalProductionSegmentRequest       # exact same object
segment_batch: SegmentBatch                      # request.segment_batch is same object
member: MicrobatchPlanMember                     # request.member is same object
raw_rows: tuple[tuple[Mapping[str, Any] | None, ...], ...]  # logical [B,T]
row_identities: tuple[SegmentIdentity, ...]      # exact request.member.row_identities
row_chronology: tuple[ChronologyCountRecord, ...]# exact request.member.row_chronology
```

Validation requirements before any scan:

- `request`, `segment_batch`, `member`, row identities and chronology are object-identical to request authority; no reconstructed equal objects;
- raw row outer width equals `SegmentBatch.consumer_valid.shape[0]`, every inner width equals T;
- PAD is `None`; every valid `[b,t]` is a mapping object; its opaque contents remain unmaterialized;
- valid rows/steps and row chronology match `member.validate_batch(segment_batch)`; no prefix is accepted or derived from raw rows;
- after adapter scan, carrier validates `result.gathered.identities` and `item_count` against the same stream-major valid traversal and `member.planned_n_valid`; only `result.gathered.local_prefixes` is usable as prefix authority.

The marker is required only with exact canonical mode/request and must be rejected if supplied in No-Local or alongside legacy markers. It is an explicit bridge input, not evidence that current collate/segment production already supplies raw rows.

## 4. Model seam and CP disposition

`training_step()` already owns both `data_batch` and resolved request at `omni_mot_model.py:1425-1429`. P2 must obtain and validate the carrier there, before calling canonical forward. `_canonical_production_segment_forward()` receives `(request, carrier, iteration)` and verifies `carrier.request is request` again.

Initial CP disposition is strict fail-closed: when `parallel_dims` declares CP enabled, canonical carrier branch raises before scan or mutation. It must not call ordinary `_get_training_inputs()` because its owner preparation and CP cache traverse `_inject_local_history()`.

The safe preparation helper may only validate the carrier’s raw/native shape/provenance and the future prepared-batch boundary; it must not call `_load_and_tokenize_text_data()` / `build_sequence_plans_from_data_batch()` / `get_data_and_condition()` yet, because this Gate has no frozen raw-row batching schema or native materialization implementation. It must explicitly hard-stop before packer/noise/forward/loss after proving legacy-zero-call. A later Gate may freeze real model-owned non-Local factoring and the one dense `x0_tokens_local_memory` / `SequencePlan.has_local_memory` adaptation.

## 5. CPU/static acceptance

Run only the two named pytest files, target `py_compile`, and child/root `git diff --check`. Fixtures must prove:

1. `B=2,T=3` mixed S0/non-S0/PAD carrier is object-bound to request/member/segment; raw mapping identity, stream-major order, actual count and S0 `None` prefix survive adapter scan;
2. foreign/equal-but-not-identical request/member/segment/carrier, wrong `[B,T]`, non-mapping valid row, PAD payload, chronology/count mismatch all reject pre-scan with no adapter/scheduler/frontier mutation;
3. enabled canonical mode without/malformed carrier, CP-enabled carrier, and legacy marker conflict reject before `_inject_local_history()` / `_ttt_local_memory_tokens()`; both call counts stay zero;
4. canonical forward remains explicit hard-stop before native materialization/packer/noise/loss/backward; No-Local still follows ordinary control-flow unchanged;
5. no test reads data/cache/checkpoint, uses GPU/CUDA, torchrun, optimizer, real GradScaler, training/evaluation/inference or LIBERO4IN1.

## 6. Verdict

请求唯一 verdict：

```text
APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC
```

或 `REQUEST_CHANGES(file:line)`。
