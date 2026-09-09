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

## ACTIVE — Production Active Wiring Design v0.4

Formal pair:
- root design SHA: `edea9f9ed199d788c9a3b31b474aa665b503aa93`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.4.md`
- request/bookkeeping HEAD: `9b34a15b360c0635d599804303b5d14270c89f6c`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_design_edea9f9_78b8c9c.md`

Canonical review commit:
`b7792f993b62bb1bd96edc55a1b7ea002643eff2`

Prior blocker closure:
- CLOSED: exact trainer/model runtime registry binding and trainer pre-forward shallow runtime-capability injection.
- CLOSED: owner-created slow-window preflight/sealed deterministic resolution surface; `canonical_segment_runtime.py` is now in the whitelist.
- CLOSED IN INTENT: active step isolates a pre-existing legacy `TTTLifecycle` and requires a zero-call spy fixture.

Current blockers:

1. **HIGH — active optimizer-window mode is not yet tied to the trainer's existing fixed gradient-accumulation boundary.**
   v0.4 only requires final completion at `grad_accum_iter + 1 == ga_effective`, while the actual trainer steps at `grad_accum_iter == config.trainer.grad_accum_iter`. It also allows normal/no-marker pass-through when no active authority is present without freezing what happens if an active window is already open.

   Required remediation: freeze one exact mode. Minimal safe form: active window starts only at `grad_accum_iter==0`; require `initial_plan.ga_effective == config.trainer.grad_accum_iter`; every accumulation microbatch until exact completion must be active and share the same registry/`ga_window_token`; active/no-marker interleaving and active start mid normal window fail before model forward/backward with zero owner/optimizer mutation. Alternatively explicitly supersede the trainer optimizer trigger for active mode with exact counter semantics. Add CPU/static mismatch/interleaving fixtures.

2. **MEDIUM — selective skipping of only `TTTLifecycleCallback` has no supported dispatcher API under the current whitelist.**
   Current `CallBackGroup` invokes every callback and exposes no exclude/filter API. v0.4 requires all non-TTT callbacks to keep the same order while only `TTTLifecycleCallback` is skipped, but `utils/callback.py` is not whitelisted.

   Required remediation: either add `cosmos_framework/utils/callback.py`/adjacent tests to the whitelist and define filtered dispatch, or explicitly freeze a trainer-local filtered dispatcher that excludes exact `TTTLifecycleCallback` instances while preserving all other callback order/arguments. Add active/no-marker callback-order Evidence.

Next authorized action for Codex:
- docs-only remediation only;
- do **not** modify child implementation yet;
- submit a new formal root SHA (child may remain `78b8c9c...` if docs-only) closing the blockers above;
- request a fresh ChatGPT review for that new formal pair.

No production implementation, packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
