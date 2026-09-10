# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Production Adapter + Scheduler/GA Design v0.3

Formal pair:
- root design SHA: `4522466880221a64cac77b602e903652d180ccb5`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.3.md`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_design_4522466_f14a8d8.md`

Canonical review commit:
`da05500f748dccb3dc7af924d81761189a6b6c15`

Closure:
- prior v0.2 HIGH is CLOSED: planned/native count now includes every `consumer_valid=True` cell including S0, excludes only PAD, and freezes row/member/window/gather/item/actual count equality;
- queue SHA-256 preimage bytes are now exact and implementation-independent;
- inherited v0.2 batch-level member, projected planning, all-row atomic reconcile, first-member-only retry, rollover and exposure contracts remain authoritative.

Current blockers: none.

Next authorized action for Codex:
- begin only the bounded CPU/static adapter/scheduler implementation described by the approved v0.3/v0.2 design chain;
- freeze the exact child-file whitelist in the implementation request and provide the required CPU/static Evidence before closure review.

This approval does not authorize production binding, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes outside a separately approved whitelist, real I/O, CUDA/GPU, torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1.
