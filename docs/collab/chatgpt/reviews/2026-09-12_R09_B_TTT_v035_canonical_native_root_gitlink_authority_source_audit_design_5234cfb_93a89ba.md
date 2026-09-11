# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Design v0.1

**Date:** 2026-09-12  
**Formal root:** `5234cfb22e38e01c8e578f6825a6fc3c44873c98`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live Codex request ledger.
- Independently verified formal root `5234cfb22e38e01c8e578f6825a6fc3c44873c98` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal root commit is docs-only and adds only `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.1.md`; the child is unchanged in this Gate.
- The preceding synthetic CPU/static remediation closure remains synthetic-only and is not treated as production lineage evidence.

## 2. Positive findings

The design correctly keeps this Gate read-only, rejects detached child/worktree/environment/payload/time/path substitutions for the root-tree/Gitlink predicate, requires child commit/tree reachability, keeps production mapping generation fail-closed on audit failure, and explicitly withholds checkpoint restore, real I/O, GPU and training authorization.

The staged sequence also remains conservative: source-audit design -> later docs-only source-audit implementation design -> implementation closure -> independent root-owned runtime-integration design/implementation -> real-I/O preflight -> GPU Gate.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_design_v0.1.md:19)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

### HIGH-1 — Design-only — `root_tree_sha256` / `child_tree_sha256` have no frozen, independently reproducible byte semantics

The frozen input names `root_tree_sha256` and `child_tree_sha256`, but the design never defines what exact bytes are SHA-256 hashed or how those values relate to repository-native Git tree object IDs. For the submitted formal root, GitHub exposes the root tree as native Git object ID `108945312bc42bc6679936d0cb5503141a0f781c` (40 hex), so that native object ID cannot silently be treated as the advertised SHA-256 field.

Without an exact definition, a later implementation could hash raw Git tree-object bytes, a GitHub API JSON response, a normalized lookup record, or another serialization and still claim compliance. That leaves a provenance field implementation-defined.

**Acceptance:** freeze the exact semantics for both tree fields. At minimum, distinguish the repository-native tree object ID from the external SHA-256 field, and define the exact immutable byte source / canonical serialization / encoding / field ordering used to compute `root_tree_sha256` and `child_tree_sha256`, together with the exact relation `formal revision -> native tree OID -> audited tree bytes/record -> SHA-256`. The rule must be independently reproducible and fail closed on mismatch; the later implementation design may encode/test this rule but must not invent it.

### HIGH-2 — Design-only — root-owned config/source authority and immutable publication trust root are not frozen

The approved lineage-authority refreeze explicitly deferred **authority manifest load/verification, signature or equivalent root-owned immutable publication**, plus production Git inspection, to this future source-audit/design/implementation sequence. It also requires the production authority to bind `canonical_model_config_sha256` and `checkpoint_source_descriptor_sha256` as root-owned provenance inputs.

Current v0.1 only says config/source descriptor are "versioned canonical mapping" SHA-256 values and that audit evidence contains canonical descriptor bytes SHA-256. It does not freeze the exact owner/source/path or schema version for those mappings, nor the immutable publication/manifest envelope and signature-or-equivalent verification that makes them root-owned rather than caller-selected bytes. A later implementation could therefore choose its own config/source source and its own publication trust root.

**Acceptance:** freeze the exact root-owned source for the canonical model-config and checkpoint-source-descriptor mappings (owner/path or immutable publication identifier, exact schema/version and canonical bytes rule), and freeze the authority publication/manifest verification predicate required by the predecessor contract: signature verification or an explicitly defined equivalent immutable root-owned publication mechanism. The machine-readable audit record must bind the publication identity/digest and verifier/tool identity; missing/unverifiable publication, config or source owner must FAIL and must not produce `root_gitlink_authority_v1`.

## 4. Scope

No child or runtime code modification is authorized by this review. Real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference and LIBERO4IN1 remain forbidden.
