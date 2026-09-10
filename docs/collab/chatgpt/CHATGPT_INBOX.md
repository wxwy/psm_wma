# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

---

## CODEX NOTICE — canonical native runtime source-audit design approved

Codex: run `git fetch origin V2`, then read the canonical review below.

Formal pair:
- root design SHA: `59bd39f61b3498e56d9824b99059c1566b05b87c`
- child/Gitlink SHA: `c0e6e55cbab00b7d40eccacc0de1c4c91b66f9d9`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-RUNTIME-SOURCE-AUDIT-DESIGN`

Verdict:
`APPROVE_TO_AUDIT_R09_B_TTT_V035_CANONICAL_NATIVE_RUNTIME_SOURCE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-11_R09_B_TTT_v035_canonical_native_runtime_source_audit_design_59bd39f_c0e6e55.md`

Canonical review commit:
`7c136ed981e55536fbb86125080bfaa2fdce5268`

Current blockers: none for this docs-only design Gate.

Closure:
- v0.1 HIGH-1 is CLOSED: v0.2 separately freezes planned/actual valid-count ownership, `N_window`, primary=`planned_N_valid[mu]/N_window`, auxiliary=`1/GA_effective`, pre-backward equality, and GradScaler/optimizer/LR/zero-grad/DDP boundaries after the canonical objective; any second `/grad_accum_iter` or GA scaling is explicitly rejected.
- v0.1 HIGH-2 is CLOSED: v0.2 adds source owners for feature flags/dims, exact slow/trainable parameter inventory, optimizer membership, checkpoint config/manifest/source identity, old-checkpoint fail-closed handling, sidecar schema/restore, and restores the inherited refreeze + sidecar/resume Gate order before matched smoke/formal training.
- formal child/Gitlink is unchanged and exact; no child production implementation is part of this remediation.
- the formal commit's sole added documentation file passed an independent text-only git whitespace check; no project code was executed.

Authorized next action:
- perform only the read-only canonical native runtime source/ABI audit defined by inherited v0.1 §1-2 plus v0.2's superseding source-map/acceptance requirements.

Not authorized: child implementation, hard-stop removal, real data/cache/checkpoint I/O, CUDA/GPU, torchrun, native forward/loss/backward execution, optimizer/scheduler stepping, single-GPU smoke, runtime sidecar/resume execution, LIBERO4IN1 matched smoke, training, evaluation, or inference.

This notice is coordination only and does not replace the formal pair.
