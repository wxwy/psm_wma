# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.3

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `73cf4a176733243d6d81ccc3ce63d28c5a5222bf`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `4396395f0e99845dc962838ea73540c71dd4b95d`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.3_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v02_6b1af60.md`

This is a fresh review of the new v0.3 formal pair. The V2 bookkeeping/request HEAD is not the formal target.

## Prior blocker status

- v0.2 HIGH-1 (closing witness post-write vs read-before-own-write causality): **CLOSED**. v0.3 now freezes a differentiable pre-write token `read(S_{t-1})` and computes the final candidate separately, while preserving the historical post-write CPU API semantics. The required `T>=17`/terminal fixtures directly target self-evidence leakage, stale read, double write and candidate/reference equality.
- v0.2 HIGH-2 (publication before optimizer success): **PARTIALLY CLOSED**. Publication is now deferred until after `_optimizer_step`, removing the original commit-before-step contradiction, but the new lag/failure policy is not yet executable against the frozen single-pending authority and current trainer failure seam.
- v0.2 additional gradient-objective concern: **CLOSED**. v0.3 explicitly supersedes Local slow-parameter segmented-vs-unsliced gradient parity while retaining native scalar/native-gradient semantics and adds a direct Local gradient reference target.

## Blocking findings

### HIGH-1 — publication-lag windows require a second same-owner segment, but the inherited authority permits only one pending transaction and no rebase rule is frozen

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.3_2026-09-04.md:30`; `cosmos_framework/model/generator/mot/runtime_authority.py:105,110-113,115-138` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.3 explicitly freezes that after a closing window reaches `BACKWARD_OK`, any micro-batches before the grad-accum optimizer boundary "belong to the next segment" and read the last committed state. It simultaneously retains transaction-local detached candidate reads for an open segment.

The inherited production authority cannot represent that state. It has exactly one `_pending_by_owner`; `begin(owner)` rejects whenever any pending transaction exists, and after materialize/backward the existing pending remains non-`COLLECT_RAW` until commit. Therefore a same-owner next-segment window cannot be admitted while the prior closing segment waits for optimizer publication. If implementation instead adds a second pending transaction, v0.3 does not freeze what state that second segment is based on or how rows already collected before publication are rebased once the older candidate commits. Building the second candidate from the last committed state would omit the older segment's writes; silently rebasing later would change the already-consumed read chronology unless explicitly defined and evidenced.

**Frozen-contract violation:** v0.3 §2 publication-lag visibility rule plus inherited single-owner contiguous segment/authority semantics. The design currently promises both a next open segment during lag and a single pending authority without defining a valid ownership/rebase state machine.

**Acceptance:** freeze one coherent same-owner policy for every supported `ttt_tbptt_steps` / `grad_accum_iter` alignment. It must either prevent any same-owner next-segment admission before publication through an explicit validated alignment invariant, or define the exact queued/multi-transaction base-state and rebase/replay semantics. Add CPU/static chronology fixtures with a deliberately misaligned segment/grad-accum pair (not only a divisor case) proving: no admission failure, no lost prior-segment write, owner-global contiguous timestep, read-after-(t-1) causality before/after publication, and no numerical double application.

### HIGH-2 — optimizer skip/exception is not an atomic success predicate at the actual trainer seam; thrown step has no abort hook and may already have mutated slow state

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.3_2026-09-04.md:24-32`; `cosmos_framework/trainer/__init__.py:500-527` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.3 freezes `optimizer step success -> on_before_zero_grad commit`, while a GradScaler skip or optimizer exception must abort the unpublished candidate and leave fast/slow sides with no progress.

The actual trainer calls `_optimizer_step()` before `on_before_zero_grad()`. `_optimizer_step()` executes `grad_scaler.step(optimizer)`, `grad_scaler.update()`, and `scheduler.step()` and returns no success/skip result. If the optimizer path raises, `on_before_zero_grad` is never invoked, so the frozen callback-only lifecycle has no post-exception seam on which to execute the promised abort. More importantly, an optimizer exception can occur after partial optimizer/parameter mutation; simply aborting the fast candidate would not establish the stated "fast/slow simultaneously no progress" guarantee. On GradScaler skip, scheduler progression is also unconditional in the current trainer, while v0.3 does not say whether that counts as forbidden slow-side progress or how the callback proves the skip before deciding commit vs abort.

**Frozen-contract violation:** v0.3 §2 atomic publication/failure semantics and its explicit acceptance requirement for GradScaler skip + thrown optimizer step, combined with v0.1's inherited rule that active wiring uses existing callback seams without changing the trainer main loop path.

**Acceptance:** freeze an observable, production-real optimizer transaction result and exact failure policy before implementation approval. CPU/static trainer-spy evidence must drive the actual trainer order and prove: successful update publishes exactly once; GradScaler-skipped update never publishes and has the explicitly frozen scheduler behavior; thrown optimizer update cannot leave a candidate visible; and if the contract retains "slow side no progress", partial parameter/optimizer/scheduler mutation is either prevented/rolled back or the exception is redefined as process-fatal with a separately frozen recovery boundary. The allowed implementation scope must include whatever real seam is required to make that policy achievable; helper-only/test-side abort calls are not sufficient evidence.

## Accepted / unchanged

- v0.3 pre-write witness semantics closes the prior causal-witness mismatch;
- existing post-write CPU contract is not silently redefined;
- Local gradient-objective supersede is now explicit and separately reference-testable;
- disabled parity, config identity, unique owner/object identity, selector/checkpoint scope and default-off boundaries remain acceptable;
- no implementation/GPU/training authorization is granted by this verdict.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`.

Still prohibited: active wiring implementation, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires a fresh same-pair independent review.
