# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence branch-typing remediation

**Date:** 2026-09-12  
**Formal root:** `c8e05cff42b1a6d4a3a599d2c02f8cdbf648c43c`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for this Gate.
- Independently verified formal root `c8e05cff42b1a6d4a3a599d2c02f8cdbf648c43c` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `eb658e0b4f7f006a20ba8a7aca9102d5cc64cb15` / same child and its canonical review.
- Incremental technical scope is docs-only and limited to five lines in `immutable_source_collection_execution_evidence_design_v0.1.md`; child/runtime and previously frozen executor / authority-root progression are unchanged.

## 2. Prior HIGH closure

### Prior HIGH-1 — PASS/FAIL execution exact-key conflict: CLOSED

The remediation now freezes branch-specific exact execution records:

- PASS: `{approval_formal_root,command_argv,interpreter,phase}`
- FAIL: `{approval_formal_root,command_argv,interpreter,phase,failure_code}`

The previous common-exact-key contradiction is removed. Existing exact four-key collection null-record and five-key receipt null-record remain consistent.

### Prior HIGH-2 — early-stage FAIL typing: PARTIALLY CLOSED

The remediation correctly makes PASS `source_entries` nonempty while allowing `[]` when FAIL occurs before source-read; it also introduces FAIL nullability for unreached SHA/revision/blob/tree/boolean/ref/path fields and keeps placeholder digest fabrication forbidden. This closes the prior blanket type/cardinality contradiction.

One machine-verifiability gap remains, described below.

## 3. Finding

### HIGH-1 — Evidence-only — FAIL phase/reachability semantics are not exact, so stage-aware nullability and partial-stage failures are not deterministically verifiable

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:27`

The schema now says fields from an "unreached FAIL stage" may be null, while fields from a reached stage must carry their normal typed values. However `phase` / `failure_code` are only required to be nonempty stable-identifier strings. No exact allowed phase vocabulary or mapping from each phase to the fixed check order is frozen.

Therefore an auditor cannot determine from the record which nested records are legitimately unreached and may be null. A record can claim an arbitrary phase string while choosing null/non-null fields inconsistently, and the contract has no deterministic validation rule to reject it.

The same omission appears for failures *inside* a reached stage. For example, if source-read starts successfully but the Nth entry fails open/read/hash, or candidate derivation computes only an initial subset before failing, that stage is "reached" but not all stage outputs exist. The current rule simultaneously requires reached-stage SHA fields to be 64-hex and provides null only for unreached stages, so there is no unique legal encoding for the partially completed stage.

**Acceptance:** freeze an exact finite `phase` vocabulary tied one-to-one to the stated check order, plus deterministic per-phase reached/failed/skipped semantics. For each phase define exactly which nested records/fields are required concrete, allowed null, required empty, or represent partial ordered results. In particular define source-read partial-entry failure and candidate-derivation partial-output failure without fabricated digests. Equivalent fixed `checks[]` records with exact `{name,status,reason,observed}` and PASS/FAIL/SKIPPED ordering would also satisfy this if the existing outer evidence schema deterministically derives nullability from them.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:27)`

Current blockers: **1 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **1**.

## 5. Scope

This verdict does not reopen the already-closed executor implementation/source-identity progression, authority-root materialization/binding, branch-specific execution key sets, or collection/receipt null-record schemas. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
