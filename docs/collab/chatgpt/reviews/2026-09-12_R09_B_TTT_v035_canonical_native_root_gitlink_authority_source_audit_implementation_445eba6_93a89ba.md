# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation closure remediation

**Date:** 2026-09-12  
**Formal root:** `445eba6c14cb484dd113b2994ceee07822bcec69`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2`, re-read the live Codex request ledger, and verified the exact request pair and Gate.
- Independently verified formal root `445eba6c14cb484dd113b2994ceee07822bcec69` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The remediation remains within the approved root tooling scope. Child is unchanged; no real root source-audit execution, production authority runtime integration, checkpoint/data/cache I/O, GPU/native workload or training is authorized.
- Prior formal `661786fc3e944348998745240b24f6c6f65a1d8a` had three HIGHs: non-finite JSON could escape canonical failure handling, malformed `rev-parse` output could be normalized/raise raw decode errors, and direct witnesses for those two failure families were missing.

## 2. Findings

### Prior Production HIGH — non-finite publication JSON: CLOSED

`validate_publication()` now uses `json.loads(..., parse_constant=...)` to reject `NaN`, `Infinity`, and `-Infinity` as typed `AuditFailure("PUBLICATION_NONFINITE")`. It also catches canonical encoder `TypeError`/`ValueError` and maps them to the same fail-closed reason. Direct CLI-level witnesses exercise all three non-finite tokens and assert exact failed check, ordered PASS/FAIL/SKIPPED evidence, exit `2`, and unchanged output bytes.

### Prior Production HIGH — malformed `rev-parse` output: CLOSED

`parse_revision_output()` now requires exactly 41 bytes, exactly one trailing newline, strict ASCII decode, and exact 40-lowercase-hex content. Root and child tree resolution both route through this helper and use stable reasons `ROOT_TREE_OUTPUT` / `CHILD_TREE_OUTPUT`. Direct witnesses cover extra-newline and non-ASCII root/child `rev-parse` outputs and assert ordered failure evidence plus zero output mutation.

### Prior Evidence-only HIGH — direct witnesses for the above: CLOSED

The temporary-fixture suite now contains direct CLI witnesses for all non-finite publication cases and malformed/non-ASCII root/child tree revision outputs. These specific prior evidence gaps are closed.

### HIGH-1 — Production — malformed non-ASCII `ls-tree` OID can still escape as raw `UnicodeDecodeError`

`parse_ls_tree()` validates the OID using `oid.decode("ascii", "ignore")` and only after that returns `oid.decode("ascii")` with strict decoding. A malformed OID field such as forty valid lowercase hex ASCII bytes followed by a non-ASCII byte passes the first validation because the non-ASCII byte is silently dropped by `errors="ignore"`; the final strict decode then raises raw `UnicodeDecodeError` outside the `AuditFailure` protocol.

That violates the frozen fail-closed rule that malformed/unexpected Git stdout must produce deterministic validation FAIL, stable reason, canonical failure JSON, and no output mutation.

**Acceptance:** decode the OID exactly once with strict ASCII handling inside a typed `AuditFailure` boundary, require exact 40-byte lowercase hex content with no ignored bytes, and add direct root Gitlink/publication `ls-tree` malformed non-ASCII/extra-byte witnesses proving exact failed check/reason, exit `2`, ordered evidence, and unchanged output.

### HIGH-2 — Production — atomic output I/O operational failures are not converted to canonical exit-3 failure

`write_atomic()` performs `output.parent.mkdir(...)`, `NamedTemporaryFile(...)`, writes canonical bytes, and `os.replace(...)`, but it lets `OSError` propagate. `main()` catches only `AuditFailure`, so operational failures such as an unwritable parent, temp-file creation failure, write failure, or replace failure can terminate with a raw Python exception instead of the exact `root_gitlink_source_audit_failure_v1` stdout contract and exit `3`.

The approved implementation design explicitly freezes `exit 3 = operational/unsupported invocation FAIL` and requires failure-no-output-mutation. This implementation therefore remains incomplete on the output-commit boundary even though the success path is atomic.

**Acceptance:** wrap all output-commit operational errors into a stable operational `AuditFailure` reason before they escape `main()`, preserve any pre-existing output byte-for-byte, clean temporary files, emit the canonical failure JSON with exit `3`, and add deterministic direct witnesses for temp/write/replace failure seams.

### HIGH-3 — Evidence-only — the two new fail-closed boundaries are not directly witnessed

The current suite directly exercises the prior non-finite and malformed `rev-parse` regressions, but it does not witness the malformed non-ASCII/extra-byte `ls-tree` OID case above or any output-commit `OSError` seam. Therefore the frozen unexpected-output and operational-failure contracts remain unproven for these reachable branches.

**Acceptance:** add direct temporary-fixture or deterministic mocked-seam tests for both production findings, asserting exact failed check/status/reason where applicable, exact exit code, canonical stdout schema, zero output mutation, and temporary-file cleanup.

## 3. Formal verdict

`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:327)`

Current blockers: **3 HIGH**.  
Production blockers: **2**.  
Design/Authority blockers: **0**.  
Evidence-only blockers: **1**.

## 4. Scope

No real root source-audit execution is authorized. Real publication/checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, runtime integration, training, evaluation, inference and LIBERO4IN1 remain forbidden. Remediation should remain inside the already-approved two root tooling files plus normal review/bookkeeping persistence.
