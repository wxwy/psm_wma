# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Implementation Design v0.3

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`  
**Formal root:** `4e77930d3ce414c3ab233c5021f04c0697f2a56d`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.3.md`  
**Previous same-Gate formal pair:** `9b8883f1d171df9b8e70062d2988310554a499e9 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.3.md:26)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start is request/ledger HEAD `93b61366c7b617738cf11dcc80bfaf9a0710119b`; the ledger declares the exact formal pair above and is not itself the formal design target.
- The formal root tree stores `cosmos-framework` exactly at Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child commit is reachable/readable and unchanged from the previous same-Gate review.
- Incremental compare `9b8883f... -> 4e77930...` is root-docs only for this technical remediation; the new technical artifact is implementation design v0.3. Intervening review/Inbox/SESSION/TODO commits are persistence/bookkeeping and do not replace formal authority.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed in this Design review.

## 2. Previous blocker lifecycle

### HIGH 2 CLOSED — post-scan hard-stop / exception now has an exact scan-capability disposition

v0.3 defines `abort_scan(request, result)` inside the already-authorized adapter whitelist. The proposed operation is identity-bound to the exact pending pair, exact-once, removes only `_scan_requests` / `_scan_results`, does not create or consume commit capability, and explicitly forbids frontier/scheduler/transaction/candidate-state mutation. The intended normal CPU/static hard-stop and every post-scan helper/materialization exception are required to abort before re-raising.

This matches the prior review's exact closure option. Current `CanonicalProductionFastStateFrontier.state_for()` is read-only with respect to the committed frontier dictionary and `scan()` only registers the request/result after constructing the graph-bearing result, so removing the exact pending registration without calling `prepare_commit()` / `commit_success()` is a source-consistent CPU/static abort contract.

This HIGH is CLOSED.

### HIGH 1 PARTIALLY CLOSED — Local-neutrality and concrete model-batch derivation are now specified, but the pre-scan authority check is temporally impossible as written

v0.3 materially improves the previous model-batch authority gap:

- it freezes an allowed canonical preparation keyset;
- it requires source-key / per-row source-object attribution and rejects foreign same-cardinality mappings;
- it fail-closes on `local_memory` key presence before `get_data_and_condition()`;
- it asserts pre/post `get_data_and_condition()` Local-neutral state and performs exactly one later adaptation from exact canonical gathered prefixes;
- it adds CPU/static witnesses for foreign model batch, Local key rejection, Local-neutrality, and source-order checks.

Those portions close the prior HIGH 1 findings about ordinary Local authority and coarse length-only acceptance.

One source-order defect remains and blocks implementation approval.

## 3. Current blocker

### HIGH — v0.3 requires `result.gathered`-based validation before `adapter.scan()` even though `result.gathered` does not exist until `scan()` completes

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.3.md:26`

At lines 26-30, the design requires `raw_rows`, `row_model_samples` and `model_data_batch["sequence_plan"]` to have length equal to `result.gathered.item_count` and order equal to `result.gathered` stream-major identities. Later in the same section it requires any identity/order/count failure to be rejected **before `adapter.scan()`**.

That sequencing cannot be implemented from the current child source:

- `CanonicalProductionAdapter.scan(request)` computes Local tokens/presence, then calls `NativeConsumerBatch.from_segment(...)`, and only then constructs `CanonicalProductionScanResult(..., gathered=...)`.
- `NativeConsumerBatch.from_segment(...)` itself derives the actual gathered payloads/prefixes/identities from the segment and checks them against the frozen member.
- therefore an actual `result.gathered` object is a post-scan value. It cannot be an input to a zero-scan-mutation preflight.

The design currently forces an implementation to violate one of its own contracts: either scan first in order to obtain `result.gathered` and thereby lose the promised pre-scan rejection, or skip the exact `result.gathered` check and weaken the stated authority binding.

This is the remaining part of the prior raw/model authority HIGH; it is not a new unrelated blocker.

### Related ABI-stage ambiguity

The same section says v0.3 preserves the v0.1 typed carrier while redefining `CanonicalRawRowCarrier.raw_rows` as a stream-major valid gathered tuple. v0.1's retained typed-carrier contract defined `raw_rows` as logical `[B,T]` with PAD=`None`, with only a **post-scan** validation against `result.gathered`. Producer ABI v0.2 likewise distinguishes logical `[B,T]` raw-row input from the stream-major valid `CanonicalGatheredRawBatch` output.

The new wording can be made coherent, but the design must explicitly choose and name the stage rather than simultaneously preserve the old `[B,T]` carrier contract and use a gathered-valid `raw_rows` field. This ambiguity belongs to the same pre/post-scan authority root cause and is therefore not counted as a second blocker.

**Violated frozen contract**

- all foreign identity/cardinality/source failures that are promised as pre-scan must be decidable from pre-scan authority;
- `result.gathered` remains the sole actual canonical scan/gather result and cannot be fabricated/reconstructed before scan;
- Local prefixes must continue to come only from that actual scan result;
- the carrier/raw-bundle stage must remain unambiguous about logical `[B,T]` vs stream-major valid gather.

**Exact closure condition**

Revise the docs-only design narrowly so it freezes two distinct validation phases:

1. **Pre-scan expected-authority validation** — derive an immutable expected stream-major valid identity/count traversal solely from the exact frozen `request.member`, exact `request.segment_batch`, chronology/provenance and the carrier's raw-row source binding. Validate `raw_rows` / `row_model_samples` / `model_data_batch` against that expected traversal before calling `adapter.scan()`. Do not reference an actual `CanonicalProductionScanResult` here.
2. **Post-scan actual-result validation** — after successful `adapter.scan()`, require `result.gathered.identities` and `item_count` to exactly equal the already-validated expected traversal/count, and only then allow safe preparation / canonical prefix adaptation. Any mismatch must go through the reviewed `abort_scan(request, result)` disposition before re-raise.
3. Explicitly resolve the carrier stage/shape:
   - either retain v0.1 logical `[B,T]` `raw_rows` and define a separate expected/gathered raw view; or
   - explicitly supersede the v0.1 raw-row shape and define the producer-side deterministic gather from logical `[B,T]` source rows into the carrier's valid stream-major tuple.
   In either case, PAD exclusion and source-object/provenance attribution must remain exact and Local prefixes must not be present before the real scan result.
4. Add CPU/static acceptance proving a foreign order/count/source mismatch rejects **without calling scan**, plus a post-scan injected actual-result mismatch path that aborts the exact pending scan pair and leaves frontier/scheduler/transaction/commit state unchanged.

No dataset/dataloader/collate/packer change is required by this review. If the intended pre-scan expected traversal cannot be derived within the already-approved model/producer seam, the design must fail closed and route to the separate data-side Gate rather than weakening identity authority.

## 4. Non-blocking findings

- The previous post-scan capability-leak HIGH is CLOSED by the exact-once abort contract.
- The previous ordinary `local_memory` / second Local source issue is CLOSED by key-presence fail-closed plus pre/post Local-neutral assertions.
- The single canonical prefix adaptation remains correctly placed after `get_data_and_condition()` and before `memory_init_training()` for this CPU/static design, with S0/PAD/dense-index semantics preserved.
- CP pre-scan hard-stop remains acceptable.
- The four-file whitelist remains sufficiently narrow for the proposed CPU/static implementation if the remaining authority-order blocker is fixed within it.
- No new blocker is raised against No-Local parity, legacy zero-call policy, packer-before hard-stop boundary, or the stated prohibition on real producer/data I/O/GPU/training.

## 5. Blocker lifecycle / scope

Current blocker count: **1 HIGH**.

Authorized next action: docs-only remediation of this same implementation-design Gate.

Not authorized: child implementation under this Gate, real producer/data pipeline changes, dataset/dataloader/collate/packer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native training/evaluation/inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.3.md:26)`
