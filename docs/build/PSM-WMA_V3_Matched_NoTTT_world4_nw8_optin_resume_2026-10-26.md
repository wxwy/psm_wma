# V3 Matched No-TTT — optional nw=8 and Resume boundaries (candidate only)

2026-10-26. Root implementation `960c0aafc79e7dc248748c914ec2a220aafe7713`; Child/Gitlink `e96584e39d2f64e3d7783bd1cb98f5cfa77eb8d4`. This candidate is NOT merged to V3, NOT DS accepted and NOT authorized for GPU / real DCP. Production `workers=0` job is immutable.

## Change scope

- `NOTTT_LOADER_WORKERS` now allows `0|1|2|4|8`; default remains `0`. CLI is still `--no-ttt-loader-workers`. Existing `--num-workers 0` must remain unchanged because it is a separate G1/raw-prefetch argument.
- `nw=8` supported only for **new** world4/GA4/B8/T16 No-TTT jobs whose name is `no_ttt_*_mpw8_world4_ga4`. Old world4 No-TTT and G1 remain unchanged. The parent retains planner, source, transforms, RNG, native collate/model/optimizer/frontier.
- Real spawned-process full/terminal order/RNG parity matrix includes 8; a focused `nw8→nw8` synthetic CPU checkpoint/resume + `nw8→nw2` negative test was added. Tests have **not** been executed independently or against the target CUDA PyTorch runtime.
- Eight workers **per rank** on GPU4–7 means up to **32 CPU worker processes**, plus four trainer rank processes. `NOTTT_PREFETCH_FACTOR=1` implies at most 8 queued tasks per rank; prefetch 2 implies up to 16. This may be slower or exhaust RAM/IO. Measure before using a production job.

## Existing workers0 same-job Resume — original job

Assume the validated `OUTPUT_ROOT`, `SOURCE_ROOT`, `CACHE_ROOT`, `DATASET_INDEX_ROOT`, `EDGE_POLICY_CHECKPOINT`, `WAN_VAE_PATH`, `BASE_CHECKPOINT_PATH` still point to the original validated resources. In the shell, unset any prior new-worker variables first:

```bash
unset NOTTT_PREFETCH_FACTOR NOTTT_PERSISTENT_WORKERS NOTTT_LOADER_TIMEOUT_S
NOTTT_LOADER_WORKERS=0 \
JOB_NAME=no_ttt_packed128_droid_fresh_30k_world4_ga4 \
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 30000
```

This reads the original Job's `checkpoints/latest_checkpoint.txt` and requires the existing rank0..3 dataloader sidecars plus full model/optim/scheduler/trainer DCP. `30000` is an absolute stop iteration, not an increment. Synthetic cross-code worker0→0 CPU parity was approved, but real DCP/CUDA same-job continuation still requires independent Gate.

## New isolated workers8 Fresh and same-profile Resume

**These two commands apply ONLY after separate review/runtime authorizations and only within an isolated new mpw8 Job.** `fresh` initializes from official DROID DCP, NOT from the old workers0 Job.

```bash
export NOTTT_LOADER_WORKERS=8
export NOTTT_PREFETCH_FACTOR=1
export NOTTT_PERSISTENT_WORKERS=1
export NOTTT_LOADER_TIMEOUT_S=120
export JOB_NAME=no_ttt_packed128_droid_fresh_30k_mpw8_world4_ga4

# Create the new workers8 checkpoint in the new isolated Job:
bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 100

# Subsequently resume that *same* workers8 Job to a total of 30000 iterations:
bash scripts/train_v3_matched_no_ttt_4gpu.sh resume 30000
```

The same worker8 profile (workers, factor, persistence, timeout, packet/cache limits), world4/GA4, Job name, model and data identities must be preserved. A worker count/profile change is rejected. Do not run `fresh` again into an existing Job.

## Existing workers0 → workers8: no valid Resume command

Setting `NOTTT_LOADER_WORKERS=8` and retaining the original workers0 `JOB_NAME` is deliberately rejected at launcher/profile validation. Changing `JOB_NAME` to `_mpw8_` and using `resume` fails because the new Job does not have its own checkpoint/identity; using `fresh` starts a new unrelated training run rather than continuing the original. Do not rewrite `v3_job_identity.json`, checkpoint `dataloader/rank_*.pkl`, Frontier schema, config digests or latest pointers by hand.

To migrate an active workers0 Job to workers8, a separately authorized migration design and implementation Gate is required: immutable source DCP + source snapshot, new isolated destination namespace, checkpointed optimizer/scheduler/trainer/Python/NumPy/Torch/CUDA RNG/Frontier, atomic model+state restoration, exact next-consumer/gradient parity, fail-closed and rollback, provenance trail, and runtime GPU gate. No migration is implemented by this candidate.

## Entry checks (not GPU authorization)

- Confirm Root/Child Gitlink match exactly and use an isolated detached candidate worktree; DO NOT checkout/reset a live training worktree.
- Independent DS synthetic CPU: `tools/v3/no_ttt_workers_entry_test.py`, `cosmos_framework/trainer/no_ttt_cpu_loader_test.py`, `cosmos_framework/trainer/no_ttt_cpu_loader_resume_test.py`; then actual target PyTorch worker lifecycle/CPU memory, 4xGPU FSDP DCP/RNG Resume, perf.
- Current approved B1 evidence concerns **workers0→0 synthetic CPU** only; it cannot authorize either nw8 live training or nw0→nw8 migration.
