# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Closure Design v0.1

**Date:** 2026-09-12  
**Formal root:** `ee4ab4ab4ad6dd8b84aa354afc51ac47aa1c0474`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CLOSURE-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`.
- Independently verified formal root `ee4ab4ab4ad6dd8b84aa354afc51ac47aa1c0474` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Prerequisite Immutable Source Collection Execution Design is approved at `1b658bfbf7068a05dc6b409414ba2c98b7b03cc8` / `93a89ba61306d840a008813f62f26a34d54850f4` with `APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_EXECUTION`.
- Incremental technical scope is docs-only: the new closure design plus bookkeeping. No real source read/hash, collection/receipt mutation, publication, audit, child/runtime, GPU or training action is authorized here.

## 2. Positive findings

- The design preserves the existing downstream source-evidence controlled-write / record / post-commit receipt / publication / read-only audit sequence.
- Authority-root selection/config lookup is external to the collection/receipt payload and remains non-circular.
- Collection-root -> receipt-root ordering, exact fixed-path allowlists, post-commit tree lookup and receipt-parent checks are correctly fail-closed.
- Live failure handling retains snapshot rollback and `ROLLBACK_INCOMPLETE`; no push/publication/downstream consumption is allowed before both roots and all post-checks succeed.

## 3. Findings

### HIGH-1 — Design/Authority — preflight source-read output is not immutably bound to the candidate blobs accepted by closure

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_closure_design_v0.1.md:23`

The closure accepts the candidate input-descriptor / manifest / identifier / checkpoint-descriptor / collection / config bytes as explicit inputs, explicitly does not re-read the source root, and explicitly says preflight candidates or prior process memory are not authority. It then proves only that the supplied candidate bytes form a self-consistent derivation chain.

That leaves the source-read provenance severed: after a valid preflight, a caller can replace the candidate set with a different internally self-consistent set and closure has no frozen value that ties those bytes to the approved same-FD source reads. Recomputing canonical JSON and hashes detects corruption inside the supplied chain, but cannot prove that this chain is the one produced by the approved source selection/read.

**Acceptance:** freeze an exact non-substitutable preflight-to-closure handoff. At minimum it must bind the reviewed execution-authority tuple plus the ordered source-entry `(ordinal, byte_length, sha256)` results and the exact candidate canonical blob SHA-256 values (and/or one canonical candidate-tree/receipt digest that uniquely commits to all of them). The handoff must be produced by the approved preflight before the source-read phase is relinquished and closure must require exact equality to it; caller/environment/current-memory replacement must fail. An equivalently strong same-run typed one-shot handoff or immutable evidence artifact is acceptable. Alternatively, closure may independently re-read/hash the reviewed source selection, but the current design explicitly chooses not to do that.

### HIGH-2 — Design/Authority — collection target base revision / Gitlink lineage is caller-selected

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_closure_design_v0.1.md:24`

The future collection target ref, index and worktree snapshot are explicit closure inputs. Section 3 requires the collection commit parent to equal that snapshot `HEAD`, but no reviewed expected target ref/base revision or expected `cosmos-framework` Gitlink is bound before mutation.

Therefore an otherwise valid five-artifact collection and receipt can be committed on an arbitrary reachable root history — including one carrying a different child Gitlink — while still satisfying the rule that the closure delta itself contains no Gitlink change. The staged allowlist proves what this transaction changed, not that it started from the reviewed production lineage.

**Acceptance:** the future real controlled-execution approval must bind one exact target ref/base root revision and the exact expected child/Gitlink. Before isolated preflight and again before live mutation, closure must prove `target HEAD == expected_base_revision`, that the base root tree resolves `cosmos-framework` exactly to the reviewed child SHA, and that the collection-root parent is the bound base revision (or a precisely frozen reviewed successor rule if intervening bookkeeping commits are intentionally permitted). Any ref/base/Gitlink drift must fail before mutation. The execution-authority root's required parent relation must likewise be checked from Git, not inferred from the tuple alone.

## 4. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_immutable_source_collection_closure_design_v0.1.md:23)`

Current blockers: **2 HIGH**.  
Design/Authority blockers: **2**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This verdict does not authorize real source selection/read/hash, execution-authority creation, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root source audit, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1. Remediation should remain docs-only for this Gate.
