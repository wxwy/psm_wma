# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.2

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `6b1af605ee46c8bbb30834ca8f91d96b955e4906`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed immediately before review write: `c522ce3d4695f1f2051274b02ab5bfc3243c4550`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.2_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v01_35f8814.md`

This is a fresh review of the new v0.2 design pair. The request/bookkeeping SHA is not the formal target.

## Prior blocker status

- v0.1 HIGH-1 (stale-read/double-write chronology): **PARTIALLY CLOSED, still blocked by a causal witness mismatch**. v0.2 now separates online detached candidate state from graph rematerialization, which removes the earlier undefined double-write framing, but the closing witness path still does not match the newly frozen read-before-own-write semantics.
- v0.1 HIGH-2 (trainer transaction/backward lifecycle): **NOT CLOSED**. v0.2 defines callback ordering, but the proposed publication point remains earlier than confirmed optimizer-step success while simultaneously promising rollback on later optimizer failure/skip.

## Blocking findings

### HIGH-1 — closing witness uses post-write read while v0.2 freezes read-before-own-write causality

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.2_2026-09-04.md:8-24`; `cosmos_framework/model/generator/mot/local_evidence.py:485-496`; `cosmos_framework/model/generator/mot/runtime_authority.py:224-247` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.2 freezes `read(t)` as `read(S_{t-1})`: window `t` may see rows `0..t-1` and must never see its own row `t`. It then requires the segment-closing window to obtain that same numerical read from the materialized witness graph.

The closed core does not provide that witness semantics. `step_projected_many()` first computes the inner gradient, forms `updated`, and only then emits the token by applying `_fast_mlp(queries[row], updated)`. `scan_segment_many()` repeatedly calls that step; `ProductionRuntimeAuthority.materialize_many()` stores those tokens and returns `pending.witness[-1]`. Therefore the closing token is currently a post-write `read(S_t)`, not the frozen pre-write `read(S_{t-1})`. It can expose the current row's own evidence and cannot be numerically equal to the v0.2 scalar causal reference merely by calling the existing materialize path.

**Frozen-contract violation:** v0.2 §1 exact chronology/read-after-(t-1) guarantee and its claim that the closing witness is numerically the same read with a graph.

**Acceptance:** freeze one explicit production witness API/path that returns a differentiable **pre-write** token `read(S_{t-1})` for the current row while separately computing the differentiable final candidate `S_t`. The closing prefix must equal a scalar reference `read(S_{t-1})`; the committed candidate must equal the one-write `S_t`. Add CPU/static coverage for at least `T>=17` plus terminal remainder, proving segment-boundary causality, no self-evidence leakage, no stale read, no numerical double write, and witness/candidate equality against the exact reference.

### HIGH-2 — `on_after_backward` commit cannot satisfy rollback-on-later-optimizer-failure semantics

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.2_2026-09-04.md:26-43`; `cosmos_framework/trainer/__init__.py:489-509` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.2 freezes `commit` in `on_after_backward` immediately after a successful closing-window backward, then separately says that if the later optimizer step fails or is skipped (including grad-scaler behavior), the Local segment must `abort`, the candidate must roll back to committed state, and fast/slow progress must not silently diverge.

The actual trainer order is backward -> `model.on_after_backward()` -> callbacks `on_after_backward()` -> increment grad accumulation; only when the accumulation boundary is reached does it call `_optimizer_step()`, followed by zero-grad. Thus `on_after_backward` occurs before optimizer success, potentially multiple micro-batches before it under `grad_accum_iter > 1`. Once the callback publishes the fast state, subsequent windows may consume that published state. A later skipped/failed optimizer step cannot causally retract memory already consumed by those windows. The current trainer also has no post-success optimizer callback frozen by this design.

**Frozen-contract violation:** v0.2 §2 failure semantics require atomic consistency between fast-state publication and slow optimizer progress, but its own hook order publishes before the event whose failure must trigger rollback.

**Acceptance:** freeze one coherent transaction policy. Either (A) defer fast-state publication until a confirmed successful optimizer step/post-step boundary, with an explicit pending/unpublished state that later windows cannot consume, or (B) deliberately redefine the contract so Local fast commit depends only on successful backward and remove the promise to roll it back on later optimizer skip/failure. If rollback semantics are retained, add CPU/static trainer-spy fixtures with `grad_accum_iter > 1`, successful step, skipped grad-scaler step, and thrown optimizer step proving no failed transaction becomes visible to a subsequent window.

## Additional contract concern — must be clarified in remediation

`docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.2_2026-09-04.md:21-24` explicitly freezes a closing-only Local slow meta-gradient, while the inherited production-runtime v0.3 contract (`docs/build/PSM-WMA_R09_B_TTT_v032_production_runtime_contract_design_v0.3_2026-09-04.md:10-27`) froze native scalar and parameter-gradient parity for segmented outer loss. The remediation must explicitly state whether active wiring is superseding that earlier gradient objective or preserving it; do not leave the scientific objective change implicit behind the generic `conflict时以v0.2为准` clause. If superseded, freeze the exact new objective and direct gradient-reference acceptance; if preserved, demonstrate parity.

## Accepted / unchanged

- v0.2 now defines a concrete online detached candidate-state concept and a graph-rematerialization concept;
- disabled parity is materially more testable than v0.1;
- config identity, unique slow-module owner/object identity, exact selector intent, slow-only checkpoint boundary and default-off scope remain acceptable;
- no implementation/GPU/training authorization is granted by this verdict.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`.

Still prohibited: active wiring implementation, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires fresh same-SHA independent review.
