# ChatGPT Independent Review — R09-B / TTT v0.3.5 Canonical Segment Producer ABI Design v0.2

**Date:** 2026-09-10  
**Role:** Independent Design / Code / Evidence / Gate Reviewer  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCER-ABI-DESIGN`  
**Formal root:** `c57e77c42b13e0a397d42c5d7979c8382b1ee144`  
**Formal child/Gitlink:** `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Artifact:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_producer_abi_design_v0.2.md`  
**Prior reviewed pair:** `ce705715b71752382632e8c6d2de7791b319d431 / 36bf3b2c3fd1bdd364df9169fa6d177f94e16541`  
**Verdict:** `APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_ABI`

## 1. Repository-truth lock

- `origin/V2` was locked after the Codex request at bookkeeping/session HEAD `f705033c111e83369a6f9ce160a887e3390a4a13`; the request commit is `f0a84274709eef36d4dc3f758b8fc12c1bbf3947`, whose parent is the declared formal root `c57e77c42b13e0a397d42c5d7979c8382b1ee144`.
- The formal root tree stores `cosmos-framework` as gitlink `36bf3b2c3fd1bdd364df9169fa6d177f94e16541`, exactly matching the request.
- The child commit is reachable/readable in `wxwy/cosmos-framework` and is unchanged from the immediately prior ChatGPT-reviewed pair. This is therefore a fresh incremental root-design review, not a repeated child implementation review.
- Relative to the prior formal root, the new technical design artifact is v0.2; intervening ChatGPT review/Inbox, SESSION/TODO and request/bookkeeping changes were treated as provenance/coordination only and were not substituted for the formal target.
- No project code, real I/O, CUDA/GPU, training, evaluation or inference was executed. This is a source-backed static Design Gate review.

## 2. Prior blocker lifecycle

The prior HIGH from the `ce705715 / 36bf3b2` review is **CLOSED**.

v0.2 now explicitly fixes the contradiction that blocked v0.1:

1. It states that canonical production must not directly call, wrap, or reach through the ordinary CP path into `_prepare_training_data()` / `_get_training_inputs()` when that path executes `_inject_local_history()` / `_ttt_local_memory_tokens()`.
2. It separates a pre-model `CanonicalGatheredRawBatch` from the later model-owned `CanonicalModelPreparedBatch`; `GenerationDataClean`, model-built/validated `SequencePlan`, tokenized indexes, CP semantics and diffusion timestep generation are no longer falsely owned by an upstream row/producer.
3. It leaves the exact canonical-safe model materialization seam to the next docs-only source audit and requires that audit to supply exact `file:line`, owner, CP ownership and any proposed minimal factoring/builder whitelist. This does not pre-authorize a new builder or implementation.
4. It freezes a single canonical Local-prefix mapping and explicitly forbids a second Local token source or second TTT state transition.
5. Diffusion timesteps remain model-owned and post-preparation at the existing noise-level seam.
6. The source-audit questions now require proof that the canonical path avoids the legacy injection edge rather than presupposing that ordinary `_prepare_training_data()` / `_get_training_inputs()` is directly reusable.

These changes satisfy the exact closure conditions of the previous review without relaxing S0/PAD/order/count/fail-closed/No-Local or Gate-scope requirements.

## 3. Independent source consistency check

The current child remains consistent with why the new design split is necessary and feasible to audit:

- `cosmos_framework/model/generator/omni_mot_model.py:1425-1438` resolves a canonical production request and returns through `_canonical_production_segment_forward(...)` before the ordinary `_get_training_inputs(...)` path.
- `cosmos_framework/model/generator/omni_mot_model.py:1020-1034` shows ordinary `_prepare_training_data()` building tokenized inputs / plans and then calling `_inject_local_history(...)` before `get_data_and_condition()`.
- `cosmos_framework/model/generator/omni_mot_model.py:1100-1112` routes enabled Local TTT through `_ttt_local_memory_tokens(...)`; `:1144-1150` binds that route to legacy `TTTLifecycle`.
- `cosmos_framework/model/generator/mot/canonical_segment_production_adapter.py:21-37,102-137` shows the canonical request/scan authority and that canonical scan produces `CanonicalProductionScanResult.gathered` from the registered encoder/core path.
- `cosmos_framework/model/generator/mot/canonical_segment_adapter_scheduler.py:287-319` shows `NativeConsumerBatch.from_segment(...)` as the stream-major gather authority for payload/local-prefix/identity and exact planned count.

Thus v0.2 correctly does **not** claim that the existing ordinary preparation function is already the safe seam; it authorizes the next source audit to identify the smallest non-Local native materialization seam while preserving the existing canonical scan/gather authority.

## 4. Non-blocking source-audit watchpoints

No blocker is raised here, but the next source audit must make these points explicit before any implementation design is authorized:

- `CanonicalGatheredRawBatch.local_prefixes` must stay bound to the existing canonical scan/gather authority (`CanonicalProductionScanResult.gathered` / `NativeConsumerBatch.from_segment(...)`), not be reconstructed from raw rows or accepted from an arbitrary foreign producer. v0.1's retained invariant that gathered payload/prefix/identity derive from the canonical `NativeConsumerBatch.from_segment(...)` authority remains in force.
- The exact safe materialization seam must prove zero calls to `_inject_local_history()` / `_ttt_local_memory_tokens()` on the canonical route, including through CP handling or helper factoring.
- The audit must locate exactly where gathered canonical `local_prefixes` map once into the model-built/validated `SequencePlan.has_local_memory` / native Local-prefix input. S0 remains `None`; PAD remains absent.
- If `memory_init_training`, CP broadcast/cache handling, or any proposed factoring has a stateful Local side effect that cannot be separated without changing unauthorized source, the source audit must return `REQUEST_CHANGES` and open the appropriate new design Gate.
- Any need to modify dataset/collate/packer, alter native noise/loss scaling, or broaden runtime/GPU/I/O scope remains outside this approval.

These are audit obligations, not implementation permissions.

## 5. Gate disposition

Current blockers: **none**.

This approval authorizes only the next **docs-only source audit** for the exact producer/native-materialization seam described by v0.2. The audit must return a concrete `file:line` source map and must fail closed if the safe seam cannot be realized within the stated design boundary.

Not authorized by this verdict: producer implementation, canonical-safe builder/factoring implementation, child production changes, dataset/dataloader/collate/packer changes, config/optimizer/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, GradScaler runtime work, training, evaluation, inference, runtime sidecar, distributed execution, or LIBERO4IN1.

## 6. Exact verdict

`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCER_ABI`
