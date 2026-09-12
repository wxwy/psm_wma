# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `e1d5e1115023caa0e18d80108f218a9f5d2382b6`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `153bf17b3755b20296e69d2f5790becd8520875d`; child/Gitlink is unchanged.

The formal root is reachable. Its tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact SHA `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed incrementally against:

- the approved real-adapter design chain v0.1-v0.6;
- prior exact-pair ChatGPT review `153bf17... / 93a89ba...`;
- cumulative remediation from `153bf17...` to current formal root;
- current authority/adapter production code and temporary CPU/static tests.

Reported `64/64` unittest, `py_compile`, Ruff and `git diff --check` are auxiliary evidence only.

## Prior blocker closure status

The prior single HIGH was that private parking removed the public `.pending` guard before commit became irrevocable, so a verifier could observe PASS while authority still considered the path pre-commit and capable of rolling refs back.

The current remediation materially improves that path:

- `EvidenceCommit.consume_by_unlink()` now takes an exclusive `flock` via `_evidence_guard_lock()` while it re-validates guard/evidence identity, digest, fixed refs and the guard handoff;
- `verify_evidence_path()` takes a shared `flock` on the same sidecar lock path;
- tests show that a cooperating verifier opening the same lock inode blocks while the writer is in the parking handoff;
- parked verification failure restores the public guard before releasing the exclusive lock;
- a foreign `.pending` created after handoff prevents commit and remains visible to the verifier.

That closes the prior race **only when writer and verifier are guaranteed to synchronize on the same lock object**. The implementation does not currently make that guarantee; see the remaining HIGH.

## Current blocker

### HIGH-1 — the new sidecar `.lock` is an unbound replaceable pathname, so writer and verifier can flock different inodes and the original premature-PASS window reappears

**Location:** `tools/psm_wma/immutable_source_authority_root.py:116` (`_evidence_guard_lock`) and `tools/psm_wma/materialize_immutable_source_authority_root.py` (`verify_evidence_path`)

`_evidence_guard_lock()` derives `<evidence>.lock` and opens it with:

```text
O_CREAT | O_RDWR | O_NOFOLLOW | O_CLOEXEC
```

It then `flock()`s the returned descriptor. The lock object is not:

- required fresh/absent;
- created with `O_EXCL` and owned by the current transaction;
- bound to a frozen `(st_dev, st_ino)` identity;
- rechecked against the public lock pathname after lock acquisition;
- represented in the frozen evidence/writer contract.

The current tests exercise one stable lock inode, so writer-exclusive and verifier-shared locking serialize correctly. But a concrete race remains:

1. writer opens `.lock` inode **L1** and acquires exclusive flock;
2. another actor unlinks/replaces the `.lock` pathname with regular inode **L2** while writer still holds L1 open;
3. writer enters `_commit_exact_guard()` and renames public `.pending` into parking, so the public guard pathname is absent while the transaction has not yet set `EvidenceCommit.committed=True`;
4. verifier calls `verify_evidence_path()`, opens the current `.lock` pathname and therefore gets L2, successfully takes a shared flock because writer holds L1, not L2;
5. verifier sees `.pending` absent, reads the final PASS and can accept it while writer is still inside the pre-commit parking path;
6. a later parked-object failure / guard-restore / callback failure can still keep `commit.committed=False` and enter ref rollback.

This recreates the exact invariant violation from the previous review; the race has moved from the guard pathname to the newly introduced lock pathname.

A pre-existing foreign regular `.lock` is also silently accepted and reused, because neither preflight nor `_evidence_guard_lock()` establishes ownership or identity. The same problem means the serialized critical section is not an authority capability; it is only a best-effort convention on a mutable path.

**Violated frozen contract:** accepted PASS must not become verifier-visible before the authority-owned commit is irrevocable, and a shared serialization primitive is acceptable only if writer and verifier are guaranteed to participate in the **same** critical section. The prior review explicitly allowed a shared lock/transaction primitive, but not a replaceable lock path whose object identity is unfrozen.

**Exact acceptance:** make writer/verifier serialization identity-safe at the lock boundary, without weakening the frozen guard semantics. One acceptable implementation is to lock an already identity-bound stable object (for example the verified final evidence inode or an authority-owned stable directory FD) rather than an unfrozen sidecar pathname. If a sidecar lock remains, its exact object identity/lifecycle must be authority-owned and mechanically shared by writer and verifier; stale/pre-existing/replaced lock objects must fail closed before PASS can be accepted. Add direct adversarial CPU/static tests that:

1. replace the lock pathname after writer has acquired exclusive lock but before the public guard handoff;
2. start a verifier after that replacement and prove it cannot accept PASS on a different lock inode;
3. cover a pre-existing foreign regular `.lock`;
4. prove any lock identity drift either preserves the public guard or fail-stops with no accepted PASS and no ref rollback-after-acceptance.

If solving this requires changing the externally frozen evidence/verifier ABI or introducing a new durable coordination artifact, that change must return to a design Gate rather than being silently added in this implementation Gate.

## Closed findings retained

No regression was found in the closures previously established for:

- stale activation / witness+commit capability lifetime;
- final local+remote ref re-observation inside the authority-owned consume transition;
- identity-bound evidence/guard/record checks;
- verify/pre-input/publication failure Evidence-v1 production;
- `ROLLBACK_INCOMPLETE / EVIDENCE_CLEANUP_INCOMPLETE` handling;
- CAS ownership attribution and deterministic candidate commit metadata.

## Blocker summary

- production/contract blockers: `1 HIGH`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:116)`

This verdict binds only the exact formal pair `e1d5e1115023caa0e18d80108f218a9f5d2382b6` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same four-file temporary CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
