# Training and Resume

## Current canonical topology

The current Local Memory + TTT A2 route is configured for one 8-GPU node:

```text
world_size = 8
B_stream / rank = 8
T = 16
GA / rank = 2
consumers / native forward / rank = 128
consumers / optimizer update / rank = 256
global consumers / optimizer update = 8 × 256 = 2048
```

This preserves the previously validated global effective batch of 2048 while moving from one rank to eight ranks. The learning rate and optimizer-step count therefore retain the same global-batch semantics.

## Global catalog and rank-local state

There is one global episode catalog per LIBERO suite. After whole-block eligibility filtering, each suite is deterministically sharded by eligible episode ordinal across ranks. The eight rank shards are disjoint and their union is the global catalog. Each rank then maps only its shard onto its own eight stable slots.

Fast state (`W_fast`), slot frontier, `slot_epoch`, queue reuse and scheduler exposure remain rank-local. DCP saves the Local runtime state as `dataloader/rank_<rank>.pkl`, so an 8-rank resume restores the matching rank-local frontier.

The four Local slow groups are intentionally replicated outside root FSDP because their evidence/TTT scan runs before the normal model forward. They are broadcast from rank 0 after checkpoint load and their gradients are explicitly averaged across all ranks before gradient clipping / optimizer callbacks. The main Cosmos parameters remain FSDP-sharded across the eight ranks.

## Assets

Default paths:

```text
LIBERO_ROOT=/disk/rl/data/LIBERO_LeRobot_v3
LIBERO_LATENT_CACHE_ROOT=/disk/rl/data/LIBERO_LeRobot_v3_cosmos_exact_window_shared_vae_v1
EDGE_POLICY_CHECKPOINT=/disk/rl/models/Cosmos3-Edge-Policy-DROID
BASE_CHECKPOINT_PATH=cosmos-framework/examples/checkpoints/Cosmos3-Edge-Policy-DROID-dcp
WAN_VAE_PATH=cosmos-framework/examples/checkpoints/wan22_vae/Wan2.2_VAE.pth
```

## Preflight

`scripts/verify.sh` checks capabilities of the currently checked-out source tree. It does **not** require a frozen Git SHA. Git SHAs are recorded in logs for reproducibility only.

```bash
cd /disk/rl/psm_wma
bash scripts/verify.sh
```

## First 8×H100 smoke

On a new 8×H100 node, first run two optimizer steps using the same output directory that will later continue the formal run:

```bash
cd /disk/rl/psm_wma
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
MAX_ITER=2 SAVE_ITER=1 \
bash scripts/train_local_memory_ttt.sh
```

With the defaults this resolves to `NPROC_PER_NODE=8` and `PSM_R09_B_TTT_ACTIVE_GA=2` automatically.

After the smoke is healthy, continue the exact same run:

```bash
CUDA_VISIBLE_DEVICES=0,1,2,3,4,5,6,7 \
MAX_ITER=5000 SAVE_ITER=50 \
bash scripts/train_local_memory_ttt.sh
```

The script auto-resumes the largest `iter_*` checkpoint. No manual checkpoint path is required.

## Batch-size derivation

The launcher derives GA from:

```text
GA = target_global_consumers / (world_size × B_stream × T)
```

The default target is 2048, so 8×8×16 gives GA=2. If an explicit GA changes the global effective batch, the script fails unless `PSM_ALLOW_GLOBAL_CONSUMER_CHANGE=1` is explicitly set.

## Explicit fresh and strict resume

Explicit fresh run:

```bash
FRESH_START=1 OUTPUT_ROOT=/path/to/new/output bash scripts/train_local_memory_ttt.sh
```

Strict resume alias:

```bash
bash scripts/resume.sh
```

The strict alias fails if no checkpoint exists.

## Runtime-validation boundary

The historical engineering evidence in `artifacts/g0/` was collected on the single-rank route. The 8-rank code path is a new topology adaptation and must be validated on the new 8×H100 machine with the short smoke (and preferably a 20-step timing/resume check) before treating its throughput or long-run stability as measured fact.
