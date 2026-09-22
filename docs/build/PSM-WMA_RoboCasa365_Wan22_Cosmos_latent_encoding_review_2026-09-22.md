# PSM-WMA RoboCasa365 Wan2.2 Cosmos-style Latent Encoding — Review

- Date: 2026-09-22
- Status: **APPROVE WITH CHANGES**
- Reviewed current child: `3fe91004471c74a728df960c05b5eb43ac120510`
- Upstream semantic reference checked: `c23e51f`

## 1. Verdict

The overall route is sound: RoboCasa365 v2.1 -> three-camera composition -> training-equivalent uint8/VideoResize -> independent 17-frame Wan2.2 exact-window encoding -> `exact_window_v1` cache.

Do not start the full build exactly as drafted. Before the full run, fix/clarify:

1. v2.1 episode/task metadata loading;
2. canonical RoboCasa domain identity;
3. v2.1 video path formatting with `episode_index`;
4. deterministic per-task episode subset selection;
5. the builder `--source-root` convention;
6. initial episode limit chosen by **training sample/window budget**, not by disk capacity alone.

## 2. Camera / canvas / latent contract — APPROVED

Current three-view composition is internally consistent:

- wrist 256x256;
- agentview left/right each resized to 128x128;
- bottom row 128x256;
- composed frame 384x256.

`resolution=None` sees min dimension 256, selects tier `256`. The nearest predefined aspect is the 9:16 canvas `(W=192,H=320)`. Aspect-preserving resize yields approximately 288x192 content plus reflection padding to 320x192.

Therefore the expected exact-window latent contract is:

```text
17 RGB frames
-> canvas 320x192
-> spatial compression 16
-> 5 causal latent frames
-> latent [5,48,20,12] float32
```

The draft is correct on this point. Reusing `to_training_uint8`, `VideoResize(resolution=None)`, `encode_uint8_vision_item`, the frozen Wan2.2 chunk contract, and `cudnn.benchmark=False` is the right route.

## 3. v2.1 metadata compatibility — APPROVE THE HOOK APPROACH

Current `ActionBaseDataset.__init__` hardcodes v3-style `meta/episodes/chunk-*/file-*.parquet` and `meta/tasks.parquet`. The staged RoboCasa data uses v2.1 `meta/episodes.jsonl` and `meta/tasks.jsonl`.

Refactoring the base constructor to call protected `_load_episodes()` / `_load_tasks()` hooks is acceptable if the default implementation preserves the current v3 behavior exactly and only RoboCasa overrides it.

Upstream `c23e51f` solves this more comprehensively by using `BaseActionLeRobotDataset` and the official LeRobot reader. That is cleaner long-term, but migrating the whole PSM-WMA data stack now is larger than necessary for cache generation. Keep the current branch and use the upstream implementation as semantic reference.

## 4. Domain registration — MODIFY THE DRAFT

Current local RoboCasa class requests `domain_name="robocasa_panda_omron"`, but the current domain table has no such entry.

Upstream `c23e51f` uses canonical domain `robocasa: 30` and deliberately does **not** freeze a single `RAW_ACTION_DIM`, because the model-side RoboCasa action contract may be 10D arm-only, 15D mobile-base raw, or 20D mobile-base ego.

The stored source action is 12D, but source width is not the same thing as the final model action contract.

Recommendation:

- use canonical `robocasa` domain ID 30 where practical;
- if `robocasa_panda_omron` is retained temporarily, make it an alias to 30;
- **do not freeze global raw_action_dim=12 merely for latent-cache construction**.

## 5. Video-path issue — REAL, BUT CAMERA-KEY DIAGNOSIS WAS PARTLY WRONG

The current local RoboCasa loader already uses the full camera keys `observation.images.robot0_*`; it is not currently using short camera names.

The real v2.1 incompatibility is that base `_video_path()` does not provide `episode_index` to the `info.json` path formatter, while v2.1 uses `episode_{episode_index:06d}.mp4`.

Minimal fix options:

- override RoboCasa `_video_path()`, or
- preferably add `episode_index=int(episode["episode_index"])` to the generic base formatter, which is backward-compatible with templates that do not use it.

## 6. Source-root contract — MUST CLARIFY

The current builder searches `source_root/<atomic|composite>/*/*/lerobot`. Therefore the current CLI should use:

`--source-root /mnt/data1/data_v2_0617/robocasa365/target`

not the parent `.../robocasa365/`, unless the builder is modified to normalize the optional `target/` level.

## 7. Episode-limit policy — DO NOT USE FIRST-N

The current builder implements `episode_ids[:episode_limit]`, which means first-N episodes, not a representative subset.

Use a deterministic per-task permutation keyed by `(seed, task_id)`, then take its prefix N. Record the seed and selected episode IDs (or a digest) in the manifest.

This also gives nested growth: N=10 can later extend to N=20 without invalidating the first subset.

## 8. Initial N should be chosen by sample count

For E003-style comparisons, the most important matching variable is training sample amount.

Using the reported corpus averages:

```text
atomic:    2.23M / 9126  ~= 244 frames/ep -> ~228 windows/ep
composite: 12.73M / 16181 ~= 787 frames/ep -> ~771 windows/ep
```

Across 18 atomic + 32 composite tasks, one additional episode per task contributes roughly 28.8k exact windows.

The archived LIBERO cache has 246,377 windows. Therefore:

```text
N ~= 9/task  -> ~259k windows
N = 10/task  -> ~288k windows
N = 20/task  -> ~575k windows
```

Recommendation: **build N=10/task first**. This is much closer to the existing LIBERO training-data scale, uses roughly ~65 GB under the draft's storage model, covers all 50 target tasks, and can be extended later.

N=20 is storage-feasible (~130 GB) but should be treated as an expansion, not the default simply because disk permits it.

After N=10, use the actual manifest `window_count` rather than averages to decide whether to extend.

## 9. Storage / extraction — APPROVED

The draft estimate of about `6.5N GB` is reasonable in magnitude for `[5,48,20,12]` fp32 exact-window latents.

Sequential `extract one task -> encode -> verify -> delete extracted lerobot -> retain tar` is appropriate. Do not delete the extracted task until atomic outputs and task-level validation have completed.

## 10. Validation — APPROVED WITH SUBSET PROVENANCE ADDED

Keep:

- parquet row / timestamp / decoded-frame alignment;
- manifest contract;
- per-window dtype/shape/finite/index checks;
- online/offline parity using the exact same VAE route and cudnn settings.

Add:

- selection seed;
- selected episode IDs or digest per task;
- actual windows per task;
- actual total window count.

This is necessary because sample amount is the primary fairness axis.

## 11. Three-camera choice

The three-camera layout is valid and uses all available observations. It is not pixel-level matched to LIBERO's two-view concat, but RoboCasa is a new benchmark, so that is acceptable.

Freeze this camera layout before encoding. If a later experiment chooses upstream's optional `left_wrist` layout, build a separate cache rather than silently reusing this one.

## 12. Final decision

### Approved

- exact_window_v1;
- 17-frame stride-1 windows;
- 384x256 three-camera composition;
- 320x192 Cosmos canvas;
- `[5,48,20,12]` latent;
- cudnn benchmark off;
- sequential task extraction;
- parity gate;
- minimal compatibility patch on the current branch rather than a project-wide rebase.

### Must change before full build

- v2.1 episode/task loading;
- domain registration without globally freezing raw action width to 12;
- episode-index-aware video path;
- deterministic per-task episode sampling;
- source-root convention.

### Recommended first cache

`episode-limit = 10 per task`

because the first-order goal is sample/window-count alignment with the existing LIBERO E003 scale.

## 13. Review verdict

> **APPROVE WITH CHANGES.** Keep the current PSM-WMA branch, borrow upstream `c23e51f` semantics as reference, make the minimal compatibility fixes, encode a deterministic N=10/task subset, verify parity, then decide whether to expand to N=20.