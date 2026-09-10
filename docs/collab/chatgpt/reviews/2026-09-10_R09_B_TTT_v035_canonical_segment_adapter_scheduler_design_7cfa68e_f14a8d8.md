# ChatGPT 独立 Canonical Segment Production Adapter + Scheduler/GA Design Review

Formal reviewed pair:
- root design SHA: `7cfa68eadd0f72d66e01b198c5d2c279d35fff54`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md`
- prior ChatGPT formal review: `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_design_0779be7_f14a8d8.md`
- request/bookkeeping commit observed: `2c0e22e45fad19db97da12c6ed6d175726cfa945`; later `857c92f` / `38f3304` / `4bbdbe3` are review-handoff/poll/session bookkeeping and do not replace the formal pair.

Verdict: `REQUEST_CHANGES(docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:71)`

## Incremental closure against v0.1

The v0.2 remediation materially closes the four prior ChatGPT findings at the design level:

1. **CLOSED — prior HIGH batch-level identity / atomic transaction ABI.** `MicrobatchPlanMember` and `CanonicalGAWindowPlan` keep membership native-microbatch-granular, retain ordered per-row identities/provenance/counts, and freeze one all-row post-backward transaction boundary.
2. **CLOSED — prior HIGH circular full-window planning.** `ChronologyCountRecord` plus a deep-copied `ProjectedSchedulerState` now separate pre-load planning from live committed scheduler mutation and require exact execution-time reconciliation.
3. **CLOSED — prior HIGH retry objective drift.** Retry is now first-member-only and pre-backward-only, while attempt-1 retains the original member list, denominator, GA effective value, indices, queue snapshot, and plan-chain. Later or post-backward failures terminalize the window instead of using the inherited suffix plan.
4. **CLOSED — prior MEDIUM queue rollover underspecification.** v0.2 freezes a versioned seed/epoch/category/index SHA-256 permutation, bound-slot continuation precedence, rollover only at a safe post-commit boundary, and cumulative exposure persistence across epochs.

Those closures do not remove the new count-semantics contradiction below.

## Current blocker

### HIGH — `planned_n_valid` excludes valid S0 while canonical gather/native `item_count` includes valid S0

**Location:** `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.2.md:71`; child `cosmos_framework/model/generator/mot/local_memory_segment.py::SegmentBatch.gather_consumers` (around lines 86-103 at child `f14a8d8`).

**Root cause:** v0.2 §4 defines each chronology count as the number of timesteps satisfying `consumer_step > 0`, while simultaneously requiring that value to equal `SegmentBatch.consumer_valid[b].sum()`. These are not equivalent for a segment containing S0. The frozen hard contract says S0 is a **valid consumer with Local absent**, not PAD. The current canonical `gather_consumers()` confirms this: every `consumer_valid=True` row is appended to `payloads` and therefore contributes to the gathered native consumer batch; only the Local payload is absent when `consumer_step == 0`.

For the canonical row `[S0, S1, PAD]`, §4 currently plans `row_planned_n_valid=1`, while `consumer_valid.sum()==2` and `NativeConsumerBatch.item_count==2`. §6 then requires `actual_n_valid == planned_n_valid` before backward, so a legal first segment would fail closed and the weighted objective denominator would undercount native consumers.

**Violated contract:** `planned_n_valid` is the native gathered-valid consumer count used for the consumer-loss weighting denominator. S0 is excluded only from Local projection/evidence use; it is not excluded from native consumer count or native consumer loss. PAD alone is excluded.

**Exact acceptance:** amend §4/§6 so that:

1. `row_planned_n_valid` counts **all valid consumer timesteps including S0** and excludes only PAD; equivalently, it is the cardinality of the frozen chronology consumer range that will become `consumer_valid=True`, not the cardinality of `consumer_step > 0`.
2. For every row, the frozen count must equal `SegmentBatch.consumer_valid[b].sum()` after load; member aggregate must equal the number of stream-major gathered payloads and `NativeConsumerBatch.item_count`.
3. `original_n_valid_window` / consumer-loss weights use that same native-consumer count. `consumer_step==0` remains Local-absent only.
4. CPU/static acceptance includes at least one row containing S0 + non-S0 + PAD and proves exact planned/actual/item-count equality and the resulting weighted objective.

## Scope / next authorized action

This verdict authorizes only a docs-only remediation of the count semantics above. It does **not** authorize child implementation, producer/packer/dataset/manifest/config/optimizer-selector/checkpoint changes, real data/cache/checkpoint I/O, CUDA/GPU/torchrun, training/evaluation/inference, P4/P5, B2-T, or LIBERO4IN1.

After the count semantics are corrected in a new formal root SHA with the exact child/Gitlink, submit that new pair for fresh design review. The reserved success literal remains:
`APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`.
