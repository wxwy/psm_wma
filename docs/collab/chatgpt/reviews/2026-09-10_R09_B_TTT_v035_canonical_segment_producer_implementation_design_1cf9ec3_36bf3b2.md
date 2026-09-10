# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Implementation Design v0.1

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN`  
**Formal root:** `1cf9ec39b8af6f3f7e16670a57a94ee9a75dd79e`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.1.md`  
**Prerequisite source-audit pair:** `10d84a5898f447fd1ab311de10817193fc149135 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.1.md:54)`

## 1. Repository-truth lock

- Latest `origin/V2` at review start was request/ledger HEAD `f9a8d7df0384fa508ef87c23ca89e17148053c80`; it declares the exact formal pair above and is not itself the formal design target.
- The formal root tree stores `cosmos-framework` exactly at Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child commit is reachable/readable and unchanged from the approved source-audit pair.
- Incremental compare `10d84a5... -> 1cf9ec3...` is ahead by six root commits; the new technical design artifact is `PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.1.md`. Intervening source-audit review / CHATGPT_INBOX / SESSION / TODO changes are persistence/bookkeeping and do not replace formal authority.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed in this Design review.

## 2. What is correct in v0.1

The design correctly preserves several already-approved boundaries:

1. It does not pretend a production raw-row carrier already exists. The proposed `CanonicalRawRowCarrier` is explicitly a future typed bridge input, not inferred from `SegmentBatch.consumer_payload: Any`.
2. Carrier validation is intended to bind the exact request/member/segment authority, exact row chronology and stream-major cardinality; raw rows cannot create Local prefixes, and canonical scan/gather remains the sole Local-prefix authority.
3. No-Local and legacy-marker conflict handling remain fail-closed; ordinary `_prepare_training_data()` / `_get_training_inputs()` is not reused as a canonical path.
4. Initial CP disposition is a strict hard-stop, which is a valid option under the approved source audit.
5. The four-file CPU/static whitelist is narrow, and the document clearly excludes real producer/materialization, native forward/loss, scheduler commit, real I/O, GPU, training/evaluation/inference and LIBERO4IN1.

Those points are not blockers.

## 3. Current blocker

### HIGH — the Design Gate defers two mandatory implementation-design obligations to another later Gate

**Direct blocking location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.1.md:54`

At line 54 the design states that the safe preparation helper must not yet call text tokenization, plan construction or `get_data_and_condition()`, must hard-stop before packer/noise/forward/loss, and that **a later Gate may freeze the real model-owned non-Local factoring and the one dense `x0_tokens_local_memory` / `SequencePlan.has_local_memory` adaptation**.

That is inconsistent with the frozen prerequisite authority for this exact next Design Gate:

- producer source audit v0.2 §2.4 states: **“The future implementation design must specify safe non-Local factoring, one prefix adaptation, and an explicit CP policy.”**
- producer source audit v0.2 §3 authorizes the next docs-only implementation design for exactly: typed carrier introduction, **model-owned safe preparation factoring and one Local-prefix adaptation**, and CP disposition.
- the previous ChatGPT approval for `10d84a5 / 36bf3b2` repeats the same approval boundary: the next docs-only implementation design is for the typed carrier, canonical-safe model preparation factoring, exactly one Local-prefix adaptation into the native model-prepared path, and explicit CP disposition.

The current v0.1 only freezes the carrier shell and CP hard-stop. It explicitly postpones the other two required pieces.

### Why this blocks `APPROVE_TO_IMPLEMENT...PRODUCER_CPU_STATIC`

The live model source shows why these are material design obligations rather than optional later implementation detail. `_prepare_training_data()` currently executes, in order, text tokenization, `SequencePlan` construction, unconditional `_inject_local_history()`, `get_data_and_condition()`, then `memory_init_training()`. The canonical-safe design therefore has to state which non-Local portions are factored/reused and where the legacy Local edge is bypassed. Without that design, there is still no frozen contract from `CanonicalRawRowCarrier` to the model-owned prepared representation.

Likewise, there is still no frozen single write/adaptation point from canonical `result.gathered.local_prefixes` into the native prepared representation (`SequencePlan.has_local_memory` / dense Local tokens). Approving child implementation now would therefore authorize only a marker/validator that intentionally hard-stops before the required prepared/native ABI exists. That does not satisfy the already-approved implementation-design Gate and would require another design decision before any real producer/materialization path could be implemented.

This is a Design-Gate completeness/authority violation, not a demand to implement real training or GPU work now.

### Exact closure condition

Choose one of the following governance-correct paths.

**A. Keep this same `CANONICAL-SEGMENT-PRODUCER-IMPLEMENTATION-DESIGN` Gate.** Revise the docs-only design so it freezes, before child implementation approval:

1. the exact model-owned canonical-safe preparation factoring in `omni_mot_model.py`: input/output schema and ordering for text indexes, model-built/validated `SequencePlan`, `GenerationDataClean`, `get_data_and_condition()` and `memory_init_training()`, while proving `_inject_local_history()` / `_ttt_local_memory_tokens()` are never entered;
2. the exact one-and-only-one adaptation point for canonical `result.gathered.local_prefixes` into the native prepared path, including S0 `None`, PAD exclusion, stream-major identity/count and the relationship between `SequencePlan.has_local_memory` and dense Local tokens;
3. the explicit CP disposition (the current fail-closed policy is acceptable if retained);
4. the exact CPU/static whitelist and acceptance tests needed to prove those contracts without claiming real I/O/GPU/training.

If the safe factoring/adaptation requires files outside the current four-file whitelist, expand the docs-only whitelist explicitly and return the revised design for review; do not let implementation choose this ad hoc.

**B. Intentionally keep only a carrier-validation pre-bridge.** Then this must not be presented as closure of the already-authorized producer implementation-design Gate or request `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_CPU_STATIC`. Define a narrower pre-implementation/bridge Gate and return later to the required implementation design that freezes safe preparation and the one Local-prefix adaptation.

## 4. Non-blocking transaction watchpoint

Current `CanonicalProductionAdapter.scan()` records the request/result in internal `_scan_requests` / `_scan_results` after constructing the scan result. Therefore an intentionally fail-closed model path must not perform a successful scan and then hard-stop while leaving an un-disposed scan capability unless an explicit, reviewed abort/reset contract exists. The current design can avoid this by hard-stopping before scan, so this is not counted as a second blocker in this Design review; it must remain explicit in the remediation/acceptance sequence.

## 5. Blocker lifecycle / scope

- Previous source-audit raw-row carrier HIGH remains **CLOSED**; this review does not reopen it.
- Current implementation-design blocker count: **1 HIGH**.
- No independent blocker is raised against carrier object/provenance binding, scan/gather prefix authority, No-Local parity, legacy-marker conflict rejection, initial CP fail-closed policy, or the stated CPU/static scope.

Authorized next action is only docs-only remediation of this implementation design.

Not authorized: child implementation under this Gate, real producer/materialization, dataset/dataloader/collate/packer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, native training/evaluation/inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_implementation_design_v0.1.md:54)`
