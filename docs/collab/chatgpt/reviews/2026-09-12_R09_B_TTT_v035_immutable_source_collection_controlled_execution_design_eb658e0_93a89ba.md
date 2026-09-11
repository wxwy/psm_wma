# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution Evidence remediation

**Date:** 2026-09-12  
**Formal root:** `eb658e0b4f7f006a20ba8a7aca9102d5cc64cb15`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`.
- Independently verified formal root `eb658e0b4f7f006a20ba8a7aca9102d5cc64cb15` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental base is the prior rejected evidence pair `fc0199178afd547e706f33e38588b50356a448e9` / same child.
- Incremental technical change is one evidence-schema line: collection/receipt failure null-record semantics plus early-stage empty/null placeholders. No executor implementation, authority-root materialization, source I/O, collection mutation, publication, GPU or training action is authorized or reviewed here.

## 2. Positive remediation

- The prior collection/receipt null-record key-set mismatch is locally corrected: collection now has the exact four-key null record `{revision:null,tree_native_oid:null,parent_revision:null,delta_paths:[]}`, while receipt retains the exact five-key null record including `blob_native_oid:null`.
- Early failure no longer requires fake source-entry digests: the remediation explicitly allows `source_entries=[]` and null handoff/candidate values instead of fabricated hashes.
- The formal Gitlink remains unchanged and exact.

## 3. Findings

### HIGH-1 — Evidence — branch-specific execution records still violate the declared common exact key set

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:15`

The schema declares the common nested **exact** execution keys as `{approval_formal_root,command_argv,interpreter}`. It then requires PASS to add `phase="complete"` and FAIL to add both `phase` and `failure_code`. Because the same document says unknown/extra fields are invalid, neither PASS nor FAIL has a unique legal `execution` object under the stated exact-key contract.

The null-record change does not touch this contradiction.

**Acceptance:** freeze branch-specific exact execution key sets, for example PASS exact `{approval_formal_root,command_argv,interpreter,phase}` and FAIL exact `{approval_formal_root,command_argv,interpreter,phase,failure_code}`, with exact types/value rules; or move `phase`/`failure_code` into one common exact record with explicit PASS/FAIL null/value semantics. Do not rely on “另含” additions to a previously declared exact key set.

### HIGH-2 — Evidence — early-stage FAIL semantics remain incomplete and conflict with common type/cardinality rules

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:29`

The common schema still requires `source_entries` to be nonempty and globally requires SHA fields to be 64-hex and boolean fields to be JSON booleans. The FAIL branch then permits `source_entries=[]` and all-null `handoff` / `candidates`, directly conflicting with those common rules unless an explicit branch override is frozen.

More importantly, failures can occur at the fixed ordering's early stages (`tool identity`, `environment`, `authority`, `lineage`) before downstream records exist. The remediation defines null handling only for source entries, handoff, candidates, collection and receipt. It does not define exact stage-aware null/SKIPPED records for later `environment`/`authority`/`lineage`/`post_checks`/`push_publication`/`rollback` fields when those phases were never reached. A compliant implementation would still have to invent values, use false placeholders that conflate FAIL with SKIPPED, or violate the declared field types.

**Acceptance:** freeze one coherent stage-aware FAIL representation across the entire fixed check order. Either define exact PASS/FAIL/SKIPPED check records with first-failure semantics and downstream SKIPPED entries, or define branch-specific exact null records/types for every nested section that may be unreached. Explicitly state which common cardinality/type rules are overridden on FAIL (`source_entries=[]`, nullable SHA/boolean fields) and forbid fabricated placeholder digests/booleans. After the first failure, later stages must have one deterministic representation.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:15)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **2**.

## 5. Scope

The earlier executor implementation/source-identity progression and authority-root materialization/binding remediation remain closed and are not reopened by this review. This verdict does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Remediation remains docs-only for this Gate.
