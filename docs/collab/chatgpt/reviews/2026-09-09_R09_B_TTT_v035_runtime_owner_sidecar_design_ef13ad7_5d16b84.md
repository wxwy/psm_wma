# ChatGPT 独立 Production Runtime Owner / Sidecar v0.7 设计审核

Formal reviewed pair:
- root design SHA: `ef13ad7adbf0b90d9d80023a0e566c5d9973f6c3`
- child/Gitlink SHA: `5d16b84fe17a42f128065bf36361f6b1bb93a436`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-WIRING-RUNTIME-SIDECAR-DESIGN`
- requested approve literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_RUNTIME_OWNER_CPU_STATIC`
- request/bookkeeping HEAD observed: `08dd6967c5f2e95261f479cbf1b83349b49b6ae6` (not the formal target)

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only design review relative to the closed production-wiring pair `593fa24d71887ea0213ff406d222957ba10285b5 / 5d16b84fe17a42f128065bf36361f6b1bb93a436`. The child is unchanged. The new formal authority is the v0.7 runtime-owner/sidecar design; current production wiring, adapter, transaction/scheduler and trainer seams were read only to verify that the proposed API can be implemented without creating a second authority or violating the inherited v0.6 contract.

## Current blockers

1. **HIGH — exact `CanonicalSegmentWiring` capability ownership is not implementable under the frozen owner ABI.**

   Files: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.7.md:38-76`; `cosmos_framework/model/generator/mot/production_segment_wiring.py:13-45`.

   v0.7 freezes `CanonicalSegmentRuntimeOwner` as holding only the rank-local scheduler, the exact adapter, and the current transaction, and its constructor is described as receiving scheduler + adapter. The same design then requires `prepare()` to call the existing **exact** `CanonicalSegmentWiring.prepare` while forbidding construction of a second wiring. Repository truth does not provide a free/static prepare function: `CanonicalSegmentWiring.__init__` requires `(adapter, local_slow_parameters)`, stores the exact slow-parameter owner, and `CanonicalSegmentForward` embeds the exact wiring object itself.

   Under the current v0.7 ABI, the runtime owner has neither an exact wiring object nor the exact `local_slow_parameters` needed to construct one. An implementation must therefore either reconstruct a wiring inside `prepare()` (violating the frozen exact-capability/no-second-wiring rule) or silently widen the constructor/state contract beyond the approved design.

   **Acceptance:** freeze one exact wiring authority. Prefer `CanonicalSegmentRuntimeOwner(scheduler, wiring)` with `wiring: CanonicalSegmentWiring`, derive/verify `wiring.adapter` as the exact adapter, and require every prepared capability to satisfy `forward.wiring is owner.wiring`. Alternatively, explicitly authorize exactly-once wiring construction at owner initialization and freeze the exact `local_slow_parameters` input/ownership. Per-call wiring reconstruction must remain forbidden. Update the exact whitelist/API and add identity fixtures accordingly.

2. **HIGH — `abort()` cannot clear the adapter's pending capability, so the failure path cannot reach the frozen safe snapshot state.**

   Files: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.7.md:73-104`; `cosmos_framework/model/generator/mot/local_memory_segment_adapter.py:49-84`.

   v0.7 freezes `abort()` as clearing the owner's open transaction handle and prohibiting later commit, while snapshot requires `open_transaction is None` **and** all pending scans cleared. Current adapter behavior is stricter: every successful `scan()` stores `_pending_scan = (identity, transaction, result)`, and the **only** path that clears `_pending_scan` is successful `commit()`. There is no pending-discard/abort API. The v0.7 whitelist permits only owner-required read-only/snapshot helper additions to `local_memory_segment_adapter.py`, so it does not currently authorize an exact mutation that can clear a failed/retried/scaler-skipped pending capability without writing sidecar state.

   Therefore `prepare -> terminal/retry/skip -> abort` leaves a stale pending capability behind. The owner handle may be empty, but the adapter is not at the frozen safe boundary; snapshot remains permanently rejected until a later scan overwrites the pending slot, which would itself weaken stale-capability authority.

   **Acceptance:** explicitly freeze and authorize an exact pending-discard helper (for example `discard_pending(identity, transaction, result)`), which clears only the same pending identity + transaction object + result object, never writes sidecar state, and fails closed on mismatch. `CanonicalSegmentRuntimeOwner.abort()` must invoke this exact cleanup after existing terminal/retry/scaler disposition. Add CPU/static witnesses for terminal failure, suffix recovery and GradScaler skip proving pending becomes `None`, prior committed sidecar state remains unchanged, stale capability still cannot commit, and a recovery suffix cannot start while the failed pending capability remains live.

3. **MEDIUM — snapshot boundary/committed-frontier authority is caller-asserted and does not exclude an admitted-but-uncommitted scheduler state.**

   Files: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_wiring_runtime_sidecar_implementation_design_v0.7.md:52-60,87-107`; `cosmos_framework/model/generator/mot/local_memory_segment.py:270-323`.

   v0.7 exposes `snapshot(boundary: RuntimeBoundary)` and freezes safe output boundaries as `AFTER_BACKWARD_COMMIT | TERMINAL_DISCARD`, but it does not freeze an owner-maintained current-boundary state or transition table that proves the caller-supplied enum matches reality. Existing scheduler semantics make this important: `admit()` immediately appends `admission_order` and advances `stable_slots`, while `committed_identities` and the sidecar record advance only after successful backward/commit. Thus `admit(identity)` followed by no `begin()` leaves `open_transaction=None` and no adapter pending scan, yet scheduler state can already be ahead of the sidecar's last committed identity. A caller-provided `AFTER_BACKWARD_COMMIT` value is not, by the current design, tied to an actual commit event.

   **Acceptance:** make the safe boundary owner-derived or owner-validated from an internal state machine, not trusted caller metadata. Freeze the transition that sets/clears the current boundary on admit/begin/prepare/commit/abort. At snapshot time, assert per-slot committed-frontier consistency: the sidecar identity must be the exact last committed identity for that slot, while any admitted-but-uncommitted identity must either be represented separately as queue/admission state or make snapshot illegal. Add a negative `admit -> snapshot(AFTER_BACKWARD_COMMIT)` witness and positive post-commit/terminal-discard consistency witnesses.

## Scope boundary

This verdict is design-only. It does not authorize creation/modification of child runtime-owner code, production packer/model/trainer integration, checkpoint persistence/restore, real data/cache I/O, config/default/registry/optimizer changes, CUDA/GPU/torchrun, training, evaluation, inference, P4/P5, B2-T or LIBERO4IN1. Any remediation produces a new root design SHA and requires fresh review against the same child/Gitlink unless the child also changes.
