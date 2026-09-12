# ChatGPT Review — Authority Root PASS Linearization CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `8534ae8d5a0979a6dd7e90cedf45f6ad33a14ae5`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

The formal root is reachable (`fix: close authority pass lifecycle recovery gaps`). Its exact tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact child `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

This is a fresh incremental remediation review against prior ChatGPT review `bc40191f0e80f98201774cce8a1b551fa2343128 / 93a89ba...` and approved PASS-linearization design v0.10. Reported `74/74` CPU tests and static checks are auxiliary evidence only.

## Prior blocker closure status

### Prior HIGH-1 — callback-visible terminal cell: PARTIALLY CLOSED

The mutable `_AuthorityTerminalCell` is no longer stored directly on `PublicationWitness` / `EvidenceCommit`; state values are frozen and the cell mutator is token-gated. However callback-visible objects still expose a writable `_terminal_key`, and accepted terminal entries remain reachable in the module registry. This permits stale accepted-cell replay; see HIGH-1.

### Prior HIGH-2 — `AcceptedPass` missing complete evidence/ref binding: PARTIALLY CLOSED

`_AcceptedPass.bind(...)` now records candidate revision, binding digest, sealed evidence identity/digest, record digest, and the final local/remote exact-candidate observation. This is substantial progress. However the capability itself is still callback-visible and mutable/rewriteable, so the frozen authority-private / replay-safe capability contract is not mechanically enforced; see HIGH-2.

### Prior HIGH-3 — B-window/restart fail-stop: PARTIALLY CLOSED

The adapter now invokes `classify_pass_restart()` before ordinary fresh-path rejection, and `_accept_terminal()` failures after a successful guard transition are converted to `PASS_CLOSURE_RECOVERY_REQUIRED` without ordinary rollback. However a `BaseException` arising from the guard helper after the durable unlink has happened still escapes before the recovery boundary and falls back to precommit rollback; see HIGH-3.

## Current blockers

### HIGH-1 — writable terminal keys allow stale ACCEPTED-cell replay and bypass the current transaction's guard/evidence transition

**Location:** `tools/psm_wma/immutable_source_authority_root.py` classes `PublicationWitness` / `EvidenceCommit`, `_AUTHORITY_TERMINALS`, and `publish_candidate()`.

The direct mutable-cell reference was removed, but both callback-visible objects still carry `_terminal_key`, and those slot attributes remain writable. `_AUTHORITY_TERMINALS` retains accepted cells after successful transactions.

A concrete bypass remains:

1. complete transaction A normally and retain returned `PublicationWitness A`; its `_terminal_key` resolves to an ACCEPTED cell;
2. start transaction B and enter its finalizer;
3. assign `commit_B._terminal_key = witness_A._terminal_key`;
4. do not seal evidence and do not execute B's guard transition; return from the finalizer;
5. `publish_candidate()` checks only `commit_B.committed`, which now reads the stale ACCEPTED cell through the reassigned key, so B is treated as committed, its refs are preserved, and `PublicationWitness B` can return while B's own terminal remains PENDING and no B evidence/guard acceptance occurred.

This is the same authority-ownership class as the prior mutable-cell finding: the semantic authority is still replaceable from callback-controlled state, only indirectly via a registry key.

**Exact acceptance:** callback-visible witness/commit/pass objects must not permit terminal authority substitution. The terminal identity used by `commit.committed`, accepted-pass consume, and witness return eligibility must be immutable and exact-current-activation bound. Add a direct stale-key adversarial test: retain an ACCEPTED witness from activation A, attempt every callback-reachable terminal-key/cell substitution during activation B, and prove B cannot become committed, preserve refs, or return a witness without B's own real seal/final-ref/guard transition. Authority registry entries must not make a prior activation's ACCEPTED state reusable as current authority.

### HIGH-2 — `AcceptedPass` is still exposed to the finalizer and its authority identity fields are rewriteable, so stale/cross-activation capability replay is not mechanically rejected

**Location:** `tools/psm_wma/immutable_source_authority_root.py` class `_AcceptedPass` and `EvidenceCommit._accepted_pass`.

The new `bind(...)` covers the frozen evidence/ref facts, but the object is reachable from arbitrary finalizer code as `commit._accepted_pass`. Its `_witness`, `_activation`, `_terminal_key`, `_facts`, and `_token` slot attributes are ordinary writable Python attributes.

Therefore a retained stale capability can be rewritten toward a new activation before use. For example, finalizer code can retain `_accepted_pass` from activation A, then in activation B mutate its `_witness`, `_activation`, `_terminal_key`, and `_facts`/binding state before installing or using it. Current `bind(...)` does not prove the stored activation is exactly `witness._activation` or the stored terminal key is exactly `witness._terminal_key`; it only checks that the mutable stored activation is active and the passed witness is the mutable stored witness. That does not satisfy the retained v0.8/v0.10 requirement that replacing activation / replay / wrong authority identity be rejected.

The current test intentionally reads `commit._accepted_pass`, which also demonstrates the capability is not authority-private in practice.

**Exact acceptance:** keep `AcceptedPass` inaccessible as mutable callback state, or mechanically freeze all identity-bearing fields after authority construction. `bind()` / `consume()` must verify exact current activation identity, exact witness/candidate/binding, exact terminal identity, sealed evidence facts, and final-ref witness against authority-owned immutable bindings, not callback-rewriteable slots. Add stale-pass/cross-activation tests that retain capability A and try to reuse/rebind/rewrite it in activation B; all such attempts must fail before guard transition and must not affect B's terminal/ref outcome.

### HIGH-3 — a real guard-success-then-`BaseException` edge still enters ordinary rollback because the recovery boundary starts after `_commit_exact_guard()` returns

**Location:** `tools/psm_wma/immutable_source_authority_root.py` `EvidenceCommit.consume_by_unlink()`.

The remediation correctly handles exceptions from `_accept_terminal()` after the guard helper has returned. But the code still has this boundary:

```text
if not _commit_exact_guard(...):
    raise ...
try:
    _accept_terminal(...)
except BaseException:
    raise PASS_CLOSURE_RECOVERY_REQUIRED
```

A durable B state can occur *inside* `_commit_exact_guard()`: the helper can successfully unlink the parked guard and then receive `KeyboardInterrupt`, custom `BaseException`, cancellation, or equivalent process interruption before returning `True`. Such exceptions are not covered by the later `try:`. They escape to the finalizer; `publish_candidate()` sees the current terminal still PENDING and, because the callback error is not `PassClosureRecoveryRequired`, routes it through `_PreCommitFinalizerError` and ordinary `_rollback(...)`.

That violates the v0.10 B-window rule: once the guard transition is durably complete, any pre-swap interruption is permanent recovery-required and must never ordinary rollback refs.

The new `test_b_window_after_guard_transition_is_recovery_not_rollback` patches `_accept_terminal` to raise. It proves the narrower post-helper case, not the exact prior acceptance request whose hook must call the real `_commit_exact_guard()` successfully and then raise before the terminal transition.

**Exact acceptance:** make the guard-success boundary explicit and recovery-safe even when the exception originates at/after the durable mutation inside the helper. Add the exact adversarial hook requested previously: wrapper calls the real `_commit_exact_guard()` to completion (guard absent), then raises ordinary/custom/`BaseException` before the terminal swap. Prove the transaction surfaces stable `PASS_CLOSURE_RECOVERY_REQUIRED`, preserves refs, never invokes `_rollback`, and restart preflight routes the resulting guard-absent evidence to recovery. Preserve the already-correct A behavior for failures where the guard did not durably transition.

## Closed behavior retained

- `finalizer=None` is rejected before ref mutation;
- terminal state value objects are mechanically frozen;
- `AcceptedPass.bind(...)` now includes candidate/binding/evidence/final-ref facts;
- restart preflight now calls `classify_pass_restart()` before ordinary fresh-destination rejection;
- `_accept_terminal()` failure after successful helper return is recovery-required rather than rollback;
- observation-only post-final-observation ref drift behavior remains intact;
- formal tree/Gitlink and frozen four-file CPU/static scope remain unchanged.

## Blocker summary

- production/contract blockers: `3 HIGH`
- total blockers: `3 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:297)`

This verdict binds only the exact formal pair `8534ae8d5a0979a6dd7e90cedf45f6ad33a14ae5 / 93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains strictly within the already approved four root tooling/test files and temporary directory/local bare-remote CPU/static tests. This verdict does not authorize real source/candidate/ref/evidence operations, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
