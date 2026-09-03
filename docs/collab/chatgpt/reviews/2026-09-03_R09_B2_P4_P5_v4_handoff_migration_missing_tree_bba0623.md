# Independent Remediation Review — R09-B2 P4/P5 v4 Handoff Migration Missing-Tree Fixture

- Gate: `G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION`
- Remediation implementation SHA under review: `bba062377b32f185822ae8eb8f6d46beddd1e8d4`
- Ledger/request SHA observed at review start: `e7ec07e4f1aee8c7258295798cf7a1f49043c48f`
- Parent / prior ChatGPT review commit: `03ddc1b3bb1be3620e8db1038b96d26a2c10d5b9`
- Prior implementation SHA: `01da148b5e3ebbd254c8ba57166dc817ff17e02d`
- Approved design SHA: `f16f6e4d260114bb89c102e476a63d590751274e`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved the remote `V2` branch through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `e7ec07e4f1aee8c7258295798cf7a1f49043c48f`; it is a ledger/review-request commit whose parent is exactly remediation implementation `bba062377b32f185822ae8eb8f6d46beddd1e8d4`.

The remediation is exactly one commit after prior ChatGPT review `03ddc1b`. The compare is tests/status only: `tools/g0/test_r09_b2_p5_full_config_diff.py`, `SESSION.md`, and `TODO.md`. No production P4/P5 tooling changed and the Cosmos Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

GitHub reports no commit statuses or check-runs for `bba0623`; the submitted `P4=86/86`, `P5=6/6`, `py_compile`, and `git diff --check` results are repository-recorded claims rather than independently rerun CI evidence in this review environment.

## Verdict

`REQUEST_CHANGES`

The prior HIGH-1, HIGH-2, and P4 wire-key issues remain closed because this remediation does not touch production code. However, the newly added missing-tree regression can pass for the wrong reason and therefore does not yet close the frozen permanent-fixture requirement.

## MEDIUM — missing-tree fixture introduces an unrelated directory-mode violation

**File:** `tools/g0/test_r09_b2_p5_full_config_diff.py:273-282`

### Root cause

The new regression currently does:

```python
run = evidence / "run"; run.chmod(0o755)
staging = run / "import_staging" / ("a" * 64)
staging.chmod(0o755)
(staging / "payload.py").unlink()
with self.assertRaises(ValueError):
    load_p4_v4_preflight(evidence)
```

The temporary `0755` on the token staging directory is required to make the unlink portable for a non-root test user, but it is never restored to the frozen roster mode `0555` before invoking the verifier.

Therefore the fixture contains two independent defects at verification time:

1. expected payload regular file is missing;
2. expected staging directory mode is `0755` instead of `0555`.

Today `_validate_roster()` checks the actual recursive path set before the per-entry mode loop, so the test currently fails at the intended missing-path condition. But as a **permanent regression**, this is insufficient: if the actual-tree missing-path protection were accidentally weakened or removed in a later change, this test could still pass merely because the staging-directory mode check raises `ValueError`.

That makes the regression a false-positive-capable fixture and does not provide durable evidence for the design-v0.2 requirement that actual-tree `missing` be permanently rejected.

### Required acceptance criteria

1. Keep the test tests-only; do not modify production roster semantics.
2. After unlinking `payload.py`, restore the token staging directory to `0555` before calling `load_p4_v4_preflight()`.
3. Preferably assert the remaining tree is otherwise valid before the verifier call, e.g. staging mode is `0555` and the payload path is absent.
4. For a stronger exact-set regression, use `assertRaisesRegex(ValueError, "roster-unlisted path")` (or an equivalent stable verifier-owned signal) so the fixture cannot pass on an unrelated mode/type failure.
5. Keep the existing extra-path negative regression unchanged.
6. Re-run only the allowed static checks: targeted P4/P5 stdlib unittests, `py_compile`, and `git diff --check`.
7. Submit a new remediation implementation SHA for same-SHA closure review.

## Accepted inherited implementation state

Because `bba0623` changes no production code, the previously reviewed closures remain intact:

- shared manifest validation preserves the old P4 `ensure_ascii=True` self-SHA spelling;
- P5 roster/P4 projection digest remains P5-canonical;
- all non-root ancestors are derived;
- the five reserved root paths cannot reappear as derived directories;
- regular/directory collisions remain rejected;
- P4 `staging_projection` remains exactly `{entries, projection_sha256}`;
- P5 roster remains exactly `{entries, sha256}`;
- actual-tree extra-path rejection remains covered;
- `AUTHORIZED_P4_V4_LOCK_SPEC` remains `None`;
- `AUTHORIZED_P4_V4_EVIDENCE` remains `None`;
- `run_parent_export()` remains under the previously reviewed hard-stop contract;
- no Cosmos submodule/runtime/GPU/training scope creep is present.

Keep the Gate in `REVIEW`. This review authorizes no real request/preflight/staging/materialization/candidate/run-root creation, record/refreeze/evidence publication, P5 export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.
