# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.4

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `fba72beff6972dbbb0f474dd0ec24745ae0dc2c3`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `31e2989878bd65a1cb54406d8491cae3ac207fbf`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.4_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v03_73cf4a1.md`

This is a fresh review of the new v0.4 formal pair. The V2 request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.3 HIGH-1 (single pending authority cannot host the next same-owner segment during publication lag): **PARTIALLY CLOSED**. v0.4's external graph-free raw deferral queue removes the immediate second-pending/rebase contradiction on the ordinary success path and freezes the post-publication base state. However, the queue is not sufficient once deferred windows themselves cross a Local segment/terminal closure, and its failure-path replay is incomplete.
- v0.3 HIGH-2 (optimizer success/skip/exception not observable at the real trainer seam): **CLOSED at the transaction-observation layer**. v0.4 now allows the minimal trainer seam, freezes a three-state `resolve_transaction` result, makes scaler-skip suppress scheduler progress, and defines optimizer exception as process-fatal. The remaining scaler-skip problem below is no longer observability; it is preservation/replay of the failed Local transaction.
- pre-write witness semantics and the explicit Local slow-gradient supersede objective remain **CLOSED/accepted**.

## Blocking findings

### HIGH-1 — raw-only publication-lag deferral cannot preserve the frozen closing-window meta-gradient when the backlog itself closes a segment or terminal remainder

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.4_2026-09-04.md:10-15`; inherited `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.3_2026-09-04.md:36`; inherited episode closure `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.1_2026-09-04.md:20-22`.

v0.4 stores publication-lag windows only as graph-free raw evidence and lets their already-executed forward/backward use the last committed Local read. It then claims the scheme works for arbitrary `ttt_tbptt_steps`/`grad_accum_iter` alignment and drains the queued rows only after the older transaction publishes/aborts.

That is insufficient under the inherited gradient contract: every Local segment must receive its one slow-parameter meta-gradient through the **closing window's witness graph**. If the lag backlog reaches another full segment before the optimizer boundary (for example `ttt_tbptt_steps=3`, `grad_accum_iter=7` or larger), the logical closing window has already completed backward while no authority transaction/witness graph existed for those queued rows. Materializing those raw rows later cannot retroactively connect the witness graph to that already-consumed task loss. The same issue occurs when an episode terminal/remainder arrives during publication lag: the terminal window's task loss is already gone, yet the inherited contract requires terminal remainder materialize/backward/closure before reset.

The queue drain is also underspecified when backlog length is `>= segment_steps`: a single authority pending may not legally absorb multiple complete segments, while splitting it later still cannot recover the original closing-window loss graphs. The proposed acceptance matrix (`segment=3 × grad_accum=2/4/5`, `16×16`) avoids the failing `lag >= segment_steps` case despite the prose claiming arbitrary alignment.

**Frozen-contract violation:** v0.4 §1 arbitrary-alignment claim + inherited v0.3 Local slow-gradient objective + inherited terminal remainder/episode closure semantics.

**Acceptance:** freeze one executable policy that preserves the exact Local gradient/closure semantics for publication-lag windows. It must explicitly cover (a) backlog crossing one or more full Local segments and (b) terminal remainder arriving while an older transaction is unpublished. Either guarantee through a fail-closed validated scheduling/barrier invariant that such a close cannot occur, or retain/replay enough native window/loss state to execute the required closing witness backward later, or explicitly supersede the scientific gradient objective with a new directly testable contract. Add CPU/static fixtures including at least `N=3, grad_accum=7` (or another `lag>=N` case) and terminal-during-lag, proving exact segment partition, one required Local meta-gradient per frozen segment/terminal rule, no lost rows, no double write, and correct reset ordering.

### HIGH-2 — SCALER_SKIP abort discards the failed segment rows, creating an owner-global timestep hole and no defined way to retry the failed Local meta-gradient

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.4_2026-09-04.md:12,23`; `cosmos_framework/model/generator/mot/runtime_authority.py:140-143,303-304` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.4 says a scaler skip aborts the unpublished candidate, preserves the deferral queue, and retries on the next grad-accum window. But the production authority's `abort()` simply removes the pending transaction. Its raw rows are therefore discarded, while `_last_timestep` remains at the last committed row. Later `admit()` requires the next source timestep to equal `last_committed + pending_count + 1`.

Concrete failure: if the last committed source timestep is `k`, the skipped segment contains `k+1..k+N`, and publication-lag rows start at `k+N+1`, abort removes `k+1..k+N`. Draining the preserved lag queue now tries to admit `k+N+1` while the authority expects `k+1`, so the exact contiguous chronology contract fails closed. Reusing only the lag queue therefore cannot implement the stated retry.

Even if the failed segment's raw evidence were separately retained, retrying its **slow meta-gradient** requires the closing native task-loss graph (or an explicitly frozen replay of that native micro-batch), which v0.4 does not retain. Committing that fast candidate later without a corresponding successful slow optimizer transaction would violate the same atomic fast/slow gate v0.4 is trying to establish.

**Frozen-contract violation:** v0.4 §1 owner-global continuous source-timestep guarantee; v0.4 §2 SCALER_SKIP retry semantics; production authority contiguous admission/abort behavior; inherited once-per-segment Local meta-gradient objective.

**Acceptance:** freeze the full skipped-transaction preservation policy. A scaler-skipped segment must either (A) retain/replay the failed segment's rows **ahead of** later deferred rows together with whatever native state is required to reproduce its closing meta-gradient and only publish after a later successful optimizer transaction, or (B) be treated as a fatal/restart boundary with an explicitly consistent owner/epoch/source-timestep recovery contract, or (C) adopt another precise fail-closed policy that does not create chronology holes or fast/slow divergence. CPU/static trainer-authority evidence must drive the real `SCALER_SKIP` seam and prove: failed segment raw rows are not silently lost, next accepted `source_timestep` is contiguous, the failed transaction never becomes visible, later rows are not admitted ahead of it, and no fast commit occurs without the frozen corresponding slow-step semantics.

## Accepted / unchanged

- the real optimizer result seam and process-fatal exception direction materially closes the prior observability blocker;
- scaler skip explicitly suppressing scheduler progress is coherent;
- single authority pending remains a valid goal; adding a second production authority is not required by this review;
- pre-write witness, disabled parity, config identity, unique owner/object identity, exact selector, slow-only checkpoint boundary and default-off scope remain acceptable;
- no implementation/GPU/training authorization is granted by this verdict.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`.

Still prohibited: active wiring implementation (including trainer changes), real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires a fresh independent review for that new formal pair.
