# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `ad9e0110494a582e707ed5f041610d4cc40a82df`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable. Its `cosmos-framework` entry is independently verified as the exact submodule/Gitlink child `93a89ba61306d840a008813f62f26a34d54850f4`, and that child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental remediation review against prior ChatGPT review `313b1dc81d83646b310d86c58c10d20b453fc739 / 93a89ba...`, approved PASS-linearization design v0.10, and the already-approved real-adapter design chain through v0.6. Reported `79/79` CPU tests and static checks are auxiliary evidence only; the verdict below is based on the formal-tree production delta plus direct formal-tree test behavior.

## Effective delta

Relative to prior formal root `313b1dc81d83646b310d86c58c10d20b453fc739`, the only production semantic change is in `tools/psm_wma/immutable_source_authority_root.py` inside `EvidenceCommit.consume_by_unlink()`:

```python
except BaseException as error:
    if isinstance(error, PassClosureRecoveryRequired):
        authority.require_recovery()
        raise PassClosureRecoveryRequired() from error
    if not self._guard.exists() and not self._guard.is_symlink():
        authority.require_recovery()
        raise PassClosureRecoveryRequired() from error
    raise
```

The approved root test file is correspondingly updated for the foreign-public-guard handoff cases. No child/runtime production code changed; the Gitlink remains exact.

## Prior blocker closure

### Prior HIGH — helper recovery classification could be downgraded by caller when a foreign public guard occupied the pathname: CLOSED

The prior blocker required the helper's explicit `PassClosureRecoveryRequired` outcome to be authoritative and sticky, independent of pathname presence.

The current implementation now does exactly that: when `_commit_exact_guard()` explicitly raises `PassClosureRecoveryRequired`, `consume_by_unlink()` first calls `authority.require_recovery()` unconditionally and only then re-raises a stable `PassClosureRecoveryRequired`. It therefore no longer re-infers A/B from `path.exists()` when the helper has already established that exact original-guard restoration is unproven.

This preserves the intended distinction:

- pre-handoff failure, or post-handoff failure with mechanically proven restoration of the exact sealed original guard identity, may remain ordinary precommit/A behavior;
- post-handoff failure where exact restoration cannot be proven is sticky recovery/B and cannot be downgraded by callback handling.

## Direct causal Evidence

The formal-tree test `test_foreign_guard_after_handoff_prevents_commit_and_acceptance` now directly drives the production handoff path:

1. the real public guard is renamed to parking;
2. a foreign guard is created at the public pathname after handoff;
3. production `_commit_exact_guard()` cannot restore the exact original guard and raises `PassClosureRecoveryRequired`;
4. the finalizer catches/swallows that immediate exception via the local `assertRaises` context and then returns normally;
5. outer `publish_candidate()` still raises `PassClosureRecoveryRequired` because recovery was latched in authority state;
6. local and remote candidate refs remain present at the candidate revision;
7. no `delete_local` / `delete_remote` event occurs;
8. the foreign guard bytes remain untouched.

The companion boundary-replacement test is likewise tightened to recovery-required/preserve-refs semantics. These tests are causal for the exact prior regression: removing the new unconditional recovery latch would restore the previous ordinary-rollback behavior and fail the assertions.

## New-violation check

No new contract violation was found in the narrow remediation delta:

- PASS-linearization v0.10's A/B/C separation is preserved;
- the terminal-state acceptance transition remains unchanged;
- the finalizer return/exception dispatch contract remains unchanged;
- accepted-state/ref preservation and restart fail-stop rules are unchanged;
- existing ordinary A behavior remains available only where exact restoration/pre-handoff semantics prove it;
- remediation stays within the approved temporary CPU/static root tooling/test scope.

## Blocker summary

- production/contract blockers: `0`
- Evidence-only blockers: `0`
- total blockers: `0`

## Final verdict

`APPROVE_TO_CLOSE_R09_B_TTT_V035_PASS_LINEARIZATION_CPU_STATIC_IMPLEMENTATION`

This verdict binds only the exact formal pair `ad9e0110494a582e707ed5f041610d4cc40a82df / 93a89ba61306d840a008813f62f26a34d54850f4`.

It closes only the temporary CPU/static PASS-linearization implementation Gate. It does **not** authorize real source/selection/config/candidate/ref/origin/collection/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.