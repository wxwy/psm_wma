# Source-bound 10 mm color and native dual-map episodes

This module ports the validated F21/F22/F24 numerical path into repository entry points. The 10 cm collision/navigation map and the 10 mm visual-color map retain separate inputs and update logic. GPU Views remain orthographic at 1 cm/pixel, with a white background and separate Island files.

## Build and CPU validation

```bash
bash g2/offline/build_native_raster.sh
python -m pytest g2/tests -q
```

The generated `g2/bin/libfast_surface_cells.so` is ignored by Git. The GPU backend additionally needs MuJoCo EGL, PyOpenGL and the NVIDIA FP64/64-bit atomic shader capabilities used by the accepted renderer. SciPy supplies the existing CPU reference path. CPU remains the renderer default; direct-color runs select their backend explicitly.

## Robot pose marker (final top View only)

`floor_top.png` is stamped **after** source-bound F27 rasterization and raw
pixel-parity verification; the native mesh, other View directions, geometry
masks, room graph, and raw F27 RGB are unchanged. Both `classic` and
`game_arrow` support one shared appearance contract:

- `--robot-pose-marker` / `--no-robot-pose-marker` (default on)
- `--robot-pose-marker-style {classic,game_arrow}` (default `game_arrow`)
- `--robot-pose-marker-outline` / `--no-robot-pose-marker-outline` (default on)
- `--robot-pose-marker-outline-width FLOAT` (default 1.0 final-image pixel)
- `--robot-pose-marker-outline-color '#E1E5EA'` (gray-white default, `#RRGGBB`)
- `--robot-pose-marker-fill-color '#454B53'` (dark gray default, `#RRGGBB`)
- `--robot-pose-marker-length-px FLOAT` (default 26.6; width, tail notch,
  arrowhead and the classic dot/shaft scale proportionally)
- `--robot-pose-marker-relief {flat,raised}` (default `raised`); `raised` is
  a 2.5D shading/pixel overlay, **not** any change to 3D scene geometry

All appearance settings are recorded in the per-state marker receipt and
source-identity-bound stage cache key. Changing color, outline, length,
style, or relief invalidates the corresponding **F27 export stage** only.
`nav_sg` and original RoboCasa frames remain untouched.

## Explicit episode inputs

`g2.offline.episode` consumes JSON with `schema="g2_direct_color_episode_inputs_v1"`, `layout`, and these references:

- `source_manifest`: the native frame-zero `nav_sg_mujoco_oracle_v1` manifest, including complete assets, metadata and FULLPHYSICS state archive.
- `visual_inventory`: the source-bound selected visual geom inventory. It may come from another frame of the same model; world poses always use the current state row.
- `role_map`: the reviewed per-geom visual-role mapping.
- `states`: increasing entries beginning at frame zero. Each has `frame`, `snapshot` and `bundle_manifest`. References are objects containing an absolute `path` and exact file `sha256`.

Optional acceptance inputs are `reference_color_manifest`, and per-state `reference_native_receipt`, `scene_graph`, and `reference_views`. The first three use the same hashed-reference form. `reference_views` is an array of `{path, sha256, relative_path}` records, with output-relative names such as `sixview/floor_top.png`. These compare independent accepted output bytes and RGB arrays; no old Fxx Python module is imported.

Snapshots, labels and Room/Island affiliation evidence are inputs to this materialized-input workflow. It does not discover the entire RoboCasa dataset or certify newly generated room/free-space evidence.

## Run the three stages

PSM-WMA and nav_sg both contain a top-level `g2` package. Run each in its own repository process; never concatenate their repository roots in PYTHONPATH. Use the exact MuJoCo version recorded by the source manifest.

From nav_sg:

```bash
python -m g2.gt.episode_nav_states \
  --source-manifest /inputs/frame0/manifest.json \
  --frames '[0,20,40]' --output /new/nav_states
```

From PSM-WMA:

```bash
python -m g2.offline.episode prepare \
  --inputs /inputs/episode.json \
  --nav-manifest /new/nav_states/nav_manifest.json \
  --output /new/color_prepared
```

The newly built nav_sg executable then maintains both maps in one process:

```bash
/native_ws/devel/lib/mapping/gt_direct_color_episode \
  --plan /new/color_prepared/native_sequence.txt \
  --output /new/native_episode \
  --emit-native-color-view-binary true
```

Back in PSM-WMA:

```bash
python -m g2.offline.episode render \
  --inputs /inputs/episode.json --prepared /new/color_prepared \
  --native-output /new/native_episode --output /new/episode_views --backend gpu
```

All output directories must be new. The native sequence format excludes whitespace in paths. Rendering checks native completion, full frame coverage, source/header/payload hashes, owners and independent references before publishing completion. Spatial snapshots remain bound to the current frame and original native entity table.

## Current verified scope

- The existing F24 native episode adapter accepts layouts 1 and 10, 2–300 ordered spatial states, up to 8,000,000 composed color voxels per state, and a sequence file of at most 128 KiB. Python enforces the same contract. This is a bounded integration gate, not all-layout support.
- Static visual geoms are preclassified from the selected recorded frames; one static cache is built, and changed dynamic geom layers are replaced. This offline look-ahead is not a real-time sensor policy.
- The native known region remains TEST_ONLY. Completion receipts retain `training_ready=false`.
- GPU nearest-color recovery retains the accepted grid/owner limits and rejects unsupported rotated or nonuniform Room-frame grids.
- This acceptance workflow retains source delta binaries and temporary native color tensors for diagnosis. It is not the final raw-map-free dataset writer.
- Dataset enumeration, fresh snapshot/Room certification, cleanup, frame-to-state packaging and large-batch throughput approval are separate work. A successful pilot does not start the 9,126-episode run.


## Fresh RoboCasa dataset → one-command Room 6views + Island 4views (candidate)

All preparation now resides under `g2/offline/atomic_6views_*.py` in the
repository. **No validation-folder scripts or pre-materialized Layout1/10
snapshots are accepted as production dependencies.**

- Auto-discover original `<task>/<date>/lerobot/meta/episodes.jsonl` and
  `extras/episode_*/{model.xml.gz,states.npz,ep_meta.json}`; use an existing
  flat V3 parquet only when provided and found. Fresh data do not require the
  parquet mapping or Depth.
- Generate per-episode source-exact model rebinding, official semantic/geom
  candidates, finite 10cm GT occupancy, native Room/SG, 10mm Visual-Geom
  incremental source and F27 original-material 1cm/pixel orthographic views.
  Keep Island's four views in an independent `islands/<id>/` folder.
- Reuse completed **source-identity-pinned** stages. An incomplete scratch
  stage is rebuilt; a mismatched final output is never claimed DONE.
  Successful episodes retain compact PNG and compressed SG; intermediate
  dense text/cloud/10cm grid/10mm worker tensors are cleaned by default.
- Every stage reports `G2_STAGE_START`, `G2_STAGE_REUSE`,
  `G2_STAGE_DONE`, or `G2_STAGE_REBUILD`, with task, global episode ID
  and timings. Each completed/failed episode emits `G2_PROGRESS` including
  overall and task-local counts, percentage and elapsed seconds; nav_sg
  native and F27 source-state logs remain visible.
- `--task` can be repeated or comma-separated. Without a task option,
  all tasks are selected. Without `--episodes-per-task`, **ALL available
  episodes of each selected task** are selected. The per-task quota is
  completely independent of `--batch-size` (100 by default).
- The compiled nav_sg native worker and ROS1 Noetic remain runtime
  dependencies. Both checked-out repositories and the MuJoCo runtime must
  be built/installed to the pinned compatible revisions (MuJoCo 3.3.7
  for current RoboCasa). This is an environment dependency, not a dataset
  preprocessing step.
- The simulator-derived known-free volume is intentionally
  `TEST_ONLY_NOT_CERTIFIED`. The output cannot claim real RGBD
  observation, semantic contact, training certification or human review.

Source-index inspection without any data production:

```bash
python -m g2.offline.atomic_6views_run scan \
  --task OpenDrawer --task CloseFridge --episodes-per-task 8 \
  --plan-root /path/to/reproducible_open_close_plan
```

**Manual-only full-source candidate** (16 episodes, four physical GPUs × two
EGL processes per GPU):

```bash
python -m g2.offline.atomic_6views_run run \
  --raw-root /mnt/data1/data_v2_0617/robocasa365_official/v1.0/target/atomic \
  --output-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/robocasa365-target-atomic-6views \
  --plan-root /mnt/data1/data_v2_0617/robocasa365_v3_flat/.g2_open_close_8_plan \
  --task OpenDrawer --task CloseFridge --episodes-per-task 8 \
  --gpus 4,5,6,7 --workers-per-gpu 2 \
  --resume --manual-start --allow-experimental
```

This command must not be executed until end-to-end non-pilot native Room/SG,
dual-map, F27 and compact receipts are tested and the user personally
authorizes the run. No assistant-initiated production is allowed. Existing
build/runtime dependencies are checked before GPU work. Existing state
manifests are automatically generated and do not need separate manual prep.


## P3: SG event keyframes and frames without directories (v3, opt-in)

The production switch `--sg-event-index` requires the existing
`--scene-event-index --sim-direct-material --lazy-texel-decode` path.
The original native nav_sg and legacy output paths remain available.

New production packages declare `sg_geometry_policy=EVENT_KEYFRAME`.
A visual scene FULL event always saves a physical SG. Independently, a semantic,
structural or unsupported change, or geometry error reaching 1 mm, saves a new
SG keyframe. Otherwise the frame directly references the most recent physical
SG. Bbox endpoints and centroids use 3D Euclidean error; known connection
distances use absolute error. The comparison stays anchored to the last
physical SG so slow drift accumulates. SG updates do not change the actual
view `update_mode`.

Each manifest row keeps `scene_graph_frame_metadata` with the current source
frame, timestamp and GT state hash. `source_scene_graph_sha256` binds the current
raw SG; `scene_graph_sha256` verifies the actual stored/reused geometry plus
current identity. `scene_graph_max_geometry_error_m` reports the difference.
Threshold-reused geometry is not claimed to be numerically identical to the
current raw graph.

Only actual SG/PNG writes create a `state_...` directory. If all views and SG
are reused, only the manifest row exists. Consumers must resolve
`view_refs` / `scene_graph_ref`; absence of that frame's directory is valid.
Use `resolve_scene_graph(root, state_id)` for SG and the existing
`resolve_indexed_png` for views. The shipped viewer already resolves physical
image owners and needs no per-frame placeholder directory.

Robot marker updates use 1 mm translation or 1 degree yaw relative to the last
drawn floor marker. These are the current fixed policy, not additional CLI
tuning knobs.

The offline v2 converter keeps its default LOSSLESS behavior and old v3
keyframe/delta files remain readable. Resume preserves already-completed,
valid v1/v2/v3 output; enabling this switch does not migrate old Episodes.
