# ChatGPT 独立 runtime-owner / sidecar design v0.8.1 review

Formal reviewed pair:
- root design SHA: `0792388fb1d6bc851d50897ceb4d202d4d4b38f5`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- request/bookkeeping HEAD observed at review start: `ba87f814ebe997f5783e9309fba6b6f5bcb76d55`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior formal design pair `b5f160f485097945516961336a41af696d28e487` / `5d16b84fe17a42f128065bf36361f6b1bb93a436`. Child is unchanged. Review is based only on the Codex request, v0.8.1 design, inherited v0.8/v0.6 contracts, and formal child source.

## Prior blocker status

**PARTIALLY CLOSED — normal multi-member GA transition is now representable.** v0.8.1 adds `MEMBER_READY -> PREPARED -> MEMBER_COMMITTED -> admit(next) -> MEMBER_READY` while preserving the same exact `LocalMemoryTransaction`, and `finish_window()` is restricted to the all-members-complete boundary. This closes the normal two-or-more-member half of the previous phase-machine blocker.

**OPEN — retry suffix remains unrealizable under the existing scheduler admission authority.** See blocker 2 below.

## Current blockers

1. **HIGH — `pending()` is frozen as a detached deep-copy, which destroys the exact pending capability identity inherited from v0.6/v0.8.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.1.md:12-20`; `cosmos_framework/model/generator/mot/production_segment_wiring.py:13-46`; `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:13-75`.

   v0.8.1 adds `pending() -> tuple[SegmentIdentity, LocalMemoryTransaction, SegmentScanResult] | None` and then states that **both** `pending()` and `committed_snapshot()` return a detached deep-copy/read-only view. That is valid for committed detached state, but invalid for the pending capability. The inherited contract requires the pending transaction and `SegmentScanResult` to remain the exact objects created by `CanonicalSegmentWiring.prepare()` / adapter `scan()`: trainer/owner identity guards depend on `pending[1] is transaction` and `pending[2] is forward.result`, while `SegmentScanResult` is graph-bearing until commit. Deep-copying or detaching the pending tuple therefore makes the owner unable to verify the exact capability and would sever/replace the graph-bearing result that v0.6 explicitly forbids reconstructing.

   **Acceptance:** split the two helper semantics. `pending()` must be a read-only exposure of the exact current tuple, preserving object identity of the transaction/result and graph-bearing tensors; it may not clone, detach, reconstruct, or mutate anything. `committed_snapshot()` may and should return detached deep-copies. Add adjacent CPU/static Evidence that `pending()[1] is exact_transaction`, `pending()[2] is exact_forward.result`, substitute/reconstructed objects fail, and reading `pending()` performs no mutation/clear/copy.

2. **HIGH — `begin_retry()` attempts to re-admit the failed suffix identity even though the scheduler already consumed that exact admission in attempt-0.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.8.1.md:47-53`; `cosmos_framework/model/generator/mot/local_memory_segment.py:293-317`.

   The frozen attempt-0 path admits a member before `prepare()`. `RankLocalSegmentScheduler.admit()` immediately appends that identity to `admission_order` and sets `stable_slots[slot] = identity`. If that member then fails transiently, the attempt-1 suffix begins with the **same failed identity**. v0.8.1 says `begin_retry(retry_plan)` “admits its first suffix member”. Delegating admission again cannot succeed: `_is_admissible()` now sees that same identity as the slot's previous identity and requires the next admitted cursor to equal `previous.cursor + 1`, so re-admitting the same cursor is rejected. The approved whitelist also forbids changing scheduler source, so this cannot be repaired during implementation by altering scheduler semantics.

   **Acceptance:** freeze retry to **reuse the already-admitted failed identity without calling scheduler.admit again**. `begin_retry()` should consume the exact immutable suffix plan once, create the new attempt-1 `LocalMemoryTransaction` with the same scheduler, verify that suffix member 0 equals the exact failed/admitted identity already present in scheduler admission authority, bind that identity into owner state, and enter `MEMBER_READY`. Later suffix members may use the normal `admit(next)` transition after the retried member commits. Add CPU/static Evidence that scheduler admission count/order does not gain a duplicate failed identity, attempt-1 scan reads the previous committed sidecar frontier correctly, and old attempt-0 transaction/forward/result remain permanently non-authoritative.

## Scope boundary

No runtime-owner CPU/static implementation authority is granted for this pair. This remains docs-only. No production model/trainer/packer wiring, persistent sidecar/checkpoint I/O, config/default/registry changes, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1 is authorized.
