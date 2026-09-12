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

- immediate prior live blob SHA: `b2e76bb28bed623e4571926c3298fb4f4b3154e5`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Execution Authority CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `fff6d05ef330ada5f6db5edbdc8dde32e2c99019`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:172)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_execution_authority_cpu_static_implementation_fff6d05_93a89ba.md`

Canonical review commit:
`0c8bb944c76725ca70d3da4805d0911101474f3b`

Current blockers: `1 HIGH`.

Closure/progress:
- prior linked-worktree `config.worktree` path bug is CLOSED: bootstrap now resolves the actual per-worktree admin dir and rejects `<git_dir>/config.worktree`;
- linked `.git` marker, reciprocal `gitdir`, and `commondir` are opened with no-follow semantics and checked for basic consistency;
- common config uses retained no-follow FD bytes and pathname identity, with before/after revalidation around each native Git observation;
- actual detached linked-worktree, forged gitdir escape, and common-config replacement witnesses are present;
- formal root/Gitlink is valid and child commit is independently reachable.

Remaining HIGH — repository-routing metadata is not frozen across native Git observation:
- linked-worktree `.git` marker, `<git_dir>/gitdir`, and `<git_dir>/commondir` are read once but their pathname identities/retained-FD bytes are not revalidated before/after `rev-parse` / `status` / `ls-tree`;
- native Git re-resolves those routing files from `cwd`, so they can be swapped after bootstrap admission while the old common config remains unchanged; Git may then jump to a different admin/common directory and consume a different local-config/object authority without tripping the current common-config check;
- `git_dir` / `git_common_dir` directory identities and `config.worktree` absence are likewise not revalidated across each observation.

Exact remediation:
1. retain accepted `(dev,ino,size)` + raw bytes for the linked worktree `.git` marker, `<git_dir>/gitdir`, and `<git_dir>/commondir`, plus accepted directory identities for `git_dir` and `git_common_dir`;
2. immediately before and after every native bootstrap Git observation, revalidate all routing paths/files/directories against those accepted identities/bytes and keep `<git_dir>/config.worktree` absent;
3. for the primary worktree, retain/revalidate the `.git` directory identity across the observations as well;
4. add direct actual-linked-worktree witnesses replacing either the `.git` marker or `commondir` after precheck but before the real Git process, proving rejection before project import/ref/evidence/callback;
5. preserve all already-closed common-config, executable identity, four-module closure, endpoint/no-replace, Evidence ABI and temporary-CAS contracts.

Reported `55/55` targeted and `100/100` combined stdlib passes plus static checks are supportive, but do not replace this missing routing-metadata causal witness.

Scope reminder: no real materialization, source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.