# ChatGPT Review — Immutable Source Authority Root CPU/static Implementation Design v0.1

**Date:** 2026-09-12  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-CPU-STATIC-IMPLEMENTATION-DESIGN`

## Exact formal pair

- root design SHA: `c61f32f3a99688043f2dfdb3d69480e11b1811dd`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`

This is a fresh review because the root formal SHA changed from the previously reviewed `31819169c9430087f5e293cd1dce169ec055b371`; the child is unchanged. The formal root tree was independently checked: `cosmos-framework` is mode `160000`, type `commit`, and points exactly to `93a89ba61306d840a008813f62f26a34d54850f4`. That child commit is reachable in `wxwy/cosmos-framework`.

## Authority chain reviewed

- authority-root materialization/binding design v0.1;
- explicit ABI supersession v0.2, formal root `31819169c9430087f5e293cd1dce169ec055b371`, previously approved by ChatGPT;
- current implementation-design v0.1;
- actual approved collection executor seam in `tools/psm_wma/immutable_source_collection.py`, especially `_authority_tree()` and `_bound_source_inputs()`.

The v0.2 supersession changes only the executor-facing revision key to `root_revision`; all retained v0.1 parent/tree/ref/reverification requirements remain in force.

## Findings

### HIGH-1 — current implementation allowlist cannot satisfy the retained pre-source fixed-ref authority check

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_cpu_static_implementation_design_v0.1.md:16,54`; actual seam `tools/psm_wma/immutable_source_collection.py::_bound_source_inputs`

**Root cause**

The retained binding v0.1 contract requires the collection executor, before opening any source, to recompute the authority-root binding from Git objects **and** re-check the fixed authority ref against the approved authority revision (including remote relookup). The current production `_bound_source_inputs()` does recompute parent/tree/blob/raw-byte authority and the collection target lineage, but it has no fixed authority-ref local/remote observation at all. Its `GitTransaction` protocol likewise has no explicit authority-ref/remote-ref read method.

The new design does not close that gap. It limits changes to the new root tool/test plus, at most, public alias/rename of existing pure validators in the collection file, while its direct compatibility acceptance only requires the seven-key mapping to pass the present authority phase and reach the synthetic source-open sentinel. Consequently the future CPU implementation can satisfy every stated test while the actual executor still accepts an authority commit whose fixed authority ref is absent, wrong, or has drifted since publication.

**Violated frozen contract**

Authority-root materialization/binding design v0.1 §4 requires pre-source object-database recomputation plus fixed-ref remote relookup to the exact authority revision. v0.2 supersedes only the serialized key name (`root_revision`), not that ref requirement.

**Why current Evidence plan does not close it**

The proposed positive/negative seven-key ABI tests exercise the current seam, but the current seam never asks for the fixed authority ref. Reaching the source-open sentinel therefore cannot witness the retained ref predicate.

**Exact acceptance**

Within this same Gate, refreeze the implementation allowlist and direct compatibility contract so the actual executor path used by collection performs an explicit typed pre-source fixed-ref check, without a caller-side adapter. At minimum:

1. the fixed ref remains the non-overridable `refs/heads/authority/r09-b-ttt-v035-immutable-source-v1`;
2. the injected Git authority exposes explicit local and remote ref observation required by the executor seam;
3. immediately before source open, both observations must resolve exactly to `authority["root_revision"]` together with the already-frozen parent/tree/blob/raw-byte checks;
4. absent, wrong-target, local/remote disagreement, or observation failure must fail before the source-open sentinel with zero ref/source mutation;
5. add direct tests for PASS plus each of those negative cases through the real `_bound_source_inputs()` / `collect_synthetic()` path;
6. list every existing production/test file that must change in the implementation allowlist. A wrapper or request/ledger translation outside the executor seam is not acceptance.

### HIGH-2 — post-CAS rollback is not concurrency-safe enough to preserve ref ownership

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_cpu_static_implementation_design_v0.1.md:28,64-65`

**Root cause**

`publish_candidate()` is frozen only as “local/remote absent → expected-zero CAS → relookup → exact rollback to absent on failure.” The design does not freeze which local/remote endpoint is mutated first, what per-endpoint mutation witness proves this activation created the ref, or that rollback is itself a conditional compare-and-delete from the exact candidate revision.

That omission permits an unsafe implementation: this activation creates one endpoint, a concurrent writer subsequently moves that ref to another revision (or creates the other endpoint), and an unconditional “restore absent” rollback deletes the concurrent writer's ref. It also leaves the one-endpoint-success/other-endpoint-conflict case ambiguous.

**Violated frozen contract**

The retained v0.1 fixed-ref contract is expected-zero, fail-stop, non-force/non-overwrite and requires exact rollback proof. An exact rollback cannot erase a ref value that this activation no longer owns.

**Why current Evidence plan does not close it**

The matrix names CAS competition, post-CAS drift and rollback, but without an ownership-aware state machine those tests can pass using an unconditional delete-to-absent fixture that would be invalid for a real adapter.

**Exact acceptance**

Refreeze publication/rollback semantics before implementation:

1. define the local and remote publication state machine and mutation order explicitly;
2. each creation is an expected-absent → exact-candidate CAS and records a per-endpoint success witness owned by this activation;
3. rollback may mutate only an endpoint this activation proved it created, and only via conditional exact-candidate → absent compare-and-delete;
4. if an endpoint currently contains any foreign revision, is unreadable, or ownership/rollback cannot be proven, do not delete it; terminate `ROLLBACK_INCOMPLETE` with no auto-retry;
5. rollback success requires fresh local and remote re-observation proving the required absent state;
6. CPU/static tests must inject races after the first successful CAS, between CAS and postcheck, and during rollback, including the one-endpoint-success/other-endpoint-conflict case, and prove foreign refs are never removed.

## Non-blocking note

The design's reuse requirement should be implemented carefully: current selection validation is embedded inside `_bound_source_inputs()` rather than exposed as a standalone pure validator. If shared validation is factored out to avoid duplicated weaker rules, that production/test delta must be included explicitly in the implementation allowlist and preserve the existing executor behavior.

## Current blocker count

`2` (both HIGH, design/production-feasibility)

## Final verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_cpu_static_implementation_design_v0.1.md:54)`

This verdict binds only the exact formal pair above. It does not authorize authority-root implementation, real JSON creation, authority commit/ref creation, real source/remote I/O, collection/receipt/source-evidence/publication, child/runtime changes, GPU, or training.
