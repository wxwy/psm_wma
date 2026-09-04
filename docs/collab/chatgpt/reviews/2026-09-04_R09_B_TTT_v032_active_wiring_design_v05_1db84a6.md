# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.5

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `1db84a6d9356e10dceb5c7353e2e21dd40ca2dfd`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `fe1db9a2ecc947e6388a633687901039a6078f36`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.5_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v04_fba72be.md`

This is a fresh review of the new v0.5 formal pair. The V2 request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.4 HIGH-1 (raw lag backlog can cross a full Local segment/terminal after the original closing task-loss backward is gone): **NOT CLOSED**. v0.5 renames the mechanism to lazy segment formation, but its flush grammar still cannot satisfy FIFO chronology, one-pending/segment length, and the inherited closing-window witness-loss objective when queued length reaches `N` before the next live forward.
- v0.4 HIGH-2 (SCALER_SKIP loses failed-segment rows / chronology / corresponding Local gradient transaction): **PARTIALLY CLOSED for raw chronology only, still blocked for executable retry/gradient semantics**. Requeueing failed rows to the FIFO front avoids the immediate source-timestep hole, but it deterministically creates the `queue_len >= N` case that v0.5 cannot legally close under its own §1 grammar.
- optimizer-result observability, scheduler skip gate, process-fatal exception direction, pre-write witness, Local-gradient supersede declaration, disabled parity/config/owner/selector/checkpoint boundaries remain accepted.

## Blocking findings

### HIGH-1 — lazy flush cannot simultaneously preserve FIFO chronology, one-pending segment length, and “closing always lands on a live window” once queue length reaches `N`

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.5_2026-09-04.md:8-15`; inherited v0.3 §3 Local-gradient objective; `cosmos_framework/model/generator/mot/runtime_authority.py:105-138,303-329` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.5 freezes three simultaneous requirements: queued rows are FIFO and graph-free; a live transaction closes every `ttt_tbptt_steps=N` admitted rows; and the closing row must be a live micro-batch whose task loss is connected to the witness graph. It also explicitly claims support for backlog `>=N`.

These cannot all hold when `queue_len >= N` before the next live forward. Example `N=3`: queue already contains source timesteps `k+1,k+2,k+3`; the next live row is `k+4`. FIFO admission makes `k+3` the logical closing row before `k+4` is admitted. But `k+3`'s original window already executed with lag read and no Local witness graph. The new live row `k+4` cannot become the closing row without either (a) admitting it ahead of queued `k+3` and violating contiguous FIFO chronology, (b) allowing a pending segment to exceed `N`, or (c) using `k+4`'s task loss to supervise the segment ending at `k+3`, which changes the inherited scientific objective from “segment closing window loss -> witness graph” to a next-window loss.

The same contradiction is stronger for terminal-during-lag: if the queued terminal row itself completes the old-epoch segment, the next live window may belong to another episode/owner and cannot serve as that terminal segment's closing task loss without cross-episode contamination.

**Frozen-contract violation:** v0.5 §1 “segment closes only on live window” + “arbitrary alignment including lag>=N” + FIFO owner-global chronology; inherited v0.3 Local slow-gradient objective and terminal-remainder closure.

**Acceptance:** freeze one executable queue-drain grammar for every `q = queue_len`, especially `q=N`, `q>N`, and terminal-in-queue. Either enforce a validated barrier/cap proving `q<=N-1` before any live forward continues, retain/replay the original closing native loss state needed to close queued segments later, or explicitly supersede the gradient objective with a new directly testable objective. CPU/static acceptance must include exact traces for `N=3, grad_accum=7`, `q=N`, `q>N`, and terminal-during-lag, proving FIFO source timesteps, exact segment boundaries, the exact task loss feeding each witness graph, one-pending legality, one meta-gradient per frozen segment, no cross-episode loss, no double write, and reset ordering.

### HIGH-2 — SCALER_SKIP retry requeues a complete failed segment, which immediately recreates HIGH-1 and cannot reproduce the frozen closing-window gradient with raw evidence alone

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.5_2026-09-04.md:17-21`; `cosmos_framework/model/generator/mot/runtime_authority.py:303-306` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.5 correctly preserves failed-segment raw rows by moving them to the front before `abort()`, so the v0.4 source-timestep hole is addressed at the raw chronology layer. However, a skipped full segment contains exactly `N` rows. Therefore the next flush starts with `queue_len >= N`, the impossible state above. The prose says the retried segment will close on a “new live closing window”, but a later live window is chronologically after all `N` failed rows; it is not the original segment's closing row.

Raw evidence is also insufficient to reproduce the inherited slow-gradient transaction. The skipped closing backward's graph is gone, and its native closing task loss is not retained. Re-materializing the same `N` raw rows later and attaching a later window's task loss changes which task loss trains the Local meta-parameters. Conversely, publishing the retried fast candidate without a successfully replayed corresponding frozen Local slow-gradient transaction would violate the fast/slow atomicity requirement.

**Frozen-contract violation:** v0.5 §2 skip-retry semantics; inherited “closing window provides the segment's unique Local meta-gradient” objective; v0.4/v0.5 fast/slow atomic publication gate.

**Acceptance:** freeze a complete retry unit, not only raw rows. Either replay/retain enough of the failed closing native micro-batch/loss state to recreate the same frozen witness-loss transaction before publish, or define SCALER_SKIP as a fatal/restart boundary, or explicitly replace the scientific objective with a new exact rule. Real trainer-spy acceptance must show for a skipped `N`-row segment: failed rows remain FIFO, next accepted source timestep is contiguous, the exact task loss used on retry is identified and contract-valid, no later row is substituted as the old segment's closing loss, no fast publish occurs without its matching successful Local slow step, and terminal skip has correct epoch/reset behavior.

## Accepted / unchanged

- preserving skipped raw rows at FIFO front is the correct chronology direction and closes the narrow “rows silently disappear” defect;
- scheduler suppression on scaler skip and the real three-state optimizer seam remain acceptable;
- exception-as-process-fatal remains acceptable under the already-frozen checkpoint recovery boundary;
- pre-write witness semantics, disabled parity, config identity, unique module ownership, exact selectors, slow-only checkpoint boundary and default-off scope remain accepted;
- no implementation/GPU/training authorization is granted.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`.

Still prohibited: active wiring implementation including trainer changes, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires fresh same-pair independent review.
