# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Production Active Wiring CPU/static Implementation closure remediation v2

Formal pair:
- root implementation SHA: `27b60046080290adeb574281f8fcdedf5840439b`
- child/Gitlink SHA: `19394c2824d36728976a9df680eab839cfd915e0`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `5d548d97029302817efeaad49983a2a16883be6e` / `3b3d83c33b54a14d52ce54f97e920875f9b48e4e`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`
- request/bookkeeping HEAD observed: `f86cad3c13500a46a88bcde5b298be8d013b8974`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_production_active_wiring_implementation_27b6004_19394c2.md`

Canonical review commit:
`7704646c24d5bf62708413e056e8764bb7b2d501`

Prior blocker closure:
- CLOSED: production active base class no longer enters `run_native_forward_for_test`; it fail-closes until the future native MoT adapter exists, while the synthetic spy is test-only.
- CLOSED FOR FIRST ATTEMPT: standard trainer now performs one tagged first-member retry in-process without another dataloader fetch or GA advance.
- CLOSED: retry identity is owner-retained and active backward validates before scaled backward with owner-terminal cleanup.
- CLOSED: exact optimizer registry/owner/transaction/GA preflight.
- CLOSED: resolved-window `ga_window_token` retirement/fresh next-window token.
- PARTIAL: Evidence now covers two-consumer S0/PAD ordering, first retry, scaler success/skip, optimizer negatives, and token freshness.

Current blockers:

1. **HIGH — attempt-1 second tagged transient is not terminalized fail-closed.**
   `ProductionActiveWiringRegistry.abort_source_transient()` does not check `transaction.plan.attempt`. On an attempt-1 retry, a second tagged transient enters `owner.abort_retry()`, whose `recover_transient()->suffix_after_failure()` raises `LOCAL_MEM_RETRY_EXHAUSTED` before pending discard/owner terminalization. This can leave owner `PREPARED` with a live pending graph.

   Required: if `prepared.transaction.plan.attempt == 1`, route directly through exact `owner.abort_terminal(...)` with a frozen retry-exhausted terminal code, clear registry authority/pending/Local grads, suppress suffix, and propagate process-fatal failure. Add a trainer-path transient-twice fixture proving first retry at counter 0, second terminal, owner `ABORTED`, pending `None`, zero optimizer/scheduler/fast commit, and no third forward.

2. **MEDIUM — required adjacent no-marker lifecycle/callback parity Evidence is still missing.**
   `active_wiring_callback_test.py` proves active exact-class TTT filtering and zero lifecycle touch, but not the v0.6-required neighboring no-marker trainer control through the original dispatcher/legacy lifecycle route.

   Required: add the adjacent no-marker trainer-level control proving active zero lifecycle calls while no-marker preserves original callback order/args/count and legacy behavior; rerun targeted CPU/static suites, target `py_compile`, and root/child `git diff --check`.

Next authorized action for Codex:
- remediate only inside the approved v0.6 CPU/static whitelist and adjacent tests;
- do not modify producer/packer/dataset/manifest/config/optimizer-selector/checkpoint;
- do not perform real I/O, CUDA/GPU/torchrun, training/evaluation/inference;
- submit a new root/child formal pair after these blockers close, then request fresh ChatGPT closure review.

No P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
