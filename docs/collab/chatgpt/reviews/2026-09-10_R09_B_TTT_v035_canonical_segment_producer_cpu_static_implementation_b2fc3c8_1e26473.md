# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer CPU/static Authority Remediation

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-CPU-STATIC-IMPLEMENTATION`  
**Formal root:** `b2fc3c85e650dff3c3a4db1c79da6d384440f091`  
**Formal child/Gitlink:** `1e26473aa5a17ca2ab256359fa012154bf4d9cfa`  
**Previous same-Gate formal pair:** `3db2c4a407b42e3c8f6325a196e83223052f293d / b8e778dd2f39c58708e5d9d6751e0bd5a20cd4be`  
**Approved design authority:** `17901f65d9f09772a98921cd28ffbb05d82d3725 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541` (accumulated v0.1–v0.5)  
**Verdict:** `REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:58)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `f13ab347e1d2ee8d489bfa7e7f133a6187ecebfb`; it declares the exact formal pair above and is not itself the formal target.
- Formal root `b2fc3c85e650dff3c3a4db1c79da6d384440f091` stores `cosmos-framework` exactly at Gitlink `1e26473aa5a17ca2ab256359fa012154bf4d9cfa`.
- Child `1e26473...` is reachable and is one commit ahead of previous reviewed child `b8e778d...`.
- Child compare `b8e778d... -> 1e26473...` changes exactly four files, all within the approved four-file whitelist: `canonical_segment_production_adapter.py`, `canonical_segment_production_adapter_test.py`, `canonical_segment_production_integration_test.py`, and `omni_mot_model.py`.
- Root compare `3db2c4a... -> b2fc3c8...` is the child Gitlink update plus prior review/Inbox/request bookkeeping. Those bookkeeping commits are not implementation authority.
- The request reports CPU-only targeted tests/py_compile/diff-check. No GitHub Actions workflow run or commit status is attached to child `1e26473...`; local run claims are therefore treated as evidence clues and closure is determined from production/test source.

## 2. Previous blocker lifecycle

### CLOSED — post-`get_data_and_condition()` working-mapping Local-neutral assertion

The previous HIGH at `omni_mot_model.py:1430` is closed. The current `_prepare_canonical_production_inputs()` now re-checks `"local_memory" in data_batch` immediately after `get_data_and_condition()` and before the single canonical prefix adaptation, while retaining the plan-false and clean-token-`None` checks. This satisfies the exact frozen v0.3 Local-neutral ordering requirement.

### PARTIALLY CLOSED — carrier transport/object binding

The previous carrier HIGH is materially improved:

- the optional `request.carrier` field has been removed;
- an independent `canonical_production_segment_carrier` marker is restored at the model diversion boundary;
- `CanonicalRawRowCarrier` now stores exact request/member/SegmentBatch/row-identity/row-chronology references and checks object identity;
- a top-level model-batch allowlist and same-cardinality foreign object test have been added.

However the native model-batch/source authority and preflight ordering remain incomplete and are current HIGH 1 below.

### PARTIALLY CLOSED — Evidence

The new adapter fixture proves one same-cardinality `text_token_ids` object-identity mismatch and the prior B=2,T=3/PAD fixture remains. The helper/CP unit witnesses also remain. But the full production-path/failure/No-Local matrix required by the previous review is still absent; current HIGH 3 remains.

### Previously closed items remain closed

- CP enabled is rejected before adapter lookup/scan.
- The canonical-safe helper exists and executes text -> plan -> clean -> one gathered-prefix adaptation -> `memory_init_training()` before the intentional pre-packer hard-stop.
- Nested `[B][T]` carrier storage, expected-before-scan / actual-after-scan equality, and narrow exact-once `abort_scan()` semantics remain intact.

## 3. Current blockers

### HIGH 1 — model-batch/source authority is still not the frozen native-collate contract, and foreign preflight may mutate adapter state

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:58`

The new authority validator is not source-compatible with the frozen v0.3 design or current collate/model configuration.

First, `_MODEL_BATCH_KEYS` hard-codes `"image"`, while live `OmniMoTModelConfig.input_image_key` defaults to `"images"` and the frozen design explicitly requires `self.input_image_key XOR self.input_video_key`, not a static adapter-owned literal set. The current validator therefore rejects the model's default legal image key and also does not enforce the required image/video XOR policy.

Second, `validate_model_data_batch()` requires every top-level value to be a `list`/`tuple` whose length equals the valid gathered count, and then requires every item to be object-identical to `row_model_samples[row][step][key]`. Current `custom_collate_fn()` only uses list-collation for a subset of keys; other native fields are `default_collate`d into tensors. The frozen v0.3 design explicitly permits deterministic stacked tensors and requires source-key, shape, dtype, device, leading-dimension and row-order provenance checks for them. The current carrier has no such stacked-field provenance path and rejects those legal native forms outright.

Third, the relation `raw_rows -> row_model_samples` is still under-specified in code. A row model sample only needs to repeat the narrow `canonical_identity` triple; it need not prove that it is the exact producer-native sample derived from the corresponding raw row. A reconstructed foreign `row_model_samples` mapping can therefore become its own source of truth if `model_data_batch` points to objects owned by that reconstructed mapping.

Fourth, full preflight is still ordered after adapter lookup. `_canonical_production_segment_forward()` calls `_canonical_production_adapter_from_model(self)` before `carrier.expected_for()` and `carrier.validate_model_data_batch()`. That helper creates and stores `self._canonical_production_adapter` when absent. Thus a foreign carrier can be rejected before `adapter.scan()` yet still mutate adapter/model state, contrary to the frozen CPU/static acceptance requirement for foreign carrier/model-batch rejection with zero adapter mutation.

Finally, `expected_for()` object-binds carrier metadata but does not independently run the request-plan/member identity and `member.validate_batch(segment_batch)` checks before adapter invocation. Category/provenance/chronology incompatibilities can therefore reach `adapter.scan()` and be rejected only inside the scan method rather than by the promised zero-scan preflight.

**Violated frozen contract**

- v0.1 exact carrier/member/segment/chronology preflight and zero-mutation rejection;
- v0.3 closed model-data key policy, `self.input_image_key XOR self.input_video_key`, exact per-row source attribution, and deterministic stacked-tensor provenance;
- v0.4 pre-scan expected authority from exact frozen member/segment/chronology/provenance;
- source-audit requirement that foreign source/order/count authority fail before canonical scan rather than being reduced to cardinality/triple checks.

**Exact closure condition**

Within the approved four-file CPU/static scope:

1. move all fallible carrier/request/model-batch authority validation before adapter lookup/creation and before `adapter.scan()`;
2. preflight exact request-plan/member/transaction identity plus `member.validate_batch(segment_batch)` semantics so category/provenance/chronology failures are zero-scan/zero-adapter-mutation;
3. make model-batch key validation model-key aware: exact `input_image_key XOR input_video_key` plus the frozen optional keyset, including the live default `images` key;
4. implement both approved source forms: per-row list/tuple object attribution and deterministic stacked-tensor attribution with explicit source-key/shape/dtype/device/leading-dimension/order validation;
5. bind each `row_model_samples[b][t]` to the exact producer-native source associated with `raw_rows[b][t]`, rather than accepting an independently reconstructed mapping that merely repeats `(slot, episode, step)`;
6. add direct negative/positive CPU witnesses for wrong category/provenance/source, default image key, image/video conflict, valid stacked tensor, foreign stacked tensor/order, and same-cardinality reconstructed row-model source; all preflight failures must prove adapter lookup/scan zero-call or zero creation/mutation.

### HIGH 2 — the restored separate carrier marker is not included in the activation matrix, so carrier-only No-Local input silently falls through

**Direct blocking location:** `cosmos_framework/model/generator/omni_mot_model.py:142`

`_CANONICAL_PRODUCTION_CARRIER_KEY = "canonical_production_segment_carrier"` is defined, but `_canonical_production_request_from_batch()` tracks only `mode_present`, `request_present`, and legacy markers. The `local_ttt_enabled=False` branch therefore returns `None` when the batch contains only the canonical carrier marker.

`training_step()` then enters the ordinary No-Local path because carrier extraction/type checking happens only after a non-`None` canonical request. This violates the retained v0.1 carrier rule that the carrier marker is valid only alongside the exact enabled canonical mode/request and must be rejected when supplied on No-Local.

This is a production activation isolation issue, not merely missing test coverage: a canonical capability can currently be silently ignored by the ordinary route.

**Exact closure condition**

- include carrier presence in the canonical activation matrix;
- when `local_ttt_enabled=False`, reject any canonical mode/request/carrier or legacy Local marker;
- when enabled, require the exact canonical mode + exact request + typed carrier tuple and reject missing/foreign/conflicting carrier before ordinary preparation;
- add a No-Local carrier-only negative witness and prove the ordinary helper/adapter path is not entered for malformed canonical marker combinations.

### HIGH 3 — Evidence still does not establish the full production closure matrix

**Direct blocking location:** `cosmos_framework/model/generator/mot/canonical_segment_production_integration_test.py:64`

The actual integration test file still contains only:

- activation/request parsing checks that do not include the new carrier marker matrix;
- registered adapter binding;
- CP pre-scan rejection;
- a direct `_prepare_canonical_production_inputs()` fake helper test.

It still does not run a valid non-CP `_canonical_production_segment_forward()` or `training_step()` through the real canonical adapter/carrier lifecycle. Therefore the suite does not directly establish:

1. valid production scan -> actual equality -> safe helper -> intentional pre-packer hard-stop -> exact pending scan abort with unchanged frontier/scheduler/transaction/commit state;
2. injected actual gathered identity/count mismatch -> exact abort and zero commit/frontier/scheduler/transaction mutation;
3. injected post-scan helper/materialization exception -> exact abort and zero partial mutation;
4. production-path zero calls to `_prepare_training_data()`, `_get_training_inputs()`, `_inject_local_history()` and `_ttt_local_memory_tokens()`;
5. No-Local `training_step()` parity and carrier/helper/adapter non-construction;
6. the restored carrier marker's malformed/disabled activation cases;
7. full carrier authority cases from HIGH 1, including source/category/provenance/keyset/default-image/stacked-tensor behavior;
8. post-clean `local_memory` insertion rejection, even though the production assertion itself is now correctly implemented.

The adapter test's new same-cardinality `text_token_ids` object mismatch is useful but proves only one list-valued field case. There are no GitHub Actions runs or commit statuses for this child to provide an independent execution record, so the request's local pytest claim cannot substitute for absent acceptance scenarios in the suite itself.

**Exact closure condition**

Add the direct CPU/static production and negative witnesses above so the test suite itself encodes `contract -> production behavior -> evidence`. Keep the test boundary before packer/noise/native forward/loss/backward and do not expand into real I/O/GPU/training.

## 4. Non-blocking findings / scope

- Previous post-clean Local-neutral production defect is CLOSED.
- Separate carrier transport has been restored in principle; its activation isolation is the remaining transport issue.
- CP pre-scan rejection remains CLOSED.
- Safe helper call order and single canonical prefix adaptation remain present.
- B=2,T=3 nested/PAD fixture remains present.
- Expected-before-scan / actual-after-scan ordering and narrow `abort_scan()` remain intact.
- Child changes remain entirely inside the approved four-file whitelist.
- No dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint mutation, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1 work is introduced.
- `data_resolutions=None` remains a later forward-enabled Gate watchpoint only; this CPU/static path still hard-stops before consumers of that value.

## 5. Blocker lifecycle / authorized next action

Current blocker count: **3 HIGH**.

Authorized next action: remediate only this CPU/static implementation under the already-approved v0.1–v0.5 design contract and return a new formal root/child pair for fresh closure review.

Do not broaden to data-side or forward-enabled work. If the team wishes to materially simplify the frozen native model-batch/source attribution contract instead of implementing it, return to a docs-only Design Gate first rather than weakening it inside implementation closure.

Not authorized: dataset/dataloader/collate/packer/trainer/config/optimizer/checkpoint changes, real producer/data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native forward/loss/backward/training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:58)`
