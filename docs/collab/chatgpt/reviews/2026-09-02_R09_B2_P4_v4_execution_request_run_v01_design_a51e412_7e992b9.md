# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `run` v0.1 design

- Design commit: `a51e41232a324679b199c164bb1c9641ef0ad81f`
- Request/ledger commit: `7e992b98fb1d830b7c0b290871e521878bbb7f4b`
- Frozen Gitlink re-read at request HEAD: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: static design only; no real preflight/staging/materialization/P5/GPU/training authorization.

## Verdict

`REQUEST_CHANGES`

## Findings

### HIGH — `run` cardinality cannot express the frozen two-backend requirement

The design defines request `run` as one exact object:

`{identity, run_token, roster_sha256}`

but later requires the two backends' `run_token`, run-root identity and roster SHA to be pairwise different. A single object has no backend dimension, so this condition cannot be represented or machine-validated in the current request schema.

The existing P5 handoff consumes one `p4_run={identity,run_token,roster_sha256}` **inside each backend request**. Therefore the root execution request must define an explicit backend mapping/pair (for example exact `{recurrent,ttt_fast_weight}` whose values each retain the already-frozen inner P5 key set), or otherwise freeze an equally explicit mapping from the root `run` section to the two backend P4 requests. Do not leave this mapping to implementation inference.

### HIGH — `roster_sha256` lifecycle is not satisfiable as an arbitrary placeholder

The design calls `roster_sha256` a 64-hex placeholder and defers roster materialization/final consistency to the later execution Gate. However the already-frozen P5 loader requires, per backend:

1. request `p4_run` == result `p4_run`; and
2. `request.p4_run.roster_sha256 == result.pre_p5_run_root_roster.sha256`.

Thus a random syntactic placeholder cannot become executable without changing/refreezing the request or without having been deterministically derived from the exact planned roster before execution.

The design must freeze one lifecycle explicitly. Acceptable shapes include: (a) the static `run` section only defines grammar and a later candidates/backends/full-request Gate deterministically fills/cross-binds the final roster digest before execution, with any non-final placeholder explicitly non-executable; or (b) define the exact candidate→planned-roster derivation that computes the final digest before materialization. In either case, the final execution request must be immutable through preflight and already contain the digest P5 will later verify.

### HIGH — trust-root/non-overlap authority is undefined at this section

The design requires the future run root to avoid "any Git trust root" and existing staging/candidate/evidence/exporter paths, while simultaneously saying this section only validates declared/static relationships and the later `candidates` section is not yet frozen. Those path sets are not named inputs to the current `run` object and no frozen authority supplies them, so the rule is not presently machine-verifiable.

Also, the design says `root == resolved_root` and rejects symlink aliases while the final component is expected not to exist. The existing P5 path identity uses non-strict `Path.resolve()` semantics; an existing symlink ancestor can therefore make the resolved spelling differ even when the final run root does not yet exist. The run design should freeze the same lexical/canonical rule now (e.g. explicit `resolve(strict=False)`/existing-prefix semantics without creating the final path), rather than leaving symlink-ancestor behavior to implementation choice.

Required remediation: either (1) restrict this section's overlap checks to named currently-available authorities (at minimum verified `source.root`/submodule and any exact frozen roots), and defer candidate/staging/evidence/exporter overlap to their later sections/full-request Gate; or (2) add an exact named authority supplying those roots. Do not maintain an implicit/ambient path denylist.

## What is already sound

- Static-only scope and prohibition boundaries are appropriate.
- Reusing the frozen inner P5 `p4_run={identity,run_token,roster_sha256}` key set is correct.
- Not requiring `resolve(strict=True)` on a future nonexistent run root is correct in principle.
- Token/digest lowercase 64-hex grammar and identity self-digest are reasonable once backend cardinality/lifecycle are fixed.

## Required next revision

A v0.2 design should freeze:

1. exact two-backend representation/mapping for `run` while preserving the P5 inner key set;
2. exact `roster_sha256` finalization/refreeze or deterministic pre-materialization lifecycle, with no executable placeholder ambiguity;
3. exact currently-authoritative root set and non-strict canonical/symlink-ancestor semantics, deferring not-yet-existing candidate/staging roots to their owning Gate unless explicitly named here.

No implementation authorization is granted by this review.
