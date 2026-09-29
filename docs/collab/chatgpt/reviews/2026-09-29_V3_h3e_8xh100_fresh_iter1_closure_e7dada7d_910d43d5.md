# PSM-WMA V3 — H3-E 8×H100 fresh iter0->iter1 closure

- Date: 2026-09-29
- Formal implementation root: `e7dada7d3aff98af110e0bde5e038a09fef8ec82`
- Formal child/Gitlink: `910d43d514dfb21aff84b9aaf1db484807f2ff57`
- Verdict: **H3E_8XH100_FRESH_ITER1_CLOSED**
- Next authorization: **APPROVE_TO_RUN_H3E_8XH100_SAME_JOB_RESUME_ITER1_TO_ITER2**

## Fresh run

The exact formal pair above completed the authorized co-resident 8×H100 fresh smoke.

All 8 ranks reported PASS.

Per rank event counts were exactly:

- native_forward = 32;
- native_backward = 32;
- pre_optimizer = 1;
- post_commit = 1.

The grouped geometry therefore exercised the intended two GA members × T16 native path on every
rank.

## Numeric/gradient evidence

- every native loss was finite;
- observed range was approximately 14.7449 to 16.6529;
- both trainer finite-gradient guards passed;
- selected gradients were finite and non-empty;
- Local parameter inventory remained 165312;
- optimizer inventory covered the frozen host keys plus Local memory;
- exactly one optimizer step completed;
- grouped completed iteration = 1;
- fast-state/frontier committed once;
- no OOM, CUDA error, NaN, or Inf.

The `slot_queries` local grad witness is zero on ranks 4-7 because `k_local=4` is sharded
along dim0 across 8 ranks, so those ranks own an empty local shard. Ranks 0-3 carry the four
rows and have non-zero local gradients. This is compatible with a non-zero global gradient and
is not treated as a defect.

## Memory/performance interpretation

The co-resident run used approximately:

- peak allocated: ~7.9 GiB/rank;
- peak reserved: ~10.0 GiB/rank.

The existing wzy job remained active and unaffected.

Wall time (~4m50s including dataset loading) is contextual only and is **not** an isolated H100
performance result.

## DCP closure

The job saved:

- latest checkpoint = `iter_000000001`;
- model/.metadata;
- optim/.metadata;
- scheduler/.metadata;
- trainer/.metadata;
- dataloader/rank_0.pkl through rank_7.pkl.

All eight rank result JSON files reported PASS.

The exact fresh output authority is:

`/mnt/data1/data_v2_0617/psm_wma_v3_h3e_fresh3_e7dada_910d`

It must remain untouched for the same-job resume Gate.

## Same-job resume authorization

Authorize only the exact continuation:

- same formal root/child pair;
- same output root;
- same job name;
- `phase=resume`;
- load the exact fresh iter1 checkpoint and rank-local dataloader states;
- continue from iteration 1 to iteration 2 only.

The resume smoke must verify:

1. resume was actually required and loaded;
2. grouped Local state/frontier/catalog scheduler state is restored from rank-local dataloader DCP;
3. the trigger loader starts after the already-consumed first optimizer window;
4. fresh iter1 committed digest / next identities agree with the restored start state;
5. one additional optimizer iteration completes;
6. final grouped completed iteration = 2;
7. one additional fast-state/frontier commit occurs;
8. native loss and selected gradients remain finite;
9. `iter_000000002` saves model/optim/scheduler/trainer metadata plus dataloader rank0..7 state;
10. the original iter1 checkpoint and prior failed fresh evidence remain untouched.

This is still a co-resident functional smoke, not a throughput benchmark.

## Still forbidden

- no H3-F 30000-step training;
- no new job for resume;
- no manual checkpoint/dataloader-state copying;
- no geometry change;
- no mutation of Stage-A, B1 cache, or manifest;
- no deletion of historical failed fresh OUTs.
