# ChatGPT Independent Review — R09-B TTT v0.3.5 Immutable Source Collection Closure Design authority remediation

**Date:** 2026-09-12  
**Formal root:** `5f6741ca0bfb61ca0e55fae95709c891fa5c5520`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CLOSURE-DESIGN`

## 1. Pair / scope

- Re-locked remote `V2`, re-read the live `docs/collab/chatgpt/CODEX_INBOX.md`, and confirmed this exact pair is the current formal remediation request for the Gate.
- Independently verified formal root `5f6741ca0bfb61ca0e55fae95709c891fa5c5520` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is prior rejected pair `ee4ab4ab4ad6dd8b84aa354afc51ac47aa1c0474` / same child and its canonical review.
- Incremental technical scope is docs-only: the closure design is modified to bind preflight handoff and target lineage; child/runtime is unchanged. No real source I/O, collection/receipt mutation, source-evidence write, publication, audit, GPU or training action is authorized by this review.

## 2. Prior HIGH closure

### Prior HIGH-1 — preflight source-read output was replaceable before closure: CLOSED

The remediation replaces free-standing candidate raw-blob inputs with a same-activation, non-serializable, one-shot typed `immutable_source_collection_preflight_handoff_v1` produced only by the approved source-read preflight. The handoff binds the reviewed execution-authority tuple, ordered `(ordinal, byte_length, sha256)` source-entry results, each fixed candidate artifact path/schema/raw SHA-256, the candidate config raw SHA-256, and `candidate_handoff_sha256`. Restart, repeat consumption, cross-process handles, caller replacement, and post-read reconstruction are all fail-closed.

Closure consumes candidate raw blobs only from that one-shot handoff and must require every candidate byte/digest to match the bound handoff before independently recomputing the full input-descriptor -> manifest -> immutable-source-identifier -> checkpoint-descriptor -> collection-artifact chain. This provides the missing non-replaceable bridge from the approved same-FD source read to the bytes later committed by closure without re-reading the source root.

### Prior HIGH-2 — collection target lineage was caller-selectable: CLOSED

The future controlled-execution approval must now bind exact `(target_ref, expected_base_root_revision, expected_child_gitlink, authority_approval_formal_root_revision)`. Before source preflight and again before live mutation, the executor must recompute from Git objects that the target ref HEAD equals the expected base, the base tree resolves `cosmos-framework` exactly to the expected child Gitlink, and the reviewed execution-authority root's parent equals the approved authority formal root. The collection commit parent is frozen to `expected_base_root_revision`.

Thus a self-consistent five-path collection delta cannot be committed onto an unreviewed root lineage or a root carrying a different child Gitlink.

## 3. Fresh audit

- The two-root collection/receipt transaction remains non-circular: collection root first, receipt root second with exact parent=collection root.
- Candidate/preflight material remains non-authoritative until closure post-checks succeed; committed collection bytes are re-read from the committed collection tree rather than reused from candidate memory.
- The five-path collection allowlist and one-path receipt allowlist remain exact; Gitlink, Inbox, publication target, checkpoint/cache and training residue remain prohibited.
- Rollback and `ROLLBACK_INCOMPLETE` semantics remain fail-closed, and no push/publication/downstream consumption is allowed before both roots and all post-checks pass.
- Downstream source-evidence controlled write, post-commit receipt, publication materializer/verifier and read-only root audit remain separate required stages before GPU smoke.

No new Design/Authority, Production, or Evidence-only blocker was found in this remediation.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_IMMUTABLE_SOURCE_COLLECTION_CLOSURE`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope

This approval authorizes only the next independently reviewed real collection controlled-execution design/review required by the frozen progression. It does not authorize real source selection/read/hash, collection/receipt mutation, source-evidence record/package/witness creation or write, publication materialization, real root source audit, child/runtime modification, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
