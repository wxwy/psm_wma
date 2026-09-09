# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Production Active Wiring CPU/static Implementation closure follow-up

Formal pair:
- root implementation SHA: `5d548d97029302817efeaad49983a2a16883be6e`
- child/Gitlink SHA: `3b3d83c33b54a14d52ce54f97e920875f9b48e4e`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `f24599d92f7447064c7422a43575e38cec843d48` / `acb2bf2c8b4caf5a415b3eaaffa34edf9a514323`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`
- request/bookkeeping HEAD observed: `2433963a88509f618f16c38d9b9561e951a63cf7`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_production_active_wiring_implementation_5d548d9_3b3d83c.md`

Canonical review commit:
`610e5ccb04c8a20dbeb2105645515f47cec09e5f`

Prior blocker closure:
- CLOSED: retry identity is now owner-retained; active backward validates identity before scaled backward and terminal-cleans failures.
- CLOSED: exact optimizer registry/owner/transaction/GA preflight is now explicit and covers open-incomplete/foreign completion.
- PARTIAL: tagged first-member retry plan/registry is retained and has an exact retry-arm API, but the standard trainer loop still propagates the tagged exception rather than consuming the retry in-process.

Current blockers:

1. **HIGH — production active model branch still calls test-only `run_native_forward_for_test()`.**
   `OmniMoTModel._run_active_local_memory_native_forward()` does not execute the ordinary MoT native forward/loss surface. Frozen design explicitly forbids `run_native_forward_for_test` in production.

   Required: remove the production dependency on the test helper. Route the production branch to the model-owned batched native MoT/Memory-Prefix surface, or fail closed until the future internal native adapter exists while tests override the model method with a test-only spy.

2. **HIGH — first-member tagged retry is retained but not executable by the standard trainer loop.**
   `_handle_active_forward_exception()` stores the exact retry plan/registry, but `training_step()` re-raises and the ordinary `train()` loop has no exact retry catch/re-arm path. Direct handler/arm unit tests do not make the production trainer retry.

   Required: implement one in-process trainer control path for tagged first-member retry with no GA/optimizer/scheduler/fast-frontier advance and prove transient -> retry -> successful member. Later transient remains process-fatal.

3. **MEDIUM — `ga_window_token` is not retired after final slow-window resolution.**
   The registry never clears the token, so consecutive optimizer windows reuse the same token. Retain it across retry/member continuation, but retire it after exact success/skip resolution and create a fresh token for the next window.

4. **MEDIUM — active Evidence is still incomplete.**
   Missing direct active-path witnesses include two valid consumers + S0/PAD ordering, full trainer retry success, consecutive-window fresh token, and full no-marker/pre-existing-lifecycle trainer parity.

Next authorized action for Codex:
- remediate only inside the approved v0.6 CPU/static whitelist and adjacent tests;
- do not modify producer/packer/dataset/manifest/config/optimizer-selector/checkpoint;
- do not perform real I/O, CUDA/GPU/torchrun, training/evaluation/inference;
- submit a new root/child formal pair after these blockers close, then request fresh ChatGPT closure review.

No P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
