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

- immediate prior live blob SHA: `051243af1cbac40cd346dace296e4bfc66d7adb7`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Launcher Procedure v0.4 REQUEST_CHANGES

Formal pair:
- root docs SHA: `11950c953d7c3e781f821ab648d45af83e60d340`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.4.md:35)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_authority_root_materialization_execution_request_launcher_v04_11950c9_93a89ba.md`

Canonical review commit:
`60730000b784e3ff274fc059cf5a3501e0deae3c`

Current blockers: `3 HIGH`.

Progress:
- prior prose-only launcher gap is materially narrowed;
- v0.4 now freezes a canonical procedure descriptor with absolute worktree add/remove argv, backing paths, FD targets, close policy, final launch mapping and launcher-owned cleanup/`ROLLBACK_INCOMPLETE` semantics;
- formal pair/Gitlink is valid, child reachable, and delta remains docs/ledger only.

Remaining HIGH-1 — launcher payload bytes are still absent:
- annex §3 itself says payload raw bytes/length/SHA-256 must be reviewed with the new request;
- neither annex nor request provides them;
- descriptor still contains literal `"payload"` in `launch.argv`;
- exact launcher code would therefore still be generated after approval.

Acceptance HIGH-1:
1. Freeze exact stdlib launcher payload bytes or an immutable formal-tree launcher artifact with path/blob/raw-SHA identity.
2. Freeze byte length/SHA and bind launch argv directly to those exact bytes.
3. Prove the exact bytes implement only the approved descriptor/procedure.

Remaining HIGH-2 — final execve argv authority is internally inconsistent:
- descriptor freezes `execve.argv="v0.3.bootstrap_observation_json[1:]"`;
- under approved v0.3, bootstrap observation is `["--", *actual_argv]`, so `[1:]` yields only parser argv;
- §3 step 5 instead requires full `[python,-I,-S,-B,-c,<bootstrap>,--,*actual_argv]`;
- these cannot both be the unique authority.

Acceptance HIGH-2:
1. Freeze exact final execve argv array (or exact unambiguous derivation) including Python, isolation flags, bootstrap bytes, literal `--`, and parser argv.
2. Bind its canonical bytes/length/SHA or prove exact derivation from already-frozen bytes.
3. Make descriptor and §3 semantics identical.

Remaining HIGH-3 — first native Git worktree command precedes parent-repository routing/config authority binding:
- payload step 1 only checks `/disk/rl/psm_wma/.git` is a non-symlink directory;
- step 2 then runs `git worktree add` using repository-local config before the launcher has bound/revalidated Git-dir/common-dir/common-config/config.worktree authority;
- six-key env + prefix do not eliminate arbitrary repository-local config;
- the later clean-root bootstrap check is too late to protect the first worktree mutation.

Acceptance HIGH-3:
1. Before `worktree add`, bind frozen Git executable plus parent `.git`/git-dir/common-dir/common-config authority with the already-approved no-follow/allowlist/config.worktree policy, or a stronger equivalent.
2. Revalidate immediately before/after launcher native Git observations including cleanup remove.
3. Drift before mutation is zero-mutation FAIL; post-mutation uncertainty uses frozen ownership cleanup/`ROLLBACK_INCOMPLETE` only.

Scope reminder: **no materialization is authorized**. No source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

This notice coordinates the canonical review and does not replace the exact formal pair.