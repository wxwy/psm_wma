# ChatGPT Review — Authority-root Execution Authority Implementation Design v0.3

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-EXECUTION-AUTHORITY-IMPLEMENTATION-DESIGN`

## Exact formal pair

- root design SHA: `65836016ebc4fbcb73c50dc055cae206a690bc4f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental design review against the prior exact pair `e69d78c02bd946d44a3a00e455668e83a639917c / 93a89ba...`. The effective semantic delta is docs-only and adds v0.3 local-config authority ABI; no root tooling or child/runtime implementation changes are in this formal pair.

## Prior blocker closure

### Prior HIGH — local Git config authority lacked a complete typed policy/ABI: PARTIALLY CLOSED

v0.3 correctly adds typed parser/invocation/Evidence-v1 fields for `git_dir`, `git_config_path`, `git_config_raw_sha256`, and `git_config_allowlist`; enumerates accepted key/value constraints; includes the config authority in the production-computed isolation fingerprint; requires exact runtime recomputation and direct native temporary-repository positive/negative witnesses.

That closes the prior omission of a concrete config authority channel. However the path-resolution rule does not bind the config that Git actually treats as local config for a linked/detached worktree, so the previous security property is not yet mechanically achieved.

## Current blocker

### HIGH-1 — `git_config_path = git_dir/config` is wrong for linked worktrees and can audit the wrong file while Git consumes the common repository config

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.3.md:7`

v0.3 says `git_dir` is derived from `git rev-parse --git-dir`, then requires `git_config_path` to be exactly `git_dir/config` and treats that file's raw SHA/allowlist as the local-config authority.

That is not a valid general Git contract for the controlled clean-worktree execution this project is designing. In a linked/detached worktree, `git rev-parse --git-dir` resolves to the per-worktree administrative directory (for example `.git/worktrees/<name>`), while `git config --local` normally reads the common repository config under the common Git directory (`git rev-parse --git-common-dir` + `/config`) when `extensions.worktreeConfig` is not enabled. The per-worktree admin directory need not contain `config` at all. Therefore the current contract can hash/allowlist a nonexistent or irrelevant `git_dir/config` while the actual Git subprocess still consumes a different common config containing `url.*`, `remote.*`, include, protocol, filter, or other authority-changing entries.

The design also describes the `git_dir` result using an `lstat regular/non-symlink Git-dir marker` rule even though the resolved Git dir itself is a directory. That makes the intended path/type check ambiguous and risks rejecting a correct repository while still not identifying the effective config source.

This directly violates the previous acceptance criterion: the exact config bytes/policy that influence native Git must be identified, frozen, re-read, and evidenced before the first object/ref/transport action.

**Exact acceptance:**

1. Freeze separate typed identities for the actual Git directory and common Git directory, derived under the already-frozen Git executable/env/prefix using `git rev-parse --absolute-git-dir` and `git rev-parse --git-common-dir` (or an equivalently exact no-config-dependent mechanism), with exact directory/path-type and symlink-escape checks.
2. With `extensions.worktreeConfig` required absent/false, define the authoritative local config as the common Git dir's `config`; bind its exact absolute path, raw SHA-256, canonical parsed mapping/allowlist, and production-computed fingerprint. If worktree-specific config is ever allowed, it needs its own explicit path/bytes/ABI and precedence contract; do not infer it from `git_dir/config`.
3. The config parsed by `git config --no-includes --local --null --list` must be proven to come from the same frozen effective config authority; any mismatch between raw file authority and parsed Git view is fail-closed before the first authority action.
4. Add a direct native witness using an actual linked/detached temporary worktree: place a forbidden `url.*`/`remote.*`/include entry in the common repo config while the per-worktree admin dir has no config; production preflight must reject before object/ref/transport action. Add the accepted minimal linked-worktree case as the positive control.
5. Preserve all v0.2 bootstrap observation, endpoint, no-replace/config-isolation, four-module closure, direct CAS, and CPU/static scope contracts.

## Blocker summary

- prior HIGH: PARTIALLY CLOSED
- current blockers: `1 HIGH`
- production implementation blockers: `0` (implementation is not yet authorized)

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_authority_root_execution_authority_implementation_design_v0.3.md:7)`

This verdict binds only the exact formal pair `65836016ebc4fbcb73c50dc055cae206a690bc4f / 93a89ba61306d840a008813f62f26a34d54850f4`.

No modification of the two root tooling files, real materialization/source/checkpoint I/O, candidate/ref/evidence mutation, collection/receipt, child/runtime changes, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
