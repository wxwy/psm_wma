# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `074d0a0f036ac6a107a693a3b9903d17e2565e10`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable (`fix: bind authority pass lifecycle identities`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental remediation review against prior ChatGPT review `8534ae8d5a0979a6dd7e90cedf45f6ad33a14ae5 / 93a89ba...` and approved PASS-linearization design v0.10. Reported `76/76` CPU tests and static checks are auxiliary evidence only.

## Prior blocker closure status

### Prior HIGH-1 — stale terminal-key substitution: CLOSED AS WRITTEN

`PublicationWitness._terminal_key` and `EvidenceCommit._terminal_key` are now write-once through their normal callback-visible interfaces, and the direct stale-accepted-key substitution regression is present. The prior `commit_B._terminal_key = witness_A._terminal_key` bypass is therefore closed under the implementation's normal object interface.

### Prior HIGH-2 — callback-visible/rewriteable `AcceptedPass`: CLOSED AS WRITTEN, but authority inputs remain callback-mutable

`_AcceptedPass` is no longer exposed as `commit._accepted_pass`; it is stored in an authority-private registry and its own identity/fact slots reject ordinary reassignment. `bind()` now verifies exact stored activation/witness/terminal identity and the evidence/ref facts. However the producer inputs that feed that capability are still rewriteable from the callback; see HIGH-1 below.

### Prior HIGH-3 — helper-success then pre-swap `BaseException`: CLOSED AS WRITTEN, but B fail-stop is not sticky against a swallowed callback exception

`consume_by_unlink()` now catches `BaseException` from `_commit_exact_guard()` itself and converts guard-absent outcomes to `PASS_CLOSURE_RECOVERY_REQUIRED`; the requested direct regression calls the real helper to completion and then raises. That closes the exact prior helper-return boundary. However `publish_candidate()` still relies on the recovery exception escaping the callback; see HIGH-2 below.

## Current blockers

### HIGH-1 — callback can still replace the authority-owned final-ref observer and binding inputs before `AcceptedPass.bind()`

**Location:** `tools/psm_wma/immutable_source_authority_root.py:444` (`EvidenceCommit.__setattr__`) and `PublicationWitness.__setattr__`

The remediation freezes `_witness`, `_activation`, `_terminal_key`, and `_token`, but it leaves other acceptance-authority fields callback-writeable. In particular:

- `EvidenceCommit._pre_unlink` remains assignable after construction;
- `EvidenceCommit._binding_sha256` remains assignable;
- `PublicationWitness.revision`, `_candidate`, and `_binding` remain assignable.

`_pre_unlink` is not incidental state. It is the only authority-owned producer of the v0.10 historical local/remote exact-candidate witness immediately consumed by `_AcceptedPass.bind()`. A finalizer can therefore replace it with a callable that simply returns `(witness.revision, witness.revision)` rather than observing Git refs.

A concrete false-accept path is reachable:

1. enter a legitimate finalizer and seal the correct evidence;
2. externally drift one fixed ref away from the candidate;
3. replace `commit._pre_unlink` with a callback returning the candidate tuple without ref I/O;
4. call `commit.consume_by_unlink()`;
5. evidence identity/digest checks pass, `_AcceptedPass.bind()` sees a syntactically exact candidate tuple, the guard transition succeeds and the terminal becomes ACCEPTED, even though the declared final-ref witness was fabricated rather than authority-observed.

The same class exists for the binding identity because both `witness._binding` and `commit._binding_sha256` can be rewritten consistently before bind. The current tests intentionally mutate several post-seal commit fields, but there is no negative proving the ref-observer/binding authority itself is immutable.

This violates the retained v0.8/v0.10 contract that candidate/binding/evidence/final-ref facts are authority-owned exact bindings, not values supplied or replaceable by the finalizer callback.

**Exact acceptance:** make every identity/witness producer that participates in acceptance immutable from callback code after authority construction. At minimum, the actual ref-observation callable/facts and binding identity used by `AcceptedPass.bind()` must not be replaceable through `EvidenceCommit` / `PublicationWitness`. Prefer keeping these authority facts in private authority state rather than callback-visible mutable slots. Add direct adversarial tests that:

- drift local or remote after seal;
- attempt to replace `_pre_unlink` with a forged candidate tuple producer;
- attempt to replace the witness/binding digest source;
- prove acceptance cannot occur, the real final observation cannot be bypassed, and foreign ref state is preserved/fail-closed under the existing rollback rules.

### HIGH-2 — B-window recovery is still exception-propagation dependent; a finalizer can swallow `PASS_CLOSURE_RECOVERY_REQUIRED` and trigger ordinary rollback after the guard is gone

**Location:** `tools/psm_wma/immutable_source_authority_root.py` `EvidenceCommit.consume_by_unlink()` and `publish_candidate()` callback dispatch

The current B handling correctly raises `PassClosureRecoveryRequired` when the guard helper has durably removed the public guard and terminal acceptance then fails. But the durable B fact is not latched in authority state. `publish_candidate()` only bypasses `_rollback()` when `callback_error` is an escaping `PassClosureRecoveryRequired`.

Because the finalizer is an arbitrary callback, it can legally catch that exception:

```python
try:
    commit.consume_by_unlink()
except PassClosureRecoveryRequired:
    pass
return None
```

At callback return the durable state is still B: guard absent, final evidence present, terminal PENDING, refs preserved so far. But `callback_error` is now `None`. `publish_candidate()` sees `commit.committed == False`, creates `_PreCommitFinalizerError(None)`, and enters the ordinary `_rollback(...)` path.

That directly violates v0.10: B is a permanent recovery-required fail-stop and callback outcome must not be able to turn it back into ordinary precommit rollback. This is the same authority principle that motivated the earlier v0.6 callback-outcome design: terminal semantics are determined by authority state, not by whether the callback propagates, catches, or returns from an exception.

**Exact acceptance:** once a durable guard transition has occurred while the terminal is still PENDING, recovery-required must become sticky authority state independent of callback exception propagation. `publish_candidate()` must inspect that authority-owned state after the callback and before any ordinary rollback decision. A finalizer swallowing the recovery exception must still produce `PASS_CLOSURE_RECOVERY_REQUIRED`, preserve refs, and never call `_rollback`. Add a direct test that performs the real guard transition, forces the pre-swap recovery path, catches/swallow the raised recovery exception inside the finalizer, returns normally, and proves the outer authority still fail-stops with refs preserved. Preserve ordinary A behavior when the guard never durably transitioned.

## Closed behavior retained

- `finalizer=None` success remains rejected before ref mutation;
- terminal state values remain frozen;
- stale terminal-key reassignment through ordinary callback attributes is rejected;
- `_AcceptedPass` is no longer exposed directly on `EvidenceCommit` and its own identity/fact slots are write-protected;
- the real helper-success-then-`BaseException` edge is converted to recovery-required when that exception escapes;
- restart preflight classification remains wired before ordinary fresh-path rejection;
- observation-only post-final-observation drift semantics remain intact;
- formal tree/Gitlink and the frozen four-file CPU/static scope remain unchanged.

## Blocker summary

- production/contract blockers: `2 HIGH`
- total blockers: `2 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:444)`

This verdict binds only the exact formal pair `074d0a0f036ac6a107a693a3b9903d17e2565e10 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains strictly within the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. This verdict does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
