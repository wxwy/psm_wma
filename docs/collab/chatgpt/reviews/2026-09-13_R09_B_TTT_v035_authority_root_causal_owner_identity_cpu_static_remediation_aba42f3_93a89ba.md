# ChatGPT Review — Authority-root Causal Owner Identity CPU/static Remediation

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `aba42f3c077629074f3f8c03420bc8a01bc1ebd7`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The root commit is independently reachable. Its exact tree records `cosmos-framework` as mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior ChatGPT-reviewed pair `e88a9a9dd989e6a00e74d51ee9848b8ad241caa1 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Requested exact verdict:

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`

or `REQUEST_CHANGES(file:line)`.

Scope remains root-only stdlib temporary-fixture CPU/static implementation/tests. This review does not authorize production/main execution, real materialization, source/checkpoint I/O, project-path authority artifacts, collection/receipt/publication, child/runtime change, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.

## Authority and delta

The controlling authority remains approved causal-owner design v0.4, especially §3.1–§3.3, plus the exact acceptance in the prior `e88a9a9...` ChatGPT review.

The formal commit changes only:

- `SESSION.md`
- `TODO.md`
- `tools/psm_wma/materialize_immutable_source_authority_root.py`
- `tools/psm_wma/test_materialize_immutable_source_authority_root.py`

The child/Gitlink is unchanged.

## Prior blocker disposition

### HIGH-1 — bootstrap index admission froze inode identity without proving regular-file type: CLOSED

The prior exact acceptance required bootstrap to reject a non-regular FD8-relative `.authority-root.index` before any FD8 Git consumer.

At the new formal root:

1. the initial FD8-relative open remains `O_RDONLY|O_NOFOLLOW|O_CLOEXEC` with `dir_fd=ownerfd`;
2. immediately after `fstat`, bootstrap now requires `stat.S_ISREG(ii.st_mode)` before accepting `(dev, ino)` as `indexid`;
3. every later `ownerbarrier()` reopens the same FD8-relative entry with no-follow semantics and requires `stat.S_ISREG(y.st_mode)` before accepting identity equality;
4. `grun()` still executes `ownerbarrier(); routecheck()` before the Git subprocess and repeats both after it;
5. exact `close_fds=True, pass_fds=(ownerfd,)` remains intact.

Therefore the production bootstrap no longer admits a directory or other non-regular owner-relative index into the first FD8 Git consumer.

## Direct Evidence assessment

The new direct temporary-fixture witness `test_bootstrap_rejects_directory_index_before_git_consumer` replaces `.authority-root.index` with a directory before bootstrap proceeds. It injects a marker immediately before the actual `grun()` Git `subprocess.run` seam and asserts:

- bootstrap exits non-zero;
- the Git-consumer marker is absent, proving rejection before the first FD8 `grun()` consumer;
- no evidence file is created.

This is causally aligned with the frozen acceptance: if the new regular-file check were removed, a directory index could pass the identity-only capture and reach the marked Git consumer.

Codex reports `py_compile`, `68/68` direct stdlib CPU tests, and `git diff --check` PASS. Those counts are auxiliary only; the closure decision is based on the production source path plus the direct causal witness above.

## Regression / scope check

The remediation is narrow and does not weaken the previously closed requirements:

- production `NativeAuthorityGit` still requires exact FD8 for production construction;
- exact procfd cwd/index ABI remains unchanged;
- bootstrap owner/index pre/post barriers remain in place;
- route checks remain in place;
- exact FD8 descendant inheritance remains `close_fds=True, pass_fds=(8,)` for Git consumers;
- child/runtime is unchanged;
- no authorized scope expansion is present in the formal delta.

No new production, Evidence, child/runtime, or scope blocker was found in this formal pair.

## Blocker summary

- current blockers: `0`
- production/authority blockers: `0`
- Evidence-only blockers: `0`
- child/runtime blockers: `0`
- prior HIGH-1: **CLOSED**

## Final verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`

This verdict binds only exact pair `aba42f3c077629074f3f8c03420bc8a01bc1ebd7 / 93a89ba61306d840a008813f62f26a34d54850f4`.

It closes only this CPU/static implementation Gate. It does not authorize production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.