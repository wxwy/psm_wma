# ChatGPT Review — Authority-root Causal Owner Identity Execution Design v0.4

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-EXECUTION-DESIGN`

## Exact formal pair

- root docs SHA: `76210e7bcbdc606e39775e2dae258542cf3c0d38`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. At that exact root, `cosmos-framework` is a submodule/Gitlink to exactly `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior ChatGPT-reviewed v0.3 pair `781824f4ed2682b1347126a58f645ef0702117bd / 93a89ba61306d840a008813f62f26a34d54850f4`. The formal v0.4 commit changes only `SESSION.md`, `TODO.md`, and the new docs-only v0.4 design; child/runtime is unchanged.

Requested verdict:

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`

or `REQUEST_CHANGES(file:line)`.

Approval at this Gate authorizes only the next root-only stdlib temporary-fixture CPU/static launcher/adapter/tests implementation. It does not authorize production/main execution, real materialization, project-path authority artifacts, source/checkpoint I/O, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Authority chain used

This review applies the inherited frozen source/raw/config/route and backing `{3,4,5}` contracts, the approved authority-root static/fail-close contracts, v0.3's accepted FD collision/lifecycle remediation, and v0.4 only where it explicitly refreezes the two remaining post-exec consumer-authority gaps. No later bookkeeping/request SHA is treated as the formal target.

## Prior blocker disposition

### Prior HIGH-1 — FD8 did not reach actual Git consumers: CLOSED

v0.4 now freezes every post-exec subprocess that dereferences an FD8-derived `cwd`, `GIT_INDEX_FILE`, or repository path as an FD8 consumer. That includes bootstrap `grun()` Git probes and all `NativeAuthorityGit` Git invocations. Each such consumer must use exact `close_fds=True, pass_fds=(8,)`, with FD3/4/5 explicitly excluded from Git-grandchild inheritance.

It additionally freezes pre/post consumer FD8 identity barriers, fail-closed handling, post-mutation `ROLLBACK_INCOMPLETE` semantics, and a mandatory actual temporary-Git witness whose `GIT_INDEX_FILE` is `/proc/self/fd/8/.authority-root.index` after global CLEAN replacement. This closes the prior design gap rather than leaving subprocess inheritance to implementation invention.

The current adapter source still launches bootstrap Git and `NativeAuthorityGit` commands without `pass_fds`; that is expected implementation work and is now precisely authorized/refrozen by this design rather than an unresolved design choice.

### Prior HIGH-2 — procfd authority was defeated by `resolve/realpath`: CLOSED

v0.4 explicitly identifies the affected seams: `bootstrap_payload()`, `_bootstrap_identity_from_runtime()`, `_verify_loaded_identity()`, `NativeAuthorityGit._repository_directory()`, and `verify_configuration_authority()`. It forbids `Path.resolve()`, `os.path.realpath()`, or `os.path.abspath()` from canonicalizing FD8-derived owner values back into global CLEAN path authority.

The replacement semantics are now frozen: FD8-rooted component-by-component no-follow dirfd traversal, type checks by `fstat`, exact raw-byte/blob verification for project modules, FD8-relative loaded-module identity, and FD8-anchored repository-boundary verification. Existing anti-symlink, Git routing marker/gitdir/commondir, common-config raw/allowlist, and `config.worktree`-absence checks must remain; global Git administrative paths may only validate Git metadata and cannot replace the FD8 owner boundary.

The current source's affected `resolve/realpath` checks therefore no longer create an implementation ambiguity: v0.4 states which ones must be replaced, what authority replaces them, which global administrative paths remain legal, and which failure/witness behavior is mandatory.

## Fresh design review

No new design/authority blocker was found.

The v0.4 design is internally consistent with the previously accepted FD layout and lifecycle:

- executor retained owner capabilities remain FD7/FD9;
- final bootstrap/adapter inherited set remains exactly `{3,4,5,8}`;
- post-exec Git grandchildren inherit only FD8 in addition to standard descriptors, not FD3/4/5;
- executor Git population remains the separate FD6 contract;
- absolute CLEAN remains executor-only and cannot become post-exec root authority;
- owner continuity is preserved through bootstrap, adapter, actual Git consumer, and cleanup/failure classification;
- the required future witnesses are causal: global CLEAN/module replacement must either leave actual consumers on the held FD8 inode or cause fail-closed behavior before foreign consumption.

The design is feasible against the current root adapter because all required source changes are confined to the already named root-only launcher/adapter module and temporary-fixture tests; no child/runtime modification is required.

## Blocker summary

- current blockers: `0`
- design/authority blockers: `0`
- child/runtime blockers: `0`
- prior v0.3 HIGH-1: `CLOSED`
- prior v0.3 HIGH-2: `CLOSED`

## Final verdict

`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC`

This verdict binds only exact pair `76210e7bcbdc606e39775e2dae258542cf3c0d38 / 93a89ba61306d840a008813f62f26a34d54850f4`.

It authorizes only root-only stdlib temporary-fixture CPU/static launcher/adapter/tests implementation under the v0.4 frozen contract. It does **not** authorize production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
