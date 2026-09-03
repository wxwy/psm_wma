# Independent Review — R09-B2 P4/P5 v4 Handoff Migration Design v0.1

- Gate: `G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION`
- Design / implementation SHA under review: `4ce8ad362b8d5a1471f9cd5ec09b599727dcaa62`
- Base SHA: `f942d7331e648bd90dbe63530f22e88a1748bf71`
- Ledger/request SHA observed at review start: `043f08fa797d266415798ca4c617ca19de82ec6f`
- Gitlink at design SHA: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_P5_v4_handoff_migration_design_v0.1_2026-09-03.md`
- Scope: static P4/P5 handoff grammar/tooling design only. No real request/preflight/materialization/staging/candidate/run-root, record/refreeze/evidence publication, P5 export/compose, torchrun, GPU/CUDA, model/data/checkpoint I/O, training, evaluation, inference, B2-T, or Local Memory training.

## Repository-state note

This review environment has no local checkout of `wxwy/psm_wma`, so a literal shell `git fetch origin V2` cannot be executed. I therefore resolved the authoritative remote `V2` branch directly through the connected GitHub repository API immediately before review and again before concluding. The remote head was `043f08fa797d266415798ca4c617ca19de82ec6f`, a ledger/request-only commit whose parent is exactly the design SHA `4ce8ad362b8d5a1471f9cd5ec09b599727dcaa62`. The Gitlink at the design SHA is exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

The design SHA itself only adds the migration design and status bookkeeping; it does not modify P4/P5 runtime/tool code or the submodule. No independent GitHub status checks are attached to the design SHA.

## Verdict

`REQUEST_CHANGES`

The fixed-point diagnosis and migration direction are correct, but v0.1 is not yet internally implementable against the already-frozen P4/P5 contracts. Two HIGH design blockers must be closed before implementation authorization.

## HIGH-1 — v2 roster is not filesystem-closed for legal nested payload-manifest paths

**File:** `docs/build/PSM-WMA_R09_B2_P4_P5_v4_handoff_migration_design_v0.1_2026-09-03.md:17-22, 42-44`

### Root cause

The proposed v2 exact path set is:

`{import_staging, import_staging/<run_token>} ∪ {payload_manifest.entries[*].path}`.

That set includes only two directory rows plus regular-file manifest rows.

However, the already-closed P4 lock manifest grammar accepts nested relative regular paths. `tools/g0/r09_b2_p4_v4_execution_preflight.py::_validate_payload_manifest()` rejects absolute/empty/dot/dotdot/repeated-separator paths, but it does not restrict a valid regular path to a single level. A path such as:

`import_staging/<run_token>/pkg/sub/mod.py`

is therefore legal under the frozen manifest grammar.

At the same time, P5 `tools/g0/export_r09_b2_p5_resolved_config.py::_validate_roster()` recursively enumerates **all** run-root filesystem entries with `rglob("*")` and requires that actual set to equal the roster path set. Materializing the example necessarily creates intermediate directories:

- `import_staging/<run_token>/pkg`
- `import_staging/<run_token>/pkg/sub`

but v0.1 does not place them in the roster. Thus a legal, self-consistent P4 payload manifest can derive a pre-execution roster SHA that can never satisfy the P5 actual-tree validator.

There is a second part of the same root issue: the design does not freeze reserved namespace / file-vs-directory collision semantics. A manifest entry may collide with `import_staging` or an ancestor needed for another manifest path unless the migration explicitly forbids it or derives the directory closure deterministically.

The current P5 manifest grammar is also weaker than the closed P4 grammar in several details (for example repeated separators / dot components / strict lowercase-hex SHA / duplicates). A cross-Gate canonical roster derivation must not leave P4 and P5 validating different manifest languages.

### Required fix / acceptance criteria

Revise the design before implementation so one verifier-owned derivation is total over every admitted manifest. Preferably:

1. Define a single deterministic `derive_v2_roster_entries(payload_manifest, run_token)` contract.
2. Derive **all required ancestor directory rows** for every regular manifest path, excluding only the run root itself; deduplicate and sort them deterministically.
3. Keep directory rows exact `type=directory, mode=0555, sha256=""`; regular rows exact `type=regular, mode=0444` with manifest SHA.
4. Freeze reserved namespace rules and reject file/directory collisions, duplicate path identities, and P4 evidence/pointer names. Explicitly state whether every payload regular path must be under `import_staging/<run_token>/`; if that is the intended contract, make it a hard rule.
5. Make P5 validate the **same manifest grammar** as the closed P4 manifest grammar, preferably via one pure shared validator/deriver or exact parity fixtures.
6. Require actual recursive run-root path set to equal this filesystem-closed derived set.
7. Add permanent design-required fixtures for at least a deeper path such as `import_staging/<token>/pkg/sub/mod.py`, plus file-vs-directory collision, reserved namespace, duplicate, dot/repeated-separator and malformed-SHA negatives.

Narrowing the P4 manifest to flat filenames would reopen an already-closed contract and is not an acceptable silent workaround in this Gate.

## HIGH-2 — “P4 planned projection and P5 roster byte-identical” contradicts the frozen wire schemas

**File:** `docs/build/PSM-WMA_R09_B2_P4_P5_v4_handoff_migration_design_v0.1_2026-09-03.md:30-32, 42`

### Root cause

The design requires the P4 planned projection and P5 roster built from the same manifest/token to be “字节及 SHA 相同”. But the already-closed P4 wire object is:

`{"entries": ..., "projection_sha256": ...}`

because `STAGING_PROJECTION_KEYS = {"entries", "projection_sha256"}` and `_planned_projection()` returns exactly that shape.

The P5 embedded roster object is intentionally kept as:

`{"entries": ..., "sha256": ...}`.

Even if the entries and underlying digest are mathematically identical, these two complete canonical JSON objects can never be byte-identical because their digest field names differ.

Renaming P4 `projection_sha256` to `sha256` inside this migration would silently alter the already-reviewed planned-lock commitment wire schema and its commitment identity, effectively reopening `4108eb63` without a dedicated schema/lock Gate.

### Required fix / acceptance criteria

Revise the design to preserve the closed P4 wire schema and compare semantic projection identity, not whole-object bytes:

1. Explicitly freeze P4 `staging_projection={entries,projection_sha256}` unchanged.
2. Define one internal derived entry list `entries = derive_v2_roster_entries(manifest, token)`.
3. Define one digest `d = SHA256(P5 canonical_bytes({"entries": entries}))`.
4. Require P4 `staging_projection.entries == entries` and `projection_sha256 == d`.
5. Require P5 roster exactly `{"entries": entries, "sha256": d}`.
6. Replace the current acceptance wording “字节及 SHA 相同” with the exact cross-schema equality above.
7. Add a permanent regression that P4 `STAGING_PROJECTION_KEYS` remains exactly `{entries,projection_sha256}` and that the existing planned-commitment outer wire keys are unchanged.

If the project instead intends to rename/change the P4 planned commitment schema, that requires an explicit reopened P4 lock/schema design Gate and a new implementation review; it must not be smuggled into this migration.

## Accepted direction / do not reopen unnecessarily

The following aspects of v0.1 are sound and should be preserved:

- The fixed-point diagnosis is real: current P5 `_validate_roster()` forces `preflight.json` into the run-root roster while result/verification bind the roster digest.
- Keeping `request.json` / `result.json` / `verification.json` solely under the P5 evidence-authority path and permanently out of the readonly run root is the correct separation.
- Keeping the embedded P5 roster key set exactly `{entries,sha256}` is reasonable.
- `AUTHORIZED_P4_V4_LOCK_SPEC` and `AUTHORIZED_P4_V4_EVIDENCE` must remain `None` through this static migration implementation.
- `run_parent_export()` hard-stop and all current no-runtime/no-GPU/no-training boundaries should remain.
- Existing request/result `p4_run` and `p4_staging` equality, P5 exact Git evidence authority, P3-owned backend difference, lexical loader/bootstrap and exporter hard-stop must not regress.

## Gate status

Do **not** implement v0.1 as written.

After the two HIGH items above are fixed in a new design SHA and that SHA is independently re-reviewed, the intended positive verdict remains:

`APPROVE_TO_IMPLEMENT_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS`

Even such approval would authorize only root static P4/P5 grammar/loader/verifier tooling and stdlib CPU fixtures. It would not authorize real P4 request/preflight/materialization/staging/candidate/run-root, record/refreeze/evidence publication, P5 authority update/export/compose, torchrun, GPU/CUDA, model/data/checkpoint I/O, training, evaluation, inference, B2-T, or Local Memory training.
