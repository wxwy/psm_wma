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

- immediate prior live blob SHA: `49f61dc4ef0645b2dd6555ccac3af7d29732376b`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit CPU/static Implementation closure remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `661786fc3e944348998745240b24f6c6f65a1d8a`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:347)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_661786f_93a89ba.md`

Canonical review commit:
`84737ede6798377bc3333543c7c2641e52da2166`

Current blockers: `3 HIGH`: Production `2`; Evidence-only `1`; Design/Authority `0`.

Closure from prior review:
- dangling ancestor symlink HIGH is CLOSED: root/child/output now inspect the original lexical path chain directly, including dangling symlink ancestors, and `main()` writes via the validated/resolved output path;
- the prior broad negative-matrix HIGH is substantially closed: the suite now directly exercises config/source key/type/value/digest families, publication/path/type/schema families, raw tree record coupling, root/child unexpected command output, child worktree/tree drift, hostile Git environment, ordered failure evidence, and atomic success replacement.

Remaining blockers:
1. Production HIGH: `validate_publication()` accepts Python `json.loads()` non-standard `NaN`/`Infinity` values, then `canonical_bytes(... allow_nan=False)` raises native `ValueError`. This escapes the approved canonical failure JSON / exit-2 path instead of deterministic fail-closed evidence. Reject non-finite JSON as typed `AuditFailure` and add CLI-level direct witnesses for `NaN`, `Infinity`, and `-Infinity` with zero output mutation.
2. Production HIGH: root/child `rev-parse` output is parsed with `.rstrip(b"\n").decode("ascii")`; extra trailing newlines can be silently normalized and non-ASCII can raise native `UnicodeDecodeError` outside `guarded()`. Require exact `40 lowercase hex + single newline` bytes and map all malformed/extra/non-ASCII output to stable `AuditFailure` reasons.
3. Evidence-only HIGH: add direct root and child malformed/extra/non-ASCII `rev-parse` witnesses plus non-finite publication witnesses, asserting exact failed check/reason, ordered PASS/FAIL/SKIPPED evidence, exit 2, and unchanged output.

Reported `16/16 PASS`, Ruff, py_compile and diff-check are supporting evidence only and do not close these remaining source/evidence gaps.

Still not authorized: real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
