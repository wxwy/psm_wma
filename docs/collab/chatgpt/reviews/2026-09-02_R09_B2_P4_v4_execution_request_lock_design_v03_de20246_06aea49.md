# ChatGPT Independent Review — R09-B2 P4-v4 Execution-Request Lock Design v0.3

- Verdict: `REQUEST_CHANGES`
- Design commit: `de20246266b514bab7459ba52eb2b7d5f24f4cdd`
- Request / ledger commit: `06aea49a11a060d86355bbef707d1b1dc8ddf0c7`
- Previous ChatGPT review anchor: `e6593d52496583c288fd4a31eef53165c2f3ed59`
- Frozen Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope reviewed: only the three blockers from v0.2 plus scope drift introduced by replacing final-request lock output with a planned-roster commitment.
- Other reviewers' verdicts were not used as evidence.

## What v0.3 closes

### v0.2 B1 — same-FD output I/O contract: CLOSED

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_lock_design_v0.3_2026-09-02.md:27-31` now uses one `O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` FD, then full write, `fsync`, same-FD seek/read-back, `fchmod(0444)`, `fstat`, and close. Post-create failures remain terminal `POISONED_NOT_LOCKED`. This is implementable and preserves the intended no-repair/no-retry semantics.

### v0.2 B2 — P5 roster object/hash grammar: direction CLOSED

`...lock_design_v0.3...:17-25` no longer invents a parallel final digest. It explicitly defines the staging projection rows with P5's `{path,type,mode,sha256}` grammar and defers the final roster object to `{entries,sha256}` with `sha256 = SHA256(canonical_bytes({"entries": entries}))`, matching `tools/g0/export_r09_b2_p5_resolved_config.py::_validate_roster()` / `_self_sha()` semantics.

This part is acceptable provided the later final-roster Gate uses the exact same canonical serializer and exact final ordered `entries` array.

## Blocking findings

### B1 — `preflight.json` ↔ `result.json` creates a cryptographic self-reference cycle

**Location:** `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_lock_design_v0.3_2026-09-02.md:13-25`, especially the requirement that `preflight.json` contain actual `result_sha256` / `verification_sha256`, and that the later final roster contain the SHA of that `preflight.json`.

The existing P5 handoff makes the cycle concrete:

- `tools/g0/export_r09_b2_p5_resolved_config.py::_validate_roster()` requires the final run-root roster to include `preflight.json`.
- `load_p4_v4_preflight()` requires `request["p4_run"]["roster_sha256"] == outcome["pre_p5_run_root_roster"]["sha256"]`.
- Therefore `result.json` contains a roster whose hash depends on the actual SHA of `preflight.json`.
- v0.3 simultaneously requires `preflight.json` to contain the actual SHA of `result.json`.

That yields the dependency:

```text
P = SHA256(preflight.json(... result_sha256=R ...))
R = SHA256(result.json(... roster_sha256=H(entries including preflight_sha256=P) ...))
```

This is not merely a sequencing problem. It is a hash fixed-point problem. A post-execution `record/refreeze` phase cannot compute its way out of it without changing one side of the contract.

The design also states at `:35` that real preflight must first have an exact final request raw/SHA, while `:25` says the final request's roster digest can only be formed after actual `preflight.json` exists. The existing public P4 path likewise admits only full `r09_b2_p4_v4_execution_request_v1` and hard-stops before any execution; there is no admitted partial-request path.

**Required remediation:** break the cycle explicitly. One acceptable architecture is:

1. Make run-root `preflight.json` a pre-execution immutable commitment that does **not** contain hashes of `result.json` / `verification.json` that themselves depend on the run-root roster; or
2. Exclude post-preflight `preflight.json` from the roster committed by the preflight input request and bind that file separately in post-preflight evidence.

Either choice changes the current P4/P5 handoff grammar and therefore needs an explicit reviewed migration contract. Do not claim the current `record/refreeze` phase alone resolves the cycle.

### B2 — new `r09_b2_p4_v4_planned_roster_commitment_v1` output schema is not frozen enough for implementation

**Location:** `...lock_design_v0.3...:15-23`.

v0.3 materially changes the artifact under review: the Gate no longer outputs the already-frozen execution-request schema and instead introduces a new canonical `r09_b2_p4_v4_planned_roster_commitment_v1`. The design describes what it conceptually contains, but does not freeze an exact top-level key-set / per-backend key-set / identity-or-self-hash fields / exact placement of the closed request-section identities / exact candidate+attempt binding shape.

For a canonical commitment object, these details are part of the security contract, not implementation trivia. Without them, the static implementation would be free to invent a representation whose bytes and authority semantics were never reviewed.

**Required remediation:** freeze the exact commitment schema before implementation, including at minimum:

- exact top-level key-set and `schema_version`;
- exact backend ordering and per-backend key-set;
- exact run/candidate/attempt/token fields and identities;
- exact representation of closed entry/source/interpreter/environment/authorities/backends bindings;
- exact `staging_projection` field shape and ordering;
- whether the commitment itself has a digest/self-identity and its exact hash formula;
- exact `AUTHORIZED_P4_V4_LOCK_SPEC` schema that authorizes this commitment output;
- exact output tool/file scope for the implementation request.

## Scope / authorization

No real request generation, preflight execution, materialization/staging/candidate/run-root creation, record/refreeze, evidence publication, P5 export/compose, torchrun, GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training is authorized by this review.

The P4-v4 full execution-request static admission and materialization static tooling remain closed; this review does not reopen them.

## Re-review target

A v0.4 design can be approved for static implementation if it:

1. keeps the v0.3 `O_RDWR` same-FD output/poison contract;
2. keeps the P5-compatible roster row/object/hash definition;
3. removes the `preflight.json` ↔ `result.json` hash cycle with an explicit P4/P5 handoff migration;
4. freezes the exact `planned_roster_commitment_v1` schema and authority schema;
5. preserves the current no-execution boundary.
