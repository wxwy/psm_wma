# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `8879742c4ea99bf2676903d4085a77aee91cd4e1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh remediation review because the formal root changed from `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49`; the child is unchanged.

The root commit resolves (`test: bind authority cleanup identity to fd`) and its formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against:

- the complete approved real-adapter design chain v0.1-v0.6;
- prior exact-pair review `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49 / 93a89ba...`;
- cumulative remediation diff `2249fdd3... -> 8879742...`;
- current four-file production implementation and temporary CPU/static tests.

Reported `58/58` unittest, `py_compile`, Ruff and task-scoped `git diff --check` are auxiliary evidence only.

## Prior blocker closure status

Three prior HIGHs are now closed and the fourth is materially reduced to one remaining atomicity defect:

1. **Prior exact activation / stale witness+commit blocker: CLOSED.** Authority now creates an opaque `_FinalizerActivation`, binds witness and commit to the same activation, requires `activation.active` for seal/consume, and invalidates the activation when the finalizer returns. The direct two-transaction stale retained pair is rejected before commit.
2. **Prior evidence-commit-point ref re-observation blocker: CLOSED.** `EvidenceCommit.consume_by_unlink()` now performs the authority-owned `pre_unlink` local+remote exact-candidate observation after record/identity validation and immediately before the guard-unlink operation. Direct local and remote drift injections after seal remain pre-commit and preserve foreign refs.
3. **Prior real FAIL / ROLLBACK_INCOMPLETE producer blocker: CLOSED.** Verify failures preserve the prepared candidate; input/request failures can emit preflight Evidence-v1; publication failures preserve endpoint observations; evidence-cleanup uncertainty is explicitly carried and serialized as `ROLLBACK_INCOMPLETE / EVIDENCE_CLEANUP_INCOMPLETE`. Temporary subprocess tests exercise these real producer paths through the independent verifier.
4. **Prior filesystem cleanup / exact guard identity blocker: PARTIALLY CLOSED.** Guard/temp identity is now captured from the creation FD, final identity is inherited from the hard-linked temp inode, final publication is no-overwrite, and cleanup refuses a pathname whose current inode already differs. One TOCTOU window remains at the actual unlink operation; see HIGH-1.

## Current blocker

### HIGH-1 — exact-object ownership is checked before deletion, but deletion is still pathname-based and can unlink a foreign replacement after the check

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py:930` (`_unlink_owned`) and `tools/psm_wma/immutable_source_authority_root.py` (`EvidenceCommit.consume_by_unlink`)

The remediation correctly records `(st_dev, st_ino)` from the FD that actually created guard/temp and uses those identities during cleanup. However `_unlink_owned()` is still:

```python
info = path.lstat()
if (info.st_dev, info.st_ino) != identity:
    return False
path.unlink()
```

The identity check and the destructive unlink are two separate pathname operations. A concurrent actor can replace `path` after `lstat()` succeeds but before `path.unlink()` executes; the current activation then deletes the foreign replacement even though the object it verified is no longer at the path.

The PASS commit guard has the same class of defect and a wider practical window. `EvidenceCommit.consume_by_unlink()` first verifies the stored guard/evidence identities, then executes `self._pre_unlink()`, which performs local/remote ref observations (including the remote lookup), and only afterwards calls `os.unlink(self._guard)`. A foreign actor can replace the guard during that ref-check interval. The subsequent pathname unlink removes the foreign guard and sets `_committed=True`, even though the exact guard object that was sealed is no longer the object consumed.

The new tests prove replacement **before** the identity check is preserved, which is useful, but they do not make the check-to-unlink transition conditional/atomic. This therefore still violates the frozen contract that cleanup only removes the exact activation-owned object and that `guard unlink succeeded <=> exact sealed EvidenceCommit consumed`.

**Exact acceptance:** keep remediation in this Gate and make each destructive evidence-path removal identity-safe at the actual mutation boundary. Acceptable implementations include an authority-owned directory-FD/OS primitive or equivalent serialized protocol where the object being removed is mechanically the same object whose identity was validated; a mutable pathname must not be re-resolved after the last identity proof without another fail-closed ownership transition. In particular:

1. guard commit must not mark `committed=True` unless the exact sealed guard object is the one removed;
2. guard/temp/final cleanup must never remove a replacement inode;
3. replacement occurring specifically **between the final identity observation and the unlink mutation** must fail-stop and preserve foreign bytes;
4. add direct adversarial tests that inject replacement at that boundary for both `EvidenceCommit.consume_by_unlink()` and `_unlink_owned()`/PASS cleanup, not only before the identity check.

## Non-blocking observations

- The new activation lifecycle is a substantial improvement and should be retained.
- Moving the final fixed-ref check into the authority-owned consume path closes the previous ref-race blocker under the frozen step ordering.
- The no-overwrite hard-link publication and FD-derived identities substantially improve writer ownership semantics.
- Failure-evidence production now covers the prior requested verify/pre-input/publication/cleanup terminal cases and should be retained.
- Before any real execution request, keep the remote identity credential-free/normalized and freeze the argv hashing convention exactly; those remain execution-request concerns, not blockers for this CPU/static closure.

## Blocker summary

- production/contract blockers: `1 HIGH`
- evidence-only blockers: `0`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/materialize_immutable_source_authority_root.py:930)`

This verdict binds only the exact formal pair `8879742c4ea99bf2676903d4085a77aee91cd4e1` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same CPU/static implementation Gate and within the approved four root files plus ordinary collaboration bookkeeping. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
