# ChatGPT 独立 Production Segment Integration Design v0.1 review

Formal reviewed pair:
- root design SHA: `454c06086a6b2d198dd726feed66d2edb1b8d4f0`
- child/Gitlink SHA: `556e278946b506195a57d0798b2b1a2e8b5eb9cc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-SEGMENT-INTEGRATION-DESIGN`
- request/bookkeeping HEAD observed: `128f2146210174511306d74edae1460d504d8a84`
- upstream closed runtime-owner authority: `e74184ee8ef76c2618658c2bf9cc12ab4d183e8a` / `556e278946b506195a57d0798b2b1a2e8b5eb9cc`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh design review relative to the closed runtime-owner pair. Child is unchanged. Root formal changes are docs-only: the new `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_segment_integration_design_v0.1.md` plus SESSION/TODO bookkeeping and the prior ChatGPT runtime-owner closure persistence.

This review is based on the Codex request, the new v0.1 design, frozen v0.3.5 training semantics, migration integration v0.2, the closed runtime-owner contract, and the actual current trainer/runtime-owner source. No MM/Kimi/DS conclusion is used.

## Correct / closed portions

- Scope is narrow and correctly excludes real SegmentBatch producer/dataset/cache/checkpoint/model execution/GPU/training.
- The design keeps exact runtime-owner/forward/transaction authority, PAD exclusion, S0 `Local=None`, non-S0 visible Local, no synthetic zero Local, post-backward sidecar commit, disabled parity intent, and no cross-microbatch graph retention.
- The whitelist is explicit and does not reopen scheduler/core/model structure.
- The success chronology direction is consistent with v0.3.5: gather valid consumers -> one native consumer batch -> backward -> successful chronology commit -> detached sidecar commit.

These strengths do not yet make the bridge contract executable without additional design authority.

## Current blockers

1. **HIGH — bridge/native-consumer ABI and execution unit are not frozen enough to derive a unique implementation.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_segment_integration_design_v0.1.md:24-39,50-56`
   - frozen upstream: `docs/build/PSM-WMA_Local_Memory_detailed_design_addendum_v0.3.5.md` §§6-10,18
   - current trainer seam: `cosmos_framework/trainer/__init__.py:550-607`

   v0.1 says the native seam accepts parallel `payloads` and `locals`, then calls `_run_local_memory_segment_backward`, but it never freezes a concrete bridge callable/signature or the native seam return ABI needed to supply that trainer function's required `primary_consumer_mean`, `auxiliary_loss`, `actual_n_valid`, and exact `member_index`.

   It also does not freeze whether one bridge invocation represents one GA member or an entire `GAWindowPlan`. The declared input contains one `SegmentBatch` and one candidate `SegmentIdentity`, while the text starts with `owner.admit -> owner.begin` and ends with `owner.admit_next or owner.finish_window`. For a multi-member plan, a later member must preserve the same open transaction and must not run `owner.begin()` again; the current document does not define that first-member/continuation split or how the next member obtains its own SegmentBatch/identity.

   There is additionally a call-cardinality ambiguity: §3 says the tuple-valued native seam is called "exactly once", while acceptance §5.1 says two valid consumers are "各一次 native seam". Frozen v0.3.5 requires gather-valid-consumers followed by **one Cosmos/native batch forward** for the microbatch, not one model forward per consumer.

   **Acceptance:** freeze one exact public bridge API and one exact execution unit. A compatible minimal contract is a per-member bridge call with explicit first-member vs continuation preconditions, deriving `member_index = len(transaction.completed_members)` from the exact transaction and forbidding a second `begin()` for later members. Freeze a single batched synthetic native callback, e.g. one call on `(forward.payloads, forward.locals)` per member, and define its exact return/result ABI. State exactly how `primary_consumer_mean`, `auxiliary_loss`, `actual_n_valid = len(forward.payloads)`, and planned-vs-actual validation are produced before the trainer seam. Rewrite the two-consumer acceptance to prove **one batch seam invocation containing exactly two valid entries and zero PAD entries** (unless an alternative cardinality is explicitly chosen and reconciled with v0.3.5). Also freeze how feature-disabled execution selects the no-Local path without reconstructing owner/plan authority.

2. **HIGH — failure/disposition ownership conflicts with the current trainer and runtime-owner APIs and can cause duplicate transaction mutation or an uncleaned pending capability.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_segment_integration_design_v0.1.md:39,54`
   - trainer: `cosmos_framework/trainer/__init__.py:550-607`
   - runtime owner: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py:119-157`

   v0.1 states that `_run_local_memory_segment_backward` is the unique transaction/scaling authority, but then says any seam/backward exception must call `owner.abort_terminal` or the transient taxonomy. The current trainer seam already mutates the transaction on failure: `failure_kind` can call `transaction.recover_transient()` or `transaction.terminal_failure()`, GradScaler skip calls `transaction.grad_scaler_skip()`, and objective/validate/backward exceptions call `transaction.terminal_failure()` before raising. The current owner abort methods also perform the transaction disposition before exact pending discard (`abort_terminal` calls `terminal_failure`; `abort_retry` calls `recover_transient`).

   Therefore a bridge that catches a trainer failure and then invokes owner abort can double-dispose the transaction. The retry case is worse: after trainer `recover_transient()` closes the attempt-0 transaction, `owner.abort_retry()` tries to recover it a second time and fails before exact pending discard, leaving owner/pending state unresolved. The current whitelist does not include runtime-owner modification, so this cannot be safely repaired by implementation guesswork.

   **Acceptance:** freeze exactly one failure-mutation owner and an executable cleanup path. Two acceptable directions are: (a) define a new whitelisted trainer bridge seam that performs objective/validation/backward but leaves terminal/retry/scaler disposition to the runtime owner exactly once; or (b) keep the existing trainer disposition semantics and explicitly expand the runtime-owner whitelist/API with a post-failure finalizer that performs only exact pending discard + owner phase/handle transition, never a second transaction disposition. In either case freeze the classification of native-seam failure vs transient vs terminal, and require CPU/static Evidence that every failure path performs exactly one transaction disposition, exactly one exact pending discard, zero sidecar commit, no stale forward reuse, and leaves retry/terminal owner state executable/fail-closed as appropriate.

## Scope boundary

No implementation authority is granted for this pair. This remains docs-only. No child code, real packer/dataset/cache/checkpoint I/O, production model execution, config/default/registry change, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`
