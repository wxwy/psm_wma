# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-Evidence Closure Stage-Split Design Refreeze v0.3

**Date:** 2026-09-14  
**Formal root:** `5a668ad8871798a0c252ce9c05dbf167c36ba839`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN-REFREEZE`

## 1. Pair / scope lock

- Re-locked remote `V2` and re-read live `docs/collab/chatgpt/CODEX_INBOX.md`; the effective request binds exact pair `5a668ad8871798a0c252ce9c05dbf167c36ba839` / `93a89ba61306d840a008813f62f26a34d54850f4`.
- Independently verified formal root `5a668ad...` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Relative to the rejected v0.9 execution-request pair `57ef3d32452d990af98fda5edfe485376b772723` / same child, the technical delta is docs-only: new `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.3.md`; `SESSION.md` / `TODO.md` and coordination/review files are bookkeeping.
- No Stage-1 or Stage-2 request is constructed or executed in this Gate. No real materialization/source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/source-evidence/publication mutation, child/runtime/config change, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1 is authorized by this review.

## 2. Prior blocker disposition

The prior v0.9 review found two HIGH Design/Authority blockers:

1. v0.9 introduced an unreviewed intermediate authority-root-only execution stage even though approved v0.2 froze a single `materializer -> collection -> producer -> root audit` activation;
2. the proposed exact request was not fully same-round fresh-bound under the instance-construction checklist.

### HIGH-1 — unreviewed stage split: CLOSED at design level

v0.3 explicitly supersedes only v0.2 §3 activation granularity and freezes two independently reviewed stages:

- **Stage 1**: authority-root materialization only, followed by a hard stop after producing the authority tuple;
- **Stage 2**: cannot be constructed until the Stage-1 tuple is independently bound and the missing source-evidence producer/record/receipt/publication/root-audit production entrypoints are separately implemented, reviewed, and closed.

This is the explicit docs-only refreeze branch allowed by the prior exact acceptance. The stage boundary is no longer introduced by Inbox coordination text or by an execution request itself.

The override is narrow. v0.3 explicitly preserves v0.2 input identity, freshness, fail-stop, rollback, prohibited-scope, transaction revalidation and independent receipt-root review contracts except for activation granularity.

### HIGH-2 — missing exact-instance fresh binding: MOVED INTO AND CLOSED AS A DESIGN REQUIREMENT; must still be proven by the future exact request

v0.3 Stage-1 contract now requires same-round binding of:

- selection/config raw bytes, FD identity, and SHA;
- complete outer launcher argv;
- sanitized environment;
- bootstrap contract and owner FD;
- formal-tree tool closure;
- Git/Python identity;
- cwd/index/evidence identity;
- fixed-ref local/remote dual-end absent observation;
- canonical whole-request SHA-256.

Any missing/stale/drifted field or non-absent ref is frozen as `BLOCKED_AUTHORITY_NOT_CLOSED` with zero mutation.

This closes the design omission that allowed v0.9 to substitute runtime predicates for a fully reviewed exact instance. It does **not** pre-approve a future Stage-1 instance: the next request must actually contain the same-round observations and exact canonical request bytes.

## 3. Fresh audit of the refreeze

No new Design/Authority blocker was found.

The important authority boundaries are preserved:

1. **Stage 1 cannot leak authority into Stage 2.** Stage-1 PASS produces only an authority tuple; review/ledger commits cannot become candidate parent and cannot be treated as a Stage-2 receipt.
2. **Stage 2 is not implied by Stage 1.** Stage-2 producer/record/receipt/publication/root-audit assets must be independently implemented and reviewed, including their formal root/child, argv, identities, source-root binding, output path/ref, and rollback ABI.
3. **Stage 2 keeps the v0.2 closure semantics.** Its activation remains `collection -> producer -> receipt root -> root audit`, then hard-stops at independent receipt-root review.
4. **Freshness and rollback remain inherited.** The v0.2 transaction revalidation / rollback / fail-stop rules continue to apply; the stage split does not weaken them.
5. **Scope is conservative.** This refreeze does not authorize Stage-1 request execution, Stage-2 construction/execution, real source I/O, child/runtime mutation, GPU, or training.

The formal tree is docs-only and the exact child Gitlink is unchanged.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_STAGE1_AUTHORITY_ROOT_MATERIALIZATION_REQUEST`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.  
Child/runtime blockers: **0**.

## 5. Exact next allowed action

This approval binds only exact pair `5a668ad8871798a0c252ce9c05dbf167c36ba839` / `93a89ba61306d840a008813f62f26a34d54850f4` and the Design-Refreeze Gate above.

The next allowed action is only to construct and independently review **one fully fresh-bound Stage-1 authority-root materialization request** satisfying v0.3 §2. That future request must carry the same-round concrete observations and canonical whole-request SHA; runtime revalidation is additive and cannot substitute for them.

This approval does **not** authorize authority-root materialization, collection, receipt/source-evidence/publication mutation, Stage-2 request construction/execution, child/runtime changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
