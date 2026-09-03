# Independent Remediation Review — R09-B2 P4/P5 v4 Handoff Migration

- Gate: `G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION`
- Remediation implementation SHA under review: `01da148b5e3ebbd254c8ba57166dc817ff17e02d`
- Ledger/request SHA observed at review start: `56957c45b0b9fbc27463b45311aee9f0f3dfae88`
- Prior implementation SHA: `3c04c4752d71a6a8003fdb0521f3e2646e9cd4e5`
- Prior ChatGPT review commit: `e3afdd25285260e366a2e0dce81b8458ceb36b77`
- Approved design SHA: `f16f6e4d260114bb89c102e476a63d590751274e`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved the remote `V2` branch directly through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `56957c45b0b9fbc27463b45311aee9f0f3dfae88`; it is a review-request/ledger commit whose parent is exactly remediation implementation `01da148b5e3ebbd254c8ba57166dc817ff17e02d`.

The remediation is one commit after the prior ChatGPT review commit `e3afdd2`. Its code/test diff is limited to `tools/g0/export_r09_b2_p5_resolved_config.py`, the two P4/P5 stdlib test files, and `SESSION.md` / `TODO.md`. The Cosmos Gitlink at the remediation SHA remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. GitHub reports no commit statuses or check-runs for the remediation SHA; submitted unittest/py_compile/diff-check results are therefore repository-recorded claims rather than independently rerun CI evidence in this review environment.

## Verdict

`REQUEST_CHANGES`

The prior two HIGH blockers and the prior wire-key MEDIUM are technically closed in code. One remaining MEDIUM fixture-coverage gap prevents closure of the exact v0.2 design contract.

## Closed — prior HIGH-1: frozen P4 manifest self-SHA spelling

The remediation adds `_p4_manifest_self_sha()` and makes `validate_v2_payload_manifest()` use the old P4 canonical spelling:

```python
json.dumps(core, sort_keys=True, separators=(",", ":"))
```

with the default `ensure_ascii=True`. This matches the pre-migration P4 `canonical_sha256()` semantics and therefore preserves legal non-ASCII manifest paths such as `pkg/é.py` under their old P4 manifest self-SHA.

The roster/projection digest remains intentionally separate and unchanged: P4 `_planned_projection()` still computes `projection_sha256` using the P5 spelling (`ensure_ascii=False`), and P5 `_validate_roster()` still validates roster `{entries,sha256}` with P5 canonicalization. The new non-ASCII regression explicitly proves the old-P4 manifest SHA differs from the P5 spelling while derived `entries` and projection digest remain P5-canonical.

This closes prior HIGH-1.

## Closed — prior HIGH-2: reserved run-root ancestor bypass

After deriving all ancestor directories, the remediation now rejects:

```python
directories & P5_V2_RESERVED_ROOT_PATHS
```

so paths such as `request.json/x` can no longer recreate the exact reserved root path `request.json` as a directory. The fixture covers all five reserved-root ancestor cases while keeping the prohibition exact to the run root.

This closes prior HIGH-2.

## Closed — prior MEDIUM: P4 projection wire key-set regression

The P4 fixture now asserts:

```python
set(item["staging_projection"]) == STAGING_PROJECTION_KEYS
```

and `STAGING_PROJECTION_KEYS` remains exactly `{entries, projection_sha256}`. The P5-side semantic regression still binds the same derived `entries` and P5 canonical digest without renaming P4 `projection_sha256`.

This closes the prior wire-key regression gap.

## MEDIUM — frozen actual-tree `missing` regression is still absent

**File:** `tools/g0/test_r09_b2_p5_full_config_diff.py:265-271`

### Root cause

Approved design v0.2 §4 freezes both **actual-tree extra** and **actual-tree missing** as permanent P5 regressions. The current test suite contains only:

`test_v4_roster_rejects_unlisted_path()`

which creates an extra `run/unexpected` entry and proves the exact-set verifier rejects an extra path. There is no corresponding committed test that removes an expected roster entry from the actual run-root tree and proves `load_p4_v4_preflight()` fails.

The production code itself is correct here:

```python
actual = {path.relative_to(run_root).as_posix() for path in run_root.rglob("*")}
if actual != {item["path"] for item in expected_entries}:
    raise ValueError(...)
```

so a missing path should fail. This is therefore a fixture/evidence gap, not a production semantic bug. However, the frozen design explicitly requires both directions as permanent regressions, so the Gate cannot be closed while one is absent.

### Required acceptance criteria

1. Add a permanent stdlib P5 regression that starts from `_v4_preflight(...)`, removes one expected actual-tree path (preferably the payload regular file), and asserts `load_p4_v4_preflight()` raises `ValueError`.
2. Keep the existing extra-path negative regression unchanged.
3. Do not change production roster semantics unless the new fixture exposes an actual defect; the existing exact-set equality is already the intended implementation.
4. Re-run the same allowed static checks only: P4/P5 targeted stdlib unittests, `py_compile`, and `git diff --check`.
5. Submit a new remediation implementation SHA for same-SHA closure review.

## Accepted scope/boundary state

No new runtime authority was introduced:

- `AUTHORIZED_P4_V4_LOCK_SPEC` remains `None`;
- `AUTHORIZED_P4_V4_EVIDENCE` remains `None`;
- the Cosmos Gitlink is unchanged;
- remediation code scope is root static grammar/loader/verifier + stdlib tests only;
- no artifact/history evidence rewrite or Cosmos submodule change is present in the remediation diff;
- `run_parent_export()` was not modified by this remediation and remains under the previously reviewed hard-stop contract.

Keep the Gate in `REVIEW`. No real request/preflight/staging/materialization/candidate/run-root creation, record/refreeze/evidence publication, P5 export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training is authorized.
