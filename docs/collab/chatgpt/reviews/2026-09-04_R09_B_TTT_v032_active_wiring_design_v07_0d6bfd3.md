# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.7

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `0d6bfd3ecde13aa17fac18613f5b6239ebf44387`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `eaaa315555fd54684efa2cb5e17b6b5f7fb8a35b`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.7_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v06_0612502.md`

This is a fresh review of the new v0.7 formal pair. The request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.6 HIGH-1 (fast-state-only commit redefines frozen C5A/production authority grammar): **CLOSED as a proposed authority path**. v0.7 removes the no-BACKWARD_OK commit route and states that `runtime_authority.py` receives no new commit grammar.
- ordinary lag q>=N issue remains **CLOSED** under the accepted `grad_accum_iter <= ttt_tbptt_steps` + continuous-owner-run invariant.
- scheduler skip gate, three-state optimizer result seam, process-fatal exception, skipped-row FIFO retention, Local `.grad` cleanup, pre-write witness, disabled parity/config/owner/selector/checkpoint boundaries remain accepted.

## Blocking findings

### HIGH-1 — terminal-during-lag discards completed-causal rows and bypasses the frozen terminal-remainder contract rather than preserving it

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.7_2026-09-04.md:11-15`; inherited `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.1_2026-09-04.md:18-23`; `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.6_2026-09-04.md:19-25`; production runtime contract v0.3 terminal-remainder acceptance.

v0.7 avoids the rejected fast-only commit by declaring terminal-during-lag remainder rows to be dropped in the wiring queue: they are never admitted, never materialized, never backwarded and never committed; reset follows after the older published transaction.

This does not preserve the upstream contract. The inherited active-wiring mapping freezes one completed-causal evidence row per native window, and the C5A/production contract freezes terminal `0<r<N` as a real terminal remainder that receives one atomic witness-bound backward before commit/reset. A wiring layer cannot make that mandatory terminal transaction disappear merely by keeping the row outside the authority and then resetting the owner. That changes admission/terminal semantics, not just scheduling.

The fact that the terminal fast state will be reset does not remove the slow-learning contract: the terminal remainder is explicitly part of the frozen CPU acceptance and its Local slow gradient is observable even though fast state is later discarded.

**Frozen-contract violation:** inherited one-step completed-causal admission; C5A v0.6 terminal `0<r<N` materialize/backward/commit grammar; production runtime terminal-remainder scalar/gradient acceptance.

**Acceptance:** preserve the terminal remainder as an authority-visible transaction. Freeze an executable carrier for terminal-during-lag that lets the queued old-epoch remainder be admitted in FIFO order, materialized once, receive one contract-valid witness-bound backward, reach `BACKWARD_OK`, publish through the normal two-stage success gate, and only then reset/advance epoch. If the project instead wants to drop terminal-lag evidence, that requires a separate upstream C5A/production-runtime refreeze Gate; active wiring alone cannot supersede it. CPU/static acceptance must include terminal `0<r<N` during lag and prove no row loss, exact old-epoch ownership, one backward/commit, then reset.

### HIGH-2 — skip-retry carrier still violates the single-pending authority: the current live row cannot enter a new segment before the retried segment commits

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.7_2026-09-04.md:17-23`; `cosmos_framework/model/generator/mot/runtime_authority.py:110-138` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.7 retries a skipped full segment by using the next same-owner live forward as a carrier: it `begin()`s, admits the N replay rows, materializes that full segment and uses the carrier window's task loss through the differentiable witness. It then says the carrier window's own evidence row is "subsequently admitted into the next segment" during that forward.

The current frozen authority cannot do that. After `materialize`, the retried owner still occupies the single `_pending_by_owner` transaction in `MATERIALIZED_PENDING`; it remains there through backward and until a later optimizer-success publication/commit. `begin(owner)` rejects while any pending exists, and `admit()` rejects unseen rows once the current pending is no longer `COLLECT_RAW`. Therefore the same forward cannot open/admit the carrier row into a second segment without either introducing a second pending authority or mutating the existing transaction grammar—both explicitly disallowed by this remediation.

There is also no frozen external-carrier API that returns the carrier row's differentiable pre-write read from the retried candidate while keeping the carrier evidence itself outside the authority transaction. The existing pre-write witness contract is row/segment based. If the intended resolution is to keep the carrier row graph-free in the wiring FIFO until the retry commits, that must be stated explicitly together with its delayed write/read chronology and differentiable carrier-read seam.

**Frozen-contract violation:** v0.7 §3 retry trace; frozen single-pending ProductionRuntimeAuthority semantics; inherited admit/read/write chronology.

**Acceptance:** freeze one single-pending-compatible retry trace. The retried N rows may occupy the authority through materialize/backward/commit, but the carrier row must not be admitted into another authority transaction before that commit. If it remains deferred, define exactly: (1) where its raw evidence is queued, (2) how the current carrier loss obtains a differentiable `read(S_retry_final)` without admitting/writing the carrier row, (3) when that carrier row is later admitted/written in FIFO order after retry publication, and (4) behavior under repeated skip and terminal arrival. CPU/static trace must prove zero second-pending attempt, exact source-timestep order, one write per row, carrier pre-write causality, and repeated-skip correctness.

## Accepted / unchanged

- removing v0.6 fast-only commit is the correct direction and closes the previous authority-grammar blocker itself;
- ordinary lag bounded by `accum <= N` and continuous owner runs remains coherent;
- using a later live window as an explicitly redefined Local-gradient carrier can be reviewed as an active-wiring Local-gradient objective, provided the single-pending chronology is made executable and upstream terminal semantics are not bypassed;
- scheduler suppression, scaler-skip `.grad` cleanup, process-fatal optimizer exception, pre-write witness, disabled parity/config/owner/selector/checkpoint boundaries remain accepted;
- no implementation/GPU/training authorization is granted.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`, unless a separate upstream C5A/production-runtime refreeze Gate is explicitly opened.

Still prohibited: active wiring implementation including trainer/runtime changes, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires fresh review.
