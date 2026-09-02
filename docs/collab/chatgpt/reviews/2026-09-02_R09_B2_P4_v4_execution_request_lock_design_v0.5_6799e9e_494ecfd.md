# ChatGPT Independent Review — R09-B2 P4-v4 Execution-Request Lock design v0.5

- Design commit: `6799e9e94cf55dde4df8c3cd8c4870de9eb28edb`
- Request ledger commit: `494ecfd3b63e5793bccc88a26be75c491b2311de`
- Prior ChatGPT anchor: `000b573d94a503ca201d5710035da4d1a0ac3140`
- Gitlink verified: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: static planned-commitment design only; no P4/P5 migration implementation, real request/preflight/materialization/staging/candidate/record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, evaluation/inference, B2-T or training.

## Verdict

`REQUEST_CHANGES`

The v0.4 blockers were addressed in the right direction: pair-level candidate attempt semantics now match the closed candidates contract, `source_tree_oid` is correctly defined as a 40-hex Git tree object id rather than a SHA256, and the spec-to-commitment mapping is substantially more explicit. The v2 roster migration that removes `preflight.json` from the run-root roster remains the correct way to eliminate the P4/P5 hash fixed point.

Three design blockers remain before static implementation.

### B1 — lock spec reintroduces premature `roster_sha256`

The v0.5 spec requires `run` to use the closed exact run grammar and `candidates` to use the closed exact candidates grammar. The closed run grammar is `{identity,run_token,roster_sha256}` for each backend, and each closed candidate backend object embeds the complete matching `run` object. Therefore the proposed spec necessarily contains `roster_sha256` fields even though the same design states that the pre-migration commitment must not carry or accept any premature `roster_sha256`, and its fixtures explicitly reject old/premature roster SHA fields.

Do not reuse the executable/final run object verbatim here. Define a planned-run/spec grammar that contains only the pre-execution authority needed at this Gate, e.g. `{identity,run_token}`, and a candidates-planning grammar whose backend binding refers to that planned-run identity without embedding a final `roster_sha256`. The later independently reviewed migration/refreeze Gate may construct the final closed run object by adding the deterministic v2 roster SHA.

### B2 — `planned` self-SHA has no schema field

The exact `planned` key-set is stated as `{root,attempt_id,recurrent,ttt_fast_weight}`, but the same paragraph requires "每 backend、planned、commitment 的 self SHA". Backend objects have `identity_sha256` and top-level has `commitment_sha256`; `planned` has no field that can carry its required self hash.

Either add an exact `identity_sha256` (or another explicitly named field) to the `planned` key-set and freeze its calculation, or remove the planned-level self-SHA requirement. Do not leave an implementation-defined hidden/parallel hash.

### B3 — source-root anchor for opening the authoritative spec is still undefined

`AUTHORIZED_P4_V4_LOCK_SPEC` contains `source_commit`, `source_tree_oid`, Gitlink, a relative `spec_path`, spec hashes, and output identity, while caller/CLI/cwd/environment are forbidden from supplying authority. The tool therefore still lacks a frozen rule for locating the source root *before* it can open and parse `spec_path` and verify the commit/tree/blob bindings.

Freeze one unambiguous source-root anchor. Acceptable examples are: an absolute lexical source-root identity in the reviewed constant, verified through the same `/`-anchored nofollow component walk; or a precisely specified derivation from the tracked tool's own already-verified source identity, with the exact nofollow/FD semantics frozen. The spec cannot bootstrap its own source root because the tool must locate the spec before reading it.

## Closed / retained

- v2 run-root roster migration permanently excluding `preflight.json`/evidence pointers: accepted design direction.
- P5 canonical roster serializer/hash alignment: accepted.
- shared pair-level `candidates.attempt_id`, pair candidate root and backend candidate path derivation: corrected.
- `source_tree_oid` as `git rev-parse <commit>^{tree}` 40-hex Git OID: corrected.
- output `O_RDWR` single-FD write/fsync/read-back/fchmod/fstat/close and terminal poison semantics: retained.
- default `AUTHORIZED_P4_V4_LOCK_SPEC=None` fail-closed: retained.

No authorization is granted for P4/P5 migration implementation or any real execution side effect.
