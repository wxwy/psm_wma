# ChatGPT independent review — R09-B TTT v0.4 production integration CPU/static implementation

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC-V04-IMPLEMENTATION`
- Formal root implementation SHA: `64c4a7adf2b60f5c01e1f37f1dc19b10d82937cb`
- Formal child/Gitlink SHA: `81596f21b21b6eac74fb6d40e22f7ed5f34ff848`
- Request/bookkeeping SHA observed: `6122d8afc2cc6a26ed4b4e16119fad4ce89f3c09`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to prior formal pair `43913155b8d0dc67b3d0fceade6b300def7224bc / c9f5f56a4276dde7ed4f7cd53e17fc0d951673c0`. Repository truth confirms root `64c4a7a` pins child `81596f2`. Child compare is exactly one commit and changes only `cosmos_framework/model/generator/mot/local_memory_segment.py` and `cosmos_framework/trainer/trainer_local_memory_integration_test.py`, both within the approved v0.4 surface. No production wiring, registry/default/config, real I/O, CUDA/GPU/torchrun, training/eval/inference or LIBERO4IN1 wiring is introduced.

The remediation closes meaningful parts of the previous findings: `recover_transient()` now checks open-state and preserves the first stored suffix on a repeated recovery attempt; an actual backward hook exception is routed through the seam to `LOCAL_MEM_OUTER_FAILURE`; and an independent attempt-1 suffix transaction is now executed with unequal valid counts and nonzero auxiliary loss.

## Blocking findings

1. **HIGH — `cosmos_framework/model/generator/mot/local_memory_segment.py:222-240` — exactly-once suffix authority is still bypassable through public `fail_transient()`.** v0.4 freezes that `LOAD_DECODE_TRANSIENT` attempt-0 may create exactly one immutable suffix and that, once the suffix is created, the original transaction permanently loses member/optimizer authority. The new guards are sufficient for `recover_transient()`, but `fail_transient()` itself still calls `_require_open()`, creates and returns `self.plan.suffix_after_failure(...)`, and only sets `slow_grads_cleared`; it does **not** store that suffix in `self.suffix_recovery` and does **not** close the transaction. Therefore a caller can invoke `fail_transient()` repeatedly and obtain multiple attempt-1 plans, or call `successful_backward()` afterward because `_closed` remains false. The adjacent lower-level fixture `cosmos_framework/model/generator/mot/local_memory_segment_test.py:153-176` still directly uses `transaction.fail_transient(1)`, confirming this remains an exposed authority path rather than an unreachable private helper.

   **Acceptance:** make suffix creation have one authoritative path. Either make `fail_transient()` itself atomically store the first suffix and close the original transaction, or make it non-authoritative/private such that only guarded `recover_transient()` can create a suffix. After the first creation, every direct/indirect second suffix request and every original-transaction `validate_success()` / `successful_backward()` / slow optimizer step must fail closed, while the first suffix object/value remains unchanged. Add a negative fixture exercising the actual formerly-bypassable `fail_transient()` path.

2. **MEDIUM — tests/Evidence-only — `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md:25-31`; `cosmos_framework/trainer/trainer_local_memory_integration_test.py:150-181`.** The mandatory seam matrix is improved but still not sufficient for closure. The actual backward exception is now covered. However the new retry/scaler fixture only asserts that a retry loss equals `7.0`, `GA_effective==1`, and that a later scaler-skip call raises. It does not assert post-skip preservation of the already committed fast chronology/exposure, `slow_grads_cleared`, zero slow optimizer/LR steps, or rejection of a subsequent slow step through this seam scenario. It also does not establish the required recovery full-window/no-second-GA-scaling invariant: because the tested retry has `GA_effective==1`, an erroneous extra division by GA is observationally identical, and no explicit full-window-equivalence assertion is made.

   **Acceptance:** extend adjacent CPU/static tests, without widening production code unless a real defect is exposed, so the unique trainer seam proves: (a) after at least one successful fast commit, GradScaler skip preserves completed fast chronology/exposure, clears slow grads, leaves slow optimizer/LR at zero, and a later slow step fails closed; (b) an actually executed attempt-1 recovery with `GA_effective>1` (or an equivalent construction that would detect duplicate GA scaling) uses unequal valid counts + nonzero auxiliary loss and explicitly proves the frozen recovery objective/full-window equivalence and no second GA division. Keep the newly added real backward-exception and exactly-once recovery tests.

## Evidence status and boundary

Request Evidence reports `44 passed`, `py_compile` PASS and diff-check PASS. These execution results were read from the request and not independently rerun by this reviewer. Pass count does not override the two contract/evidence gaps above.

This verdict does not authorize v0.4 CPU/static closure, production wiring, registry/default/config changes, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
