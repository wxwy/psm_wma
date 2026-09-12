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

- immediate prior live blob SHA: `2af62929fe32267f4a497f2f418c8e5484f2ced5`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Execution Authority CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `a564e953aadc646daeed66e46115ecdb614e80b8`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:165)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_execution_authority_cpu_static_implementation_a564e95_93a89ba.md`

Canonical review commit:
`f27d9683eb0f7969b3b8f52f32409fc3b4c0b618`

Current blockers: `1 HIGH`.

Closure/progress:
- prior executable-identity HIGH is CLOSED: bootstrap now verifies interpreter absolute regular/non-symlink + raw SHA + exact version and Git regular/non-symlink + raw SHA + exact version before project import; isolated drift witnesses were added;
- `extensions.worktreeConfig=true` is now rejected before native Git observations;
- module closure/symlink, endpoint/no-replace, Evidence ABI, CAS and child/Gitlink contracts remain intact;
- formal root/Gitlink is valid and child commit is reachable.

Remaining HIGH — bootstrap common-config authority is still not causally frozen before its first Git observations:
- bootstrap `lstat`s `.git`/config and then separately `open(...).read()`s them; it does not use no-follow same-FD identity binding, retained `(dev,ino)`, or before/after bytes revalidation around `rev-parse`/`status`/`ls-tree`;
- linked-worktree common-dir authority is manually derived without proving the common directory itself is an absolute existing non-symlink directory inside the frozen repository authority;
- `<git_dir>/config.worktree` is still not required absent at the bootstrap boundary, although the approved v0.4 contract explicitly requires it;
- therefore a safe common config can be replaced after bootstrap admission but before native Git consumes it, recreating the raw-vs-effective-config authority gap.

Exact remediation:
1. before first bootstrap Git command, derive/freeze exact absolute `git_dir` and `git_common_dir` identities without unaudited Git config; prove existing non-symlink directories and frozen-authority containment;
2. require `<git_dir>/config.worktree` absent;
3. open `<git_common_dir>/config` with no-follow semantics, bind same-FD `(dev,ino)` + raw bytes, and parse the allowlist from those exact bytes;
4. immediately around first Git observations prove the path still resolves to the same identity/bytes, or otherwise force Git to consume only the already-admitted immutable config bytes; any drift fails before project import/ref/evidence/callback;
5. add isolated-bootstrap witnesses for config replacement after read/before Git view, common-dir/symlink escape, and pre-existing `config.worktree`.

Reported CPU/static passes and static checks are supportive but do not replace this missing causal witness.

Scope reminder: no real materialization, source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.