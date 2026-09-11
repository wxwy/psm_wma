# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit CPU/static Implementation

**Date:** 2026-09-12  
**Formal root:** `12277d0649a2f886186f9bf7554231971e207836`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live Codex request ledger.
- Independently verified formal root `12277d0649a2f886186f9bf7554231971e207836` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The child is unchanged. Relative to the approved implementation-design formal `b29fdf7e71a0464e8678e0750871284ebd866f10`, the implementation adds exactly the approved two tooling files; SESSION/TODO and collaboration/review files are bookkeeping only.
- Reported `6/6 PASS`, Ruff, `py_compile`, and `git diff --check` are supporting evidence only; source behavior and the frozen direct-witness matrix remain authoritative.

## 2. Positive findings

- Bootstrap READY/FAIL and nullable pre-identity failure semantics are implemented.
- Git subprocesses use the frozen absolute `/usr/bin/git`, explicit sanitized environment, disabled replacement objects, `shell=False`, `text=False`, and raw object bytes for hashing.
- Publication raw bytes are required to equal the canonical JSON reserialization, so whitespace/key-order drift is fail-closed.
- The exact nested config/source schemas and compact 14-key audit record are implemented.
- Success output uses sibling temporary-file + `os.replace`; failure paths shown in `main()` do not intentionally write the requested output.
- No child/runtime/training code or real source-audit execution is introduced.

## 3. Formal verdict

`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:508)`

Current blockers: **3 HIGH**.  
Production blockers: **2**.  
Evidence-only blockers: **1**.  
Design/Authority blockers: **0**.

### HIGH-1 — Production — failure evidence uses a different `checks` object from the one updated by the audit

`main()` creates `checks = checks_template()` and keeps that object only for its eventual failure response. `audit()` independently creates its own second `checks` list, marks PASS rows on that local object, and then raises `AuditFailure` on the first failed validation. The exception carries only a reason string, not the active check name / observed record / updated checks state. Consequently `main()` serializes its untouched template: prior successful checks are lost, the actual failing step is not marked `FAIL`, and the result can be twelve `SKIPPED/NOT_REACHED` rows even after several verified object lookups.

This violates the frozen v0.2 evidence contract: prior checks must remain PASS, the first failed check must be FAIL with a stable reason/observed evidence, and only later checks may be SKIPPED. The current tests do not inspect this failure evidence path, so the defect is not exposed by `6/6 PASS`.

**Acceptance:** use one shared evidence state across `main()` and `audit()` (or return/raise a structured failure carrying the exact checks state). Every fallible audit stage must map to the frozen check name; on failure preserve prior PASS rows, mark exactly the current row FAIL with the stable reason and allowed observed fields, leave only subsequent rows SKIPPED, and serialize that exact state while preserving zero output mutation. Add direct negatives after multiple successful steps (for example noncanonical publication and missing/unreachable child commit) that assert the full ordered PASS/FAIL/SKIPPED sequence and reason codes.

### HIGH-2 — Production — success evidence re-bootstrap Git identity after all object lookups instead of binding the identity that authorized execution

`main()` establishes bootstrap READY and builds a full `command_identity`, but does not pass that identity into `audit()`. At success, `audit()` calls `bootstrap_git()` a second time and builds a new identity for the evidence. Therefore the emitted command identity is not necessarily the exact identity established before the audited Git commands ran. If the executable becomes unreadable/changes or the second bootstrap otherwise differs, the PASS artifact can contain an identity inconsistent with the execution that produced the audit record; `command_identity()` itself does not require bootstrap status READY.

That breaks the authority meaning of the command identity frozen in v0.2/v0.3: evidence must bind the trusted executable/version/environment/whitelist identity under which the object lookups actually occurred, not a newly sampled post-hoc identity.

**Acceptance:** bootstrap exactly once before any Git audit command; construct the full command identity once; pass that exact object into the audit/evidence builder and never call `bootstrap_git()` again on the success path. Add a direct witness that a second bootstrap cannot affect emitted evidence (or otherwise prove there is no second bootstrap), and assert the emitted identity is object/value-exact with the pre-audit identity.

### HIGH-3 — Evidence-only — the approved direct-witness matrix is materially incomplete

The approved v0.1 implementation design requires direct temporary-fixture witnesses for root/child object type drift; Gitlink mode/path/object drift; child reachability/tree drift; publication path/blob type/missing/extra-entry cases; raw tree/blob byte/length/digest drift; publication/config/source missing/unknown/type/value/hex/digest drift; relative/symlink escape; child HEAD/worktree substitution; Git command failure/unexpected output; plus the v0.2 hostile environment set including alternate object directories and replacement refs.

Current six tests cover one valid case, noncanonical publication plus uppercase revision, a limited hostile environment (`GIT_DIR`, `GIT_OBJECT_DIRECTORY`, config alias injection), bootstrap failures, and a direct root symlink. They do not directly witness most of the frozen matrix, do not assert the failure checks/reasons schema for ordinary validation failures, do not exercise alternate-object / replace-ref hostile inputs, and the test named `test_symlink_root_and_child_substitution_fail` only tests the root symlink.

**Acceptance:** expand the temporary-fixture suite to cover the frozen negative matrix from approved implementation-design v0.1 plus the v0.2/v0.3 remediation witnesses. Parameterization/helper fixtures are fine; the requirement is direct causal coverage, not test count. In particular include ordered failure-evidence assertions, child symlink/substitution, alternate-object and replace-ref hostile environment, Gitlink mode/path/object negatives, child reachability/tree negatives, publication/config/source schema/type/digest negatives, and Git command failure/unexpected-output negatives.

## 4. Scope

This review does **not** authorize real root publication/source-audit execution, production `root_gitlink_authority_v1` runtime integration, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference, or LIBERO4IN1. Remediation should remain in the already-approved two root tooling files; bookkeeping may update root status docs only.
