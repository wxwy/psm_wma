# Independent Remediation Review — R09-B2 P4/P5 v4 Handoff Migration Exact Missing-Tree Fixture

- Gate: `G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION`
- Remediation implementation SHA under review: `28b859203d1735e33e0b1d8d7813429841e1c778`
- Ledger/request SHA observed at review start: `105188faeccfda893b73296f3578c0789afdf43d`
- Parent / prior ChatGPT review commit: `282b75ffe90ecc87221cc7a6af44c6a47ca216ef`
- Prior remediation implementation: `bba062377b32f185822ae8eb8f6d46beddd1e8d4`
- Approved design SHA: `f16f6e4d260114bb89c102e476a63d590751274e`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This review environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved the remote `V2` branch through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `105188faeccfda893b73296f3578c0789afdf43d`; it is a ledger/review-request commit whose parent is exactly remediation implementation `28b859203d1735e33e0b1d8d7813429841e1c778`.

The remediation is exactly one commit after prior ChatGPT review `282b75f`. The compare is tests/status only: `tools/g0/test_r09_b2_p5_full_config_diff.py`, `SESSION.md`, and `TODO.md`. No production P4/P5 tooling changed. The Cosmos Gitlink at the remediation SHA remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

GitHub reports no commit statuses or check-runs for `28b8592`; the submitted `P4=86/86`, `P5=6/6`, `py_compile`, and `git diff --check` results are repository-recorded claims rather than independently rerun CI evidence in this review environment.

## Verdict

`APPROVE_TO_CLOSE_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS`

The only remaining blocker from review `282b75f` is closed. This approval is strictly for the static handoff-migration tooling/fixture Gate and does not authorize any real execution.

## Closure — exact missing-tree regression is now single-fault and reason-bound

The prior fixture temporarily changed the token staging directory to `0755` to permit portable unlink and failed to restore it before invoking the verifier. That allowed the test to pass on an unrelated mode violation if the missing-path exact-set protection were later weakened.

The remediation now performs the portable unlink and then restores the frozen directory mode before verification:

```python
staging.chmod(0o755)
(staging / "payload.py").unlink()
staging.chmod(0o555)
self.assertEqual(staging.stat().st_mode & 0o777, 0o555)
self.assertFalse((staging / "payload.py").exists())
with self.assertRaisesRegex(ValueError, "roster-unlisted path"):
    load_p4_v4_preflight(evidence)
```

This satisfies all acceptance criteria from the prior review:

1. remediation is tests-only; production roster semantics are untouched;
2. token staging is restored to `0555` before verifier entry;
3. the test explicitly proves the surviving staging directory has the frozen mode and the expected payload file is absent;
4. the failure is bound to the verifier-owned exact-tree signal `roster-unlisted path`, so an unrelated mode/type rejection cannot satisfy the fixture;
5. the existing extra-path regression remains unchanged.

The run-root itself remains outside the embedded roster row set, so its temporary `0755` used for fixture mutation does not create a competing roster-entry mode violation. The verifier's exact recursive path-set comparison occurs against the derived entries, and the new fixture now isolates the intended missing payload path.

## Inherited implementation closure remains intact

Because `28b8592` changes no production code, the previously reviewed static implementation state remains intact:

- shared manifest validation preserves the frozen P4 `ensure_ascii=True` manifest self-SHA spelling;
- P5 roster/P4 projection digest remains P5-canonical;
- arbitrary legal nested payload paths derive all non-root ancestor directories;
- reserved root paths cannot reappear as regular files or derived directories;
- regular/directory and strict-ancestor collisions fail;
- P4 `staging_projection` remains exactly `{entries, projection_sha256}`;
- P5 roster remains exactly `{entries, sha256}`;
- P4/P5 share the same verifier-derived `entries` and P5 canonical digest;
- actual-tree extra and missing directions now both have permanent regressions;
- P5 actual-tree exact-set, mode/type, regular SHA, symlink, and `st_nlink==1` checks remain unchanged;
- `AUTHORIZED_P4_V4_LOCK_SPEC` remains `None`;
- `AUTHORIZED_P4_V4_EVIDENCE` remains `None`;
- `run_parent_export()` still hard-stops immediately after `build_v4_pair_requests(...)` and before output creation/export;
- no Cosmos submodule/runtime/GPU/training scope creep is present.

## Scope boundary

This verdict closes only:

`G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION` static tooling/fixture implementation.

It does **not** authorize:

- real P4 execution request creation;
- real P4 preflight;
- real staging/materialization/candidate/run-root creation;
- record/refreeze/evidence publication;
- P5 authority update;
- P5 export/compose;
- child/torch/torchrun execution;
- GPU/CUDA;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T;
- Local Memory / LIBERO training.

Any such next step requires its own frozen design/Gate and same-SHA reviewer approval.
