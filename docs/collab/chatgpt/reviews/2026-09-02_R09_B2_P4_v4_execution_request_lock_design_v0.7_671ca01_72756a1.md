# Independent Review — R09-B2 P4-v4 Execution-Request Lock design v0.7

- Review anchor: `065b45fc22ff2920ea3d758222e2cbc504d1802b`
- Design commit: `671ca0123352b050125f3a413f8e74eeabbe6088`
- Formal request / ledger head: `72756a1a288bdd23e7f95f0adea7e463d9e58482`
- Gitlink at request head: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: design-only approval for root static planned-commitment tooling and stdlib CPU fixtures. No P4/P5 migration implementation, final request generation, real preflight/materialization, record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, evaluation/inference/training.

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

v0.7 closes the two remaining blockers from the v0.6 review without reopening previously closed contracts.

## Closure of prior blockers

### B1 — CLOSED — multi-component spec path is now FD-anchored and nofollow-safe

The design now freezes `spec_path` as a nonempty lexical relative path, rejecting absolute paths, empty components, `.`, `..`, and repeated separators. Starting from the already verified `source_root` directory FD, every parent component is opened with `openat(O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` and verified by `fstat` as a directory. Only the final basename is opened with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` and verified as a regular file. Full pathname re-resolution after the FD chain is forbidden.

This closes the intermediate-component symlink/retarget escape identified in the prior review. Required fixtures explicitly include intermediate symlink/retarget and final nofollow behavior.

### B2 — CLOSED — planned output mapping is now unambiguous construction, not direct copy

The design now states:

- `planned.root = spec.planned_candidates.root`;
- `planned.attempt_id = spec.planned_candidates.attempt_id`;
- each backend output object is newly constructed as `{backend,run_identity,run_token,candidate_root,staging_projection,identity_sha256}`;
- backend/candidate-root come from the candidate side;
- run identity/token come from `planned_run` and must equal the corresponding candidate-side bindings;
- staging projection is rebuilt only from payload manifest + token;
- backend identity is recomputed from the constructed object without its identity field;
- only after both backend objects exist is `planned.identity_sha256` recomputed over the complete planned object without that field.

This removes the v0.6 contradiction between byte-for-byte candidate-item copy and adding `staging_projection`.

## Retained accepted contracts

The following remain accepted and unchanged:

- planned-only run/candidate grammar carries no premature final `roster_sha256`;
- shared pair-level candidate attempt semantics and derived backend candidate leaf;
- explicit `planned.identity_sha256`;
- absolute `source_root` authority and 40-hex Git `source_tree_oid` binding;
- P4/P5 roster-v2 migration direction that removes evidence/pointer files from run-root roster to eliminate the hash fixed point;
- P5-compatible canonical projection/hash definition;
- default `AUTHORIZED_P4_V4_LOCK_SPEC=None` zero-write fail-closed behavior;
- same-FD `O_RDWR -> write/fsync/read-back -> fchmod(0444)/fstat -> close` success path and terminal post-create poison semantics.

## Repository / scope verification

`065b45f... -> 72756a1...` changes only `SESSION.md`, `TODO.md`, the v0.7 design, and Inbox. `671ca01... -> 72756a1...` is Inbox-only. No P4/P5 production code changed in this submission. Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Implementation authorization boundary

Authorized next work is limited to the static Request-Lock planned-commitment helper and its stdlib CPU fixtures under the frozen v0.7 contract.

Still not authorized:

- P4/P5 handoff migration implementation;
- final immutable execution-request generation;
- real request/preflight/materialization/staging/candidate/run-root creation;
- record/refreeze/evidence publication;
- P5 authority population/export/compose;
- B2-T;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- evaluation/inference/training, including Local Memory training.

After implementation, submit the exact implementation SHA and ledger head for independent closure review.
