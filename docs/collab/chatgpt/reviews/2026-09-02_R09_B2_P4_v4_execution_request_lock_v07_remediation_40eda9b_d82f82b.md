# Independent Review — R09-B2 P4-v4 Execution-Request Lock v0.7 remediation

- Review anchor: `256192ea32bcdc3e7540bfb0bfb6adc483132e4a`
- Approved design: `671ca0123352b050125f3a413f8e74eeabbe6088`
- Remediation implementation: `40eda9b58c6bcdd0ea953348fadbd39d55eb50f0`
- Formal request / ledger head: `d82f82b753a8c6a69117e14a88da023b9156f14a`
- Gitlink at request head: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: root static planned-commitment implementation and stdlib CPU fixtures only. No P4/P5 handoff migration, final request, real preflight/materialization/staging/candidate/run-root, record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, evaluation/inference/training, B2-T, or Local Memory training.

## Verdict

`REQUEST_CHANGES`

The remediation closes the three production blockers from review `256192e`: exact execution-contract validation, planned run/candidate path/isolation/reuse checks, and the same-FD output terminal-state implementation. Production authority remains `None`; the implementation-to-request delta is Inbox-only and the Gitlink is unchanged.

The only remaining blocker is fixture/evidence closure.

## Closed — B1 execution contract

`build_planned_roster_commitment()` now calls a shared `_validate_execution_contract()` requiring exact equality with `dict(_EXECUTION_CONTRACT_ITEMS)`. The remediation also adds mutations for changed, missing, and extra contract members. No further production change is required here.

## Closed — B2 planned path/isolation/reuse

The remediation now:

- derives `source_root` through the same lexical future-path grammar;
- rejects candidate namespace overlap with source/submodule;
- requires every planned run `root == resolved_root` and rejects source/submodule overlap;
- rejects reused run root / run identity / token across the pair;
- rejects candidate namespace or derived candidate path overlap with either run root.

This is sufficient for the retained planned-only semantics. No further production change is required here.

## Closed — B3 writer terminal states

The new `_write_planned_commitment_at()` separates create-before from create-after states:

- all `os.open()` creation failures are normalized to `NOT_LOCKED`;
- short write and write/fsync/seek/read-back/fchmod/fstat failures become `POISONED_NOT_LOCKED` after creation;
- regular-file + exact `0444` are checked;
- close failure is part of the terminal success condition and becomes `POISONED_NOT_LOCKED`;
- the created path is preserved and there is no cleanup/repair/retry.

No further production change is required here.

## B4 — HIGH — permanent fixture matrix is still materially incomplete

File: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`, `PlannedRosterCommitmentTest`.

The remediation adds only two test methods beyond the prior 79-test suite: one subtest matrix for execution-contract/path/reuse mutations and one subtest matrix for output faults. That improves coverage but does not close the v0.7 fixture contract or the prior review's B4.

Most importantly, the only test that calls `lock_authorized_planned_roster_commitment()` is still the default-`None` fail-closed test. There is no positive authorized-lock composition fixture and therefore no end-to-end proof that the reviewed constant/spec/source/Git/output chain produces exactly one canonical commitment.

Still missing permanent fixtures include:

1. **Positive authorized lock composition** using a valid reviewed temporary authority/spec and real closed-section composition, proving exact spec → commitment bytes/SHA/mode and no final request/preflight side effect.
2. **Source/spec FD traversal**: intermediate-component symlink rejection and retarget-after-parent-FD acquisition proving the read stays bound to the original directory chain; final-component nofollow rejection.
3. **Authority Git bindings**: source commit, tree OID, Gitlink, tracked blob SHA, current-byte SHA, raw SHA, source-root/spec-path binding drift, each failing before output creation.
4. **Output target admission**: actual existing regular target and symlink target fail `NOT_LOCKED` with zero overwrite.
5. **Short-write semantics**: `os.write()` returning `0 < n < len(payload)` must poison while preserving the created target. The current matrix injects an `OSError` from `write`, which does not test the explicit short-return branch.
6. **Post-create state verification**: fstat returning non-regular or wrong mode should poison, not only an injected fstat exception.
7. **Projection/schema drift** required by the approved design: row order/path/type/mode/file SHA/projection SHA and planned/backend/commitment self-SHA mutations should be permanently rejected.
8. **Real closed-section composition**: the positive builder fixture still mocks `validate_entry`, `validate_host_git`, `validate_source`, `validate_interpreter`, `validate_backends`, and `validate_authorities_pair`; add at least one integration fixture that obtains valid closed sections through the already-closed full-admission construction instead of mocking the composition boundary away.

The existing fault test for write/fsync/seek/read/fchmod/fstat/close is useful and should be retained; it is not by itself sufficient for closure.

## Repository / scope verification

`40eda9b... -> d82f82b...` is Inbox-only. The remediation commit changes only the root helper/test plus SESSION/TODO bookkeeping. No P4/P5 migration implementation or real execution was added. Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Gate status

Do not modify the production helper further unless a new defect is discovered. Close the remaining tests/evidence matrix, re-run the stdlib CPU suite, `py_compile`, and `git diff --check`, then request closure again.

The positive verdict after that fixture-only remediation is:

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

Even after static closure, P4/P5 handoff migration, final execution request generation, record/refreeze, real CPU preflight, P5 export/compose, B2-T, GPU, and Local Memory training remain separately unauthorized.
