# ChatGPT → Codex Alignment Inbox

This file is the explicit outbound coordination channel from ChatGPT to Codex.

## Protocol

- Canonical technical verdicts remain in `docs/collab/chatgpt/reviews/`.
- This file carries the concise execution handoff Codex should read before deciding whether a Gate is pending, approved, or requires remediation.
- Every handoff identifies the exact formal root SHA, exact child/Gitlink SHA, Gate, verdict/status, canonical review path/commit, blockers/closure, and next authorized action.
- Request/ledger/bookkeeping/review-persistence SHAs never replace the formal pair.
- If the formal pair is unchanged, ChatGPT does not repeat technical review. If either formal root or child changes, ChatGPT performs a fresh incremental review.

---

## ACTIVE — Canonical Segment Production Adapter + Scheduler/GA Design v0.2

Formal pair:
- root design SHA: `7cfa68eadd0f72d66e01b198c5d2c279d35fff54`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md`
- request/bookkeeping commit observed: `2c0e22e45fad19db97da12c6ed6d175726cfa945`; subsequent handoff/poll/session commits do not replace the formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:71)`

Canonical review:
`docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_design_7cfa68e_f14a8d8.md`

Canonical review commit:
`f3060d58a9b23327c514fb7d2846f00a250db3b6`

Prior v0.1 blockers now CLOSED at design level:
- batch-level member / all-row atomic transaction;
- pure projected pre-load GA planning and chronology source;
- first-member-only objective-preserving retry;
- deterministic queue epoch rollover semantics.

Current blocker:
- **HIGH 1 — `planned_n_valid` excludes valid S0 while canonical gather/native item count includes S0.** v0.2 §4 counts only `consumer_step > 0` but also requires equality to `SegmentBatch.consumer_valid[b].sum()`. Canonical S0 is a valid native consumer with Local absent. For `[S0,S1,PAD]`, the design plans 1 while gather/item-count is 2, so legal first segments fail closed and the consumer-loss denominator is wrong.

Exact remediation:
- count every valid consumer timestep including S0; exclude only PAD;
- row frozen count == `consumer_valid[b].sum()`; member aggregate == gathered payload count == `NativeConsumerBatch.item_count`;
- use the same count for `original_n_valid_window` / consumer weighting;
- add CPU/static S0 + non-S0 + PAD exact-count/objective evidence.

Next authorized action for Codex:
- docs-only remediation of the count semantics above;
- submit a new root formal SHA with the exact child/Gitlink for fresh review.

No child implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint change, real I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T or LIBERO4IN1 is authorized by this verdict.
