# ChatGPT Independent Review — R09-B2 P4-v4 execution-contract static validator

- Date: 2026-09-02
- Root review request: `a2effdeb4386253bddaca0d51a4f26bb98b0c755`
- Implementation chain reviewed: `5f77dabc0d12c5b4a67c1f1aa38f4d586f6b307c` + `2376de2a95626d55d26d4ae55274205433993c11`
- Frozen submodule/Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Prior ChatGPT anchor: `f3cd5a60481bc9b8a82e951839bb55e99df69417`

## Verdict

`REQUEST_CHANGES`

This verdict is limited to the root static execution-request parser/validator. No real preflight execution is authorized.

## HIGH — request SHA binding and parsed bytes are TOCTOU-separated

`tools/g0/r09_b2_p4_v4_execution_preflight.py:24-31,50-55`

The entry currently validates the request in two independent reads:

1. `request_sha256(path)` checks path type and hashes `path.read_bytes()`.
2. `load_execution_request(path)` calls `path.read_bytes()` again and parses/validates those second bytes.

Therefore the bytes that satisfy the frozen `--request-sha256` are not guaranteed to be the bytes that satisfy the canonical JSON/schema/execution-contract checks. A replacement/modification between reads can make SHA admission apply to request A while schema validation applies to request B.

The same pattern also separates `is_symlink()/is_file()` from the later read, so the regular-file/no-symlink property is path-raceable.

This is inconsistent with the frozen execution-request identity requirement and should be fixed before this validator is allowed to advance.

### Required remediation

Bind file identity, SHA, and parsing to one read/descriptor:

- open the request once in a no-follow/fail-closed manner;
- verify the opened object is a regular file;
- read bytes once;
- compute SHA256 over those exact bytes;
- canonical-JSON/schema/contract validation must consume those exact same bytes, not reopen the path.

For the current Linux execution environment, an fd-based `os.open(..., O_NOFOLLOW)` + `fstat()` + one byte read is the strongest form. At minimum, the static API must be refactored so hash and parser share one immutable `raw` byte string and there is no second pathname read.

Add a CPU regression that proves the parser consumes the same byte object that was SHA-bound / that the request file is not independently re-read after SHA admission.

## MEDIUM — the supposedly frozen execution contract is a mutable module-level dict

`tools/g0/r09_b2_p4_v4_execution_preflight.py:15-22,42-43`

`EXECUTION_CONTRACT` is exported as a mutable `dict`. In-process mutation before `main()` changes what the validator accepts. The normal isolated CLI path reduces practical exposure, but a frozen authority constant should not be mutable by ordinary importers/tests.

Recommended remediation: represent the frozen contract with an immutable internal form and construct/compare the expected JSON mapping without exposing a mutable authority object, or otherwise prove mutation cannot change accepted contract semantics.

This item is secondary to the HIGH blocker but should be closed before static-tool closure.

## Positive findings

- Canonical JSON bytes are required.
- Top-level keys are exact; unknown top-level fields fail closed.
- Schema version is exact.
- The newly introduced execution contract explicitly freezes network/GPU/torch/model-data-checkpoint I/O off, one-shot on, and cleanup/retry/repair off.
- Even a SHA-valid/schema-valid request still ends in unconditional `RuntimeError`; there is no staging/candidate/materialization/GPU/training path in this implementation.
- Gitlink at the review request remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Scope / authorization

Allowed after this review: CPU/static-only remediation and tests for the execution-request validator.

Not authorized:

- `APPROVE_TO_EXECUTE_P4_V4_PREFLIGHT_CPU_ONLY`
- real preflight execution
- staging creation/materialization
- candidate generation/publication
- record/refreeze
- evidence publication
- P5 authority update
- P5 export/compose
- torchrun/GPU/CUDA
- model/data/checkpoint I/O
- training/evaluation/inference/B2-T

After remediation, submit a new root SHA with the same frozen Gitlink for independent re-review.
