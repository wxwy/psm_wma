# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence phase/reachability remediation

**Date:** 2026-09-12  
**Formal root:** `7e633d1c6b4d74f661d9421c6ab7e75eda0cf203`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for the Gate.
- Independently verified formal root `7e633d1c6b4d74f661d9421c6ab7e75eda0cf203` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `c8e05cff42b1a6d4a3a599d2c02f8cdbf648c43c` / same child and its canonical review.
- Incremental technical scope remains docs-only: evidence phase/reachability semantics plus root bookkeeping. Child/runtime and the previously frozen executor implementation / authority-root progression are unchanged.

## 2. Prior HIGH closure

### Prior HIGH — finite phase vocabulary / partial source-read and candidate typing: PARTIALLY CLOSED

The remediation does freeze a finite FAIL phase vocabulary tied to the fixed check order and adds deterministic prefix rules for `source_read`, `candidate_derivation`, collection/receipt null records and post-check prefixes. This closes the prior arbitrary-phase-string defect and substantially improves stage-aware typing.

However fresh audit found three remaining evidence-encoding defects below.

## 3. Findings

### HIGH-1 — Evidence-only — live-stage primary failure cannot carry the required successful rollback witness

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:41`

The inherited controlled-execution contract requires any live failure to restore the snapshot and prove rollback; if restoration cannot be proved, the result is `ROLLBACK_INCOMPLETE`. The new table instead makes `rollback` null for primary failures in `collection`, `receipt`, `post_check` and `push_publication`, while reserving `phase=rollback` for a later standalone failure.

That loses the required evidence for the normal case “collection/receipt/post-check failed, then rollback succeeded”. It also makes the phase model inconsistent: rollback is a recovery action triggered by an earlier first failure, not an independent next normal check that can be the first unsuccessful phase after every previous section completed.

**Acceptance:** keep the primary failure phase separately from rollback outcome. For every phase where live mutation may have occurred, freeze a concrete rollback record after the primary failure: before/after snapshot digests plus `verified=true|false`; `verified=false` must fail-stop as `ROLLBACK_INCOMPLETE`. If a separate rollback-failure phase is retained, preserve the primary failure identity in an exact field rather than discarding it. Pre-live failures may use an exact not-required/null rollback form.

### HIGH-2 — Evidence-only — a forbidden push/publication event cannot be encoded as observed evidence

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:44`

The `push_publication` row says the only legal FAIL representation is exactly `{pushed:false,published:false}` and that any non-false value has no legal FAIL representation. But this check can only fail meaningfully when the observed state violates the invariant, e.g. `pushed=true` or `published=true`.

Thus the most important safety violation becomes unrepresentable in the canonical evidence: the executor/auditor cannot record the observed `true` value without making the evidence itself invalid.

**Acceptance:** either remove `push_publication` as a failure phase and make `{false,false}` a mandatory invariant checked elsewhere, or allow the FAIL record to encode the observed booleans and require at least one `true` for `phase=push_publication`. Such a record remains FAIL-only and must never authorize downstream consumption.

### HIGH-3 — Evidence-only — `candidate_derivation` partial rule conflicts with the inherited one-shot handoff contract

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:40`

The approved closure contract freezes `immutable_source_collection_preflight_handoff_v1` as being created only after the five candidate artifacts and candidate config digests have been derived; the handoff itself binds those digests. The new `candidate_derivation` row simultaneously requires `handoff` to be fully typed while allowing the `candidates` record to contain only a 0..5 digest prefix.

Those states cannot both be true under the inherited handoff definition. If candidate construction has only produced a prefix, a complete handoff does not yet exist. Conversely, if the complete handoff exists and the candidate-derivation *verification* fails, all candidate digests may be concrete even though the derivation relation/check failed, but the new table declares six concrete candidate digests to mean the phase already succeeded.

**Acceptance:** distinguish candidate construction from candidate verification, or redefine the failure encoding so it matches the inherited handoff lifecycle. Before handoff creation, partial candidate construction may be represented with `handoff` null; after handoff creation, verification failure must permit all candidate digests to remain concrete while separately recording which derivation/config-equality check failed. Do not weaken the approved one-shot handoff binding.

## 4. Positive findings

- The exact finite FAIL phase vocabulary is now frozen and tied to the fixed order.
- `source_read` partial failure is represented by an ordered successful prefix without placeholder entries.
- Collection/receipt null-record exact key sets remain correct.
- Post-check uses a deterministic true-prefix / first-false / trailing-null representation.
- Formal Gitlink is exact and child is reachable.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:40)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **3**.

## 6. Scope

This verdict does not reopen the already-closed executor implementation/source-identity progression, authority-root materialization/binding, PASS/FAIL execution key sets, collection/receipt null-records, or source-read prefix semantics. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
