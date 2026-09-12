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

- immediate prior live blob SHA: `da47911cc874945cd27d3019c4a0931a651d75f9`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Execution Authority CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `5efcbdf8954f65da9c7dfd1d0f34c96204c5ddf6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:165)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_execution_authority_cpu_static_implementation_5efcbdf_93a89ba.md`

Canonical review commit:
`da25404e8ce2406b18406de6b97f8437e9a43737`

Current blockers: `2 HIGH`.

Closure/progress:
- prior module-path symlink issue is materially closed: bootstrap now checks the unresolved absolute module path with direct `lstat`, rejects symlink/non-regular paths, requires `realpath(full)==full`, and verifies raw SHA + exact formal-tree blob before project import;
- prior hostile local-config examples `core.fsmonitor` and `[include]` are now rejected before the first native Git command;
- formal root/Gitlink is valid and child commit is reachable.

Remaining HIGH-1 — executable identity is still split across the project-import boundary:
- interpreter is only realpath-compared pre-import; regular/non-symlink type, raw SHA and exact version remain post-import;
- Git gets pre-import type/raw-SHA checking but exact `--git-version` remains post-import.

Exact remediation:
- before `sys.path.insert`/`runpy`, verify interpreter absolute regular non-symlink + raw SHA + exact version;
- also verify exact Git version pre-import;
- add isolated witnesses for interpreter symlink/path/hash/version drift and Git version drift, proving no project import/ref/evidence/callback.

Remaining HIGH-2 — bootstrap still permits worktree-specific config authority before its first Git commands:
- bootstrap allowlist accepts `extensions.worktreeconfig=true`;
- it does not require `<git_dir>/config.worktree` absent before `rev-parse`/`status`/`ls-tree`;
- therefore Git can still consume unaudited per-worktree config before the v0.4 common-config authority boundary is established.

Exact remediation:
- before first Git command require `extensions.worktreeConfig` absent or exactly false;
- derive/validate worktree admin and common Git directories without unaudited Git config and require `config.worktree` absent;
- bind the same common config authority used by production preflight;
- add an isolated witness for `worktreeConfig=true` plus hostile `config.worktree`, proving no Git authority observation/project import/ref/evidence before rejection.

Reported `92/92 PASS` and static checks are supportive but do not replace these missing causal witnesses.

Scope reminder: no real materialization, source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.