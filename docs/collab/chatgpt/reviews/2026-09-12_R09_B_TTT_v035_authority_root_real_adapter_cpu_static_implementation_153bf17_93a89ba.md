# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `153bf17b3755b20296e69d2f5790becd8520875d`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `8879742c4ea99bf2676903d4085a77aee91cd4e1`; child/Gitlink is unchanged.

The formal root is reachable. Its tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, exact SHA `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed incrementally against:

- approved real-adapter design chain v0.1-v0.6;
- prior exact-pair ChatGPT review `8879742... / 93a89ba...`;
- cumulative remediation from `8879742...` to current formal root;
- current authority/adapter production code and direct temporary CPU/static tests.

Reported `61/61` tests and static checks are auxiliary evidence only.

## Prior blocker closure status

The prior single HIGH was the identity-check-to-pathname-unlink TOCTOU at guard/cleanup deletion boundaries.

The current remediation is a meaningful improvement:

- direct pathname `lstat -> unlink` has been replaced by `_unlink_exact_regular()`;
- the helper moves the current pathname into a private same-directory parking directory, then re-checks the parked object's `(st_dev, st_ino)` before deleting it;
- both `EvidenceCommit.consume_by_unlink()` and adapter cleanup reuse that helper;
- new tests cover replacement immediately before handoff and record mutation after seal.

However the frozen PASS linearization contract is still not satisfied; see the remaining HIGH below.

## Current blocker

### HIGH-1 — private parking removes the public `.pending` guard before identity handoff is proven/committed, so PASS can become verifier-visible and later roll back

**Location:** `tools/psm_wma/immutable_source_authority_root.py:77` (`_unlink_exact_regular`) and `EvidenceCommit.consume_by_unlink()`

The new helper currently performs:

1. `lstat(public_path)` and compare `(dev, ino)`;
2. create a private parking directory;
3. `rename(public_path, parking/owned)`;
4. `lstat(parking/owned)` and re-check identity;
5. unlink the parked object;
6. return `True`; caller then sets `commit._committed = True`.

For ordinary cleanup this is safer than direct pathname unlink, because the helper does not delete a raced foreign replacement before re-checking the parked inode.

For the **PASS guard**, however, the public `.pending` pathname has special frozen semantics: verifier acceptance is exactly gated on that pathname being absent. Moving the guard away with `rename()` therefore makes PASS verifier-visible immediately at step 3 — before the parked object has been re-verified, before it has been deleted, before the helper returns, and before `EvidenceCommit.committed=True`.

This creates two reachable violations.

#### A. Correct guard is moved, but a later handoff step fails

If the owned guard is successfully renamed to parking, the public guard becomes absent and a concurrent verifier may accept the final PASS. After that point `parked.lstat()` or `unlink(parked)` can still fail. That exception remains pre-commit from the authority module's point of view, so `publish_candidate()` can enter rollback while PASS was already externally verifier-visible.

That violates the frozen invariant:

`accepted PASS visible <=> exact EvidenceCommit committed <=> exact candidate refs preserved`.

#### B. A foreign replacement is moved during the lstat→rename race

If a foreign object replaces the guard after the initial `lstat()` but before `rename()`, the rename moves that foreign object out of the public `.pending` pathname. Even though the subsequent parked-identity check detects the mismatch and tries to restore/fail-stop, there is an interval where the public guard is absent and PASS is verifier-visible while the exact commit remains uncommitted and may subsequently roll refs back.

The current adversarial test injects replacement immediately before `rename()` and checks that the foreign bytes are eventually restored. It does **not** test the frozen externally visible invariant during the handoff window. Preservation after restoration is insufficient because the verifier contract treats guard absence itself as acceptance.

There is also a second race after a correct rename: once the owned guard has been moved to parking, another actor can create a new foreign `.pending` at the original path. The helper can still delete the parked owned guard and return `True`, after which the caller marks the commit committed while a `.pending` guard exists again, making the PASS non-acceptable to the verifier. That breaks the reverse direction of the same invariant.

**Violated frozen contract:** v0.4/v0.5 define guard removal as the unique PASS linearization point. No operation may make the public guard absent before the transaction is irrevocably committed, and no fallible operation that can enter rollback may occur after PASS becomes verifier-visible.

**Exact acceptance:** replace the parking protocol, or redefine it with a verifier-coupled mechanism, so that:

1. the public `.pending` guard remains verifier-visible until the single authority-owned commit transition;
2. the exact object identity is proven before that transition;
3. once the public guard becomes absent, `EvidenceCommit.committed` is already irrevocably true and no subsequent exception can enter ref rollback;
4. no raced foreign guard can be moved, deleted, overwritten, or leave `committed=True` while `.pending` exists;
5. add direct adversarial tests that run a verifier observation at the handoff boundary, including:
   - correct guard moved + injected parked-lstat/unlink failure;
   - foreign replacement between identity check and handoff;
   - foreign `.pending` creation immediately after handoff but before helper return;
   and mechanically prove `verify_evidence_path()` can never accept before commit and can never reject solely because a guard reappeared after a reported successful commit.

A shared directory lock/transaction primitive honored by both writer and verifier, or an equivalent exact-object atomic commit mechanism, is acceptable. A temporary rename-away of the public guard followed by further fallible work is not.

## Closed findings retained

The current pair retains the previous closures:

- activation lifetime prevents stale retained capability use across transactions;
- authority-owned final ref recheck is performed inside `consume_by_unlink()` before guard transition;
- verify failure retains prepared candidate;
- bad input/request preflight produces terminal Evidence-v1;
- cleanup uncertainty can produce `ROLLBACK_INCOMPLETE / EVIDENCE_CLEANUP_INCOMPLETE`;
- CAS ownership and deterministic metadata fixes remain intact.

## Blocker summary

- production/contract blockers: `1 HIGH`
- total blockers: `1 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:77)`

This verdict binds only the exact formal pair `153bf17b3755b20296e69d2f5790becd8520875d` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same four-file temporary CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
