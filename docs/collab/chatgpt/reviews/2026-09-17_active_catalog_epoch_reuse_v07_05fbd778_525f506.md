# ChatGPT Independent Review — ACTIVE-CATALOG-EPOCH-REUSE v0.7

- Gate: `G0-R09-B-TTT-V035-ACTIVE-CATALOG-EPOCH-REUSE`
- formal root: `05fbd7780d034eab59a658e313496a0ed104657f`
- child/Gitlink: `525f5066393cba044f00f1104b83f5eb424a9c49`
- design blob: current v0.7 document at the formal root
- review type: fresh project-level design review after v0.6 `REQUEST_CHANGES`
- verdict: **REQUEST_CHANGES**

## Project-level assessment

v0.7 correctly closes the two previous direction-level HIGH findings:

1. It withdraws `_epoch_observed` and restores `scheduler.cumulative_valid_consumer_exposure` as the weighted-deficit control authority.
2. It no longer rewinds non-terminal episodes to cursor 0 / W0 at a catalog boundary; non-terminal slots continue exact chronology with cursor+1 and detached fast-state carry.

Those two corrections are accepted.

However the new per-slot reuse mechanism introduces a new unresolved authority mismatch that makes the design internally inconsistent with the current scheduler snapshot/resume ABI.

## HIGH-1 — per-slot `_slot_epoch` cannot be represented by the existing scalar scheduler queue identity

v0.7 explicitly permits two slots of the same category to advance reuse independently and therefore to hold different `_slot_epoch[slot]` values. The design then uses:

`queue_permutation(queue_seed, _slot_epoch[slot], category, catalog_size)`

for each terminal slot independently.

But `RankLocalSegmentScheduler` currently owns only one global:

- `queue_seed`
- `queue_epoch`
- `queue_permutation`
- `segment_provenance`

and `configure_queue(...)` overwrites that one scalar/global tuple. `snapshot()` / `rebuild()` likewise persist only one global queue identity.

Therefore when (for example) slot 0 is at slot-epoch 2 and slot 4 of the same category is still at slot-epoch 1, there is no single `scheduler.queue_epoch` / `scheduler.queue_permutation` that truthfully describes both active slot queues. v0.7 §5 and criteria 7/10 nevertheless state that existing scheduler queue fields are already sufficient for checkpoint/resume consistency. They are not.

This is not only a documentation problem: after resume, the driver may restore `_slot_epoch`, but the scheduler snapshot exposes only one queue epoch/permutation, so the claimed queue-identity cross-check is either ambiguous or false.

### Required change

Choose and freeze one coherent authority model before implementation:

- **Option A:** make queue identity explicitly per-slot (or per category+slot) in the scheduler snapshot/rebuild ABI, with a new exact representation and tests; or
- **Option B:** declare the scheduler scalar queue fields non-authoritative for active-route per-slot reuse and persist the complete per-slot queue identity in the driver state, with an explicit derivation/cross-check contract and resume tests.

Do not keep a per-slot runtime algorithm while claiming the existing scalar scheduler fields already represent it.

## MEDIUM-1 — existing v0.6 planning evidence does not validate the v0.7 state machine

The retained §10 planning evidence was produced by the old global-reset rollover reference implementation. v0.7 changes the state machine materially: non-terminal slots continue, terminal slots independently rewind/reorder, and slot epochs can diverge. The old `45 × 112` planning trace therefore does not prove that v0.7 can actually produce 5040 complete windows, preserve every non-terminal continuation, and avoid duplicate/stranded authority under asynchronous slot reuse.

Before implementation approval, add a CPU/static reference probe implementing the **v0.7** algorithm (not the v0.6 global-reset algorithm) and record at minimum:

- first reuse boundary and the exact per-slot action (continue vs reuse);
- `_slot_epoch` trajectory for all slots across multiple reuse events;
- no cursor discontinuity for non-terminal slots;
- no sidecar reset for non-terminal slots;
- complete-window production beyond the former 113th-window failure;
- no scheduler admission/commit rejection;
- full block-identity coverage / no permanent stranding;
- queue-identity state matching the authority model chosen to close HIGH-1.

## Scope / status

- v0.7 **does close** the previous ChatGPT HIGH-1 chronology reset and HIGH-2 scheduler-authority replacement.
- It is **not yet approved to implement** because the replacement per-slot epoch mechanism has no coherent queue-identity persistence model.
- `D8b` 5000-step long training remains **BLOCKED**.

Canonical verdict: `REQUEST_CHANGES`.