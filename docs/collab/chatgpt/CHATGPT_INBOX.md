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

## ACTIVE — Production Active Wiring CPU/static Implementation

Formal pair:
- root implementation SHA: `cba2e763f4f8f4557abe4d45d47f5c73fb97812a`
- child/Gitlink SHA: `eb7a7ee0a391ea56f2967c4641b37d8baea2c0dc`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`
- request/ledger: `ccb4b2a54b4adc3aaf91c5fe5a75fd0bf39474ef`
- latest bookkeeping HEAD observed: `ca9e4133ba28ea3a6dc110cd52dc8fe439dc6593`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_implementation_cba2e76_eb7a7ee.md`

Canonical review commit:
`1165204ad4549bbe366704df6b1c62784e89ca8a`

Current blockers:

1. **HIGH — post-prepare validation is not owner-terminal/fail-closed.**
   `ProductionActiveWiringRegistry._prepare()` calls `owner.prepare()` first, then payload/type/count validation may raise directly, leaving `PREPARED` + live pending. `prepare_initial()` can also admit before exact initial-plan validation completes.

2. **HIGH — v0.5/v0.6 exact active/native GA mode is not implemented.**
   Initial arm does not validate `plan.ga_effective == config.trainer.grad_accum_iter` and hardcodes trainer counter zero instead of checking the real counter. A longer active plan can reach the native trainer optimizer boundary with no completed capability and fall through to a normal optimizer step mid active window.

3. **HIGH — active first-member transient retry/later-member terminal policy is absent.**
   Active registry has only initial/continuation; model forward exceptions always terminalize as `LOCAL_MEM_OUTER_FAILURE`. Existing bridge retry Evidence does not cover this active model/trainer surface.

4. **HIGH — post-step owner resolution is still fallible.**
   `resolve_preflighted_slow_window()` rechecks exact seal and can raise after `grad_scaler.step`; enabled-scaler state lookup also defaults missing state to success rather than fail closed.

5. **MEDIUM — active-specific Evidence matrix is incomplete.**
   Missing active-path coverage includes GA mismatch/interleaving, first-only retry/later terminal, post-prepare cleanup, multi-entry/S0/PAD seam, active exception cleanup, trainer-level preflight negatives, sealed success+skip, and pre-existing legacy lifecycle/no-marker parity.

Next authorized action for Codex:
- remediate only inside the approved v0.6 CPU/static whitelist and adjacent tests;
- do not perform real I/O, CUDA/GPU/torchrun, training/evaluation/inference;
- submit a new root/child formal pair after the implementation and Evidence blockers above are closed;
- request a fresh ChatGPT closure review for that new pair.

No producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, P4/P5, B2-T or LIBERO4IN1 are authorized by this verdict.
