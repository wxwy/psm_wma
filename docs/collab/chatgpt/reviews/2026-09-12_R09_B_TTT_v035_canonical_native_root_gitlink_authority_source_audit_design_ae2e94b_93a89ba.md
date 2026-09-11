# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Design v0.2

**Date:** 2026-09-12  
**Formal root:** `ae2e94b045c9d1cf3f352ad49e374548153b0043`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `CODEX_INBOX.md`.
- Independently verified formal root `ae2e94b045c9d1cf3f352ad49e374548153b0043` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal root is docs-only and adds only `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.2.md`; child is unchanged.
- This review only checks remediation of the prior v0.1 Design/Authority findings and any new contradiction introduced by v0.2.

## 2. Positive findings

- Prior HIGH-1 is closed: v0.2 now distinguishes native Git tree OIDs from external SHA-256 values and freezes the exact relation `formal revision -> native tree OID -> raw tree content bytes -> tree_content_sha256 -> canonical tree record -> tree_record_sha256`.
- The specified `git cat-file tree <native_oid>` byte source is concrete and reproducible; object type, byte length, canonical record schema and fail-closed mismatch behavior are all explicit.
- v0.2 also moves the config/source authority to a fixed root-tree path and explicitly forbids caller/env/working-tree/time substitution.
- Scope remains docs-only and does not authorize child/runtime changes, real checkpoint/data/cache I/O, GPU/native workload, optimizer/scheduler stepping, sidecar, training/eval/inference or LIBERO4IN1.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.2.md:17)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

### HIGH-1 — Design/Authority — publication envelope is self-referential and cannot be constructed deterministically

v0.2 requires the publication blob itself to contain both:

- `publication_blob_sha256`, which must equal SHA-256 of the **same blob raw bytes**; and
- `publication_root_tree_native_oid`, which must equal the audited root tree OID even though that root tree OID depends on the Git blob object produced from the publication bytes.

This creates two circular fixed-point requirements. The blob bytes would need to contain their own SHA-256, and the blob would also need to contain the tree OID that is computed from a tree entry referencing the blob object produced from those same bytes. This is not a stable buildable immutable-publication scheme.

**Acceptance:** remove all self-referential identity fields from the publication blob. A safe pattern is:

1. publication blob contains only its own versioned schema plus the canonical model-config and checkpoint-source-descriptor mappings;
2. the source-audit record, external to that blob, derives and binds `formal_root_revision`, `root_tree_native_oid`, fixed publication path, publication blob native OID, `publication_blob_sha256 = SHA256(raw_blob_bytes)`, and verifier schema;
3. root ownership is proven because the verified formal root tree contains the exact fixed path -> exact publication blob object; no blob field needs to claim its own digest or containing root tree OID.

Any equivalent non-circular construction is acceptable, but the contract must freeze it here rather than leave the implementation design to invent it.

### HIGH-2 — Design/Authority — nested `canonical_model_config` and `checkpoint_source_descriptor` schemas remain implementation-defined

The prior v0.1 acceptance required the exact root-owned source **and exact schema/version/canonical bytes rule** for both `canonical_model_config_sha256` and `checkpoint_source_descriptor_sha256`.

v0.2 fixes the publication path and outer envelope, but only says the two nested mappings "须 exact versioned schema". It does not freeze the actual schema identifiers, exact keysets/types, or a reference to an already-frozen concrete schema contract. Therefore a later implementation could still choose different model-config/source-descriptor mappings and claim they are "versioned canonical".

**Acceptance:** freeze, in this design, the exact schema/version identity for each nested mapping and its exact key/type contract, or explicitly bind to a previously approved concrete schema by canonical artifact/path/version. Their SHA-256 values must be computed from the same frozen canonical JSON rule, and unknown/missing/type/value/schema drift must fail the source audit before any `root_gitlink_authority_v1` can be emitted.

## 4. Scope

No child/runtime code modification is authorized. Real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference and LIBERO4IN1 remain forbidden.
