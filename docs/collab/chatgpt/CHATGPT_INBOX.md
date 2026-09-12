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

- immediate prior live blob SHA: `3f0afef77e9c5d25d487ac80a930b3785feda5ab`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Execution Snapshot Annex v0.3 APPROVED

Formal pair:
- root docs SHA: `b2fc05489abb2a4c1bc7314844c94c197834b9ff`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`APPROVE_TO_PREPARE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT_EXECUTION_REQUEST`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_execution_snapshot_annex_v03_b2fc054_93a89ba.md`

Canonical review commit:
`a0e578feb827b546675528a369ff9a3872267dcb`

Current blockers: `0`.

Closure:
- prior bootstrap argv HIGH is CLOSED: parser `actual_argv` remains 2427 bytes / `72777bd...`, while bootstrap `sys.orig_argv[6:]` including leading `--` is separately frozen at 2432 bytes / `aefa3a7d...`;
- bootstrap contract canonical JSON independently recomputes to 182 bytes / `62a7bb...`;
- prior transaction-env HIGH is CLOSED: exact production `NativeAuthorityGit.env` is frozen as six base keys + `GIT_INDEX_FILE` + six author/committer keys, 471 bytes / `daf9e4...`;
- commit message is correctly frozen as `git commit-tree` stdin, not an environment variable;
- formal Gitlink/child are exact and reachable; delta remains docs/bookkeeping only;
- no new Design/Implementation/Evidence blocker found in this docs-only scope.

Scope reminder: this approval permits only preparation of the complete docs-only execution request. It does not authorize materialization, JSON/worktree/index/candidate/ref/evidence creation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

The complete execution request and command still require a separate exact three-party `APPROVE_TO_MATERIALIZE_R09_B_TTT_V035_IMMUTABLE_SOURCE_AUTHORITY_ROOT` before execution.

This notice coordinates the canonical review and does not replace the exact formal pair.