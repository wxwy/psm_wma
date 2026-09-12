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

- immediate prior live blob SHA: `20e90b94028fcba434342dd2fe72c7c07255470d`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Authority-root Execution Authority CPU/static Remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `817191c91ae8c8eb7e1a66f15055d2286d0b76c4`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:177)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_authority_root_execution_authority_cpu_static_implementation_817191c_93a89ba.md`

Canonical review commit:
`35aa349a24916b0fd301e870ebc8070347bc4651`

Current blockers: `1 HIGH`.

Closure/progress:
- executable identity is CLOSED: interpreter/Git type, non-symlink, raw SHA and exact version are all checked before project import;
- common config now uses an `O_NOFOLLOW` retained FD, frozen `(dev,ino,size)` and raw bytes, and those bytes drive the bootstrap allowlist;
- the config pathname identity/FD bytes are rechecked before each bootstrap Git call;
- a pre-existing normal-worktree `.git/config.worktree` witness is present;
- formal root/Gitlink is valid and the child commit is independently reachable.

Remaining HIGH — linked-worktree/effective common-config authority is still incomplete:
- when `.git` is a linked-worktree marker file, the resolved per-worktree Git dir is `gd`, but bootstrap checks `wcfg = os.path.join(admin,'config.worktree')`; `admin` is the marker file path, so this does not inspect the real `<git_dir>/config.worktree`;
- linked-worktree common dir is assumed as `dirname(dirname(gd))` instead of being bound through the actual `commondir` authority or an exact equivalent;
- `grun()` checks config identity/bytes only before `subprocess.run`; Git then reopens the config path and there is no post-call identity/bytes revalidation, leaving a replacement window between admission and effective Git consumption;
- the new `config.worktree` witness covers only a normal worktree and therefore does not prove the v0.4 linked/detached-worktree contract.

Exact remediation:
1. in linked worktrees, bind the real worktree Git dir separately from the `.git` marker and derive the common Git dir through the authoritative `commondir` relation (or an equally exact no-config-dependent mechanism), with absolute existing non-symlink directory checks;
2. require the actual `<git_dir>/config.worktree` absent before the first bootstrap Git observation and add a direct linked/detached-worktree witness for it;
3. retain the no-follow common-config FD but revalidate pathname identity and FD bytes after each native Git bootstrap observation as well as before it, or otherwise guarantee Git can consume only the admitted immutable config bytes;
4. add a direct race witness replacing common config after the precheck but before/during Git consumption and prove rejection before project import/ref/evidence/callback;
5. preserve all closed executable/module/endpoint/no-replace/Evidence/CAS/CPU-static contracts.

Reported test/static passes remain supportive only; they do not replace the missing linked-worktree and post-consumption causal witnesses.

Scope reminder: no real materialization, source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.

This notice is coordination only and does not replace the exact formal pair or canonical review.