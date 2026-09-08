# ChatGPT independent review — R09-B TTT production integration CPU/static v0.4 implementation

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC-V04-IMPLEMENTATION`
- Formal root implementation SHA: `43913155b8d0dc67b3d0fceade6b300def7224bc`
- Formal child/Gitlink SHA: `c9f5f56a4276dde7ed4f7cd53e17fc0d951673c0`
- Request/bookkeeping SHA observed: `1693d3a886011b2b57543ba8a542326744671e8f`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to approved v0.4 design pair `6c1bfb5b6af5de37f3ecf81a6482e8c403726b31 / 43d57c327dc28bda05e143470966d3abec8fe614`. Root `43913155` changes only the child Gitlink. The child implementation touches only v0.4-authorized surfaces: `cosmos_framework/model/generator/mot/local_memory_segment.py` (`LocalMemoryTransaction` guard state), adjacent `local_memory_segment_test.py`, and existing/modified `trainer_local_memory_integration_test.py`. No production wiring, registry/default/config, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference wiring is introduced.

The remediation correctly adds a transaction `_closed` guard, makes `validate_success()` and `slow_optimizer_step_succeeded()` reject closed transactions, closes the original transaction after terminal failure / suffix recovery / GradScaler skip, and adds a real NaN numerical-path seam test. These are valid improvements, but the exact v0.4 contract is not fully closed.

## Blocking findings

1. **HIGH — transient recovery is still not single-authority / exactly-once fail-closed.** `cosmos_framework/model/generator/mot/local_memory_segment.py:218-234` closes the transaction only *after* `recover_transient()` calls `fail_transient()`, but neither `fail_transient()` nor `recover_transient()` calls `_require_open()` before creating the suffix. Therefore the same already-closed attempt-0 transaction can call `recover_transient(failed_index)` again and obtain another attempt-1 `GAWindowPlan`. The trainer seam likewise handles `failure_kind="LOAD_DECODE_TRANSIENT"` before any open-state validation, so re-entering the same closed transaction can generate another suffix instead of failing closed. This violates v0.4 §2: attempt0 `LOAD_DECODE_TRANSIENT` may produce **exactly one immutable suffix**, after which the original transaction is permanently closed.

   **Acceptance:** make suffix creation itself authoritative and exactly-once. Before `fail_transient()` / `recover_transient()` creates or returns a suffix, require the original transaction to be open and to have no existing `suffix_recovery`; a second recovery attempt on the same transaction must fail closed without creating/replacing a plan. Add an adjacent negative seam/transaction fixture proving repeated attempt0 transient recovery on the same original transaction is rejected and the first suffix object/contents remain unchanged.

2. **MEDIUM — tests/Evidence-only — mandatory v0.4 seam matrix remains incomplete.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md:25-30` requires the unique trainer seam to prove: actual non-finite numerical routing, an actual `loss.backward()` exception to OUTER, GradScaler skip after at least one fast commit with chronology retention/no slow step, and actual execution of the immutable attempt1 suffix with unequal valid counts, nonzero aux, recovery `GA_effective`, full-window equivalence and no second GA scaling, plus negative fail-closed calls after terminal/recovery/skip. Current `cosmos_framework/trainer/trainer_local_memory_integration_test.py:1-155` adds the NaN numerical case, but the function named `numerical_and_backward_failures` contains only that NaN tuple; no actual backward exception is triggered. The scaler-skip seam fixture still starts with zero completed members, and the transient fixture only creates/stores the suffix—it never executes an independent attempt1 suffix transaction or proves recovery scaling. Negative coverage is also incomplete for `successful_backward()` and repeated recovery.

   **Acceptance:** add adjacent CPU/static seam fixtures that (a) use an autograd/backward path that actually raises during `loss.backward()` and assert `LOCAL_MEM_OUTER_FAILURE`; (b) commit at least one fast member through the seam before GradScaler skip and prove committed chronology is retained while slow optimizer/LR remains forbidden; (c) instantiate and execute the stored attempt1 suffix transaction with unequal valid counts + nonzero aux and prove recovery `GA_effective`, full-window equivalence and no second `/grad_accum_iter`; and (d) cover the remaining negative fail-closed calls required by v0.4. Production code need not change for this MEDIUM unless those fixtures reveal a semantic defect.

## Evidence assessment

Request Evidence reports `43 passed`, `py_compile` PASS and diff-check PASS. These results were read from the request and were not independently executed by this reviewer. They do not close the missing contract-to-behavior evidence above.

## Boundary

This verdict does not authorize v0.4 CPU/static closure, production wiring, registry/default/config changes, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
