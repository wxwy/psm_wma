# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Authority-Root Materialization/Binding Design

**Date:** 2026-09-12  
**Formal root:** `36b4e6bc3144a67d16d6c9684649e8939d181230`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-AUTHORITY-ROOT-MATERIALIZATION-BINDING-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and reviewed the current request independently of MM/Kimi.
- Independently verified formal root `36b4e6bc3144a67d16d6c9684649e8939d181230` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new docs-only Design Gate after the approved CPU/static executor pair `d281d6f3079602632000b1576c47fd4546de22e6` / same child.
- Review basis: current materialization/binding design, approved controlled-execution v0.2 authority contract, and the current approved executor authority seam in `tools/psm_wma/immutable_source_collection.py`.

## 2. Positive findings

The design correctly preserves the major authority and scope properties:

- materialization parent is the reviewed materialization formal root, not ambient `HEAD`, index/worktree, ledger or request head;
- authority commit is an exact two-path delta with full inherited `(path, mode, type, native OID)` preservation, including the child Gitlink;
- selection/config are canonical raw-byte authorities rather than caller mappings/digests/defaults;
- candidate objects are not accepted authority until independent committed-object relookup and the fixed one-shot authority ref CAS succeeds;
- verifier does not trust the materializer's self-reported tuple;
- pre-live failure is non-mutating and post-mutation uncertainty is fail-stop as `ROLLBACK_INCOMPLETE`;
- approval remains docs-only and does not authorize real source I/O, collection/receipt mutation, publication chain, child/runtime, GPU or training.

## 3. Current blocker

### HIGH-1 — Design / ABI — materialized seven-field tuple does not match the already-approved executor authority ABI

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_binding_design_v0.1.md:42` (seven-field tuple), with conflicting production seam at `tools/psm_wma/immutable_source_collection.py` `_authority_tree()` / `_bound_source_inputs()`.

The current design freezes the direct handoff tuple as:

`(authority_root_revision, selection_path, selection_blob_native_oid, selection_raw_sha256, config_path, config_blob_native_oid, config_raw_sha256)`

and states this is the unique authority delivered to the collection executor. Controlled-execution v0.2 uses the same conceptual first field name `authority_root_revision`.

However the already-approved current executor is fail-closed on an exact seven-key dictionary whose first key is `root_revision`; `_authority_tree()` also dereferences `authority["root_revision"]`. `_bound_source_inputs()` rejects any key-set drift before source open. There is no currently frozen adapter or later explicit authority that maps `authority_root_revision -> root_revision`.

Therefore a tuple produced exactly according to this design cannot be consumed by the approved executor: it will be rejected as `authority or lineage tuple drift`. This is a design-feasibility / frozen-ABI conflict, not merely naming style.

**Violated frozen contract:** authority-root materialization/binding must produce the exact authority accepted by the already-approved controlled collection executor, and any authority ABI migration must be explicit rather than delegated to an unreviewed caller/adapter.

**Why existing Evidence does not close it:** the CPU/static executor tests exercise the current `root_revision` ABI; they do not witness acceptance of the design's `authority_root_revision` tuple, and no reviewed bridge exists.

**Exact acceptance:** explicitly reconcile the ABI in the design. Either:

1. freeze the materialized executor-facing seven-key binding with first key `root_revision`, while explicitly stating that this is the serialization name of the conceptual `authority_root_revision` and that semantics are unchanged; update review/evidence wording consistently; or
2. define an explicit typed/fail-closed serialization bridge from `authority_root_revision` to `root_revision`, freeze its ownership/identity and exact pre-source-open behavior, and require it to be independently implemented/reviewed before real materialization/execution.

Do not leave the rename to caller code, request text, ledger, or an unfrozen future adapter.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_authority_root_materialization_binding_design_v0.1.md:42)`

Current blockers: **1 HIGH**.  
Design/ABI blockers: **1**.  
Implementation blockers: **0** (this Gate is docs-only).  
Evidence-only blockers: **0**.

## 5. Scope

This review does not reopen the already-approved CPU/static executor pair or its closed tree-entry / raw-selection-transport findings. It only requires the new materialization/binding design to produce an authority ABI that the approved executor can actually consume.

No real authority-root materialization, source I/O/hash, collection/receipt/source-evidence mutation, publication/root audit, child/runtime modification, CUDA/GPU, `torchrun`, forward/backward, optimizer/scheduler/scaler step, training, evaluation, inference or LIBERO4IN1 is authorized.