# Independent Re-review — R09-B2 P4/P5 v4 Handoff Migration Design v0.2

- Gate: `G0-R09-B2-P4-P5-V4-HANDOFF-MIGRATION`
- Design SHA under review: `f16f6e4d260114bb89c102e476a63d590751274e`
- Parent / prior ChatGPT review commit: `8f21b78e1b16750996b77bc3c4fe5567ccc3c3f7`
- Ledger/request SHA observed at review start: `2abdc36513bdd1630cfbb740784d264e6c4416d2`
- Gitlink at design SHA: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Design: `docs/build/PSM-WMA_R09_B2_P4_P5_v4_handoff_migration_design_v0.2_2026-09-03.md`
- Prior design: `4ce8ad362b8d5a1471f9cd5ec09b599727dcaa62`
- Prior review: `docs/collab/chatgpt/reviews/2026-09-03_R09_B2_P4_P5_v4_handoff_migration_design_4ce8ad3.md`

## Repository-state note

This review environment still has no local checkout of `wxwy/psm_wma`, so I could not literally execute shell `git fetch origin V2`. I therefore resolved the remote `V2` branch directly through the connected GitHub repository API immediately before review. At review start remote `V2` HEAD was `2abdc36513bdd1630cfbb740784d264e6c4416d2`, whose only change is the review-request append; its parent is exactly the design SHA `f16f6e4d260114bb89c102e476a63d590751274e`.

The design SHA itself is documentation/status-only: it adds the v0.2 design and updates `SESSION.md` / `TODO.md`; it does not modify P4/P5 tooling/runtime code or the submodule. Gitlink at the design SHA independently resolves to `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`. No GitHub status checks are attached to the design SHA.

## Verdict

`APPROVE_TO_IMPLEMENT_P4_P5_V4_HANDOFF_MIGRATION_STATIC_TOOLS`

The two HIGH blockers from the v0.1 review are closed at the design level without reopening the already-closed P4 planned-lock wire schema.

## Closure of prior HIGH-1 — filesystem-closed nested payload roster

v0.2 now freezes a single verifier-owned pure derivation:

`derive_v2_roster_entries(payload_manifest, run_token) -> entries`

The contract preserves the already-closed P4 manifest language rather than silently flattening it. It explicitly requires the P5 side to reuse the same P4 manifest grammar (or prove exact accepted-language parity), derives every non-root ancestor directory needed by arbitrary legal nested regular paths, and makes the actual recursive run-root path set exact-equal to the derived path set.

This closes the v0.1 impossibility where a legal path such as `import_staging/<token>/pkg/sub/mod.py` necessarily created unlisted `pkg` / `pkg/sub` directories.

The new design also freezes the missing collision/reserved namespace semantics:

- duplicate regular identities fail in the manifest validator;
- a regular file equal to a required directory fails;
- a regular file that is a strict ancestor of another regular file fails;
- reserved run-root paths `preflight.json`, `request.json`, `result.json`, `verification.json`, `candidate_link.json` fail;
- `import_staging` and `import_staging/<run_token>` are directory-only;
- directory rows are verifier-derived, deduplicated and sorted;
- directory rows are `{type:"directory",mode:"0555",sha256:""}`;
- regular rows are `{type:"regular",mode:"0444",sha256:<manifest SHA>}`.

The required fixture matrix now explicitly includes the deep nested-path positive, ancestor rows, collision/reserved paths, duplicate/path-grammar/SHA negatives and actual-tree extra/missing cases.

## Closure of prior HIGH-2 — cross-schema semantic identity, not whole-object byte identity

v0.2 explicitly preserves the P4 planned-lock wire object:

`staging_projection = {entries, projection_sha256}`

and preserves P5 embedded roster:

`{entries, sha256}`.

It no longer requires complete object byte equality. Instead, for the same verified manifest/token, the single derivation yields `entries` and:

`d = SHA256(P5 canonical_bytes({"entries": entries}))`.

The exact frozen cross-binding is now:

- P4 `staging_projection.entries == entries`;
- P4 `projection_sha256 == d`;
- P5 `roster.entries == entries`;
- P5 `roster.sha256 == d`;
- P4 request `p4_run.roster_sha256 == d`;
- P4 result `pre_p5_run_root_roster == {entries,sha256:d}`.

The design also requires a permanent regression that `STAGING_PROJECTION_KEYS`, the P4 planned-commitment outer key set and the `projection_sha256` field name remain unchanged. This is the correct way to migrate the semantics without smuggling a planned-lock wire-schema rename into this Gate.

## Cross-check against frozen P5/P4 boundaries

The migration remains compatible with the existing P5 v0.8 handoff envelope shape (`roster={entries,sha256}` and rows `{path,type,mode,sha256}`) while intentionally replacing the old v1 `preflight.json` roster inclusion that caused the fixed point.

No new authority is introduced:

- `AUTHORIZED_P4_V4_LOCK_SPEC` must remain `None`;
- `AUTHORIZED_P4_V4_EVIDENCE` must remain `None`;
- `run_parent_export()` remains hard-stopped;
- no historical evidence/artifact rewrite is permitted;
- P4 request/result `p4_run` / `p4_staging` equality, P5 Git/current/Gitlink evidence authority, P3-only backend difference and lexical loader/bootstrap contracts remain regression requirements.

## Implementation authorization scope

This approval authorizes only the v0.2 static implementation scope:

- root P4/P5 pure manifest/roster derivation and validators;
- P5 loader/verifier migration to v2 roster semantics;
- P4 planned projection semantic parity while retaining its closed wire schema;
- temporary final-payload validator/static pair-verifier updates;
- stdlib CPU fixtures, `py_compile`, and `git diff --check`.

It does **not** authorize:

- real P4 execution request generation;
- real P4 preflight;
- run-root/staging/materialization/candidate creation;
- record/refreeze/evidence publication;
- P5 authority update;
- P5 export/compose;
- child/torch/torchrun execution;
- GPU/CUDA;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T;
- Local Memory / LIBERO training.

Implementation completion must stop at REVIEW and be re-reviewed against its exact new implementation SHA. No approval from `4ce8ad3`, `f16f6e4`, or any prior SHA may be reused for that implementation closure.
