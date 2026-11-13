# G2 P1 — scene movement gate and indexed sixview (2026-11-13)

**EXPERIMENT ONLY. Not integrated into production F27/packager. Not merged into formal V3.**

Base: formal V3 bdc920ac48312ba302e41114ce4ad1198de2ecc1.

## Owner-approved contract

At every sampled 2 Hz View time, compare non-robot GT Visual Geom positions/rotations with the preceding sampled View time. No per-View input signatures, no room-dependency graph, and no PNG hash in the RUNTIME motion decision.

- Object moved: rerender all environmental Views and draw current floor_top chassis arrow.
- Objects still, robot base x/y/yaw moved: reuse raw environmental Views and render only the new game_arrow on an **unmarked** cached floor-top background.
- Neither moved: reference previously materialized Images. Each sampled state still has its own frame ID, source mapping and Scene Graph.

Robot Visual Geoms are already excluded from the original scene roster (79 robot-role Geoms in the acceptance scene). The arrow overlay already exists as a separate post-render step; no duplication of this original capability.

## Prototype modules and schema

- g2/offline/scene_view_event_index.py: SceneViewCursor, conservative nonrobot pose comparison and circular yaw delta. FULL / ARROW_ONLY / REUSE_ALL. Default tolerance 1e-10, and configurable explicit tolerance for *experiments only*.
- g2/offline/scene_view_index_package.py: separate offline v2 compact index-packaging oracle for already fully rendered v1 Episodes; it writes a new output directory and keeps per-state Scene Graph gzip files independently. Direct one-hop indexed PNG references are represented by view_refs[relative_path]={ref_state, path}, never chained or across Episodes.
- g2/viewer/viewer.js: v1 compatible, adds v2 index resolver; Island selectors include indexed directions. Bad, future, chained and missing references fail closed.
- g2/tests/test_scene_view_event_index.py and test_scene_view_index_package.py, plus viewer_scene_index_smoke.js: isolated tests.

The offline packer compares SHA256 of candidate reused PNG against the original already-rendered source PNG, as an A/B AUDIT ONLY. It never uses image equality to decide whether the simulated object moved.

## Executed verification

- G2 Python tests: **865/865 PASS**, including 16 new P1 tests.
- Node viewer regressions: **3/3 PASS** (existing Island Views, existing no-flicker, new v2 indexed views).
- Real completed CloseBlenderLid Episode 000027, 45 spatial states: **46 direct view references**, 269 physical PNGs, 45 independent per-frame Scene Graphs, no invalid references. All 46 references certified byte-exact against the original v1 output.
  - The chosen transitions for this package demo came from previously observed exact PNG equality. This proves schema/index and image parity, **not GT event detection correctness**.
- Real NavigateKitchen Episode 002022, 19 states, 707 nonrobot Visual Geoms:
  - strict pose tolerance <= 1e-5: FULL 19/19, no events safe for reuse.
  - threshold 1e-4 (maximum component-wise translation in meters, rotation as matrix-entry delta): 10 FULL, 9 ARROW_ONLY; **4 referenced raw Views differ by a single pixel**.
  - threshold 1e-3: 1 FULL, 18 ARROW_ONLY; **21 referenced raw Views differ, one pixel each**.
  - Real MuJoCo object pose jitter means widening movement tolerance breaks bit-exact PNG parity. Do not silently deploy a relaxed threshold.
- Additional real arrow-only A/B: reconstruct frame 30's current game_arrow on a reused unmarked frame 20 floor_top background; SHA256 of final PNG is identical to reconstructing from frame 30's own raw view.

## Outstanding gates

1. Decide whether physical pose jitter counts as actual object motion. Strict event detection preserves mathematical correctness but may produce no optimization on jittery RoboCasa episodes. A nonzero movement tolerance needs an explicit image-fidelity policy.
2. Wire this cursor into the F27 2 Hz loop, reusing its original chassis arrow code and preserving independent per-frame SG.
3. Update authoritative resume validation and training consumer for indexed v2 manifests. The standalone offline packer DOES NOT yet change the main production runner.
4. Validate two distinct RoboCasa layouts, complete upstream checks, visual/SG purity, upper_up/Island view handling and cold-start/full-map behavior.

Formal V3, original nav_sg RGB-D and the stopped 9,126-episode production remain untouched.
