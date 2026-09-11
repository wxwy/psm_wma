# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation closure remediation

**Date:** 2026-09-12  
**Formal root:** `661786fc3e944348998745240b24f6c6f65a1d8a`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2` and independently verified formal root `661786fc3e944348998745240b24f6c6f65a1d8a` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Remediation remains substantively in the approved root tooling implementation. Child is unchanged.
- Prior formal `12e07051ff74ecdb46d67aafdd9883eecfac8e7a` had two HIGHs: dangling ancestor symlink handling and incomplete direct negative witness matrix.

## 2. Findings

### Prior Production HIGH — dangling ancestor symlink handling: CLOSED

`path_arg()` now walks the original absolute lexical chain directly (`value`, then all parents) and tests `is_symlink()` on every component, avoiding the prior `exists()` behavior that skipped dangling symlinks. `main()` also uses the validated/resolved output path returned by `path_arg()` for the atomic write. Direct fixtures now cover relative paths plus root/child/output dangling ancestor symlinks.

### Prior Evidence-only HIGH — negative matrix: substantially improved, but not fully closed

The suite is materially stronger: it now covers every config key missing, config bool/type/value families, source key/schema/type/hex families, publication outer-key/schema/noncanonical JSON, publication path/type/multi-entry parser failures, raw tree byte/length/record-digest coupling, root/child unexpected `cat-file -e` output, child tree OID drift, root tree type drift, child worktree substitution, ordered PASS/FAIL/SKIPPED evidence, hostile caller Git environment, bootstrap failures, and atomic success replacement.

However, two source fail-closed behaviors remain uncovered and are not contract-correct, so the evidence Gate cannot close yet.

### HIGH-1 — Production — non-finite JSON can escape the canonical failure contract

`validate_publication()` uses Python `json.loads(raw)`, which accepts non-standard `NaN` / `Infinity` tokens by default. It then calls `canonical_bytes(data)`, whose `json.dumps(..., allow_nan=False)` raises a native `ValueError` for those non-finite values. `validate_publication()` catches only `UnicodeDecodeError` / `JSONDecodeError`, and `guarded()` catches only `AuditFailure`.

Therefore a publication containing a non-finite number can escape the approved fail-closed path as an uncaught Python exception instead of deterministic `PUBLICATION_*` / validation FAIL evidence with exit 2 and zero output mutation. This violates the approved source-audit design's explicit non-finite rejection rule.

**Acceptance:** make JSON decoding/canonicalization reject `NaN`, `Infinity`, and `-Infinity` as a typed `AuditFailure` before authority production. Add direct CLI-level temporary-fixture witnesses proving exact failed check/reason, exit 2, ordered evidence, and unchanged output for each non-finite case.

### HIGH-2 — Production — `rev-parse` output is not exact single-line fail-closed

Root and child tree OIDs are decoded via `run_git(... rev-parse ...).rstrip(b"\n").decode("ascii")`. This silently normalizes extra trailing newlines (e.g. `oid + "\n\n"`) and the ASCII decode sits outside `guarded()`, so non-ASCII output can raise native `UnicodeDecodeError` rather than `AuditFailure`.

The implementation design requires unexpected/extra stdout to FAIL and the exact evidence/failure schema to remain canonical. `cat-file -e` unexpected stdout is tested, but `rev-parse` output is not validated as exact `40-lowerhex + one newline`.

**Acceptance:** parse root/child `rev-parse` output with one exact helper that requires byte-for-byte `40 lowercase hex + "\n"`, maps all malformed/non-ASCII/extra-output cases to stable `AuditFailure` reason codes, and add direct root and child temporary-fixture witnesses asserting ordered evidence, exit 2, and zero output mutation.

### HIGH-3 — Evidence-only — witnesses do not cover the two remaining fail-closed families above

The reported `16/16 PASS` is useful supporting evidence, and the previous matrix gap is mostly closed. But there is no direct witness for publication non-finite JSON or for malformed/extra/non-ASCII root/child `rev-parse` stdout. Because both are currently source-behavior gaps, the frozen direct-evidence contract remains incomplete.

**Acceptance:** add the direct witnesses described above; rerun target unittest, Ruff, `py_compile`, and `git diff --check`.

## 3. Formal verdict

`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:347)`

Current blockers: **3 HIGH**.  
Production blockers: **2**.  
Design/Authority blockers: **0**.  
Evidence-only blockers: **1**.

## 4. Scope

No real root source-audit execution is authorized. Real publication/checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, runtime integration, training, evaluation, inference and LIBERO4IN1 remain forbidden. Remediation should stay within the approved two root tooling files plus normal review/bookkeeping persistence.
