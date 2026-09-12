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

- immediate prior live blob SHA: `8021ed839cc24feca23105192c590516b983a8d3`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Execution Evidence canonical worktree-snapshot remediation APPROVED

Formal pair:
- root design SHA: `981f89873263f5c10fcfc8c30740bf5ce014eb2d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CONTROLLED_EXECUTION`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_immutable_source_collection_controlled_execution_design_981f898_93a89ba.md`

Canonical review commit:
`b59ed0ab84fd61c736b36f31e547792e10dd296c`

Current blockers: `0`; Design/Authority `0`; Production `0`; Evidence-only `0`.

Closed in this remediation:
- all pre-live early FAIL paths now use the single exact five-key not-required rollback null-record;
- the worktree snapshot derivation is frozen to the six fixed collection/receipt paths, repo-relative POSIX names, UTF-8 byte ordering, exact absent/regular entry forms, exact `100644|100755` JSON-string modes, raw-byte SHA-256, `git status --porcelain=v1 -z --untracked-files=all` out-of-allowlist rejection, and `find -P` type checks;
- retained before/after snapshots, target-ref revision, local HEAD symbolic/detached identity, controlled index tree and worktree digest together provide the required machine-checkable rollback witness;
- prior push/publication violation encoding, source-read prefix semantics, and candidate construction vs post-handoff verification remain closed.

Scope remains docs-only. This approval does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Continue only along the already frozen source-evidence/publication closure sequence.

This notice is coordination only and does not replace the formal pair or canonical review.
