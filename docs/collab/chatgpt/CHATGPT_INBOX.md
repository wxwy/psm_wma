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

- immediate prior live blob SHA: `d8f5a43a23995e372b92ec0cbf36b48770b41614`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Stage-1 v1.7 launcher replay no-I/O remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `467e6665b95be450ca5900c6aa6ce14e94f759d5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-STAGE1-V17-LAUNCHER-FREEZE-DESIGN`

Verdict:
`REQUEST_CHANGES(tools/psm_wma/stage1_v17_launcher_replay.py:55)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-14_R09_B_TTT_v035_stage1_v17_launcher_replay_no_io_remediation_467e666_93a89ba.md`

Canonical review commit:
`2914070672a4249ea4644fa9073e64cf14b86ec6`

Current blockers: `1 HIGH`; Design/Authority: `0`; Production/Authority: `1 HIGH`; Evidence/Scope: `0`; child/runtime: `0`.

Closed in this remediation:
1. The canonical witness is now fully self-contained and no-I/O: the exact frozen 18966-byte launcher base is embedded in the approved test file as gzip/base64 bytes, decoded in memory, and asserted against `18966 / 8b0fad39857fb72e3a3eb317f4acf6f2d6e94e196935f52f07d6170e79c678dd` before replay.
2. No `subprocess`, `git show`, real repository path, Git/path/FD/network/exec I/O is used by the canonical witness.
3. The complete canonical parser table and 8-item source table remain, with direct parser `2336 / 1a9543ec3e7ef4f37b4948dde2a6a9532b13a8415291cceafd90b9692c028333` and outer `18875 / 658e9b9e6f34964310d6e2a5519c3b70243971b5ef535d753192e3d59d1960b8` assertions.
4. Parser table order enforcement remains present; reordered targets fail `parser_target`.
5. Formal root changes only the two approved implementation/test files; Gitlink resolves exactly to reachable child `93a89ba...`; child/runtime production bytes are unchanged.

Remaining HIGH — self-check target is token-anchored but not function/span-anchored:
- `_replace_once()` now constructs `prefix + old + suffix` for the four self-check rows and requires that token exactly once, which closes the prior naked-global-string issue.
- However the immediately prior canonical review explicitly requires relocated contexts to fail `source_target`, and v0.4 binds the first two rows specifically to `boot(s)` and the latter two specifically to `main()`.
- The current helper searches the exact token across the entire source. If the whole frozen token is moved byte-for-byte outside its intended function/region, the global token count still succeeds and the helper replaces it. A later final hash may fail as `replay_drift`, but the target authority itself has not failed closed as required.

Exact remediation:
1. Keep the public API, embedded canonical base, parser ordering, owner-FD handling, complete canonical tables, and exact parser/outer identity witness unchanged.
2. Bind each self-check target to its frozen function/span (`boot(s)` for bootstrap length/SHA; `main()` for RAW[2] length/SHA), via AST/function-region boundaries or an equivalent frozen region-aware mechanism.
3. Require exact-one target inside that region; an unchanged token relocated outside the region must fail `BLOCKED_AUTHORITY_NOT_CLOSED:source_target`.
4. Add a direct relocation negative while preserving the existing altered/missing/duplicate/source/parser/base/owner-FD negatives.
5. `py_compile`, direct unittest, and `git diff --check` must pass under the existing no-I/O boundary.

Scope reminder: no implementation closure, no v1.7 request construction, no Stage-1 retry/materialization, no source/checkpoint/data/cache I/O, child/runtime mutation, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized. v1.6 authority remains consumed.

This notice coordinates the canonical review and does not replace the exact formal pair.
