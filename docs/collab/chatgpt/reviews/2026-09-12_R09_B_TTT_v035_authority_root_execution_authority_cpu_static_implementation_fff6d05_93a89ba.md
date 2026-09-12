# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `fff6d05ef330ada5f6db5edbdc8dde32e2c99019`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is an actual submodule/Gitlink resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental implementation review against prior exact pair `817191c91ae8c8eb7e1a66f15055d2286d0b76c4 / 93a89ba...`. The remediation delta remains within the approved root adapter/test CPU/static scope plus normal status bookkeeping.

## Prior blocker closure progress

### Prior HIGH — linked-worktree/common-config authority: PARTIALLY CLOSED

The remediation materially closes most of the prior acceptance criteria:

- linked-worktree `.git` is now opened with no-follow semantics and parsed from a retained FD;
- the per-worktree admin `gitdir` reciprocal file and `commondir` are read through no-follow retained FDs;
- `git_dir` must be a descendant of the derived common directory;
- actual `<git_dir>/config.worktree` is rejected for linked worktrees;
- common config is opened through `O_NOFOLLOW`, its same-FD raw bytes and `(dev,ino,size)` identity are retained;
- each native bootstrap Git observation now checks the common-config pathname identity and retained-FD bytes before and after the Git subprocess;
- direct isolated fixtures cover an actual detached linked worktree with `config.worktree`, a forged gitdir escape, and common-config replacement after the precheck.

Those changes correctly fix the specific `817191c...` defects around the wrong `config.worktree` location and missing post-observation common-config revalidation.

## Current blocker

### HIGH-1 — the repository-routing authority (`.git` marker / `gitdir` / `commondir`) is still not frozen across the native Git observation

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:172`

For a linked worktree, native Git does not locate the repository from `<git_common_dir>/config` alone. It first consumes the worktree `.git` marker, then the per-worktree admin directory and its `commondir` routing metadata. The bootstrap now safely reads those files once, but `grun()` only revalidates the already-selected common config. It does not revalidate the pathname identity and retained-FD bytes of:

- `<worktree>/.git` (the marker opened as `afd`),
- `<git_dir>/gitdir` (the reciprocal file opened as `bfd`),
- `<git_dir>/commondir` (opened as `cfd0`),
- nor the already-derived `git_dir` / `git_common_dir` directory identities themselves.

Therefore there is still a routing-authority race: after bootstrap admission but before a native Git command actually resolves the repository, the `.git` marker or `commondir` can be replaced while the old common config remains byte-for-byte unchanged. Git can then execute against a different Git admin/common directory and consume a different local config/object authority, while the current before/after common-config checks continue to validate only the original config path. The newly added config-replacement witness does not cover this route-switch case.

This means the approved v0.4 requirement to freeze exact `git_dir` / `git_common_dir` authority before Git observations is still not causally complete for linked worktrees.

### Exact acceptance

1. For linked worktrees, retain the accepted raw bytes and `(dev,ino,size)` identities for the worktree `.git` marker, `<git_dir>/gitdir`, and `<git_dir>/commondir`, plus the accepted directory identities for `git_dir` and `git_common_dir`.
2. Immediately before **and after every** native bootstrap Git observation, revalidate that all routing paths still resolve to the same accepted identities/bytes and that `git_dir` / `git_common_dir` are still the same non-symlink directories; also keep `<git_dir>/config.worktree` absent across the observation.
3. For the primary worktree, likewise retain/revalidate the `.git` directory identity across the bootstrap Git observations so the repository route cannot be swapped underneath the common-config check.
4. Any marker/gitdir/commondir/directory/config.worktree drift must fail before project import, project callback, ref/evidence mutation or accepted closure.
5. Add direct isolated-bootstrap witnesses on an actual detached linked worktree that replace either the `.git` marker or `commondir` after the bootstrap precheck but before the real Git process executes, and prove rejection with no project-import sentinel/ref/evidence. A single wrapper may exercise both cases separately.
6. Retain all already-closed common-config same-FD checks, executable identity, four-module closure/symlink checks, endpoint/no-replace, Evidence ABI, production config authority and temporary CAS contracts.

## Evidence assessment

The reported `55/55` targeted tests, `100/100` combined stdlib tests, `py_compile` and `git diff --check` are supportive. The new actual-linked-worktree and config-replacement witnesses are useful and close real portions of the prior HIGH. They do not yet witness routing-metadata replacement between admission and native Git resolution, which remains visible directly in the production bootstrap.

## Blocker summary

- prior HIGH: PARTIALLY CLOSED
- current blockers: `1 HIGH`
- design blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:172)`

This verdict binds only the exact formal pair `fff6d05ef330ada5f6db5edbdc8dde32e2c99019 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Scope remains temporary CPU/static only. This review does not authorize real materialization/source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime changes, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.
