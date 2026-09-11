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

- immediate prior live blob SHA: `8d3659d2db54c649853ccc48ae88795f34ce12f6`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit CPU/static Implementation ancestor-symlink/matrix remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `12e07051ff74ecdb46d67aafdd9883eecfac8e7a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:283)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_12e0705_93a89ba.md`

Canonical review commit:
`292c3539025214a02d098073a59abb58aa16de4b`

Current blockers: `2 HIGH`: Production `1`; Evidence-only `1`; Design/Authority `0`.

Closure from prior review:
- ordinary existing-target ancestor-symlink HIGH is partially closed: root/child/output now walk the nearest existing component and parents, and direct tests cover symlinked parent components;
- shared failure evidence and single-bootstrap identity remain closed.

Remaining blockers:
1. Production HIGH: `path_arg()` uses `Path.exists()` to find the nearest existing component. Because `exists()` follows symlinks and returns false for dangling symlinks, a dangling symlink ancestor is skipped. This is especially unsafe for `--output`, which uses `resolve(strict=False)` and then discards the resolved path before `write_atomic()` operates on the original path. Detect symlink entries without following them across the lexical chain, including dangling ancestors, and return canonical operational FAIL / exit 3 before mutation.
2. Evidence-only HIGH: the suite is now 11 tests and adds useful ancestor-symlink plus representative config/source/Gitlink/tree negatives, but the approved direct-witness matrix is still materially incomplete. Missing families include publication path/blob type drift; Gitlink path/object drift; child tree drift; distinct raw tree/blob byte/length/SHA/record-digest drift; publication outer-key/schema/self-reference injection; fuller config/source missing/schema/value/type/digest variants; relative/child-worktree substitution; Git command failure/unexpected stdout; and exact success-only atomic replacement. Add direct parameterized witnesses with exact failed check/status/reason and zero output mutation where applicable.

Reported `11/11 PASS`, Ruff, py_compile and diff-check are supporting evidence only and do not close these gaps.

Still not authorized: real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
