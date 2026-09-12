# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `313b1dc81d83646b310d86c58c10d20b453fc739`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable (`fix: preserve authority guard recovery`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental remediation review against prior ChatGPT review `a18d178877c192fdc9682033acbd36c4184b3639 / 93a89ba...` and approved PASS-linearization design v0.10. Reported `79/79` CPU tests and static checks are auxiliary evidence only.

## Prior blocker closure status

### Prior HIGH — helper could return `False` after losing public guard: PARTIALLY CLOSED

The remediation materially improves `_commit_exact_guard()`:

- handoff state is explicit via `handed_off`;
- after handoff, a non-success path only returns ordinary `False` when `restore_if_public_absent()` successfully restores the public path and a fresh `lstat()` proves the exact original `(st_dev, st_ino)`;
- failed restoration now raises `PassClosureRecoveryRequired` rather than silently returning ambiguous `False`;
- a new direct test covers parked-unlink failure + restore-rename failure with public guard absent, callback swallowing the immediate recovery exception, and outer sticky recovery preserving refs.

That closes the exact previous restore-failure/public-absent reproducer.

## Current blocker

### HIGH-1 — post-handoff foreign guard causes recovery to be raised but not latched, so callback swallowing can still downgrade an unrecovered handoff to ordinary rollback

**Location:** `tools/psm_wma/immutable_source_authority_root.py:135` (`_commit_exact_guard`) and `EvidenceCommit.consume_by_unlink()`

The prior acceptance was intentionally stronger than pathname existence: after a handoff, ordinary A/precommit rollback is allowed only if the **exact original public guard** is restored and its identity matches the sealed guard identity. Any outcome where exact restoration cannot be proven must become sticky recovery/B.

`_commit_exact_guard()` now follows that rule correctly. If a foreign `.pending` appears after the original guard has been renamed to private parking, `restore_if_public_absent()` returns `False` because the public pathname already exists, and `restore_or_recover()` raises `PassClosureRecoveryRequired`.

However `EvidenceCommit.consume_by_unlink()` still decides whether to latch sticky recovery by checking only pathname absence:

```python
try:
    guard_committed = _commit_exact_guard(...)
except BaseException as error:
    if not self._guard.exists() and not self._guard.is_symlink():
        authority.require_recovery()
        raise PassClosureRecoveryRequired() from error
    raise
```

If the helper raised `PassClosureRecoveryRequired` specifically because a **foreign guard now occupies the pathname**, `self._guard.exists()` is true. The exception is re-raised without `authority.require_recovery()`.

An arbitrary finalizer can then swallow that recovery exception and return normally. After callback return:

- exact original guard was handed off and not restored;
- a foreign guard remains at the public pathname;
- terminal state is still PENDING;
- `authority.recovery_required` is still false;
- `publish_candidate()` therefore enters `_PreCommitFinalizerError` and ordinary `_rollback(...)`.

The current direct test `test_foreign_guard_after_handoff_prevents_commit_and_acceptance` demonstrates this behavior: it creates a foreign guard after handoff, catches the `AuthorityRootError` inside the finalizer, and the outer assertions require both candidate refs to be deleted.

That violates the previous acceptance contract. A foreign pathname is not proof that the exact original guard was restored. Relying on the foreign guard as the thing hiding Evidence-v1 is unsafe: the foreign actor can later delete its own file, exposing final evidence after authority refs have already been rolled back.

This is also internally inconsistent with the new helper contract: the helper itself has already classified the outcome as `PassClosureRecoveryRequired`, but the caller discards that authority classification and re-infers A/B from pathname presence.

**Exact acceptance:**

1. Treat the helper's recovery outcome as authoritative. If `_commit_exact_guard()` raises `PassClosureRecoveryRequired`, `consume_by_unlink()` must latch `authority.require_recovery()` unconditionally before re-raising, independent of whether the public pathname is absent, foreign, replaced, or otherwise present.
2. Ordinary rollback after handoff is allowed only when helper non-success mechanically proves the exact original guard has been restored with the sealed identity.
3. Add a direct adversarial test for the existing foreign-guard path where:
   - real public -> parking handoff succeeds;
   - a foreign `.pending` appears at the public pathname;
   - helper raises `PassClosureRecoveryRequired` because exact original restoration is impossible;
   - finalizer catches/swallows the immediate recovery exception and returns normally;
   - outer `publish_candidate()` still raises stable `PASS_CLOSURE_RECOVERY_REQUIRED`;
   - local/remote candidate refs remain preserved and no delete event occurs;
   - foreign guard bytes remain untouched.
4. Keep the already-correct A behavior when failure occurs before handoff, or when post-handoff restoration of the exact original identity is proven.

A richer typed helper result is also acceptable, but pathname existence must not override an explicit recovery classification.

## Closed behavior retained

- acceptance authority inputs remain private and immutable from finalizer code;
- sticky recovery after terminal-transition failure remains correct;
- public-guard absent restore-failure now correctly latches recovery;
- stale terminal identity / AcceptedPass replay protections remain intact;
- restart preflight classification remains wired before ordinary fresh-path rejection;
- observation-only post-final-observation ref semantics remain intact;
- formal tree/Gitlink and frozen CPU/static scope remain unchanged.

## Blocker summary

- production/contract blockers: `1 HIGH`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:135)`

This verdict binds only the exact formal pair `313b1dc81d83646b310d86c58c10d20b453fc739 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains strictly within the already approved root tooling/test files and temporary directory/local bare-remote CPU/static tests. This verdict does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
