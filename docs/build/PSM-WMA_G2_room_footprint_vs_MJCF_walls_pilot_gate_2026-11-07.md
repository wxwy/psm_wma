# PSM-WMA G2 — Room Footprint vs MuJoCo Physical Walls: Real-data Pilot Gate

Date: 2026-11-07 (local). **STATUS: PARTIAL_PASS / NATIVE_ROOM_COMPARISON_BLOCKED**. The user authorized starting the validation. This is a completed read-only pilot on the existing authorized `data` server, NOT a claim that a fully integrated native Full-GT RoomPipeline is finished. Production source, original dataset, GPU tests and active training processes were not changed.

## Sources and version boundaries

- Canonical public-facing repository: `wxwy/nav_sg:G2`, HEAD `bcbc46a53bee66b5820b793dd35acbe44c348a5c`. PR #2 (`codex/g2-n1-robocasa-offline-replay`) and stacked PR #4 (`codex/g2-n3-h1-semantic-review`) remain **Draft** and **not merged**.
- The already executed, immutable G2 PR #4 real Episode forensic data were read at:
  `/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.nav_sg_g2_sg_review/episode_005077_run_8e24974_cpu_20261106/native`
- Current operation launcher `start_sh/sg.sh` launches `ObjectNav-mapping-only/src/mapping`; baseline snapshot `mapping_8_3/mapping` has seven differing common files, including `src/map_ros.cpp` and `src/object_mapping/object_map3d.cpp`. Do not confuse baseline snapshots, physical runtime source and the PR candidate source.
- MuJoCo independent GT for `target/atomic/PickPlaceDrawerToCounter/20250820/lerobot/extras/episode_000036` (global id 5077) includes `model.xml.gz` and `ep_meta.json`. Also sampled local episodes 33,34,37 and 3 local episodes of each of 18 target-atomic task classes.
- Native audit `summary.json` says 459/459 frame processing, latest nonempty 950 occupied voxels. Its `source_physical_geometry_gate=PENDING_DS_GATE_B_C`; a COMPLETE status is **not** a fully approved full-world GT map.

## Gate A: Native Room Footprint Availability — BLOCKED

- 27 selected semantic snapshots in `native_semantic_audit.jsonl`: **0 Room nodes** across all snapshots; the Scene Graph contains a Building and confirmed Objects only.
- At final frame 458, 950 occupied voxels, 2114 free voxels, `resolution=0.10m`, indices serialized as `x*ny*nz + y*nz + z` and successfully decoded into real world XYZ with voxel-center offset.
- Observed occupied XYZ min/max (m): X `2.35..4.85`, Y `-1.35..0.05`, Z `0.05..1.75`.
- MJCF physical floor XY bounding extents (m) on the same episode: X `-0.04..5.54`, Y `-3.04..0.04`. The current Left-only replay has incomplete coverage; at most `17.34%` of 0.10m XY grid cells inside that GT bounding extent have **any** projected native FREE/OCCUPIED voxel evidence (which does **not** establish actual visible floor).
- Of four GT walls, the native occupied voxels within 0.15m of a wall's finite collision box and 0.3–2.5m in Z: back wall 227 (may include adjacent furniture), front/left/right **0** each. This is a **proximity** audit, not successful wall recognition.
- **Consequence:** no actual native Room footprint exists in the currently recorded stream. It is incorrect to claim `boundary_hull_2d` or `computeFootprintFromVoxels()` agrees/disagrees with GT walls from this run. To obtain that measurement, a full GT geometry occupancy source must first be fed through the actual RoomPipeline.

## Gate B: Actual MJCF Layout Shape — PASS for sampled sources

- Local EP33/34/37: one candidate kitchen layout, 4 primary collision wall boxes; EP36: a different candidate kitchen layout, also 4 collision wall boxes.
- Extended read-only sample: **18 underlying target-atomic tasks × first 3 episodes per task = 54 episodes**; among their MJCF geometries, **50 contain four and 4 contain five primary wall collision boxes**. The five-wall examples in this sample use `layout_id=10`.
- Layout 10 has `wall_left_2_room_main` in addition to the other four primary wall bodies and **two distinct floor collision boxes**. A Room can therefore require more than four physical segments even though the renderer uses stable ±X/±Y directional slots.
- Independent GT floor collision geometry raster test at 0.025m, **not native RoomPipeline output**:
  - Layout 1: floor box union ≈17.143m²; convex hull of GT floor-box corners ≈17.220m²; false-covered ≈0.077m² (0.4%, dominated by grid approximation).
  - Layout 10: GT floor-box union ≈24.103m²; naive convex hull ≈25.842m²; **extra ≈1.739m² (7.2% of true floor)**. Therefore, treating convex hull as exact wall/room boundary can be seriously misleading for nonconvex layouts.
- This geometric counterexample **does not measure `Room.boundary_hull_2d` real error**, because it uses actual MJCF floor-box corners, not an observed RoomPipeline's topology nodes. It only motivates testing the voxel-based footprint against true walls.

## Gate C: Native RoomBuilder 2D flood control-flow — RISK CONFIRMED (not native GTest)

In both checked mapping trees, `src/room_pipeline/room_pipeline_room.cpp:515-577`:
- Builds `traversable` with `0=unobserved/no voxel, 1=any FREE, 2=only OCCUPIED`;
- Seeds from Room topology nodes and expands a **4-connected BFS**;
- Tests `traversable[nx2,ny2] == 0` to stop expansion; **2 (occupied-only)** is therefore passed through as though it were open. The comment “respects walls” is not sufficient to prove walls are blocked.
- Declares `max_dist_cells` at ~line 517 but does not use it in the shown BFS propagation condition. This suggests the declared radius is not enforced by this mode's flood loop.

An isolated Python control-flow analogue with a 9×13 mask (an entire center column set to occupied-only) gives:
- current condition `value!=0`: 9 barrier cells labeled, 45 free cells on far side reached from left seed;
- proposed `value==1` traversing only FREE: 0 barrier cells and 0 far-side free cells reached.

**This is source-code-plus-toy-reproduction evidence, not a passed actual C++ native regression.** The correct fix may be **two-pass**: flood only FREE cells, then optionally assign adjacent OCCUPIED cells to Room IDs **without allowing expansion through them**. Preserve object→room querying semantics. Implement a native C++ regression before changing production.

## Isolated results on the authorized data server

```text
/mnt/data/shenzhen/szrobot/logs/.tmp_backup/.nav_sg_g2_room_wall_audit_20261107/
  audit.py
  audit.json
  audit.md
  gt_walls_vs_partial_native_occupancy.png   # diagnostic, NOT Cosmos spatial BEV
  gt_floor_shape_audit.py
  gt_floor_shape.json
  gt_floor_layout1_shape_vs_convex_hull.png  # geometry diagnostic
  gt_floor_layout10_shape_vs_convex_hull.png # geometry diagnostic
```

Files were created in an isolated scratch directory only; original demo/replay/train outputs were not overwritten. The server's remote file transfer was blocked by corporate proxy upload restrictions, so diagnostic PNGs remain available directly on `data` and are not silently represented as user-downloadable attachments.

## Next implementation gate (not yet executed)

1. **G0 — native C++ wall-blocking regression for RoomBuilder 2D recovery**, ensure OCCUPIED-only does not permit propagation, confirm existing object room attribution remains valid; check whether max distance is supposed to limit BFS, and test it rather than rewriting the whole algorithm.
2. **G1 — complete GT scene-geometry import for native SDF/RoomPipeline**: correct 3D occupancy from MJCF primitives and mesh/fixture transforms, with FREE/UNKNOWN distinguished. **Do not feed an all-surface mesh point cloud to `inputPointCloud(fake_sensor_pos)`**, because native raycasting would incorrectly mark nonobserved space free. Keep implementation isolated, follow project GT-adapter design.
3. **G2 — actual native Room UID + Room footprint across Layout 1 and nonconvex Layout 10**; compare `voxel_labels_2d_` region, real finite wall geometry and open/unknown boundaries with GT; report coverage, false walls, incorrect room merges and UID consistency.
4. **G3 — validate Room Cardinal ±X/±Y and Room/Island orthographic images from nav_sg-compatible colored 3D surfaces**, then L2/L3 frozen encoder cache. Do not conflate geometry comparison plots with actual PSS spatial-condition images.

**Current recommendation:** G0 and G1 are prerequisites for the exact “existing Room footprint vs actual physical walls” full-map measurement. Do not build a new wall-recognition network or freeze six-view input based on the current incomplete native Room run.
