# ChatGPT independent review — R09-B TTT production integration v0.4 docs-only design

- Gate: `G0-R09-B-TTT-V035-PRODUCTION-INTEGRATION-CPU-STATIC-V04-DESIGN`
- Formal root design SHA: `70ae8d1913dd8535c2927fd99d900a62faaf74de`
- Formal child/Gitlink SHA: `43d57c327dc28bda05e143470966d3abec8fe614`
- Request/bookkeeping SHA observed: `4583d4670c8c9f84a37e563ee31a0be433ac1333`
- Verdict: `REQUEST_CHANGES`

## Incremental scope

Fresh docs-only review relative to the prior implementation closure pair `df80666ed31232f461197e2679b8152f4113f6cb / 43d57c327dc28bda05e143470966d3abec8fe614`. Root `70ae8d1` changes only `SESSION.md`, `TODO.md`, and new `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md`; the child/Gitlink is unchanged. No child implementation, production wiring, real I/O, CUDA/GPU/torchrun, training/evaluation/inference is authorized by this request.

## Prior blocker status at design level

- CLOSED in design — prior HIGH symbol-whitelist gap: v0.4 explicitly adds `LocalMemoryTransactionSnapshot` and `LocalMemoryTransaction` to the exact allowed symbols and limits them to irreversible transaction guards/state.
- CLOSED in design — prior HIGH fail-closed authority gap: v0.4 requires `validate_success()`, `successful_backward()`, and `slow_optimizer_step_succeeded()` to reject terminal/original-plan-recovery/GradScaler-skip states; freezes original-plan suffix invalidation and independent attempt-1 authority; and requires terminal/scaler skip to prohibit slow optimizer/LR.
- CLOSED in design — prior MEDIUM Evidence gap: v0.4 requires seam-level numerical/backward-exception paths, post-fast-commit scaler-skip retention, executed attempt-1 recovery with `GA_effective`/primary+aux invariants, and negative fail-closed fixtures.

## Blocking finding

1. **MEDIUM — the v0.4 exact whitelist still mislabels an existing test file as `new`.** `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_integration_implementation_design_v0.4.md:16` marks `cosmos_framework/trainer/trainer_local_memory_integration_test.py` as `new`, but repository truth at the formal child `43d57c327dc28bda05e143470966d3abec8fe614` shows that file already exists. Since this design is supposed to authorize the next implementation from the current child baseline, the status must be `existing/modified`; otherwise the exact edit surface is internally inconsistent and recreates the same existing/new ambiguity previously rejected in v0.2.

   **Acceptance:** change only the v0.4 design/bookkeeping as needed so `cosmos_framework/trainer/trainer_local_memory_integration_test.py` is frozen as `existing/modified` relative to child `43d57c3`; preserve the current exact symbol whitelist, irreversible transaction contract, mandatory Evidence matrix, approval literal, and prohibition boundary unchanged. No child code change is needed for this remediation.

## Boundary

The v0.4 technical direction is otherwise sufficient for the requested fail-closed transaction CPU/static remediation. This verdict is docs-only and does not authorize child implementation, production wiring, registry/default/config changes, real checkpoint/data/cache I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1. A new formal root is required after correcting the whitelist status, and that new pair requires fresh review.
