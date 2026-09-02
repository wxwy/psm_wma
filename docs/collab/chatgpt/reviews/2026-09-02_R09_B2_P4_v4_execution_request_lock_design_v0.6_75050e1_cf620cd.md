# Independent Review — R09-B2 P4-v4 Execution-Request Lock design v0.6

- Review anchor: `82c567cc5fa7e572eb5222ccf56e963533628056`
- Design commit: `75050e1f939289ea3e460eb20a3c8448c929e447`
- Formal request / ledger head: `cf620cddab20b94981aa34e48b2d1457bbf1b824`
- Gitlink at request head: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Scope: design-only review for root static planned-commitment tooling. No real P4/P5 migration, request, preflight, materialization, record/refreeze, P5 export/compose, GPU, model/data/checkpoint I/O, evaluation/inference/training.

## Verdict

`REQUEST_CHANGES`

v0.6 closes all three blockers from the v0.5 review: it introduces planned-only run/candidate grammars without `roster_sha256`, adds `planned.identity_sha256`, and adds an absolute `source_root` authority anchor. The P4/P5 roster-v2 migration direction and same-FD output poison contract remain acceptable.

Two design blockers remain before static implementation.

## B1 — HIGH — multi-component `spec_path` is not nofollow-safe

File: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_lock_design_v0.6_2026-09-02.md`, §1.

v0.6 correctly anchors `source_root` by walking every absolute component with `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC`, but then says that source-root FD is used as the root for:

`openat(..., O_NOFOLLOW)` on the relative `spec_path`.

For a normal multi-component path such as `docs/build/<spec>.json`, `O_NOFOLLOW` protects only the final component. An intermediate component such as `docs` or `docs/build` can be replaced with a symlink and pathname resolution can escape the anchored source root.

Required remediation:

1. Freeze `spec_path` as lexical relative path with no empty / `.` / `..` components.
2. Starting from the already verified `source_root` FD, walk every parent component with `openat(..., O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC)` + `fstat` directory verification.
3. Open only the final basename relative to the verified parent FD with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`, then `fstat` regular-file verification.
4. Never re-resolve the full `spec_path` pathname after the FD chain is established.
5. Add fixtures for intermediate-component symlink/retarget, not only final-file nofollow.

An alternative is to restrict `spec_path` to one direct-child basename of `source_root`, but that would be a different contract and must be stated explicitly.

## B2 — HIGH — output `planned` mapping is internally contradictory

File: same design, §2.

The design freezes:

- output `planned` key-set as `{root,attempt_id,recurrent,ttt_fast_weight,identity_sha256}`;
- “前四项逐字节复制 `planned_candidates`”; and then
- each output backend as `{backend,run_identity,run_token,candidate_root,staging_projection,identity_sha256}`.

But `planned_candidates.<backend>` has only `{backend,candidate_root,run_identity,run_token,identity_sha256}` and therefore cannot be byte-for-byte copied while simultaneously gaining `staging_projection` and a recomputed self identity.

Required remediation:

Freeze one unambiguous mapping, for example:

- only `planned.root = spec.planned_candidates.root` and `planned.attempt_id = spec.planned_candidates.attempt_id` are direct copies;
- for each backend, construct a new output backend object with exact field mapping:
  - `backend = spec.planned_candidates.<backend>.backend`
  - `candidate_root = spec.planned_candidates.<backend>.candidate_root`
  - `run_identity = spec.planned_run.<backend>.identity` and equal the candidate-side `run_identity`
  - `run_token = spec.planned_run.<backend>.run_token` and equal the candidate-side `run_token`
  - `staging_projection = deterministic v2 projection from payload_manifest + run_token`
  - `identity_sha256 = SHA256(P4 canonical bytes of the backend object without this field)`
- only after both backend objects are constructed, compute `planned.identity_sha256` from the whole planned object without that field.

Fixtures should prove exact spec→commitment mapping and reject any backend direct-copy shortcut that omits or misbinds the projection.

## Closed from prior review

- planned-only spec no longer carries final `run/candidates/roster_sha256`: closed.
- shared pair-level `attempt_id` and derived backend candidate leaf: closed.
- `planned.identity_sha256` has an explicit field: closed.
- `source_tree_oid` is explicitly a 40-hex Git tree object ID, not SHA256: closed.
- absolute source-root authority exists: closed, subject only to B1's child-path traversal requirement.
- P4/P5 roster-v2 migration remains design-only and is not authorized for implementation by this verdict.

## Repository / scope verification

`82c567c... → cf620cd...` changes only `SESSION.md`, `TODO.md`, the v0.6 design, and Inbox. `75050e1... → cf620cd...` is Inbox-only. No P4/P5 production code changed in this submission. Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Gate status

Do not implement the Request-Lock static helper yet. After B1/B2 are frozen and independently re-reviewed, the appropriate positive verdict would be:

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_LOCK_STATIC_TOOLS`

Even after such approval, real P4/P5 migration, final execution request generation, record/refreeze, real CPU preflight, P5 export/compose, B2-T, GPU, and Local Memory training remain separately unauthorized.
