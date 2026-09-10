# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer ABI Design Remediation

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-ABI-DESIGN`  
**Formal root:** `ce705715b71752382632e8c6d2de7791b319d431`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md`  
**Prior reviewed pair:** `c9596881eea09962ecaccc8d0b2b14eb57e6c8fa / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:27)`

## 1. Repository-truth lock

- `origin/V2` was locked at request/ledger HEAD `c25262653638ce692859934afe1c00fbe8e4182f`; its parent is the declared formal root `ce705715b71752382632e8c6d2de7791b319d431`.
- The formal root tree stores `cosmos-framework` as gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`, exactly matching the request.
- The child is unchanged from the immediately prior ChatGPT-reviewed pair, so this is a fresh incremental **root-design** review, not a repeated child implementation review.
- The formal remediation commit itself changes only `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md` (`9 additions / 9 deletions`). Intervening review/Inbox/AGENTS commits are bookkeeping/process provenance and are not substituted for the formal target.
- No project code, real I/O, CUDA/GPU, training, evaluation, or inference was executed by this reviewer; this is a source-backed static Design Gate review.

## 2. Prior blocker lifecycle

The previous HIGH at `:17` is **CLOSED** in its original form.

The remediation now correctly separates collate-truth raw/native rows from model-owned materializations:

- `CanonicalRawNativeRow` no longer claims ownership of `GenerationDataClean`, model-generated `input_text_indexes`, or diffusion timesteps;
- model-side tokenization / clean-generation materialization / CP handling remain model-owned;
- diffusion timestep generation remains after preparation at the existing model noise-level seam;
- S0/PAD/order/count/fail-closed and legacy-route exclusions remain stated.

That directly fixes the lifecycle-ownership error identified in the `c959688 / 36bf3b2` review.

However, the revised design now freezes the **reuse path** for model-side preparation in a way that conflicts with both the already-approved P1 activation contract and the live child. This is a new Design blocker exposed by the corrected ownership boundary.

## 3. Current blocker

### HIGH — “call existing `_prepare_training_data()` / `_get_training_inputs()` once” re-enters the forbidden legacy TTT injection path

**Location:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:27`
- same document `:32` (output ownership symptom)
- same document `:46` (source-audit instruction)

**Relevant frozen authority / live source:**
- `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md:13-18` — canonical activation must intercept before ordinary `_get_training_inputs()`; enabled canonical mode must not call `_inject_local_history()` / `_ttt_local_memory_tokens()`.
- `cosmos_framework/model/generator/omni_mot_model.py:1425-1438` — live `training_step()` resolves the canonical request and returns `_canonical_production_segment_forward(...)` before the ordinary `_get_training_inputs(...)` call.
- `cosmos_framework/model/generator/omni_mot_model.py:1020-1034` — `_prepare_training_data()` calls `_load_and_tokenize_text_data()`, `build_sequence_plans_from_data_batch()`, then unconditionally calls `_inject_local_history(...)` before `get_data_and_condition()`.
- `cosmos_framework/model/generator/omni_mot_model.py:1100-1112` — when `local_ttt_enabled=True`, `_inject_local_history()` calls `_ttt_local_memory_tokens(...)` and writes those legacy-produced tokens into `data_batch["local_memory"]` / `SequencePlan.has_local_memory`.
- `cosmos_framework/model/generator/omni_mot_model.py:1144-1150` — `_ttt_local_memory_tokens()` lazily obtains/creates `self._ttt_lifecycle` via `TTTLifecycle.from_registered_modules(self.net)`.

**Why this blocks the Design Gate**

The remediation text at `:27` says that after stream-major raw-row gather the canonical path will call the **existing model-side preparation chain once**, preserving `_load_and_tokenize_text_data()`, `build_sequence_plans_from_data_batch()`, `get_data_and_condition()` and CP handling. Source-audit item 2 at `:46` makes that more concrete by asking how gathered rows enter existing `_prepare_training_data()` / `_get_training_inputs()`.

But the existing `_prepare_training_data()` is not a Local-neutral native-materialization primitive. In the current child it always invokes `_inject_local_history()`, and under the very condition required for canonical TTT (`local_ttt_enabled=True`) that function enters `_ttt_local_memory_tokens()` and therefore the legacy `TTTLifecycle` route.

That contradicts two already-frozen requirements in the same authority chain:

1. canonical production is intercepted before ordinary `_get_training_inputs()` specifically so enabled TTT cannot fall through to the legacy injection path; and
2. the producer-ABI design itself says the new path must not fall back to `_get_training_inputs()`, old row-wise routes, `TTTLifecycle`, active wiring, or v0.5 sidecar as an implicit converter.

Therefore the current text cannot be implemented literally while preserving its own authority. Either a later implementation would re-enter legacy TTT and violate canonical ownership/exact-once state semantics, or it would silently factor/bypass part of `_prepare_training_data()` even though that canonical-safe materialization seam has not been frozen by this Design Gate.

This is not something the next source audit may simply “discover and decide” after approval: the Design Gate must first state that the canonical branch reuses the **native non-Local materialization semantics** without traversing the legacy Local injection side effect.

### Same-root schema symptom (not a second blocker)

At `:32`, `CanonicalNativeConsumerBatch` still declares `sequence_plans: tuple[SequencePlan, ...]` even though `:27` says producer itself only freezes raw gather identity/order/Local prefix and `build_sequence_plans_from_data_batch()` remains model-side. Because a raw row may merely contain an existing plan *if one was collated*, while the native model path may create a plan when absent, the current producer-output ownership is ambiguous.

This should be resolved together with the same lifecycle blocker, not counted separately: either the producer output is a purely gathered raw batch (`raw_rows`, canonical Local prefixes, identities, count), followed by a distinct canonical-safe model-prepared bundle; or the design must explicitly define a post-materialization object whose `sequence_plans` are produced by the canonical-safe model seam. It must not make `SequencePlan` simultaneously producer-owned and model-built.

## 4. Exact closure condition

Revise the docs-only design narrowly so that it freezes a source-accurate canonical materialization boundary:

1. Preserve the corrected ownership split from this remediation: raw/collate rows stay pre-model; `GenerationDataClean`, tokenized inputs, CP semantics, and diffusion timesteps remain model-owned.
2. Explicitly prohibit the canonical path from invoking the ordinary `_prepare_training_data()` / `_get_training_inputs()` flow **in any form that executes `_inject_local_history()` or `_ttt_local_memory_tokens()`**. Reuse/factoring of their non-Local native preparation semantics may be proposed, but the next source audit must map the exact safe seam `file:line`.
3. Freeze where the canonical `local_prefixes` become the `SequencePlan.has_local_memory` / native Local-prefix input relative to plan construction and `get_data_and_condition()`, without creating a second legacy Local token source or a second TTT state transition.
4. Align the producer output schema with that boundary: do not require model-generated `SequencePlan` in a pre-model producer result unless it genuinely existed in the collated raw row; preferably distinguish raw gathered producer output from a later model-prepared native batch.
5. Keep timestep/noise sampling at the current post-preparation model seam; keep S0 `None`, PAD exclusion, stream-major order, exact count, fail-closed identity, No-Local parity, and all current scope prohibitions unchanged.
6. Rewrite source-audit item 2 so the audit proves the canonical-safe preparation seam rather than presupposing that ordinary `_prepare_training_data()` / `_get_training_inputs()` is directly reusable.

The source audit may then determine the smallest concrete factoring/builder path and whether it fits an allowed whitelist. It must `REQUEST_CHANGES` and open a new design Gate if the safe seam requires unauthorized dataset/collate/packer changes or changes native loss/noise semantics.

## 5. Blocker count / authorization

- Previous `c959688 / 36bf3b2` HIGH: **CLOSED**.
- New blocker: **1 HIGH**.
- No separate blocker is raised for S0, PAD, stream-major gather, actual/planned count equality, model-owned timestep semantics, or docs-only scope.

This verdict authorizes only another narrow **docs-only producer-ABI lifecycle remediation**.

Not authorized: source-audit closure, producer implementation, child production changes under this Gate, dataloader/collate/packer changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, training, evaluation, inference, runtime sidecar, distributed execution, or LIBERO4IN1.

## 6. Exact verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.1.md:27)`
