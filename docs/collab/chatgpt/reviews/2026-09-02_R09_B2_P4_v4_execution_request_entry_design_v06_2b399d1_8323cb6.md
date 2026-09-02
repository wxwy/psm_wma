# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `entry` Contract v0.6

## Verdict

`REQUEST_CHANGES`

## Reviewed object

- Design commit: `2b399d1bba8329607e08abfe58804a43806e8922`
- Review request commit: `8323cb6fb4c4b13b4bf824c0edfd41d2f00d3379`
- Design: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_entry_design_v0.6_2026-09-02.md`
- Frozen Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Previous ChatGPT static-validator approval anchor: `7aa9172528b82701eb8fbf0dcb0f99d11b8b31a8`

## HIGH — `root_revision` grammar is incompatible with this repository's Git commit identity

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_entry_design_v0.6_2026-09-02.md:18,25`

The proposed exact grammar requires:

```json
"root_revision": "<64 lowercase hex>"
```

and then states that all four digest/revision fields accept only lowercase 64-hex.

That is not the identity format used by this repository. Current root commits are 40-hex Git object IDs, including the reviewed design `2b399d1bba8329607e08abfe58804a43806e8922`, request `8323cb6fb4c4b13b4bf824c0edfd41d2f00d3379`, and the frozen submodule Gitlink `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

If implemented as written, no real root commit revision from the current repository can satisfy the `entry` grammar, so a future frozen execution request would be unconstructable even before the later `source` authority check.

### Required correction

Freeze the fields separately:

- `root_revision`: exactly `40 lowercase hex` for this repository's current Git object format;
- `git_blob_sha256`: exactly `64 lowercase hex`;
- `current_sha256`: exactly `64 lowercase hex`;
- `identity_sha256`: exactly `64 lowercase hex`.

Add permanent CPU negatives for at least:

1. 64-hex `root_revision` rejected;
2. 39/41-char root revision rejected;
3. uppercase/non-hex root revision rejected;
4. valid 40-hex root revision accepted at this grammar stage.

The later `source` section must still independently prove that the 40-hex revision resolves to the authorized root commit; grammar acceptance alone is not authority.

## Positive observations

The rest of the v0.6 split is sound for a static design step:

- `tool_path` is frozen to the exact root entry path;
- `identity_sha256` excludes itself and hashes the canonical remaining entry object, avoiding self-reference;
- `entry` explicitly does not self-authorize Git/current-byte identity;
- Git blob/current bytes/root Gitlink cross-validation remains source-owned and deferred to the next section;
- existing single-read `O_NOFOLLOW` request binding and immutable execution-contract regressions are required to remain passing;
- no real preflight, staging, candidate materialization, record/refreeze, evidence publication, P5 export/compose, GPU, training, evaluation, inference, B2-T, or Local Memory training is authorized.

## Authorization after this review

Allowed only:

- edit v0.6 design to correct `root_revision` grammar;
- CPU/static tests or documentation needed to demonstrate that correction;
- resubmit the corrected design/implementation for independent review.

Not authorized:

- `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_ENTRY_STATIC_TOOLS` under the current v0.6 grammar;
- any real P4-v4 preflight execution or runtime side effect.
