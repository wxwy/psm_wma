# Independent Review — R09-B2 P4-v4 Preflight Materialization v0.4 implementation

- Implementation under review: `9bc78f1bae4a9177d6f5f2b6a79bc70d875c911a`
- Formal request / ledger head: `e29448c02b53f63c98c646b08b394456ccf49f99`
- Approved design: `dcb5b12fbdd83dd3869884e702dc8484ac5e6bde`
- Prior ChatGPT design approval: `35e4e4987074088ff6ddd6dc8dd21dd2b9a3a46d`
- Gitlink verified at request head: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

The public CLI remains hard-stopped and the closed Execution Request / FULL admission contracts are not reopened. The blockers below are confined to the new materialization helper and its fixtures.

## Findings

### B1 — HIGH — `_AdmittedRequest` is forgeable and mutable, so the helper is not actually bound to prior full admission

Files:
- `tools/g0/r09_b2_p4_v4_execution_preflight.py:103-114`
- `tools/g0/r09_b2_p4_v4_execution_preflight.py:716-744`
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py:20-34`

The approved v0.4 contract requires the sole admission route to be `_admit_execution_request(raw)` after successful `load_execution_request(raw)`, with helper authority derived only from the admitted SHA-bound raw bytes.

Current implementation exposes a mutable dataclass:

```python
@dataclass(slots=True)
class _AdmittedRequest:
    raw: bytes
    request_sha256: str
    _seal: object
    _consumed: bool = False
```

All admission fields and the latch are assignable. A caller can therefore mutate `raw` and `request_sha256` together after a valid admission, reset `_consumed`, or directly construct an object with the module-level `_ADMISSION_SEAL` without ever calling `load_execution_request()`.

The new fixture does exactly the latter: `_admitted()` constructs `_AdmittedRequest(...)` directly. Its raw payload contains only `{"run": ...}` and even reuses the same `roster_sha256` on both backends, so it could not pass the existing full execution-request admission / run-pair validator. Thus the passing reservation tests do not prove the approved admission→reservation composition path.

Required remediation:
1. Make the admission data (`raw`, request SHA, seal/proof) non-reassignable after successful admission and make the one-shot state non-resettable through the normal object interface.
2. Ensure direct construction cannot create an admitted capability without executing the same full admission check (for example, construction itself validates, or the capability has no externally usable direct constructor under the project's private-interface assumptions).
3. Build reservation fixtures through the real `_admit_execution_request()` using a fully valid canonical execution request; add negative fixtures for bare raw/dict/reparse/forged capability and post-admission mutation/reset attempts.

### B2 — HIGH — path-based `os.mkdir(path)` is not the frozen nofollow-safe reservation primitive

File:
- `tools/g0/r09_b2_p4_v4_execution_preflight.py:745-783`

The approved design freezes each mutation as a **nofollow mkdir target** followed by **nofollow stat**, with all writes confined to the admitted namespace.

Current implementation prechecks pathnames, then performs:

```python
os.mkdir(path)
...
os.lstat(path)
```

`lstat()` does not follow the final component, but both pathname operations still resolve parent components at call time. A parent can be replaced by a symlink after precheck (or after the preceding directory's successful lstat) and before the next `os.mkdir(path)`. The mkdir can then occur outside the admitted namespace; the subsequent full-path `lstat(path)` can still observe a directory through the redirected parent. This is a precheck→mutation TOCTOU escape and does not satisfy the nofollow-safe contract.

Required remediation:
- Anchor the namespace with a verified directory FD and perform child creation/verification relative to verified parent directory FDs (`dir_fd` / mkdirat-style operations, with directory opens using nofollow semantics). Each next-level parent must be the already verified directory object/FD, not a re-resolved pathname.
- Add a fixture that retargets/replaces a parent between operations and proves no write can escape the namespace.

### B3 — HIGH — the required v0.4 fixture matrix is largely absent

File:
- `tools/g0/test_r09_b2_p4_v4_execution_preflight.py:20-64`

The approved design requires fixtures for:
- all six mkdir failure points with exact prefixes;
- all six post-mkdir stat failure points with exact prefixes;
- raw-byte admission vs mutable/forged inputs;
- capability one-shot, including failed attempts;
- required same-backend ancestor relation and unexpected overlap rejection;
- precheck failure with zero mkdir;
- ambient/subprocess/P5/child zero calls;
- public `main()` hard-stop with zero reservation call.

The implementation adds only two tests: a success/second-call case, plus first-mkdir and first-stat failures. It does not cover the 12 mutation points or the remaining frozen boundaries. Reported `65/65 PASS` therefore does not close the approved materialization contract.

Required remediation: add the full deterministic matrix above, including exact `created_paths`, `failed_path`, cause class/message where frozen, consumed state after every terminal path, and explicit zero-side-effect assertions.

## Scope / authority

This review does **not** authorize a real execution request, P4 preflight, run/candidate/staging materialization, record/refreeze/evidence publication, P5 authority/export/compose, subprocess child execution for the preflight, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, or Local Memory training.

The existing `main()` unconditional hard-stop remains the correct boundary until a later independently reviewed exact-request execution Gate.
