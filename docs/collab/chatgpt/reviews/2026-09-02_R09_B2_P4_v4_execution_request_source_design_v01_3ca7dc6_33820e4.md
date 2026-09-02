# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request `source` v0.1

## Verdict

`REQUEST_CHANGES`

## Reviewed object

- root design: `3ca7dc6b522f60fd4b654cf737002e5ed5bad899`
- review request: `33820e44a4deeb948cbe0619af7ba312a8b0f68c`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`
- design: `docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_source_design_v0.1_2026-09-02.md`
- prior approved entry implementation: `ad2bfcc3b1e85e77317443a4f46dba0780403d34`

## HIGH — exact source revision authority contradicts the proposed HEAD rule

`docs/build/PSM-WMA_R09_B2_P4_v4_execution_request_source_design_v0.1_2026-09-02.md:7` states that validation accepts only the exact request-declared revision and rejects descendants. However `:26` explicitly states that current `HEAD == root_revision` is **not** an acceptance condition.

That permits this state to pass the proposed authority:

1. request/source declares commit A as `root_revision`;
2. working tree is clean at descendant commit B;
3. B leaves the entry bytes and `cosmos-framework` Gitlink unchanged;
4. `git show A:<entry>` equals current entry bytes and submodule HEAD still equals A's Gitlink;
5. the validator accepts while the actual checkout contains other root files from unreviewed descendant B.

That is not an exact source-revision binding. Future execution may consume other root code/dependencies from B, so entry-byte equality alone is insufficient to make a descendant checkout authoritative.

### Required change

Freeze the root checkout identity itself:

- `git -C <root> rev-parse HEAD` must equal `source.root_revision` exactly;
- descendants and ancestors must both fail unless their exact commit is the reviewed/requested `root_revision`;
- retain the existing `rev-parse --verify <root_revision>^{commit}` exact-resolution check;
- retain full-clean/untracked rejection, Gitlink == submodule HEAD, tracked regular entry, Git blob/current-byte equality and entry/source cross-binding.

Add a permanent CPU Git fixture where commit B is a descendant of A but changes only an unrelated root file while preserving the entry bytes and Gitlink. With request `root_revision=A` and checkout `HEAD=B`, validation must fail specifically on checkout revision identity. This is the important negative because it proves the descendant cannot pass merely because the currently checked entry bytes happen to match A.

## Positive findings

The rest of the design direction is sound: canonical absolute root, exact source schema/identity, entry/source revision/blob/current cross-binding, full-clean root and submodule, exact Gitlink/submodule binding, tracked regular non-symlink entry, Git-blob/current-byte SHA equality, fail-closed Git errors, and preservation of the existing unconditional execution hard-stop.

## Authorization boundary

Allowed after remediation: design/static-only changes and stdlib CPU Git fixtures, followed by re-review.

Not authorized: `APPROVE_TO_IMPLEMENT_P4_V4_EXECUTION_REQUEST_SOURCE_STATIC_TOOLS`, real P4-v4 preflight, staging/materialization, candidate generation, record/refreeze, evidence publication, P5 authority update/export/compose, torchrun/GPU/CUDA, model/data/checkpoint I/O, training/eval/inference, B2-T, or Local Memory training.
