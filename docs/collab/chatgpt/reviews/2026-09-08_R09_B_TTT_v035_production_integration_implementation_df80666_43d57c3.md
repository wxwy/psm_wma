# ChatGPT independent review — R09-B TTT production integration CPU/static closure

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC`
- Formal root implementation SHA: `df80666ed31232f461197e2679b8152f4113f6cb`
- Formal child/Gitlink SHA: `43d57c327dc28bda05e143470966d3abec8fe614`
- Request/bookkeeping SHA observed: `9fa7e9b6490983393ccd8bce94d1b75a731f8d33`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior pair `764eb09da87dddae265f4476c0237ca00b05cd52 / 6c5251b9f07901bf0161838fb7d17e895c0ce37d`. Repository truth confirms root `df80666` pins child `43d57c3`. The child compare from `6c5251b` to `43d57c3` changes only `cosmos_framework/model/generator/mot/local_memory_segment.py`, `cosmos_framework/trainer/__init__.py`, and `cosmos_framework/trainer/trainer_local_memory_integration_test.py`; no registry/default/config, model-forward, real I/O, CUDA/GPU/torchrun, training/evaluation/inference wiring was introduced.

The remediation materially improves the prior transaction seam: exact member/count validation is moved before backward, successful backward commits through `LocalMemoryTransaction`, transient attempt0 can create a suffix plan, terminal codes/suppression are recorded, and GradScaler skip is represented. However the formal Gate still cannot close.

## Blocking findings

1. **HIGH — implementation violates the exact v0.3 symbol whitelist.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.3.md:7-17` freezes `cosmos_framework/model/generator/mot/local_memory_segment.py` to changes only in `SegmentBatch`, `RankLocalSegmentScheduler`, and `GAWindowPlan`, with all other symbols behaviorally unchanged. The current child modifies `LocalMemoryTransactionSnapshot` / `LocalMemoryTransaction` in `cosmos_framework/model/generator/mot/local_memory_segment.py:163-248` by adding terminal/suppression/recovery state and new methods. Those symbols were not authorized by the approved design literal.

   **Acceptance:** either (a) revert all `LocalMemoryTransaction*` changes and implement the required transaction behavior strictly inside already-authorized symbols/seams, or (b) first create and obtain approval for a new docs-only design formal pair that explicitly adds the exact `LocalMemoryTransaction*` symbols and permitted changes to the whitelist. Do not treat file-level inclusion as symbol-level authorization.

2. **HIGH — suppression/recovery/scaler state is recorded but not fail-closed authority.** `cosmos_framework/model/generator/mot/local_memory_segment.py:190-239` sets `remaining_members_suppressed`, `suffix_recovery`, and `slow_grads_cleared`, but `validate_success()` / `successful_backward()` do not reject a transaction after terminal failure or after suffix recovery has been created. The original transaction can therefore be reused to execute/commit the supposedly suppressed suffix. Likewise `slow_optimizer_step_succeeded()` has no guard for terminal failure or GradScaler-skip state and can still increment slow optimizer/LR counters. Existing lower-level fixture `local_memory_segment_test.py:153-176` explicitly calls `slow_optimizer_step_succeeded()` after `grad_scaler_skip()` and expects the counters to advance, which contradicts the frozen "no slow optimizer/LR step" transaction boundary.

   **Acceptance:** make terminal/recovery/scaler dispositions authoritative and irreversible for the affected transaction: after terminal failure, no further member may validate/backward/commit and no slow optimizer/LR step may succeed; after attempt0 suffix recovery is created, the original plan must not continue and only the immutable attempt1 suffix authority may execute; after GradScaler skip, prior committed fast chronology must remain, slow grads must be cleared, and the transaction must prohibit slow optimizer/LR advancement. Add negative fixtures proving these forbidden calls fail closed.

3. **MEDIUM — mandatory seam-level Evidence is still incomplete.** `cosmos_framework/trainer/trainer_local_memory_integration_test.py:1-139` now covers success, identity/planned mismatch, transient-plan creation, taxonomy flags, and a fresh-transaction scaler skip. It does not exercise an actual non-finite objective or actual backward exception through the seam, does not prove scaler skip after an already committed fast member retains that chronology, and does not execute the stored attempt1 suffix as a real retry to prove recovery `GA_effective` / primary+aux scaling. The reported aggregate `42 passed` therefore does not yet establish the full `contract -> behavior -> evidence` mapping required by the approved v0.2/v0.3 acceptance.

   **Acceptance:** add adjacent CPU/static seam-level fixtures that (i) trigger the real numerical path via non-finite native loss, (ii) trigger an actual backward exception, (iii) commit at least one fast member before scaler skip and prove retention + no slow optimizer/LR step, and (iv) execute the immutable attempt1 suffix with unequal valid counts + nonzero aux and prove recovery scaling/full-window equivalence/no second GA division.

## Boundary

This verdict does not authorize production-integration closure, production wiring, registry/default/config changes, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.