# G2 P1 — owner-approved movement thresholds and 2-Episode evidence (2026-11-13)

**EXPERIMENTAL P1 BRANCH ONLY. No production V3 or nav_sg source change. Full 9,126-Episode task remains stopped.**

## Agreed runtime decision

At each 2 Hz spatial sampling state, use the compiled source MuJoCo GT pose of EVERY non-robot Visual Geom. Only the scene view rendering decision is affected: all SG/object GT, scene/provenance and original frame IDs continue to exist per frame.

- When **each** visual geom has 3D Euclidean translation strictly **below 0.001 m (1 mm)** AND its SO(3) geodesic relative rotation angle strictly **below 1.0 degree**, treat the scene as unchanged.
- If any geom's movement reaches or exceeds EITHER threshold, refresh all scene Views and update the scene reference.
- Compare against the **last actually rendered scene keyframe**; do NOT compare only adjacent samples, otherwise small movements can accumulate indefinitely.
- Evaluate robot base x/y/yaw independently at each sampled View time. If scene unchanged but chassis changes, reuse the previously generated unmarked floor_top scene background and overlay the NEW game_arrow only. If both are unchanged, reuse all final PNGs through direct indexes.
- In original RoboCasa layouts the robot is already excluded from the scene geometry, and its arrow already uses an independent compositor. The candidate does not duplicate either component.
- Rotation must be a true relative angle from the 3x3 MuJoCo rotation matrices. Never compare matrix entries directly to a "one degree" numeric tolerance.
- These thresholds are user-approved image fidelity policy, NOT a claim of pixel-exact equivalence for all image frame pairs.

Source: standalone g2/offline/scene_view_event_index.py, and experimental indexed package/viewer.

## Real A/B — original F27 raw PNG oracle

All original images were already rendered by the existing F27. The event detector uses ONLY source GT to decide: it does not inspect PNG content. The byte hashes and RGB pixel differences below were computed independently **after** the decision. Note the metrics are possible render-skips, not measured end-to-end speedups.

| Episode | Spatial states | FULL | ARROW_ONLY | REUSE_ALL | Raw view comparisons | Different PNGs | Total different pixels | Worst one PNG |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| NavigateKitchen/episode_002022 (Layout 7) | 19 | 1 | 18 | 0 | 144 | 21 | 21 | 1 pixel |
| OpenDrawer/episode_003029 (Layout 5) | 36 | 10 | 26 | 0 | 104 | 54 | 1,245 | 57 pixels |

- NavigateKitchen skipped scene rendering at 18/19 = 94.74% of states.
- OpenDrawer skipped at 26/36 = 72.22%. A large real Drawer motion near frame 270 onward triggers full scene refresh as required.
- The 57-pixel maximum occurred in a 609x326 raw view (0.0287% of image pixels). The aggregate 1,245 pixel differences were spread across 104 reused views; this is NOT bit-exact and requires human quality Gate if needed.
- Both episodes showed robot motion at skipped scene states (ARROW_ONLY); separate synthetic tests cover REUSE_ALL with no robot pose change.
- Each frame's Scene Graph and exact MuJoCo states are preserved. No spatial-state reduction.
- The prior real robot-arrow-only A/B reproduced the same final floor_top PNG bytes by re-overlaying the original chassis pose on cached raw scene background.

## Verification

- Isolated full G2 Python suite: **871/871 PASS**.
- Viewer Node smoke tests: **3/3 PASS** (original Island sources, no flicker, indexed v2).
- Tests cover 3D Euclidean distance vs per-axis thresholds, true 1 degree SO(3) angle, strict boundary >= threshold, cumulative sub-threshold motion with keyframe refresh, robot-only changes, base yaw wrap, bad direct refs and corrupt frames.
- P1 index_state rejects a forged non-FULL event exceeding the approved physical thresholds.
- Real GPU full P0 Lazy Texture gate remains separately PASS 19/19, 0 mismatches. P2 two-layout original native-color counterfactual remains PASS. They are not enabled as production settings.

## Human Gate

Local server-on-device: http://127.0.0.1:18769/index.html (requires SSH port forwarding to server). Files: /tmp/g2_p1_human_gate_1mm_1deg_20261113/index.html. Four OpenDrawer worst-case comparisons show original PNG, reused PNG, highlighted red differing pixels and magnified crop.

## Remaining engineering work

The P1 cursor, v2 indexed offline packager and Viewer support are independently tested, but **not yet integrated into the actual F27 production render loop**. Production resume schema and data loaders are still on v1. Do NOT change the authoritative 9,126 output schema without v2 resume and viewer/loader integration, then additional full-Episode A/B and human quality Gate. Existing 202 completed v1 Episodes remain valid, and resumed production must not recompute them.

## Human visual-acceptance Gate (2026-11-13)

**H1 PASS — user inspected the side-by-side and magnified P1 1 mm/1 degree A/B images and reported no visible difference.** This is a visual acceptability decision for the explicit P1 motion tolerance only, not a bit-exact F27 result, and not approval to skip SG/native provenance for any sampled state.

The accepted comparison was made available at the server-local preview path /tmp/g2_p1_human_gate_1mm_1deg_20261113/index.html. It included four OpenDrawer worst-case pairs: cached scene, original F27 scene, red-highlighted differing pixels and magnified crop. P1's existing 1 mm and 1 degree thresholds and last-rendered-keyframe reference remain unchanged.

**Next gate still OPEN:** integrate runtime FULL/ARROW_ONLY/REUSE_ALL decisions into F27; keep v1/202 completed Episode behavior unchanged, implement complete v2 resume and image-index consumption, and run two-layout end-to-end temporal parity plus runtime benchmarks before production promotion.
