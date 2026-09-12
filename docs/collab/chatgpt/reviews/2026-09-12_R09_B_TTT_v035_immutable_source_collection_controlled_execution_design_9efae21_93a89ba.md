# ChatGPT Independent Review — R09-B TTT v0.3.5 Controlled Collection Execution Evidence failure-lifecycle remediation

**Date:** 2026-09-12  
**Formal root:** `9efae217d8c45b7afd651d52e3cb5b8cc63226f9`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for the Gate.
- Independently verified formal root `9efae217d8c45b7afd651d52e3cb5b8cc63226f9` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `7e633d1c6b4d74f661d9421c6ab7e75eda0cf203` / same child and its canonical review.
- Incremental technical scope remains docs-only: evidence failure-lifecycle semantics plus bookkeeping; child/runtime and the already-frozen executor/authority-root progression are unchanged.

## 2. Prior HIGH closure

### Prior HIGH-1 — primary live failure lacked rollback outcome: CLOSED IN DIRECTION

The remediation now preserves the primary failure phase and makes rollback a separate recovery outcome for `collection`, `receipt`, `post_check`, and `push_publication`. `verified=false` is fail-stopped as `ROLLBACK_INCOMPLETE` without overwriting the primary phase. This closes the previous loss-of-primary-failure problem.

### Prior HIGH-2 — forbidden push/publication was unencodable: CLOSED

`phase=push_publication` now records the observed booleans and requires at least one of `pushed` / `published` to be `true`. The record remains FAIL-only and cannot authorize downstream consumption.

### Prior HIGH-3 — candidate partial state conflicted with one-shot handoff lifecycle: CLOSED

Candidate construction and post-handoff verification are now separate phases. Construction permits only a deterministic digest prefix while `handoff` remains null; verification requires all six candidate digests and the complete one-shot handoff to remain concrete. This matches the inherited handoff lifecycle.

## 3. Findings

### HIGH-1 — Evidence-only — PASS rollback representation contradicts the new lifecycle contract

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:49`

The remediation explicitly states that rollback is executed only after a live primary failure and is not part of the primary phase order. But the PASS rule still requires `rollback.verified=true`. No exact PASS-only semantics are frozen for `before_snapshot_sha256` / `after_snapshot_sha256`, and a successful run has no rollback action to verify.

Therefore one exact PASS record is not semantically defined: either it fabricates a rollback witness that never occurred, or `verified=true` is being repurposed to mean “rollback not required” without an exact schema rule saying so.

**Acceptance:** freeze one unambiguous PASS representation. Prefer an exact not-required/null rollback record for PASS (and pre-live FAIL), or define a separate exact rollback status that distinguishes `NOT_REQUIRED` from an actually executed-and-verified rollback. Do not overload `verified=true` for both meanings.

### HIGH-2 — Evidence-only — `verified=true` does not machine-prove exact snapshot restoration

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:42`

For live failures the schema requires both snapshot SHA fields to be 64-hex and sets `verified=true` for an ordinary recovered failure, but it never freezes the acceptance relation between those two digests. As written, a record with different `before_snapshot_sha256` and `after_snapshot_sha256` can still satisfy the schema while claiming `verified=true`.

That is weaker than the inherited closure contract, which requires proving exact restoration of target ref / HEAD / index / worktree state before an ordinary failure may return; otherwise the result must be `ROLLBACK_INCOMPLETE`. A reviewer must not have to trust the executor's boolean assertion.

**Acceptance:** freeze the snapshot digest semantics and the exact verification predicate. At minimum, define the canonical snapshot fields covered by `*_snapshot_sha256` and require `verified=true` iff the independently recomputed after-snapshot is exactly equal to the before-snapshot (or an equivalently explicit component-wise equality predicate). Any mismatch, missing component, or unverifiable state must force `verified=false` and `failure_code=ROLLBACK_INCOMPLETE` while retaining the primary failure phase.

## 4. Positive findings

- finite primary failure vocabulary and fixed ordering remain exact;
- source-read ordered-prefix and candidate-construction prefix rules remain deterministic and placeholder-free;
- push/publication violation is now directly observable in canonical FAIL evidence;
- candidate construction vs complete-handoff verification now matches the approved one-shot lifecycle;
- collection/receipt null-records and post-check prefix semantics remain exact;
- formal Gitlink is exact and child is reachable.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_execution_evidence_design_v0.1.md:49)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **2**.

## 6. Scope

This verdict does not reopen the already-closed executor implementation/source-identity progression, authority-root materialization/binding, phase vocabulary, source-read/candidate partial typing, push/publication observation, or candidate handoff lifecycle. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
