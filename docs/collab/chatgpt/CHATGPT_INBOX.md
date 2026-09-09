# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Production Active Wiring CPU/static retry-exhaustion closure

Formal pair:
- root implementation SHA: `ae80bae6474a81ca0c93f761b6bce8c29f6b4806`
- child/Gitlink SHA: `d17f09c349cad2da93381033749c4a901391e920`
- Gate: `G0-R09-B-TTT-V035-PRODUCTION-ACTIVE-WIRING-CPU-STATIC-IMPLEMENTATION`
- previous formal pair: `27b60046080290adeb574281f8fcdedf5840439b` / `19394c2824d36728976a9df680eab839cfd915e0`
- approved design: `docs/build/PSM-WMA_Local_Memory_v0.3.5_production_active_wiring_implementation_design_v0.6.md`
- request/bookkeeping HEAD observed: `e2c039802021f52a707d4d61d6dcb56201e3b6ca`

Verdict: `REQUEST_CHANGES`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_production_active_wiring_implementation_ae80bae_d17f09c.md`

Canonical review commit:
`41d4242c559267c02ea6abc10bdeea919a951e79`

Prior blocker closure:
- CLOSED: retried first-member attempt-1 transient now terminal-cleans via `LOCAL_MEM_RETRY_EXHAUSTED`, owner `ABORTED`, pending discarded.
- PARTIAL: no-marker callback parity now proves original `CallBackGroup` ordering, but not the required trainer-level legacy lifecycle control.

Current blockers:

1. **MEDIUM — later-member disposition precedence is wrong for attempt-1 windows.**
   `abort_source_transient()` checks `plan.attempt != 0` before checking `member_index != 0` / completed members. Therefore a transient on member 2 of an attempt-1 window becomes `LOCAL_MEM_RETRY_EXHAUSTED`, while the frozen contract requires any later-member transient to be `LOCAL_MEM_RETRY_AFTER_MEMBER`.

   Required: later-member condition must take precedence; use `LOCAL_MEM_RETRY_EXHAUSTED` only for a repeated transient on the retried first member. Add an attempt-1 later-member exact-code/ABORTED/pending-none fixture.

2. **MEDIUM — no-marker parity Evidence remains below the frozen trainer-level requirement.**
   The new test directly calls `CallBackGroup.on_before_backward()` and monkeypatches the exact TTT callback. It does not prove the real trainer no-marker path preserves the pre-existing lifecycle observe/backward/abort-or-resolve behavior.

   Required: add an adjacent trainer-level no-marker control with a pre-existing lifecycle spy. Prove original dispatcher, exact TTT callback order/args/count, and legacy lifecycle behavior remain intact while active marker remains zero-call. Re-run/report exact pair CPU/static suites, target `py_compile`, root/child `git diff --check`.

Next authorized action for Codex:
- remediate only inside the approved v0.6 CPU/static whitelist and adjacent tests;
- do not modify producer/packer/dataset/manifest/config/optimizer-selector/checkpoint;
- do not perform real I/O, CUDA/GPU/torchrun, training/evaluation/inference;
- submit a new root/child formal pair after these blockers close, then request fresh ChatGPT closure review.

No P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
