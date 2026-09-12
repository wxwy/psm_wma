# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `5efcbdf8954f65da9c7dfd1d0f34c96204c5ddf6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The corrected formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental implementation review against prior exact pair `cc36db3a6b863d86d57f5eb0e3fcefb5aef3376d / 93a89ba...`. The effective remediation delta remains confined to the approved root adapter/test files plus collaboration bookkeeping.

## Prior blocker closure progress

### Prior HIGH-1 — pre-import executable/module path identity: PARTIALLY CLOSED

The module-path half is materially improved. The bootstrap now uses the unresolved absolute module path, performs direct `lstat`, rejects symlinks/non-regular files, additionally requires `realpath(full) == full`, and compares raw SHA-256 plus exact formal-tree `100644 blob <oid>` identity before `sys.path.insert()` / `runpy`. The direct module-symlink witness is present.

However the approved design also requires the interpreter and Git executable identity to be proved before project import. The current bootstrap only compares the realpath of `sys.orig_argv[0]` with the declared interpreter path; it does not pre-import verify the interpreter is regular/non-symlink, does not hash it against `--interpreter-raw-sha256`, and does not verify `--interpreter-version`. Git is pre-import checked for regular/non-symlink plus raw SHA, but `--git-version` remains unverified until adapter code is imported and `_verify_executable_identity()` runs.

This means the frozen executable identity contract is still split across the import boundary, contrary to the approved bootstrap ordering.

### Prior HIGH-2 — bootstrap Git ran before local-config authority admission: PARTIALLY CLOSED

The remediation correctly moves a stdlib parse of the common local config before the first native Git command and directly rejects unapproved keys such as `core.fsmonitor` and `[include]`. That closes the specific hostile-config examples from the previous review.

But the bootstrap still does not establish the same complete v0.4 local-config authority that production later enforces. In particular, `extensions.worktreeconfig` is allowed to be either `true` or `false` by the bootstrap parser. If it is `true`, Git may consume per-worktree `config.worktree`; the bootstrap does not check that file is absent before running `rev-parse`, `status`, and `ls-tree`. The approved v0.4 contract requires `extensions.worktreeConfig` absent/false and `config.worktree` absent before authority Git actions. Therefore a worktree-specific config remains an unaudited authority channel for the bootstrap's first Git observations.

The bootstrap also derives the common directory manually from the `.git` admin path but does not independently bind/check the common directory with the same typed non-symlink/common-config identity later used by `verify_configuration_authority()`. The direct hostile-local-config witness covers `core.fsmonitor` and `include`, but not the `worktreeConfig=true` + `config.worktree` path that remains semantically active here.

## Current blockers

### HIGH-1 — interpreter/Git executable identity is still not fully proved before project import

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:165`

Before `sys.path.insert()` / `runpy.run_module()` the stdlib bootstrap must prove the complete frozen executable identities, not just their paths or partial hashes.

**Exact acceptance:**

1. pre-import, verify the declared interpreter path itself is absolute, regular and non-symlink, its raw SHA-256 equals `--interpreter-raw-sha256`, and its exact version output equals `--interpreter-version` under a frozen no-ambient environment;
2. retain the existing Git regular/non-symlink/raw-SHA check and additionally verify exact `--git-version` before any project import;
3. reject interpreter/Git path/hash/version drift before project import, ref/object action, evidence write or project callback;
4. add direct isolated-interpreter witnesses for interpreter symlink/path/hash/version drift and Git version drift, proving no project-import sentinel/ref/evidence is reached.

### HIGH-2 — bootstrap still allows worktree-specific local config to affect its first Git commands

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:190`

The bootstrap's allowlist accepts `extensions.worktreeconfig=true`, then immediately starts native Git observations. Under that mode, `config.worktree` can participate in Git's local configuration, but the bootstrap has not admitted or rejected it yet.

**Exact acceptance:**

1. before the first `rev-parse` / `status` / `ls-tree`, require `extensions.worktreeConfig` to be absent or exactly `false`;
2. for linked worktrees, derive and validate both the worktree admin directory and common Git directory without consuming unaudited Git config, prove both are absolute existing non-symlink directories, and require `<git_dir>/config.worktree` absent;
3. bind the same `<git_common_dir>/config` authority the production preflight later uses; no alternate local-config layer may remain active for bootstrap Git commands;
4. add a direct isolated-bootstrap witness with `extensions.worktreeConfig=true` and a hostile `config.worktree` entry (for example `core.fsmonitor` or transport-affecting config) and prove rejection before any native Git authority observation/project import/ref/evidence;
5. retain the existing fsmonitor/include rejection witnesses and all previously closed endpoint/no-replace/Evidence/CAS contracts.

## Evidence assessment

The reported `92/92 PASS`, py_compile, Ruff and diff-check are supportive only. They do not close either missing causal witness above because the remaining behavior is visible directly in the production bootstrap and the required adversarial cases are not represented by the current isolated-bootstrap tests.

## Blocker summary

- prior HIGH-1: PARTIALLY CLOSED
- prior HIGH-2: PARTIALLY CLOSED
- current blockers: `2 HIGH`
- design blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:165)`

This verdict binds only the exact formal pair `5efcbdf8954f65da9c7dfd1d0f34c96204c5ddf6 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Scope remains temporary CPU/static only. This review does not authorize real materialization/source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.
