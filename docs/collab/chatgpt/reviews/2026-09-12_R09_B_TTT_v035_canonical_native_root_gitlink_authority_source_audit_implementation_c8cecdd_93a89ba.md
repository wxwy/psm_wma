# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation closure remediation

**Date:** 2026-09-12  
**Formal root:** `c8cecddf0c0eb2c2b1da6fb4e045e6789970144a`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live Codex request ledger.
- Independently verified formal root `c8cecddf0c0eb2c2b1da6fb4e045e6789970144a` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Remediation remains within the approved root tooling scope; child is unchanged. The substantive implementation files remain `tools/g0/audit_r09_b_ttt_root_gitlink_authority.py` and `tools/g0/test_audit_r09_b_ttt_root_gitlink_authority.py`; SESSION/TODO/collaboration files are bookkeeping only.
- Prior formal `12277d0649a2f886186f9bf7554231971e207836` had three HIGHs: shared failure evidence, single bootstrap identity, and incomplete direct witness matrix.

## 2. Findings

### Prior Production HIGH — failure evidence state: CLOSED

The remediation now passes one shared `checks` object from `main()` into `audit()`. `guarded()` marks the exact active check `FAIL`, attaches the same state to the raised `AuditFailure`, and `main()` emits `getattr(exc, "checks", checks)`. Direct tests now verify both publication failure and child-unreachable ordering as prior PASS / current FAIL / remaining SKIPPED.

### Prior Production HIGH — single bootstrap identity: CLOSED

`main()` performs bootstrap once, constructs one `root_gitlink_git_command_identity_v1`, passes it into `audit()`, and success evidence carries that exact identity. The previous second `bootstrap_git()` call inside `audit()` has been removed; a direct test asserts one bootstrap invocation.

### HIGH-1 — Production — ancestor symlink escape remains accepted

`path_arg()` rejects only `value.is_symlink()` on the terminal path component and then calls `value.resolve(strict=True)`. An absolute path whose parent directory is a symlink but whose leaf is not a symlink therefore resolves and is accepted. The approved implementation design explicitly requires any symlink escape to FAIL; this implementation only proves the leaf-symlink case.

The same structural issue also matters for `--output`: `main()` checks only whether the output leaf itself is a symlink before `write_atomic()` operates through its parent path. A symlinked parent can redirect the supposedly absolute output path.

**Acceptance:** validate the full path chain for root, child Git dir, and output against symlink traversal/escape before any Git lookup or output mutation. Add direct temporary-fixture witnesses using a symlinked parent component (not merely a symlink leaf) for root/child/output, proving deterministic operational FAIL and unchanged/non-created output.

### HIGH-2 — Evidence-only — approved direct negative witness matrix remains materially incomplete

The design requires direct temporary-fixture witnesses for, at minimum: root/child object type drift; Gitlink mode/path/object drift; child reachability/tree drift; publication path/blob type drift; raw tree/blob byte/length/SHA/record-digest drift; publication outer-key/schema/self-reference injection; config 15-key and source five-key missing/unknown/type/value/hex/digest drift; relative/symlink-escape paths; child HEAD/worktree substitution; Git command failure/unexpected output; and success-only atomic replacement.

The remediation increases the suite from 6 to 9 tests and adds valuable checks for ordered failure evidence, unreachable child, alternate-object/replace hostile env, and single-bootstrap identity. However, the majority of the required matrix is still not directly exercised. Reported `9/9 PASS` therefore cannot close the frozen evidence contract.

**Acceptance:** add direct parameterized temporary-fixture tests covering every required witness family from the approved implementation design, including the ancestor-symlink case above. For failure cases, assert exact failure check name/status/reason, prior PASS / remaining SKIPPED ordering where applicable, exit code, and zero output mutation; for drift cases, independently verify the intended raw/canonical digest input rather than only the final exit code.

## 3. Formal verdict

`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:283)`

Current blockers: **2 HIGH**.  
Production blockers: **1**.  
Design/Authority blockers: **0**.  
Evidence-only blockers: **1**.

## 4. Scope

No real root source-audit execution is authorized. Real publication/checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, runtime integration, training, evaluation, inference and LIBERO4IN1 remain forbidden. The next remediation should stay within the already-approved two root tooling files plus normal review/bookkeeping persistence.
