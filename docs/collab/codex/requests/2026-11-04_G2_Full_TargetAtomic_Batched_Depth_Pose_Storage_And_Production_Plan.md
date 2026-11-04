# G2 full target-atomic — staged Depth/Pose production and storage proposal

Date: 2026-11-04, Asia/Shanghai. **Planning only; no new export authorization.**
Authority: Owner correction `a8da67f9c69c5936a681b3061d781436911b5f1b`,
[full-source clarification](../../chatgpt/reviews/2026-11-04_G2_Full_RoboCasa_Training_Cohort_Owner_Clarification.md).
This supersedes the requirement to find a historical N100 training cohort.
The old intake/audit/publication records remain historical evidence.
Approved source remains Root `3eb8b334150018212ae1f51afb5e954b83fa1186` /
Child-Gitlink `1069fe78841228cadbbfbe6afbd767eaed6225da`; bounded Gate C is closed.

## Production target and identities already established

Depth/Pose coverage targets the full source: **18 task classes, 9126 episodes,
2231347 complete source frames**, two 256×256 cameras. Local-TTT and No-TTT
use this full dataset lineage without an N100 cap. Both recorded `split=train`,
`split_seed=42`, `split_val_ratio=0.01`; this does not mean that every source
episode is consumed by train. Do not infer train IDs/counts by subtracting a
rounded 1%, change training splits, or make effective-train enumeration a blocker
for producing Depth for the full source. Future consumers must retain the split.

Existing server-local authoritative inputs, verified in the audit:

| Input | SHA256 |
| --- | --- |
| Flat `flat_v3_mapping.parquet` | `aa884820494a17f50b41a8a8c2bfa6b6fda11babbbef31c449c1c0ce850e09ed` |
| Full G0 `dataset_manifest.json` | `8e63c73b4e07cdbebd6427d9efdd3f2d8b293ecd10511cae25a55c6566f6db88` |
| Full verified-index `receipt.json` | `247e5a853cbc2ddd007cb4b243b492f8337179276fade9b191f6bb4fe0d5798c` |

The full manifest is at
`/mnt/data/shenzhen/szrobot/logs/.tmp_backup/datasets/robocasa365-target-atomic-left_wrist-exact_window/dataset_manifest.json`.
9126 selected/accepted/index/mapping members agree; episode cap is null.
The 2085331 overlapping exact windows are not the full-frame budget. Reuse
these established inputs; do not search for or manufacture a historical N100
receipt, resample seed42, or reconstruct a training subset.

## Storage and elapsed-time reference

Raw arrays are `393560 * full_frames`: 2-byte Depth + 1-byte valid mask,
float32 K/GL/CV poses and int64 indices for both cameras. Original RGB remains
a reference and is not duplicated. Full raw arrays: **878168925320 B**
(817.859 GiB). This is not compressed disk usage.

The audit recorded free space **137476116480 B** (137.476 decimal GB) on
`/mnt/data1` at 2026-11-04 13:20 UTC; refresh it before any execution.
Gate C observed 335313120 raw-array bytes, 46507310 NPZ bytes and 47675013
committed task bytes over 852 frames. Scaling these three scenes gives:

| Scenario: empirical estimates, not capacity guarantees | Decimal GB |
| --- | ---: |
| Full NPZ payload, exact Gate C per-frame ratio | 121.800 |
| Additional committed metadata, crude per-frame proxy | 3.058 |
| Payload + metadata proxy | 124.859 |
| Payload 10% larger + same metadata proxy | 137.039 |
| Payload 20% larger + same metadata proxy | 149.219 |
| Least-compressible of the 3 observed tasks + metadata proxy | 139.055 |

At the 10% scenario only about 0.438 GB remains before active staging or logs,
already less than 1 GiB. Metadata also depends on episode/chunk counts and can
exceed this proxy. These estimates are **not a full-corpus measurement** or an
upper bound. Source audit/Owner records and exact arithmetic are bound in
`docs/collab/codex/evidence/2026-11-04_g2_full_corpus_budget/reference_budget.json`.

The earlier `2*raw+1GiB = 1757411592464 B` conservative scenario is retained
in its original report; it is **not an implementation requirement for two full
raw disk copies**. Existing export writes compressed chunks in one episode
staging directory and atomically renames that directory. Capacity planning must
count cumulative committed data plus active episode/batch staging, preserved
failures, metadata, validation evidence, shared-disk growth and a safety reserve.
Batching bounds temporary work; it does not solve final cumulative occupancy.

The one-worker time proxy is `2231347*220.50/852`, about 6.68 days for export
alone. It is not an approved deadline, and task mix/startup, full verification,
previews and retries can change it. Reported peak RSS 5051668 KiB is a three-scene
measurement, not a whole-dataset bound. Initial production proposal remains one
CPU/OSMesa replay process; parallelism needs its own measured resource budget.

## Placement and retention decision before rendering

Preferred: allocate/expand durable **local storage on the authorized server**,
then approve a concrete full-coverage quota plus headroom and output path.
Current free space does not justify unattended full-corpus execution based only
on the mean compression proxy. No other volume's path/capacity is assumed.

If storage is not ready, a separately authorized first batch can be produced
and retained, then stop for review of actual bytes/time and remaining capacity.
Do not automatically continue all batches. Moving new production data between
server-local volumes requires a named placement/verification/retention plan;
this document performs or authorizes no copy/delete operation. Server sensor
files must not leave the server, including transfer to this cloud workspace.
Do not free space by deleting old Gate B/C, DCP, latent caches or historical
Evidence, and do not stream into nav_sg then discard Depth without an explicit
later retention decision.

## Proposed first batch policy — explicit new production partition

Recommend **at most 100 episodes total per batch**, not 100 per task. This is a
proposal for the next decision, not a frozen selection or historical training
identity. Reuse existing `source.select()` episode sharding of the full manifest:
`num_episode_shards=ceil(9126/100)=92`, shard IDs 0..91. Current source sorts
`(task_class,global_episode_index)` and takes `picked[shard::count]`; no sampler
implementation is needed. This yields 18 batches of 100 and 74 of 99, collectively
9126. Count limits do not bound bytes: frame totals and maximum episode length
must be frozen per batch. The first manifest and its exact IDs are not yet made.

Connected execution role's next **read-only** preparation:

1. Recheck the three known input hashes and original roots. Reuse existing
   `selected_episodes`, `mapping_episodes`, `select` on server; no renderer.
2. Freeze all 92 batch member lists/SHAs and per-task/episode/frame/shape totals
   as new production metadata. Prove pairwise disjointness, exact union with the
   9126-member source, total 2231347 frames and no dropped/duplicated IDs. Do not
   derive frame totals from window_count. Report task coverage of the first batch.
3. Compute each batch's exact raw arrays and conservative storage/time proposal;
   inspect the largest batch/episode. Refresh target filesystem bytes/inodes and
   competing disk growth, choose a named local storage destination, hard reserve,
   staging/failure allowance and first-batch wall/RSS/stop limits. Do not assume
   the previous free-space snapshot is current.
4. Run only the existing non-rendering CLI for proposed batch 0, in a clean exact
   approved checkout, with private caches, empty CUDA and one numeric thread.
   Use a new external evidence directory and an absent proposed cache root.
   Discovery plus dry-run may use one 30min outer preparation watchdog (TERM at
   1785s, KILL 15s later), never a renewed timer per substep. Server temporary
   validation scripts are allowed; record their command/SHA and keep them local.

Prepared command **inside** that bounded metadata runner, not executed here:

```bash
cd "$CODE_ROOT"
env CUDA_VISIBLE_DEVICES='' MUJOCO_GL=disable \
  OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  "$SIM_PYTHON" -m tools.g2.export_robocasa_rgbd_pose \
    --raw-root "$RAW_ROOT" --flat-root "$FLAT_ROOT" \
    --output-root "$NEW_PRODUCTION_CACHE" --selection-manifest "$FULL_G0_MANIFEST" \
    --episode-shard 0 --num-episode-shards 92 \
    --cameras robot0_agentview_left,robot0_eye_in_hand \
    --state-index-policy frame_index --depth-format uint16_mm --chunk-frames 32 \
    --dry-run > "$NEW_EVIDENCE/batch_000_dry_run.json" \
    2> "$NEW_EVIDENCE/batch_000_dry_run.stderr.log"
```

Omit `--frames` for full episodes. No output cache should be created by dry-run.
This freezes a new proposed batch, not a training split. If Owner/GPT chooses a
different batch size/policy, refreeze metadata before rendering; do not substitute
another cohort silently. The 100-total/92-partition proposal is not yet approved.

## Execution and coverage contract still to approve

After placement and batch 0 identities/limits are concrete, obtain separate
production execution approval. For stop-on-first-error, reuse the approved
single-episode CLI under a frozen batch controller: the multi-episode CLI catches
per-episode errors and may continue, so its end-of-batch failure is not immediate
stop. No production code change is demanded by this planning document.

Keep uint16-mm/chunk32, original RGB, source/frame/state binding, Depth/masks,
K/GL/CV poses, immutable atomic episode commits and verified skips unchanged.
Maintain a server-local coverage ledger: planned/exported/verified/failed/pending
episode IDs and frame counts, batch manifest SHA, payload/report identities,
elapsed/RSS/disk, location and external visual provenance where reviewed. Only
valid committed episodes count as coverage. Resume reuses verified commits and
restarts unfinished episodes; preserve failures and stop on drift or budget
exhaustion. A batch's completion is not permission to start the next batch.

Full completion requires the planned union's 9126 episodes / 2231347 full frames
with the agreed production validation, without promoting sampled Gate C checks
to every-pixel accuracy. Existing `rgbd_pose_schema.md` is the later nav_sg data
interface. No converter, training/Config/DCP change, GPU/EGL run, V3 merge or
production export is authorized by this proposal. Gate C remains closed.
