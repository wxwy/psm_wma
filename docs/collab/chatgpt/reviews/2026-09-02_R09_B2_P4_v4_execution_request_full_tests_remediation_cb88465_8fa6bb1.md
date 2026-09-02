# Independent review — R09-B2 P4-v4 Execution Request FULL tests remediation

- Review anchor: `cec66b1c31548de5c52f878d0d448474ad98b403`
- Tests-only remediation: `cb88465b9dd93ace2bd37046e4e76d411cae3d39`
- Formal request / ledger HEAD: `8fa6bb149118f46c27b5ef01b712eaa67b324f94`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Approved design: `fad1e8d6959fcfee76129e04dc213e7fd6ea49f1`

## Verdict

`REQUEST_CHANGES`

Production orchestration from `c3b64b5ab56fde2669a5af739fbbc1d97a1a4733` remains acceptable and is unchanged by this remediation. B1 (exact eight-validator order) is now closed. The remaining blockers are fixture-only.

## Findings

### HIGH — Full composition still replaces `validate_source` and `validate_interpreter` instead of exercising the frozen validators

File: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py`, `FullAdmissionCompositionTest._load`.

The approved v0.2 design required a route-only composition fixture that mocks the **lower-level I/O of closed source/interpreter/authorities validators**, while the correct validators themselves remain on the full route. The remediation now executes real `validate_authorities_pair()` via `wraps`, but `_load()` still replaces both `validate_source` and `validate_interpreter` with `source_spy` / `interpreter_spy`.

Consequences:

1. the nominal full-valid composition request is not demonstrated to pass the frozen source/interpreter validators;
2. the source mutation (`source.root = "/wrong"`) is rejected by the synthetic `source_spy`, not by `validate_source`;
3. the interpreter identity mutation is rejected by the synthetic `interpreter_spy`, not by `validate_interpreter`.

This leaves B2/B3 only partially closed.

Required remediation: keep `validate_source` and `validate_interpreter` real in the composition fixture. Patch only their already-closed lower-level I/O/provenance dependencies (for example fixed Git/file/interpreter helper calls as needed), or construct a minimal valid temp fixture that makes the real validators pass. Then prove the source and interpreter reidentified mutations fail through those real validators.

### CLOSED — Exact full validator order

`test_full_route_calls_frozen_validator_order` explicitly freezes:

`entry -> host_git -> source -> interpreter -> run -> candidates -> backends -> authorities`

This closes the prior B1 ordering gap.

### CLOSED/PARTIAL — Authorities/environment composition route

The new composition fixture executes real `validate_authorities_pair()` and confirms the legacy `validate_environment_pair` / `verify_d005_pair` routes are unreachable. Environment/authorities binding is therefore materially improved and acceptable. The remaining issue is limited to source/interpreter being replaced by synthetic spies.

## Scope / safety

- `cec66b1... -> 8fa6bb1...` changes only tests plus ledger/status; production parser is unchanged.
- Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.
- No real execution request, preflight, candidate/run/staging materialization, record/refreeze, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized by this review.

Expected next submission: tests-only remediation. No production rewrite is requested unless the real source/interpreter composition fixtures expose an actual implementation defect.
