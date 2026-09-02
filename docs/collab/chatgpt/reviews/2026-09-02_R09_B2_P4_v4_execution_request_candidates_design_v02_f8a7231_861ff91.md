# ChatGPT independent review — R09-B2 P4-v4 execution request `candidates` v0.2

- Design commit: `f8a7231b76fe04e3a570dc2e432da8e018008cd5`
- Request/ledger commit: `861ff91ff4e65bb0258c2f5c46951d7dfb831c3d`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Prior review: `b82e299f64af89e9ca3d877fe612f8e48b172e5d`

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_CANDIDATES_STATIC_TOOLS`

## Findings

The v0.1 blockers are closed:

1. Outer `candidates.identity_sha256` now has exact canonical self-digest semantics and lowercase-64-hex grammar.
2. Each backend record now contains exact `{backend,candidate_root,run,identity_sha256}` and requires `run` to be canonical-equal to the corresponding `request.run.<backend>` full object, so candidate→run cross-binding is machine-verifiable without inference.
3. The candidate namespace root and both derived backend leaves are required to be lexically non-overlapping with both run roots, in addition to source/submodule isolation.
4. Both namespace root and derived leaves reuse the same future lexical path validation, including existing-prefix `lstat` symlink rejection.
5. `attempt_id` is exact lowercase 64-hex and explicitly differs from both backend run tokens.

The design remains static-only and does not authorize reading/creating candidate/run/staging trees, materialization, preflight, P5, GPU, model/data/checkpoint I/O, training/eval/inference, or evidence publication.

## Implementation requirements

Permanent stdlib CPU fixtures should directly cover all frozen v0.2 branches: exact outer/inner key sets and identities; attempt grammar and inequality against both run tokens; backend labels; exact derived leaf mapping; canonical-equal embedded run object; namespace and leaf overlap against source/submodule and both run roots; relative/dot/dotdot/repeated/double-separator paths; existing-prefix symlink rejection on root and leaf; backend/root/run/identity reuse; hostile ambient environment independence; and proof that no future root is created.

Lifecycle note: the static request is non-executable. When a later full-request Gate replaces the run section's placeholder roster SHA with deterministic final roster digests, the embedded `candidates.<backend>.run` objects and dependent backend/outer candidate identities must be regenerated in the new immutable final request so canonical equality remains exact. This does not require a schema change.
