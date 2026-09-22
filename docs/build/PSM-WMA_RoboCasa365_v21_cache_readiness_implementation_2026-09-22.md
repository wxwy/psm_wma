> **SUPERSEDED — 2026-09-22:** RoboCasa production input has been switched to flat LeRobot v3 only. This document is retained as historical design context and must not be used as the current execution runbook. See `docs/build/PSM-WMA_RoboCasa365_v3_only_migration_2026-09-22.md`.

# PSM-WMA RoboCasa365 — v2.1 Cache Readiness Implementation

- Date: 2026-09-22
- Status: CODE COMPLETE / RUNTIME SMOKE PENDING
- Camera-layout implementation root parent: `d1938dfbd6d9ebbd7aea6a0731f29ed6ce144a33`
- Current child target after compatibility closure: `debaa3c349428bc544839b91c87b5303da38f45e`

## 1. Implemented readiness items

### LeRobot v2.1 metadata

`ActionBaseDataset` now exposes `_load_episodes()` / `_load_tasks()` hooks while preserving the previous parquet behavior as the default.

`RoboCasaLeRobotDataset` overrides them for:

```text
meta/episodes.jsonl
meta/tasks.jsonl
```

If those files are absent, RoboCasa falls back to the previous parquet loaders. A regression test covers that fallback.

### v2.1 video path

The shared `_video_path()` formatter now also supplies `episode_index`, allowing RoboCasa v2.1 templates such as:

```text
videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4
```

Existing templates that do not reference `episode_index` remain unchanged.

### Canonical domain

RoboCasa now uses:

```text
robocasa -> domain_id 30
```

The legacy PSM-WMA name `robocasa_panda_omron` is kept as an alias to 30.

No global RoboCasa raw-action dimension is registered. The source parquet happens to be 12D, but future model-side RoboCasa policy contracts may be 10/15/20D and must not be conflated with source width.

### Full-by-default encoding with optional deterministic per-task limit

**Formal/default target is the full dataset.** When `--episode-limit` is omitted, every source episode for every selected task is part of the encoding target.

`--episode-limit N` is an optional cap for smoke tests, subset experiments, or staged resource use; it no longer means first-N.

Each episode receives a stable task-aware score:

```text
SHA256(seed : task_id : episode_index)
```

The N lowest-ranked episodes are selected, then sorted only for processing order.

Properties:

- **no limit => all episodes**;
- deterministic across runs when a limit is set;
- independent of filesystem/parquet order;
- nested: the N=10 set is a strict subset of N=20 for the same seed/task;
- staged resume is monotonic: `N=10 -> N=20 -> all` only fills missing target episodes;
- if all episodes required by the current target already have valid matching cache files, the task performs no VAE encoding;
- default `--episode-seed=42`;
- selected IDs, digest, seed, source episode count and actual windows are recorded in manifests.

## 2. Source-root normalization

The cache builder now accepts any of:

```text
.../robocasa365
.../robocasa365/target
.../robocasa365/target/atomic   (when building atomic)
.../<Task>/<date>/lerobot       (single-root smoke)
```

This removes the previous ambiguity about whether `target/` belongs in `--source-root`.

## 3. Camera layouts retained

All three previously implemented layouts remain:

```text
left_wrist       : 256x512 -> current canvas 192x320 -> expected [5,48,12,20]
wrist_lr         : 384x256 -> current canvas 320x192 -> expected [5,48,20,12]
left_wrist_right : 256x768 -> current canvas 192x320 -> expected [5,48,12,20]
```

`left_wrist` remains the default first-stage route.

## 4. Cache isolation

An existing output manifest is checked before writing. Reusing the same output root for a different suite or camera layout fails closed; use a separate output root per camera-layout experiment.

Existing episode files are reused only if their stored camera layout matches the requested layout.

## 5. Tests added in child

The child test module now covers:

- 2-view horizontal composition;
- 3-view wrist-over-left/right composition;
- 3-view full horizontal composition;
- expected Cosmos canvas for all three;
- legacy camera-mode alias;
- v2.1 JSONL episode/task loading;
- v2.1 `episode_index` video path formatting;
- canonical RoboCasa domain 30 and old alias;
- fallback to the pre-existing parquet metadata format.

These tests are committed but have not been executed on the RoboCasa training server from this chat.

## 6. Runtime gate still required

Before the formal full encoding, run a real-data smoke on one task:

```text
task: CloseBlenderLid
camera_set: left_wrist
episode_limit: 2
episode_seed: 42
```

Required evidence:

1. dataset constructs from v2.1 JSONL;
2. resolved video paths exist;
3. composed source video is 256x512;
4. post-VideoResize canvas is 192x320;
5. encoded latent is [5,48,12,20] float32 finite;
6. exact_window_v1 metadata/index checks pass;
7. offline/online parity max_abs_diff <= 1e-6;
8. manifest records selected episode IDs/digest and actual window count.

After this smoke, the formal builder should be launched **without `--episode-limit`** when storage/time permit, so the target is the complete selected RoboCasa suite.

## 7. Formal cache target and staged resume

Frozen owner decision:

```text
formal default:
  --episode-limit omitted
  => encode ALL episodes

optional staged run:
  --episode-limit 10
  => encode deterministic N=10/task

later:
  --episode-limit 20
  => reuse valid N10 files and only encode newly required/missing episodes

final:
  --episode-limit omitted
  => reuse all valid existing files and encode the remaining episodes until complete
```

If the current target is already complete, the task is resume-skipped with no VAE work.

`N=10` remains useful for smoke/subset experiments and for matching a specific training sample budget, but it is **not the default corpus definition**.