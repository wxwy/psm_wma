# R09-B2 P4-v4 execution preflight v0.5 design review

## Object

- Request / Design: `5e8acad14765fdc40a5967c7758fd046a786956a`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

## Findings

### HIGH — execution authorization boundary is still underspecified

The v0.5 design correctly limits scope to CPU-only, copy-only candidate preflight and explicitly forbids record/refreeze, P5 export/compose, GPU and training. However, before authorizing execution, the exact execution request contract is not frozen.

Need exact immutable fields:

- entry script SHA;
- request JSON SHA;
- interpreter SHA/path identity;
- source revision;
- evidence/P1/P3/P5 authority identities;
- output run root generation rule;
- candidate root generation rule;
- allowed environment.

The design currently says these will be frozen in an approved execution request, but that execution request is a future artifact.

### HIGH — candidate execution must define publication handoff more strictly

The design says PASS remains candidate and waits for independent record/refreeze. Correct.

Need additionally freeze:

- candidate directory exact schema;
- failure artifact location;
- whether candidate root may be inspected after failure;
- no cleanup/retry semantics;
- how the later refreeze consumes immutable candidate bytes.

### MEDIUM — command contract needs exact interpreter identity

The command template:

`python -I -S -B tools/g0/<reviewed-p4-v4-preflight-entry>.py`

is directionally correct, but `<reviewed-p4-v4-preflight-entry>` and `python` identity are placeholders. Execution approval must not approve placeholders.

## Positive observations

- Static tooling closure prerequisite is correctly separated from execution.
- No P5 export/compose/GPU/training authority is requested.
- Fresh run-root and copy-only semantics are correct.

## Gate decision

Not authorized:

- APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY
- actual preflight execution
- staging creation
- candidate materialization
- record/refreeze
- evidence publication
- GPU/training
