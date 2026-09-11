# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution Design v0.1

**Date:** 2026-09-12  
**Formal root:** `47a05a526ed98ab477ffad7e7f8548be1c1d981c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal request for this Gate.
- Independently verified formal root `47a05a526ed98ab477ffad7e7f8548be1c1d981c` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Prerequisite closure design is approved at `5f6741ca0bfb61ca0e55fae95709c891fa5c5520` / same child with `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CLOSURE`.
- Incremental technical scope is docs-only: new controlled-execution runbook plus root bookkeeping. No real source I/O, authority-root creation, collection/receipt mutation, source-evidence write, publication, audit, GPU or training action is authorized by this review.

## 2. Positive findings

- The runbook preserves the approved target-lineage tuple, authority tuple, same-activation one-shot handoff, same-FD double-hash source-read semantics, five-path collection root, one-path receipt root, and rollback / `ROLLBACK_INCOMPLETE` contract.
- It keeps collection and receipt publication downstream of complete post-checks and preserves the required source-evidence controlled-write -> record/receipt -> publication materializer/verifier -> root audit sequence before GPU smoke.
- The formal Gitlink is unchanged and exact.

## 3. Findings

### HIGH-1 — Design/Authority — the real executor referenced by the only command does not exist and has no reviewed implementation/source-identity progression

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.1.md:15`

The runbook freezes one command shape invoking `tools/psm_wma/immutable_source_collection.py execute`, but that path does not exist in the submitted formal tree. No implementation-design, implementation-closure, source-audit, source digest, allowed implementation file set, or CPU/static behavior witness is frozen before the design says a later execution approval may fill concrete inputs and run real source I/O.

That creates a trust gap at the most sensitive boundary: a future execution approval could introduce or replace the executable at the same time it asks permission to read real source bytes and mutate the collection lineage, without any previously approved implementation contract proving that the code actually enforces root-FD/no-symlink reads, same-FD double hashes, one-shot handoff, target lineage checks, exact staged deltas, rollback and fail-stop behavior.

**Acceptance:** before any real execution approval, freeze and independently review the executor implementation/source identity. Prefer a separate docs-only implementation design followed by CPU/static implementation closure for the exact root-owned tool path. At minimum, the future approved executable must be bound by exact formal root/path/raw SHA-256 (or Git blob OID plus raw SHA-256), with an allowed source-file set and direct witnesses covering authority drift, lineage drift, source-read races, handoff single-use, five-path/one-path allowlists, rollback and `ROLLBACK_INCOMPLETE`. Any executable/source drift must block real source I/O.

### HIGH-2 — Design/Authority — the execution-authority root is assumed as a pre-existing input but its materialization/binding path is not executable

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.1.md:9-13`

The inherited contract requires a reviewed execution-authority root containing the exact selection-request and resolved config blobs before any source entry is opened. This runbook explicitly says it does not create an authority root, while the future command requires `--authority-root-revision <reviewed>`. The current progression contains no exact materialization transaction that creates that non-circular root, proves its parent is the reviewed approval root, restricts its delta to exactly the two fixed blobs, and obtains the three-party tuple binding before real execution.

Merely listing an authority tuple among future approval inputs does not explain how the tuple becomes a reviewed immutable fact. Without a frozen creation/binding step, the real execution path either dead-ends or silently relies on an ad hoc/manual commit whose selection/config bytes were never independently accepted as the execution authority.

**Acceptance:** freeze an exact non-circular authority-root materialization/binding step before source-read execution. It must create or consume one root whose parent is the approved authority formal root, whose delta is exactly the fixed selection-request and resolved-config paths, and whose tree/blob/raw-SHA values are independently recomputed and explicitly bound by review to the seven-field authority tuple. The controlled executor must accept only that reviewed tuple; caller/env/worktree-created substitutes remain forbidden.

### HIGH-3 — Evidence — real execution success/failure evidence is prose-only, so the required behavior cannot be independently re-audited

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.1.md:40`

Section 4 mentions an `execution report`, a stable failure code, and minimal evidence, but freezes no exact machine-readable success/failure schemas, check ordering, command/tool identity, environment/workdir/network/CPU identity, or concrete witnesses for the authority tuple, target lineage, ordered source-entry hashes, one-shot handoff digest, collection/receipt parents, staged deltas, post-commit lookups and rollback state.

Because the next approval is intended to authorize real source reads and Git mutations, a prose log is insufficient. A reviewer must be able to prove after the run that the exact approved executable/command/environment was used and that each fail-closed boundary held, without trusting terminal narrative or mutable process memory.

**Acceptance:** freeze exact canonical machine-readable PASS/FAIL evidence before real execution. At minimum bind: execution approval/formal root; tool path/source identity; interpreter/command identity; sanitized environment/workdir plus CPU-only/no-network enforcement identity; reviewed authority tuple; target-lineage tuple; ordered source-entry `(ordinal,byte_length,sha256)` results; `candidate_handoff_sha256`; candidate artifact digests; collection root/tree/parent and exact five-path delta; receipt root/tree/parent and exact one-path delta; post-check results; push/publication state; and, on failure, phase/stable code plus before/after snapshot and rollback verification / `ROLLBACK_INCOMPLETE`. Evidence must exclude raw source bytes and must fail closed on missing/unknown/drifted fields.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.1.md:15)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **1**.

## 5. Scope

This verdict does not authorize real source selection/read/hash, authority-root creation, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Remediation should remain docs-only unless a separately approved Gate explicitly authorizes implementation or real execution.
