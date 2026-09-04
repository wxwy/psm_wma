# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.1

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `35f881468e27ce3f0f902e8529d7593973e588a2`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `918e6666a85e1e2edf429e63481c1260cf0e225e`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.1_2026-09-04.md`

The prior config/optimizer/checkpoint closure remains accepted. This review covers only the new active Cosmos/trainer wiring design.

## Blocking findings

### HIGH-1 — per-window causal fast-state visibility conflicts with segment-only materialization

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.1_2026-09-04.md:22`

The design freezes that the pending segment is materialized only when it reaches `ttt_tbptt_steps` (default 16) or terminal remainder, while the same sentence requires intermediate windows to consume a detached fast-state K/V-only read. Under the closed production authority, raw rows are collected first and the TTT scan/update is performed by materialization. Therefore the design does not define how window 2..N can observe a fast state updated by the newly admitted preceding rows without either (a) remaining stale until segment close, or (b) executing an additional online update that would later be repeated by the full-segment materialization.

This leaves the core continual-memory causality ambiguous and can produce stale reads or double writes.

**Acceptance:** freeze one exact training chronology. For each row/window define: admit raw source -> numerical fast update/candidate state -> which window consumes the post-update read (same-t or next-t) -> graph rematerialization for outer loss -> rollback/commit. The graph-building rematerialization must not numerically apply a second write. Add CPU/static two-step plus N=3/default16/terminal fixtures proving no stale read, no double write, exact rollback to committed state, and train/inference chronology compatibility where applicable.

### HIGH-2 — native micro-batch backward is not a defined segment transaction

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.1_2026-09-04.md:23`

The design defines `L_segment` over multiple windows but then states that the trainer's existing single `loss.backward()` per micro-batch is the segment's unique backward and that commit happens in `on_after_backward`. It does not freeze how the losses/graphs for N windows coexist in one backward, whether one micro-batch is guaranteed to contain one complete segment, or how native `zero_grad` / gradient accumulation / optimizer step / scheduler ordering is prevented from advancing slow parameters while a Local segment is still pending. A per-window native backward would free graphs before the segment closes and cannot simultaneously be the one segment backward; conversely retaining N window graphs requires an explicit trainer-owned accumulation lifecycle.

**Acceptance:** freeze the exact trainer transaction owner and call order for N=1, N=3/default16 and terminal remainder: zero_grad/forward-loss accumulation/materialize/one ordinary backward/nonfinite handling/optimizer step/scheduler/Local commit-or-abort. Explicitly prohibit per-window backward or optimizer step while a segment transaction is open unless the design proves equivalence. Define failure semantics for backward/nonfinite and optimizer-step failure so committed fast state and slow-parameter progress cannot silently diverge. Require CPU/static spies asserting exact call counts/order and no commit/optimizer step for `N_valid_window=0`.

## Accepted / unchanged

- config identity/defaults and mutually exclusive enablement direction;
- unique registered slow-module owner / runtime object identity;
- exact four-group optimizer selector intent;
- slow-only checkpoint registration boundary;
- disabled-by-default parity requirement;
- training-side-only scope and explicit deferral of inference/GPU/training execution.

## Scope after this verdict

Allowed remediation is docs/status/ledger only for this design Gate. Do not implement active wiring yet.

Still prohibited: active wiring implementation, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires fresh same-SHA three-party review.
