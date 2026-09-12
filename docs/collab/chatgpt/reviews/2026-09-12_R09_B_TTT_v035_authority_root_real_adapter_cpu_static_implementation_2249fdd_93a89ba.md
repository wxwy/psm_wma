# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh technical review of the corrected exact pair. The prior request containing `2249fdd3377f82d037d85b7f3ed854cf90472303` was a formal-target resolution failure only and is not reused as a technical verdict.

The corrected root resolves to commit `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49` (`fix: close authority failure evidence paths`), parent `0b77d2d11c39a179266d2c6de073eff94e1853dd`, tree `6cc036c120cf1c447a157310a2ed9e381d327326`. The formal tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against:

- the complete approved real-adapter design chain v0.1-v0.6;
- prior exact-pair review `2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378 / 93a89ba...`;
- cumulative production diff `2f9fd4b... -> 2249fdd3f750...`;
- current four-file implementation and temporary CPU/static tests.

Reported `53/53` unittest, `py_compile`, Ruff and `git diff --check` are auxiliary evidence only.

## Prior blocker closure status

The current implementation materially improves all four prior findings, but none is fully closed under the frozen exact transaction contract:

1. **Prior exact activation / guard identity blocker: PARTIALLY CLOSED.** `EvidenceCommit` now records witness activation, guard/evidence `(st_dev, st_ino)` identities and exact raw-record SHA-256, and rejects a stale commit when paired with a current witness. A stale *witness+commit pair* can still be reused against a later activation's writer state; see HIGH-1.
2. **Prior evidence-commit-point ref re-observation blocker: PARTIALLY CLOSED.** The CLI finalizer now reads both refs and `before_seal` re-observes them. The last ref observation still occurs before `seal_for_guard()` and `consume_by_unlink()` perform multiple fallible filesystem operations; see HIGH-2.
3. **Prior filesystem publication/cleanup ownership blocker: PARTIALLY CLOSED.** Guard/temp creation now uses `O_EXCL`, final publication uses hard-link no-overwrite, and cleanup is limited by ownership booleans. Cleanup still operates by pathname without verifying that the current object is the one this activation created; see HIGH-3.
4. **Prior real FAIL / ROLLBACK_INCOMPLETE producer blocker: PARTIALLY CLOSED.** Authority now exposes structured rollback/publication witnesses and the CLI emits several real publication-phase terminal records. Verify/pre-input and cleanup-uncertainty paths remain inconsistent; see HIGH-4.

## Current blockers

### HIGH-1 — stale exact witness+commit from activation A can still commit activation B's evidence and make B roll refs back after PASS becomes visible

**Location:** `tools/psm_wma/immutable_source_authority_root.py:195` (`EvidenceCommit.seal_for_guard` / `consume_by_unlink`)

The new `seal_for_guard(witness, guard, evidence_path, digest)` verifies that the supplied witness is *that commit's own witness*. That closes only the specific case tested by `test_stale_commit_cannot_seal_current_activation_guard`, where an old A commit is paired with B's current witness.

A stronger reachable path remains:

1. activation A's finalizer retains **both** A's `PublicationWitness` and A's uncommitted `EvidenceCommit`, then returns without committing; A rolls its refs back;
2. activation B reaches its finalizer and creates B's guard/final evidence;
3. B's finalizer invokes the writer with the retained A witness + A commit;
4. A's commit sees its own A witness, accepts B's guard/path/digest, unlinks B's guard and sets **A** committed;
5. B's exact commit remains uncommitted, so B's `publish_candidate()` enters its rollback path;
6. B's PASS is verifier-visible while B's refs are rolled back.

The capability stores activation identity but does not prove that its activation is the **currently executing finalizer activation**, and it does not cryptographically/structurally bind the evidence record's request/candidate/binding/revision to its own witness. The frozen invariant therefore remains breakable.

**Exact acceptance:** make the writer/authority finalization handshake authority-owned and exact-current-activation bound. The capability used to seal/unlink must be the exact commit issued to the current `publish_candidate()` finalizer, and the accepted record must bind the same request/candidate/binding/revision/activation. A retained A witness+A commit must fail before removing B's guard. Add a direct two-activation negative that retains both A objects and attempts to use them against B's guard/evidence.

### HIGH-2 — the last fixed-ref observation still precedes the actual guard-unlink linearization point by a race window

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`run_authority_cli` finalizer / `write_pending_evidence`)

The finalizer now:

- reads local and remote refs before building PASS;
- re-observes both refs in `before_seal()`;
- then calls `commit.seal_for_guard(...)`;
- then separately calls `commit.consume_by_unlink()`.

However `seal_for_guard()` performs `lstat`, `open`, full evidence read and JSON parse; `consume_by_unlink()` then performs another `lstat`, `open`, full evidence read and digest/identity verification before `os.unlink(guard)`.

A ref can drift **after `before_seal()` succeeds but before guard unlink**, producing accepted PASS with non-candidate ref state. Because guard unlink is the frozen commit point and post-commit rollback is forbidden, this remains a direct violation of `accepted PASS <=> exact candidate refs preserved`.

**Exact acceptance:** the authority-owned commit transition must include the final local+remote exact-candidate check at the linearization boundary. No unbounded/fallible work that permits ref drift may occur between the final ref check and guard unlink. An equivalent serialized/locked authority transition is acceptable, but the invariant must be mechanically true. Add local and remote drift injections after seal but immediately before consume/unlink and prove no PASS is accepted; the path must remain pre-commit and use frozen rollback / `ROLLBACK_INCOMPLETE` semantics.

### HIGH-3 — evidence cleanup uses ownership booleans but can still unlink a foreign replacement of a previously owned pathname

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`write_pending_evidence`, `write_failure_evidence`, `_cleanup_pending_evidence`)

The remediation correctly uses `O_EXCL` for guard/temp and `os.link(temp, final)` for no-overwrite publication. It also tracks `guard_owned`, `temporary_owned`, and `final_owned` booleans so a pre-existing foreign path is not cleaned.

But an ownership boolean proves only that this activation **once created an object at the pathname**. `_cleanup_pending_evidence()` later performs unconditional `Path.unlink()` by pathname. If another actor removes/replaces an owned guard/temp/final before cleanup runs, the boolean remains true and cleanup deletes the foreign replacement.

The same class of bug applies to `write_failure_evidence`: `owned=True` for the temp pathname is not an inode/object-identity witness.

**Exact acceptance:** track the exact object identity created/published by this activation (directory-FD + inode/dev or equivalent race-safe capability) and condition every cleanup delete on that exact identity. A changed/replaced pathname must be preserved and force fail-stop if cleanup cannot be proven. Add direct replacement-after-create races for guard, temp and final on PASS writer, plus temp/final on failure writer; prove foreign replacements are never deleted/overwritten.

### HIGH-4 — actual terminal failure evidence production is still incomplete and one verify path produces a record that its own verifier rejects

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`_no_mutation_failure_record`, `run_authority_cli`, `main`, `_publication_failure_record`)

The corrected implementation now produces real evidence for many publication failures, including pre-publication, remote-CAS, post-publication, binding-reverify, evidence-write and a real `ROLLBACK_INCOMPLETE` path. That is a substantial improvement.

But the terminal producer is still not closed:

1. **Verify failure is self-inconsistent.** `run_authority_cli()` catches `verify_candidate()` failure and raises `InvocationFailure("verify", ...)`. `main()` then calls `_no_mutation_failure_record()`, which always serializes an **empty candidate**. The frozen verifier explicitly requires `phase="verify"` to carry a **prepared** candidate. Therefore an actual verify failure causes `write_failure_evidence()` to reject the producer's own record instead of publishing valid verify FAIL evidence.
2. **Input/request preflight can fail before `invocation` exists.** `request_from_input_fds()` (regular-FD check, raw SHA check, canonical selection/config validation) runs before the `InvocationFailure` handling path and before `AuthorityAdapterInvocation` is constructed. Those real preflight failures therefore still exit with no terminal Evidence-v1. Existing drift tests assert nonzero/no refs but do not require a failure record.
3. **Evidence-cleanup uncertainty can disagree with the serialized status.** `publish_candidate()` special-cases `EvidenceCleanupIncomplete` to raise `RollbackIncomplete` even after ref rollback completed, because evidence cleanup itself is unprovable. But `PublicationFailure.rollback.complete` reflects only ref rollback; `_publication_failure_record()` derives `status` solely from `outcome.complete`. It can therefore serialize ordinary `FAIL` while the authority terminal outcome is `RollbackIncomplete`.

These are production semantics, not missing optional tests: the next execution-request Gate cannot reconstruct truthful terminal evidence after the fact.

**Exact acceptance:** preserve the exact reached candidate state in no-mutation failure outcomes (`verify` must serialize prepared candidate); define and implement a terminal evidence path for request/input preflight failures consistent with the frozen `preflight` row; and derive terminal status from the complete transaction/evidence cleanup state, not only ref rollback completeness. Add end-to-end temporary CLI tests for at least verify failure, bad input/raw/canonical preflight, and `EvidenceCleanupIncomplete`, and require the independently verified record status/phase to match the actual thrown terminal (`FAIL` vs `ROLLBACK_INCOMPLETE`).

## Non-blocking observations

- CAS command-result/porcelain ownership attribution remains sound and should be retained.
- deterministic detached-commit metadata remains explicit and stable.
- loaded interpreter/module identity binding remains a useful fail-closed check.
- before any real execution request, remote identity should be explicitly credential-free/normalized, and the exact argv hashing convention should be frozen unambiguously.

## Blocker summary

- production/contract blockers: `4 HIGH`
- total blockers: `4 HIGH`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:195)`

This verdict binds only the exact formal pair `2249fdd3f7503d7e4c2be89bdd102cb4daf5aa49` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same CPU/static implementation Gate and within the approved four root files plus ordinary collaboration bookkeeping. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
