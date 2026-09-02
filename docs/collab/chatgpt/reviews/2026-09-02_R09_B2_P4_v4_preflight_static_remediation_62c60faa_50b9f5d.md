# R09-B2 P4-v4 static tooling remediation review

## Verdict

REQUEST_CHANGES

## Scope

- Request: `62c60faaeb0e605672c0ffd9fd8b54c39821626d`
- Implementation: `50b9f5d0cdd054244132c6087012cad7f23f7813`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Findings

### HIGH — closure evidence is insufficient

The implementation fixes the main code paths:

- token/run-root poison now rejects token reuse and run-root reuse;
- effective launch pair binding adds `cwd`, `toml`, `overrides`, `interpreter`, `loader_argv`, and `runtime_sys_path` checks.

However, permanent regression coverage is still missing.

Required tests:

- old token + new run-root => FAIL
- old run-root + new token => FAIL
- loader_argv drift => FAIL
- runtime_sys_path drift => FAIL
- full P5-valid pair => PASS

### MEDIUM — avoid monkeypatched closure paths

Closure tests must not bypass:

- `_validate_final_pair`
- `_reject_failed_identity_reuse`

Otherwise the tests do not prove the repaired trust boundaries.

## Decision

Not approved for:

`APPROVE_TO_CLOSE_P4_V4_PREFLIGHT_STATIC_TOOLS`

Still prohibited:

- real preflight execution
- staging/candidate materialization
- record/refreeze
- evidence publication
- P5 authority update
- GPU/training/B2-T
