# Source-bound 10 mm color and native dual-map episodes

This module ports the validated F21/F22/F24 numerical path into repository entry points. The 10 cm collision/navigation map and the 10 mm visual-color map retain separate inputs and update logic. GPU Views remain orthographic at 1 cm/pixel, with a white background and separate Island files.

## Build and CPU validation

```bash
bash g2/offline/build_native_raster.sh
python -m pytest g2/tests -q
```

The generated `g2/bin/libfast_surface_cells.so` is ignored by Git. The GPU backend additionally needs MuJoCo EGL, PyOpenGL and the NVIDIA FP64/64-bit atomic shader capabilities used by the accepted renderer. SciPy supplies the existing CPU reference path. CPU remains the renderer default; direct-color runs select their backend explicitly.

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
