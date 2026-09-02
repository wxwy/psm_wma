# R09-B2 P4-v4 Execution Request `run` v0.2 static implementation review

- Implementation: `c86b0b522f129f5ea5449882e7095a803aa1409d`
- Request/ledger HEAD: `940f0f81b33251509675d3c2cc65fd4785b84e51`
- Approved design: `3609ae9a9c24e2565cb3c31d74a20a03490c21ad`
- Design approval: `e23722de3725cb89d41ff0a8aaca5f358726b279`
- Gitlink re-read at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

The production/static validator is consistent with the approved v0.2 design: exact two-backend `run` pair, frozen P5 inner key set, canonical identity SHA, lowercase 64-hex token/roster grammar, backend reuse rejection, non-strict future-path lexical checks, ancestor-symlink rejection, and source/submodule overlap rejection are all implemented. I found no new production-logic blocker and no authorization expansion into real preflight/run-root creation.

Closure is blocked only by the permanent CPU fixture contract frozen in v0.2.

## Blocking fixture gaps

The approved design requires permanent negative fixtures for `uppercase/non-hex/length` digest errors and ambient path/environment independence. Current `RunAuthorityTest` covers an uppercase `run_token`, but does not permanently cover:

1. a well-shaped lowercase/non-hex `run_token` rejection;
2. short/long `run_token` length rejection;
3. `roster_sha256` grammar independently (uppercase or non-hex and short/long length); and
4. an explicit ambient `os.environ` / PATH-independence positive fixture proving `validate_run_pair()` reaches the same result with hostile/unrelated environment values.

These are explicitly part of the approved v0.2 CPU acceptance matrix, so the section cannot be closed on 48/48 alone.

## Required remediation

Tests-only remediation is sufficient. Add permanent stdlib CPU cases for the four groups above. Mutations should preserve all non-target fields so they reach the intended run-digest/ambient branches. No production validator change is requested unless a new test exposes a defect.

Continue to prohibit real preflight, run-root/staging/candidate creation, record/refreeze, P5 export/compose, torch/GPU, model/data/checkpoint I/O, training/eval/inference.

## Progress

Closed execution-request sections remain 5/8: `entry`, `source`, `interpreter`, `environment`, `authorities`. `run` remains implementation-in-review until the frozen fixture matrix closes.
