# ChatGPT Independent Review — R09-B TTT v0.3.5 Root Gitlink Authority Source-audit Implementation Design v0.1

**Date:** 2026-09-12  
**Formal root:** `ba684bf769016aaf8bac8b8d4271f6b6bcb3708c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-CANONICAL-NATIVE-ROOT-GITLINK-AUTHORITY-SOURCE-AUDIT-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read live `CODEX_INBOX.md`.
- Independently verified formal root `ba684bf769016aaf8bac8b8d4271f6b6bcb3708c` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Formal root is docs-only for the implementation-design Gate; child is unchanged.
- The approved predecessor is source-audit design v0.3 formal `7d5580b34e9f27ecf5dbbfde863bacd15a03e67c` / same child. Its v0.3 contract keeps v0.1 scope/read-only inputs/fail-closed evidence binding while superseding only later authority details.
- No implementation or real source-audit execution is authorized by this review.

## 2. Positive findings

- Two-file future implementation whitelist is root-only and does not touch child/runtime/training code.
- Git object command set is narrow; raw tree/blob bytes are explicitly required for hashing.
- The design correctly carries forward the exact three-key non-circular publication, exact 15-key config, exact five-key source descriptor, exact 14-key success audit record, atomic success-only output mutation, and temporary-fixture CPU/static tests.
- It continues to withhold real publication audit, real checkpoint/data/cache I/O, GPU/native workload, runtime integration and training authorization.

## 3. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_native_root_gitlink_authority_source_audit_implementation_design_v0.1.md:31)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

### HIGH-1 — Design/Authority — Git execution trust boundary is not frozen strongly enough to make caller environment non-authoritative

The design states that environment variables / Git aliases / working-tree substitution are forbidden, but the actual command contract only freezes command arguments. It does not freeze the executable identity/resolution or the subprocess environment. A normal `subprocess` invocation can inherit `PATH`, `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_NAMESPACE`, replacement-object controls and Git config injection variables. In particular, replacement refs / inherited Git context can change what `rev-parse` / `cat-file` resolve while the visible command line still matches the whitelist.

This is an authority-boundary issue, not merely an implementation detail: the predecessor contract says caller/env/working-tree inputs cannot select the audited provenance. The implementation design must therefore freeze how Git execution is isolated rather than leave that choice to the implementer.

**Acceptance:** freeze a deterministic Git-execution contract: trusted Git executable resolution/identity and a sanitized explicit subprocess environment (including disabling replacement objects and excluding caller-selected Git repo/object/config variables), with root and child repositories selected only by the approved `-C` / `--git-dir` arguments. Add direct temporary-fixture negatives proving hostile `GIT_DIR` / object-directory-or-alternate / replacement-object / config-injection inputs cannot change the audited formal root, Gitlink, publication or child tree. Bind the Git command/tool version identity into the machine-readable evidence as required by the source-audit contract.

### HIGH-2 — Design/Authority — the implementation artifact drops binding per-step audit evidence from source-audit design v0.1

Source-audit design v0.1 remains binding for the machine-readable fail-closed evidence and explicitly requires root-tree lookup, Gitlink lookup, child commit/tree reachability, canonical descriptor digest evidence and audit command/version identity, with exact PASS/FAIL and failure reason per record. v0.3 explicitly retained v0.1 fail-closed artifact semantics.

The implementation design instead specifies a success artifact containing only `status="PASS"`, tool source SHA-256, command schema/version, the compact 14-key success audit record and its digest; failure only prints an unspecified one-line summary JSON. It does not freeze the required lookup/reachability evidence records, their PASS/FAIL/reason schema, or an exact failure-summary schema. Therefore two implementations could both satisfy this document while producing materially different and incomplete audit evidence, and failure provenance may not be independently reviewable.

**Acceptance:** freeze exact machine-readable evidence schemas for root commit/tree lookup, Gitlink lookup, publication-blob lookup, child commit/tree reachability, nested mapping/digest validation and command/tool identity. Every attempted check must have deterministic status and failure reason; success artifact must carry the required evidence (or canonical digests plus exact referenced records), and failure stdout/artifact schema must be exact and independently parseable while still preserving failure-no-output-mutation. Also add a direct witness that non-canonical publication raw JSON bytes are rejected or otherwise demonstrate the exact v0.3 canonical-publication byte rule.

## 4. Scope

No child or runtime implementation is authorized. Real root publication audit, checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, forward/loss/backward, optimizer/scheduler stepping, sidecar, training, evaluation, inference and LIBERO4IN1 remain forbidden.
