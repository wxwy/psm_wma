# ChatGPT Independent Review — R09-B2 P4-v4 Execution Request Source Static Remediation

- Date: 2026-09-02
- Branch: `V2`
- Approved design: `6eea35c443bb7ac7c5f91f76d1c6d04945c7ec89`
- Prior ChatGPT review: `9d13a7eb6999c20bd1c61b861a39d4c4f763a8d9`
- Remediation implementation: `b0581d89c452cadaa40e9739c6d51313eb13a615`
- Review request / ledger: `ec1e607e4d44fcc90f077660241a84abeb259ac1`
- Gitlink: `21d064f2b7c7aeeb67cfee50ac8d6722a944eddb`

## Verdict

`APPROVE_TO_CLOSE_P4_V4_EXECUTION_REQUEST_SOURCE_STATIC_TOOLS`

## Closure findings

The two blockers from review `9d13a7e` are closed.

### 1. Entry current-byte authority is now single-fd / no-follow

`tools/g0/r09_b2_p4_v4_execution_preflight.py` factors file admission through `_read_regular_nofollow()`:

- `os.open(... O_RDONLY | O_NOFOLLOW | O_CLOEXEC)`;
- same fd `fstat()` regular-file validation;
- exactly one raw-byte read from that fd;
- the same `current_raw` is used for current SHA256 and Git-blob byte equality;
- no authority decision reopens the entry pathname.

This closes the prior pathname TOCTOU between symlink/regular-file admission and current-byte binding.

### 2. Frozen source Git fixture matrix is now represented in permanent CPU tests

The source tests now cover the v0.3 required matrix, including:

- exact-HEAD positive case;
- unrelated clean descendant with unchanged entry/Gitlink -> FAIL;
- dirty root -> FAIL;
- untracked root -> FAIL;
- declared Gitlink drift -> FAIL;
- submodule HEAD drift -> FAIL/fail-closed;
- entry Git blob/current-byte drift -> FAIL;
- entry/source cross-binding drift -> FAIL;
- symlink root -> FAIL;
- symlink entry -> FAIL;
- ancestor checkout -> FAIL;
- no pathname `Path.read_bytes()` reopen and one `os.open()` for current entry authority.

The submitted evidence reports `13/13` stdlib CPU tests PASS, plus `py_compile` and `git diff --check` PASS. Inspection of the committed tests matches that claim and the approved v0.3 contract.

### 3. Existing source authority semantics remain intact

The implementation still enforces before the unconditional execution hard-stop:

- exact source schema/canonical identity;
- strict-resolved absolute non-symlink root;
- root and submodule full-clean including untracked;
- `HEAD == source.root_revision`;
- exact `rev-parse --verify <root_revision>^{commit}`;
- exact parent Gitlink and submodule HEAD binding;
- tracked entry path;
- Git blob/current-byte SHA and byte equality;
- source↔entry revision/blob/current cross-binding.

No source implementation drift exists after `b0581d8`; `ec1e607` only updates status/Inbox review request state.

## Forward requirement — not a blocker for this static closure

Before any real execution is authorized, the later interpreter/environment contract must prevent source Git authority from depending on an untrusted ambient `PATH` resolution of `git` (or otherwise freeze/verify the Git executable used by `_git()`). This is not a blocker for the present source-static closure because the entry remains unconditionally hard-stopped and real preflight is still forbidden.

## Authorized scope

This verdict closes only `P4-v4 execution-request source static parser/validator + stdlib CPU Git fixtures`.

Next work may proceed to the next independently reviewed execution-request section (expected: `interpreter`) and its CPU/static tooling only.

## Still forbidden

No authorization for:

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
