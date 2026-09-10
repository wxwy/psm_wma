# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Implementation Design v0.2

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`  
**Formal root:** `9b8883f1d171df9b8e70062d2988310554a499e9`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.2.md`  
**Previous same-Gate formal pair:** `1cf9ec39b8af6f3f7e16670a57a94ee9a75dd79e / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.2.md:21)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `b1a46efb98e9343d64c26ab92a155c968b146925`; the ledger declares formal root `9b8883f1d171df9b8e70062d2988310554a499e9` and child/Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541` and is not itself the formal target.
- The formal root tree stores `cosmos-framework` exactly at Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child commit is reachable/readable and unchanged from the previous same-Gate review.
- Incremental compare `1cf9ec3... -> 9b8883f...` is root-docs only for this technical remediation; intervening review/Inbox/SESSION/TODO commits are persistence/bookkeeping and do not replace formal authority.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed in this Design review.

## 2. Previous blocker lifecycle

### CLOSED — v0.1 deferred safe preparation and single Local-prefix adaptation

The previous review raised one HIGH because v0.1 froze only the carrier shell and CP hard-stop while postponing canonical-safe non-Local preparation factoring and the one Local-prefix adaptation to a later Gate.

v0.2 closes that blocker itself: it now freezes a model-private safe preparation helper, the non-Local text/plan/clean preparation order, an explicit `get_data_and_condition()` -> Local adaptation -> `memory_init_training()` sequence, and the single adaptation from exact `result.gathered.local_prefixes` into `SequencePlan.has_local_memory` plus dense `x0_tokens_local_memory`.

The prior HIGH is therefore CLOSED and is not restated below.

## 3. Current blockers

### HIGH 1 — `model_data_batch` is a new unbound payload authority and is not proven Local-neutral

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.2.md:21`

The design introduces `carrier.model_data_batch` as a producer-supplied, gathered-order native collated representation and validates only coarse properties such as plan/cardinality. That is not yet enough to bind this new mapping to the already-frozen raw-row authority.

The approved source-audit contract requires the future carrier to remain tied to the exact request/member/`SegmentBatch`/row chronology and stream-major gather authority. In v0.2, `raw_rows` and `model_data_batch` coexist inside the carrier, but the design does not freeze a field-by-field derivation or identity-preserving transform from the valid `[B,T]` raw rows to `model_data_batch`. A foreign collated mapping with the right length can therefore satisfy the stated shape/count checks without being proven to contain the exact consumer rows represented by the frozen member/segment.

There is also a concrete Local-authority violation in the current child source. `OmniMoTModel.get_data_and_condition()` is not purely non-Local: it reads `data_batch["local_memory"]`, mutates `SequencePlan.has_local_memory`, and materializes `x0_tokens_local_memory`. v0.2 calls this routine before the canonical §3 adaptation but never freezes `model_data_batch["local_memory"]` as absent/fail-closed. Because current collate can carry `local_memory`, a producer-supplied `model_data_batch` may introduce an ordinary Local token source before the exact scan/gather prefixes are written, violating the single-prefix-source contract.

**Violated frozen contract**

- carrier/model-prepared inputs must be bound to the exact member/segment/gather chronology rather than accepted by cardinality alone;
- Local prefixes must come only from the exact canonical scan/gather result;
- canonical mode must not silently re-enter an ordinary Local input path through `data_batch["local_memory"]`;
- source-audit approval explicitly required the next design to freeze the exact safe model-preparation boundary rather than introduce another opaque/unverified payload layer.

**Exact closure condition**

Revise the docs-only design so that it freezes all of the following before implementation approval:

1. the concrete `model_data_batch` construction/derivation contract from `CanonicalRawRowCarrier.raw_rows`, including the allowed top-level keys, list nesting, stream-major valid-row order and which values must preserve exact object identity versus which deterministic wrapping/copying is allowed;
2. validation that every model-batch sample is attributable to the exact frozen row/member/segment chronology, not merely that `len(sequence_plan) == actual_n_valid`;
3. a strict Local-neutral precondition before `get_data_and_condition()`: ordinary `local_memory` must be absent (prefer fail-closed on key presence rather than silently consuming/stripping it), no raw/foreign Local token source may enter the model batch, and the design must state the expected pre-adaptation `SequencePlan.has_local_memory` / `gen_data_clean.x0_tokens_local_memory` state;
4. after `get_data_and_condition()`, assert the Local-neutral precondition, then perform the one canonical adaptation from exact `result.gathered.local_prefixes` only;
5. CPU/static tests for a foreign same-cardinality `model_data_batch` and for a `model_data_batch` carrying `local_memory`, both rejecting before scan/Local mutation.

If the required derivation cannot be frozen within the approved model/producer seam without dataloader/collate/dataset/packer changes, fail closed and open the separate data-side Design Gate already required by the source audit.

### HIGH 2 — the intended path scans and then deliberately hard-stops with no scan-capability failure disposition

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.2.md:26`

v0.2 orders the path as preflight -> CP reject -> `CanonicalProductionAdapter.scan()` -> safe preparation/helper -> Local adaptation -> `memory_init_training()` -> intentional hard-stop before packer/noise/forward/loss/backward.

Current `CanonicalProductionAdapter.scan()` is not bookkeeping-free: after a successful scan it records the request in `_scan_requests` and the result in `_scan_results`. That prevents the same request from being scanned again and creates a live graph-bearing scan capability. The only currently defined downstream lifecycle is commit preparation/commit success; this Gate explicitly does not reach backward/commit, and v0.2 defines no failure discard/abort/rollback for the scan capability.

Therefore the *normal intended CPU/static path* reaches a successful scan and then intentionally hard-stops while leaving adapter state behind. Any exception in tokenization, `get_data_and_condition()`, adaptation or `memory_init_training()` after the scan has the same problem. The statement that boundary validation must happen pre-scan cannot cover these post-scan runtime failures.

This converts the previous review's non-blocking scan-capability watchpoint into a real blocker.

**Violated frozen contract**

- scheduler/transaction path must preflight before mutation and failure must have zero partial mutation;
- stale/failed/unsupported paths must leave the frontier/transaction authority unchanged and must not leave a foreign or consumed capability that changes later behavior;
- this Design Gate must not introduce a successful scan lifecycle without specifying how its capability is disposed when no backward/commit occurs.

**Exact closure condition**

Before child implementation approval, freeze one exact governance-safe path:

1. either do not invoke the real adapter `scan()` in this intentionally pre-forward CPU/static bridge and narrow the acceptance claims accordingly; **or**
2. add an exact one-shot scan-failure/abort/discard contract inside the existing adapter whitelist that removes only the pending scan bookkeeping/capability and provably does not commit or alter fast frontier, scheduler or transaction state.

If option 2 is chosen, the design must specify exact identity checks and idempotence/fail-closed rules, and tests must cover both the expected intentional hard-stop and injected post-scan helper/materialization exceptions, proving no residual `_scan_requests` / `_scan_results` capability and zero frontier/scheduler/transaction commit.

Do not solve this by calling `commit_success()` without backward or by silently broadening to trainer/runtime-sidecar scope.

## 4. Non-blocking findings

- The prior safe-preparation/prefix-adaptation deferral HIGH is CLOSED.
- CP initial hard-stop remains acceptable.
- Carrier request/member/segment/chronology object-identity constraints from v0.1 remain useful and should be preserved.
- No-Local ordinary control flow remains out of this canonical carrier path.
- The four-file CPU/static whitelist can remain narrow if the two blockers are closed within it; otherwise the design must explicitly revise the whitelist before implementation.

## 5. Blocker lifecycle / scope

Current blocker count: **2 HIGH**.

Authorized next action: docs-only remediation of this same implementation-design Gate.

Not authorized: child implementation under this Gate, real producer/data pipeline changes, dataset/dataloader/collate/packer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native training/evaluation/inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.2.md:21)`
