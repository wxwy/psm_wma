# ChatGPT Independent Review — R09-B2 P4-v4 Materialization v0.6 remediation

- Review date: 2026-09-02
- Approved design: `988dcbaac2fe9a7e5f55054a1d4884763905e9a3`
- ChatGPT design approval: `0765bf369a907caf8572c10632d719b255a9ff62`
- Previous ChatGPT remediation review: `0c0500ac21dff085b21b3b845517aabc440fd479`
- Remediation SHA under review: `b423c70231c06d580f3d7aff713848fa7e129099`
- Formal request/ledger HEAD: `09877fb5990228560e3a9d5b9a3b2707ff444156`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **REQUEST_CHANGES**

## Scope

Reviewed only P4-v4 materialization static helper/fixtures. Existing Execution Request nested/full static closure remains closed. No real preflight/materialization/staging/P5/GPU/model/data/checkpoint/training action is authorized.

## Closed from previous review

### B2 CLOSED — both backend absence prechecks now precede every mkdir

`_reserve_staging()` now performs FD-relative `os.stat(..., follow_symlinks=False)` for both `recurrent` and `ttt_fast_weight` before entering the six-step mutation loop. The new `ttt_fast_weight`-already-exists fixture asserts zero mkdir and no recurrent root creation.

### B3 CLOSED — composition/race/forbidden-call fixture route is materially complete

Materialization fixtures now derive a complete canonical request from `FullAdmissionCompositionTest`, update run/candidate bindings, and call its real `_admit_execution_request()` route while mocking only the already-closed lower-level source Git/entry-byte/clean and loader I/O. Component-acquisition and post-anchor retarget fixtures assert external target zero-write; ambient/subprocess/child and CLI-zero-helper coverage are also present. Six mkdir + six verification fault-prefix coverage remains.

Namespace and child mutation continue to use anchored FD-relative open/stat/mkdir/open/fstat flow, and public `main()` remains unconditional hard-stop.

## Remaining blocker

### B1 — capability authority is still forgeable/resettable through module-visible registry and `object.__setattr__`

**File:** `tools/g0/r09_b2_p4_v4_execution_preflight.py`, around `_ADMITTED_REQUESTS`, `_AdmittedRequest`, `_admit_execution_request()` and `_reservation_plan()`.

Removing `_issued_admitted_request()` closes the previous alternate helper, but the actual admission authority is still a mutable module-level object:

```python
_ADMITTED_REQUESTS: weakref.WeakSet = weakref.WeakSet()
```

and `_reservation_plan()` authorizes solely by:

```python
isinstance(admitted, _AdmittedRequest)
admitted in _ADMITTED_REQUESTS
admitted._consumed is False
request_sha256(admitted.raw) == admitted.request_sha256
```

A caller can still bypass the claimed factory-only / unforgeable contract using only module-visible state and Python primitives:

```python
forged = object.__new__(_AdmittedRequest)
object.__setattr__(forged, "raw", attacker_canonical_raw)
object.__setattr__(forged, "request_sha256", request_sha256(attacker_canonical_raw))
object.__setattr__(forged, "_consumed", False)
object.__setattr__(forged, "_locked", True)
_ADMITTED_REQUESTS.add(forged)
```

No `load_execution_request()` admission occurs on this path, but the object can satisfy the current `_reservation_plan()` checks. Likewise, after a legitimate capability is consumed, `object.__setattr__(admitted, "_consumed", False)` can re-enable it. The new fixture checks only ordinary attribute assignment, so it does not prove the frozen `unforgeable` / `UNUSED -> CONSUMED` non-resettable authority.

This is not a theoretical mismatch with Python privacy conventions: the current authorization decision explicitly trusts a module-visible registry plus object fields that can both be modified without invoking the class `__setattr__` override.

## Required remediation

Keep B2/B3 unchanged. Move the actual admission/consumption authority out of module-visible mutable state and out of capability object fields.

A sufficient pattern is a closure-local `WeakKeyDictionary`/equivalent authority created by a private factory that returns:

- the sole real `_admit_execution_request(raw)` function, which first runs `load_execution_request(raw)` and then records the original admitted raw/SHA/state in hidden closure storage;
- an internal consume/read function used by `_reservation_plan()`, which obtains the admitted raw/SHA from hidden storage and atomically transitions hidden state from UNUSED to CONSUMED.

The capability object itself need not expose authoritative `raw`, SHA, or `_consumed` fields. If such fields remain for diagnostics, reservation must bind against the hidden original state rather than trusting those fields.

Required fixtures:

1. `object.__new__(_AdmittedRequest)` + arbitrary `object.__setattr__` field population cannot become admitted because there is no externally mutable enrollment registry.
2. After one successful or terminal reservation attempt, `object.__setattr__` cannot restore authority; a second call remains rejected.
3. Mutating any visible diagnostic raw/SHA fields via `object.__setattr__` cannot alter the hidden admitted plan/authority.
4. Existing real full-admission, dual-precheck, namespace-race, forbidden-call, CLI hard-stop and 12-fault fixtures remain passing.

Expected delta can remain limited to the P4 helper/test plus status/ledger bookkeeping. No new materialization design is required if the approved v0.6 semantics remain unchanged.
