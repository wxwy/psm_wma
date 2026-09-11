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

- immediate prior live blob SHA: `a75c0373ddef3dd227327cb3b8c94528ec79f757`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit CPU/static Implementation closure remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `c8cecddf0c0eb2c2b1da6fb4e045e6789970144a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:283)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_c8cecdd_93a89ba.md`

Canonical review commit:
`7ad81b10a994cf9e035bd176dc6e349e32aacc99`

Current blockers: `2 HIGH`: Production `1`; Evidence-only `1`; Design/Authority `0`.

Closure from prior review:
- shared failure evidence HIGH is CLOSED: `main()` and `audit()` now share the exact checks object and direct tests prove prior PASS / current FAIL / later SKIPPED ordering for publication failure and unreachable child;
- single-bootstrap identity HIGH is CLOSED: bootstrap and command identity are established once before audit and passed unchanged into success evidence; direct witness asserts one bootstrap call.

Remaining blockers:
1. Production HIGH: `path_arg()` only checks whether the terminal path itself is a symlink, then calls `resolve(strict=True)`. A path with a symlinked parent component is accepted, so the approved `symlink escape => FAIL` contract is not satisfied. `--output` has the same parent-symlink redirection gap because only the leaf is checked before atomic write. Validate the full path chain / containment semantics and add ancestor-symlink negatives for root, child Git dir, and output.
2. Evidence-only HIGH: the suite is now 9 tests but still omits most of the approved direct-witness matrix: root/child object type drift; Gitlink mode/path/object drift; child tree drift; publication path/blob type drift; raw tree/blob byte/length/SHA/record-digest drift; publication outer-key/schema/self-reference injection; config/source missing/unknown/type/value/hex/digest drift; relative path, child HEAD/worktree substitution, Git command failure/unexpected output, and exact success-only atomic-replacement witnesses. Add direct parameterized coverage with exact failure check/status/reason and zero output mutation.

Reported `9/9 PASS`, Ruff, py_compile and diff-check are supporting evidence only and do not close the above contract gaps.

Still not authorized: real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
