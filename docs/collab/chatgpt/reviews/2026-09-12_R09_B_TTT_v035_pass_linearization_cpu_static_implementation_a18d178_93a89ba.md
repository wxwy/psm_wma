# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `a18d178877c192fdc9682033acbd36c4184b3639`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable (`fix: harden authority acceptance recovery`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental remediation review against prior ChatGPT review `074d0a0f036ac6a107a693a3b9903d17e2565e10 / 93a89ba...` and approved PASS-linearization design v0.10. Reported `78/78` CPU tests and static checks are auxiliary evidence only.

## Prior blocker closure status

### Prior HIGH-1 — callback can replace final-ref observer / binding authority inputs: CLOSED

The new `_AcceptanceAuthority` is constructed before the finalizer and privately owns the exact revision, binding digest, and final-ref observer. `EvidenceCommit` no longer carries callback-writeable `_pre_unlink` or `_binding_sha256`, while `PublicationWitness.revision/_candidate/_binding` are write-once. `AcceptedPass.bind()` consumes the private authority's revision/binding and the private observer output. The direct regression that attempts to replace the old callback-visible observer/binding sources is present.

### Prior HIGH-2 — B recovery could be swallowed by the callback and fall back to rollback: CLOSED AS WRITTEN

`_AcceptanceAuthority` now has sticky `recovery_required` state. When guard transition has become durable but terminal acceptance fails, `consume_by_unlink()` latches recovery before raising `PassClosureRecoveryRequired`. After the arbitrary finalizer returns, `publish_candidate()` checks the authority latch before any ordinary precommit rollback decision. The new direct regression swallows `PassClosureRecoveryRequired` inside the finalizer and still proves the outer authority fail-stops with refs preserved and without delete events.

## Current blocker

### HIGH-1 — `_commit_exact_guard()` can return `False` after losing the public guard, so an unprovable B state can still be misclassified as ordinary precommit failure and rolled back

**Location:** `tools/psm_wma/immutable_source_authority_root.py:135` (`_commit_exact_guard`) and `EvidenceCommit.consume_by_unlink()`

The sticky-B remediation correctly handles two cases:

1. `_commit_exact_guard()` raises a `BaseException` and the public guard is absent: recovery is latched;
2. `_commit_exact_guard()` returns `True`, followed by terminal-transition failure: recovery is latched.

But the helper's `False` result does **not** mechanically mean the public guard is present/restored.

Current helper flow can do:

```text
rename(public guard -> private parked)
...
os.unlink(parked) raises OSError
restore_if_public_absent() tries os.rename(parked -> public) and that restore raises OSError
return False
```

`restore_if_public_absent()` returns `False` on restore failure, but its return value is ignored by the helper's failure branches. The same issue exists for other post-handoff failure branches that call restore and then unconditionally return `False`.

Therefore `_commit_exact_guard()` may return `False` while:

- final Evidence-v1 still exists;
- the public `.pending` guard is absent;
- terminal state is still PENDING;
- refs are still candidate/owned.

That is exactly the durable B/recovery state from v0.10, not an ordinary A/precommit failure.

However `consume_by_unlink()` currently does:

```text
if not guard_committed:
    raise AuthorityRootError("evidence commit guard identity 漂移")
```

without proving that the exact public guard has been restored. The finalizer can then return/propagate this ordinary error; `publish_candidate()` sees no sticky recovery latch and enters ordinary `_rollback(...)`, violating the permanent B fail-stop contract.

Existing tests cover successful restoration after a parked `lstat` failure and cover helper-success-then-`BaseException`, but they do not cover **helper returns False after public handoff plus failed restore**, leaving public guard absent.

**Exact acceptance:** every non-success helper outcome must have one of two mechanically proven meanings:

1. ordinary precommit/A outcome: the exact original public guard is present again with the expected identity before returning/raising; or
2. recovery/B outcome: guard restoration cannot be proven, so the authority latches `recovery_required` and surfaces stable `PASS_CLOSURE_RECOVERY_REQUIRED`, preserving refs and bypassing ordinary rollback.

A plain `False` result must never mean "guard state unknown/absent".

Add direct adversarial coverage for at least:

- real public->parking handoff succeeds;
- parked unlink (or another post-handoff step) fails;
- restore rename also fails;
- helper leaves public guard absent;
- outer result is `PASS_CLOSURE_RECOVERY_REQUIRED` even if the finalizer catches/swallow the immediate error;
- local/remote refs remain preserved and `_rollback` delete events do not occur;
- restart classification sees guard-absent evidence and routes to recovery.

Also retain the existing A behavior: if the helper fails before durable handoff, or can prove the exact guard was restored, ordinary rollback remains allowed.

## Closed behavior retained

- `finalizer=None` success remains rejected before ref mutation;
- terminal state values and terminal identity bindings remain protected from ordinary callback reassignment;
- private `AcceptedPass` identity/facts remain non-copyable/non-pickle and authority-bound;
- final ref observation and binding authority are now held in private `_AcceptanceAuthority` rather than callback-writeable commit fields;
- swallowed B-window recovery is sticky at the authority level;
- helper-success-then-`BaseException` is recovery-required;
- restart preflight classification remains wired before ordinary fresh-path rejection;
- observation-only post-final-observation drift semantics remain intact;
- formal tree/Gitlink and frozen four-file CPU/static scope remain unchanged.

## Blocker summary

- production/contract blockers: `1 HIGH`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:135)`

This verdict binds only the exact formal pair `a18d178877c192fdc9682033acbd36c4184b3639 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains strictly within the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. This verdict does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
