# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-evidence Producer / Closure Design authority remediation

**Date:** 2026-09-12  
**Formal root:** `180038024ae2b4cc2e436bddafbcc01018087b0c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`.
- Independently verified formal root `180038024ae2b4cc2e436bddafbcc01018087b0c` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is prior formal pair `08b069e8b0cff7da7018b74d50e76f42fedd8514` / `93a89ba61306d840a008813f62f26a34d54850f4` and canonical review `docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_source_evidence_producer_closure_design_08b069e_93a89ba.md`.
- The remediation is docs-only. The child is unchanged. No real collection, record/package/witness write, publication, real source audit, checkpoint/data/cache I/O, GPU or training action is authorized or reviewed here.

## 2. Prior HIGH closure

### Prior HIGH-1 — missing collection Gate progression / reconstructable binding

**Partially closed.** The sequence now explicitly inserts independent `IMMUTABLE-SOURCE-COLLECTION-DESIGN`, `...EXECUTION-DESIGN`, and `...CLOSURE` Gates before any source-evidence controlled write, and introduces a fixed collection-receipt path plus a detailed receipt mapping.

However the new collection receipt is itself circular as currently specified; see HIGH-1 below.

### Prior HIGH-2 — `canonical_model_config` had no formal authority

**Closed in substance.** The design now requires `canonical_model_config` to be read only from the collection receipt's bound config artifact path/raw canonical bytes, with recomputed `canonical_model_config_artifact_sha256` and `canonical_model_config_sha256`, and forbids caller/environment/working-tree selection.

### Prior HIGH-3 — no post-commit package/witness closure receipt

**Partially closed.** A separate next-root `source_evidence_postcommit_closure_receipt_v1` is now defined and correctly avoids putting the receipt into the source-evidence formal root itself. It binds the source-evidence formal root, record identity/digest, package/witness digests, and config/descriptor digests.

The witness blob OID remains unanchored to a fixed path/tree lookup; see HIGH-2 below.

## 3. Findings

### HIGH-1 — Design/Authority — `immutable_source_collection_receipt_v1` is self-referential and therefore cannot be materialized as specified

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:35`

The remediation says the collection closure's unique artifact path is `docs/build/PSM-WMA_immutable_source_collection_receipt_v1.json`; the receipt itself contains `collection_formal_root_revision`; and that formal revision plus reachable blob OID/digests must be recomputed from the **closure formal root** tree/blob lookup.

If that receipt lives in the closure formal root whose SHA it contains, the commit is circular: the receipt bytes determine the tree, the tree determines the commit SHA, yet those same receipt bytes must already contain that final commit SHA. A normal Git commit cannot satisfy this fixed point contract.

This is the same class of circularity the design correctly avoided for the post-commit source-evidence receipt by placing it in a *next independent receipt root*. The collection authority needs the same treatment.

In addition, the collection receipt lists `collection_artifact_path`, `collection_artifact_schema`, `collection_artifact_blob_native_oid`, `canonical_model_config_artifact_path`, and related digests but does not freeze their exact type/value semantics at this level. Those may be frozen by the independent collection Gate, but the closure contract must state that they are exact reviewed outputs of the pre-receipt collection formal root and are not caller-selectable.

**Acceptance:** make the collection provenance non-circular. For example:

1. first create/close a collection formal root containing the fixed collection/config evidence artifacts but no receipt that names its own SHA;
2. then create a separate collection-receipt root whose parent is exactly that collection formal root and whose fixed-path receipt may safely contain `collection_formal_root_revision` plus exact artifact paths/schemas/blob OIDs/raw SHA-256 values;
3. bind the receipt-root formal revision/path/blob identity by independent review;
4. future source-evidence controlled write may accept only that reviewed receipt-root identity and must derive all record/config authority from it;
5. freeze exact types/constraints for formal revision (40 lowercase Git SHA-1), blob OIDs (40 lowercase Git SHA-1), paths/schemas (exact reviewed strings), and SHA-256 fields (64 lowercase hex).

An equivalent non-circular two-root receipt model is acceptable. Do not solve this by omitting formal-root binding or by letting callers provide the receipt values.

### HIGH-2 — Design/Authority — post-commit `witness_blob_native_oid` has no fixed path/tree ownership, so it is not independently recomputable

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:68`

The post-commit receipt contains `witness_blob_native_oid` and says all revision/OID/raw-digest values are recomputed through the receipt-root tree and parent-root tree. But no fixed witness artifact path is defined, and the receipt contains no `witness_path`. A Git tree lookup resolves a blob OID through a path; without a fixed path there is no unique tree-owned witness blob from which `witness_blob_native_oid` can be independently recomputed.

The witness SHA-256 itself can be deterministically recomputed from the frozen package/witness fields, so retaining a Git blob OID is optional. But if a Git blob OID is part of the authority receipt, its tree ownership must be exact and non-caller-selectable.

**Acceptance:** choose one exact model and freeze it:

- **Persisted witness model:** define one fixed witness path in the independent receipt root (or add an exact `witness_path` field whose value is frozen by design), require that path's tree entry be a normal blob, recompute the blob OID/raw bytes/SHA-256 from the receipt-root tree, and bind `input_witness_sha256` to those exact bytes; or
- **Derived-only witness model:** remove `witness_blob_native_oid` entirely and specify that the witness canonical bytes/SHA-256 are deterministically reconstructed from the reviewed source-evidence formal root/record/config/descriptor/package bindings, with no persisted witness blob claim.

In either model, the next publication materializer must receive only the reviewed receipt-root formal revision/fixed receipt path/blob identity, never caller-selected package/witness material.

## 4. Positive findings

- The independent collection Gate sequence is now explicit and precedes source-evidence controlled write.
- The resolved `canonical_model_config` is now anchored to collection authority rather than a schema-valid caller mapping.
- The source-evidence post-commit receipt is correctly placed in a separate next root, avoiding self-reference to the source-evidence formal root.
- The fixed six-key source-evidence record schema, staged-set Gitlink/publication prohibitions, isolated preflight, rollback and `ROLLBACK_INCOMPLETE` semantics remain aligned with the approved Root Publication Freeze Design.
- Scope remains docs-only.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:35)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 6. Scope

No real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source audit, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1 is authorized by this verdict. Remediation should remain docs-only for this Gate.