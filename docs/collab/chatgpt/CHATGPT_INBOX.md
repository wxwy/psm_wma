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

- immediate prior live blob SHA: `335dbb51f2fbd3cd1f60ca3ed6bff9ccff626722`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit CPU/static Implementation malformed-output remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `445eba6c14cb484dd113b2994ceee07822bcec69`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:327)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_445eba6_93a89ba.md`

Canonical review commit:
`096763ce146f87fb5091a18b49c87f4a952471ad`

Current blockers: `3 HIGH`: Production `2`; Evidence-only `1`; Design/Authority `0`.

Closure from prior review:
- non-finite publication JSON HIGH is CLOSED: `NaN`/`Infinity`/`-Infinity` now map to typed `PUBLICATION_NONFINITE`, with direct CLI witnesses and zero output mutation;
- malformed root/child `rev-parse` HIGH is CLOSED: exact 40-lowercase-hex ASCII + one newline is required, with direct extra-newline/non-ASCII witnesses;
- the prior direct-witness gap for those two families is CLOSED.

Remaining blockers:
1. Production HIGH: `parse_ls_tree()` validates with `oid.decode("ascii", "ignore")` and later returns `oid.decode("ascii")`. A malformed OID containing forty valid lowercase-hex ASCII bytes plus a non-ASCII byte can pass the ignored-byte validation and then raise raw `UnicodeDecodeError`, escaping canonical failure handling. Decode exactly once with strict ASCII inside `AuditFailure`, require exact 40-byte lowercase hex, and directly witness malformed/non-ASCII/extra-byte `ls-tree` OIDs.
2. Production HIGH: `write_atomic()` lets mkdir/temp-file/write/`os.replace` `OSError` escape, while `main()` catches only `AuditFailure`. Operational output-commit failures must become stable operational `AuditFailure`, canonical failure JSON, exit `3`, with pre-existing output preserved and temporary files cleaned.
3. Evidence-only HIGH: add direct witnesses for both boundaries above, asserting exact failure schema/check/reason where applicable, exit code, zero output mutation, and temporary-file cleanup.

Reported `16/16 PASS`, Ruff, py_compile and diff-check remain supporting evidence only.

Still not authorized: real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
