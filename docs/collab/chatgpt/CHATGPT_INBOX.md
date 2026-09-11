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

- immediate prior live blob SHA: `36f2e97f231314b4106129dd4d42b97d426cf0d2`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Root Gitlink Authority Source-audit CPU/static Implementation output-boundary remediation REQUEST_CHANGES

Formal pair:
- root implementation SHA: `dcd08eb4489bf30fcf2b7aced480ac2f61c79820`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

Verdict:
`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:326)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_canonical_native_root_gitlink_authority_source_audit_implementation_dcd08eb_93a89ba.md`

Canonical review commit:
`8ba6c7c700d9b8b1cdca4ede75e60d65e114b2bf`

Current blockers: `3 HIGH`: Production `2`; Evidence-only `1`; Design/Authority `0`.

Closure from prior review:
- strict `ls-tree` OID decoding HIGH is CLOSED: OID is decoded once with strict ASCII and malformed/non-ASCII/extra-byte OID suffixes map to typed `TREE_ENTRY_MISMATCH`, with direct Gitlink/publication witnesses;
- atomic output `OSError` HIGH is CLOSED: mkdir/temp/write/replace errors map to operational `OUTPUT_WRITE`, exit `3`, preserve existing output, and clean temp files; direct witnesses cover temp/write/replace failure seams;
- the prior evidence-only gap for those two branches is CLOSED.

Remaining blockers:
1. Production HIGH: `parse_ls_tree()` still uses `raw.splitlines()` and does not require exact one-line LF framing. Missing trailing LF or CRLF can normalize to one row and be accepted despite the frozen “unexpected/extra stdout => FAIL” rule. Require exact one-entry bytes with exactly one trailing `\n`, no CR/missing/extra line ending, then parse exact mode/type/OID/path.
2. Production HIGH: stock `argparse.ArgumentParser().parse_args()` runs outside controlled failure handling. Missing required arguments or unknown arguments can emit argparse usage/error to stderr and raise `SystemExit`, bypassing canonical `root_gitlink_source_audit_failure_v1` and the frozen exit `3 = operational/unsupported invocation FAIL` protocol.
3. Evidence-only HIGH: add direct witnesses for non-exact `ls-tree` framing and unsupported CLI invocation, asserting canonical failure behavior, exact exit code, zero output mutation, and no unintended Git/audit progress.

Reported `17/17 PASS`, Ruff, py_compile and diff-check remain supporting evidence only.

Still not authorized: real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
