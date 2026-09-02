# ChatGPT independent review — R09-B2 P4-v4 Execution Request FULL static implementation

- Date: 2026-09-02
- Approved design: `fad1e8d6959fcfee76129e04dc213e7fd6ea49f1`
- ChatGPT design approval: `24c314820bf81d5cb6f736cf25bede9b1bf6a690`
- Implementation under review: `c3b64b5ab56fde2669a5af739fbbc1d97a1a4733`
- Formal request/ledger HEAD inspected: `dd21f8bf7d551c81b392e0e6a7f45cb16bfac16d`
- Gitlink independently confirmed at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: root static parser/orchestration + stdlib CPU fixtures only. No real request/preflight/staging/P5/GPU/training was authorized or executed by this review.

## Verdict

`REQUEST_CHANGES`

Production orchestration is acceptable. The remaining blockers are fixture-only; no production redesign is requested unless the new fixtures expose a real defect.

## What is correct

`tools/g0/r09_b2_p4_v4_execution_preflight.py::load_execution_request()` implements the approved v0.2 route:

1. entry;
2. host-Git validation;
3. source using the returned `git_path`;
4. interpreter using the same `git_path` object;
5. run;
6. candidates;
7. backends;
8. authorities using one `source_root = Path(value["source"]["root"])` derived from the already-parsed canonical source field and the same `git_path` object.

The legacy standalone `validate_environment_pair()` / `verify_d005_pair()` routes are not added to the full admission path. `main()` still performs the single-read SHA binding and ends in the unconditional reviewed-request hard-stop. I found no new execution path, P5 call, materialization, GPU/model/data/checkpoint I/O, or training authority in the production diff.

## Blocking fixture gaps

### B1 — the full-route fixture does not prove the frozen orchestration order

In `tools/g0/test_r09_b2_p4_v4_execution_preflight.py::EntryFoundationTest`, the new `test_full_route_reuses_host_git_and_canonical_source_root()` checks argument reuse but does not assert the v0.2 frozen validator sequence.

The approved design explicitly freezes:

`validate_entry -> validate_host_git -> validate_source -> validate_interpreter -> validate_run_pair -> validate_candidates -> validate_backends -> validate_authorities_pair`.

A permanent route fixture must record/assert this complete order (and the required host-Git/source-root arguments), so a future accidental reorder/omission cannot still pass.

### B2 — the nominal "full valid" fixture bypasses three closed validators instead of spying the real route

`EntryFoundationTest.setUp()` currently replaces `validate_source`, `validate_interpreter`, and `validate_authorities_pair` with bare `Mock` objects. Consequently `_request()` supplies only `{ "root": "/source" }` for source and `{}` for interpreter/environment/authorities. This synthetic request is not a genuinely valid eight-section request; it reaches the hard-stop only because three validators are completely bypassed.

That is weaker than the approved v0.2 fixture contract, which allowed mocking the **underlying I/O** of already-closed sections while spying the actual validator route. It also means the full-route test does not demonstrate that the authorities validator's unique environment-D005 projection route remains live when composed by `load_execution_request()`.

Remediation should remain tests-only: use valid section-shaped synthetic objects and either wrap/spy the real closed validators while stubbing their low-level I/O, or otherwise construct an equivalent route fixture that executes the actual validator bodies without touching real evidence or execution paths.

### B3 — close the full-admission mutation matrix at the composition layer

The approved v0.2 fixture matrix calls for a reidentified mutation in every nested section to fail through full admission. Existing per-section unit tests are useful but do not by themselves prove that `load_execution_request()` cannot omit/bypass a section. Add a compact full-route mutation table covering at least `entry/source/interpreter/environment/authorities/run/candidates/backends`, recomputing relevant identities so rejection is caused by the section contract rather than stale outer/self-digests.

## Required closure evidence

A remediation can be tests-only in `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`. Re-review should show:

- exact full validator call order asserted;
- same `git_path` object observed at source/interpreter/authorities;
- source-root canonical-value binding asserted;
- real authorities validator route exercised with only its underlying fixed-I/O mocked/stubbed;
- legacy environment/D005 pair route remains unreachable;
- one reidentified mutation per eight section fails through `load_execution_request()`/`main()`;
- hostile ambient independence and future run/candidate roots remain uncreated/unopened;
- stdlib CPU suite / `py_compile` / `git diff --check` PASS.

No real request creation, preflight, staging/materialization, record/refreeze, evidence publication, P5 export/compose, torchrun, CUDA/GPU, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized by this review.
