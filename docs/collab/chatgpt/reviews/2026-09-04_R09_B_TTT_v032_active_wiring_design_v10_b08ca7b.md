# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.10

## Verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`

## Formal target

- root/design SHA: `b08ca7b3c2d82e6eb8df427038d28985d09cadd9`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `140cca99bc2d95601d5a17cd8f273ae408b0911e`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.10_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v09_36ee7cf.md`

This is a fresh review of the new v0.10 formal pair. The request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.9 HIGH-1 (external-backward success predicate did not enforce the inherited non-finite-loss abort contract): **CLOSED**.
- v0.8 HIGH-1 (no legal single-backward seam to move authority to `BACKWARD_OK`): remains **CLOSED** under v0.9/v0.10 authority-owned `mark_external_backward` lifecycle.
- v0.7 terminal-lag and skip-retry blockers remain **CLOSED structurally** under Option B single-stage fast commit.

## Review finding

v0.10 now freezes two independent authority-owned conditions before `BACKWARD_OK`:

1. the exact unscaled native loss for the armed closing micro-batch must be finite (`torch.isfinite(...).all()`), with NaN/+Inf/-Inf fail-closed before `BACKWARD_OK`/commit; and
2. `witness_leaf.grad is not None` must prove that the trainer's sole backward actually traversed the materialized witness graph.

The lifecycle obtains the native loss from the existing `on_before_backward(model, loss, iteration)` seam, passes that exact tensor into `mark_external_backward(owner, loss=...)` after the trainer's one backward, and keeps the phase transition inside the unique ProductionRuntimeAuthority. The existing `commit()` `BACKWARD_OK` gate is unchanged. This directly closes the previous defect without adding a second backward or a private phase owner.

The design also preserves the accepted distinction between an invalid closing backward and a later GradScaler skip: a finite, successfully traversed closing backward may publish fast state under Option B even if the later optimizer step is skipped; scheduler suppression and Local `.grad` cleanup remain separate slow-side behavior.

The acceptance matrix is sufficient for this design Gate: finite success, NaN, +Inf/-Inf, later scaler skip, thrown backward, and finite-loss/no-witness negative cases are all explicitly required through the real trainer/authority order.

## Non-blocking note

The prose statement that finite unscaled loss and finite scaled loss are "equivalent" is not strictly true under finite-precision arithmetic because multiplication by a finite scale can overflow. This does **not** block approval because the contract explicitly chooses the **unscaled native loss** as the authority finite predicate and separately assigns scaled-gradient overflow to the later GradScaler-skip semantics. Implementation/tests should follow that explicit source-of-truth and not infer equivalence to the scaled tensor.

## Scope of approval

This approval authorizes only the next CPU/static implementation Gate for the frozen v0.10 active-wiring design and its allowed files/seams, including the minimal authority-owned `mark_external_backward` transition and the frozen trainer callback/abort/skip seams.

It does **not** authorize real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T, LIBERO4IN1, or inference wiring. Any implementation SHA/Gitlink change requires a fresh independent implementation review.
