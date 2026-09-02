# R09-B2 P4-v4 Execution Request `entry` Static Implementation Review

- Date: 2026-09-02
- Root implementation: `ad2bfcc3b1e85e77317443a4f46dba0780403d34`
- Review request: `baa0b43f70ae391a800c25427c8a95fa10531b5b`
- Status-only follow-up: `ec4f8b4010a74273c1d87067cba39bc9d31ac442`
- Approved design: `99562b62366134d87c192b7258ef0a9365a18f8f`
- Prior ChatGPT design approval: `2b571aa39ea101efedaf5d44b0ac2e9de07fc56c`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_ENTRY_STATIC_TOOLS`

## Findings

No blocking finding.

The implementation matches the approved v0.7 `entry` contract:

1. `entry` has an exact key set: `tool_path`, `root_revision`, `git_blob_sha256`, `current_sha256`, `identity_sha256`.
2. `tool_path` is fixed literally to `tools/g0/r09_b2_p4_v4_execution_preflight.py`.
3. `root_revision` accepts exactly 40 lowercase hexadecimal characters.
4. `git_blob_sha256`, `current_sha256`, and `identity_sha256` accept exactly 64 lowercase hexadecimal characters.
5. `identity_sha256` is recomputed over the canonical JSON representation after removing `identity_sha256` itself.
6. Permanent CPU negatives cover identity drift, wrong path, 64/39/41-character revisions, uppercase/non-hex revisions, and extra keys.
7. Prior single-open `O_NOFOLLOW` / `fstat` / one-raw-byte binding, request SHA binding, and immutable execution-contract behavior remain unchanged.
8. The entry point still unconditionally hard-stops after static validation and does not create staging/candidate roots or execute P4.
9. No code drift exists after the implementation commit; later commits only update TODO/Inbox status.
10. Root Gitlink remains exactly `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`.

## Scope

This closes only the `entry` nested static grammar/identity implementation.

Next work may define and implement the `source` section as a separately reviewed static contract, including independent authority for revision resolvability, root Gitlink, entry Git blob, current bytes, and equality checks. Passing `entry` grammar is not Git authority.

## Not authorized

This review does **not** authorize:

- real P4-v4 preflight execution;
- staging/materialization;
- candidate generation;
- record/refreeze;
- evidence publication;
- P5 authority update;
- P5 export/compose;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T or Local Memory training.
