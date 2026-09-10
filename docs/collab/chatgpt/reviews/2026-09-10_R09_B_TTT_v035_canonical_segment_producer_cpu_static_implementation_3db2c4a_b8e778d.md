# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer CPU/static Implementation Remediation

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`  
**Formal root:** `3db2c4a407b42e3c8f6325a196e83223052f293d`  
**Formal child/Gitlink:** `b8e778dd2f39c58708e5d9d6751e0bd5a20cd4be`  
**Previous same-Gate formal pair:** `b7fe7f8edc6e5db53c4b6d7b43c9db0da19e6622 / ee9a63c0976dc8235124bff687b237c9a6fabc91`  
**Approved design authority:** `17901f65d9f09772a98921cd28ffbb05d82d3725 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541` (accumulated v0.1–v0.5)  
**Verdict:** `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:45)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `846c1372a9e552f359ebe9eee7a5b024194fb4ee`; it declares the exact formal pair above and is not itself the formal target.
- Formal root `3db2c4a407b42e3c8f6325a196e83223052f293d` stores `cosmos-framework` exactly at Gitlink `b8e778dd2f39c58708e5d9d6751e0bd5a20cd4be`.
- Child `b8e778d...` is reachable and is the direct child of previous reviewed child `ee9a63c...`.
- Child compare `ee9a63c... -> b8e778d...` contains exactly three changed files, all inside the approved four-file whitelist: `canonical_segment_production_adapter_test.py`, `canonical_segment_production_integration_test.py`, and `omni_mot_model.py`. The production carrier/adapter file itself is unchanged in this remediation.
- Root compare `b7fe7f8... -> 3db2c4a...` consists of prior review/persistence bookkeeping plus the Gitlink update; bookkeeping/review SHAs are not formal implementation targets.
- The request reports targeted pytest, py_compile and diff-check execution. No independent runtime execution/log capture was available in this review, so those claims are treated as evidence clues and checked against actual production/test source.

## 2. Previous blocker lifecycle

### HIGH 2 CLOSED — CP is now rejected before adapter lookup/scan

The current `_canonical_production_segment_forward()` checks `self.parallel_dims.cp_enabled` before `_canonical_production_adapter_from_model(self)`, before carrier traversal reaches the adapter, and before `adapter.scan(request)`. The new integration test also exercises this ordering with a model that has no adapter/runtime available; the CP error is raised first.

This exactly closes the previous CP pre-scan disposition blocker.

### HIGH 1 PARTIALLY CLOSED — canonical safe-preparation sequence now exists, but the frozen post-clean Local-neutral assertion is incomplete

The remediation adds `_prepare_canonical_production_inputs()` and the production branch now calls it only after actual gathered identity/count equality. The helper performs the approved main sequence:

`_load_and_tokenize_text_data()` -> `build_sequence_plans_from_data_batch()` -> pre-clean plan Local-neutral check -> `get_data_and_condition()` -> clean/plan Local-neutral check -> one adaptation from `result.gathered.local_prefixes` -> `memory_init_training()` -> return to the intentional pre-packer hard-stop.

It does not call `_prepare_training_data()`, `_get_training_inputs()`, `_inject_local_history()` or `_ttt_local_memory_tokens()` directly. The previous “hard-stop before all safe preparation” defect is therefore materially fixed.

However the frozen v0.3 contract requires a second post-`get_data_and_condition()` assertion that the **source working mapping still has no `local_memory` key** before canonical adaptation and `memory_init_training()`. Current code checks `"local_memory" not in data_batch` only before tokenization/clean materialization, then after `get_data_and_condition()` checks only `SequencePlan.has_local_memory` and `gen_data_clean.x0_tokens_local_memory`. It never re-checks the working `data_batch` mapping itself. A helper/future override that inserts an ordinary `local_memory` key without setting those two checked outputs can therefore reach the canonical adaptation and then `memory_init_training()` with a second Local authority present.

This leaves one exact piece of the prior HIGH 1 closure condition open; it is listed as current HIGH 2 below.

### HIGH 3 OPEN — carrier authority/transport was not remediated

The previous review required the carrier to be bound to exact request/member/segment/row-identity/chronology authority, full source/category/provenance, and closed `model_data_batch` derivation/keyset. It also required a return to Design Gate if `request.carrier` was intentionally replacing the frozen separate model-diversion carrier marker ABI.

The remediation child does not modify `canonical_segment_production_adapter.py` at all, so this blocker is unchanged. It is current HIGH 1 below.

### HIGH 4 PARTIALLY CLOSED — evidence improved, but closure matrix is still incomplete

The remediation adds a real `B=2,T=3` nested carrier/PAD fixture, a CP pre-scan test, and a direct safe-helper call-order/prefix-adaptation fake witness. Those are meaningful additions.

But the suite still does not directly exercise the full valid canonical production forward path through scan -> actual equality -> safe helper -> abort -> intentional hard-stop, nor several required failure/authority cases. This blocker remains open as current HIGH 3 below.

## 3. Current blockers

### HIGH 1 — carrier remains a triple-only, unbound payload and silently keeps the unapproved `request.carrier` transport

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:45`

`CanonicalRawRowCarrier` still contains only:

- `raw_rows`;
- `row_model_samples`;
- `model_data_batch`.

It does not carry/bind the exact request, member, SegmentBatch, exact row identities or exact row chronology as required by retained v0.1 authority. `expected_for(request)` validates each valid row only against `(slot_id, episode_id, consumer_step)` from the supplied `SegmentBatch`, checks the model sample repeats the same triple, and checks only total planned cardinality.

That leaves the prior authority hole intact:

- no carrier-row binding to `source_digest`;
- no carrier-row binding to category;
- no manifest/provenance/source-record binding;
- no exact row-chronology object authority;
- no exact request/member/segment object binding stored in the carrier;
- no closed top-level `model_data_batch` keyset validation;
- no per-field `raw_rows -> row_model_samples -> model_data_batch` source attribution / deterministic wrapping-or-stacking validation;
- no shape/dtype/device/leading-dimension/order validation for stacked model fields;
- a same-cardinality mapping with the same narrow `(slot, episode, step)` triples can still be foreign in the dimensions the frozen design explicitly requires.

The transport ABI is also still changed inside implementation: `CanonicalProductionSegmentRequest` has an optional `carrier` field, while the retained v0.1 contract freezes a separate exact carrier marker at the model-diversion boundary and requires the carrier itself to hold/bind request/member/segment authority. No docs-only Design Gate has authorized replacing that ABI with `request.carrier`.

**Violated frozen contract**

- v0.1 typed-carrier exact object/chronology binding;
- v0.3 closed model-batch keyset and field/source attribution;
- v0.4 pre-scan expected authority from exact frozen member/segment/chronology/provenance;
- v0.5 nested `[B][T]` storage as the sole source authority;
- prior implementation review closure condition requiring a Design Gate before intentionally retaining `request.carrier` as a replacement transport ABI.

**Exact closure condition**

Implement the already-frozen carrier authority before scan:

1. bind the carrier to the exact request/member/SegmentBatch and exact row identity/chronology authority, with full source/category/provenance attribution;
2. retain nested `[B][T]` PAD/valid semantics and reject foreign same-cardinality rows before `adapter.scan()`;
3. enforce the v0.3 closed `model_data_batch` keyset and deterministic per-row/per-field derivation from exact `row_model_samples`, including required source-key/shape/dtype/device/leading-dimension/order checks;
4. either use the frozen separate model-diversion carrier marker/transport, or return first to a docs-only Design Gate that explicitly authorizes `request.carrier` and updates the object-binding contract;
5. add direct CPU/static negative witnesses for same-cardinality foreign source/provenance/model-batch/keyset cases with zero scan calls/mutation.

Do not weaken this to `(slot, episode, step)` + count equivalence.

### HIGH 2 — post-`get_data_and_condition()` Local-neutral mapping assertion is still missing

**Direct blocking location:** `cosmos_framework/model/generator/omni_mot_model.py:1430`

The helper correctly checks `"local_memory" not in data_batch` before tokenization/clean materialization and then checks post-clean plans plus `gen_data_clean.x0_tokens_local_memory`. But immediately after:

`gen_data_clean = self.get_data_and_condition(data_batch, iteration=iteration)`

it never reasserts that the working `data_batch` mapping still has no `local_memory` key, even though v0.3 explicitly freezes that post-call assertion before the one canonical prefix adaptation.

That distinction is intentional: canonical mode must not permit a second ordinary Local source to appear between the pre-clean check and `memory_init_training()`. Checking only plan flags and clean tokens is not equivalent to checking the mapping itself.

**Exact closure condition**

Immediately after `get_data_and_condition()` and before any canonical plan/token write:

- fail closed if `"local_memory" in data_batch`;
- retain the existing all-plan-false and `gen_data_clean.x0_tokens_local_memory is None` assertions;
- add a CPU fake witness in which `get_data_and_condition()` mutates/inserts `local_memory` while leaving the checked plan/clean outputs otherwise neutral, and prove the helper rejects before canonical adaptation / `memory_init_training()`.

### HIGH 3 — submitted Evidence still does not establish the full CPU/static closure behavior

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:61`

The new tests close only part of the previous Evidence gap:

- CP pre-scan rejection is tested;
- helper call order and a two-item `(None, prefix)` adaptation are tested directly;
- adapter test now uses nested `B=2,T=3` with PAD and a narrow foreign triple mismatch.

Still missing are direct witnesses required by the approved v0.3–v0.5 acceptance contract and the previous review:

1. a valid canonical production-forward fixture that reaches `adapter.scan()`, verifies actual equality, executes the safe helper, then proves the intentional pre-packer hard-stop disposes the exact pending `_scan_requests/_scan_results` pair and leaves frontier/scheduler/transaction/commit capability unchanged;
2. injected post-scan gathered identity/count mismatch through the production path, proving exact `abort_scan()` disposition and zero commit/frontier/scheduler/transaction mutation;
3. injected post-scan safe-helper/materialization exception through the production path with the same disposition proof;
4. explicit zero-call spies/witnesses for `_inject_local_history()` and `_ttt_local_memory_tokens()` on the production branch;
5. No-Local `training_step()` parity/fall-through witness showing carrier/helper/adapter are not constructed or invoked when `local_ttt_enabled=False`;
6. pre-scan rejection evidence for foreign same-cardinality model batch, foreign source/provenance/source-key, unexpected top-level keyset, nested order, and relevant field-source mismatches;
7. the post-clean `local_memory` insertion rejection required by current HIGH 2.

The direct helper unit test is useful but does not prove that the production branch invokes the helper and then performs the reviewed abort/hard-stop lifecycle. Likewise manual `adapter.abort_scan()` testing is not equivalent to proving every production failure disposition.

**Exact closure condition**

Add the missing direct CPU/static acceptance witnesses above and return the next root/child formal pair. Runtime claims such as “pytest passed” are not sufficient unless the suite itself encodes the frozen `contract -> behavior -> evidence` matrix.

## 4. Non-blocking findings / scope

- Previous CP HIGH is CLOSED.
- The previous “safe helper absent entirely” defect is mostly CLOSED; only the explicit post-clean working-mapping Local-neutral assertion remains.
- `B=2,T=3` nested carrier/PAD coverage is now present.
- Expected-before-scan / actual-after-scan ordering remains correct.
- `abort_scan()` narrow bookkeeping semantics remain source-consistent.
- Child remediation remains inside the approved four-file whitelist and does not add real I/O, CUDA/GPU, torchrun, packer/noise/native forward/loss/backward/training/evaluation/inference/runtime-sidecar/LIBERO4IN1 scope.
- `data_resolutions` is still returned as `None` in the safe helper rather than reproducing ordinary `image_size`-derived resolution handling. Because this Gate intentionally hard-stops before packer/noise/native forward and the value is not consumed here, this is recorded as a future native-path watchpoint rather than a current closure blocker; it must not be silently carried into a later forward-enabled Gate.

## 5. Blocker lifecycle / authorized next action

Current blocker count: **3 HIGH**.

Authorized next action: remediate only this CPU/static implementation under the already-approved v0.1–v0.5 design contract and return a new formal root/child pair for fresh closure review.

If `request.carrier` is intentionally desired as the production transport ABI, do not change it further inside this implementation Gate; return to a docs-only Design Gate first and freeze that transport/binding change explicitly.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:45)`
