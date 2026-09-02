# ChatGPT independent review — R09-B2 P4-v4 execution request `run` static closure

- Implementation: `8295b93bb9e64c24ebf0d8783a8f7ccfcf348750`
- Review request: `fd6fc69bb58c3ebd6f789938691ea97cd2ffff9b`
- Approved design: `3609ae9a9c24e2565cb3c31d74a20a03490c21ad`
- Prior ChatGPT review: `a51184ee6a710e64aea232ebc2c3636a7c0e433f`
- Gitlink at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_RUN_STATIC_TOOLS`

## Independent findings

The prior implementation review found the run validator logic acceptable and requested only permanent fixture completion. This tests-only remediation closes those gaps without modifying the validator contract:

1. Exact run identity key-set drift is permanently rejected (extra/missing identity keys).
2. `run_token` grammar now has permanent negative coverage for lowercase non-hex, short, long, and previously covered uppercase values.
3. `roster_sha256` has independent permanent negative coverage for uppercase, lowercase non-hex, short, and long values.
4. `validate_run_pair()` is shown independent of hostile ambient `PATH`, `PYTHONPATH`, and `LC_CTYPE` and does not mutate the request.
5. Existing fixtures continue to cover exact two-backend schema, identity SHA/kind/resolved-root binding, backend root/token/roster reuse rejection, path normalization, repeated separators, ancestor symlink rejection, and source/submodule overlap.

The implementation/request boundary remains static-only. No run-root/staging/candidate creation, preflight execution, P5 export/compose, GPU/CUDA, model/data/checkpoint I/O, training/evaluation/inference, B2-T, record/refreeze, or evidence publication is authorized by this verdict.

## Closure

The `run` static section is closed. The remaining execution-request sections are `candidates` and `backends`; the later final immutable execution request and any CPU preflight execution remain separately gated.
