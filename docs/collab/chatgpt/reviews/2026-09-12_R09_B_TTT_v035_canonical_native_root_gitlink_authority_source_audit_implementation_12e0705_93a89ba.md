# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation closure remediation

**Date:** 2026-09-12  
**Formal root:** `12e07051ff74ecdb46d67aafdd9883eecfac8e7a`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION`

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `CODEX_INBOX.md`.
- Independently verified formal root `12e07051ff74ecdb46d67aafdd9883eecfac8e7a` resolves `cosmos-framework` exactly to child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Remediation remains inside the approved two root tooling files; child is unchanged. SESSION/collaboration files are bookkeeping only.
- Prior formal `c8cecddf0c0eb2c2b1da6fb4e045e6789970144a` had two HIGHs: ancestor symlink escape and incomplete direct witness matrix.

## 2. Findings

### Prior Production HIGH — ordinary ancestor symlink escape: PARTIALLY CLOSED

The remediation improves `path_arg()` from leaf-only checking to walking the nearest existing path component and its parents, and direct temporary-fixture witnesses now cover symlinked parent components for root, child Git dir and output. The ordinary existing-target ancestor-symlink case from the prior review is therefore closed.

### HIGH-1 — Production — dangling ancestor symlink is still skipped and can bypass the frozen output failure contract

`path_arg()` finds the nearest existing component with:

```python
while not probe.exists() and probe != probe.parent:
    probe = probe.parent
```

`Path.exists()` follows symlinks and returns `False` for a dangling symlink. Therefore a dangling symlink component is treated as if that path component did not exist and is skipped before the subsequent `is_symlink()` walk. For root/child with `strict=True`, resolution will generally fail later, but the output path explicitly uses `must_exist=False`: a dangling symlink ancestor can survive `resolve(strict=False)`, and the resolved value is discarded. `write_atomic()` then operates on the original path. This can surface as an uncaught filesystem exception rather than the frozen `root_gitlink_source_audit_failure_v1` operational FAIL / exit 3 / zero-output-mutation contract.

This remains within the already-frozen requirement that symlink escape must fail closed before any output mutation.

**Acceptance:** detect symlink directory entries without following them across the full lexical path chain, including dangling symlinks, for root, child Git dir and output. The accepted representation must deterministically raise `AuditFailure(<LABEL>_PATH, operational=True)` before Git lookup/output mutation. Add direct temporary-fixture witnesses for dangling ancestor symlinks, especially `--output`, asserting canonical failure stdout, exit 3 and unchanged/non-created destination.

### Prior Evidence HIGH — direct witness matrix: PARTIALLY CLOSED, still HIGH

The suite is expanded to 11 tests and now directly covers ordinary ancestor symlink escape plus representative config/source key/type/hex negatives, Gitlink mode mismatch and tree-object-type mismatch. These are useful additions.

However the approved implementation-design matrix is still materially incomplete. Missing direct witness families include, among others:

- publication fixed-path missing/drift and publication blob-type mismatch;
- Gitlink path/object drift beyond one mode/type parser sample;
- child tree drift and root/child object-type/reachability permutations;
- raw tree/blob byte, byte-length, SHA-256 and canonical tree-record digest drift as distinct direct witnesses;
- publication outer-key/schema/self-reference injection;
- config 15-key and source five-key missing-key, schema/value, numeric/boolean/type and digest variants beyond the small representative subset;
- relative-path and child symlink/worktree-substitution cases;
- Git command failure and unexpected-stdout cases;
- exact success-only atomic replacement witness.

The design explicitly froze these as direct CPU/static witnesses, not merely as code paths that appear logically capable of rejecting them. `11/11 PASS`, Ruff, py_compile and diff-check remain supporting evidence only.

**Acceptance:** add direct parameterized temporary-fixture/unit witnesses covering every required family from the approved implementation design. For integration-style failures, assert exact failed check name/status/reason, prior PASS / later SKIPPED ordering, exit code and zero output mutation. For pure validator/raw-object cases, assert the exact intended invariant (raw bytes/length/digest/schema/key/type/value) rather than only `AuditFailure` generically.

## 3. Formal verdict

`REQUEST_CHANGES(tools/g0/audit_r09_b_ttt_root_gitlink_authority.py:283)`

Current blockers: **2 HIGH**.  
Production blockers: **1**.  
Design/Authority blockers: **0**.  
Evidence-only blockers: **1**.

## 4. Scope

No real root source-audit execution is authorized. Real publication/checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, runtime integration, training, evaluation, inference and LIBERO4IN1 remain forbidden. The next remediation should remain within the approved two root tooling files plus normal review/bookkeeping persistence.
