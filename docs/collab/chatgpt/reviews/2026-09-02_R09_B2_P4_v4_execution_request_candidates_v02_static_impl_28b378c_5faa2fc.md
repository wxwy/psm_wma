# Independent review — R09-B2 P4-v4 execution request candidates v0.2 static implementation

- Verdict: `REQUEST_CHANGES`
- Implementation: `28b378c8861a2994fa6ae2f18b61d5ce8d909b8a`
- Closure request / ledger: `5faa2fcdfb9ed875df8dcdcb061e641eb88d830a`
- Approved design: `f8a7231b76fe04e3a570dc2e432da8e018008cd5`
- Prior design approval: `ce34350c07b50db09be99e70d2cfca50e77ebce5`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb` (independently re-read at request HEAD)
- Scope: static parser/validator + stdlib CPU fixtures only. No candidate creation, preflight, P5, GPU or training authorized.

## Accepted implementation

`validate_candidates()` implements the approved v0.2 structure in the intended direction:

- exact outer/root/backend key sets and canonical identities;
- 64-lowercase-hex `attempt_id`;
- backend record `run` canonical-equal to the corresponding closed `run.<backend>` object;
- derived candidate leaf exactly `<root>/<attempt_id>/<backend>`;
- candidate namespace/root and leaves rejected on source/submodule and both run-root overlap;
- `attempt_id` rejected when equal to either backend run token;
- shared `_future_lexical_path()` applies ancestor-symlink fail-closed behavior without materializing future roots;
- ambient environment is not consulted by the validator.

I found no new main-validator contract blocker in this submission.

## Required changes before closure

### 1. HIGH — approved v0.2 outer-schema fixture contract is not complete

Design v0.2 explicitly freezes permanent fixtures for outer `added/missing/retyped/digest drift`.

Current `CandidatesAuthorityTest.test_candidates_reject_exact_schema_and_identity_drift()` covers:

- outer extra/addition;
- outer identity digest drift;
- root identity drift;
- backend identity drift.

It does **not** permanently cover outer missing-key and outer retyped-value/schema cases. Add targeted fixtures that recompute unrelated identities where necessary so the intended outer schema/type branch is reached.

Affected file: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py` (`CandidatesAuthorityTest`, around the exact-schema/identity test).

### 2. HIGH — candidate-specific lexical grammar matrix is incomplete

Approved v0.2 requires candidate fixtures to cover the exact lexical grammar for both namespace root and derived leaf. The current candidates tests do not exercise candidate-specific:

- relative path;
- `.`;
- `..`;
- repeated separator;
- double-leading separator.

The older `RunAuthorityTest` coverage is not a substitute for the candidates section's permanent contract, because candidates adds derived-path mapping and candidate identities around the same helper.

Add mutations for candidates root and/or backend `candidate_root`, recomputing root/backend/outer identities as appropriate, and prove fail-closed behavior.

Affected file: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py` (`CandidatesAuthorityTest`).

### 3. HIGH — derived-leaf ancestor-symlink fixture does not reach the intended branch

The current symlink case makes the **candidate namespace root path itself** traverse a symlink (`linked/candidate`). It does not prove the approved v0.2 requirement that a clean candidate root can still fail when a **derived leaf's later existing prefix** is a symlink.

Add a real temp-filesystem fixture where:

- `candidates.root` is a normal canonical directory/path prefix;
- an existing child prefix such as `<root>/<attempt_id>` (or another prefix between root and backend leaf) is a symlink;
- backend `candidate_root` remains the exact derived spelling;
- validator rejects it through the leaf `_future_lexical_path()` path.

This proves the v0.2 derived ancestor-symlink rule rather than only the root-level rule.

Affected file: `tools/g0/test_r09_b2_p4_v4_execution_preflight.py` (`test_candidates_reject_source_run_overlap_and_symlink_ancestor`).

### 4. MEDIUM — finish explicit attempt/backend reuse grammar fixtures

For durable closure, add explicit `attempt_id` uppercase/short/long cases in addition to current non-hex, and a direct backend candidate-identity reuse mutation (with unrelated outer identity recomputed) so the v0.2 `identity reuse FAIL` clause is permanently exercised.

This is test-only remediation; no contract redesign or validator rewrite is requested unless a fixture exposes a real bug.

## Closure condition

Resubmit a new implementation SHA with only the missing permanent CPU fixtures (unless the new fixtures expose an implementation defect). Re-run the existing stdlib CPU suite, `py_compile`, and `git diff --check`. Keep all real candidate/preflight/P5/GPU/training actions prohibited.

Until then, `candidates` remains open and Execution Request progress remains 6/8 closed (75%).
