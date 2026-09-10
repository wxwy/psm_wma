# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer CPU/static Closure Remediation v2

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`  
**Formal root:** `0e88086397eb0ca709a7215fc918f5f662264fc1`  
**Formal child/Gitlink:** `d171d7149533cb31b241b402eb738d091c927ed0`  
**Previous same-Gate formal pair:** `b2fc3c85e650dff3c3a4db1c79da6d384440f091 / 1e26473aa5a17ca2ab256359fa012154bf4d9cfa`  
**Approved design authority:** `17901f65d9f09772a98921cd28ffbb05d82d3725 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541` (accumulated producer implementation design v0.1–v0.5)  
**Verdict:** `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:100)`

## 1. Repository-truth lock

- Latest `origin/V2` observed at review start is request/bookkeeping HEAD `77d1be7bf3fd40523693dcbb23ad5fa6bf2cbb7a`; the canonical request itself is persisted in ledger `e318070becb22b15a74b5360354ebbacd3adddba`. Neither is a formal implementation target.
- The request declares formal pair `0e88086397eb0ca709a7215fc918f5f662264fc1 / d171d7149533cb31b241b402eb738d091c927ed0` and asks for exactly `APPROVE_TO_CLOSE_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC` or `REQUEST_CHANGES(file:line)`.
- Formal root `0e880863...` advances the root-side Gitlink to child `d171d714...`; root changes outside the Gitlink are SESSION/TODO/review/Inbox bookkeeping and do not replace the implementation target.
- Child `d171d714...` is exactly one remediation commit ahead of previous reviewed child `1e26473...` and changes only the four already-approved files: `canonical_segment_production_adapter.py`, `canonical_segment_production_adapter_test.py`, `canonical_segment_production_integration_test.py`, and `omni_mot_model.py`.
- The request reports adapter pytest `4 passed`, integration pytest `6 passed`, Ruff, py_compile and child diff-check PASS. These execution claims are treated as evidence clues; no GitHub commit status/workflow is attached, so closure is determined from the actual production and test source.

## 2. Previous blocker lifecycle

### CLOSED — carrier marker activation isolation

The prior carrier-marker activation HIGH is closed. `_canonical_production_request_from_batch()` now tracks `canonical_production_segment_carrier` presence. Disabled No-Local rejects carrier-only input; enabled canonical mode requires exact mode, typed request and typed carrier before the ordinary path can be reached. The integration test covers the disabled carrier-only case and missing enabled carrier case.

### CLOSED — post-clean Local-neutral mapping assertion

The previously closed post-`get_data_and_condition()` assertion remains correct: the helper re-checks the working mapping for `local_memory`, re-checks all plan flags and `gen_data_clean.x0_tokens_local_memory`, then and only then performs the single gathered-prefix adaptation.

### PARTIALLY CLOSED — carrier/model-batch preflight

Several parts of the prior carrier authority HIGH are correctly remediated:

- all fallible request/member/segment/model-batch preflight now runs before adapter lookup/creation and before `adapter.scan()`;
- request transaction/plan/member identity plus `member.validate_batch(segment_batch)` are checked pre-scan;
- model key handling is dynamic and enforces exactly one of `self.input_image_key` / `self.input_video_key`, including the live default `images` key;
- list/tuple source object attribution is checked;
- a separate stacked-source record exists and checks tensor order, shape, dtype, device, leading dimension and exact stacked value;
- the new integration fixture proves one foreign model batch rejects before adapter creation.

The remaining raw/source authority defect is current HIGH 1 below.

### PARTIALLY CLOSED — Evidence

Evidence is materially stronger: carrier activation negatives are present, the B=2,T=3 carrier fixture remains, list/stacked/XOR model-batch cases are added, foreign model batch is shown to reject before adapter creation, and a real registered adapter scan is exercised followed by a controlled helper exception and exact scan-bookkeeping abort.

However the complete frozen closure matrix is still not encoded. Current HIGH 3 remains.

## 3. Current blockers

### HIGH 1 — raw-row source authority still omits the frozen `source_digest` identity and is replaced by a non-collate sentinel

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:100`

The approved producer ABI v0.2 freezes `CanonicalRawNativeRow.identity` as:

`(slot_id, episode_id, source_digest, consumer_step)`.

It also states that a non-PAD raw row contains only actual opaque collate-truth raw/native fields; foreign/reconstructed row identity must fail closed before model forward.

Current `CanonicalRawRowCarrier.expected_for()` still validates `raw["canonical_identity"]` only against the three-tuple:

`(slot_id, episode_id, consumer_step)`.

`source_digest` is not represented or checked in the raw-row identity. `member.validate_batch(segment_batch)` proves that the `SegmentBatch` itself matches the frozen member/category/provenance, but it does not prove that the raw-row object placed at `[b,t]` came from that same source. A foreign raw row from another `source_digest` can therefore reuse the same `(slot, episode, step)` triple and pass this raw-row check.

The attempted raw -> model-sample binding also introduces a second problem. `validate_model_data_batch()` requires:

`raw.get("canonical_model_sample") is source`.

That `canonical_model_sample` key is not a collate-truth field from the audited joint dataloader; the tests add it to the raw dictionaries after construction. The frozen ABI explicitly keeps raw rows as opaque collate/native truth rather than permitting producer bookkeeping to be injected into the raw payload itself. Source-object binding metadata belongs in the typed carrier/provenance record, not by mutating the raw row into a synthetic authority object.

This leaves the exact source-digest/row provenance hole from the previous review open even though request/member/segment object binding and model-batch list/stacked validation are improved.

**Violated frozen contract**

- producer ABI v0.2 `CanonicalRawNativeRow.identity = (slot_id, episode_id, source_digest, consumer_step)` and collate-truth-only raw-row semantics;
- implementation design v0.1 exact row/member/chronology authority;
- v0.3/v0.4 requirement that foreign row/source mismatch fail before scan and that model materialization be attributable to the exact logical raw source;
- previous same-Gate closure condition requiring wrong source/provenance negatives rather than triple-only equivalence.

**Exact closure condition**

Within the same four-file CPU/static scope:

1. represent and validate the raw-row source identity including exact `source_digest` before adapter creation/scan; keep the consumer-facing expected gathered identity separate if `NativeConsumerBatch.identities` intentionally remains `(slot, episode, step)`;
2. bind raw row -> producer-native model sample through typed carrier-side source/provenance metadata or exact object references without injecting a synthetic `canonical_model_sample` field into the collate-truth raw row;
3. ensure a raw row from a foreign `source_digest` with the same slot/episode/consumer-step cannot pass preflight;
4. add direct CPU negatives for foreign source_digest / reconstructed raw source and prove zero adapter creation/scan/mutation.

Do not collapse source authority back to `(slot, episode, step)`.

### HIGH 2 — `sequence_plan` canonical adaptation mutates carrier-owned raw metadata before the mandatory hard-stop

**Direct blocking location:** `cosmos_framework/model/generator/omni_mot_model.py:1440`

`_prepare_canonical_production_inputs()` starts with only a shallow `dict(carrier.model_data_batch)` copy. The live `build_sequence_plans_from_data_batch()` returns `data_batch["sequence_plan"]` directly when that key is present. `sequence_plan` is an explicitly allowed raw/native carrier key and source audit records it as optional collate metadata.

The canonical helper then executes:

`plan.has_local_memory = prefix is not None`

on those returned plan objects. For a legal carrier that supplies collated `sequence_plan` metadata, those objects are therefore the same objects held by `carrier.model_data_batch` / `row_model_samples`. The current CPU/static production path then intentionally raises before packer and calls `abort_scan()`. `abort_scan()` correctly clears scan bookkeeping, but it does not and cannot roll back the already-mutated carrier-owned plan objects.

This violates the typed carrier's immutable/source-authority role and the standing failure zero-partial-mutation contract. It also has a direct retry consequence: after a first intentional hard-stop with a non-S0 prefix, a second call using the same carrier can observe `has_local_memory=True` at the pre-clean neutrality check and fail because of state leaked from the previous attempt.

The current tests avoid the defect because the production carrier fixture omits `sequence_plan`, causing the builder to create fresh default plans, while the direct safe-helper test monkeypatches the builder to return independent `SimpleNamespace` plans.

**Exact closure condition**

- make the canonical model-prepared `SequencePlan` objects model-owned/ephemeral before applying the one Local-prefix adaptation; when raw collated `sequence_plan` metadata exists, validate/clone or reconstruct it so canonical writes do not mutate carrier/raw source objects;
- on intentional hard-stop and injected post-scan/memory-init exceptions, prove the original carrier `model_data_batch` and row source `SequencePlan` objects/flags remain unchanged while adapter scan bookkeeping is aborted;
- preserve exactly one canonical prefix adaptation on the model-owned prepared plans and do not write ordinary `data_batch["local_memory"]`.

### HIGH 3 — Evidence still does not encode the full CPU/static closure contract

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:200`

The new production test is useful but still replaces `_prepare_canonical_production_inputs` with a stub that immediately raises. It proves a real adapter scan can be followed by scan-bookkeeping abort, but it does not prove the real production path runs the actual safe helper and remains clean through the reviewed failure lifecycle.

The current two-file suite still lacks direct witnesses for several frozen/previously-requested acceptance cases:

1. foreign raw source with identical `(slot, episode, step)` but different `source_digest` rejecting before adapter creation/scan;
2. a valid non-CP production forward that uses the real `_prepare_canonical_production_inputs()` through text -> plan -> clean -> single gathered-prefix adaptation -> memory-init -> intentional hard-stop, with pending scan cleared and frontier/scheduler/transaction/commit state unchanged;
3. injected post-scan `result.gathered` identity/count mismatch through the production path, proving exact abort and zero committed mutation;
4. injected post-scan real-helper/materialization/memory-init exception with the same disposition proof;
5. explicit production-path zero-call witnesses for `_prepare_training_data()`, `_get_training_inputs()`, `_inject_local_history()` and `_ttt_local_memory_tokens()`;
6. `training_step()` No-Local parity/fall-through with no carrier/helper/adapter construction;
7. legal collated `sequence_plan` input followed by intentional hard-stop/exception proving the carrier/raw plan metadata is not mutated;
8. post-clean insertion of ordinary `local_memory` rejecting before canonical adaptation/memory-init.

The request's local `4 passed` / `6 passed` results can establish only that the submitted tests pass; they cannot establish contract behaviors that the suite does not exercise. No independent GitHub status/workflow exists for this child.

**Exact closure condition**

Add the missing direct CPU/static witnesses above while remaining before packer/noise/native forward/loss/backward and without widening to real I/O/GPU/training. The suite must encode `contract -> production behavior -> evidence`, not only unit helper behavior.

## 4. Non-blocking findings / scope

- Prior carrier-marker activation HIGH is CLOSED.
- Prior post-clean `local_memory` mapping assertion HIGH remains CLOSED.
- Prior adapter-creation-before-preflight problem is CLOSED.
- Dynamic default image key / image-video XOR issue is CLOSED.
- Tensor stacked-field ordering/value validation is materially present; no separate blocker is opened for it here.
- CP pre-scan rejection remains CLOSED.
- Nested `[B][T]`, S0/PAD traversal, expected-before-scan / actual-after-scan ordering and exact scan-bookkeeping abort remain intact.
- Child diff stays entirely inside the four approved files and does not add dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.
- `data_resolutions=None` remains a future forward-enabled Gate watchpoint only; it is not consumed before this Gate's hard-stop.

## 5. Blocker lifecycle / authorized next action

Current blocker count: **3 HIGH**.

Authorized next action: remediate only this CPU/static implementation under the already-approved v0.1–v0.5 design/producer ABI contract and return a new formal root/child pair for fresh closure review.

Do not broaden into data-side or forward-enabled work. If the team wants to redefine `CanonicalRawNativeRow.identity` to drop `source_digest`, permit synthetic bookkeeping inside raw collate rows, or permit carrier-owned `SequencePlan` mutation on failure, that is a contract change and must return to a docs-only Design Gate first rather than being silently normalized in implementation.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:100)`
