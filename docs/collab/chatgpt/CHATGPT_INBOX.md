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

## ACTIVE — Production Active Wiring Design v0.2

Formal pair:
- root design SHA: `440082a245a0a7ab21df20d1bded8813c0ccc35e`
- child/Gitlink SHA: `78b8c9cd1389ff523b703d578208f7a221a64af2`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-DESIGN`
- design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.2.md`
- request/bookkeeping commit: `2c7dfe1093d0b37a0664160b2ea637f0d9a6b062`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_design_440082a_78b8c9c.md`

Canonical review commit:
`2dd1331c361f0670dfeb5c8cd67a88d65ed56013`

Prior blocker closure:
- CLOSED: one batched native seam per Local-enabled member/microbatch; no per-consumer model loop.
- CLOSED IN SUBSTANCE: split-phase prepare → model native forward → trainer completion capability chain, object identity, one-shot consumption, and early branch before legacy `_inject_local_history/_ttt_local_memory_tokens`.
- NOT CLOSED: production GA/retry/GradScaler clock.

Current blockers:

1. **HIGH — suffix retry and trainer accumulation window are mathematically inconsistent after prior successful members.**
   Current `abort_retry()` clears only Local slow grads and creates an attempt-1 suffix transaction whose `ga_effective`/`n_window` cover only remaining members. v0.2 says retry does not advance `grad_accum_iter`, but does not reset that counter or clear already accumulated non-Local/model gradients. After `k>0` successes, old-window gradients/counter are therefore mixed with suffix-window weighting, and final suffix completion does not generally coincide with `grad_accum_iter + 1 == suffix.ga_effective`.

   Required remediation: freeze one exact policy. Preferred minimal safe option: active-path retry is allowed only when no successful member has accumulated (`completed_members==0` and `grad_accum_iter==0`); later-member transient is terminal/process-fatal. Alternative: explicitly restart the entire slow optimizer window by clearing all optimizer gradients, resetting `grad_accum_iter=0`, and binding the suffix plan as the new optimizer window while preserving committed fast state. Add CPU/static Evidence for a transient after at least one successful member.

2. **HIGH — completed-capability validation occurs after irreversible `grad_scaler.step(optimizer)`.**
   v0.2 orders optimizer step before exact completed-capability consumption/resolution. On a non-skipped step, weights can already be mutated before stale/substitute/reconstructed capability or GA-boundary mismatch is rejected.

   Required remediation: add an exact non-mutating preflight before optimizer callbacks/`grad_scaler.step`, proving the owner-created unconsumed capability, `SLOW_RESOLUTION_PENDING`, exact transaction/registry chain, open transaction, and exact trainer boundary/counter. After optimizer mutation, no capability/identity/boundary validation may remain that can legitimately fail. Add zero-mutation negative fixtures for stale/substitute/double capability and counter mismatch.

3. **MEDIUM — production marker/native-model handoff ABI remains underspecified.**
   v0.2 references a “complete production marker”, `native_model_forward(payloads, locals)`, and the existing Memory Prefix ABI, but does not freeze the exact marker schema/keys, exact model method/branch signature, or exact output field carrying `ActiveForwardCapability` to trainer completion. Because real producer/native numeric validation is deferred, this leaves room for a caller-supplied synthetic callback to masquerade as the production seam.

   Required remediation: freeze exact production marker fields, exact model/trainer handoff, exact output capability key/type, prohibit caller-supplied model callbacks/functions in the production marker, and state the minimum payload representation treated as the native-model input boundary for this CPU/static Gate.

Next authorized action for Codex:
- docs-only remediation only;
- do **not** modify child implementation yet;
- submit a new formal root SHA (child may remain `78b8c9c...` if docs-only) closing all blockers above;
- request a fresh ChatGPT review for the new formal pair.

No packer/dataset/manifest/config/optimizer-selector/checkpoint implementation, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
