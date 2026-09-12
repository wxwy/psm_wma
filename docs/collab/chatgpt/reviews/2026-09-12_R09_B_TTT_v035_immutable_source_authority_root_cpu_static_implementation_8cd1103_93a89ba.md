# ChatGPT Review — Immutable Source Authority Root synthetic CPU/static Implementation

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION`

## Exact formal pair

- root implementation SHA: `8cd1103deecc0720b7168e9e2b86b576e818b2bd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh implementation review. The preceding approved design authority is v0.2 formal root `ee0de157d337bc85bf3d8d1c9e4957c31aa03c07` with the same child/Gitlink. MM/Kimi state is coordination information only and is not inherited as ChatGPT's conclusion.

The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Incremental review basis

Reviewed against:

- implementation-design v0.1 and explicit v0.2 supersession;
- prior ChatGPT design review on `ee0de157... / 93a89ba...`;
- the actual four implementation/test files in the formal tree;
- the existing collection executor seam, especially `_bound_source_inputs()` / `collect_synthetic()`;
- direct CPU/static tests, without treating the reported `41/41 PASS` count as sufficient Evidence by itself.

The implementation commit changes exactly the four approved production/test files plus root bookkeeping (`SESSION.md`, `TODO.md`); no child change is present.

## What is correctly implemented

The following central v0.2 design requirements are materially present in production source:

- `AUTHORITY_REF` is fixed and not caller-overridable.
- The real collection executor path now observes local and remote authority refs before source open and requires both to equal the seven-key `root_revision`.
- Publication order is local expected-absent CAS followed by remote expected-absent CAS.
- Per-endpoint `local_created` / `remote_created` ownership witnesses exist.
- Rollback only attempts deletion for endpoints this activation reports creating, and deletion is conditional candidate -> absent.
- Foreign revisions are preserved rather than force-deleted.
- `AuthorityBinding` is one-shot, identity-bound, mapping-immutable, and rejects copy/pickle/reconstruction.
- Candidate tree/blob/raw-byte recomputation and exact seven-key mapping are present in `verify_candidate()`.

These facts close the previous *design* blockers, but the current implementation still has the blockers below.

## Current blockers

### HIGH-1 — exact structural authority is not independently provable at the prepare/verifier boundary

**Location:** `tools/psm_wma/immutable_source_authority_root.py:36-39,170-208` (`AuthorityGitTransaction`, `prepare_candidate`, `verify_candidate`)

**Root cause**

The frozen v0.1 contract requires an exact single-parent authority commit and direct rejection of formal-root Gitlink missing/mode/type/OID drift. It also requires `prepare_candidate()` itself to return only a candidate whose full tree delta is exactly the two fixed `100644/blob` paths with all inherited entries unchanged.

The current implementation does not make those predicates independently observable enough:

1. `AuthorityGitTransaction.parent(revision) -> str` collapses parent multiplicity. `verify_candidate()` compares that one string to the expected parent, so the production verifier cannot itself distinguish an exact one-parent commit from a multi-parent commit if an adapter returns only one parent.
2. The code already loads the full parent tree, but it never requires the parent `cosmos-framework` entry itself to be exactly `("160000", "commit", expected_child_gitlink)`. It instead trusts a separate `gitlink_at(parent) -> str`, which can hide missing/wrong mode/type structure.
3. `prepare_candidate()` calls `create_detached_commit()` and, before returning, checks only that the returned revision is a 40-hex value. It does not relookup the new object and prove exact parent count, two-path full-entry delta, fixed entry mode/type/OID/raw bytes, and inherited-entry equality as frozen for stage 1.

**Violated frozen contract**

Implementation design v0.1 §2-§4: detached single-parent candidate, exact two-path full-entry delta, complete inherited-entry preservation, and CPU matrix rejection of candidate zero/multi parent plus child Gitlink missing/mode/type/OID drift.

**Why current Evidence is insufficient**

`test_verifier_rejects_parent_delta_and_blob_drift` covers a wrong single parent, an extra path and a blob drift, but there is no direct zero-parent/multi-parent witness or Gitlink missing/mode/type witness. The fixture API itself cannot represent parent multiplicity through the production protocol.

**Exact acceptance**

Within this same Gate:

1. expose exact parent structure (`parents(revision)` or an explicitly fail-closed `single_parent(revision)` whose contract rejects zero/multiple parents) and require exactly one parent equal to `materialization_formal_root`;
2. directly require the formal-root full-tree entry `cosmos-framework == ("160000", "commit", expected_child_gitlink)`; do not rely only on an OID-returning side channel;
3. factor a shared exact candidate-structure validator and invoke it immediately after `create_detached_commit()` before `prepare_candidate()` returns, and again independently in `verify_candidate()`;
4. directly test zero parent, two parents, Gitlink missing, wrong mode, wrong type, wrong OID, inherited entry drift and fixed-path mode/type drift.

### HIGH-2 — rollback/postcheck fresh endpoint observations are short-circuited

**Location:** `tools/psm_wma/immutable_source_authority_root.py:228-255` (`_rollback`) and `publish_candidate()` ref checks

**Root cause**

v0.2 freezes fresh, independent local and remote observations after rollback and requires both endpoints to be proven absent before rollback success. The current `_rollback()` computes:

`complete = complete and git.local_ref(...) is None and git.remote_ref(...) is None`

If any prior cleanup step has already set `complete=False`, Python short-circuiting skips the final local/remote observations entirely. Similar `or`-chained pre-publication and post-CAS checks may skip the remote observation when the local predicate already fails.

The function still fail-stops in these cases, so this is not a foreign-ref deletion bug, but it does not implement the frozen two-endpoint observation/witness state machine and cannot provide the required final post-state observation when cleanup is already incomplete.

**Violated frozen contract**

Implementation design v0.2 §2-§3: both endpoints must be freshly observed; rollback completion must independently re-observe local and remote, with success only if both are proven absent.

**Why current Evidence is insufficient**

Race tests prove foreign refs are retained and that `ROLLBACK_INCOMPLETE` is raised, but they do not assert that both required final endpoint observations actually occur after an earlier cleanup failure or unreadable endpoint.

**Exact acceptance**

1. read local and remote observations into separate variables/calls before deciding each precheck/postcheck outcome; do not rely on boolean short-circuit to perform required observations;
2. after rollback attempts, independently attempt fresh local and remote observations regardless of the current `complete` flag, then aggregate the two observed states/errors with cleanup outcomes;
3. add deterministic event-order tests proving both final reads occur after delete failure, foreign drift and observation error, while foreign refs remain untouched and result remains `ROLLBACK_INCOMPLETE`.

### MEDIUM-3 — frozen non-serializable typed request/candidate/result contract is only implemented for `AuthorityBinding`

**Location:** `tools/psm_wma/immutable_source_authority_root.py:52-61,94-98`

**Root cause**

v0.1 §2 freezes non-serializable typed request/candidate/result objects. `AuthorityBinding` explicitly rejects copy/pickle/reconstruction, but `AuthorityRequest`, `AuthorityCandidate`, and `PublicationWitness` are ordinary top-level frozen dataclasses with no serialization guard and are therefore serializable/reconstructable by default.

**Violated frozen contract**

Implementation design v0.1 §2 typed/non-serializable object boundary.

**Why current Evidence is insufficient**

`test_capability_copy_and_replay_fail` tests only `AuthorityBinding`; it does not witness the other frozen typed boundaries.

**Exact acceptance**

Either implement the frozen non-serialization rule for the request/candidate/result types and add direct pickle/copy tests, or explicitly supersede that rule in a new design pair before implementation. Do not silently weaken the already-approved contract inside this implementation Gate.

### HIGH-4 — Evidence-only: no direct verifier-output -> real collection-executor compatibility witness

**Location:** `tools/psm_wma/test_immutable_source_authority_root.py::test_prepare_verify_and_publish`; `tools/psm_wma/test_immutable_source_collection.py::setUp/test_authority_fixed_ref_is_checked_before_source_open`

**Production blocker:** `0` for this item; this is Evidence-only.

**Root cause**

The frozen acceptance requires `AuthorityBinding.as_mapping()` from the actual verifier to be handed directly to the actual collection executor authority seam. The authority-root test only checks the mapping's key tuple, while collection tests manually construct `self.authority`. There is no direct witness that the object produced by `verify_candidate()` is accepted by `_bound_source_inputs()` / `collect_synthetic()` with the fixed refs and reaches the source-open sentinel.

There is likewise no direct end-to-end negative witness derived from that generated mapping for the required alias/dual-key/missing-key cases.

**Violated frozen contract**

Implementation design v0.1 §3 and CPU matrix item 8; v0.2 §1 direct compatibility requirement. This is also an Evidence quality issue: independently fabricated look-alike mappings do not prove the production producer -> consumer binding.

**Exact acceptance**

Add a direct CPU/static integration witness using the real production functions:

1. `prepare_candidate()` -> `verify_candidate()` -> exact `binding.as_mapping()`;
2. set the in-memory local/remote fixed refs to that candidate revision through the approved publication path/state;
3. pass the exact generated mapping directly into the real `_bound_source_inputs()` / `collect_synthetic()` path and prove the source-open sentinel is reached;
4. derive alias/dual-key/missing/extra-key negatives from that generated mapping and prove rejection before the sentinel with zero ref/source mutation.

## Blocker summary

- production/contract blockers: `3` (`2 HIGH`, `1 MEDIUM`)
- Evidence-only blockers: `1 HIGH`
- total blockers: `4`

The reported `41/41 PASS`, Ruff, `py_compile`, and `git diff --check` remain useful auxiliary evidence, but they do not close the direct contract gaps above.

## Final verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_authority_root.py:199)`

This verdict binds only the exact formal pair `8cd1103deecc0720b7168e9e2b86b576e818b2bd` / `93a89ba61306d840a008813f62f26a34d54850f4`.

Remediation stays in the same authority-root synthetic CPU/static implementation Gate. This verdict does **not** authorize real selection/config JSON creation, authority commit/ref creation, real source or remote I/O, collection/receipt/source-evidence/publication, child/runtime modification, checkpoint/data/cache I/O, CUDA/GPU, training, evaluation, inference, or LIBERO4IN1.