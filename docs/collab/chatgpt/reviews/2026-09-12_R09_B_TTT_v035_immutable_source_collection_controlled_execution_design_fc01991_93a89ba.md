# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution Design evidence remediation

**Date:** 2026-09-12  
**Formal root:** `fc0199178afd547e706f33e38588b50356a448e9`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`; this exact pair is the current formal evidence-remediation request.
- Independently verified formal root `fc0199178afd547e706f33e38588b50356a448e9` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental technical scope from the prior rejected pair `a3b03c9baea7cd89cc38c591124cae7c3aaea1f0` is docs-only: one 35-line execution-evidence design plus review/Inbox bookkeeping; child/runtime is unchanged.
- Prior HIGHs for executor implementation/source-identity progression and authority-root materialization/binding remain closed. No real source I/O, authority-root creation, collection/receipt mutation, publication, audit, child/runtime, GPU or training action is authorized here.

## 2. Positive findings

- The remediation now freezes an outer evidence key set, a named schema/version, canonical JSON rules, PASS/FAIL statuses, nested records, ordered source-entry tuples, check ordering, and `evidence_sha256` recomputation semantics.
- It narrows the prior path prohibition to approved tool/workdir/authority paths while excluding source transport/raw-source paths, raw bytes, URLs and secrets.
- Tool/source identity, authority tuple, lineage, handoff, candidate digests, collection/receipt roots, post-checks, push/publication state and rollback data are all represented in the intended evidence model.

## 3. Findings

### HIGH-1 — Evidence — PASS/FAIL branch requirements contradict the declared exact nested key sets

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:10`

The design declares common nested **exact keys**, including `execution={approval_formal_root,command_argv,interpreter}` and `collection={revision,tree_native_oid,parent_revision,delta_paths}`. It then requires PASS `execution` to add `phase`, FAIL `execution` to add `phase,failure_code`, and the FAIL collection null-record to add `blob_native_oid`.

Under the same document's rule that unknown/extra fields fail, these branch records cannot simultaneously satisfy both the common exact-key declaration and the branch-specific requirements. An implementation therefore has no single valid schema to emit or audit.

**Acceptance:** freeze branch-specific exact schemas instead of mutating a common exact-key set. For example, define exact PASS and FAIL nested key sets explicitly (or define a common superset where `phase`/`failure_code` and `blob_native_oid` have exact nullable/value rules). Ensure every field allowed in a branch is present in that branch's exact schema and no branch requires an extra key outside it.

### HIGH-2 — Evidence — early FAIL records are impossible because later-stage evidence is mandatory and non-null

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:25`

`source_entries` is required to be a nonempty ordered array for every record, while `handoff.candidate_handoff_sha256` and all candidate SHA fields are also mandatory common fields. But the fixed check ordering explicitly permits failure at tool identity, environment, authority, or lineage — before any source entry is opened and before a handoff/candidate set can exist.

So a correct fail-closed executor cannot encode evidence for precisely the early failures this schema is meant to audit without inventing hashes or violating the nonempty constraint. The collection/receipt null-record only solves late-stage Git outputs, not unreached source/handoff/candidate stages.

**Acceptance:** define exact stage-aware FAIL semantics. For every stage after the first failure, freeze either exact `null`/null-record/SKIPPED representations or a fixed checks array with PASS/FAIL/SKIPPED state; allow `source_entries=[]` only when source-read was not reached, and define exact nullability for handoff/candidate/collection/receipt fields by phase. Preserve the fixed check order and prohibit fabricated placeholder digests. Also freeze field types for `ordinal`, `byte_length`, `command_argv`, `phase`, `failure_code`, `delta_paths`, refs/paths, and nullability so the machine-readable contract is complete.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:10)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **2**.

## 5. Scope

This verdict does not reopen the already-closed executor implementation/source-identity progression or authority-root materialization/binding requirements. It only requires an internally consistent, stage-complete exact execution-evidence schema before proceeding to executor implementation design. No real source I/O, authority materialization, collection/receipt mutation, source-evidence write, publication/audit, child/runtime, GPU, training, evaluation, inference or LIBERO4IN1 is authorized.
