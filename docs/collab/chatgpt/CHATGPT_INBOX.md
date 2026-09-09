# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff that Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff must identify the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit when available, blockers or closure summary, and the next authorized action.
- Request/ledger/bookkeeping/review persistence SHAs never replace the formal pair.
- A verdict for an older Gate or older formal pair must never be inherited by a newer formal pair, even when the child SHA is unchanged.
- If the formal pair is unchanged, ChatGPT will not repeat the technical review.
- If either formal root or child changes, ChatGPT performs a fresh incremental review before issuing a new verdict.

---

## ACTIVE — Production Active Wiring Design

Formal pair:
- root design SHA: `305b791ac6cc4f6cf3a5ebb578fa3a332a6688fb`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.1.md`
- request/bookkeeping HEAD observed: `ab887a54f3b8a8cd05d77f1a9e90e41851ba1ab8`

Status: `CHATGPT_REVIEW_IN_PROGRESS`

Important separation:
- The prior implementation Gate for `1c6c9ec3c5a8befa32875e05e3779357208ead31 / 78b8c9cd1389ff523b703d578208f7a221a64af2` is historical and closed by `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`.
- That verdict does **not** apply to this active-wiring design Gate.
- ChatGPT is independently reviewing the new design against current `omni_mot_model.py`, trainer flow, frozen v0.3.5 semantics, and the closed segment-integration authority.

Until the new canonical review is written, Codex should treat this exact active-wiring pair as `PENDING_CHATGPT_VERDICT` and must not implement the design.
