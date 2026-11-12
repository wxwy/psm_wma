# G2 RoboCasa Full Map F27: Source-bound Color-only Native Gate (2026-11-12)

## Scope and protected baseline

**Simulation-only**: this optimization applies exclusively to source-proved MuJoCo Full Map RoboCasa offline Views + Scene Graph export. The original nav_sg RGB-D/perception point-cloud fusion, occupancy/ESDF updates, online navigation, Room/SG manager, 30cm AABB connectivity, hierarchy and all existing native dual-map executables are unchanged.

Default V3 is unchanged; enable the new path only with **both** `--sim-direct-geometry-only --sim-color-only`. `--sim-color-only` without the GT-only flag is rejected. The new color worker has a different binary, protocol magic, receipt schema and work-stage namespace. It never certifies navigation or occupancy.

## Data flow

1. Original MJCF/Mesh, metadata and FULLPHYSICS → **frame0 source-bound 10cm GT only** → native nav_sg Room/SG. This one-time initialization is required for the native Room frame/footprint.
2. Original FULLPHYSICS at selected 2Hz frames → current source-world vertices/BBoxes → original nav_sg connection rules → dynamic Scene Graph. This already exists in `g2/offline/atomic_6views_snapshots.py` and does not read `nav_states`.
3. Original Visual Mesh/material/color source → per-geom 10mm static/dynamic layer batches; state SHA and source SHA are verified from FULLPHYSICS; no `nav_manifest` is supplied.
4. A **separate** nav_sg `gt_direct_color_only` program uses exactly the original `ColorCloudMapWorker.applyDirectColorSource` and `snapshotDirectColorSource`. It accepts only `F24_G2_NATIVE_COLOR_ONLY_SEQUENCE_V1`, verifies original scene/source/frame, each layer file SHA, full composed 10mm color digest and idempotent frame replay. Outputs the unchanged `native_view_color_TEMP.g2col10.bin` binary payload, with color-only receipt explicitly reporting null 10cm navigation certification.
5. The existing F27 `SurfaceRenderer` / Visual Mesh source registry emits exact Views. The native Room/SG source remains independent of color worker.

No `nav_states`, per-frame 10cm grid file, `native_dualmap`, synthetic RGB-D or geometry-point cloud is needed in this opt-in **offline Views+SG** chain. The original dual-map mode is still required when testing dynamic navigation/ESDF or topology-changing rooms.

## Verified evidence

| Episode | States | Original/native 10mm color | SG | F27 |
|---|---:|---|---|---|
| CloseFridge 503 | 27 | 27/27 native color binaries byte-identical | 27/27 source JSON bytes identical | 108/108 PNG bytes identical |
| OpenDrawer 3022 | 35 | 35/35 native color binaries byte-identical | 35/35 source JSON bytes identical | 140/140 PNG bytes identical |
| OpenDrawer 3029 | 36 | 36/36 original native 10mm digests pass | 36/36 decompressed SG JSON bytes identical | 144/144 PNG bytes identical |

503 native color-only worker elapsed **9.26s** including 27 native frame exports. OpenDrawer3029 full official V3 Worker `work --sim-direct-geometry-only --sim-color-only` completed in **395.35s**, including initial source-GT Room/SG, 36 dynamic snapshots, 10mm native color and F27. The production candidate was validated by `completed_output()` against the pinned source selection; all 36 SG payloads and all 144 PNGs match prior production. Its scratch directory had **no** `nav_states`, `nav_deltas`, `native_dualmap`, `prescan` or `native_prepare` stages. Initial 10cm GT Room/SG source is still present. The exact speedup of complete source→PNG jobs needs matched-load A/B; F27 remains the dominant cost.

### Regression and isolation

- Standalone native color-only parser **6/6 fail-closed**: rejects legacy F24 V1, incorrect scene/source SHA, repeated or missing frames, incorrect full color digest, and overwriting existing output.
- V3 isolated `g2/tests`: **833 passed**. nav_sg GT tests: **76 passed**.
- The separate simulator color-only C++ file is located at `nav_sg/g2/gt/gt_direct_color_only.cpp`, **outside** the native source-hash inventory `mapping_8_3/mapping/{src,include}`; CMake registers it as an extra executable only. No native perception/Room/SG source is changed.
- The native GT launch argument fix only emits `--full-map-geometry-only true` on explicit opt-in; the false/default launch retains its original CLI.
- Existing official 16 completed episode packages remain unmodified.

## Promotion gate

All three real episode gates are complete. The final isolated catkin C++ build passed for **all three targets** (`gt_direct_color_only`, legacy `gt_direct_color_episode`, and `gt_oracle_native`). All **157 original `mapping/{src,include}` C++/header files are byte-identical** to the unmodified G2 source tree. The generated `NAV_SG_SPATIAL_BUILD_SHA256` is **byte-identical** between legacy and candidate native builds: `eb2701b6597a5fa95ddb4504ef6188f6ff0041293370677462a105d6b8a816f6`. The new tool is outside that hash's source scope. GitHub nav_sg G2 must merge before V3. Server native runtime must be rebuilt from matching official G2; do not use transient acceptance binaries for production. All resulting views are spatial-conditioning artifacts; `training_ready` remains false.
