# Issue #4 — No-TTT spawned CPU Worker candidate

2026-10-26 (Asia/Shanghai). Implementation candidate only. Owner task: `docs/collab/chatgpt/requests/2026-10-26_Codex_V3_Matched_No_TTT_multiprocess_workers_optin.md`. Production baseline `e6ae2084305a8c24d763d82b517984660cc73c30` / Child `923d9c3fd392e6bafbdb1771a292c7b313e6b3dc`; development starts at following docs HEAD `0beaeacd7d00b0b5826b3eac12b86676eb8b7db3`. Publish only `v3-nottt-process-workers-20261026` in both repositories. **Do not merge V3/v3-local-ttt before GPT Gate. Do not change any live checkout/job/checkpoint/source/cache/index.**

## Why the official recipe cannot simply replace this sampler

Official `RankPartitionedDataLoader` allocates datasets/ranks and builds a real PyTorch DataLoader; `PackingDataLoader` packs ordinary sampled inputs to token budgets. Neither owns this job's dynamic, immutable `ExactWindowRankPlanner` windows or its committed slot/cursor Frontier. Replacing `GroupedTriggerLoader` with the ordinary recipe would alter rank partition, episode/rebind order, member counts and Resume cursor.

This candidate therefore uses the **real PyTorch DataLoader**, with a map-style raw Dataset and a parent `WindowSampler` emitting frozen per-segment jobs. It does not claim the official RankPartitionedDataLoader or PackingDataLoader itself is the training producer. No ThreadPoolExecutor is used. The native collator and native model/outer loss remain in the parent.

## Process and ownership contract

| Actor | Owns / executes | Excludes |
| --- | --- | --- |
| Trainer main | Sole planner/frontier; existing verified SourceReader/LeRobot/Arrow; verified per-window source snapshots; ordered `producer.materialize`, every Python/Torch/NumPy stochastic Transform, native collate, model/gradient/optimizer | No worker-owned state commit |
| Spawned DataLoader worker | Cache catalog/contract metadata, CPU source snapshot for its exact request; mmap Episode reader, existing raw-policy adapter and raw ABI checks; bounded CPU result encoding | No live LeRobot/HF/Arrow reader, planner/frontier/tokenizer/model/optimizer, CUDA, checkpoint, simulation |
| Checkpointer | Existing F0/F1 synchronous save/RNG protocol plus opt-in No-TTT committed frontier callback | No in-flight requests, worker PID, iterator, queue or prefetch state in checkpoint |

`ExactWindowSegmentProducer.prepare` first validates the parent request capability. Its local step offsets are explicitly converted to flat indices for IPC. Workers echo a token covering exact slot/episode/cursor/segment/binding epoch/count; parent checks token, actual child PID, ordered flat indices and packet size, rebuilds the original cached zero-video representation and invokes the original parent `prepare/materialize`. No Local module/scan/fast weight/prefix exists.

Per-window job order is member-major then stable slot-major, identical to the Planner. Standard ordered DataLoader return is retained. B8 is divisible by all supported worker counts1/2/4, so slot-to-worker round-robin affinity repeats each member; the same Episode is not concurrently deserialized by several workers in one rank. Four rank shards stay as already frozen for world4. This does not make world4's episode partition equal to old world8.

SourceReader itself reads cache identities. The **opt-in** path replaces both of its parent cache readers with one bounded mmap reader too; otherwise parent source identity reads would eagerly load whole latent Episodes before Worker startup. No file is rewritten. The unchanged zero-worker path never constructs this adapter or changes its readers. Existing window/identity checks are reused; mmap Episode header validation matches the original reader and file version changes fail closed. Initial metadata setup and Source/Arrow reads remain serial in the trainer, so Worker support is not a claim that this source-read cost is parallelized.

## RNG and spawn boundary

The official DataLoader receives its own CPU `torch.Generator`; base-seed draws do not consume the training generator. The sampler is deterministic. Parent raw-source snapshot work and production worker raw-policy/cache work are checked not to change Python, NumPy or Torch CPU global RNG. Every stochastic Transform executes once in original order in the parent. Unsupported random raw-read behavior fails closed rather than silently changing augmentation.

Workers use `spawn`, not fork after NCCL/CUDA initialization. `CpuSpawnProcess.start` temporarily scopes CPU-only CUDA visibility/COSMOS_DEVICE, empty rank/distributed env and single-thread BLAS/OpenMP settings **before interpreter launch and unpickling**, then restores the parent's original environment in `finally`. This control is main-thread only. `worker_init_fn` also applies CPU/thread/offline restrictions and checks CUDA is not initialized. Tests use a CPU PyTorch build and simulated parent CUDA labels; actual CUDA process behavior remains the target-host Gate.

## Bounded memory, IO and lifecycle

- Metadata recipe only: no raw dataset/live readers/model; serialized metadata cap64MiB.
- Source snapshots: CPU-only compact cloned storages, bytes envelope, cap1MiB/segment; at most32 segment jobs in a world4/GA4/B8 window. No source tensors leak through queue reducers into shared storage/file-descriptor fan-out.
- Result: exact window tensors cloned before encoding; zero-video pixels transported only as a shape tag and reconstructed to the original dense/compact representation in parent. Result bytes cap32MiB/job, avoiding IPC export of an entire Episode tensor storage. All tensor values/ABI remain equal.
- `workers=1/2/4`, prefetch factor1/2. At most `workers × factor` tasks outstanding (max8). `pin_memory=False`; tensors transfer through the existing main-process native path.
- mmap cache: at most `8/workers` Episodes/worker and2GiB mapped file bytes per reader; parent identity cache at most8 Episodes/2GiB. A too-large Episode or metadata/window count is rejected, not loaded eagerly. These are mapped-file/packet/entry bounds, **not a claim of a hard RSS cap**. Python/Torch imports, Arrow in parent, OS page cache and decoder metadata need independent real-host RAM measurement.
- Persistent workers default on only for opt-in workers; explicitly off is supported. All results must be consumed before a window finishes; next-window reset reuses idle workers only after commit. No speculative next-window Frontier is published.
- Any raw/order/ABI/timeout/crash/cancel/optimizer error closes owned workers, clears pending jobs and poisons the Trainer instance. Restart uses a new pool from the last committed checkpoint, never a partially consumed iterator.
- Cleanup retains exact Process handles even for partial startup, unregisters only its own DataLoader SIGCHLD registration, then bounded TERM→KILL/join, closes feeder queues and checks exit codes. Foreign controls survive. A process trapped in uninterruptible kernel IO cannot be promised killable; surviving handles/PIDs remain a non-success cleanup diagnostic.
- A narrow PyTorch-private lifecycle seam (`_MultiProcessingDataLoaderIter`, PID registry and queue shutdown fields) is isolated in this adapter because the public DataLoader API has no bounded close/partial-startup recovery method. DS must validate the real training Python/Torch version; author CPU version is in Evidence. No global PID-name kill, global waitpid or general Trainer change.

## Identity and compatibility

`workers=0` keeps its old argument list, data calls, transforms/RNG, config/semantic digest and `psm_v3_matched_no_ttt_frontier_v1` schema. New flags default disabled; G1's `--num-workers` still denotes its old threads. World8 No-TTT remains unchanged.

Opt-in is **world4/GA4/T16/B8 only**, new job suffix `_mpwN_world4_ga4`. Profile includes worker count, prefetch, persistence, timeout, transport/cache bounds and source/transform mode. It is in training semantic identity/config digest, launch effective-source metadata and structured runtime audit. No-TTT worker checkpoint format is `psm_v3_matched_no_ttt_loader_frontier_v1`; the old format is unchanged. Worker-count/options changes or zero↔worker same-job Resume fail. All original rank/world/seed/GA/source/cache/receipt/model/optimizer/scheduler/RNG authorities remain; in-flight state is absent and snapshots reject pending/failed windows.

The Owner's world4 **Root status/HEAD/Child HEAD/Gitlink exemption is unchanged**. No new Git admission check is added; source identity continues to say `nottt_world4_ga4_source_head_not_verified`. Formal candidate SHAs identify review objects, not a restoration of startup SHA pins.

## Candidate usage (not runtime authorization)

Required paths/venv/CUDA4–7 behavior are inherited from the existing launcher. New environment interface:

```bash
# Old behavior, with no new flags or identity fields:
NOTTT_LOADER_WORKERS=0 bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 100

# NEW independent job; only after code/DS/Owner runtime gates:
NOTTT_LOADER_WORKERS=2 NOTTT_PREFETCH_FACTOR=1 NOTTT_PERSISTENT_WORKERS=1 \
  NOTTT_LOADER_TIMEOUT_S=120 \
  bash scripts/train_v3_matched_no_ttt_4gpu.sh fresh 100
```

Default opt-in job is `no_ttt_packed128_droid_fresh_30k_mpw2_world4_ga4` for workers2; explicit JOB_NAME must carry the matching suffix. Never enable workers on the current running No-TTT or G1 job. Zero workers rejects prefetch/persistent/timeout env options. CLI uses separate `--no-ttt-loader-workers`, `--no-ttt-prefetch-factor`, `--no-ttt-persistent-workers` or `--no-ttt-nonpersistent-workers`, and `--no-ttt-loader-timeout-s`; old `--num-workers` stays0 for this profile.

## Metrics and acceptance

Structured `[NoTTT][cpu_loader]` stdout is emitted per committed rank/iteration: actual worker PIDs/count/config, source snapshot host time (including source reads/serialization), worker prepare-time sum, parent result wait, decode/rebuild, materialize including Transform, separately timed Transform, native collate, complete step-window host wall before telemetry (includes nonpersistent shutdown), observed worker RSS and mapped cache entries/bytes. Host waits are **not GPU idle time**. Capture stdout together with existing native Forward/Backward/optimizer/straggler telemetry.

CPU matrix covers single and four logical ranks, full and terminal B8/T16/GA4, worker0 vs1/2/4, actual native collation/tensor equality, stochastic transforms/parent RNG, consumer ordering/weighted scalar and generation toy gradient, real synthetic `.pt`/parquet/mmap/policy path, PID/startup/persistence/bounds/crash/timeout/ignoredTERM/cancel/restart/foreign controls, identity and malformed state. Four logical ranks are executed sequentially on CPU: not a Gloo/NCCL/FSDP performance or collective test.

The synthetic full CPU state test runs each logical rank Fresh100 and same-state Resume101→500 with a **scale-reduced T1/B1/GA4 toy model**, real momentum/scheduler/Python/NumPy/Torch RNG and the actual frontier callback. Full B8/T16/GA4 is verified separately. This is not real DCP, CUDA RNG, model-gradient or physical world4 Save→Resume evidence.

Three baseline fixture defects reproduced against original923d9c3 code are corrected without weakening behavior: initialize the world4 test catalog outside its accidentally escaped comment; match the exact current standing-G1 rejection message; compare text stderr to the exact text diagnostic. No G1 production fix accompanies these test repairs.

After candidate publication: GPT fresh incremental review → DS clean detached CPU → separately authorized S0 real-input/RAM/PyTorch lifecycle validation → Owner-authorized CUDA canary/perf matrix0/1/2/4 → real Fresh/Resume. Same assets, plan, batches, augmentation/RNG, GPU/resources and staged budgets must be frozen for performance comparison; report medians/tails, rank stragglers, source/read/wait/Transform/Collate/Forward/Backward/step wall, worker/parent RSS/CPU/IO and GPU memory. Do not call CPU fixture wall time an H100 speedup. No live job migration or automatic V3 merge follows author PASS.
