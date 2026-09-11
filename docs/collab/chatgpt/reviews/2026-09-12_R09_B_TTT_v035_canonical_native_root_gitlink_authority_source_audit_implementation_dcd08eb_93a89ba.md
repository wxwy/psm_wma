# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation closure remediation

**Date:** 2026-09-12  
**Formal root:** `dcd08eb4489bf30fcf2b7aced480ac2f61c79820`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2`, re-read the live Codex request ledger, and independently verified formal root `dcd08eb4489bf30fcf2b7aced480ac2f61c79820` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Remediation remains in the approved two root tooling files; child is unchanged. SESSION/TODO/collaboration changes are bookkeeping only.
- Prior formal `445eba6c14cb484dd113b2994ceee07822bcec69` had three HIGHs: malformed/non-ASCII `ls-tree` OID could escape as raw decode error, atomic output `OSError` could escape canonical operational failure, and those two branches lacked direct witnesses.
- No real root source-audit execution, publication/runtime authority integration, checkpoint/data/cache I/O, GPU/native workload, training/evaluation/inference, or LIBERO4IN1 is authorized by this review.

## 2. Findings

### Prior Production HIGH — strict `ls-tree` OID decode: CLOSED

`parse_ls_tree()` now strictly decodes the OID once with ASCII and maps decode failure to typed `AuditFailure("TREE_ENTRY_MISMATCH")`. It then requires exact 40-lowercase-hex content. Direct Gitlink/publication witnesses cover non-ASCII and extra-byte OID suffixes with ordered failure evidence, exit `2`, and unchanged output.

### Prior Production HIGH — atomic output operational errors: CLOSED

`write_atomic()` now maps mkdir/temp-file/write/`os.replace` `OSError` to operational `AuditFailure("OUTPUT_WRITE")`, and temp cleanup is attempted in `finally`. Direct deterministic witnesses exercise temp-file creation, write, and replace failure seams and assert canonical failure schema, exit `3`, preserved pre-existing output, and no surviving sibling temp file.

### Prior Evidence-only HIGH — direct witnesses for the above: CLOSED

The suite now directly exercises both prior production findings. The specific prior evidence gap is closed.

### HIGH-1 — Production — `ls-tree` framing is still not exact, so malformed/missing-line-ending stdout can be accepted

The frozen implementation design states that unexpected/extra Git stdout must FAIL and requires the fixed Gitlink/publication tree entry to be exact. `parse_ls_tree()` currently uses `raw.splitlines()` and validates the resulting row fields, but it does not require the raw command output itself to end in exactly one `\n` byte. Therefore both a row with no trailing newline and a CRLF-terminated row can normalize to one logical line and be accepted even though they are not the exact expected Git stdout framing.

This is inconsistent with the exact-output discipline already applied to `rev-parse`, `cat-file -t/-s`, and `cat-file -e`, and violates the approved “unexpected output => FAIL” contract.

**Acceptance:** require `ls-tree` stdout to be exact one-entry bytes with exactly one trailing LF and no CR/extra line ending or missing newline before field parsing. Preserve the existing exact mode/type/path/OID checks. Add direct Gitlink and publication witnesses for missing trailing LF, CRLF, and extra line ending, asserting exact failed check/reason, exit `2`, ordered PASS/FAIL/SKIPPED evidence, and unchanged output.

### HIGH-2 — Production — CLI parse errors bypass the canonical failure protocol

`main()` uses a stock `argparse.ArgumentParser()` and calls `parse_args()` before any controlled failure handling. Missing required arguments, unknown arguments, or malformed invocation therefore trigger argparse's own `SystemExit` and usage/error text on stderr. They do not emit the frozen canonical `root_gitlink_source_audit_failure_v1` JSON and do not use the approved exit `3 = operational/unsupported invocation FAIL` path.

The approved implementation design requires the CLI to provide the exact four arguments and freezes operational/unsupported invocation failures as canonical exit-3 failures. Current argument parsing is therefore outside the fail-closed contract.

**Acceptance:** make CLI parse/unsupported-invocation failures deterministic and canonical: no argparse-owned stderr/usage escape, canonical failure JSON on stdout, exit `3`, zero output mutation, and no Git/audit execution. Preserve normal `--help` only if explicitly frozen; otherwise route it consistently as unsupported invocation. Add direct witnesses for at least missing required argument and unknown argument.

### HIGH-3 — Evidence-only — the two remaining boundary families are not directly witnessed

The reported `17/17 PASS` suite covers the prior malformed-OID and output-I/O failures, but it does not directly test non-exact `ls-tree` line framing or argparse missing/unknown-argument behavior. Therefore the frozen unexpected-output and unsupported-invocation contracts remain unproven on reachable branches.

**Acceptance:** add direct temporary-fixture or CLI-level witnesses for both findings above, asserting canonical failure schema, stable reason/check when applicable, exact exit code, no stderr escape where the contract forbids it, zero output mutation, and zero unintended Git/audit progress.

## 3. Formal verdict

`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:326)`

Current blockers: **3 HIGH**.  
Production blockers: **2**.  
Design/Authority blockers: **0**.  
Evidence-only blockers: **1**.

## 4. Scope

No real root source-audit execution is authorized. Real publication/checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, runtime integration, training, evaluation, inference and LIBERO4IN1 remain forbidden. Remediation should remain inside the already-approved two root tooling files plus normal review/bookkeeping persistence.
