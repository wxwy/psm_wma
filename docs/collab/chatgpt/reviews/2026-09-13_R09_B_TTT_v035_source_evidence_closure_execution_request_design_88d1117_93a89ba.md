# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-Evidence Closure Execution Request Design v0.1

**Date:** 2026-09-13  
**Formal root:** `88d11170db2cd058567af175c69152231917360a`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN`

## 1. Pair / incremental scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md` request ledger.
- Independently verified formal root `88d11170db2cd058567af175c69152231917360a` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- This is a new formal pair relative to the previously reviewed request-design pair, so a fresh incremental Design Gate review is required.
- Formal technical delta is root docs-only: `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.1.md` plus task/session bookkeeping; child/runtime is unchanged.
- This review does not execute real source/checkpoint/manifest/data/cache I/O, collection/receipt/publication, child/runtime modification, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.

## 2. Authority chain checked

Relevant prior frozen authority includes:

1. `G0-R09-B-TTT-V035-IMMUTABLE-SOURCE-COLLECTION-CLOSURE-DESIGN`, formal root `5f6741ca0bfb61ca0e55fae95709c891fa5c5520`, whose approved review keeps the collection root / receipt root transaction non-circular and preserves later source-evidence controlled write, post-commit receipt, publication materializer/verifier, and read-only root audit as separate required stages.
2. `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`, formal root `1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95`, whose approved contract freezes the post-commit closure receipt at `docs/build/PSM-WMA_source_evidence_postcommit_closure_receipt_v1.json` in a **next independent receipt root**, explicitly outside the source-evidence record formal root. That receipt root must be independently reviewed with `parent=source-evidence formal root`; downstream materialization may consume only the reviewed receipt formal-root/path/blob identity.

No later authority located in the reviewed chain explicitly supersedes that independent receipt-root review requirement.

## 3. Current blocker

### HIGH — §3 collapses the frozen independent post-commit receipt-root review boundary

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.1.md`, §1 / §3 / §4.

**Root cause:** the new design states that one future request runs as a single activation through materializer → collection/receipt → source-evidence producer/publication verifier → root audit, and then releases `(receipt_root_revision, receipt_path, receipt_blob_native_oid)` to the downstream smoke-instance Gate. It intentionally says no additional horizontal provenance Gate is introduced. However, the inherited approved Source-evidence Producer / Closure Design freezes a stronger authority boundary: the post-commit receipt must live in a **next independent receipt root**, and that exact receipt root must itself receive independent review binding its parent to the source-evidence formal root before downstream materialization consumes its identity.

The exact future receipt-root SHA cannot exist at request-instance review time, so reviewing the request before execution cannot substitute for the required post-creation independent receipt-root review. A machine `publication verifier` or `root audit` likewise does not substitute for the frozen reviewer authority.

**Violated frozen contract:** later design may only supersede an earlier contract when it explicitly says so. This v0.1 says it follows the already-approved source-evidence producer/record/receipt contract; it does not explicitly refreeze or supersede the independent receipt-root review boundary. Therefore the single-activation direct handoff is inconsistent with the inherited authority chain.

**Why current design evidence does not close it:** pre-bind checks, post-commit lookup, rollback/fail-stop, exact request-instance review, publication verification, and root audit can prove integrity of bytes/lineage, but none creates the missing independent reviewer approval for the newly materialized receipt root.

**Exact acceptance:** revise the design so that, after the source-evidence formal root and next receipt root are materialized and machine-verified, execution stops without releasing the receipt triple downstream; require a separate independent review of the exact receipt root that binds `parent=source-evidence formal root` and the exact receipt path/blob identity, and only after that approval may the reviewed receipt triple enter `INSTANCE-CONSTRUCTION-AND-REVIEW`. Alternatively, an explicit later refreeze may supersede the old independent-review rule, but that refreeze must state the supersession and freeze an equivalent replacement authority boundary; the present document does neither.

## 4. Other reviewed properties

Apart from the blocker above, the current docs-only design appropriately keeps this Gate non-executing, binds future request inputs before source open, prohibits worktree/environment/default-path completion, requires pre-live-write authority revalidation, retains rollback / `ROLLBACK_INCOMPLETE` fail-stop semantics, and does not itself authorize GPU or training.

No additional blocker is required for the current pair.

## 5. Formal verdict

`REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_source_evidence_closure_execution_request_design_v0.1.md:§3)`

Current blockers: **1 HIGH**.  
Design/Authority blockers: **1**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 6. Scope reminder

This verdict binds only formal pair `88d11170db2cd058567af175c69152231917360a` / `93a89ba61306d840a008813f62f26a34d54850f4` and this exact Design Gate. It does not authorize construction or execution of the future closure request, real source/checkpoint/data/cache I/O, collection/receipt/publication, child/runtime changes, GPU/CUDA/torchrun, training, evaluation, inference, or LIBERO4IN1.
