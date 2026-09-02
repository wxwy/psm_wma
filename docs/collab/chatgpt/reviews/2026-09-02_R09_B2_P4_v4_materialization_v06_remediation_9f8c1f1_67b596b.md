# ChatGPT Independent Review — R09-B2 P4-v4 Materialization v0.6 remediation

- Review date: 2026-09-02
- Approved design: `988dcbaac2fe9a7e5f55054a1d4884763905e9a3`
- ChatGPT design approval: `0765bf369a907caf8572c10632d719b255a9ff62`
- Remediation SHA under review: `9f8c1f1373008ca8d7d1505e5b05d2b3af08525d`
- Formal request/ledger HEAD: `67b596b02cb9d444182edd1ec942a1c345be7bb0`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

Reviewed only P4-v4 materialization static helper/fixtures. Existing Execution Request nested/full static closure remains closed. No real preflight/materialization/staging/P5/GPU/model/data/checkpoint/training action is authorized.

The remediation correctly improves one part of the previous capability issue: the capability no longer stores the mutable parsed `run` dict, the integer-id registry was replaced by a `WeakSet`, and reservation re-derives run data from canonical SHA-bound raw bytes. The namespace/child FD anchored `openat`/`mkdirat` direction and public CLI hard-stop remain intact.

## Blocking findings

### B1 — `_admit_execution_request()` is still not the unique admission issuer

**File:** `tools/g0/r09_b2_p4_v4_execution_preflight.py` around `_issued_admitted_request()` / `_admit_execution_request()`.

The approved v0.6 contract freezes a factory-only capability issued only after real `load_execution_request(raw)` admission. Current code still exposes a second helper:

```python
def _issued_admitted_request(raw, request):
    admitted = object.__new__(_AdmittedRequest)
    ...
    _ADMITTED_REQUESTS.add(admitted)
    return admitted
```

`_issued_admitted_request()` itself performs no full admission. A caller can therefore register a capability from arbitrary raw bytes without going through `_admit_execution_request()` / `load_execution_request()`. WeakSet membership proves only that this alternate issuer registered the object, not that full admission occurred.

**Required remediation:** remove the alternate unchecked issuer. Construct/register the capability only inside `_admit_execution_request()` after `load_execution_request(raw)` succeeds, with no separately callable registration path. Add a negative fixture proving there is no alternate issuer path.

### B2 — both backend direct-child absence prechecks are still not completed before the first mkdir

**File:** `tools/g0/r09_b2_p4_v4_execution_preflight.py::_reserve_staging()`.

Current flow is effectively:

```text
check recurrent absent
→ create recurrent root/middle/leaf
→ check ttt_fast_weight absent
→ create ttt_fast_weight root/middle/leaf
```

The frozen v0.6 contract requires **all filesystem prechecks before any mutation**. If `ttt_fast_weight` already exists while recurrent does not, current code creates the recurrent three-directory footprint and then raises ordinary `ValueError("...already exists")`. That violates the zero-mkdir precheck guarantee and leaves an unmodelled partial footprint outside `POISONED` semantics.

**Required remediation:** after namespace FD is anchored, first check both backend direct-child names with FD-relative `stat(..., follow_symlinks=False)` and accept only ENOENT for both. Only after both checks succeed may the six-step mutation loop begin. Add a fixture with TTT existing / recurrent absent and assert zero mkdir and no recurrent root creation.

### B3 — v0.6 fixture contract remains unclosed

**File:** `tools/g0/test_r09_b2_p4_v4_execution_preflight.py::MaterializationReservationTest`.

The test helper `_admitted()` still patches `load_execution_request` and supplies a minimal `{"run": ...}` JSON. Therefore the materialization suite still does **not** prove the frozen requirement that fixtures obtain capabilities through real `_admit_execution_request()` over a complete canonical request/full-admission route.

Also missing from the materialization fixture class are the frozen namespace race assertions: component-acquisition-window retarget and post-anchor pathname retarget with proof that the external target receives zero writes. The current symlink-namespace test is useful but is not equivalent to those race fixtures. Ambient/subprocess/P5/child and explicit CLI-zero-helper coverage should also be closed as specified by v0.6.

**Required remediation:** use a complete valid execution request and exercise the real admission route while mocking only the already-approved underlying fixed I/O where necessary; add the missing precheck/race/forbidden-call fixtures. Keep the six mkdir + six post-create fault matrix.

## Non-blocking observations

- `created_paths` mutation-prefix semantics are consistent with v0.4/v0.6.
- Namespace traversal from `/` and child creation are FD-relative and use `O_DIRECTORY|O_NOFOLLOW`.
- Public `main()` still ends at unconditional hard-stop and does not call reservation helper.
- Request ledger after `9f8c1f1` changes only Inbox bookkeeping; Gitlink remains frozen.

## Required re-review evidence

Expected delta can remain limited to:
- `tools/g0/r09_b2_p4_v4_execution_preflight.py`
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`
- status/ledger bookkeeping

For re-review provide the exact remediation SHA and request-ledger SHA, with CPU unittest, `py_compile`, and `git diff --check` PASS. No real preflight/materialization/P5/GPU/training is authorized.
