# Independent Slice Review — R09-B2 P4-v4 Log Namespace Static Validator

- Parent Gate: `G0-R09-B2-P4-V4-EXACT-REQUEST-RECORD-REFREEZE-STATIC-TOOLS`
- Requested slice verdict: `APPROVE_TO_CLOSE_P4_V4_LOG_NAMESPACE_STATIC_SLICE`
- Implementation SHA under review: `1ef7f4962346e4cdbdf3a179ef657eb59db09591`
- Ledger/request SHA observed at review start: `cfcd330cbb8e55ca317a0ef938c9fc88015afefa`
- Prior implementation SHA: `6c521c115b05006d20d8ce37288b72331c9cb7f2`
- Prior ChatGPT review: `21d19886340e05d658fd1e3b7874777f8081f440`
- Approved design SHA: `b70cd294f4d9896cbe297d96535540b62cf43391`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Repository-state note

This environment has no local checkout of `wxwy/psm_wma`, so literal shell `git fetch origin V2` could not be executed. I resolved remote `V2` through the connected GitHub repository API immediately before review. Remote `V2` HEAD was `cfcd330cbb8e55ca317a0ef938c9fc88015afefa`; it is the ledger/review-request commit and its parent is exactly implementation SHA `1ef7f4962346e4cdbdf3a179ef657eb59db09591`.

`21d1988 -> 1ef7f49` is one remediation commit changing only `SESSION.md`, `TODO.md`, `tools/g0/r09_b2_p4_v4_static_contract.py`, and `tools/g0/test_r09_b2_p4_v4_static_contract.py`. The request is now explicitly narrowed to the log-namespace validator slice; the full exact-request/record-refreeze/CAS static-tools Gate remains `IN_PROGRESS`. The Cosmos Gitlink is unchanged. GitHub exposes no commit statuses for this implementation SHA; submitted `13/13 PASS`, `py_compile`, and `git diff --check` are repository-recorded evidence rather than independently rerun CI here.

## Verdict

`REQUEST_CHANGES`

The scope correction closes the prior HIGH-2: this SHA no longer asks to close the whole static-tools Gate. One HIGH remains in the slice itself.

## HIGH-1 — exact namespace shape is present, but namespace identities are still caller-selected

**Files:**
- `tools/g0/r09_b2_p4_v4_static_contract.py:39-61`
- `tools/g0/test_r09_b2_p4_v4_static_contract.py:25-49`

### Root cause

The remediation replaces the free-form `forbidden_roots` tuple with an exact structured object:

```python
LOG_NAMESPACE_KEYS = {
    "source_root", "submodule_root", "run_roots", "candidate_root", "p5_paths"
}

validate_logs(value, namespaces)
```

and correctly requires exactly two run roots and six P5 paths. This prevents omission of a namespace *category*.

However, the values of those categories are still supplied by the caller and are only checked as lexical absolute paths. The helper does not prove that:

- `source_root` is the source root from the admitted/frozen final request;
- `submodule_root` is exactly that source root's frozen `cosmos-framework` identity;
- `run_roots` are the two exact verifier-owned run identities from the final request/planned commitment;
- `candidate_root` is the exact frozen final-request candidate root;
- `p5_paths` are the six exact fixed evidence publication paths under the frozen evidence authority/root.

Therefore a caller can supply a fully schema-valid but false namespace object. Example:

```python
namespaces = {
    "source_root": "/fake-source",
    "submodule_root": "/fake-source/cosmos-framework",
    "run_roots": ("/fake-run/recurrent", "/fake-run/ttt"),
    "candidate_root": "/fake-candidates",
    "p5_paths": tuple(f"/fake-evidence/{i}" for i in range(6)),
}
```

A correctly re-digested `logs_v1` whose root is `/real-candidates/attempt/logs` will pass `validate_logs()` as long as it does not overlap those fake values. The current helper has no final-request/planned/P5 identity input with which to reject that substitution.

This is the same authority problem identified in the prior review, narrowed to substitution rather than category omission. An exact key-set is not by itself a verifier-owned authority.

The new fixtures do not close this case. They cover missing/wrong type/arity, relative paths, stale log self-digest, and overlap against the supplied namespace object, but they never substitute a mandatory namespace with a different *valid absolute* identity while placing `logs.root` inside the real frozen namespace.

### Required acceptance criteria for this slice

1. Keep the request scoped to `APPROVE_TO_CLOSE_P4_V4_LOG_NAMESPACE_STATIC_SLICE`; do not reopen the full record/refreeze/CAS closure.
2. Do not accept caller-selected namespace identities as authority. Use one of these auditable patterns:
   - derive the namespace binding from already-validated final request/planned/source/P5 inputs inside a verifier-owned helper; or
   - accept only an opaque/verifier-issued namespace binding produced by a factory that independently validates those identities before `validate_logs()` consumes it.
3. Bind each category exactly:
   - source root to the admitted final request/source binding;
   - submodule root to the corresponding frozen `cosmos-framework` identity;
   - the two ordered run roots to the two final/planned backend identities;
   - candidate root to the final request candidate root;
   - six P5 paths to the fixed evidence publication paths/evidence-root authority.
4. Add permanent substitution fixtures for every category: use a different but lexically valid absolute source/submodule/run/candidate/P5 path, recompute any applicable digest, place `logs.root` inside the real frozen namespace, and require rejection.
5. Preserve existing positive grammar checks, exact key-set, 2-run/6-P5 arity, P4 logs self-digest, exact stdout/stderr basenames, and symmetric ancestor/descendant overlap behavior.
6. Keep the parent `...STATIC-TOOLS` Gate `IN_PROGRESS`; production authorities remain `None`; no real request/preflight/log/candidate/record/P5/GPU/training side effect is authorized.

## Accepted remediation properties

The following changes are correct and should be retained:

- the request token is now slice-specific rather than full-Gate closure;
- `TODO.md` / `SESSION.md` keep the parent static-tools Gate `IN_PROGRESS` and explicitly defer record/refreeze/CAS contracts;
- namespace category key-set is exact;
- run-root arity is exactly 2 and P5-path arity exactly 6;
- logs self-digest remains the approved P4 canonical JSON spelling;
- lexical path and exact stdout/stderr child checks remain fail-closed;
- overlap checking is symmetric;
- the closed candidate PASS/FAIL file-set is not modified;
- production execution authority remains `None` and no runtime execution path is opened.

## Scope

Do not close `APPROVE_TO_CLOSE_P4_V4_LOG_NAMESPACE_STATIC_SLICE` at this SHA. Keep the parent static-tools Gate `IN_PROGRESS/REVIEW`.

This review authorizes no production exact-request generation, P4 preflight/staging/materialization/candidate/log creation, record/refreeze/evidence publication, P5 authority/export/compose, child/torch/torchrun, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory/LIBERO training.