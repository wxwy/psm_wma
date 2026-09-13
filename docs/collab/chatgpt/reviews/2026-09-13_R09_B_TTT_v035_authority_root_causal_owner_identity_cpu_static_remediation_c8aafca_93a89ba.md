# ChatGPT Review — Authority-root Causal Owner Identity CPU/static Remediation

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `c8aafca005ff061788114281e47fd1a4e2b6a843`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. At that exact root, `cosmos-framework` is a submodule/Gitlink to exactly `93a89ba61306d840a008813f62f26a34d54850f4`; the child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh remediation pair relative to the prior ChatGPT-reviewed implementation pair `5a2a3207853cdbbe4dc8135080cd5fe5050b7787 / 93a89ba61306d840a008813f62f26a34d54850f4`. The formal commit changes only `SESSION.md`, `TODO.md`, `tools/psm_wma/materialize_immutable_source_authority_root.py`, and its direct stdlib CPU test. Child/runtime remains unchanged.

Requested verdict:

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`

or `REQUEST_CHANGES(file:line)`.

This Gate remains limited to root-only stdlib temporary-fixture CPU/static implementation/tests. It does not authorize production/main execution, real materialization, source/checkpoint I/O, project authority artifacts, collection/receipt/publication, child/runtime changes, GPU, training, evaluation, inference, or LIBERO4IN1.

## Frozen authority used

The controlling authority is the approved v0.4 causal-owner design plus the exact acceptance from the prior `5a2a320...` review. In particular:

- final post-exec owner ABI is exact FD8 with mandatory `--bootstrap-owner-root-fd 8` and exact procfd cwd/index/bootstrap-root fields;
- every production/FD8 consumer must fail closed rather than admit a legacy pathname owner route;
- every bootstrap `grun()` and every `NativeAuthorityGit` Git invocation that consumes FD8-derived paths uses exact `close_fds=True, pass_fds=(8,)`;
- before and after **each** FD8 consumer, owner identity and the owner-relative index/required path identity must be revalidated;
- bootstrap project-module closure uses FD8-started component-by-component `O_DIRECTORY|O_NOFOLLOW` plus leaf `O_NOFOLLOW` before import;
- owner-mode runtime checks must not canonicalize procfd to global CLEAN; loaded adapter/authority identity must remain bound to the FD8 owner object.

## Prior blocker disposition

### Prior HIGH-1 — FD8 ABI optional/non-exact: PARTIALLY CLOSED / STILL BLOCKING

The remediation correctly makes `--bootstrap-owner-root-fd` required in argparse, requires bootstrap `ownerfd==8`, freezes `cwd=/proc/self/fd/8`, `index=/proc/self/fd/8/.authority-root.index`, and `bootstrap-project-root=/proc/self/fd/8`, and removes the owner-mode `Path.resolve()` equality check.

However one second production admission path remains: `NativeAuthorityGit(production=True, owner_fd=None)` is still accepted. The exact FD8 check is nested inside `if owner_fd is not None`, so the production transaction can still be constructed without any owner capability and falls back to ordinary pathname cwd/index behavior.

### Prior HIGH-2 — bootstrap project modules lacked component no-follow closure: CLOSED

The import-free bootstrap now starts each formal project-module read from `os.dup(ownerfd)`, opens every intermediate component using `O_DIRECTORY|O_NOFOLLOW`, opens the leaf using `O_NOFOLLOW`, validates regular-file type, reads bytes from the opened FD, and retains formal-tree blob/raw-SHA checks before `sys.path` / `runpy`. A direct isolated bootstrap intermediate-component symlink witness was also added.

### Prior HIGH-3 — procfd canonicalization / loaded module content-only identity: CLOSED

`_bootstrap_identity_from_runtime()` now validates exact raw FD8 procfd fields rather than resolving cwd/bootstrap-root. `_verify_loaded_identity()` reads expected module bytes through the owner-FD no-follow traversal and additionally compares the actual loaded adapter/authority `(dev, ino)` against the corresponding FD8-relative no-follow object identity. This materially closes the prior same-content-at-foreign-path acceptance flaw.

## Current blockers

### HIGH-1 — production `NativeAuthorityGit` still admits `owner_fd=None`, leaving a legacy non-FD8 authority route

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:1614` (`NativeAuthorityGit.__init__`).

The constructor currently performs the exact production FD8 rejection only inside `if owner_fd is not None:` and then checks `if self.production and owner_fd != 8`. Therefore `NativeAuthorityGit(..., production=True, owner_fd=None)` bypasses the exact FD8 requirement entirely. It initializes with ordinary `cwd/index`, `_verify_owner_barrier()` becomes a no-op, and `_git_consumer_kwargs()` returns only `close_fds=True` without `pass_fds=(8,)`.

This is a real second production admission path. The fact that `main()` now passes a required parser field does not close the constructor's own production authority contract: the class itself is the production Git transaction owner used by the adapter and remains callable with `production=True` and no owner capability.

**Violated frozen contract:** v0.4 exact final FD8 ABI; activation fail-closed/no legacy pathname fallback; prior HIGH-1 exact acceptance requiring the exact value 8 in `NativeAuthorityGit` owner binding.

**Why current Evidence does not close it:** the positive harnesses provide FD8. No direct witness shown by the formal delta constructs `production=True, owner_fd=None` and proves rejection before any Git/config/module consumption.

**Exact acceptance:**

1. reject production construction unless `owner_fd == 8` **before** any owner/path-derived Git authority is accepted; do not nest the production requirement under `owner_fd is not None`;
2. require exact `/proc/self/fd/8` cwd and `/proc/self/fd/8/.authority-root.index` for production owner mode;
3. add direct negative witnesses for `production=True` with `owner_fd=None`, non-8 owner, mismatched cwd, and mismatched index; all must fail before Git/config/module consumption;
4. keep non-production temporary helper behavior only where explicitly needed by existing CPU fixtures; it must not become a production fallback.

### HIGH-2 — bootstrap `grun()` passes FD8 but does not implement the frozen per-consumer pre/post owner/index identity barrier

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:350` (`bootstrap_payload()` → `routecheck()` / `grun()`).

The remediation correctly makes bootstrap owner FD8 mandatory and launches each bootstrap Git probe with exact `close_fds=True, pass_fds=(ownerfd,)`. But `grun()` currently does only `routecheck()` → `subprocess.run(...)` → `routecheck()`.

The frozen v0.4 §3.2 requires **every** FD8 consumer, explicitly including import-free bootstrap `grun()` Git probes, to perform an owner capability barrier before and after the subprocess: live `fstat(8)` identity plus FD8-relative no-follow validation of `.authority-root.index` and any required owned path, followed by revalidation after return.

`routecheck()` preserves existing Git route/config FDs and bytes, but it does not freeze and compare the FD8 owner `(dev, ino)` or `.authority-root.index` identity around each `grun()` call. In particular, the bootstrap payload has no captured index identity analogous to `NativeAuthorityGit._index_identity`. Thus the adapter-side consumer barrier is implemented, while the bootstrap consumer barrier named by the design is not.

**Violated frozen contract:** v0.4 §3.2 consumer pre/post identity barrier; direct causal Evidence requirement for the actual consumer.

**Why current Evidence does not close it:** the actual changed-index witness exercises `NativeAuthorityGit`, not bootstrap `grun()`. The new bootstrap intermediate-component symlink test proves module traversal, not the missing Git-consumer owner/index barrier.

**Exact acceptance:**

1. in import-free bootstrap, capture the initial FD8 owner identity and FD8-relative `.authority-root.index` identity using no-follow FD operations;
2. before and after every `grun()` subprocess, revalidate FD8 owner identity and the relevant owner-relative index/required path identity; mismatch must fail closed before further foreign consumption;
3. retain exact `close_fds=True, pass_fds=(8,)` and no FD3/4/5 leakage;
4. add a direct isolated bootstrap Git witness that changes/replaces the owner-relative index (or otherwise invalidates the frozen owner barrier) between Git consumers and proves the next `grun()` rejects before foreign consumption.

## Evidence assessment

The reported `63/63` CPU tests, `py_compile`, and `git diff --check` are useful auxiliary evidence. The remediation now has a direct bootstrap intermediate-component symlink witness and retains actual temporary-Git FD8 coverage. However those results cannot close the two production authority gaps above.

This remains a **production-blocking** review, not Evidence-only.

## Blocker summary

- current blockers: `2 HIGH`
- production/authority blockers: `2 HIGH`
- Evidence-only blockers: `0`
- child/runtime blockers: `0`
- prior HIGH-2: `CLOSED`
- prior HIGH-3: `CLOSED`
- prior HIGH-1: materially improved but not closed because a production owner-less constructor route remains

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:1614)`

This verdict binds only exact pair `c8aafca005ff061788114281e47fd1a4e2b6a843 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No Gate closure is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
