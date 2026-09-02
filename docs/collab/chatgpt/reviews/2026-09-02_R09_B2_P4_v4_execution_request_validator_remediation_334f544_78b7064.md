# R09-B2 P4-v4 execution-request static validator remediation review

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_STATIC_TOOLS`

## Reviewed objects

- remediation implementation: `334f544f1d9a4cb130dbbbbb7df042d3dd0b06cf`
- review request: `78b70645865615517774c9c02dfef5f5f658015e`
- status-only follow-up: `2547d3db917ab373f40da2cfb13c84b59c2651ab`
- prior ChatGPT blocker review: `d5f4bacee690dfb5c4588026f24d02b8d324142e`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Findings

### PASS — HIGH TOCTOU blocker closed

The prior implementation hashed one pathname read and parsed a second pathname read. The remediation now:

1. opens the request once using `os.open(..., O_NOFOLLOW | O_RDONLY)`;
2. validates the opened object with `fstat()` as a regular file;
3. reads one `raw: bytes` value from that descriptor;
4. computes SHA256 from that exact `raw`;
5. parses canonical JSON/schema/execution-contract from the same exact `raw`;
6. performs no pathname re-open before the unconditional hard-stop.

The regression test additionally rejects any `Path.read_bytes()` fallback and asserts exactly one `os.open()` call on the accepted path.

This closes the previously identified identity break: `frozen SHA bytes == validator-consumed bytes`.

### PASS — MEDIUM mutable-contract blocker closed

The mutable exported `EXECUTION_CONTRACT` dict was removed. Accepted semantics are represented by immutable `_EXECUTION_CONTRACT_ITEMS` tuple and captured as the default argument of `load_execution_request()`. Rebinding the module-level private name after function definition therefore does not change the accepted contract. The committed regression exercises this case.

### PASS — scope remains static/fail-closed

After request SHA and static validation, the entry still unconditionally raises `RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")`. No staging/candidate creation, materialization, record/refreeze, evidence publication, P5 authority update, export/compose, torch/GPU/model/data/checkpoint I/O, training/eval/inference, or B2-T path is authorized by this review.

## Remaining work before any execution approval

This verdict only permits continued root static parser/validator tooling and stdlib CPU tests. The nested request sections (`entry`, `source`, `interpreter`, `environment`, `run`, `candidates`, `backends`, `authorities`) still require exact per-section grammar/identity validation and a separately reviewed concrete execution request before `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY` can be considered.

## Authorized scope

- root static execution-request parser/validator implementation
- stdlib CPU regression tests
- static documentation/contracts supporting that implementation

## Forbidden scope

- real P4-v4 preflight execution
- staging/materialization/candidate generation
- record/refreeze or evidence publication
- P5 authority population/update
- P5 export/compose
- torchrun/GPU/CUDA
- model/data/checkpoint I/O
- training/evaluation/inference/B2-T/Local Memory training
