# ChatGPT Review — Authority-root Execution Authority CPU/static Implementation Remediation Closure

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root implementation SHA: `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is an actual Gitlink (`160000 commit`) resolving to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is an incremental implementation review against prior exact pair `fff6d05ef330ada5f6db5edbdc8dde32e2c99019 / 93a89ba...`. The effective remediation delta remains within the approved root adapter/direct stdlib test scope plus collaboration/status bookkeeping; child/runtime code is unchanged.

## Prior HIGH closure

### Prior HIGH — repository-routing metadata was not frozen across native Git observations: CLOSED

The prior review required the linked-worktree routing authority (`.git` marker, `<git_dir>/gitdir`, `<git_dir>/commondir`, `git_dir`, `git_common_dir`, and `config.worktree` absence) to be retained and revalidated together with common-config authority immediately before and after every bootstrap native Git observation.

The production bootstrap now does that:

- for a normal worktree, `.git` is opened as a no-follow directory FD and its directory identity is retained in `routedirs`;
- for a linked worktree, the `.git` marker is opened no-follow and its raw bytes plus `(dev, ino, size)` are retained;
- `<git_dir>/gitdir` and `<git_dir>/commondir` are opened no-follow and their raw bytes plus identities are retained;
- the resolved `git_dir` and common Git directory are opened no-follow as directory FDs and their identities are retained;
- the real `<git_dir>/config.worktree` path must remain absent;
- the common config remains bound by the retained no-follow FD, pathname identity, size and raw bytes;
- `routecheck()` revalidates all retained routing files, routing directories, `config.worktree` absence and common-config identity/bytes before and after every `rev-parse`, `status` and `ls-tree` bootstrap Git observation.

This directly closes the route-switch window identified in the previous review: persistent replacement of the worktree marker, `gitdir`, `commondir`, Git-directory identity, `config.worktree` state or common-config path/bytes is rejected before the bootstrap can proceed to project import.

## Direct causal witnesses

The direct stdlib tests now include actual detached linked-worktree adversarial cases through the production bootstrap:

- pre-existing real `<git_dir>/config.worktree` rejects before evidence/ref acceptance;
- forged linked-worktree Git-dir escape rejects;
- common-config replacement after the precheck rejects;
- actual linked-worktree `.git` marker replacement after the precheck rejects;
- actual linked-worktree `commondir` replacement after the precheck rejects.

The marker/commondir race witness uses a frozen test Git wrapper to perform the replacement immediately after bootstrap precheck and before delegating to the real Git executable. The production post-observation `routecheck()` then detects the changed pathname identity, and the test proves a failing bootstrap with no accepted evidence path or authority ref. Source ordering additionally makes the rejection occur inside `grun()` before the later `sys.path.insert()` / `runpy.run_module()` transition.

Reported targeted `56/56`, combined root stdlib `101/101`, `py_compile` and `git diff --check` are supportive; the approval is based on the production authority path plus those direct adversarial witnesses rather than counts alone.

## Regression / scope check

No regression was found in the previously closed CPU/static contracts:

- process-level `sys.orig_argv` bootstrap source/argv binding remains before project import;
- interpreter and Git regular/non-symlink/raw-SHA/exact-version identity remains pre-import;
- adapter/authority/collection/audit formal-tree + raw-byte closure remains pre-import;
- canonical endpoint / no-remote-alias and no-replace/config-isolation rules remain intact;
- common-config allowlist and worktreeConfig rejection remain fail-closed;
- Evidence-v1 and temporary local/bare CAS behavior are not widened by this remediation;
- formal child/Gitlink is unchanged.

No real materialization/source/checkpoint I/O, project origin/ref/evidence mutation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference or LIBERO4IN1 is authorized by this closure.

## Blocker summary

- prior routing-authority HIGH: `CLOSED`
- current implementation blockers: `0`
- design blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_EXECUTION_AUTHORITY_CPU_STATIC_IMPLEMENTATION`

This approval binds only the exact formal pair `9dd2fb8b63ccd6a3193eec7ab6584cc24a68a4a5 / 93a89ba61306d840a008813f62f26a34d54850f4` and the temporary CPU/static scope above.