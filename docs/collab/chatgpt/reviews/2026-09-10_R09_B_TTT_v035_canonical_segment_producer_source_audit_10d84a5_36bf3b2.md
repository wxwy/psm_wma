# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer Source Audit v0.2

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-SOURCE-AUDIT`  
**Formal root:** `10d84a5898f447fd1ab311de10817193fc149135`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_source_audit_v0.2.md`  
**Prior approved authority:** producer ABI v0.2 at `c57e77c42b13e0a397d42c5d7979c8382b1ee144 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Previous same-Gate review:** `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_producer_source_audit_7bca138_36bf3b2.md`  
**Verdict:** `APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_IMPLEMENTATION`

## 1. Repository-truth lock

- The Codex request/ledger commit is `5cce08f8ce67328156ec1b0503740d179b6e9cf7`; it declares formal root `10d84a5898f447fd1ab311de10817193fc149135` and child/Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The formal root tree stores `cosmos-framework` exactly at Gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`.
- The child commit is reachable/readable. The child is unchanged from the prior same-Gate review, so this is a fresh incremental docs/source-audit remediation review; no child implementation verdict is inherited or repeated.
- The current `V2` advancement above the request is bookkeeping/status only and does not replace the formal pair.
- No project code, tests, real I/O, CUDA/GPU, training, evaluation or inference was executed in this review.

## 2. Previous blocker lifecycle

### CLOSED — v0.1 did not map the canonical raw-row carrier/extraction seam

The previous review raised one HIGH because v0.1 proved only that collate preserves raw/native fields, then inferred that `CanonicalGatheredRawBatch.raw_rows` could exist without identifying the actual current carrier/lifecycle boundary.

v0.2 closes that blocker exactly:

1. It now states the current repository truth explicitly: **no canonical raw-row carrier exists today**.
2. It maps `CanonicalProductionSegmentRequest` at `canonical_segment_production_adapter.py:26-33` and correctly records that the request contains scheduler/plan/transaction/member/member_index/`SegmentBatch`, but no `data_batch`, raw-row tuple or typed raw-row capability.
3. It maps `SegmentBatch.consumer_payload` at `local_memory_segment.py:27-84` as `Any | None`, and correctly distinguishes presence/PAD validation from collate-row identity/type authority. The current tests using string/object payloads are consistent with that conclusion.
4. It maps the current model boundary at `omni_mot_model.py:1425-1429`: `training_step()` still holds the collated `data_batch` when it resolves the exact canonical request, while `_canonical_production_segment_forward()` at `:1394-1400` accepts only `(request, iteration)` and therefore does not retain the raw batch.
5. It no longer describes a future carrier as an already-existing ABI. Instead, the next docs-only implementation design must explicitly introduce/freeze a typed immutable carrier at the model-owned canonical diversion boundary or fail closed and route to a separate data-side design Gate if that cannot be done without touching dataloader/collate/dataset/packer.
6. It binds the future carrier to the exact request/member/`SegmentBatch`/gather authority and stream-major cardinality while keeping Local prefixes exclusively sourced from the canonical scan/gather result.

This satisfies the previous review's exact closure conditions.

## 3. Independent source checks

### 3.1 Current request and carrier truth

`CanonicalProductionSegmentRequest` is a frozen dataclass carrying the frozen scheduling/transaction/member authority plus `SegmentBatch`, with no raw-row or `data_batch` field. `SegmentBatch.consumer_payload` remains opaque `Any`; its validation enforces `[B,T]` shape, valid/PAD presence, chronology and S0/evidence constraints, but does not type the payload as a collate-native row.

Therefore v0.2 is correct to treat current raw-row carrier absence as repository truth rather than infer a carrier from collate field availability.

### 3.2 Model-owned capture boundary

At `OmniMoTModel.training_step()`, the collated `data_batch` and resolved exact `CanonicalProductionSegmentRequest` are simultaneously available immediately before canonical diversion. The present `_canonical_production_segment_forward()` receives only request/iteration and is a fail-closed placeholder.

For this source-audit Gate, identifying that call boundary as the minimal model-owned place at which a later design may introduce a typed carrier is sufficient. The audit does not claim the association mechanism already exists and does not pre-authorize an implementation shape.

### 3.3 Identity / provenance binding

`NativeConsumerBatch.from_segment()` validates the exact frozen member against the `SegmentBatch`, gathers stream-major valid consumers, and checks `(slot_id, episode_id, step)` identities plus `planned_n_valid` exactly.

The narrower gathered identity does not erase full provenance authority: `MicrobatchPlanMember.row_identities` / `row_chronology` retain the frozen row identity/provenance, and `ChronologyCountRecord.validate_row()` checks `source_digest`, manifest digest, category, slot, episode and exact valid-step range against the `SegmentBatch`.

v0.2's requirement that the future carrier bind to the **same request object, same member object / row chronology, same SegmentBatch object and same gathered order/count** is therefore an adequate source-level constraint for the next design. The next design must not promote the narrow gathered tuple into a substitute for full member/provenance authority.

### 3.4 Preserved findings from v0.1

The previously non-blocking source findings remain valid and are correctly preserved by v0.2:

- canonical scan/gather is the sole Local-prefix/order/count authority;
- PAD is excluded and valid S0 alone may carry `None` Local prefix;
- ordinary `_prepare_training_data()` / `_get_training_inputs()` traverses legacy Local injection and is not a canonical-safe materialization path;
- ordinary CP owner preparation is therefore not automatically reusable by canonical mode;
- diffusion timestep/noise/packer/loss ownership remains model-side and post-preparation;
- No-Local keeps the untouched ordinary path;
- no dataloader/collate/dataset/packer/loss-scaling/runtime/GPU scope is authorized by this audit.

## 4. Approval boundary

Current blockers: **none**.

This approval authorizes only the next **docs-only implementation design** for:

- a typed `CanonicalRawRowCarrier` introduced at the model-owned canonical diversion boundary with exact request/member/segment/gather binding;
- canonical-safe model preparation factoring that never executes legacy `_inject_local_history()` / `_ttt_local_memory_tokens()`;
- exactly one Local-prefix adaptation from canonical scan/gather authority into the native model-prepared path; and
- an explicit CP disposition.

The next design must continue to fail closed if the required association cannot be achieved within the authorized model/producer seam and would require dataloader/collate/dataset/packer changes.

Not authorized: producer/builder implementation, child production changes, dataset/dataloader/collate/packer/config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, training, evaluation, inference, runtime sidecar, distributed execution or LIBERO4IN1.

## 5. Exact verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_IMPLEMENTATION`
