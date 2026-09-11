# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- After every actual new ChatGPT technical review, this Inbox MUST be updated with the exact formal pair, Gate, verdict, canonical review path, and review commit SHA.
- Codex should run `git fetch origin V2` before concluding that no ChatGPT review exists.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review; persistence/notification repair is allowed without changing the technical verdict.
- Historical coordination notices remain available in Git history; the latest notice below supersedes older action-required notices for the same Gate.

## Live rollover

- immediate prior live blob SHA: `1edbf8e36d7b5b9f18db9257879390490e9f35ca`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — Source-evidence Producer / Closure Design derived-only witness remediation APPROVED

Formal pair:
- root design SHA: `1d8f103e1dcf119ac8e90abbcbcde0eaced0bb95`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-PRODUCER-CLOSURE-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_PRODUCER_CLOSURE`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-12_R09_B_TTT_v035_source_evidence_producer_closure_design_1d8f103_93a89ba.md`

Canonical review commit:
`ad11a5accc1e88d53b64db83e4893062796d6c13`

Current blockers: `0`. Design/Authority `0`; Production `0`; Evidence-only `0`.

Closure:
- the final stale witness Git-blob requirement is removed;
- Section 3 now uses exactly one witness authority model: derived-only canonical bytes/SHA-256 reconstructed from reviewed record/config/descriptor/package bindings;
- no witness Git path/blob/OID is declared, retained, or accepted as authority;
- the non-circular collection-root -> collection-receipt-root model, resolved config authority, separate next-root post-commit receipt, staged Gitlink/publication exclusions, isolated preflight, rollback and `ROLLBACK_INCOMPLETE` semantics remain intact;
- formal root resolves exactly to the requested reachable child/Gitlink and child is unchanged.

Authorized next action only: proceed with the independently reviewed immutable-source collection design/execution/closure progression frozen by this design, before any source-evidence controlled-write design.

Still not authorized: real immutable-source collection, source-evidence record/package/witness creation or write, publication materialization, real root source-audit execution, child/runtime modification, real checkpoint/data/cache I/O, DCP, CUDA/GPU, `torchrun`, model forward/loss/backward, optimizer/scheduler step, sidecar, training, evaluation, inference or LIBERO4IN1.

This notice is coordination only and does not replace the formal pair or canonical review.
