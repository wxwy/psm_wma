# PSM-WMA V3 — H3-E 8×H100 fresh co-resident execution authorization

- Date: 2026-09-29
- Formal implementation root: `db08117786a2483ca5cc7f4b58a0c3518e78bccc`
- Formal child/Gitlink: `b43097c74982f13e67c071ece729c7b6929cad52`
- Owner decision: **8-GPU co-resident execution explicitly authorized**
- Gate: **APPROVE_TO_RUN_H3E_8XH100_FRESH_ITER0_TO_ITER1_CORESIDENT**

## Authorization change

The previous status was `H3E_8XH100_FRESH_WAITING_FOR_GPU` because all eight H100s were
occupied by another user's active training.

The project owner has now explicitly authorized sharing all eight H100s with the existing job,
based on the observed memory headroom and the known H3-E memory envelope.

This removes the governance blocker against launching the fresh H3-E smoke while the other job
is still resident.

## Interpretation of this run

This run is a **co-resident functional/integration smoke**, not a performance benchmark.

Valid evidence from this run includes:

- all 8 ranks initialize and complete;
- production grouped data path works;
- finite native losses;
- finite/non-empty selected gradients;
- Local gradient witnesses;
- optimizer inventory and exactly one optimizer step;
- atomic fast-state/frontier commit;
- complete iter1 DCP including all rank-local dataloader states;
- result JSON / CUDA memory evidence;
- no OOM/non-finite/error path.

Do **not** use this co-resident run to make claims about:

- isolated throughput;
- isolated wall time;
- step/sec;
- scaling efficiency;
- standalone H100 utilization.

Wall time and memory may still be recorded as contextual evidence.

## Launch-time guard

Immediately before torchrun, record a fresh per-GPU snapshot.

Co-resident execution may proceed only if:

1. all 8 GPUs are still visible and healthy;
2. each rank can be launched without killing/pausing the existing job;
3. observed free memory remains sufficient for the known H3-E envelope plus safety margin;
4. no GPU is in an error/reset state.

If launch or runtime encounters OOM, CUDA reset, non-finite state, or system instability, stop
and report `H3E_8XH100_FRESH_ITER1_BLOCKED`. Do not change geometry to force a pass.

## Scope unchanged

Only fresh `iter0 -> iter1` is authorized.

Still not authorized:

- same-job resume `iter1 -> iter2`;
- H3-F 30000-step formal training;
- geometry reduction/fallback;
- code/config/assets mutation.
