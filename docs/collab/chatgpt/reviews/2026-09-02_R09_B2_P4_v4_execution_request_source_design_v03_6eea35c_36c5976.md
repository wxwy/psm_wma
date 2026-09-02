# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `source` v0.3

- Date: 2026-09-02
- Design: `6eea35c443bb7ac7c5f91f76d1c6d04945c7ec89`
- Review request: `36c597658aa6e73fcd4cad8df33718018b52a360`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- Prior blocking review: `ad733625b0127009338cf8aafc607d2198a86f78`

## Verdict

`APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_SOURCE_STATIC_TOOLS`

## Findings

The prior HIGH blocker is closed.

v0.3 now requires both:

- `git -C root rev-parse HEAD == source.root_revision`
- `git -C root rev-parse --verify <root_revision>^{commit} == source.root_revision`

Therefore ancestor, descendant, or unrelated clean checkouts cannot satisfy source authority merely because the entry bytes and Gitlink happen to remain unchanged.

The design also freezes the required permanent descendant fixture: create commit A, then clean descendant B that modifies only an unrelated root file while keeping entry bytes and Gitlink unchanged; with request/source=A and checkout HEAD=B, validation MUST fail on checkout revision identity.

Other source-owned authority boundaries remain coherent:

- exact canonical root grammar;
- root and submodule full-clean including untracked;
- root/submodule must be Git roots and submodule path non-symlink;
- source revision / entry revision cross-binding;
- source Gitlink == tree gitlink == submodule HEAD;
- fixed entry tracked regular non-symlink;
- entry Git blob SHA == current-byte SHA == source declaration == entry declaration;
- all failures are fail-closed before the existing unconditional execution hard-stop.

## Authorized scope

Only:

- root static parser/validator implementation for the `source` section;
- stdlib CPU Git fixtures/tests described by v0.3.

## Not authorized

No authorization is granted for:

- real P4-v4 preflight execution;
- staging/materialization;
- candidate generation;
- record/refreeze;
- evidence publication;
- P5 authority update/export/compose;
- torchrun/GPU/CUDA;
- model/data/checkpoint I/O;
- training/evaluation/inference;
- B2-T or Local Memory training.

The implementation must return for independent review before any runtime authorization is considered.
