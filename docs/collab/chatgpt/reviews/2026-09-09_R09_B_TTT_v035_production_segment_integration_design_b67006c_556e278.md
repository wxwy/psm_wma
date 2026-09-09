# ChatGPT 独立 Production Segment Integration Design v0.3 review

Formal reviewed pair:
- root design SHA: `b67006c3cbd8b3be37549f1746c3cc57a0dcc26b`
- child/Gitlink SHA: `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-DESIGN`
- previous formal pair: `1359c762c84eb5f957baf286a87ce72cd82fb128` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- upstream closed runtime-owner authority: `e74184ee8ef76c2618658c2bf9cc12ab4d183e8a` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- request/bookkeeping HEAD observed: `e45d861c6f3e938dc0a0dfb69ced0ac05648f9a3`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only remediation review relative to v0.2. Child is unchanged. Root changes are the new v0.3 design plus bookkeeping/review persistence. v0.3 correctly addresses the three v0.2 blockers in substance: retained-retry has an explicit entry mode, the pure backward seam restores `validate_success -> finite objective -> one backward`, and GradScaler is moved out of the per-member seam to a post-window boundary with real Local `.grad` clearing.

Those fixes are directionally correct, but two authority/phase contracts remain under-specified and can produce divergent implementations.

## Prior blocker closure

- **CLOSED IN SUBSTANCE — retained retry entry.** `RetryMemberCapability` now provides a legal `MEMBER_READY` retry entry with no second admission or `begin()`.
- **CLOSED IN SUBSTANCE — pre-backward validation / finite ordering / classification.** The trainer seam now explicitly performs exact transaction validation before the current finite/scaling owner and before a single backward, and no longer originates transient/scaler results.
- **CLOSED IN SUBSTANCE — GradScaler timing and actual slow-grad cleanup.** v0.3 moves real scaler resolution to the post-window optimizer boundary and requires actual `wiring.clear_local_slow_grads()` for terminal/retry/scaler cleanup.

## Current blockers

1. **HIGH — continuation/retry still accept a caller-supplied `plan` without proving `plan is transaction.plan`, so objective scaling authority can diverge from the exact transaction.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_segment_integration_design_v0.3.md:20-32,60-72`

   `run_member(...)` carries a `plan` argument on every call. Initial entry is safe because `owner.begin(plan)` stores that exact plan in the transaction. Continuation and retained-retry entries, however, only require exact owner/transaction state and then continue with the caller-supplied `plan`; the design never requires `plan is owner.transaction.plan`.

   The pure backward seam likewise accepts both `plan` and `transaction`, validates identity/count through `transaction.validate_success(...)` (which uses `transaction.plan`), but computes the finite/scaled objective from the separate caller `plan`. A substitute plan can therefore keep the current member projection and current planned count identical while changing later counts / `n_window` / `ga_effective` / chain metadata, causing a different objective scale without violating the transaction precheck. That recreates the plan-authority class of bug already closed in the runtime-owner design.

   **Acceptance:** make the transaction-owned plan the sole scaling authority. Either remove the public/trainer `plan` argument after initial `begin()` and always derive `plan = transaction.plan`, or require object identity (`plan is transaction.plan`) before any callback/objective/backward on continuation and retry. The pure backward seam must use `transaction.plan` (or an object-identical alias) for `CanonicalSegmentRuntimeAdapter.objective`. Add a negative CPU/static fixture with same current member/count but modified later counts/order/chain metadata and prove rejection before callback/backward with zero owner/scheduler/pending/grad mutation.

2. **HIGH — last-member `finish_window()` semantics conflict with the closed runtime owner and the new `SLOW_RESOLUTION_PENDING` capability is not frozen as an exact one-shot owner boundary.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_segment_integration_design_v0.3.md:46-54,78-90`
   - current source: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py:94-100`

   v0.3 says the last successful member calls `owner.finish_window(transaction)` inside the bridge and returns `CompletedWindowCapability`; §3 then says that capability makes the owner enter `SLOW_RESOLUTION_PENDING` until the real optimizer/scaler resolution consumes it. The currently closed owner contract does the opposite: `finish_window()` clears `identity/transaction/forward` and immediately sets phase=`IDLE`.

   v0.3 authorizes modifying `canonical_segment_runtime.py`, but it does not explicitly supersede/freeze the new exact `finish_window` semantics: whether the owner retains the transaction, retains an exact completed-capability handle, whether snapshot/admit/begin are forbidden while slow resolution is pending, and how substitute/stale/double `CompletedWindowCapability` is rejected. Without that, two incompatible implementations are possible: (a) keep old `finish_window -> IDLE` and resolve through a detached caller-held transaction, or (b) change `finish_window` to a pending phase with owner-retained authority. Only the latter matches the stated owner-controlled post-window contract, but it is not yet frozen.

   **Acceptance:** explicitly supersede the old normal-finish boundary for this bridge and freeze one exact state transition, e.g. `MEMBER_COMMITTED(all complete) -> finish_window -> SLOW_RESOLUTION_PENDING`, with no snapshot/admit/begin/prepare while pending. The owner must retain (directly or via an object-identical internal pending handle) the exact transaction and exact `CompletedWindowCapability`; `resolve_local_memory_slow_window` must consume that exact capability once, reject reconstructed/stale/double consumption with zero mutation, perform success/skip bookkeeping/grad-clear as specified, then clear pending authority and only then enter `IDLE`. Add CPU/static positive/negative fixtures for success and scaler-skip resolution plus stale/substitute/double-resolve rejection.

## Scope boundary

No implementation authority is granted for this pair. It remains docs-only. No child production bridge/trainer/runtime-owner changes, real SegmentBatch producer/packer, dataset/cache/checkpoint I/O, model execution, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`
