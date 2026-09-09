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

## ACTIVE — Production Active Wiring Design v0.6

Formal pair:
- root design SHA: `721b4100624a37edbdd75bb555515b7d7e67c8e1`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`
- request/bookkeeping HEAD: `7abf307a331d2e2001ded68f7098bb1c1713e4e3`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_PRODUCTION_ACTIVE_WIRING_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_design_721b410_78b8c9c.md`

Canonical review commit:
`a7ad3d586b7195e6fa2c348253bd7cfd24bc38ac`

Closure:
- CLOSED: active/native GA window is exactly bound to trainer accumulation and no-marker interleaving is forbidden while an active token is open.
- CLOSED: trainer-local callback filtering is now explicitly implementable via a narrowly scoped read-only access to `callback_group._callbacks`; exact-class `TTTLifecycleCallback` exclusion, registration order, arguments, callback identity, subclass behavior, and no-marker parity are all frozen.
- CLOSED: registry binding, pre-forward prepared injection, owner sealed preflight/resolve, one batched native seam, first-member-only retry, and legacy lifecycle isolation remain intact.

Current blockers: none.

Next authorized action for Codex:
- implement only the v0.6 CPU/static whitelist: `production_active_wiring.py`, `canonical_segment_runtime.py`, `omni_mot_model.py`, `trainer/__init__.py`, `production_segment_bridge.py`, and adjacent CPU/static tests;
- `utils/callback.py` remains out of scope;
- after implementation, submit a new formal root/child pair for fresh ChatGPT closure review.

No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this design approval.
