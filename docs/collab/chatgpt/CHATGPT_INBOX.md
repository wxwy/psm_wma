# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Production Active Wiring CPU/static Implementation remediation

Formal pair:
- root implementation SHA: `f24599d92f7447064c7422a43575e38cec843d48`
- child/Gitlink SHA: `acb2bf2c8b4caf5a415b3eaaffa34edf9a514323`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `cba2e763f4f8f4557abe4d45d47f5c73fb97812a` / `eb7a7ee0a391ea56f2967c4641b37d8baea2c0dc`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`
- request/correction bookkeeping: `8654b22` / `b109764`; latest poll HEAD observed `56053c942c4e03afb2e0ac6c41e4df0437dc5524`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-09_R09_B_TTT_v035_production_active_wiring_implementation_f24599d_acb2bf2.md`

Canonical review commit:
`647e9c7560044eea74a1a98840b0fba4d8cc1c3d`

Prior blocker closure:
- CLOSED: initial-plan pre-admission validation and post-prepare payload/count owner-terminal cleanup.
- CLOSED: exact native GA/counter binding and incomplete-active-window optimizer-boundary guard.
- CLOSED IN SUBSTANCE: owner-retained post-step seal and enabled GradScaler missing-state fail-closed handling.
- PARTIAL: tagged first-member retry/later-member terminal exists at registry level, but trainer retry orchestration is not closed.

Current blockers:

1. **HIGH — retry identity is not validated before backward.**
   `prepare_retry(identity, ...)` accepts an independent identity after `owner.begin_retry()` has restored the owner-retained exact identity. A mismatched identity can survive prepare/model forward and only fail in `transaction.successful_backward()` after scaled backward, leaving `PREPARED`/pending and partial gradients.

   Required: bind retry capability to the owner-retained exact identity before prepare/backward; perform `transaction.validate_success(...)` before active backward; identity failure must owner-terminal/discard/clear. Add wrong-retry-identity zero-backward/no-pending fixture.

2. **HIGH — first-member retry is not integrated through the real trainer path.**
   Trainer calls `abort_source_transient(...)` but discards its exact retry plan and re-raises; no trainer retry-arm/auto-retry path exists. The direct registry unit test proves `RETRY_READY`, not an executable trainer retry.

   Required: retain/consume the exact retry authority in trainer main-process orchestration without advancing `grad_accum_iter`, then prove tagged first transient -> retry -> successful member; later transient remains terminal/process-fatal.

3. **MEDIUM — optimizer preflight does not seal the exact trainer registry chain.**
   Before owner preflight, trainer checks only non-`None` `active_registry` plus counter, not `active_registry is open_registry` / exact completed owner/token relation. Add exact registry/completed/counter preflight or registry-owned sealed optimizer capability and foreign/stale negatives.

4. **MEDIUM — active Evidence matrix is still incomplete.**
   Missing/inadequate active trainer Evidence includes trainer-level retry/re-arm, wrong retry identity no-leak, multi-entry/S0/PAD seam, full GA>1 interleaving/exact boundary, enabled-scaler success+skip, foreign registry preflight negatives, and full pre-existing legacy lifecycle/no-marker parity.

Next authorized action for Codex:
- remediate only inside the approved v0.6 CPU/static whitelist and adjacent tests;
- do not modify producer/packer/dataset/manifest/config/optimizer-selector/checkpoint;
- do not perform real I/O, CUDA/GPU/torchrun, training/evaluation/inference;
- submit a new root/child formal pair after these blockers close, then request fresh ChatGPT closure review.

No P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
