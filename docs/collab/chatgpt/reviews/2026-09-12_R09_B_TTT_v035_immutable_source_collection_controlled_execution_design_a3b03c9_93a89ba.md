# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution Design v0.2

**Date:** 2026-09-12  
**Formal root:** `a3b03c9baea7cd89cc38c591124cae7c3aaea1f0`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current remediation request for the Gate.
- Independently verified formal root `a3b03c9baea7cd89cc38c591124cae7c3aaea1f0` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is prior rejected pair `47a05a526ed98ab477ffad7e7f8548be1c1d981c` / same child and its canonical ChatGPT review.
- Incremental technical scope is docs-only: new v0.2 controlled-execution design plus bookkeeping/review persistence. No executor implementation, real source I/O, authority-root materialization, collection/receipt mutation, source-evidence write, publication, audit, child/runtime, GPU, or training action is authorized by this review.

## 2. Prior HIGH closure

### Prior HIGH-1 — executor source identity / reviewed implementation progression: CLOSED

v0.2 now requires, before any real execution approval, an independently approved progression of `executor implementation design -> root CPU/static implementation closure -> authority-root materialization/binding -> controlled execution approval`. The executor path is fixed to `tools/psm_wma/immutable_source_collection.py`, and the later implementation design must bind the executor/test allowlist plus formal root/path/Git blob OID/raw SHA-256. CPU/static closure must directly witness authority drift, lineage drift, descriptor-safe source reads, same-FD double-hash/fstat stability, single-use handoff, exact five-path/one-path allowlists, rollback success, and `ROLLBACK_INCOMPLETE`, using temporary fixtures only.

This closes the previous trust gap in which a nonexistent/unreviewed executable could have been introduced only at the real-I/O approval step.

### Prior HIGH-2 — execution-authority materialization/binding path: CLOSED

v0.2 now inserts an independent authority-root materialization/binding stage before any source entry is opened. The authority root must have parent equal to the reviewed authority formal root and exact delta limited to the fixed selection-request and resolved-config paths. Parent/path/schema/blob OID/raw SHA-256 are re-read from the committed tree, and three-party review binds the exact seven-field authority tuple consumed by the executor.

This supplies the previously missing executable creation/binding path for the selection/config authority and keeps caller/env/worktree substitutes forbidden.

## 3. Finding

### HIGH-1 — Evidence-only — `immutable_source_collection_execution_evidence_v1` is still not an exact machine-readable PASS/FAIL schema

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.2.md:32`

Section 4 names `immutable_source_collection_execution_evidence_v1`, says unknown/missing/drift fields must fail, and enumerates information that evidence “must contain.” That is materially better than v0.1, but it still does not freeze an exact schema that an implementation and later reviewer can validate deterministically. There is no exact outer key set, field type contract, PASS/FAIL `status` enum, success-vs-failure branching rule, exact nested shapes for tool/command/environment/authority/lineage/source-entry/handoff/collection/receipt/post-check/rollback records, required check ordering, or canonical record digest semantics.

Because the contract says unknown fields fail, an open-ended “must contain” list is internally incomplete: neither implementation nor audit can determine which fields are unknown, which are optional only on FAIL, or how nested drift is detected. The same paragraph also requires tool path/workdir/authority tuple information but the FAIL paragraph broadly says evidence must not contain “路径”; that wording conflicts unless it is narrowed to source transport/raw-source paths or otherwise enumerated exactly.

This is the final evidence boundary before real source I/O and Git mutation. A later read-only reviewer must be able to validate the exact execution record without relying on prose interpretation.

**Acceptance:** freeze exact canonical PASS and FAIL evidence contracts before executor implementation. At minimum:

1. define the exact outer key set and `schema="immutable_source_collection_execution_evidence_v1"`;
2. define `status` exact values (for example PASS/FAIL), exact field types, and which fields are present in both statuses versus FAIL-only fields;
3. freeze exact nested record key sets/types for tool identity, interpreter/command identity, sanitized env/workdir/CPU-only/no-network identity, reviewed authority tuple, target lineage, ordered source-entry results, handoff/candidate digests, collection/receipt root-tree-parent-delta records, post-checks, push/publication state, and rollback/snapshot records;
4. freeze check ordering and stable `phase` / `failure_code` vocabulary or exact derivation rules;
5. freeze canonical JSON / SHA-256 semantics for the evidence record itself so later audit can bind exact bytes;
6. narrow the no-path rule so approved tool/workdir/fixed authority paths required by the schema are not simultaneously forbidden, while raw source bytes and unapproved source transport paths remain excluded.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_controlled_execution_design_v0.2.md:32)`

Current blockers: **1 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **1**.

## 5. Scope

This verdict keeps remediation docs-only. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference, or LIBERO4IN1.
