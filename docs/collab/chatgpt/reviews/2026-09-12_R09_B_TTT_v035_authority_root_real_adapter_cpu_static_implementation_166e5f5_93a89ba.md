# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `166e5f5f6470bcc7c77f8c3326914e1281e922b6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh implementation review following the approved v0.6 design pair `944c1305bcaef818e178c781b5cf2ce8aebbc9a8 / 93a89ba61306d840a008813f62f26a34d54850f4`.

The formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`; that child commit is reachable in `wxwy/cosmos-framework`.

Reported `36/36` stdlib tests, `py_compile`, and `git diff --check` are treated as auxiliary evidence only. The current review is based on the actual four-file implementation and the frozen v0.1-v0.6 design chain.

## Current blockers

### HIGH-1 — the approved real adapter/CLI execution seam is not implemented

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (module ends after `NativeAuthorityGit.cas_delete_remote`; no CLI/orchestrator exists)

The approved v0.1 design explicitly requires stage 1 to implement a root-only **real adapter/CLI**, with a readonly preflight that validates the two input FDs, exact/canonical bytes, formal-root full tree, child Gitlink, tool/interpreter/Git identity, fresh local+remote ref absence, and then directly invokes the already-closed `prepare_candidate -> verify_candidate -> publish_candidate` flow. It also requires an auditable argv for the later exact execution request.

The current module contains an evidence verifier/writer and a `NativeAuthorityGit` protocol implementation only. It never imports or invokes `prepare_candidate`, `verify_candidate`, or `publish_candidate`; it has no CLI entrypoint, no two-input-FD preflight, no exact frozen selection/config identity check at the adapter boundary, no tool/interpreter/Git identity preflight, and no executable argv surface for the next execution-request Gate.

This is not a cosmetic omission: the just-approved two-stage route depends on this Gate closing a runnable, reviewable adapter/CLI before the separately gated exact real execution request is constructed.

**Exact acceptance:** implement the frozen CLI/orchestration inside the approved four-file allowlist; keep all real execution disabled in tests. CPU/static tests must exercise exact CLI PASS plus pre-mutation rejection for input/raw-byte/formal-root/Gitlink/tool/ref identity drift and prove the CLI directly traverses `prepare_candidate -> verify_candidate -> publish_candidate` using only temporary repositories/remotes.

### HIGH-2 — CAS methods can report activation-owned success when the Git CAS command itself failed

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:525-538`

The four ref mutation methods do not bind success to the Git command return code. `_run(..., check=False)` returns only stdout, discarding the process return code. `cas_create_remote()` and both delete methods then decide success only from the freshly observed final ref value; `cas_create_local()` also cannot distinguish an empty-stdout failed `update-ref` from success before checking the final value.

This violates the frozen ownership rule that `local_owned` / `remote_owned` may become true **only because this activation's exact CAS succeeded**. A same-candidate race demonstrates the issue: after the pre-observation but before this activation's create CAS, a foreign actor can create the fixed ref at the exact candidate. This activation's expected-zero CAS then fails, but the subsequent fresh observation equals `revision`, so the current adapter can return `True` and falsely claim ownership. The analogous delete race can report successful conditional deletion merely because another actor deleted the ref first.

The existing fast-forwardable-foreign test covers a different-revision conflict, not same-candidate create or concurrent-delete attribution.

**Exact acceptance:** make each CAS result require both (a) the exact Git mutation command itself returned success and (b) the mandated fresh post-observation matches the expected terminal state. Preserve the exact-old lease/update-ref primitives. Add deterministic local+remote same-candidate create-race tests and local+remote concurrent-delete tests proving a failed command never yields an activation-owned success witness and never authorizes deletion of foreign state.

### HIGH-3 — detached commit identity still depends on ambient repository metadata and cannot satisfy the frozen execution request

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:509-515`

`NativeAuthorityGit.create_detached_commit()` builds a tree and calls `git commit-tree <tree> -p <parent>` without an explicit frozen commit message and without injected author/committer name, email, or timestamp. `NativeAuthorityGit.__init__()` exposes no commit-metadata inputs; its sanitized env contains only `GIT_INDEX_FILE`, `LC_ALL`, and `LANG`.

The design chain explicitly requires the future exact execution request to freeze `commit author/committer/message/timestamp`, and evidence v1 already records this exact `commit_metadata` object. With the current adapter, real candidate identity can depend on ambient repository config/current time, while the later execution request has no supported way to inject the frozen values without modifying this supposedly closed adapter or relying on ambient config.

**Exact acceptance:** make commit metadata an explicit immutable adapter/execution input, validate it before mutation, pass author/committer identity and timestamps through the sanitized environment, and pass the exact message through a deterministic `commit-tree` input/argv. Tests must prove ambient repo/user config and clock changes cannot alter the candidate when the frozen metadata is unchanged, and metadata drift changes/rejects identity as specified.

### HIGH-4 — Evidence v1 failure verifier is looser than the frozen exact ABI

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:44-49,160-181`

The frozen v0.4/v0.5 ABI says:

- `primary_phase` is only `preflight|prepare|verify|pre_publication|local_cas|remote_cas|post_publication|binding_reverify|evidence_write`; `rollback` is never a primary phase;
- ordinary `FAIL` and `PASS` must have `rollback_phase=null, rollback_code=null`;
- only `ROLLBACK_INCOMPLETE` carries the secondary `rollback` failure.

The implementation's `_PHASES` includes `"rollback"`, so an impossible record can use rollback as its primary phase. `_validate_failure()` also accepts a non-null secondary rollback phase/code for ordinary `FAIL`; it only requires the rollback phase for `ROLLBACK_INCOMPLETE`, not the converse. Those records violate the exact chronology the verifier is supposed to enforce.

**Exact acceptance:** remove `rollback` from the primary-phase set; enforce both directions of status/nullability (`PASS` all-null, ordinary `FAIL` primary-only with rollback fields null, `ROLLBACK_INCOMPLETE` primary + secondary rollback fields concrete); add direct negative tests for `primary_phase="rollback"` and ordinary `FAIL` carrying rollback secondary fields.

## Non-blocking findings

- The v0.6 post-commit finalizer outcome split is implemented in the right direction: callback `BaseException` is captured before the authority-owned committed-state dispatch, and committed callback errors are re-raised as `PostCommitFinalizerError` outside the rollback path.
- Evidence guard cleanup and single-FD reread coverage are materially improved.
- The formal Gitlink is unchanged and correct.
- No real I/O/origin/GPU/training authorization is inferred from this review.

## Blocker summary

- production/design blockers: `4 HIGH`
- Evidence-only blockers: `0` (HIGH-4 is an implementation blocker because the verifier itself violates the frozen ABI)
- total blockers: `4`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:525)`

This verdict binds only the exact formal pair `166e5f5f6470bcc7c77f8c3326914e1281e922b6 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation stays in the same CPU/static implementation Gate and must remain within the already approved four root files plus normal bookkeeping. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.