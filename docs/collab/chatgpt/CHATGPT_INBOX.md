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

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_design_305b791_78b8c9c.md`

Canonical review commit:
`91dd1458a0c7ccc73b6df2a8f776f8e23b989322`

Important separation:
- The prior implementation Gate for `1c6c9ec3c5a8befa32875e05e3779357208ead31 / 78b8c9cd1389ff523b703d578208f7a221a64af2` is historical and closed by `APPROVE_TO_CLOSE_R09_B_TTT_V035_PRODUCTION_SEGMENT_INTEGRATION_CPU_STATIC`.
- That verdict does **not** apply to this active-wiring design Gate.

Current blockers:

1. **HIGH — native callback cardinality conflicts with the closed bridge contract.**
   v0.1 says `one native callback per gathered consumer`; the frozen contract is one **batched** native callback per GA member/microbatch over the complete gathered `(payloads, locals)` tuple. Multiple valid consumers must be entries in one model call; PAD is absent.

2. **HIGH — model/trainer/bridge split-phase authority is not frozen.**
   Current `production_segment_bridge.run_member` owns prepare -> native callback -> pure backward -> commit/finish, while current trainer performs model forward first and backward later. v0.1 asks model to execute the real native forward and trainer to call bridge pure-backward, but defines no exact graph-bearing capability/API between those phases. It also does not freeze the exact `OmniMoTModel.training_step` branch point that bypasses `_inject_local_history/_ttt_local_memory_tokens` before the legacy TTT lifecycle can run.

3. **HIGH — GA/GradScaler production clock and scaling are not frozen.**
   `GAWindowPlan` valid-consumer weighting already owns the GA scale; the Local-enabled real backward must use native GradScaler exactly once without a second `/grad_accum_iter`. The design must freeze one successful bridge member == one successful trainer accumulation microbatch, retry/terminal effects on `grad_accum_iter`, final completion alignment with the optimizer boundary, and exact scaler success/skip resolution ordering without `TTTLifecycle`.

Next authorized action for Codex:
- docs-only remediation of the active-wiring design;
- do **not** modify child implementation yet;
- submit a new formal root SHA (child may remain unchanged if docs-only) that closes all three blockers;
- request a fresh ChatGPT review for the new formal pair.

No production model/packer/dataset/config/checkpoint implementation, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
