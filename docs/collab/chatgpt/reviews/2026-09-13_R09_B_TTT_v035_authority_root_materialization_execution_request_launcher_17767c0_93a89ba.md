# ChatGPT Review — Authority-root Materialization Launcher Remediation

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-EXECUTION-REQUEST`

## Exact formal pair

- root docs SHA: `17767c0c52cb2e5856a9c98baf29f520ce27fc5b`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its exact `cosmos-framework` entry is a submodule/Gitlink to the stated child, and that child commit is independently reachable in `wxwy/cosmos-framework`.

The delta from prior pair `3b67d317de595ac8df2529eabfb239efbf988733` is docs/review bookkeeping plus eleven added lines in the materialization request. No production root tooling or child/runtime code changed.

## Progress from prior review

The prior launcher blocker is **partially** remediated. The request now explicitly separates launcher ownership from adapter ownership and defines the intended pre-adapter ordering plus the rule that launcher-owned cleanup failure terminates as `ROLLBACK_INCOMPLETE`. This closes the prior ambiguity around whether launcher-side worktree/backing mutations could be called a zero-mutation ordinary failure.

However, the approval object still does not contain the complete auditable launcher/command or an equivalent canonical launcher artifact/procedure with exact bytes/identity and invocation. The previous acceptance required that no authority-bearing choices remain after approval.

## Blocker

### HIGH-1 — launcher ownership semantics are described, but launcher execution authority is still not exact/reviewable

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.3.md:23`

The new text says the launcher will:

- check the clean root absent;
- create a detached worktree at the frozen formal parent;
- create three exclusive regular non-symlink backing objects;
- write/re-read frozen selection/config/contract bytes;
- open/bind FD 3/4/5 and close other inherited FDs;
- `execve` frozen Python/bootstrap/`--`/argv/environment;
- clean up launcher-owned objects on pre-adapter failure.

That is the correct *shape*, but it remains natural-language intent rather than a complete executable authority. The reviewed request still does not freeze, for example:

1. the exact native Git argv/prefix/env used for detached-worktree creation and any worktree removal/cleanup;
2. the exact three backing-object pathnames and their creation/write/fsync/re-read identity rules;
3. the exact descriptor transformation to FD 3/4/5 (`dup2`/equivalent), offsets, inheritance state, lifetime and close-set semantics;
4. the exact final `execve(path, argv, env)` arrays derived from annex v0.3;
5. the exact launcher-side cleanup commands/identity checks needed to prove ordinary failure restored the pre-launch state.

Because those choices still have to be made after approval, the request still does not satisfy the previously approved requirement that the **complete execution request and command** be reviewed before real materialization. The newly stated ownership/rollback semantics are necessary but not sufficient to make the launcher itself part of the frozen authority.

### Exact acceptance

1. Put the complete one-shot launcher/command in the reviewed request, **or** bind an equivalent canonical launcher artifact/procedure whose exact bytes/identity and invocation are reviewable. A prose sequence alone is insufficient.
2. Freeze exact detached-worktree creation and cleanup invocation(s), including absolute frozen Git executable, exact argv/prefix/environment, target path and formal parent. No shell, PATH, aliases, ambient config or caller-supplied values.
3. Freeze exact backing-object paths and exact create/write/fsync/re-read/open identity contract for selection/config/bootstrap-contract bytes. Any additional path is new authority and must be reviewed.
4. Freeze exact FD 3/4/5 binding: source descriptors, `dup2`/equivalent semantics, seek/offset state, `FD_CLOEXEC` transitions, lifetime and exact closure of all non-authorized inherited FDs before `execve`.
5. Freeze the exact final `execve` executable path, full argv array and environment array. These must be mechanically derivable from the already-approved annex v0.3 and introduce no new runtime value.
6. Freeze launcher-side rollback/cleanup commands and identity proofs. After any launcher-owned mutation, ordinary FAIL is permitted only after exact clean-root/admin/backing freshness is re-proven; otherwise terminal `ROLLBACK_INCOMPLETE`, no ref/materialization retry or continuation.
7. Preserve all existing scope prohibitions: no source/checkpoint I/O, collection/receipt/publication/root audit, child/runtime change, CUDA/GPU, training, evaluation, inference or LIBERO4IN1.

If implementing the launcher requires new executable/payload bytes or runtime values not already in annex v0.3, amend the same Gate and obtain a new exact-pair review before execution; do not open a separate horizontal provenance Gate.

## Blocker summary

- docs/request blockers: `1 HIGH`
- implementation blockers: `0`
- child/runtime blockers: `0`

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_execution_request_v0.3.md:23)`

This verdict binds only exact pair `17767c0c52cb2e5856a9c98baf29f520ce27fc5b / 93a89ba61306d840a008813f62f26a34d54850f4`.

No materialization is authorized by this review.