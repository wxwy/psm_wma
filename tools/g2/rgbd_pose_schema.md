# Stage-1 input/output schema — psm_wma_robocasa_rgbd_pose_v1

## Inputs

`--raw-root` and `--flat-root` are read-only local directories; `--output-root`
must be separate. `--mapping-file` defaults to Flat's `flat_v3_mapping.parquet`.
Flat `meta/info.json` must explicitly declare a LeRobot v3 codebase version.
This is an **episode-level table**, not a frame-level table. Required columns:

| Column | Meaning enforced by the tool |
| --- | --- |
| task_class | Underlying environment class; portable task name |
| global_episode_index | Unique Flat V3 episode ID |
| local_episode_index | Episode ID in the original task dataset |
| local_row_from, local_row_to | Half-open original parquet row interval |
| global_row_from, global_row_to | Half-open Flat parquet row interval |
| length | Positive episode length; both interval lengths must match |

The real table additionally has `task_slot`, `local_annotation`,
`global_annotation`, `resolved_task_class`, `tasks_phrasing`. These are not frame
indices. If present, `resolved_task_class` must agree with `task_class`; the tool
does not infer a different class or state offset from annotation/timestamps.
Full table SHA256 is pinned in the cache contract.

For frame `i`, `0 <= i < length`, verify raw/Flat `frame_index == i`, original
`index == local_row_from+i`, Flat `index == global_row_from+i`, and exact
`observation.state` equality. The explicit `frame_index` state policy additionally
requires exactly `length` simulator states and uses `states[i]`, not a timestamp
offset. Raw/Flat observation-state equality is **not** proof that the simulator
state restores the correct image; that remains Gate B/C.

Original dataset layout follows official RoboCasa `lerobot_utils`:

```text
<raw-root>/<Task>/<recording>/lerobot/
  data/*/episode_*.parquet
  meta/info.json
  extras/dataset_meta.json
  extras/episode_000000/{states.npz,model.xml.gz,ep_meta.json}
  videos/<paths described by meta/info.json>
```

More than one possible original dataset is an error; `--source-dataset` selects
an explicit directory beneath raw-root. Per-camera original RGB HWC dimensions
come from info.json. `--image-size` can assert that size, never silently resize it.

## Selection

One explicit global episode, or a task + local episode, needs no sampler.
Batch selection uses the **existing** g0 `exact_window_v1`/`lerobot_v3` manifest
and its accepted `tasks[].episodes[].episode_index` rows, which are global IDs.
The source_dataset header must match the supplied Flat root. If present, the
original `selected_episode_ids`/digest are validated, but selected short episodes
absent from accepted cache rows are not reintroduced.

An external list made from independently verified training membership is also
accepted:

```json
{
  "schema": "psm_wma_rgbd_episode_selection_v1",
  "episode_namespace": "global_episode_index",
  "flat_mapping_sha256": "<SHA256 of the exact flat_v3_mapping.parquet>",
  "episodes": [
    {"task_class": "CloseFridge", "global_episode_index": 0}
  ]
}
```

The ID above is illustrative, not a frozen N100 selection. No hash-ranking code,
random seed or episode-limit default is duplicated. Task/episode sharding is a
deterministic partition of the supplied members, never a new sampling step.

## Committed output

```text
<output-root>/
  cache_manifest.json                  # Effective immutable cache configuration
  tasks/<Task>/episodes/episode_<global:06d>/
    manifest.json                      # Identity, sources, runtime, array/file hashes
    COMPLETE.json                      # Manifest hash; published last in staging
    frames.jsonl                       # One row per selected frame, in source order
    cameras/<camera>/chunk_000000.npz   # Bounded lossless ZIP/NumPy container
  _runs/<uuid>.json                     # Process/export summaries, not sensor data
  .locks/                              # OS-released advisory locks
  .staging/                            # Uncommitted data after abrupt interruption
  .failed/<uuid>/failure.json           # Isolated failed episode plus local artifacts
```

Each camera chunk has:

| Array | Type / shape / meaning |
| --- | --- |
| depth | uint16 millimeters **or** float32 meters, `[N,H,W]` |
| valid | bool `[N,H,W]`, invalid depth stored as zero |
| K | float32 `[N,3,3]`, one calibrated intrinsic matrix per frame/camera |
| T_world_camera_gl | float32 `[N,4,4]`, GL camera-to-world |
| T_world_camera_cv | float32 `[N,4,4]`, optical CV camera-to-world |
| frame_indices | int64 `[N]`, original episode-local frame indices |

Default chunk size32, configurable1..256. `uint16_mm` valid range is
`[0.001,65.535]` meters, rounding-to-nearest, error <=0.0005001m. Overflow and
underflow fail; rerun in a **new namespace** with explicit `float32_m` if needed.
ZIP is lossless with respect to these encoded arrays; millimeter quantization is
not lossless with respect to the original floating depth. Masked non-finite/far
background pixels remain explicitly invalid. No silent saturation/fallback.

Frames JSONL carries task, global/local episode, frame, source-state/RGB-frame
indices, global/local row indices, flat timestamp, actual simulator time/state
roundtrip error and each camera's chunk/offset, original video path/frame,
depth statistics and quantization error. It contains no RGB pixel payload.

Camera axes: GL right/up/backward; CV right/down/forward. Upright image origin is
top-left, centers `(column+.5,row+.5)`. Depth is **optical-axis Z**, not unit-ray
range. `T_world_camera_cv = T_world_camera_gl @ diag(1,-1,-1,1)`.
robosuite's extrinsic helper already returns CV. Both raw RGB and buffer are
flipped vertically once after `sim.render`; poses are read anew after every state.

Manifest records actual software versions and official helper source hashes,
raw input hashes, Flat parquet/video stat witnesses, mapping SHA and code-content
hashes. Source files must stay immutable during an episode. Code commit IDs are
provenance; docs-only successors do not invalidate identical code-content caches.

`full_episode=false` distinguishes the three-frame Gate B cache from full exports.
Neither a COMPLETE marker nor an offline checksum pass closes the physical
geometry Gate. Native replay reports are separate immutable text evidence.
