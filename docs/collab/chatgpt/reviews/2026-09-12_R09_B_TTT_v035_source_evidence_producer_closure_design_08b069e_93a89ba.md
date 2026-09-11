# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-evidence Producer / Closure Design v0.1

**Date:** 2026-09-12  
**Formal root:** `08b069e8b0cff7da7018b74d50e76f42fedd8514`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`.
- Independently verified formal root `08b069e8b0cff7da7018b74d50e76f42fedd8514` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- The prerequisite Root Publication Freeze Design is closed at formal pair `c6be81ef0b9b9937987c53bb84524131019b5d9a` / `93a89ba61306d840a008813f62f26a34d54850f4` with `APPROVE_TO_DESIGN_R09_B_TTT_V035_ROOT_PUBLICATION_FREEZE`.
- This submission is docs-only. No source-evidence record/package/witness is created, no real checkpoint/manifest/data/cache is read, and no publication/audit/GPU/training action is authorized.

## 2. Findings

### HIGH-1 — Design/Authority — required immutable collection authority exists in prose but has no executable Gate path or reconstructable formal binding

The design requires all four source-evidence record digest fields to come from an independent, already-approved immutable source-evidence collection Gate formal output, and says the collection formal root must be recoverable from the future closure formal root. However the frozen sequence goes directly from this design to a `source-evidence controlled-write execution design`; it does not contain any collection design/execution/closure Gate that can create the required authority before the write. The six-key source-evidence record also intentionally contains no collection-root/path binding, and this design freezes no separate exact collection artifact path/schema/blob digest/closure receipt from which that prerequisite can be independently reconstructed.

This makes the controlled-write authority impossible to establish without either silently collecting real source evidence inside a later Gate that explicitly says it is not authorized, or accepting caller/prose-selected collection outputs.

**Acceptance:** before any controlled-write design, freeze an independent immutable-source collection progression and its machine-verifiable output binding. The six-key record schema from the approved publication-freeze design must remain unchanged; therefore bind collection provenance externally via an exact formal collection root plus fixed artifact path/schema/raw-bytes digest/blob identity (or an equivalently exact non-circular closure receipt). The controlled-write producer must derive the four record values only from that verified formal output, never from caller/environment/working-tree inputs.

### HIGH-2 — Design/Authority — actual `canonical_model_config` value has no formal authority source

Section 3 constructs the publication input package from the fixed record plus an “already frozen `canonical_model_config` / `checkpoint_source_descriptor`.” The descriptor is materially anchored by the fixed record: its canonical digest must equal `checkpoint_source_descriptor_sha256`, and its five semantic fields are represented by the record fields. The actual `canonical_model_config`, however, is only schema-constrained. No fixed root-owned config-evidence artifact, formal revision, path, raw-bytes digest, or other approved authority source is specified for the resolved values that the publication-freeze design requires to match the values actually consumed by training.

As written, any schema-valid active mapping could be supplied when generating the package; the external witness would then self-consistently hash that caller-chosen mapping. This reintroduces the exact caller-selected authority problem the prior Gate was intended to remove.

**Acceptance:** freeze an exact machine-verifiable authority for the resolved `canonical_model_config` before package generation. It may be a separate fixed config-evidence artifact or part of the independently approved collection/closure evidence, but it must bind the exact canonical config bytes/digest to an approved formal root/path/source and prohibit production caller/environment/working-tree selection. Package generation must derive the config from that authority and recompute its digest, not accept an arbitrary schema-valid mapping.

### HIGH-3 — Design/Authority — post-commit package/witness closure has no exact machine-readable receipt

The design correctly keeps package/witness data out of the source-evidence record to avoid self-reference and says package/witness binding is generated only after the new formal root exists. But it does not freeze the exact object that closes this post-commit phase. It says witness raw-byte SHA-256 and Git blob OID are “externally recorded,” without defining the receipt schema, persistence location, formal revision/path/digest binding, or what the next Gate must verify.

Consequently, after the record commit, a later caller can generate another self-consistent package/witness pair for the same record and present it as the closure result. The next publication materializer design has no unique machine-readable object that distinguishes the reviewed pair from a replacement pair.

**Acceptance:** freeze an exact non-circular post-commit closure receipt, produced only after the source-evidence formal root is known. It must at minimum bind the formal source-evidence root revision, fixed record path, record blob identity/raw SHA-256, input-package SHA-256, witness SHA-256, and the canonical config/descriptor digests; if a witness Git blob OID is retained, freeze its derivation semantics too. Because a receipt containing the formal root cannot live in that same root without circularity, define its separate immutable persistence/review binding explicitly. The next Gate must accept only the receipt frozen by the reviewed closure, not caller-supplied package/witness objects.

## 3. Positive findings

- The fixed source-evidence record path and exact six-key record schema remain aligned with the approved publication-freeze design.
- The design correctly keeps `cosmos-framework` Gitlink and the publication path out of the controlled-write staged set.
- The isolated-preflight / live-transaction / snapshot rollback / `ROLLBACK_INCOMPLETE` semantics are consistent with the now-approved Root Publication Freeze Design.
- Scope remains docs-only; no real collection/write/audit/runtime/GPU/training authority is claimed.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_producer_closure_design_v0.1.md:35)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **3**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

No real source-evidence collection, source-evidence record/package/witness creation or write, publication materialization, real root source audit, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1 is authorized by this verdict. Remediation should remain docs-only for this Gate.