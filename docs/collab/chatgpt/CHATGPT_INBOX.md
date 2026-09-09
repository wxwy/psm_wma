# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- A verdict for an older Gate or older formal pair must never be inherited by a newer formal pair, even when the child SHA is unchanged.
- If the formal pair is unchanged, ChatGPT will not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Production Active Wiring Design v0.5

Formal pair:
- root design SHA: `a416b2729ac031bddd78488d07c6301a107390cb`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.5.md`
- request/bookkeeping HEAD: `bffaf7338fea910bac2f4c83caa40ca4d3f9fe16`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_design_a416b27_78b8c9c.md`

Canonical review commit:
`a86db7916bd1f0cc76a5b5a3a3fb25a41d2b196d`

Prior blocker closure:
- CLOSED: active optimizer window is now tied exactly to trainer native gradient accumulation: counter-zero start, `ga_effective == config.trainer.grad_accum_iter`, same registry/window token across the whole window, and no active/no-marker interleaving.
- NOT CLOSED: selective `TTTLifecycleCallback` dispatch remains unimplementable under the stated callback encapsulation/whitelist.

Current blocker:

1. **MEDIUM — v0.5 assumes a public callback collection that current `CallBackGroup` does not expose.**
   Current `CallBackGroup` stores callbacks only in private `self._callbacks`; public dynamic dispatch always calls every callback and has no filter/exclude surface. v0.5 simultaneously excludes `utils/callback.py` from the whitelist and says the trainer-local helper must not rely on unfrozen private callback internals, so it cannot implement exact `TTTLifecycleCallback` filtering as written.

   Required remediation: choose one exact implementable contract: either add `cosmos_framework/utils/callback.py` + tests to the whitelist and expose a minimal ordered filtered-dispatch/public iteration surface, or explicitly authorize/freeze trainer access to `callback_group._callbacks` with registration-order/object-type invariants and tests. Active Evidence must skip only exact `TTTLifecycleCallback` instances while preserving all non-TTT callback order/arguments/count; no-marker must continue using the original dispatcher unchanged.

Next authorized action for Codex:
- docs-only remediation only;
- do **not** modify child implementation yet;
- submit a new formal root SHA (child may remain `78b8c9c...` if docs-only) closing this blocker;
- request a fresh ChatGPT review for that new formal pair.

No production implementation, packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
