# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `885b94fe8ed4c859014410dd7f53abb4550f3dc1`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable (`fix: linearize authority pass state`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Fresh implementation review against:

- approved PASS-linearization design v0.10 formal `001336fa5d785d8c77a2685ac1c754c096b4fb06 / 93a89ba...`;
- retained v0.8/v0.9 contracts: external `PublicationWitness` ABI, private opaque `AcceptedPass`, one immutable authority terminal-state cell, A/B/C crash semantics, path verifier as observation only, observation-only ref witness;
- current production authority/adapter control flow and direct CPU/static tests.

Reported `67/67` unittest and static checks are auxiliary evidence only.

## Current blockers

### HIGH-1 — `publish_candidate(finalizer=None)` still returns a PENDING witness and preserves both refs without acceptance

**Location:** `tools/psm_wma/immutable_source_authority_root.py:~790` (`publish_candidate`)

After local/remote ref creation, post-publication observation and binding reverify, the current implementation creates a fresh `_AuthorityTerminalCell()` in PENDING state, constructs a `PublicationWitness`, then immediately returns it when `finalizer is None`.

No guard transition occurs, no terminal pointer swap to ACCEPTED occurs, and no private acceptance capability is consumed. Yet both refs remain created and no rollback runs.

This directly contradicts the approved v0.10 state contract:

- PENDING has `preserve_refs=False` and `witness_returnable=False`;
- successful public return is only legal after the accepted terminal transition;
- without accepted authority, refs must not be silently preserved as a successful publication.

This is not dead code. Existing tests explicitly depend on it: `test_capability_copy_and_replay_fail`, `test_all_typed_boundaries_reject_copy_and_pickle`, and `test_verifier_mapping_enters_real_collection_executor` call `publish_candidate(...)` without a finalizer and treat the returned witness / persisted refs as valid success. The last test then passes the binding mapping into the collection executor, proving the bypass is still an intended authority path in the test contract.

**Exact acceptance:** either reject `finalizer=None` before any ref mutation, or route that path through the exact approved terminal acceptance protocol. No public `PublicationWitness` may return and no candidate refs may remain preserved while the shared terminal cell is PENDING. Update all direct tests so no downstream authority/collection flow is authorized from a PENDING publication.

### HIGH-2 — the approved private `AcceptedPass` capability is absent from the implementation

**Location:** `tools/psm_wma/immutable_source_authority_root.py` around `_AuthorityTerminalCell`, `PublicationWitness`, `EvidenceCommit`

v0.10 explicitly retains the v0.8 private capability contract: an authority-private, non-copyable/non-pickle/replay-safe `AcceptedPass` exists inside the transaction, is bound before commit, never escapes the authority dispatch, and its internal consume is part of the success protocol.

The implementation defines no `AcceptedPass` class/object at all. Acceptance is reduced to `EvidenceCommit.committed -> terminal.state.accepted`, and tests contain no private-capability construction/copy/pickle/replay/activation-boundary checks.

That silently removes one of the approved design's authority boundaries rather than implementing it. The design approval did not authorize optimizing away the capability.

**Exact acceptance:** implement the private opaque `AcceptedPass` (or return to the design Gate and explicitly supersede it). It must share the exact terminal cell, be pre-bound to the exact activation/witness/candidate/binding/evidence/ref witness, reject construction/copy/pickle/replay, never escape authority dispatch, and have the frozen total internal consume/check semantics before `PublicationWitness` becomes returnable.

### HIGH-3 — `AuthorityTerminalState` is not immutable, so the claimed single pointer-swap commit is not mechanically true

**Location:** `tools/psm_wma/immutable_source_authority_root.py` class `_AuthorityTerminalState`

The approved design requires immutable PENDING/ACCEPTED state objects and one semantic write: the cell pointer replacement.

Current `_AuthorityTerminalState` is a normal class with writable `__slots__`. The global `_PENDING_TERMINAL_STATE` and `_ACCEPTED_TERMINAL_STATE` objects can be modified in place, e.g. their `accepted`, `rollback_enabled`, `preserve_refs`, or `witness_returnable` fields can be reassigned. Because every transaction shares these global objects, an in-place mutation changes terminal semantics across multiple cells without any `cell.state = ACCEPTED` pointer transition.

That reintroduces exactly the multi-field/split-state class the v0.9/v0.10 design eliminated.

**Exact acceptance:** make terminal states mechanically immutable (for example a frozen dataclass, `NamedTuple`, or equivalent object whose fields cannot be reassigned), and add direct negatives proving PENDING/ACCEPTED members cannot be mutated. All semantic authority changes must be possible only through the single cell reference replacement.

### HIGH-4 — the required A/B/C crash/restart fail-stop implementation and acceptance matrix are missing

**Locations:** `tools/psm_wma/immutable_source_authority_root.py`, `tools/psm_wma/materialize_immutable_source_authority_root.py`, and direct tests

v0.10 retains the approved A/B/C crash contract:

- A: guard visible / PENDING, existing fail-closed lease rules;
- B: guard absent + final evidence + PENDING, deterministic permanent fail-stop;
- C: guard absent + final evidence + ACCEPTED, process loss still permanent fail-stop;
- B/C cannot be reconstructed as accepted from pathname/evidence/refs;
- tests must inject failures around guard transition and terminal swap and prove only PENDING or ACCEPTED is observable.

The submitted implementation adds one new post-final-observation ref-drift regression but does not implement this crash/restart contract. The adapter preflight still only performs the generic `evidence destination 必须为fresh absent absolute path` rejection. There is no exact A/B/C restart classifier/result, no B/C recovery-Gate handoff, no process-loss fixture, and no required boundary injection matrix around guard-success/pointer-swap.

The reported suite increased from 66 to 67 tests, consistent with the single new drift test; it does not supply the frozen v0.10 crash acceptance evidence.

**Exact acceptance:** implement and directly test the approved restart/fail-stop semantics within the frozen four-file scope. Tests must cover A/B/C durable combinations, guard-transition success followed by pre-swap interruption, post-swap interruption, ordinary/custom/`BaseException` boundaries, and prove B/C can never auto-retry/auto-close/train or reconstruct acceptance from evidence/refs/path observation. Crash-window A must also fail closed on same-candidate foreign refs rather than infer ownership from equality.

## Preserved closure

The submitted code does correctly move `EvidenceCommit.committed` onto a shared terminal cell and implements the approved observation-only historical ref behavior in the added post-observation remote-drift regression. Those are real improvements, but they are insufficient for implementation closure because the bypass/capability/immutability/crash contracts above remain open.

## Blocker summary

- production/contract blockers: `4 HIGH`
- total blockers: `4 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:790)`

This verdict binds only the exact formal pair `885b94fe8ed4c859014410dd7f53abb4550f3dc1 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains strictly within the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. This verdict does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
