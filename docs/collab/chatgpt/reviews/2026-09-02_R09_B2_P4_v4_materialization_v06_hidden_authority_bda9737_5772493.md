# ChatGPT Independent Review — R09-B2 P4-v4 Materialization v0.6 hidden-authority remediation

- Review date: 2026-09-02
- Previous ChatGPT review anchor: `c2c3603352efc3daf4d10b7a792d02b8cba73fdb`
- Approved design: `988dcbaac2fe9a7e5f55054a1d4884763905e9a3`
- Design approval: `0765bf369a907caf8572c10632d719b255a9ff62`
- Remediation SHA under review: `bda97378bd67d1f5bb54a4a7607dd1d8942b21a1`
- Formal request / ledger HEAD: `57724934a134a222270ffd43af49be498bb88f72`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Verdict: **APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS**

## Scope

Reviewed only the remaining P4-v4 materialization static-helper blocker from ChatGPT review `c2c3603`: admission / consumption authority must not rely on a module-visible registry or mutable capability fields. Previously closed B2/B3 were checked for drift but not reopened. No real request execution, preflight, materialization, staging, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, or B2-T is authorized.

## Closure finding

The remaining capability-authority blocker is closed.

The remediation removes module-level `_ADMITTED_REQUESTS` as the source of truth and moves the authoritative tuple `(raw, request_sha256, consumed)` into a closure-local `weakref.WeakKeyDictionary` created by `_admission_authority()`.

The active pair:

```text
_admit_execution_request
_consume_admitted_request
```

shares that hidden authority. `_admit_execution_request(raw)` performs the full existing `load_execution_request(raw)` admission before inserting the capability into the hidden authority. `_reservation_plan()` no longer trusts the capability's visible `raw`, `request_sha256`, or `_consumed` fields; it obtains the authoritative raw/SHA and atomically advances one-shot state only through `_consume_admitted_request()`.

Therefore:

- an `object.__new__(_AdmittedRequest)` forgery with manually populated visible fields is not present in the hidden authority and is rejected;
- mutating visible `raw` / SHA fields does not redirect reservation authority;
- resetting visible `_consumed` after a successful reservation does not reset the closure-local consumed state;
- the prior alternate unchecked issuer is absent;
- the only active issuer recognized by the active consume closure is `_admit_execution_request()` after full admission.

The new fixtures explicitly exercise both object-level forgery and post-admission `object.__setattr__` mutation/reset while proving the hidden authority still rejects or preserves one-shot consumption.

## Previously closed B2/B3 remain closed

No regression found in the already-remediated areas:

- both backend direct-child absence checks are completed with namespace-FD-relative `stat(..., follow_symlinks=False)` before the first mkdir;
- namespace acquisition remains anchored from `/` with per-component `O_DIRECTORY|O_NOFOLLOW` opens;
- child creation remains parent-FD-relative mkdir/open/fstat;
- materialization fixtures still use the full composition request and real `_admit_execution_request()` route while only stubbing already-approved lower fixed I/O;
- second-backend-existing zero-mkdir coverage, component-acquisition retarget, post-anchor retarget, ambient/subprocess/child prohibition, CLI-zero-helper, and six mkdir + six verification fault-prefix coverage remain present;
- public `main()` still ends at the unconditional hard-stop and does not call reservation.

## Evidence / drift check

Codex ledger reports:

- P4 CPU tests: `76/76 PASS`;
- materialization targeted tests: `13/13 PASS`;
- `py_compile`: PASS;
- `git diff --check`: PASS.

Independent repository drift check:

- `c2c3603... -> 5772493...` changes only the intended helper/tests plus status/Inbox bookkeeping;
- `bda9737... -> 5772493...` changes only `docs/collab/chatgpt/CODEX_INBOX.md`;
- Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Verdict

**APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_MATERIALIZATION_STATIC_TOOLS**

This closes only the static materialization helper/tooling Gate. It does **not** authorize creation or execution of a real frozen execution request, real P4 preflight/materialization/staging, record/refreeze/evidence publication, P5 export/compose, B2-T, GPU/CUDA, model/data/checkpoint I/O, or Local Memory training. Those require separate exact-request / execution Gates.