# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Controlled Execution CPU/static Implementation cumulative remediation

**Date:** 2026-09-12  
**Formal root:** `1db0d539fd3d52fa7d521962a47204b578e0f94f`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CONTROLLED-EXECUTION-IMPLEMENTATION-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current cumulative CPU/static implementation remediation request for this Gate.
- Independently verified formal root `1db0d539fd3d52fa7d521962a47204b578e0f94f` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental baseline is first rejected implementation pair `fb9c5e04e811865247e2ed44072af59acc8b93c9` / same child. Relative to it, the technical remediation remains confined to the approved two implementation files `tools/psm_wma/immutable_source_collection.py` and `tools/psm_wma/test_immutable_source_collection.py` plus review/session bookkeeping; child/runtime are unchanged.
- I reviewed the cumulative formal-tree source rather than relying on the stated `26/26` unittest result.

## 2. Prior HIGH closure

The first implementation review had five broad HIGHs. Their main bodies are substantially remediated:

- canonical `immutable_source_collection_execution_evidence_v1` outer/nested ABI, phase/nullability, digest verification and PASS/FAIL shapes now exist;
- seven-field authority tuple / four-field lineage checks, authority blob/raw-byte verification and Gitlink checks now exist;
- source reads now use one opened handle with stat/read/rewind/read/stat equality and close-on-failure semantics;
- candidate canonical derivation, same-activation typed one-shot handoff and handoff digest verification now exist;
- isolated preflight, five-path collection commit, one-path receipt commit, committed-tree relookup, post-checks, rollback and `ROLLBACK_INCOMPLETE` paths now exist.

The latest remediation also deep-copies retained in-memory evidence and rolls the Git transaction back when a PASS evidence sink rejects before confirmed completion.

Three production-contract defects remain.

## 3. Findings

### HIGH-1 — Design / Authority — execution-authority validation implements “entire tree has two paths” instead of the frozen two-path delta

**Location:** `tools/psm_wma/immutable_source_collection.py:582`

The approved controlled-execution design freezes an execution-authority **commit whose parent is the reviewed authority formal root and whose delta is exactly the two fixed selection/config paths**. The current implementation instead does:

`if set(tree) != {SELECTION_PATH, COLLECTION_PATHS[1]}: FAIL`

and the post-check repeats equality against a two-entry `expected_tree`.

`GitTransaction.tree_entries()` is used elsewhere as the full committed tree: preflight starts from `tree_entries(parent)`, collection commits preserve the parent tree, and receipt commits preserve the collection tree. Therefore, for a real authority commit parented by the formal repository root, the committed tree necessarily contains the inherited parent tree plus the two-path delta. Requiring the whole tree to contain only two entries either rejects every valid real authority root or would only pass a commit that deleted the inherited repository, which violates the frozen materialization transaction.

**Acceptance:** validate the authority commit exactly as a two-path delta over `authority_root_revision^`: parent equals `authority_approval_formal_root_revision`; both fixed paths resolve to the bound blob OIDs/raw bytes/schemas; every inherited parent-tree entry remains byte/object-identical; and no other path is added/modified/deleted. The post-check must use the same full-tree/delta rule. Keep all checks before source open.

### HIGH-2 — Evidence / Transaction — `EvidenceSink.emit()` has no atomic/receipt semantics, so “persist PASS then raise” can leave a stale valid PASS after rollback

**Location:** `tools/psm_wma/immutable_source_collection.py:806`

The latest code correctly handles a sink that rejects before storing the PASS: it rolls the target/index/worktree snapshot back and returns `EVIDENCE_SINK_FAILED` (or `ROLLBACK_INCOMPLETE`). But the injected `EvidenceSink` contract is only `emit(record) -> None`; the executor cannot distinguish “nothing was persisted” from “the canonical PASS was persisted and then the sink raised”.

If a real controlled-directory sink writes the PASS durably/visibly and then raises (fsync/rename/ack failure, wrapper failure after write, etc.), this code rolls the Git transaction back while the previously persisted PASS remains validly signed and says collection/receipt/post-checks completed. That is exactly a stale-success witness for a state the executor has just undone. The current tests cover only a rejecting sink that verifies and raises without persisting; they do not cover persist-then-raise.

**Acceptance:** freeze and implement one non-ambiguous evidence commit protocol before closure. Either (a) `emit` is an explicitly atomic sink operation whose contract guarantees an exception implies no visible/durable record, with a CPU/static witness that injects partial-write/after-write failures, or (b) use a two-phase sink/receipt/abort capability so a PASS becomes visible/accepted only after the executor receives a durable commit receipt and can revoke/mark invalid on rollback. No path may leave an accepted canonical PASS after the Git transaction is rolled back.

### HIGH-3 — Transaction / Evidence — rollback uncertainty can lose the mandated `ROLLBACK_INCOMPLETE` fail-stop when the post-failure snapshot itself is unreadable

**Location:** `tools/psm_wma/immutable_source_collection.py:750`

Inside `_commit_candidates`, rollback failure enters the nested exception handler and immediately calls `after = git.snapshot()` before setting a rollback record and before raising `CollectionError("ROLLBACK_INCOMPLETE")`. If `snapshot()` itself fails or returns an invalid/unreadable state — precisely one of the uncertainty cases the frozen contract classifies as `ROLLBACK_INCOMPLETE` — this second exception escapes instead. The outer handler then derives a generic `<PHASE>_FAILED`, and canonical live-failure evidence can no longer satisfy the required rollback witness.

The frozen contract is explicit that rollback **or HEAD/index/worktree verification uncertainty** must become the single fail-stop `ROLLBACK_INCOMPLETE`, prohibit authority/autoretry/downstream, and must not be reclassified as an ordinary phase failure. A broken snapshot re-read is therefore not an optional diagnostic edge.

**Acceptance:** make rollback verification itself a fail-stop boundary. Any exception or invalidity while restoring or re-reading target ref / HEAD / index / worktree must deterministically surface `ROLLBACK_INCOMPLETE` and must never fall back to `<PHASE>_FAILED`. Because the exact execution-evidence ABI cannot invent an unreadable `after_snapshot`, define one reviewed fail-stop evidence/diagnostic handling rule for this unavailable-snapshot case that cannot be mistaken for ordinary canonical PASS/FAIL authority; add a direct CPU/static witness for `rollback()` failure plus `snapshot()` failure/invalidity.

## 4. Positive findings

- The evidence ABI is no longer the earlier six-key toy record; exact outer keys, canonical digest and phase reachability are substantially implemented.
- Source-read handling now models a same opened handle, pre/mid/post stat stability, rewind, second complete hash and guaranteed close.
- Candidate derivation matches the frozen input-descriptor → manifest → identifier → descriptor → collection chain, with exact canonical config bytes.
- One-shot handoff is same-activation, non-constructible through its public constructor, non-serializable, single-consume and re-derives bytes/digests on take.
- Collection/receipt transaction code now has isolated preflight, committed-tree lookup/recompute, exact five-plus-one path checks, parent checks, post-check ordering and rollback.
- The latest evidence-retention deep copy closes alias pollution in `MemoryEvidenceSink`.
- No real source/checkpoint/cache/network/GPU/model/training operation is introduced in this CPU/static implementation pair.

## 5. Formal verdict

`REQUEST_CHANGES(tools/psm_wma/immutable_source_collection.py:582)`

Current blockers: **3 HIGH**.  
Design/Authority blockers: **1**.  
Transaction/Evidence blockers: **2**.  
Production blockers: **0** beyond those contract defects.

## 6. Scope

This verdict does not reopen already-closed evidence schema design, source-read FD design, candidate derivation design, or the docs-only controlled-execution design. It only states that the current CPU/static implementation is not yet a faithful implementation of those frozen contracts.

It does not authorize real source selection/read/hash, authority-root materialization, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler/scaler step, sidecar, training, evaluation, inference or LIBERO4IN1.
