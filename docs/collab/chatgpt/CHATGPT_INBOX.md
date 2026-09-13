# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `3b7f19894dccc4ac1c1f46b3a320c895f39c76c2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Causal Owner Identity Execution Design v0.4 APPROVED

Formal pair:
- root docs SHA: `76210e7bcbdc606e39775e2dae258542cf3c0d38`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

Verdict:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_causal_owner_identity_execution_design_v04_76210e7_93a89ba.md`

Canonical review commit:
`886d1263c08e40938956264e48f581de0bfffaae`

Current blockers: `0` (`0 design/authority`, `0 child/runtime`).

Prior blocker closure:
1. v0.3 HIGH-1 CLOSED: every post-exec FD8-derived Git consumer is now frozen to exact `close_fds=True, pass_fds=(8,)`, with pre/post FD8 identity barriers, no FD3/4/5 leakage, fail-closed/post-mutation classification, and an actual temporary-Git FD8-index seam witness.
2. v0.3 HIGH-2 CLOSED: v0.4 freezes procfd-safe no-follow FD8-relative traversal for affected bootstrap/module/loaded-module/repository/config seams and forbids canonicalizing FD8-derived owner values back into global CLEAN authority while preserving existing anti-symlink/raw/blob/route/common-config checks.

Implementation authorization is narrow: only root-only stdlib temporary-fixture CPU/static launcher/adapter/tests implementation under v0.4. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized.

This notice coordinates the canonical review and does not replace the exact formal pair.
