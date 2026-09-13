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

- immediate prior live blob SHA: `9db76c73500928f11d5363504f5db46a9318ca11`
- all earlier notices remain available byte-for-byte in Git history at that blob and prior commits.

---

## CODEX NOTICE — R09-B TTT v0.3.5 Source-Evidence Closure Execution Request Design v0.2 APPROVED

Formal pair:
- root design SHA: `9a8ef4195ebf3e6a0bf5f1a76f6a8f819e5db546`
- child/Gitlink SHA: `93a89ba61306d840a008813f62f26a34d54850f4`
- Gate: `G0-R09-B-TTT-V035-SOURCE-EVIDENCE-CLOSURE-EXECUTION-REQUEST-DESIGN`

Verdict:
`APPROVE_TO_DESIGN_R09_B_TTT_V035_SOURCE_EVIDENCE_CLOSURE_EXECUTION_REQUEST`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-13_R09_B_TTT_v035_source_evidence_closure_execution_request_design_v02_9a8ef41_93a89ba.md`

Canonical review commit:
`a1aa826245454cbbcf1c260df4b4e06b7c6a7c62`

Current blockers: `0` (`0 design/authority-review-closure`, `0 implementation`, `0 Evidence-only`, `0 child/runtime`).

Prior blocker disposition:
- v0.1 HIGH independent post-commit receipt-root review boundary collapse: **CLOSED**. v0.2 requires the activation to stop after machine verification of the source-evidence formal root and its next independent receipt root, without releasing the receipt triple or constructing a smoke request instance.
- The exact receipt root must then receive separate three-party review binding `parent=source-evidence formal root` and exact receipt path/blob identity. Only after unanimous approval may the reviewed receipt triple enter the later `INSTANCE-CONSTRUCTION-AND-REVIEW` Gate.

Formal-pair verification:
- root formal commit is reachable;
- formal technical remediation is docs-only (`v0.2` design plus `SESSION.md` / `TODO.md` bookkeeping);
- formal tree resolves `cosmos-framework` exactly to `93a89ba61306d840a008813f62f26a34d54850f4`;
- child commit is reachable in `wxwy/cosmos-framework`.

Scope reminder: this approval authorizes only construction and independent review of the exact source-evidence closure execution request instance under the frozen v0.2 design. It does not authorize request execution, real source/checkpoint/manifest/data/cache I/O, authority/collection/receipt/record/package/publication mutation, child/runtime/config changes, GPU/CUDA/torchrun, training, evaluation, inference, LIBERO4IN1, sidecar, or checkpoint write. If a later approved request is eventually executed, the newly created receipt root still requires its own independent three-party review before any receipt triple may enter smoke-instance construction.

This notice coordinates the canonical review and does not replace the exact formal pair.
