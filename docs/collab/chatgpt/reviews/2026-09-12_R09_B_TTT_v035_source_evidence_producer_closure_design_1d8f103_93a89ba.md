# ChatGPT Independent Review — R09-B TTT v0.3.5 Source-evidence Producer / Closure Design derived-only witness remediation

**Date:** 2026-09-12  
**Formal root:** `1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95`  
**Formal child/Gitlink:** `93a89ba61306d840a008813f62f26a34d54850f4`  
**Gate:** `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

## 1. Pair / incremental scope

- Re-locked remote `V2` and re-read the live `docs/collab/chatgpt/CODEX_INBOX.md` request ledger.
- Independently verified formal root `1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95` resolves `cosmos-framework` exactly to reachable child `93a89ba61306d840a008813f62f26a34d54850f4`.
- Incremental authority is prior rejected pair `f3a423c39020081b3ff34128328792af166ba09a` / `93a89ba61306d840a008813f62f26a34d54850f4` and review `docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_source_evidence_producer_closure_design_f3a423c_93a89ba.md`.
- Relative to that pair, the only technical design change is the stale witness-Git-blob sentence in Section 3; other intervening changes are review/request bookkeeping. Child/runtime is unchanged. No real collection/write/publication/audit/I-O/GPU/training action is authorized here.

## 2. Prior HIGH closure

### HIGH — Section 3 had mutually exclusive witness authority models: CLOSED

The stale sentence requiring witness raw-byte SHA-256 **and Git blob OID** to be externally recorded has been replaced. Section 3 now consistently freezes one authority model only:

- the witness is `derived-only`;
- its exact canonical bytes are deterministically reconstructed from the reviewed record/config/descriptor/package bindings;
- `input_witness_sha256` is recomputed from those canonical bytes;
- no witness Git path/blob/OID is declared, retained, or accepted as authority;
- the next-root post-commit closure receipt binds the formal source-evidence root, record path/blob/raw digest, package digest, witness digest, and config/descriptor digests, while remaining non-circular.

This is exactly the prior acceptance criterion. The already-correct non-circular collection-root -> collection-receipt-root model, resolved config authority, staged Gitlink/publication exclusions, isolated preflight, live rollback and `ROLLBACK_INCOMPLETE` fail-stop semantics remain intact.

## 3. Fresh audit

No new Design/Authority, Production, or Evidence-only blocker was found in the formal remediation.

The design remains internally consistent on the relevant authority chain:

1. immutable-source collection authority is established before any source-evidence controlled write;
2. collection provenance is externalized through a separate receipt root whose parent is the collection formal root;
3. resolved `canonical_model_config` is derived from reviewed fixed artifact bytes/digest rather than caller/environment/working-tree selection;
4. source-evidence record remains the inherited exact six-key object;
5. package/witness are generated only after the source-evidence formal root exists;
6. the witness is deterministic derived-only state, not a persisted Git object authority;
7. post-commit receipt lives in a separate next root and is the only accepted machine-readable binding for later materializer work.

## 4. Formal verdict

`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE`

Current blockers: **0**.  
Design/Authority blockers: **0**.  
Production blockers: **0**.  
Evidence-only blockers: **0**.

## 5. Scope / next allowed action

Approval closes only this docs-only Source-evidence Producer / Closure Design Gate. The next allowed work is the independently reviewed immutable-source collection design/execution/closure progression frozen by this design, followed later by the source-evidence controlled-write execution design. This approval does **not** authorize real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.
