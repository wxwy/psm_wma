# Stage-1 input/output schema — psm_wma_robocasa_rgbd_pose_v2

Issue #19 changes the codec and cache identity. v1 caches are rejected explicitly,
never accepted by relaxing v2 verification. See the
[v2 contract and seven-episode transition plan](../../docs/build/PSM-WMA_G2_Depth_ZeroSentinel_v2_and_SevenEpisode_Transition_2026-11-05.md).

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

An external explicit batch/membership list frozen against the exact mapping is
also accepted:

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

Each camera chunk has exactly these five arrays; no `valid` array is stored:

| Array | Type / shape / meaning |
| --- | --- |
| depth | uint16 millimeters **or** float32 meters, `[N,H,W]` |
| K | float32 `[N,3,3]`, one calibrated intrinsic matrix per frame/camera |
| T_world_camera_gl | float32 `[N,4,4]`, GL camera-to-world |
| T_world_camera_cv | float32 `[N,4,4]`, optical CV camera-to-world |
| frame_indices | int64 `[N]`, original episode-local frame indices |

Default chunk size32, configurable1..256. `uint16_mm` valid range is
`[0.001,65.535]` meters, inclusive, rounding-to-nearest, error <=0.0005001m.
Renderer-invalid pixels and finite renderer-valid values outside this interval
are stored as **0**, never wrapped or saturated to 65535. Readers derive the
transient boolean mask from `depth > 0`. The renderer mask itself is not stored.
No camera near/far plane is changed to force representability.

`float32_m` retains finite, positive, float32-representable depths outside the
uint16 interval; it does not inherit the uint16 range filter. Renderer-invalid
pixels are also 0. A renderer-valid nonfinite value, or a nonpositive/overflowing
or underflow-to-zero float32 value, is malformed input and fails closed. ZIP is
lossless with respect to the encoded arrays; millimeter quantization is not
lossless with respect to the original floating depth.

Each frame/camera `encoding` object has disjoint integer counts: `total_pixels`,
`renderer_invalid`, `below_1mm`, `above_65_535m`, `encoded_valid`. The last four
sum to `total_pixels`; `encoded_valid` equals the positive payload count. The two
range counts apply only to uint16 and are 0 for float32. Finite raw min/max,
`range_filter_applied` and excluded fraction of renderer-valid pixels are recorded.
Exclusion above 1% produces `RANGE_EXCLUSION_GT_1_PERCENT`, a diagnostic, not a
relaxed geometry PASS. The fraction and threshold are explicit even below 1%.
The episode manifest aggregates these counts and `warning_frames` per camera.
No per-pixel diagnostic bitmap is persisted in NPZ or JSON.

Frames JSONL carries task, global/local episode, frame, source-state/RGB-frame
indices, global/local row indices, flat timestamp, actual simulator time/state
roundtrip error and each camera's chunk/offset, original video path/frame,
depth statistics, quantization error and encoding diagnostics. It contains no
RGB pixel payload. Depth statistics describe storage-representable pixels.

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

The replay verifier compares the saved mask against a fresh **storage** mask,
not against the raw renderer mask. Source classification counts must also match;
independent geometry still requires at least 16 rays and <=1 cm error, with the
existing K/Pose/projection thresholds. An all-zero frame cannot obtain spatial
PASS. RGB photometry remains a separate diagnostic; human visual acceptance is
an external record.
