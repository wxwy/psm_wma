# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution Implementation Design

**Date:** 2026-09-12  
**Formal root:** `c62bc80440dc2e78091c183b39cec96aa17e7f13`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal request for this Gate.
- Independently verified formal root `c62bc80440dc2e78091c183b39cec96aa17e7f13` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is the approved controlled-execution design pair `2c73ad0bf9f49d1dd13f0803046ac75f3cd9449c` / same child.
- Incremental technical scope is docs-only: one new implementation-design document plus bookkeeping; child/runtime are unchanged.

## 2. Findings

### HIGH-1 — Design / Authority — source identity is required before the future files exist, so the prescribed binding point is impossible

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md:8`

The design says the two future implementation files must have their path / Git blob / raw SHA and interpreter frozen **before implementation**, against the formal root. But the implementation-design formal root does not yet contain `tools/psm_wma/immutable_source_collection.py` or `tools/psm_wma/test_immutable_source_collection.py`; these are exactly the files this Gate proposes to add later. Therefore there is no committed blob/raw-SHA identity available at the stated binding point.

This conflicts with the already-approved progression, which needs a stable executor identity before source open but also places CPU/static implementation closure after implementation design. The implementable sequence is: freeze the two-path allowlist and identity derivation rule in this design; create only those files; commit the CPU/static implementation; then have the CPU/static closure bind the **implementation formal root** plus exact path/blob/raw-SHA/interpreter from that committed tree. Later authority-root materialization and controlled execution approval must accept only that exact reviewed tool identity.

**Acceptance:** move the concrete source-identity binding to the CPU/static implementation formal root / closure after the files exist, while preserving fail-before-source-open drift checks for all later stages. Do not let request/ledger/handoff commits replace that implementation formal pair.

### HIGH-2 — Design / Implementation — the CPU/static seam is test-only and in-memory-only, so the reviewed source would have to change before real execution

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md:14-18`

The document calls `tools/psm_wma/immutable_source_collection.py` the unique production executor, but then constrains the module to accept only an injectable `TemporaryGitFixture` / FD shim and requires it to construct execution evidence only as an in-memory object. The approved controlled-execution contract, however, requires the bound executor later to operate through the real Git/FD transaction path and to emit canonical evidence to the controlled failure-evidence directory.

If the CPU/static implementation follows this design literally, later real execution requires editing the executor to add real Git/FD adapters and an evidence sink, which changes the tool blob/raw SHA after CPU/static closure and invalidates the identity that authority materialization / execution approval is supposed to bind. Conversely, quietly adding unspecified real adapters or a file sink during the CPU/static implementation would exceed the frozen implementation design.

**Acceptance:** freeze one exact production dependency-injection seam now, implemented unchanged in the two-file CPU/static closure. The same production executor code path must accept explicit Git/FD/evidence-sink dependencies or equivalent interfaces; CPU/static tests bind those dependencies only to temporary synthetic Git/FD roots and a temporary/in-memory sink, while later real execution binds the same unchanged interfaces to approved real inputs only after authority materialization and execution approval. No later executor source modification may be required merely to switch from synthetic fixtures to approved real execution.

## 3. Positive findings

- The proposed file allowlist is narrow: one executor plus one direct stdlib test file.
- The negative-test inventory correctly includes authority/lineage drift, descriptor-safe FD failures, same-FD race checks, one-shot handoff, collection/receipt allowlists, retained snapshots, rollback and `ROLLBACK_INCOMPLETE`.
- The scope correctly forbids real source/checkpoint/cache I/O, authority-root materialization, live collection/receipt/publication mutation, child/GPU/training.
- The design preserves the previously frozen source-evidence/publication closure before any GPU work.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md:8)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **1**.  
Implementation blockers: **1**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This verdict does not reopen the already-approved controlled-execution/evidence contracts. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
