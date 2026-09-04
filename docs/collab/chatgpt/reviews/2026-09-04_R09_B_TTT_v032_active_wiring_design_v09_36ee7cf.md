# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.9

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `36ee7cfdc3edfed94ff82db643c029c75a44112a`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `6d4595b0e3b0783cab9dcbe2d38c524b2b03c086`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.9_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v08_778272d.md`

This is a fresh review of the new v0.9 formal pair. The V2 request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.8 HIGH-1 (no legal single-backward seam to move authority to `BACKWARD_OK` before commit): **CLOSED**. v0.9 now freezes an authority-owned `mark_external_backward(owner)` transition after the trainer's existing single backward, expands the real implementation scope to `runtime_authority.py` and the trainer backward exception seam, and keeps private phase mutation forbidden.
- v0.7 terminal-lag / skip-retry blockers remain **CLOSED structurally** under v0.8 Option B single-phase fast commit.
- the accepted single-stage fast publication semantics, pre-write witness, single-pending authority, scaler-skip scheduler rule, Local `.grad` cleanup, disabled parity, config/owner/selector/checkpoint boundaries remain accepted.

## Blocking finding

### HIGH-1 — external-backward success predicate does not enforce the inherited non-finite-loss abort contract

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.9_2026-09-04.md:8-17`; inherited `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.8_2026-09-04.md` §1 backward-failure rule; `cosmos_framework/trainer/__init__.py:488-506` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.9 defines successful external backward as `phase == MATERIALIZED_PENDING` plus `witness_leaf.grad is not None`, then immediately transitions to `BACKWARD_OK` and commits. That is sufficient to prove that some backward traversal reached the materialized witness leaf, and it closes the duplicate-backward problem from v0.8.

However, v0.9 inherits v0.8's explicit rule that a **non-finite loss is a backward-path failure that must abort before commit**. The actual trainer has no finite-loss check around the backward call: it scales `loss`, calls `loss_scaled.backward()`, then continues to post-backward hooks. PyTorch autograd normally does not raise merely because the loss or resulting gradients are NaN/Inf. Therefore a closing micro-batch with non-finite loss can still populate `witness_leaf.grad` (including a zero or non-finite tensor), causing `mark_external_backward()` to mark `BACKWARD_OK` and publish fast state even though the inherited contract requires abort.

This is not the later `SCALER_SKIP` case. Option B intentionally allows a **finite, successful closing backward** to commit fast state even if the later optimizer step is skipped. The unresolved case is the earlier predicate that decides whether the closing backward itself is contract-valid.

**Frozen-contract violation:** v0.8/v0.9 single-stage commit semantics as inherited by v0.9; explicit v0.8 non-finite-loss abort rule; v0.9 §1 definition of `mark_external_backward` success.

**Acceptance:** freeze one production-real finite-backward predicate before implementation approval. At minimum, for an armed closing transaction the real trainer/lifecycle path must fail closed before `BACKWARD_OK` when the native loss (or the exact scaled loss used for the one backward, as explicitly chosen by the design) is non-finite. The predicate must remain distinct from later GradScaler `SCALER_SKIP`. CPU/static trainer-authority fixtures must prove:

1. finite closing loss + successful single backward -> witness observed -> `BACKWARD_OK` -> exactly one commit;
2. NaN loss -> abort, no `BACKWARD_OK`, no commit, committed snapshot unchanged;
3. +Inf/-Inf loss -> same fail-closed behavior;
4. ordinary finite backward followed by GradScaler skip -> fast commit remains valid, Local slow `.grad` cleanup and scheduler suppression follow the already-frozen Option B semantics;
5. backward exception -> abort then original exception re-raised.

The finite check may live in the trainer backward seam or in an authority/lifecycle-owned pre-mark token, but the exact source value and ordering must be frozen; `witness_leaf.grad is not None` alone is not sufficient evidence of a contract-valid backward.

## Accepted / unchanged

- the v0.9 external-backward arm/observe/mark direction is the correct closure of the v0.8 blocker;
- adding a minimal authority-owned public mark transition is acceptable and does not by itself reopen the C5A commit grammar because `commit()` still requires `BACKWARD_OK`;
- the single backward count and backward-exception abort routing are correctly placed on the real trainer seam;
- no implementation/GPU/training authorization is granted by this verdict.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`.

Still prohibited: active wiring implementation, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires fresh same-pair independent review.
