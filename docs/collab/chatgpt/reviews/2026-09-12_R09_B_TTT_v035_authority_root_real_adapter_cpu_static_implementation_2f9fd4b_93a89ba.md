# ChatGPT Review — Authority Root Real Adapter CPU/static Implementation Remediation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-REAL-ADAPTER-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the formal root changed from `64db875135addac644c96d0028ab5c08a1dddf54`; the child is unchanged.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. The child commit is independently reachable in `wxwy/cosmos-framework`.

## Review basis

Reviewed against the approved real-adapter design chain v0.1-v0.6, the prior exact-pair ChatGPT review for `64db875... / 93a89ba...`, current production source, and current temporary CPU/static tests. The reported `47/47` unittest, `py_compile`, Ruff, and `git diff --check` are auxiliary evidence only.

## Prior blocker closure status

The remediation materially closes three of the four previous blockers:

1. **Prior CLI/evidence-transaction bypass: CLOSED for PASS path.** `run_authority_cli()` now supplies a finalizer to `publish_candidate()`, builds PASS evidence, writes it through `write_pending_evidence()`, and the subprocess CLI test requires accepted evidence plus both candidate refs.
2. **Prior no-owned ordinary-FAIL terminal gap: CLOSED.** Any publication-try ordinary `FAIL` now requires recovery entered and `rollback.complete=true`; `complete=true` still requires both fresh final observations absent.
3. **Prior loaded interpreter/module identity gap: CLOSED.** Preflight binds `sys.executable`, the executing adapter `__file__`, and loaded authority module `__file__` to the frozen identities; the test that calls a copied formal tree through an already-imported module is rejected pre-mutation.
4. **Prior `EvidenceCommit` guard/digest/activation blocker: PARTIALLY CLOSED.** The capability now carries witness activation plus concrete guard/evidence paths and a digest, and no-op callback sealing is removed. However the authority module still does not enforce the frozen same-activation / exact-guard-identity semantics strongly enough; see HIGH-1.

## Current blockers

### HIGH-1 — `EvidenceCommit` is not actually same-activation / exact-guard-identity bound, so a stale commit can expose PASS and make the current activation roll refs back

**Location:** `tools/psm_wma/immutable_source_authority_root.py` (`EvidenceCommit.seal_for_guard()` / `consume_by_unlink()`)

The capability stores `witness._activation`, but neither `seal_for_guard()` nor `consume_by_unlink()` checks that the commit being sealed/consumed is the exact commit issued for the current finalizer activation. The writer also accepts any object with the expected methods.

A concrete reachable split-brain remains:

1. activation A exposes its uncommitted `EvidenceCommit` to a finalizer that saves it externally, then fails and rolls back;
2. activation B reaches its finalizer;
3. B's finalizer calls `write_pending_evidence(..., stale_commit_from_A)`;
4. the stale A commit accepts B's guard/path/digest, unlinks B's guard, and marks itself committed;
5. B's own exact commit remains uncommitted, so `publish_candidate()` enters B's rollback path;
6. accepted PASS is now visible while B's authority refs are rolled back.

This directly violates the frozen invariant `guard unlink succeeded <=> exact EvidenceCommit for this activation committed <=> accepted PASS visible <=> refs preserved` and the v0.5 requirement that wrong/different-witness/replayed capability use fail before commit.

The guard binding is also path-based rather than identity-based: `seal_for_guard()` stores a `Path`, and `consume_by_unlink()` later unlinks whatever object currently occupies that path. A guard replacement between seal and consume can therefore unlink foreign state and still mark the commit committed. The stored evidence digest is only compared to the JSON's `evidence_sha256` field; the authority capability does not itself recompute/bind the exact verified record bytes.

**Exact acceptance:** make the writer/authority handshake carry an authority-verifiable opaque finalization token that is bound to the exact current activation/witness/commit, exact writer-owned guard identity, exact evidence-path identity and recomputed canonical record digest. Stale/different-activation commits must fail before guard removal; guard replacement must fail-stop without deleting foreign state; `committed=True` must be reachable only for the exact commit issued to that finalizer. Add direct stale-commit, different-witness, guard-replacement and altered-record negatives.

### HIGH-2 — PASS evidence hard-codes post-publication ref facts and does not re-observe the fixed refs at the evidence commit point

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`_pass_evidence_record()` / `run_authority_cli()` finalizer)

`publish_candidate()` performs its fresh post-CAS observations before entering the finalizer. `_pass_evidence_record()` then serializes `local/remote == candidate`, all six publication bits true and `committed_binding_reverified=true` as constants. Neither the finalizer nor `write_pending_evidence()` re-observes the fixed local/remote refs immediately before seal/guard unlink.

A concurrent actor can therefore change a fixed ref after the authority module's earlier post-observation but before guard unlink. The finalizer will still write and commit PASS evidence claiming both refs are candidate, and post-commit control is intentionally forbidden from rolling refs back. The accepted invariant can therefore be false at the exact evidence linearization point.

v0.5 explicitly froze finalizer-side validation of the record/ref invariant before `seal_for_guard()` / guard unlink. Earlier authority post-observation is necessary but not sufficient under the already-recognized ref-race threat model.

**Exact acceptance:** in the actual finalizer, perform fresh local and remote observations immediately before the commit seal/unlink transition and require both exact candidate; bind those concrete observations into the evidence record. If either observation is foreign/unreadable/non-candidate, no accepted PASS may become visible and the existing pre-commit rollback / `ROLLBACK_INCOMPLETE` semantics must run. Add local and remote drift races injected after `publish_candidate()`'s initial post-observation but before evidence commit.

### HIGH-3 — evidence writer cleanup/publication is not ownership-safe under races and can overwrite/delete foreign evidence state

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`write_pending_evidence()` / `_cleanup_pending_evidence()`)

The writer checks final/guard absence before mutation, but does not carry per-path ownership witnesses. On any exception it calls `_cleanup_pending_evidence((temporary, path, guard), ...)`, which blindly unlinks all three paths if present.

Consequences:

- if another actor creates the guard after the initial absence check and before this activation's `O_EXCL` guard open, the open fails and cleanup can delete the foreign guard;
- if a stale/foreign `.tmp` already exists, the temporary `O_EXCL` open fails and cleanup can delete that foreign file;
- if another actor creates the final evidence path after the initial absence check, `os.replace(temporary, path)` can overwrite that foreign final path.

This violates the frozen writer contract that existing final/pending/temp state is never overwritten and the broader ownership rule that cleanup only removes state proven to belong to the current activation.

**Exact acceptance:** track ownership separately for guard/temp/final publication; cleanup may unlink only entries successfully created/published by this activation. Final publication must use a no-overwrite atomic primitive or an equivalent directory-FD protocol that proves the destination remained absent. Existing/raced final, guard or temp entries must be preserved. Add direct races for foreign guard before guard-open, foreign temp before temp-open and foreign final immediately before publication; prove no foreign byte/path is deleted or overwritten.

### HIGH-4 — the real CLI still has no producer for actual `FAIL` / `ROLLBACK_INCOMPLETE` transaction evidence

**Location:** `tools/psm_wma/materialize_immutable_source_authority_root.py` (`run_authority_cli()` / `main()`)

The actual CLI now produces PASS evidence, but every failing path still only raises an exception. There is no execution producer for the frozen failure records:

- preflight / prepare / verify failure;
- pre-publication / local-CAS / remote-CAS failure;
- post-publication / binding-reverify / evidence-write failure;
- rollback/final-proof failure yielding `ROLLBACK_INCOMPLETE`.

`verify_evidence_bytes()` can validate manually constructed test fixtures for those statuses, but `publish_candidate()` / `_rollback()` do not return a structured chronology and the CLI never serializes those actual events. Consequently the exact Evidence-v1 failure ABI is not an execution artifact; it is currently test-only schema code.

The approved design chain freezes `PASS | FAIL | ROLLBACK_INCOMPLETE` as transaction evidence and requires first-failure chronology plus per-endpoint rollback/final-observation facts. Closing this implementation with only a PASS producer would force the next execution request to invent another producer or accept unauditable failure outcomes.

**Exact acceptance:** expose enough authority-owned structured transaction outcome/witness data for the CLI to write a truthful canonical terminal record for every frozen phase, without duplicating private rollback logic. A normal failure must produce exact `FAIL`; incomplete/unprovable recovery must produce exact `ROLLBACK_INCOMPLETE` preserving the primary failure plus secondary rollback/final-proof code. Add end-to-end temporary CLI tests that induce at least preflight, no-owned local-CAS/foreign final proof, remote-CAS, evidence-write and rollback-incomplete outcomes and validate the produced records with the independent verifier.

## Non-blocking observations

- The prior CAS command-result / same-candidate ownership fix remains sound and should be retained.
- Deterministic commit metadata injection remains sound and should be retained.
- Actual loaded module/interpreter identity binding is a meaningful improvement and should be retained.
- The implementation still accepts an arbitrary `--remote` string and hashes it directly. Before any real execution request, the frozen request must use a credential-free remote identity; preferably the adapter should normalize/reject credential-bearing remote forms rather than relying on operator discipline.
- `argv_sha256` currently hashes the parsed argument tail while interpreter/module identity are bound separately; the exact execution request should make the command-token convention explicit so the digest has one canonical meaning.

## Blocker summary

- production/contract blockers: `4 HIGH`
- Evidence-only blockers: `0`
- total blockers: `4`

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:128)`

This verdict binds only the exact formal pair `2f9fd4bcaec0fd0ea0c6302aa69910e24ce9e378` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation remains in the same CPU/static implementation Gate and within the approved four root files plus ordinary collaboration bookkeeping. This verdict does **not** authorize real selection/config JSON creation, real candidate/ref/origin mutation, real source/collection I/O, child/runtime changes, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.
