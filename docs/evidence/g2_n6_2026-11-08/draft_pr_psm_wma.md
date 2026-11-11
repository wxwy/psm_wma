G2 has no source-bound path from MuJoCo visual surfaces through native nav_sg outputs into spatial view assets. This adds isolated simulation/source, native-bundle and view modules for [Issue #26](https://github.com/wxwy/psm_wma/issues/26).

**Draft on V3 `7b8b733e1f585bb44a0eac7c14ad545c29355a86`. Fixed implementation: `c7ebb429074be5726ff9abead0e0d930a7e2138d`, tree `6aa4204f81fa5360cf07f487d986c88087478ac9`.** A later handoff/evidence-only successor preserves all runtime bytes. Native companion: [branch](https://github.com/wxwy/nav_sg/tree/codex/g2-n6-native-snapshot), fixed `2009fae35d86579bb22c273fb97ec1bf0835b533`, stacked on unchanged PR #7. Keep Draft and unmerged; Issue #26 stays open.

### Behavior
- `g2/sim` loads verified MJCF/assets and saved states, explicitly separates visual/collision/robot roles, samples actual supported asset albedo/UVs and exports bounded world XYZRGB with color validity/provenance. No camera rendering, fake pose, physics rollout or ordinary GT detection injection.
- `g2/nav_bridge` seals actual native IDs, memberships, source parts/joints, meshes, relationships, colors and full tri-state grid bytes with source/frame/build/hash checks. Room/Island grouping remains in native C++.
- `g2/views` uses a shared metric orthographic renderer: House Floor/Upper plus four Room cardinal assets, and four separate assets per native Island. It preserves unknown regions, geometry occlusion, world scale, depth and an explicit native-ID index table. Original 3D is retained.
- A plan-only recorded adapter binds original model/states/ep_meta to genuine recorded RGB-D and matching native model observations. It requires the recorded `world` frame and never executes inference.

### Author evidence
- **64/64 G2 Python tests PASS**, zero failure/error/skip.
- Companion active-tree native build PASS; **129 distinct C++ cases PASS**, including 9 new, zero failure/error/skip.
- Native Python regression **449 passed, 73 skipped** for optional CPU-torch model-service/pooling tests.
- **6 TEST_ONLY native invocations / 12 frame 0/200 snapshots** sealed and rendered, covering rectangular/L-shaped/doorway × ESDFGrid/GVD.
- Four-frame normal prebuilt geometry/input smoke PASS without semantic acceptance.
- Published trees exactly match tested source; readback verifies 15 PSM and 43 native file hashes. Separate read-only code review closed reported findings for the Draft scope.

### Acceptance still open
**Ordinary native structural roots are NOT IMPLEMENTED**, so complete normal Floor/Upper/cardinal/Island output remains blocked even with genuine object observations. Diagnostic source roots cannot certify normal perception. The L-shaped case conservatively yields no Island; the doorway still yields one Room.

Original Layout 1/10 frame 0/200, whole-house material completeness, genuine recorded YOLOE/SigLIP execution and human visual review are NOT_RUN/pending. Unsupported primitive/cube/opacity/translucent appearance fails or produces explicit partial artifacts with no COMPLETE. Views remain spatial previews with `training_ready=false`, never temporal video.

No Cosmos source, Gitlink, V3 production training/dataset/cache, GPU or simulation evaluation changes. Child/Gitlink stays `1ca308055fc41fb69efaeb9efaa23808f164a18e`. Existing nav_sg PR #2/#4/#6/#7 are unchanged.

[Runbook](https://github.com/wxwy/psm_wma/blob/codex/g2-n6-prescan-native-views/docs/build/PSM-WMA_G2_N6_implementation_runbook_2026-11-08.md) · [Measured author evidence](https://github.com/wxwy/psm_wma/tree/codex/g2-n6-prescan-native-views/docs/evidence/g2_n6_2026-11-08)
