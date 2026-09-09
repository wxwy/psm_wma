# ChatGPT 独立 Production Active Wiring Design v0.2 review

Formal reviewed pair:
- root design SHA: `440082a245a0a7ab21df20d1bded8813c0ccc35e`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- previous formal pair: `305b791ac6cc4f6cf3a5ebb578fa3a332a6688fb` / `78b8c9cd1389ff523b703d578208f7a221a64af2`
- request/bookkeeping commit: `2c7dfe1093d0b37a0664160b2ea637f0d9a6b062`
- latest bookkeeping HEAD observed during review: `24f6dfa073948d60c178a162ca759827814007ce`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.2.md`

Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only remediation review relative to v0.1. Child is unchanged. v0.2 correctly supersedes the v0.1 callback, split-phase and trainer-clock text, but the real GA/retry clock is still not closed and the optimizer-boundary capability check is ordered after an irreversible optimizer mutation. A smaller production-marker/native-seam ABI ambiguity also remains.

## Prior blocker status

1. **CLOSED — batched native-forward cardinality.** v0.2 now freezes exactly one native model invocation per Local-enabled GA member/microbatch over the complete ordered `(payloads, locals)` tuples. Multiple valid consumers are entries in that single batched call; PAD is absent.

2. **CLOSED IN SUBSTANCE — model/trainer split-phase authority.** v0.2 introduces registry-owned `PreparedActiveMemberCapability` and `ActiveForwardCapability`, freezes object-identity checks and one-shot consumption, separates prepare/model-forward/trainer-completion, and requires the active model branch to occur before `_get_training_inputs()` so `_inject_local_history/_ttt_local_memory_tokens()` cannot create the legacy lifecycle.

3. **NOT CLOSED — real GA/GradScaler clock.** See HIGH blocker 1 below.

## Current blockers

1. **HIGH — transient retry produces a suffix transaction with a new GA denominator/window size, but v0.2 neither resets the trainer accumulation window nor the full optimizer gradient state.**
   - design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.2.md` §3.1 and §4
   - current owner: `cosmos_framework/model/generator/mot/canonical_segment_runtime.py::abort_retry/begin_retry`
   - current transaction: `cosmos_framework/model/generator/mot/local_memory_segment.py::GAWindowPlan.suffix_after_failure/objective`

   The current owner retry path calls `wiring.clear_local_slow_grads()` and replaces the original transaction with a new attempt-1 **suffix** transaction. `suffix_after_failure()` keeps only the remaining members/counts, so its `ga_effective` and `n_window` are the suffix values. v0.2, however, only states that a transient retry "does not advance" the trainer `grad_accum_iter`; it does not reset that counter and does not clear the non-Local/model gradients already accumulated by earlier successful members.

   After `k>0` successful members, this creates two incompatible clocks/normalizations: trainer `grad_accum_iter` still reflects the original window and non-Local gradients from those members remain live, while the retry transaction starts at member index 0 with a new suffix `ga_effective/n_window`. The v0.2 final-boundary check `grad_accum_iter + 1 == ga_effective` therefore does not in general coincide with the suffix transaction's real final member, and the optimizer gradient is a mixture of original-window and suffix-window weighting.

   **Acceptance:** freeze exactly one production retry policy that is mathematically executable. Safe compatible choices include either: (A) permit active-path transient retry only before any successful member (`completed_members==0` and trainer `grad_accum_iter==0`), with any later-member transient terminal/process-fatal; or (B) explicitly restart the slow optimizer window on retry by clearing **all** optimizer gradients, resetting trainer `grad_accum_iter=0`, and binding the suffix plan as the new native optimizer window while preserving already-committed fast-state chronology. If prior gradients are to be preserved instead, the design must retain the original window denominator/member clock rather than using the current suffix-plan semantics. CPU/static Evidence must include a transient after at least one successful member and prove exact counter, gradient, objective-denominator and optimizer-boundary behavior.

2. **HIGH — exact completed-capability/boundary validation is specified at consumption after `grad_scaler.step(optimizer)`, which can mutate model weights before a stale/substitute/boundary mismatch is rejected.**
   - design: v0.2 §4 optimizer-boundary sequence
   - current owner: `CanonicalSegmentRuntimeOwner.resolve_local_memory_slow_window()`
   - current trainer: `ImaginaireTrainer._optimizer_step()`

   v0.2 requires reconstructed/stale/double completed capabilities and counter/boundary mismatches to fail closed, but its frozen order is callbacks -> `grad_scaler.step(optimizer)` -> read found-inf -> consume/resolve the exact `CompletedWindowCapability`. On a non-skipped step, the optimizer has already irreversibly mutated slow/model weights before `resolve_local_memory_slow_window()` performs its exact object-identity/phase/transaction check. A bad or stale capability can therefore be discovered too late to satisfy zero-mutation fail-closed semantics.

   **Acceptance:** freeze a non-mutating exact preflight before any irreversible optimizer-boundary mutation (preferably before optimizer callbacks and 반드시 before `grad_scaler.step`). The preflight must prove: exact owner-created unconsumed capability, owner `SLOW_RESOLUTION_PENDING`, exact transaction/registry chain, transaction still open, and exact trainer GA boundary/counter. After a successful optimizer step, no capability/identity/boundary validation may remain that can legitimately fail; only the actual scaler success/skip result and deterministic one-shot resolution should remain. CPU/static tests must prove stale/substitute/reconstructed/double capability and counter mismatch cause zero optimizer/scheduler/owner mutation.

3. **MEDIUM — the production marker/native model seam remains underspecified enough that implementation could satisfy CPU spies without proving it is wired to the ordinary MoT path.**
   - design: v0.2 §2, §3.2, §5-6
   - current model: `OmniMoTModel.training_step/_get_training_inputs/_inject_local_history`

   v0.2 refers to a "complete production marker", an `native_model_forward(payloads, locals)` pseudo-signature, and the "existing Memory Prefix ABI", but it does not freeze the actual marker schema/keys, the exact model method/signature that consumes the capability, or the output-batch field carrying the exact `ActiveForwardCapability` to trainer completion. Because the producer and real native numerical Gate are deferred, an implementation could otherwise expose a caller-supplied synthetic callback through the production marker and pass CPU/static tests without actually binding the active branch to the real MoT forward surface.

   **Acceptance:** freeze the production marker schema and exact model/trainer handoff API in the design: exact marker/capability fields, exact model method or branch signature, exact output field carrying the one-shot `ActiveForwardCapability`, and an explicit prohibition on caller-supplied model callbacks/functions in the production marker. Also state what minimum payload representation this CPU/static Gate treats as the native model input boundary. Synthetic spies may test control flow, but they must not become the production branch's runtime ABI.

## Scope boundary

No implementation authority is granted for this pair. It remains docs-only. No child production wiring/model/trainer implementation, packer/dataset/manifest/config/optimizer-selector/checkpoint change, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized.

Requested approval literal remains reserved for a corrected formal pair:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`
