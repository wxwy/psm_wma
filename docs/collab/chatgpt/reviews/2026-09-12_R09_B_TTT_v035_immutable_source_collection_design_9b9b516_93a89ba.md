# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Design v0.1

**Date:** 2026-09-12  
**Formal root:** `9b9b516132806369718361b0e1b7b54c15c0483d`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`.
- Independently verified formal root `9b9b516132806369718361b0e1b7b54c15c0483d` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Prerequisite Source-evidence Producer / Closure Design is approved at `1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95` / `93a89ba61306d840a008813f62f26a34d54850f4` with `APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE`.
- Incremental technical scope is docs-only: new immutable-source collection design plus root bookkeeping/decision files. No child/runtime change, real collection, source-evidence write, publication, audit, GPU or training action is authorized by this review.

## 2. Positive findings

- The collection-root -> separate receipt-root structure is non-circular.
- The receipt root is required to have the collection root as exact parent, and fixed paths/schema/digest constraints are explicit.
- Preflight/live-transaction rollback and `ROLLBACK_INCOMPLETE` semantics remain fail-closed.
- Gitlink/publication/checkpoint/cache/training residue are excluded from the staged set.
- Resolved canonical model config is persisted as a fixed root-owned artifact rather than caller-selected mapping.

## 3. Findings

### HIGH-1 — Design/Authority — this Gate rewrites already-approved downstream progression while claiming to reuse it unchanged

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_design_v0.1.md:13`

The design states that after collection/receipt closure the next design must be `SINGLE-GPU-SMOKE-DESIGN`, and that no further provenance Gate may be inserted. This directly conflicts with the already-approved Source-evidence Producer / Closure Design, which freezes the downstream sequence as: immutable-source collection design/execution/closure -> source-evidence controlled-write execution design -> `APPROVE_TO_WRITE_SOURCE_EVIDENCE` -> source-evidence record closure -> independent post-commit receipt closure/review -> publication materializer/verifier implementation design. The approved Root Publication Freeze Design further preserves controlled publication materialization and the later read-only root Gitlink source-audit before runtime/real-I/O/GPU progression.

The same new design also says there will be only one merged `IMMUTABLE-SOURCE-COLLECTION-CLOSURE` execution Gate and explicitly removes the separately approved `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN` stage. That is another progression rewrite of the inherited approved contract.

A user priority decision to reach GPU sooner can guide sequencing, but this design cannot both say it “reuses but does not rewrite” the approved contracts and silently delete their still-binding Gates.

**Acceptance:** either preserve the approved progression exactly, or open an explicit docs-only refreeze/supersession Gate whose sole purpose is to amend the previously approved source-evidence/publication progression, enumerate every superseded clause/Gate, preserve all authority invariants, and obtain independent approval before any abbreviated route is adopted. This immutable-source collection Gate itself must not unilaterally skip `IMMUTABLE-SOURCE-COLLECTION-EXECUTION-DESIGN`, source-evidence controlled write/receipt, publication materialization, or the read-only root source audit.

### HIGH-2 — Design/Authority — the collection values are still not derived from a frozen immutable-source input authority

Section 2 freezes a six-key collection artifact containing `immutable_source_identifier`, `source_manifest_sha256`, `source_input_sha256`, and `checkpoint_source_descriptor_sha256`, and Section 3 says preflight validates an “input immutable contract.” But no exact immutable input artifact(s), fixed path/schema, raw bytes, source-manifest/source-input descriptor schemas, or deterministic derivation chain is frozen for those four values.

Therefore a future executor can provide any self-consistent set of 64-hex values, write them into the collection artifact, and the receipt can successfully re-read/re-hash that artifact. The Git/receipt checks prove immutability of the committed values, not that they were derived from the intended approved checkpoint source.

**Acceptance:** freeze the machine-verifiable source-input authority before the controlled collection write. At minimum define exact root-owned/fixed-path artifact schemas and canonical bytes for the immutable source descriptor/manifest/source-input evidence, the deterministic computation of `immutable_source_identifier`, `source_manifest_sha256`, `source_input_sha256`, and `checkpoint_source_descriptor_sha256`, and how the collection closure independently recomputes each value from those reviewed bytes rather than accepting caller/environment labels or precomputed digests. If the real bytes cannot yet be read in this docs-only Gate, freeze the future artifact schemas/paths/derivation semantics now and keep actual collection execution in its own approved Gate.

### HIGH-3 — Design/Authority — exact checkpoint-source descriptor bytes are missing from the reviewed authority chain

The collection artifact and receipt bind only `checkpoint_source_descriptor_sha256`; they do not persist or bind the exact five-key `root_gitlink_checkpoint_source_descriptor_v1` canonical bytes/path/blob identity. The approved source-evidence/package contract later needs the exact `checkpoint_source_descriptor` object, not merely its digest, so the downstream package cannot be reconstructed solely from the reviewed collection/receipt authority.

The canonical model config correctly gets its own fixed artifact; the descriptor needs the same treatment or an equivalently exact non-circular binding.

**Acceptance:** add a fixed root-owned checkpoint-source-descriptor artifact (or equivalently embed and bind the exact canonical descriptor bytes in a reviewed artifact) with exact `root_gitlink_checkpoint_source_descriptor_v1` schema, fixed path, canonical raw bytes SHA-256 and tree/blob ownership. The receipt must bind its path/blob/digest, and downstream package generation must read/recompute that exact descriptor from the reviewed collection authority, never accept caller-supplied descriptor mappings.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_design_v0.1.md:13)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **3**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This verdict does not authorize real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Remediation should remain docs-only unless a separately approved Gate explicitly authorizes otherwise.
