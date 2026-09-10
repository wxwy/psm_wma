# ChatGPT 独立 Canonical Segment Production Adapter + Scheduler/GA Design Review

Formal reviewed pair:
- root design SHA: `4522466880221a64cac77b602e903652d180ccb5`
- child/Gitlink SHA: `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`
- Gate: `G0-R09-B-TTT-V035-CANONICAL-SEGMENT-PRODUCTION-ADAPTER-SCHEDULER-DESIGN`
- artifact: `docs/build/PSM-WMA_Local_Memory_v0.3.5_canonical_segment_production_adapter_scheduler_design_v0.3.md`
- prior ChatGPT formal review: `docs/collab/chatgpt/reviews/2026-09-10_R09_B_TTT_v035_canonical_segment_adapter_scheduler_design_7cfa68e_f14a8d8.md`

Verdict: `APPROVE_TO_IMPLEMENT_R09_B_TTT_V035_CANONICAL_SEGMENT_ADAPTER_SCHEDULER_CPU_STATIC`

## Incremental closure

### CLOSED — prior HIGH: S0/native-consumer count contradiction

v0.3 now freezes one consistent native-consumer count authority:
- every `consumer_valid=True` cell is counted, including `consumer_step==0` S0;
- only PAD is excluded;
- per-row frozen chronology count must equal `SegmentBatch.consumer_valid[b].sum()`;
- member `planned_n_valid` is the sum of row counts and must equal gathered payload count, `NativeConsumerBatch.item_count`, and native `actual_n_valid`;
- `original_n_valid_window` and weighted consumer-loss coefficients use that same count source;
- S0 differs only in Local projection: payload is gathered, Local prefix is absent.

This matches the canonical child behavior where `SegmentBatch.gather_consumers()` gathers every valid consumer, including S0, and excludes only invalid/PAD cells. The prior legal-first-segment planned/actual mismatch is therefore closed.

### CLOSED — deterministic queue digest byte encoding

v0.3 also removes the remaining byte-level implementation ambiguity by freezing the exact SHA-256 preimage as UTF-8 label/category bytes, single NUL `0x00` separators, ASCII non-negative decimal integers without leading zeroes, and no Unicode/category normalization. Ordering remains `(digest bytes, canonical_index)` and inherited rollover/continuation/exposure semantics remain unchanged.

## Scope check

The formal root remains docs-only. Relative to the prior formal design pair, the reviewed chain adds the v0.3 design plus review/session/Inbox bookkeeping; the child/Gitlink remains `f14a8d8e3f0cc453545f3d9b1406af76cea7e151`. No production binding, real packer/dataset/manifest/config/optimizer/checkpoint change, real I/O, CUDA/GPU, torchrun, training, evaluation, inference, P4/P5, B2-T, or LIBERO4IN1 is authorized by this verdict.

## Current blockers

None.

## Authorized next action

Only the bounded CPU/static implementation described by the approved v0.3/v0.2 design chain may start. The future implementation Gate must independently freeze its exact child-file whitelist and prove the required CPU/static evidence, including S0/non-S0/PAD exact count equality, unequal-count GA objective, deterministic queue preimage/permutation, projected planning, all-row atomic member commit, and first-member-only retry semantics.
