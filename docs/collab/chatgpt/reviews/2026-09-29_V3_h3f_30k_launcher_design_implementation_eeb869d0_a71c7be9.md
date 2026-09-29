# PSM-WMA V3 — H3-F 30k formal training launcher implementation

- Date: 2026-09-29
- Formal H3-F root: `eeb869d0f2c65d9f9f4cfc86f1c99afb0d378052`
- Formal H3-F child/Gitlink: `a71c7be99f8d485f3066128c34d210ef709a1440`
- Status: **H3F_LAUNCHER_IMPLEMENTED_PENDING_READINESS**
- Long-run authorization: **NOT YET AUTHORIZED**

## Purpose

H3-F is a separate formal-training launcher, not an expansion of the closed H3-E smoke harness.

New files:

- `examples/psm_wma_robocasa_h3f.py`
- `examples/psm_wma_robocasa_h3f_test.py`

The launcher reuses the H3-E-proven source/cache/Stage-A/Edge/VAE authorities and grouped trainer,
but freezes long-run-specific training semantics in its own config digest.

## Formal training contract

- target-atomic train catalog: 9036 episodes;
- ranks: 8 H100;
- B_stream: 8 per rank;
- T: 16;
- GA: 2;
- K_local: 4;
- nominal global consumer exposure: 2048/update;
- optimizer: frozen H3-E Edge+Local selector, FusedAdam, lr 5e-5;
- max_iter: **30000**;
- scheduler: LambdaLinear cycle `[30000]`;
- warmup: **500**;
- checkpoint save cadence: every **1000** optimizer iterations;
- primary evaluation milestones:
  `1000, 2000, 4000, 8000, 12000, 16000, 20000, 24000, 30000`.

Saving every 1000 guarantees every primary evaluation milestone has a resumable DCP. Storage
capacity must be reviewed before long-run authorization.

The 30k run starts fresh from the frozen H100-local Stage-A warmstart; it does not use H3-E iter1
or iter2 as a training warmstart.

## Long-run-specific protections

The H3-F config digest additionally binds:

- 30k horizon;
- scheduler cycle;
- 500-step warmup;
- save cadence;
- primary evaluation milestones.

Same-job resumes therefore fail if the long-run schedule changes.

Resume attempts use the same job but separate evidence directories keyed by explicit
`--attempt` and starting checkpoint iteration.

Fresh must use attempt 1; resume must use attempt >=2.

## Distributed startup

All ranks run read-only preflight before distributed execution.

Filesystem publication is synchronized:

1. ranks enter distributed init;
2. rank0 creates the evidence attempt directory;
3. a distributed barrier publishes it;
4. all ranks continue.

This avoids an 8-rank race where one process creates the job/evidence directory while another is
still checking fresh-run nonexistence.

## Long-run observer

H3-E wrote every native event because it was only a one-step smoke. That is not acceptable for
30k.

H3-F aggregates each optimizer iteration into one durable JSONL record per rank containing:

- 32/32/1/1 event contract;
- loss min/max/mean;
- frontier epoch;
- allocated/reserved/peak memory;
- Local non-empty/non-zero gradient shard counts.

Thus the evidence volume is O(optimizer steps), not O(native events).

## Resume semantics

The formal trigger loader remains the H3-E-proven grouped trigger loader. The base trainer sets its
start position from the restored optimizer iteration, while the grouped dataloader DCP restores
frontier/slot/cursor/scheduler/fast state.

A completed formal run must finish at iter30000 and save a complete final DCP including this rank's
dataloader state.

## Required readiness Gate

Before any 30k run is started, ds must validate this exact formal pair with:

- H3-F unit/static tests plus the closed H3-E/grouped trainer tests;
- Ruff check/format and git diff check;
- exact-pair read-only H3-F preflight;
- frozen 9036 catalog/manifest/Stage-A authority;
- 30k scheduler/warmup/save contract;
- disk free-space report and actual checkpoint-size estimate;
- timing estimate based on H3-E resume-step evidence.

The purpose of the final two checks is to avoid starting a formally correct but operationally
unfinishable 30k run.

Until that evidence is reviewed, **H3-F 30000-step training is not authorized**.
