# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-evidence Producer / Closure Design non-circular remediation

**Date:** 2026-09-12  
**Formal root:** `f3a423c39020081b3ff34128328792af166ba09a`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`, and verified this exact pair is the current formal request for the Gate.
- Independently verified formal root `f3a423c39020081b3ff34128328792af166ba09a` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is prior rejected pair `180038024ae2b4cc2e436bddafbcc01018087b0c` / `93a89ba61306d840a008813f62f26a34d54850f4` and its canonical review.
- The formal technical commit modifies only `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md`; child/runtime is unchanged. No real collection, write, publication, audit, I/O, GPU or training action is authorized.

## 2. Prior HIGH closure

### Prior HIGH — collection receipt self-reference: CLOSED

The design now uses a non-circular two-root model. A collection formal root is created first and does not contain a receipt naming its own SHA. A separate collection-receipt root must have that collection root as its exact parent and carries the fixed-path `immutable_source_collection_receipt_v1`. The receipt binds the collection root revision, reviewed artifact/config paths and schemas, blob OID and SHA-256 values, and the future producer may only derive record/config authority from the independently reviewed receipt-root identity. This closes the Git-commit self-reference defect.

### Prior HIGH — unowned `witness_blob_native_oid`: CLOSED in the new receipt schema

`witness_blob_native_oid` has been removed from `source_evidence_postcommit_closure_receipt_v1`, and the new paragraph defines the witness as derived-only canonical bytes/SHA-256 reconstructed from reviewed record/config/descriptor/package bindings. That is a valid non-circular direction and removes the prior requirement for an unowned witness Git blob OID.

## 3. Finding

### HIGH-1 — Design/Authority — Section 3 still simultaneously requires an external witness Git blob OID and forbids retaining/declaring one

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:69`

Immediately before the new post-commit receipt contract, the inherited witness paragraph still states that the witness raw-bytes SHA-256 **and Git blob OID must be externally recorded**. The next paragraph now states the opposite: the witness is **derived-only**, its canonical bytes/SHA-256 are reconstructed from reviewed bindings, and it does **not retain or declare a witness Git blob OID**.

Both sentences are binding text in the same section. A later implementation or closure review therefore has two incompatible authorities: persist/record a witness blob identity, or never create/retain one. This makes the witness closure non-unique even though the receipt schema itself has been corrected.

**Acceptance:** remove or supersede the stale Git-blob-OID requirement and freeze one exact model only. The simplest compatible model is the new derived-only contract: witness canonical bytes are deterministically rebuilt from the reviewed record/config/descriptor/package bindings; `input_witness_sha256` is recomputed from those bytes; no witness Git path/blob/OID exists or is accepted as authority. The post-commit receipt and all later materializer verification must use only that model. No child/runtime change or execution is required.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:69)`

Current blockers: **1 HIGH**.  
Design/Authority blockers: **1**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

No real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1 is authorized by this verdict. Remediation should remain docs-only for this Gate.
