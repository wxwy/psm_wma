# ChatGPT independent review — R09-B TTT v0.4 production integration CPU/static remediation

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC-V04-IMPLEMENTATION`
- Formal root implementation SHA: `3a95ba26931dba94574e27055ac48c1cfd3684a1`
- Formal child/Gitlink SHA: `b4b369d75259579f1c2e4d2b13f4e3ead91b73d2`
- Request/bookkeeping SHA observed: `6cf9ac74b661d12cde383539f2f34c26c879bdff`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh incremental review relative to `64c4a7adf2b60f5c01e1f37f1dc19b10d82937cb / 81596f21b21b6eac74fb6d40e22f7ed5f34ff848`. Repository truth confirms formal root `3a95ba2` pins child `b4b369d`. The child delta is one commit and touches only `cosmos_framework/model/generator/mot/local_memory_segment.py` and `cosmos_framework/trainer/trainer_local_memory_integration_test.py`, both within the approved v0.4 CPU/static surface. No production wiring, registry/default/config, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 authority is introduced.

## Prior blocker status

**CLOSED — prior HIGH exactly-once suffix authority blocker.** `cosmos_framework/model/generator/mot/local_memory_segment.py:221-240` now makes public `fail_transient()` itself authoritative: it checks open state and existing recovery, writes `self.suffix_recovery`, closes the original transaction, and returns that stored suffix. `recover_transient()` delegates to that same path. Because `validate_success()` / `successful_backward()` and slow optimizer/LR progression are guarded by `_require_open()`, the original transaction can no longer continue after suffix creation.

The prior MEDIUM Evidence gap is materially reduced: the seam-level retry fixture now asserts fast exposure retention, `slow_grads_cleared`, zero slow optimizer/LR steps and later slow-step rejection after a GradScaler skip; the previous real backward-exception route remains covered.

## Current blocker

1. **MEDIUM — tests/Evidence-only — `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md:30`; `cosmos_framework/trainer/trainer_local_memory_integration_test.py:165-189`.** The frozen v0.4 Evidence contract explicitly requires adjacent fixtures to prove through the **unique trainer seam** an actually executed immutable attempt-1 suffix with unequal valid counts, nonzero auxiliary loss, recovery `GA_effective`, full-window equivalence and no second GA scaling. The current seam-level retry fixture at lines 165-182 does execute a real attempt-1 suffix, but that suffix has only one remaining member (`GA_effective==1`), so it cannot detect an erroneous extra GA division. The new `test_local_memory_segment_recovery_objective_has_one_ga_division()` at lines 185-189 uses `GA_effective==2`, unequal counts and nonzero aux, but calls `GAWindowPlan.objective()` directly; it does not pass through `ImaginaireTrainer._run_local_memory_segment_backward`, is not an actually derived suffix transaction, and therefore cannot detect a second scaling introduced at the adapter/trainer seam. It also does not explicitly establish the required recovery/full-window equivalence through the authoritative seam.

   **Acceptance:** tests/Evidence-only remediation is sufficient. Construct an original GA plan whose transient failure leaves an attempt-1 suffix with at least two members, then execute every suffix member through `ImaginaireTrainer._run_local_memory_segment_backward` with unequal valid counts and nonzero auxiliary losses. Assert the aggregate seam objective/gradients equal the frozen recovery formula/full-window expectation and would fail under a second GA division. Preserve the existing skip-after-fast and real backward-exception fixtures. Also add a direct negative assertion that the original recovered transaction cannot `successful_backward()` again (or equivalent seam-level member continuation), completing the recovery fail-closed witness required by v0.4. Production code should remain unchanged unless the new fixture exposes a real semantic violation.

## Evidence status and boundary

Request Evidence reports `45 passed`, `py_compile` PASS and diff-check PASS. These execution results were read from the request and were not independently rerun by this reviewer. The pass count does not substitute for the explicit seam-level acceptance above.

This verdict does not close the v0.4 CPU/static Gate and does not authorize production wiring, registry/default/config changes, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. Review/Inbox bookkeeping does not change the formal pair.
