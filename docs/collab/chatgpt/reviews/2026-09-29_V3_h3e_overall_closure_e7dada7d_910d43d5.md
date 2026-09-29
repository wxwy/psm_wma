# PSM-WMA V3 — H3-E overall closure

- Date: 2026-09-29
- Formal H3-E root: `e7dada7d3aff98af110e0bde5e038a09fef8ec82`
- Formal H3-E child/Gitlink: `910d43d514dfb21aff84b9aaf1db484807f2ff57`
- Verdict: **H3E_CLOSED**

## Fresh iter0 -> iter1

The fresh 8×H100 integration smoke closed on the formal pair above:

- 8/8 ranks PASS;
- exact per-rank observer counts 32 native forward / 32 native backward / 1 pre-optimizer / 1 post-commit;
- finite native losses and selected gradients;
- frozen host + Local optimizer inventory with Local trainable count 165312;
- exactly one optimizer step and one grouped fast-state/frontier commit;
- complete iter1 DCP with model/optim/scheduler/trainer metadata and dataloader rank_0..rank_7 state;
- no OOM, NaN/Inf, or CUDA error.

## Same-job resume iter1 -> iter2

The same fresh job was resumed in place with the same formal pair.

Execution evidence reported:

- 8/8 ranks PASS;
- exact 32/32/1/1 events per rank;
- native losses finite, approximately 13.236 to 15.863;
- peak allocated memory approximately 8.67 GiB/rank, no OOM;
- iter2 DCP complete while iter1 remained preserved;
- 62/64 slot identities continued directly from the fresh next identities;
- the two non-identical slot transitions were legal `training_stream_end` episode advances, not replay.

This proves the H3-D resume state is actually exercised by the full H3-E runtime: model/optimizer/
scheduler/trainer state and rank-local grouped Local state can continue in the same job without
replaying the already-committed first optimizer window.

No third smoke step is required. The information target of H3-E is satisfied.

## H3-E boundary

H3-E is now closed. Future work belongs to H3-F formal training. The historical fresh/fresh2
failure outputs remain preserved as failure evidence and do not invalidate the final passing pair.
