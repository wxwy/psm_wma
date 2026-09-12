# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `bc40191f0e80f98201774cce8a1b551fa2343128`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable (`fix: close authority pass lifecycle gaps`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental remediation review against prior ChatGPT review `885b94fe8ed4c859014410dd7f53abb4550f3dc1 / 93a89ba...` and approved PASS-linearization design v0.10.

Reported `70/70` CPU tests and static checks are auxiliary evidence only.

## Prior blocker closure status

### Prior HIGH-1 — `finalizer=None` publication bypass: CLOSED

`publish_candidate()` now rejects `finalizer is None` before binding consumption or any ref mutation. The previously valid no-finalizer success path has also been removed from the normal positive tests.

### Prior HIGH-2 — private `AcceptedPass` missing: PARTIALLY CLOSED

A private `_AcceptedPass` object now exists and rejects copy/pickle through `_NonSerializable`. However it is not pre-bound to the complete frozen authority facts from v0.8/v0.10; see HIGH-2 below.

### Prior HIGH-3 — terminal state object mutable: CLOSED AS WRITTEN

`_AuthorityTerminalState` is now a frozen dataclass and direct member mutation tests were added. However the shared terminal **cell pointer** is still callback-mutable, which is a new authority-ownership bypass; see HIGH-1 below.

### Prior HIGH-4 — A/B/C crash/restart fail-stop absent: PARTIALLY CLOSED

A `classify_pass_restart()` helper and some interruption coverage were added, but the production B-window behavior and CLI restart handoff remain incorrect/incomplete; see HIGH-3 below.

## Current blockers

### HIGH-1 — finalizer callback can directly set the authority terminal cell to ACCEPTED and bypass guard/evidence acceptance

**Location:** `tools/psm_wma/immutable_source_authority_root.py:289` (`_AuthorityTerminalCell`) and `publish_candidate()` callback dispatch

v0.10 requires the terminal cell to be **authority-owned**, with the only semantic commit being the authority-controlled pointer replacement after the final fallible guard transition.

Current code passes `PublicationWitness` and `EvidenceCommit` into an arbitrary finalizer callback. Both objects retain the mutable cell as `_terminal`, and `_AuthorityTerminalCell.state` is publicly writable Python state. Therefore a callback can do the equivalent of:

```python
witness._terminal.state = _ACCEPTED_TERMINAL_STATE
return
```

without sealing evidence, without validating evidence identity/digest, without the final ref witness, and without executing `_commit_exact_guard()`.

After callback return, `publish_candidate()` checks only `commit.committed`, which derives from that same cell. It therefore treats the forged callback write as accepted publication, skips rollback, preserves both candidate refs, and returns `PublicationWitness`.

Freezing the PENDING/ACCEPTED *objects* does not close this: the cell pointer itself is the semantic authority and currently escapes to callback-controlled objects.

**Exact acceptance:** make the mutable terminal transition authority-private. Callback-visible witness/commit/pass surfaces must not expose a mutable cell reference or any equivalent setter. Only the exact authority-owned commit transition may replace PENDING with ACCEPTED. Add a direct adversarial callback test that attempts to mutate every callback-reachable terminal/acceptance field and proves it cannot make `commit.committed` true, cannot preserve refs, and cannot return a witness without the real evidence/guard transition.

### HIGH-2 — `_AcceptedPass` is still not bound to the frozen evidence and final-ref witness facts

**Location:** `tools/psm_wma/immutable_source_authority_root.py` class `_AcceptedPass` and `publish_candidate()` construction site

The retained v0.8/v0.10 contract says the private capability is pre-commit bound to:

- current activation identity;
- exact `PublicationWitness` / candidate revision;
- binding digest;
- sealed evidence FD identity and evidence digest;
- the last exact local/remote candidate observation that the observation-only terminal transition consumes.

Current `_AcceptedPass` stores only `_witness`, `_activation`, `_terminal`, and `_token`. It is constructed **before** the finalizer creates/seals evidence and before `pre_unlink()` performs the declared last exact ref observation. It therefore cannot bind the sealed evidence identity/digest or the final ref witness at all. Its `consume()` only checks witness identity, activation active, and `terminal.state.accepted`; it is effectively a ceremonial post-swap check rather than the frozen bound capability.

The new test checks copy/pickle and that consume-before-accept fails, but does not test wrong evidence identity/digest, wrong binding digest, wrong final ref witness, or activation/witness replay after those facts are bound.

**Exact acceptance:** keep the capability private, but complete its frozen pre-accept binding. Before the terminal pointer swap, bind and validate the exact candidate/binding identity plus the sealed evidence identity/digest and the exact last local/remote observation facts that v0.10 defines as the historical witness. No fallible allocation/validation may remain after the authority commit point. Add direct wrong-evidence, wrong-binding, wrong-ref-witness, replay/cross-activation negatives. If the implementation intentionally wants `EvidenceCommit` rather than `AcceptedPass` to own these facts, return to the design Gate and explicitly supersede the retained capability contract instead of silently weakening it.

### HIGH-3 — the durable B crash window still enters ordinary precommit rollback, and restart classification is not wired into the real CLI path

**Locations:** `tools/psm_wma/immutable_source_authority_root.py` `EvidenceCommit.consume_by_unlink()` / `publish_candidate()` and `tools/psm_wma/materialize_immutable_source_authority_root.py` preflight/main

v0.10 freezes:

- B = guard transition has succeeded, final evidence exists, terminal still PENDING;
- B is deterministic permanent fail-stop;
- B must not ordinary-retry/close/train and must not be rolled back as an ordinary precommit outcome;
- restart must surface the manual `PASS-CLOSURE-RECOVERY-DESIGN` handoff rather than infer acceptance from paths.

Current `consume_by_unlink()` performs:

```text
_commit_exact_guard(...)
terminal.state = ACCEPTED
```

A process interruption / `BaseException` can occur after `_commit_exact_guard()` has durably removed the guard but before the pointer assignment. In that state the finalizer exits with `commit.committed == False`; `publish_candidate()` converts it to `_PreCommitFinalizerError` and enters the ordinary `_rollback(...)` path. That is exactly the B window the design says must be permanent fail-stop, not rollback.

The added `test_guard_transition_interruptions_remain_pending_and_rollback` patches `_commit_exact_guard` to raise directly; it therefore exercises a failure **before** successful guard transition, not the required B case where the real guard transition succeeds and interruption occurs before the terminal pointer swap.

Separately, `classify_pass_restart()` is currently an isolated helper. `preflight_authority_invocation()` still rejects any existing evidence/guard with generic `evidence destination 必须为fresh absent absolute path`, and `main()` does not invoke the restart classifier before that path. A real re-invocation in B/C therefore follows ordinary preflight/failure-evidence behavior rather than deterministically surfacing `PASS_CLOSURE_RECOVERY_REQUIRED`.

**Exact acceptance:**

1. Implement a real B-window fail-stop path: once the exact guard transition has succeeded, any interruption before terminal acceptance must bypass ordinary ref rollback and produce/raise a stable recovery-required terminal outcome.
2. Add a direct adversarial test whose hook calls the real `_commit_exact_guard()` successfully and then raises ordinary/custom/`BaseException` before the terminal pointer swap. Prove guard absent + evidence present + PENDING never enters `_rollback` and never auto-retries/closes.
3. Wire restart classification into the actual CLI/preflight entrypoint before ordinary fresh-destination rejection/failure writing. B/C must deterministically surface recovery-required and must not overwrite/reclassify the existing evidence as a normal preflight FAIL.
4. Cover A with same-candidate foreign refs and prove ownership is never inferred from equality alone.

## Closed behavior retained

- no-finalizer success is now rejected before ref mutation;
- terminal state values are mechanically frozen;
- observation-only post-final-observation drift semantics remain correctly preserved in the dedicated regression;
- the formal tree/Gitlink and frozen four-file CPU/static scope remain unchanged.

## Blocker summary

- production/contract blockers: `3 HIGH`
- total blockers: `3 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:289)`

This verdict binds only the exact formal pair `bc40191f0e80f98201774cce8a1b551fa2343128 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains strictly within the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. This verdict does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
