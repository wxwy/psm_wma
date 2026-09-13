# ChatGPT Review — Authority-root Causal Owner Identity CPU/static Remediation

**Date:** 2026-09-13  
**Gate:** `G0-R09-B-TTT-V035-AUTHORITY-ROOT-CAUSAL-OWNER-IDENTITY-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `e88a9a9dd989e6a00e74d51ee9848b8ad241caa1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is independently reachable. Its tree records `cosmos-framework` as mode `160000` at exactly `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh formal pair relative to the prior ChatGPT-reviewed pair `c8aafca005ff061788114281e47fd1a4e2b6a843 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Requested final verdict:

`APPROVE_TO_CLOSE_R09_B_TTT_V035_AUTHORITY_ROOT_CAUSAL_OWNER_IDENTITY_CPU_STATIC_IMPLEMENTATION`

or `REQUEST_CHANGES(file:line)`.

Scope remains root-only stdlib temporary-fixture CPU/static implementation/tests. No production/main execution, real materialization, source/checkpoint I/O, project-path authority artifacts, collection/receipt/publication, child/runtime change, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## Frozen authority

The controlling authority remains approved causal-owner design v0.4, especially §3.1–§3.3:

- every FD8 Git consumer uses exact `close_fds=True, pass_fds=(8,)`;
- before and after every consumer, FD8 owner identity and FD8-relative `.authority-root.index` / required owned-path identity are revalidated;
- any owner mismatch, FD8 close, procfs failure, **index/path type mismatch**, or inability to re-prove authority must fail closed before the next foreign consumption;
- post-exec owner ABI remains exact FD8 and exact procfd cwd/index/bootstrap-root fields.

## Prior blocker disposition

### Prior HIGH-1 — production `NativeAuthorityGit` admitted `owner_fd=None`: CLOSED

`NativeAuthorityGit.__init__` now rejects `production=True` unless `owner_fd == 8` before entering the optional owner branch. The exact procfd cwd/index check remains enforced when FD8 is present. Direct negative tests cover `None`, non-8, mismatched cwd, and mismatched index.

### Prior HIGH-2 — bootstrap `grun()` lacked per-consumer owner/index barrier: CLOSED as to identity ordering

`bootstrap_payload()` now captures the FD8 owner and index `(dev, ino)` and invokes `ownerbarrier(); routecheck()` before and after every `grun()` subprocess while retaining exact `close_fds=True, pass_fds=(ownerfd,)`. The remediation also adds a direct changed-index bootstrap witness.

## Current blocker

### HIGH-1 — bootstrap index admission freezes inode identity without proving the index is a regular file

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:341-344` (`bootstrap_payload()` → initial index capture / `ownerbarrier()`).

Current bootstrap code opens `.authority-root.index` with `O_RDONLY|O_NOFOLLOW|O_CLOEXEC`, immediately records only `(st_dev, st_ino)`, and repeats the same identity-only check in `ownerbarrier()`:

- initial `ii=os.fstat(ifd); indexid=(ii.st_dev,ii.st_ino)` has no `stat.S_ISREG(ii.st_mode)` check;
- repeated `y=os.fstat(j)` similarly compares only `(dev, ino)`.

On Linux, those open flags can successfully open a directory. Therefore an FD8 owner whose `.authority-root.index` entry is a directory can pass the bootstrap owner barrier and reach the first `grun()` Git subprocess with `GIT_INDEX_FILE=/proc/self/fd/8/.authority-root.index`. Git may then fail, but that is too late: the frozen v0.4 §3.2 contract requires an index/path **type mismatch** to fail closed before the FD8 consumer starts.

This is not merely an Evidence gap; it is a production authority gap in the import-free bootstrap path. The adapter-side helper `_fd8_index_identity()` already performs a regular-file check, but bootstrap duplicates the primitive rather than enforcing the same type contract.

**Violated frozen contract:** v0.4 §3.2 consumer pre/post identity barrier and explicit `index/path type不符` fail-close requirement before foreign consumption.

**Why current Evidence does not close it:** the new bootstrap witness replaces the index with another regular file and proves inode drift rejection. It does not cover a non-regular owner-relative index admitted before the first Git consumer. Reported `67/67`, `py_compile`, and `git diff --check` cannot close this semantic gap.

**Exact acceptance:**

1. at bootstrap initial FD8-relative index capture, require the opened `.authority-root.index` object to be a regular file before accepting/freeze-binding its identity;
2. retain no-follow FD8-relative checking and ensure subsequent barriers cannot accept a non-regular entry as valid authority;
3. add a direct temporary-fixture CPU witness where the owner-relative `.authority-root.index` is a directory (or other safely constructible non-regular object) and prove bootstrap rejects it **before any `grun()` Git consumer is launched**;
4. do not weaken exact `pass_fds=(8,)`, owner/index pre/post barriers, route checks, or existing ABI witnesses.

## Evidence assessment

The remediation materially closes both blockers from the prior pair. Source inspection confirms the owner-less production constructor route is gone and the bootstrap `grun()` pre/post identity ordering is present. However the bootstrap's duplicated index primitive is weaker than the frozen type contract.

I did not rely on Codex's reported `67/67` count as proof. An independent suite rerun was attempted in the reviewer sandbox, but that sandbox could not resolve `github.com`; this does not affect the source-level blocker above.

## Blocker summary

- current blockers: `1 HIGH`
- production/authority blockers: `1 HIGH`
- Evidence-only blockers: `0`
- child/runtime blockers: `0`
- prior HIGH-1: `CLOSED`
- prior HIGH-2: `CLOSED` as to requested identity ordering

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:341)`

This verdict binds only exact pair `e88a9a9dd989e6a00e74d51ee9848b8ad241caa1 / 93a89ba61306d840a008813f62f26a34d54850f4`.

No Gate closure is authorized from this pair. No production/main execution, real materialization, source/checkpoint I/O, project-path worktree/backing/index/candidate/ref/evidence creation, collection/receipt/publication, child/runtime modification, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.
