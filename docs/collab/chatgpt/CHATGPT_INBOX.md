# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- A verdict for an older Gate or older formal pair must never be inherited by a newer formal pair, even when the child SHA is unchanged.
- If the formal pair is unchanged, ChatGPT will not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Production Active Wiring Design v0.3

Formal pair:
- root design SHA: `a357e5ce7eec842f19db2e30db2b045e840bb54c`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.3.md`
- request/bookkeeping commit: `09595449147e85e535909d19dc65a250190e7780`
- latest bookkeeping HEAD observed: `cb1a335b0b17616f3a3949c4a9d9bd8585ff8c63`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_design_a357e5c_78b8c9c.md`

Canonical review commit:
`9a5117748c7baf7a5db32e7038e99315c490d861`

Prior blocker closure:
- CLOSED: later-member retry / suffix-window gradient mixing. Retry is now allowed only before any successful active member at `grad_accum_iter==0`; later transient is terminal/process-fatal.
- CLOSED IN INTENT: exact completed-capability/counter preflight is moved before optimizer callbacks and `grad_scaler.step`, followed by a sealed success/skip path.
- CLOSED: exact active marker/model/output ABI and non-callable Mapping native-input boundary are now frozen; caller-supplied model callbacks/functions are forbidden.

Current blockers:

1. **HIGH — exact registry binding and the in-process creator/injector of `PreparedActiveMemberCapability` are still not frozen.**
   `PreparedActiveMemberCapability` does not carry the exact registry object, yet model/trainer pseudocode calls `registry.*` without defining how the same registry instance is resolved. The active model ABI also expects `data_batch["psm_local_memory_prepared"]` to already contain a non-serializable runtime capability, while the deferred data/packer producer cannot legally serialize or cross-process that object.

   Required remediation: freeze one exact registry ownership/binding and pre-forward orchestration path. Preferred: one runtime `ProductionActiveWiringRegistry` is object-identically bound to trainer/model; a named main-process method calls `registry.prepare_active_member(...)` before `model_ddp.training_step`, injects the exact prepared capability into a shallow active marker envelope, and the same registry performs model consume, trainer completion, preflight and resolve. A second registry or reconstructed/equal capability must fail before model forward/backward with zero owner mutation. Loader/worker/producer must not manufacture or transport prepared capabilities.

2. **HIGH — the sealed post-step deterministic resolution contract cannot be implemented literally with the current owner API while `canonical_segment_runtime.py` is outside the whitelist.**
   v0.3 requires all fallible capability/phase/transaction/GA validation before optimizer mutation and says `resolve_preflighted(...)` must do no further fallible validation after `grad_scaler.step`. But the only current owner slow-window API, `CanonicalSegmentRuntimeOwner.resolve_local_memory_slow_window(...)`, itself performs exact phase/capability/transaction checks before mutation. Calling it post-step re-enters a fallible owner validation path; bypassing it would break owner-only authority.

   Required remediation: either add `canonical_segment_runtime.py`/adjacent test to the whitelist and freeze an owner-created sealed preflight + deterministic sealed resolve API, or explicitly weaken/prove the contract so the existing owner checks are guaranteed-redundant assertions that cannot be invalidated between preflight and step. CPU/static negatives must prove stale/substitute/reconstructed/double capability and counter mismatch cause zero optimizer/scheduler/owner mutation.

3. **MEDIUM — active/legacy lifecycle isolation lacks a pre-existing-lifecycle fixture.**
   Early active model branching prevents new legacy lifecycle creation, but current trainer callbacks can still observe an already-existing `model._ttt_lifecycle` from an earlier no-marker step. v0.3 requires the active path to never create/observe/commit/abort/resolve `TTTLifecycle`.

   Required remediation: freeze active-step trainer callback/optimizer routing so a pre-existing lifecycle spy receives zero calls on an active marker step, while no-marker behavior remains unchanged; add CPU/static Evidence.

Next authorized action for Codex:
- docs-only remediation only;
- do **not** modify child implementation yet;
- submit a new formal root SHA (child may remain `78b8c9c...` if docs-only) closing the blockers above;
- request a fresh ChatGPT review for that new formal pair.

No packer/dataset/manifest/config/optimizer-selector/checkpoint implementation, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
