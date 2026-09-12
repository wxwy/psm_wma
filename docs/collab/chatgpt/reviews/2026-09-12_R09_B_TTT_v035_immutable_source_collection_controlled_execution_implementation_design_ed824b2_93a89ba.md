# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution Implementation Design seam remediation

**Date:** 2026-09-12  
**Formal root:** `ed824b2e06c27328f6639aba6b5c06e1de6bee73`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current remediation request for this Gate.
- Independently verified formal root `ed824b2e06c27328f6639aba6b5c06e1de6bee73` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is prior rejected pair `c62bc80440dc2e78091c183b39cec96aa17e7f13` / same child and its canonical review.
- Incremental technical scope remains docs-only and modifies only the implementation-design seam / identity-binding text; child/runtime are unchanged.

## 2. Prior HIGH closure

### Prior HIGH-1 — concrete tool identity was required before future files existed: PARTIALLY CLOSED

The remediation correctly moves concrete executor/test file identity binding until after the two implementation files exist and are committed in the CPU/static implementation formal root/closure, and it explicitly prevents request/ledger/handoff commits from replacing that implementation formal pair. That closes the impossible pre-implementation file-blob binding.

One source-identity ambiguity remains: the same sentence now says concrete `path/Git blob/raw SHA/interpreter` are bound "从 committed tree". The first three are derivable from the committed Git tree; the interpreter is not.

### Prior HIGH-2 — CPU/static source would have needed modification before real execution: CLOSED

The remediation freezes one production dependency-injection seam for Git transaction, root-FD opener and evidence sink. CPU/static tests bind temporary synthetic implementations; future real execution binds approved real Git/FD/evidence-directory dependencies to the same unchanged executor source. Evidence emission also goes through the same injected sink rather than a test-only in-memory-only code path. This satisfies the prior acceptance condition that switching from synthetic fixtures to approved real execution must not require changing the reviewed executor blob.

## 3. Finding

### HIGH-1 — Design / Authority — interpreter identity is incorrectly described as derivable from the committed Git tree

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md:8`

The design states that concrete `path/Git blob/raw SHA/interpreter` will be bound in the CPU/static implementation formal root/closure "从 committed tree". A Git tree can independently bind the executor/test paths, blob OIDs and raw bytes, but it cannot establish the actual Python interpreter identity used by CPU/static closure or by a later controlled execution. The same design still treats interpreter drift as a fail-before-source-open condition, so leaving its authority source undefined creates two incompatible readings: either the interpreter is falsely treated as Git-tree-derived, or it is supplied from some unspecified runtime/caller source.

This matters because the CPU/static test interpreter and the later approved real-execution interpreter need not be the same executable. Binding the former as if it were part of the implementation formal pair would incorrectly reject a legitimate later approved interpreter; accepting an arbitrary later interpreter would weaken the frozen drift check.

**Acceptance:** separate the two authorities explicitly. Bind executor/test `path + Git blob OID + raw SHA-256` from the committed CPU/static implementation formal root/tree. Define a separate exact interpreter-identity derivation and binding rule from the controlled execution environment (for example an exact executable identity record) and state at which reviewed stage it is frozen. CPU/static closure may record its test interpreter witness, but later real execution must independently satisfy the same interpreter-identity rule under controlled execution approval; neither value may be caller-default authority, and interpreter drift must still fail before source open.

## 4. Positive findings

- The impossible pre-implementation source-file binding point is otherwise corrected.
- The implementation formal pair, not request/ledger/handoff commits, is frozen as the later tool-source authority.
- One unchanged production DI code path now spans CPU/static synthetic fixtures and later approved real dependencies.
- Git transaction, root-FD opener and evidence sink are explicit injection seams; temporary fixture paths remain barred from project/source/checkpoint/cache roots.
- CPU/static scope continues to forbid real source/checkpoint/cache I/O, authority-root materialization, live collection/receipt/publication writes, network, child, GPU and training.
- Formal Gitlink is exact and the child commit is reachable.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_executor_implementation_design_v0.1.md:8)`

Current blockers: **1 HIGH**.  
Design/Authority blockers: **1**.  
Implementation blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 6. Scope

This verdict does not reopen the approved controlled-execution/evidence contracts or the now-closed production DI/evidence-sink seam. It does not authorize executor implementation, real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
