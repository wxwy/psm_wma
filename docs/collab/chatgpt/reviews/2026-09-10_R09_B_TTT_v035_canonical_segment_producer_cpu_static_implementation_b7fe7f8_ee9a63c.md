# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer CPU/static Implementation

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`  
**Formal root:** `b7fe7f8edc6e5db53c4b6d7b43c9db0da19e6622`  
**Formal child/Gitlink:** `ee9a63c0976dc8235124bff687b237c9a6fabc91`  
**Approved design authority:** `17901f65d9f09772a98921cd28ffbb05d82d3725 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541` (accumulated v0.1–v0.5)  
**Verdict:** `REQUEST_CHANGES(cosmos_framework/model/generator/omni_mot_model.py:1409)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `d6af224b96ec1f8410dbac97544af45c96d92751`; it declares the exact formal pair above and is not itself the formal target.
- The formal root commit is `b7fe7f8edc6e5db53c4b6d7b43c9db0da19e6622`; its tree stores `cosmos-framework` exactly at Gitlink `ee9a63c0976dc8235124bff687b237c9a6fabc91`.
- Child `ee9a63c...` is reachable and is a direct child of the previously approved child `36bf3b2...`.
- The child implementation commit changes only three files, all within the four-file whitelist: `canonical_segment_production_adapter.py`, `canonical_segment_production_adapter_test.py`, and `omni_mot_model.py`. The allowed integration-test file was not changed. No dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint file is changed.
- The request reports `6 passed`, target `py_compile`, and child `git diff --check` PASS. These claims are treated as evidence clues only; closure is evaluated against the actual production diff and actual test contents.

## 2. What is correctly implemented

Several narrow pieces of the approved design are present and are not blockers:

1. The carrier uses nested `raw_rows[B][T]` / `row_model_samples[B][T]`; no flat carrier field is introduced.
2. PAD entries are required to be `None`, valid entries are required to be present, and the expected traversal stores `(row, step)` logical indexes rather than a second raw source.
3. Actual `result.gathered.identities` / count are compared only after `adapter.scan()`.
4. `abort_scan(request, result)` is exact-pair checked, exact-once for the pending scan bookkeeping, and removes only `_scan_requests` / `_scan_results`; the current canonical hard-stop path aborts before re-raising.
5. The branch rejects `model_data_batch` containing `local_memory` before scan.
6. No native packer/noise/forward/loss/backward, real I/O, GPU, torchrun, optimizer, training, evaluation, inference or LIBERO4IN1 work is introduced by this child commit.

These points do not close the Gate because multiple mandatory CPU/static contracts from the approved design are still absent.

## 3. Current blockers

### HIGH 1 — canonical branch hard-stops before the approved safe preparation and single Local-prefix adaptation are implemented

**Direct blocking location:** `cosmos_framework/model/generator/omni_mot_model.py:1409`

After pre-scan expected validation and post-scan gathered equality, the production branch immediately raises:

`RuntimeError("canonical-production native forward seam is unavailable")`.

The accumulated approved design does not authorize closure at that earlier boundary. v0.3 §3/§5, retained by v0.4/v0.5, requires this CPU/static implementation to exercise the canonical-safe model preparation sequence without entering legacy Local injection:

- `_load_and_tokenize_text_data()`;
- `build_sequence_plans_from_data_batch()`;
- `get_data_and_condition()`;
- post-`get_data_and_condition()` Local-neutral assertions;
- exactly one adaptation from the exact `result.gathered.local_prefixes` into `SequencePlan.has_local_memory` and dense `gen_data_clean.x0_tokens_local_memory`;
- `memory_init_training()`;
- only then the intentional hard-stop before packer/noise/forward/loss/backward.

The current child implements none of those steps. There is no canonical safe-preparation helper, no post-clean Local-neutral witness, no single canonical prefix adaptation, and no `memory_init_training()` call on the canonical path. Therefore the implementation is a smaller pre-bridge than the formally approved CPU/static implementation contract and cannot be closed as this Gate.

**Exact closure condition**

Within the already-approved whitelist/design boundary, implement the model-owned canonical-safe preparation sequence exactly as frozen: do not call `_prepare_training_data()`, `_get_training_inputs()`, `_inject_local_history()` or `_ttt_local_memory_tokens()`; perform the non-Local preparation, prove Local-neutral state before/after `get_data_and_condition()`, perform exactly one prefix adaptation from the actual canonical gather, run `memory_init_training()`, then abort the scan and hard-stop before the native packer/noise/forward/loss/backward seam. Add the corresponding CPU/static witnesses.

### HIGH 2 — CP-enabled canonical mode is not rejected before scan

**Direct blocking location:** `cosmos_framework/model/generator/omni_mot_model.py:1405`

The approved v0.1–v0.5 contract explicitly keeps CP fail-closed for this Gate: when `parallel_dims` declares CP enabled, canonical mode must reject before `adapter.scan()` and before any scan capability/state mutation.

The current `_canonical_production_segment_forward()` checks carrier presence and `local_memory`, then calls `adapter.scan(request)` unconditionally. It never inspects `self.parallel_dims` / `cp_enabled`. Consequently a CP-enabled canonical request reaches the scan, violating the frozen pre-scan CP disposition even though the function later aborts on its generic hard-stop.

**Exact closure condition**

Add the exact CP-enabled preflight before `adapter.scan()` and prove with CPU/static integration evidence that CP-enabled canonical mode causes zero scan calls/bookkeeping/frontier/scheduler/transaction mutation. Do not route through ordinary CP preparation/cache.

### HIGH 3 — carrier pre-scan authority is weaker than the frozen object/provenance/model-batch binding contract

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:45`

The retained v0.1 typed-carrier contract requires an immutable capability bound to the exact request/member/`SegmentBatch`, exact `row_identities`, and exact `row_chronology`; v0.3/v0.5 additionally require closed-keyset, per-row source attribution from the nested raw authority into `model_data_batch`, and rejection of foreign same-cardinality mappings before scan.

The implemented `CanonicalRawRowCarrier` contains only:

- `raw_rows`;
- `row_model_samples`;
- `model_data_batch`.

It does not carry or object-bind the exact request/member/segment/row identities/row chronology. Instead, `expected_for(request)` compares each raw row only to the narrow `(slot_id, episode_id, consumer_step)` triple from the supplied `SegmentBatch`, checks that each model sample repeats that same triple, and finally checks only `planned_n_valid` cardinality. It does not bind the raw/model rows to `source_digest`, category, manifest/provenance or the exact frozen chronology; nor does it validate the approved closed top-level `model_data_batch` keyset, nested arity, field-level source-object attribution, deterministic wrapping/stacking metadata, dtype/device/leading dimension, or row order. Apart from rejecting `local_memory` later, `model_data_batch` is otherwise unused/unvalidated.

The implementation also silently changes the frozen carrier transport: v0.1 requires the typed carrier to be supplied as its own exact `data_batch` marker at model diversion and itself contain the exact request/member/segment authority; the child instead adds an optional `carrier` field directly to `CanonicalProductionSegmentRequest` without a corresponding design change.

This means a same-cardinality carrier/model mapping with the same narrow `(slot, episode, step)` values but foreign source/provenance/content can pass the current carrier preflight. That is precisely the authority hole the producer source-audit/design sequence was intended to close.

**Exact closure condition**

Implement the frozen carrier capability/binding rather than a narrow triple-only surrogate. Before scan, prove exact request/member/segment/row-identity/chronology authority, full source/category/provenance attribution, nested `[B,T]` PAD/valid semantics, and the closed `raw_rows -> row_model_samples -> model_data_batch` derivation/keyset contract. If retaining `request.carrier` instead of the frozen separate marker is intentional, return to a docs-only Design Gate and explicitly change/freeze that ABI first; do not silently redefine it in an implementation closure.

### HIGH 4 — the submitted CPU evidence suite does not test the required closure behavior

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:22`

The request cites the two named pytest files and reports `6 passed`, but the actual integration test file is unchanged at this child and contains only:

- activation-matrix/request parsing checks; and
- registered encoder/core adapter-binding checks.

It never calls `_canonical_production_segment_forward()` or `training_step()` with a real canonical request/carrier. It therefore provides no direct evidence for:

- CP pre-scan rejection;
- canonical safe-preparation call order;
- legacy `_inject_local_history()` / `_ttt_local_memory_tokens()` zero-call behavior on the production branch;
- `get_data_and_condition()` / `memory_init_training()` witnesses;
- pre/post Local-neutral assertions;
- single canonical prefix adaptation with mixed S0/non-S0/PAD;
- post-scan actual-identity/count mismatch followed by exact abort;
- intentional hard-stop and injected post-scan exceptions leaving frontier/scheduler/transaction/commit capability unchanged;
- No-Local production-path parity.

The newly added adapter test is also only `B=1,T=2` and exercises one narrow foreign `(slot, episode, step)` mismatch; it does not satisfy the v0.5 `B=2,T=3` nested fixture or the v0.3/v0.4 source-key/model-batch/CP/prefix/actual-mismatch acceptance matrix.

Thus `6 passed` demonstrates only that the current reduced suite passes; it does not establish `contract -> real CPU/static behavior -> evidence` for the closure request.

**Exact closure condition**

Add/restore the exact CPU/static acceptance tests frozen in v0.3–v0.5, including `B=2,T=3` mixed S0/non-S0/PAD, foreign same-cardinality/source-key/model-batch rejection pre-scan, CP zero-scan, production safe-preparation/legacy-zero-call witness, single prefix adaptation, actual mismatch abort, intentional/injected post-scan failure disposition, and No-Local parity. Then return the new root/child formal pair with direct test evidence.

## 4. Blocker lifecycle / scope

- The v0.4 carrier **storage-shape** HIGH remains CLOSED: this child does use nested `[B][T]` storage.
- The earlier Design-Gate pre/post-scan authority-order defect remains CLOSED: this child computes expected pre-scan and compares actual gathered post-scan.
- The earlier exact-once scan-abort Design blocker remains CLOSED at the narrow bookkeeping level implemented here.
- Current implementation-closure blockers: **4 HIGH**.

The current three-file diff remains within the approved child whitelist and does not itself broaden into real data/GPU/training scope. The problem is missing/underpowered implementation and missing evidence, not whitelist expansion.

Authorized next action: remediate only this CPU/static implementation under the accumulated approved design contract, or return to a docs-only Design Gate for any intentional ABI change such as carrying the carrier inside `CanonicalProductionSegmentRequest`.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 5. Exact verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/omni_mot_model.py:1409)`
