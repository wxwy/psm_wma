# ChatGPT independent review — R09-B TTT v0.3.7 canonical training/runtime transaction contract @ b912aab

Date: 2026-09-08

## Verdict

**APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_CPU_DESIGN**

Formal Gate:
`G0-R09-B-TTT-V035-CANONICAL-SEMANTICS-DESIGN`

Formal design pair:
- root design SHA: `b912aab3f9607319d383cee6507796df90cc4130`
- child/Gitlink baseline: `80aec090688e3c710c41e1dfd86b6500773db2c7`
- request/bookkeeping HEAD observed at review start: `30891cb18149d4e06e564cc6e23750d36a45656d`
- superseded prior design target: `bc252114b6799559a172a3061677562c8df565a2`
- prior ChatGPT review: `2dfd518332d62378f8f27bb2adfc251d71b57d6a` (`REQUEST_CHANGES`)

The bookkeeping SHA `30891cb...` is not the design target; its parent is the exact formal root `b912aab...`. This verdict binds only `b912aab... / 80aec090...`.

## Scope check

- v0.3.7 is docs-only and keeps the child/Gitlink exactly `80aec090...`;
- the technical delta is the new `docs/build/PSM-WMA_Local_Memory_canonical_training_runtime_contract_v0.3.7.md`, with SESSION/TODO bookkeeping around the same Gate;
- no child/runtime/packer/trainer implementation, GPU/CUDA/torchrun, real data/cache/checkpoint I/O, training, evaluation or inference is authorized by this review.

## Closure of the v0.3.6 HIGH

The single HIGH from the v0.3.6 review is closed.

v0.3.7 now freezes one deterministic GA-window transaction:

1. Before the first Local-path backward, the rank-local scheduler creates an immutable `GAWindowPlan` containing ordered member identities, `planned_N_valid[mu]`, and fixed `N_window`.
2. Before each member backward, `actual_gathered_N_valid[mu] == planned_N_valid[mu]` is mandatory. A mismatch fails before that member contributes slow gradient or fast-state/cursor/exposure commit.
3. A member may commit detached fast state/cursor/queue/exposure only after inner/candidate finiteness, native-loss finiteness, planned/actual equality, successful ordinary outer backward, and identity validation.
4. If a later member fails after earlier members succeeded, earlier fast chronology commits remain authoritative and are never replayed/rolled back; the entire partial slow-gradient window is discarded/zeroed; no slow optimizer or slow-LR-scheduler step occurs; remaining old-window members do not execute.
5. A new `GAWindowPlan` and denominator are rebuilt from the current committed scheduler state. Only the uncommitted current/remaining identities may be deterministically redelivered; rebind/resample/random replay/episode substitution are forbidden.
6. `GradScaler` skip is explicitly separated from transaction failure and retains the already-frozen fast chronology semantics.
7. Required CPU/static fixtures cover full success, first-member failure, later-member failure, planned/actual mismatch, and identity/retry failure while observing fast bytes, scheduler state, slow grads, optimizer/LR iterations, executed identity sequence and new denominator.

This is consistent with the v0.3.6 loss partition and scheduler semantics and resolves the denominator/partial-gradient ambiguity identified by ChatGPT.

## Non-blocking implementation-design requirement

v0.3.7 intentionally leaves the exact retry budget, exception taxonomy and terminal/error codes to the next CPU/static implementation design. That is acceptable at this Gate because the algorithmic invariant is already frozen: retries must be deterministic, identity-preserving, finite/fail-closed, and may not alter the partial-slow-window-discard / fast-commit-retain semantics. The next design must make those operational limits executable before any implementation code is authorized.

## Authorization boundary

This approval authorizes **only the next CPU/static implementation design** for the canonical Local-Memory training/runtime path.

It does **not** authorize:
- child/runtime/packer/trainer implementation;
- GPU/CUDA/torchrun;
- real model/data/cache/checkpoint I/O;
- training/evaluation/inference;
- formal Local-Memory training or later smoke/runtime Gates;
- P4/P5, B2-T or LIBERO4IN1 operations.

Any next implementation/design target requires its own exact-SHA review.
