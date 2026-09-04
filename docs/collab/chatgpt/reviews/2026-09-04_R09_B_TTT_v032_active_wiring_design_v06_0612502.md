# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.6

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `061250269bc4e6a72e7b9cb0a9a140abfdbd7553`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `8dedaa632ab1564646c333ea4f253478f1c3ab6b`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.6_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v05_1db84a6.md`

This is a fresh review of the new v0.6 formal pair. The request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.5 HIGH-1 (q>=N queue cannot preserve FIFO + exact segment length + live closing): **CLOSED for the ordinary non-terminal/non-skip lag path**. v0.6 adds a fail-closed `grad_accum_iter <= ttt_tbptt_steps` invariant, so ordinary publication lag is bounded to q<=N-1, and per-owner flush can make the next owner-live row the closing row when q=N-1.
- v0.5 HIGH-2 (SCALER_SKIP raw chronology hole / retry): **CLOSED only at raw-row chronology level**. Requeued rows preserve FIFO/source_timestep continuity and `.grad` cleanup is now explicit, but the proposed fast-only completion changes the already-frozen authority transaction contract.
- optimizer result observability, scheduler skip gate, process-fatal exception, pre-write witness, disabled parity/config/owner/selector/checkpoint boundaries remain accepted.

## Blocking finding

### HIGH-1 — v0.6 fast-state-only commit redefines frozen C5A/production authority semantics inside the active-wiring Gate

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.6_2026-09-04.md:13-19`; `docs/build/PSM-WMA_R09_B_TTT_v032_c5a_chronology_owner_segment_design_v0.6_2026-09-04.md:19-25`; `cosmos_framework/model/generator/mot/runtime_authority.py:243-248` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.6 resolves terminal-during-lag and SCALER_SKIP by explicitly introducing a new authority path that publishes a segment with **no witness backward / no Local slow meta-gradient**. It requires `runtime_authority.py` to add a detached "fast-state-only commit" path and says terminal remainders and skipped full segments may publish on a later SUCCESS boundary with `gradient=None`.

That is not an adapter-level scheduling detail. It changes the already-frozen C5A transaction grammar. C5A v0.6 freezes `MATERIALIZE_PENDING` -> ordinary outer `backward()` -> atomic commit, and specifically freezes terminal `0<r<N` as one atomic backward before commit. The current production authority enforces the same rule in code: `commit()` rejects every transaction whose phase is not `BACKWARD_OK`.

The PSM-WMA active-wiring layer therefore cannot introduce a second no-backward publication authority while still claiming to inherit C5A/production authority unchanged. Doing so would make two incompatible commit grammars authoritative for the same owner/segment state and would bypass the frozen completed-causal transaction closure contract precisely on terminal and scaler-skip boundaries.

**Frozen-contract violation:** C5A v0.6 §3-§4 atomic materialize/backward/commit semantics; current `ProductionRuntimeAuthority.commit()` BACKWARD_OK gate; active-wiring inheritance rule that runtime integration must not redefine frozen C5A authority semantics.

**Acceptance:** choose one authority-consistent policy before active-wiring implementation approval. Either:

1. preserve C5A semantics for terminal/skip cases, meaning every committed non-empty segment still reaches `BACKWARD_OK` through the frozen witness-bound backward before publication, with an executable loss/retry carrier; or
2. formally reopen/refreeze the upstream C5A/production-runtime contract in a separate design Gate to introduce a precisely scoped fast-only transaction type, including its phase grammar, replay/identity/chronology semantics, terminal/reset behavior, optimizer relationship, and direct CPU Evidence. Only after that upstream authority is approved/implemented may active wiring consume it.

An active-wiring-only edit to `runtime_authority.py` that adds a no-backward commit path is not acceptable evidence of closure.

## Accepted / unchanged

- the `grad_accum_iter <= ttt_tbptt_steps` fail-closed bound plus per-owner continuous-run validation is a coherent way to eliminate ordinary q>=N lag;
- per-owner flush and q=N-1 live-closing semantics are structurally consistent for the ordinary path;
- preserving skipped raw rows at FIFO front, suppressing scheduler progress on scaler skip, and clearing Local slow `.grad` are acceptable directions;
- exception-as-process-fatal remains acceptable;
- no implementation/GPU/training authorization is granted.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`, unless the project explicitly opens a separate upstream C5A/production-runtime refreeze Gate.

Still prohibited: active wiring implementation including trainer/runtime-authority changes, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design or upstream authority refreeze creates a new formal pair and requires fresh review.
