# R09-B2 P4-v4 Execution Request `source` Static Implementation Review

- Date: 2026-09-02
- Root implementation: `a36ac2151bfa9637225edc93dab474a6dd4f8f1b`
- Review request / ledger: `6608e39a940f459f6ac5a74737a79a19d8b1a964`
- Approved design: `6eea35c443bb7ac7c5f91f76d1c6d04945c7ec89`
- Prior ChatGPT design approval: `1445e2b19c2489be564556536b90374e7d46769a`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`REQUEST_CHANGES`

The implementation correctly adds the core source-owned authority path: exact source schema/identity, canonical root checks, root/submodule full-clean checks, exact `HEAD == root_revision`, exact `rev-parse --verify <root_revision>^{commit}`, Gitlink == submodule HEAD, tracked entry Git blob/current-byte checks, and entry/source cross-binding. The unrelated-descendant fixture also closes the previously identified exact-HEAD issue.

However, the static source Gate cannot close yet for the following blockers.

## HIGH — permanent CPU Git fixtures required by the approved v0.3 design are mostly missing

`tools/g0/test_r09_b2_p4_v4_execution_preflight.py:116-166` defines only one `SourceAuthorityTest` method. That single method covers:

- exact-head positive acceptance; and
- the critical unrelated-descendant negative case.

The approved v0.3 design explicitly requires permanent source Git fixtures for at least:

1. dirty root;
2. untracked root;
3. Gitlink drift;
4. submodule HEAD drift;
5. entry Git blob/current-byte drift;
6. entry/source cross-binding drift;
7. symlink root;
8. symlink entry;
9. ancestor checkout/revision mismatch; and
10. the already-present unrelated descendant case.

The reported `7/7` total is therefore not seven source-authority fixtures; it is the pre-existing six entry/foundation tests plus one source test. This is insufficient evidence to close the source static authority contract.

Required remediation: add explicit stdlib CPU Git tests for every frozen source negative above, preserving the existing positive exact-head and unrelated-descendant tests. No mocks around the source admission path for these fixtures.

## HIGH — current entry non-symlink/current-byte identity has a TOCTOU gap

`tools/g0/r09_b2_p4_v4_execution_preflight.py:127-133` first performs pathname checks with `is_symlink()`, `is_file()` and `stat()`, then later reads `entry_path.read_bytes()` twice.

This separates the non-symlink/regular-file identity check from the bytes that are actually hashed/compared. The pathname can be replaced between those operations; the two `read_bytes()` calls can also observe different file objects/bytes. That violates the source contract's intended binding:

`tracked regular non-symlink current entry object == current bytes used for SHA/blob equality`.

This is the same class of identity/TOCTOU issue already fixed for the execution request itself.

Required remediation: read the current entry through one no-follow file descriptor:

1. `os.open(..., O_RDONLY | O_NOFOLLOW | O_CLOEXEC)`;
2. `fstat()` the same fd and require a regular file;
3. read exactly once into `current_raw`;
4. use that same `current_raw` for both current SHA256 and Git-blob byte equality;
5. do not reopen the entry pathname for authority decisions.

Add a permanent CPU regression proving no pathname `read_bytes()` reopen is used and that a symlink/replacement attempt fails closed.

## Positive findings

- `source` exact key set and digest widths are implemented.
- canonical root / identity validation is present.
- `HEAD == root_revision` is enforced, so clean descendants are rejected.
- the requested descendant fixture specifically changes only an unrelated root file while entry/Gitlink remain unchanged and still fails on checkout revision identity.
- root/submodule full-clean and Gitlink/submodule checks are present.
- entry/source revision/blob/current cross-binding is present.
- the existing top-level request remains fail-closed and still reaches the unconditional execution hard-stop only after static validation.
- no real preflight/staging/candidate/record/refreeze/P5 export/compose/GPU/training authorization is granted by this review.

## Required next action

CPU/static remediation only:

- add the missing source Git negative fixtures;
- make current entry identity/bytes a single-fd no-follow read;
- rerun the complete stdlib CPU suite, `py_compile`, and `git diff --check`;
- submit a new implementation SHA for independent review.

## Authorization boundary

Allowed:

- root static parser/validator remediation;
- stdlib CPU Git fixtures/tests.

Not authorized:

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
