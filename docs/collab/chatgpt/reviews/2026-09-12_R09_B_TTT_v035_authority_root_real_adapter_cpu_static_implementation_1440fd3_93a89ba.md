# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `1440fd3391d46ef383d60387da8d7e7aa8238d5f`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh incremental review because the formal root changed from `e1d5e1115023caa0e18d80108f218a9f5d2382b6`; child/Gitlink is unchanged.

The formal root resolves to commit `1440fd3391d46ef383d60387da8d7e7aa8238d5f` (`fix: bind authority lock to evidence identity`). Its formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact SHA `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against:

- the approved real-adapter design chain v0.1-v0.6;
- prior ChatGPT exact-pair review `e1d5e111... / 93a89ba...`;
- current authority/adapter code and direct temporary CPU/static tests;
- the remediation diff that removes the sidecar `.lock` and instead flocks the opened final-evidence FD.

Reported `66/66` unittest, `py_compile`, Ruff and diff-check are auxiliary evidence only.

## Prior blocker closure status

The prior HIGH was that writer and verifier could lock different sidecar `.lock` inodes if the sidecar pathname was replaced.

The current pair removes that sidecar and is a meaningful improvement:

- `_evidence_guard_lock()` now opens the final evidence path with `O_NOFOLLOW`, verifies the opened object is regular, and flocks that FD;
- the writer requires the locked FD `(st_dev, st_ino)` to equal the sealed evidence identity;
- the verifier reads from the same locked FD rather than reopening the path;
- tests cover replacement immediately after writer flock acquisition and confirm that early replacement is detected before guard transition.

However the pathname namespace can still diverge **after** the writer's one-time path-identity check and before the public `.pending` guard transition. The sole remaining HIGH is below.

## Current blocker

### HIGH-1 — locking the old final-evidence inode does not serialize a later replacement inode; pathname replacement after the writer's lstat check can bypass the flock and re-open the early-visible PASS race

**Location:** `tools/psm_wma/immutable_source_authority_root.py:385` (`EvidenceCommit.consume_by_unlink`) and `tools/psm_wma/materialize_immutable_source_authority_root.py` (`verify_evidence_path`)

The current consume path does, under an exclusive flock on opened evidence inode **E1**:

1. `lstat(self._evidence_path)` and require the pathname currently resolves to sealed identity E1;
2. read/verify bytes from the already-open locked E1 FD;
3. perform the final fixed-ref recheck;
4. call `_commit_exact_guard(...)`, which moves the public `.pending` guard into private parking before completing parked verification/removal;
5. set `_committed=True` only after `_commit_exact_guard()` returns.

The writer does **not** revalidate that the public final-evidence pathname still resolves to E1 after step 1.

A reachable race therefore remains:

1. writer opens E1, takes exclusive flock, and passes the pathname→E1 identity check;
2. after that check but before `_commit_exact_guard()`, another actor removes the final-evidence pathname and creates **E2** at the same pathname containing the same valid PASS bytes;
3. verifier now opens E2 and takes a shared flock on E2. That flock is independent of the writer's exclusive flock on E1, so the verifier is not serialized with the writer;
4. writer enters `_commit_exact_guard()` and renames public `.pending` into parking. During that handoff the public guard is absent;
5. verifier on E2 can now observe `.pending` absent, read the valid PASS bytes from E2, and accept PASS;
6. if the writer's later parked-guard verification/removal fails, the authority still treats this as pre-commit, restores/fail-stops, keeps `commit.committed=False`, and can roll refs back.

That recreates the exact forbidden state:

`accepted PASS visible` while `EvidenceCommit` is still uncommitted and ref rollback remains reachable.

The new test `test_final_evidence_lock_identity_drift_preserves_guard` replaces the evidence pathname **inside the flock hook immediately after LOCK_EX is acquired**. That case is caught by the subsequent pathname `lstat()` and therefore does not cover the remaining window: replacement **after** the successful pathname identity check but **before** guard transition.

The same mechanism also means the synchronization authority is still the pathname namespace, not the locked FD alone: the verifier always opens whatever inode the public final-evidence pathname names at verifier start.

**Violated frozen contract:** accepted PASS visibility must be serialized with the exact authority-owned commit transition; no namespace replacement may let a verifier escape the writer's critical section, observe guard absence, and accept a PASS that can still be followed by rollback.

### Exact acceptance

1. Close the final-evidence pathname replacement window between the writer's last namespace identity proof and public guard transition. The verifier must not be able to lock a replacement inode and bypass the writer's critical section.
2. The object/namespace coordination primitive must remain valid through the exact guard commit transition; a one-time `lstat(path)==locked_fd_identity` earlier in the critical section is insufficient.
3. Add a direct adversarial test that:
   - lets writer obtain its exclusive final-evidence FD lock;
   - lets writer pass its current pathname-identity check;
   - then replaces the public final-evidence pathname with a new inode containing the same valid PASS bytes;
   - starts a verifier on that replacement inode;
   - injects failure after the public guard has been moved but before `_commit_exact_guard()` reports success;
   - proves the verifier never accepts PASS while `commit.committed` is false and rollback remains reachable.
4. Also test the success branch of the same replacement timing and prove a replacement pathname cannot become the accepted PASS authority unless it is the exact sealed evidence object.
5. If this cannot be made mechanically true while keeping `.pending` absence as the unique frozen commit signal, return to the design Gate rather than introducing another implicit coordination artifact/ABI in implementation.

## Closed findings retained

This review does **not** reopen the previously closed items:

- stale activation/capability isolation;
- final fixed-ref re-observation before guard transition;
- real FAIL / `ROLLBACK_INCOMPLETE` Evidence-v1 production;
- CAS ownership attribution;
- deterministic detached-commit metadata;
- loaded interpreter/module identity checks;
- cleanup object-identity preservation improvements.

## Blocker summary

- production/contract blockers: `1 HIGH`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:385)`

This verdict binds only the exact formal pair `1440fd3391d46ef383d60387da8d7e7aa8238d5f` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same four-file temporary CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
