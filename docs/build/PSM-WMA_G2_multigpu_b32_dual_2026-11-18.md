# Issue68: one B32/T1 engine, two production lifecycles

This is an incremental stack on PR67, not a new dataset or encoder. The final
implementation SHA and actual Gate verdicts are in the Issue68 evidence summary.
No full9126 run, promotion, training or production deletion is authorized here.

## Shared numerical and queue contract

`WanBatchEncoder` composes the unchanged #53 `WanSingleFrameEncoder` loader,
normalizer, preprocessing and fixed Child. One genuine native call receives
`[B,3,1,256,256]`, B1..32. Each output keeps its entire FP32 `[48,16,16]` grid.
There is no pooling, streaming/T32 substitute or scalar-loop batch fallback.
Each GPU has one spawned resident worker. The coordinator exposes physical
`CUDA_VISIBLE_DEVICES=4,5,6,7`; each child exposes one physical GPU and uses its
logical `cuda:0`. Workers consume the same SQLite EventSpool, across episodes
and Views. No encode operation holds the coordinator or SQL writer lock.

The batch recipe is distinct from legacy B1, including deterministic flags and
workspace policy. Even actual B=1 under this policy is a new numerical recipe.
Existing B1 `encoding.py`, `encode_record()` and old recipes remain unchanged.
Measured nonzero differences against legacy B1 are reported, never relabeled
as bit equality. Different batch membership is a different execution context.

`engine_batches` pins the ordered original final-pixel descriptors and recipe.
`engine_members` links actual `(job,event)` rows. A short claim creates an
immutable batch and fenced lease/token. Heartbeats are independent of encoding.
At most32 images are selected when full or the oldest image reaches500ms by
default. A tail remains T1. Each record holds a deduplicated batch-context ref,
its position, actual GPU/device, worker, attempt and descriptor fingerprint.

Existing per-record atomic/fsync writer and ACK are reused. All batch PNG BLOBs
remain until every numeric member is persisted and reverified. A crash resumes
the same ordered batch. Already durable members must compare exactly before
missing members can be published. If all files exist, recovery only ACKs them.
OOM or a replay difference fails with source retained; no implicit split or
batch resizing. The owned-process supervisor reclaims a dead worker's lease;
tokens reject stale writes. Numerical reservations, pending BLOB/event limits,
active-job bounds, disk watermark and restart limits are finite.
If completed staging consumes the numeric budget and no batch can be admitted,
the coordinator gives source-ready/finalization/GC a bounded chance to progress
(existing worker timeout, default300s), then explicitly fails with source and
fixed-batch results retained. Busy state cannot suppress this capacity failure
forever. Budgets are never enlarged or batch membership changed implicitly.

Completed numeric staging and active SQL batch/member rows are collected only
after all member jobs have genuine existing completed-job tombstones. Small
worker logs, completion receipts and empty lock directories are audit/control
metadata; they are not extra source JSON copies or latent records.
The old B1 pending-pixel sharing optimization applies only to B1 storage keys;
equal RGB from another episode cannot pin a distinct batch/position chunk.
Native-call counts and queue-wait ranges are separate from ACK-only recovery
counts; logs retain the actual CUDA duration and encode-API intervals.

## Independent View-first lifecycle

The watcher reads only episodes with their own COMPLETE. Partial/staging
directories and task directories not yet published do not become errors or
sources. It verifies the original View-only profile, gzip/raw receipt, actual
owners and immutable PNG bytes, then offers those events to the shared engine.
Explicit task/episode selectors apply even to a directly supplied episode root;
dataset catalogue locations must match the manifest identity.
It never reruns F27, MuJoCo, ROS or SG. Reference states are indexed without
being re-encoded. Compact owner/state identity still comes from sealed source.
Recovery revalidates and re-offers a published independent job left between
durable registration and source offer. It never treats sync's still-producing
job as a published source. Startup failures release target leases and children.

VAE has its own manifest/COMPLETE. Original episode/profile COMPLETE and
Views/SG/tasks/language/metadata do not change during B. Stage C is the existing
explicit `retire_view_first_sources`, with a separate genuine verified-cache
handoff and posthoc policy. The watcher does not silently delete sources.
After C it validates the final capsule/cache; it does not restore full JSON.

Default idle600s expires only when no active jobs, pending/in-flight batches or
new publications exist. This returns **IDLE_TIMEOUT**, not corpus completion.
`--resume` watches for later publications and reuses valid complete caches.
`ALL_COMPLETE` additionally requires a pinned `g2_vae_expected_episodes_v1`
list `(episode_key,source_fingerprint)` and `g2_view_publisher_done_v1` with
`complete=true`, matching list SHA, dataset root, exact episode count and no
failed episodes. Every selected final cache is independently verified again.

Draft command (existing environment, new external bounded spool):

```bash
CUDA_VISIBLE_DEVICES=4,5,6,7 "$PY" -m tools.g2.run_spatial_vae_engine \
  --execute --mode independent --dataset-root "$VIEW_DATASET" \
  --spool-root "$NEW_BATCH_SPOOL" --weights "$WEIGHTS" \
  --cosmos-root "$FIXED_ROOT/cosmos-framework" \
  --gpus 4,5,6,7 --max-batch-size 32 --max-wait-ms 500 \
  --idle-timeout-s 600 --resume
```

The old build CLI also delegates explicitly with `--engine batch --view-first
--batch-size 32 --spool-root ...`. Its default legacy path stays B1 and strict.
Both entrypoints use the same engine, not two independent implementations.

## Synchronous View+VAE lifecycle

The original `full_production.py` gains optional `vae_engine` configuration;
unset preserves legacy B1. Renderer, state compaction, final material/background
and robot-arrow paths are untouched. Existing final-pixel events enter the
same engine before source-ready. No model is loaded per renderer. Source-ready
seals the actual final owner mapping; early extra events cannot change it.

Once all relevant immutable batches are durable, the original writer assembles
one file per episode/logical View, verifies the cache and publishes the full
profile. Existing v2 retirement and owned work/record collectors run afterward.
Source/final-cache/index/transaction verification precedes deletion. Sync has
no idle exit; the producer supervisor stops it only after drain or an explicit
pause. SIGTERM is a pause, never fabricated successful completion.

Example additional production-config fields:

```json
{
  "vae_engine": {
    "gpus": [4, 5, 6, 7],
    "max_batch_size_per_gpu": 32,
    "batch_wait_ms": 500,
    "idle_timeout_s": 600
  },
  "allow_shared_gpu_processes": true,
  "max_events": 512,
  "max_spool_bytes": 536870912,
  "final_source_format": "capsule_v2"
}
```

All original fixed Root/Child/nav, environment, plan, path isolation, immutable
mapping and manual-start checks still apply. Shared GPU processes require the
explicit config flag; no existing process is stopped. This Gate has Owner's
explicit GPU4-7 sharing authorization. Recipe must be freshly planned/pinned;
never insert the B1 recipe into a B32 config.

```bash
"$PY" -m tools.g2.run_stage_a_production preflight --config "$NEW_CONFIG"
"$PY" -m tools.g2.run_stage_a_production run --config "$NEW_CONFIG" --manual-start
"$PY" -m tools.g2.run_stage_a_production resume --config "$NEW_CONFIG" --manual-start
```

These are production drafts, not an instruction to launch corpus work now.
Output/work/spool/run must be fresh nonoverlapping staging paths. The current
`tmux view` and its data/configuration are excluded from mutation and cleanup.

## Gates and recovery

CPU commands: `docs/collab/codex/evidence/2026-11-18_issue68/cpu_commands.sh`.
They retain all612 historical identities and old test source bytes, plus new
batch/lease/ACK/real OS crash/discovery/idle/final-source tests. Legacy B1
negative cases stay intact. Optional dependency skips are reported explicitly;
the existing server PSM environment must run them without installation.

`real_gate.py` runs only two copied View episodes in a fresh private namespace
for independent B/C. It publishes the second after the watcher starts, requires
actual mixed-episode B32, verifies all View files, then explicitly retires only
those copies and replays the original contexts. The sync Gate uses the original
official producer with fresh outputs, actual MuJoCo/native/F27, two episodes,
dual top/Island/absent directions/changed states, early durable ACK and a real
owned worker hard exit after ACK. Both require genuine multiple-GPU work,
full publication/GC, post-retirement readers and exact same-context re-encoding.
The fresh sync per-state pixels/view availability are compared with verified
originals. Private data/models/images/logs remain on the server.

Failure before VAE, corrupt cache/source/context or failed final publication:
retain source and legitimate products. Fsynced incomplete numeric chunks can
be retried only under their original membership/recipe. Retirement crashes
continue via the unchanged v2 journal and fsync protocol before ordinary reads.
Independent B and C coordinate through the existing per-target lease; the
engine coordinator lock prevents two managers but never serializes GPU encode.
Each ordinary training reader still opens only requested per-View files and
does not import VAE/producer/ROS. Real replay is separately explicit:

```bash
CUDA_VISIBLE_DEVICES=4 "$PY" -m tools.g2.verify_spatial_vae_batches \
  --dataset-root "$ISOLATED_DATASET" --weights "$WEIGHTS" \
  --cosmos-root "$FIXED_ROOT/cosmos-framework" --device cuda:0
```

No `training_ready=true` is produced. BOTH `INDEPENDENT_VAE_E2E=PASS` and
`SYNC_VIEW_VAE_E2E=PASS` are mandatory; CPU fixtures or old169 B1 observations
cannot substitute. Exact executed commands/raw results/timing and NOT_RUN
items must accompany the fixed implementation. Two samples do not establish
9126EP throughput, capacity, task coverage or release approval.
