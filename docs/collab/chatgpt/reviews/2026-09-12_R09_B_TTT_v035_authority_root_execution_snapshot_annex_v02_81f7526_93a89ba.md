# ChatGPT Review — Authority-root Execution Snapshot Annex v0.2

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `81f7526881dc4f93cf03da13988e2b74dda7d0de`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` tree entry is a submodule/Gitlink to the stated child, and that child commit is independently reachable in `wxwy/cosmos-framework`.

The delta from the prior annex pair `29c8aaa2a048f538892295afa6bc6d49031b0d0c` is docs/status/review bookkeeping only. No production root tooling or child/runtime code changes are introduced.

## Closure/progress

The previous annex-completeness HIGH is materially addressed in scope and structure: v0.2 now supersedes v0.1, freezes selection/config canonical bytes, launcher/bootstrap environment bytes, FD numbers, commit metadata, bootstrap identity and a complete parser-argv authority, and forbids a later execution request from introducing new runtime authority. Endpoint/input digest/OID values independently recompute correctly.

However, two authority-critical frozen values are inconsistent with the exact production adapter ABI, so the annex is not yet a valid sole runtime authority.

## Blockers

### HIGH-1 — parser argv digest is incorrectly reused as the bootstrap `sys.orig_argv[6:]` digest

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.2.md:89`

The annex freezes the parser argv JSON as 2427 bytes with SHA-256 `72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2`, then states that bootstrap observes `json.dumps(sys.orig_argv[6:], ...)` and therefore `bootstrap_argv_sha256` must equal the same digest.

These are not the same byte array. In the approved production launcher ABI, `sys.orig_argv` is:

`[python, -I, -S, -B, -c, <payload>, --, <parser argv...>]`

and the bootstrap code explicitly hashes `a[6:]`, which includes the literal leading `"--"`. The parser's `actual_argv` starts at `a[7:]` and does not include it.

Independent recomputation from the annex-frozen parser tuple gives:

- parser argv JSON (`actual_argv`): 2427 bytes, SHA-256 `72777bd7305c760c48c069eafd068f1a538383a6fdb8d40258acf3d8fc3b7ae2` — this value is correct for adapter `argv_sha256`;
- bootstrap-observed JSON (`sys.orig_argv[6:]` = `["--", *actual_argv]`): 2432 bytes, SHA-256 `aefa3a7d02be8ca5af6572e59eb125ced458b739d5f9ac2cc8fc3122018455a6`.

With the annex as written, the bootstrap contract must declare `72777bd...`, while production observes `aefa3a7d...`; `_bootstrap_identity_from_runtime()` therefore fails before project execution. This is a frozen-authority contradiction, not an editorial issue.

**Exact acceptance:**
1. Keep the 2427-byte / `72777bd...` digest as the adapter parser-argv/evidence `argv_sha256` authority if desired.
2. Separately freeze bootstrap `sys.orig_argv[6:]` canonical bytes semantics, explicitly including the leading `"--"`.
3. Freeze `bootstrap_argv_sha256` to the independently derived 2432-byte digest `aefa3a7d02be8ca5af6572e59eb125ced458b739d5f9ac2cc8fc3122018455a6`, or recompute it by an equivalent exact derivation and show that it matches production.
4. Freeze the bootstrap-contract canonical JSON from `bootstrap_raw_sha256` plus this distinct bootstrap-argv digest; the later execution request may only reproduce it.

### HIGH-2 — NativeAuthorityGit environment authority does not match production

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.2.md:57`

The annex correctly freezes the six-key launcher/bootstrap environment, but then says `NativeAuthorityGit`'s commit-only environment equals that mapping plus the next section's seven metadata keys.

Production does something different. `NativeAuthorityGit.__init__()` builds the transaction environment from:

- the six launcher/Git isolation keys;
- `GIT_INDEX_FILE` pointing to the frozen temporary index;
- six author/committer environment variables: `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_AUTHOR_DATE`, `GIT_COMMITTER_NAME`, `GIT_COMMITTER_EMAIL`, `GIT_COMMITTER_DATE`.

The seventh candidate metadata field, commit message, is **not** an environment variable; it is supplied as stdin to `git commit-tree`. Conversely, `GIT_INDEX_FILE` is authority-critical and is absent from the annex's stated derivation.

This matters directly because production evidence computes `sanitized_env_sha256` over `transaction.env`. Under the annex's frozen index path and metadata, the exact canonical transaction-env JSON is 471 bytes with SHA-256 `daf9e4bfb1740f5e94d038547619256b900eb16be7830bd37c7df8d4f6a0f235`; the annex currently does not freeze this correct environment view.

**Exact acceptance:**
1. Keep the six-key launcher/bootstrap environment as its own frozen authority.
2. Separately freeze the exact `NativeAuthorityGit.env` mapping used by production: six base keys + `GIT_INDEX_FILE` + the six author/committer env keys, with canonical bytes and SHA-256.
3. State explicitly that commit message is not part of `transaction.env`; it is the frozen `commit-tree` stdin payload.
4. Require the later execution request/evidence to reproduce this exact mapping and digest without additional inherited environment variables.

## Blocker summary

- docs/request blockers: `2 HIGH`
- implementation blockers: `0` (closed `9dd2fb8...` implementation remains authoritative)
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_execution_snapshot_annex_v0.2.md:89)`

This verdict binds only exact pair `81f7526881dc4f93cf03da13988e2b74dda7d0de / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization, JSON/worktree/index/candidate/ref/evidence creation, source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized.
