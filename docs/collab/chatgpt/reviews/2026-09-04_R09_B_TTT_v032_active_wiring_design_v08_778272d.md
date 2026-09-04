# ChatGPT independent design review — R09-B TTT v0.3.2 active wiring v0.8

## Verdict

`REQUEST_CHANGES`

## Formal target

- root/design SHA: `778272d8c99439cc75fd8bcdff54bfe1aa308874`
- child/Gitlink: `dce279a966b6feef39ceb269cc064f6cd8f2240f`
- request/bookkeeping HEAD observed before review write: `b09d0c2115d6237c07bc1e89c06242774451c044`
- requested approval literal: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V032_ACTIVE_WIRING`
- design: `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.8_2026-09-04.md`
- previous same-Gate review: `docs/collab/chatgpt/reviews/2026-09-04_R09_B_TTT_v032_active_wiring_design_v07_0d6bfd3.md`

This is a fresh review of the new v0.8 formal pair. The V2 request/bookkeeping HEAD is not the formal target.

## Prior blocker status

- v0.7 HIGH-1 (terminal-during-lag dropped the mandatory terminal remainder): **CLOSED structurally**. v0.8 removes publication lag entirely; terminal remainder now closes in its own live terminal window and follows the ordinary witness/backward/commit/reset path.
- v0.7 HIGH-2 (skip retry carrier conflicts with single pending): **CLOSED structurally**. v0.8 removes skip retry/requeue entirely; fast commit is now intentionally backward-bound rather than optimizer-bound.
- v0.6 fast-only/no-BACKWARD_OK authority-grammar blocker remains **CLOSED**: v0.8 still requires witness-bound backward and the existing `BACKWARD_OK` commit gate; it does not introduce a no-backward commit path.
- Option (B) itself is acceptable as a contract choice: Local fast publication may be defined to depend only on successful closing backward, with no promise to roll it back on later scaler skip/optimizer failure.

## Blocking finding

### HIGH-1 — v0.8 has no legal single-backward seam that moves the frozen authority to `BACKWARD_OK` before `on_after_backward` commit

**Location:** `docs/build/PSM-WMA_R09_B_TTT_v032_active_wiring_design_v0.8_2026-09-04.md:8-13,23-25,37,41`; `cosmos_framework/trainer/__init__.py:489-509`; `cosmos_framework/model/generator/mot/runtime_authority.py:244-293`; `cosmos_framework/model/generator/mot/production_runtime_adapter.py:29-35` at child `dce279a966b6feef39ceb269cc064f6cd8f2240f`.

v0.8 freezes the following sequence: the trainer performs its existing single `loss_scaled.backward()`, then `on_after_backward` commits the closing Local segment. It also explicitly freezes `runtime_authority.py` as zero-change and requires the existing `commit()` `BACKWARD_OK` gate to remain authoritative.

The current production interfaces cannot realize that sequence. `ProductionRuntimeAuthority.commit()` rejects unless the pending phase is already `BACKWARD_OK`. The only public authority transition that sets this phase is `backward_and_mark()` / `backward_and_mark_many()`, and those methods themselves call `loss.backward()` before setting the phase. `ProductionLocalMemoryRuntime.backward()` simply delegates to that method. Meanwhile the actual trainer already calls `loss_scaled.backward()` before `model.on_after_backward()` and `callbacks.on_after_backward()`.

Therefore an implementation that follows v0.8 literally has only invalid choices:

1. call the current runtime `backward()` after the trainer backward, causing a second backward / graph-reuse failure and violating the frozen "trainer every micro-batch exactly one backward" rule;
2. call `commit()` directly, which fails because phase is still `MATERIALIZED_PENDING`;
3. mutate private `_pending_by_owner[owner].phase` from the adapter/model/callback, which bypasses the unique authority and creates a second lifecycle authority;
4. change `runtime_authority.py` or the trainer backward region to add/delegate an external-backward transition, which v0.8 currently forbids by freezing `runtime_authority.py` to zero change and limiting trainer modifications to `_optimizer_step` skip/result handling.

The same missing seam affects the promised backward-failure semantics: current trainer code does not route a thrown `loss_scaled.backward()` through a Local abort callback before propagation, while v0.8 acceptance requires an exact abort/rollback path.

**Frozen-contract violation:** v0.8 §1/§2 single-backward + `on_after_backward` commit ordering; C5A/production authority `BACKWARD_OK`-before-commit grammar; unique authority ownership; v0.8 §4 zero-change/runtime scope restriction.

**Acceptance:** freeze one explicit production-real external-backward lifecycle before implementation approval, while preserving exactly one backward and the existing `BACKWARD_OK -> commit` grammar. Acceptable examples include:

- delegate the closing micro-batch's one scaled backward to the authority/runtime so that it performs the trainer's only backward and marks `BACKWARD_OK`; or
- add a minimal authority-owned "arm/observe/mark external backward" transition that proves the materialized witness was actually traversed by the trainer backward, then lets `on_after_backward` commit, with a corresponding failure/abort seam.

Whichever policy is chosen, the design must expand the allowed implementation scope to the real files/seams it requires; private phase mutation is forbidden. CPU/static trainer-authority fixtures must drive the actual trainer order and prove: exactly one backward, closing loss reaches the witness, phase becomes `BACKWARD_OK` only after successful backward, commit occurs once in `on_after_backward`, backward exception cannot commit and leaves the committed snapshot unchanged, terminal remainder follows the same path, and non-closing windows never mark/commit.

## Accepted / unchanged

- Option (B) removes the publication-lag family cleanly and is materially simpler than v0.4-v0.7;
- terminal remainder and single-pending chronology are coherent again once lag/retry are removed;
- scaler skip may leave the already committed fast state intact while slow parameters do not step, because v0.8 explicitly defines fast publication as backward-bound rather than optimizer-bound;
- scheduler suppression on scaler skip, Local `.grad` cleanup, process-fatal optimizer exception, pre-write witness, disabled parity, config identity, unique module ownership, exact selectors and slow-only checkpoint boundary remain acceptable;
- no implementation/GPU/training authorization is granted by this verdict.

## Scope after this verdict

Allowed remediation is design/status/ledger only for `G0-R09-B-TTT-V032-ACTIVE-WIRING-DESIGN`.

Still prohibited: active wiring implementation, real checkpoint I/O, GPU/CUDA/torchrun, training/evaluation/inference, P4/P5, B2-T and LIBERO4IN1. A remediated design is a new formal root SHA and requires fresh review.
