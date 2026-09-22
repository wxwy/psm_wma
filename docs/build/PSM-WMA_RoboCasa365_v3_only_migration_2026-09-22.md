# PSM-WMA RoboCasa365 — LeRobot v3-only migration

Date: 2026-09-22

Current child implementation: `01c0d1ef002dc1d707af83196b43741f61f32654`

## Decision

RoboCasa input support is now intentionally v3-only.

The canonical target sources are the three flat EMBER RoboCasa365 LeRobot v3 mirrors:

- robocasa365-target-atomic
- robocasa365-target-composite-seen
- robocasa365-target-composite-unseen

The old task/date/lerobot v2.1 hierarchy, JSONL metadata overrides, per-episode video-path logic, and tar orchestration are no longer part of the RoboCasa production path.

## Critical task identity rule

LeRobot v3 task_index indexes natural-language phrasings. It must not be used as the 18/16/16 underlying RoboCasa task class.

The v3 mirrors provide annotation.human.task_name as a global task-table index. The loader/builder resolves that index through meta/tasks.parquet and uses the resulting task string as task_class.

All deterministic episode limits are therefore per underlying task_class.

## Input layout

One flat local LeRobot v3 root per suite:

- target atomic: expected 18 task classes
- target composite seen: expected 16
- target composite unseen: expected 16

The cache builder fails closed if the recovered class count differs.

## Camera layouts

Unchanged:

- left_wrist (default): 256x512 -> current 192x320 canvas -> expected [5,48,12,20]
- wrist_lr: 384x256 -> 320x192 -> expected [5,48,20,12]
- left_wrist_right: 256x768 -> current 192x320 -> expected [5,48,12,20]

## Exact-window cache

Output remains exact_window_v1 with:

- 17 RGB frames/window
- stride 1
- anchors 0,4,8,12,16
- float32 latent
- atomic episode writes
- per-task-class deterministic episode selection
- monotonic resume N2 -> N10 -> N20 -> ALL

The output hierarchy remains:

tasks/<task_slug>/episodes/episode_XXXXXX.pt

so cache consumers do not depend on the source storage layout.

## Current experiment execution

The current planned first conversion remains N=10 per underlying task class, camera_set=left_wrist.

Code capability defaults to ALL when --episode-limit is omitted; that is not the current execution budget.

## Download helper

tools/g0/download_robocasa365_v3_target.sh downloads the three target v3 mirrors.


## Runtime status

Code migration is complete, but a real v3 dataset smoke has not been executed from this chat.

The first runtime gate must verify:

- v3 metadata loads through LeRobotDatasetMetadata
- underlying task-class counts are 18 / 16 / 16
- annotation.human.task_name resolves through meta/tasks.parquet
- N=2 deterministic subset and resume
- left_wrist source composition 256x512
- post-VideoResize canvas 192x320
- exact-window latent [5,48,12,20] float32 finite
- no source-video decode during training when latent_cache_root is enabled

Only after that gate should the current N=10/task-class conversion start.
