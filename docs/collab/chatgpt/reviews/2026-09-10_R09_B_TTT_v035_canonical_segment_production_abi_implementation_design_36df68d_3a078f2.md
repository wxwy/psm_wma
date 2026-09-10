# ChatGPT 独立 Canonical Segment Production ABI Implementation Design v0.3 Review

Formal reviewed pair:
- root design SHA: `36df68dff72a6cf1b9bc60f1bb97d0aa78642bb5`
- child/Gitlink SHA: `3a078f28f3d107bb633c932271f86498f7c427f7`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ABI-IMPLEMENTATION-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_abi_implementation_design_v0.3.md`
- previous formal review: `82574180f08fdee2682dd8699269e3198e7f3240 / 3a078f28f3d107bb633c932271f86498f7c427f7`, verdict `REQUEST_CHANGES`, canonical review `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_production_abi_implementation_design_8257418_3a078f2.md`.
- direct engineering authority: closed P0 source-ABI audit `395dadff0b17ed6206887e372718bb166aa63b40 / 3a078f28f3d107bb633c932271f86498f7c427f7` plus P1 v0.2 sections not superseded by v0.3.
- request/ledger/poll/session commits after the formal root are bookkeeping only and do not replace the formal pair.

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC`

## Incremental result

v0.3 precisely closes the remaining three HIGH and one MEDIUM from the v0.2 review without reopening the already-closed scan/gather, normal attempt-0 commit, S0/PAD/count, loss/GA, scan-owner or GradScaler hard-stop contracts.

### CLOSED — activation / legacy fallback

The only untouched ordinary path now requires `local_ttt_enabled=False`. With `local_ttt_enabled=True`, an exact canonical-production declaration plus exact `CanonicalProductionSegmentRequest` is mandatory before `_get_training_inputs()`; missing/malformed/foreign requests and any conflicting old canonical/active/row-wise markers fail closed. This removes the previous path by which enabled TTT could silently reach `_inject_local_history()` / `_ttt_local_memory_tokens()`.

### CLOSED — exact registered canonical encoder/core binding

v0.3 freezes the canonical construction point inside the existing `OmniMoTModel.build_net()` local-history/TTT branch: `net.local_history_runtime.encoder` is constructed with `CANONICAL_EVIDENCE_FEATURE_CONFIG`, while `recurrent_backend` is the exact registered `ContinualTTTLocalMemoryCore`. The adapter may use only those exact model-owned objects and may not construct a trainable copy. This is implementable within the existing P2 `omni_mot_model.py` whitelist and places the canonical slow parameters under the same model materialization/parallelization/optimizer ownership as the rest of the network.

### CLOSED — attempt-1 retry lineage

`CanonicalBatchWindowTransaction.retry_first_member_pre_backward()` in the exact child returns `replace(self.plan, attempt=1, ...)`, so the retry plan retains the original member tuple objects, `original_n_valid_window`, `original_ga_effective`, and plan-chain identity while closing the attempt-0 transaction. v0.3 correctly freezes attempt-1 as a typed lineage capability from that exact attempt-0 owner, forbids a second `freeze_plan()`/admission, and requires retry success to consume the original scheduler frozen member transition exactly once. This resolves the previous conflict between retry and scheduler object identity.

### CLOSED — fp32 fast-state frontier

v0.3 now requires all four `ContinualTTTFastState` tensors to remain fp32 for fresh, continuation, candidate and committed storage. Fresh state is differentiably derived from the exact registered `w0_fast_*` parameters; continuations are detached fp32 clones of the exact committed slot/episode/source/cursor predecessor. The existing core preserves the dtype of explicit `state_in` when producing updated candidate state, so a canonical fp32 `state_in` supports this contract without modifying `local_evidence.py`. The required B>1 no-alias/no-leak and registered-W0-gradient evidence is explicit.

## Retained required P2 contract

P2 implementation remains constrained by v0.2 plus the v0.3 overrides:

- pre-scan request contains no caller-supplied gathered payload/prefix/count state;
- `CanonicalProductionAdapter` owns the same-graph canonical encoder/core scan;
- `NativeConsumerBatch.from_segment(...)` remains the sole gather and `actual_n_valid` authority;
- object-bound scheduler/plan/transaction/member identity and prepared reconcile preflight are mandatory;
- `transaction.mark_backward_started(member_index)` occurs immediately before the one canonical backward;
- canonical objective is already window-normalized and must not receive a second `/GA`;
- success-only one-shot fast-state/scheduler/transaction commit remains atomic by preflight-before-first-mutation discipline;
- enabled/unsupported GradScaler or real canonical optimizer boundary remains a P2 hard stop; real Option-B semantics stay in P3;
- S0 is counted with `None` prefix, PAD produces no native item, and historical row-wise routes are not fallback authorities.

## Scope

Formal Gitlink at the reviewed root resolves exactly to `3a078f28f3d107bb633c932271f86498f7c427f7`; this remediation is docs-only.

Current blockers: **none**.

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_PRODUCTION_ABI_CPU_STATIC`

This approval authorizes only the P2 CPU/static implementation under the exact whitelist frozen by P1 v0.2/v0.3 and its directed CPU/static evidence. It does not authorize real data/cache/checkpoint I/O, CUDA/GPU, torchrun, runtime sidecar, LIBERO4IN1, training, evaluation, inference, or P3/P4 work. Any later formal root or child SHA change requires fresh independent review.
