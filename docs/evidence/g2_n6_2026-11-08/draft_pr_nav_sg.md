Precolored scans currently stop at ColorCloudMap without a source-bound native 3D snapshot for G2. This adds an opt-in quiescent snapshot API, frame-0 prebuilt geometry/color initialization, and native Room/object grouping for the PSM-WMA spatial preview adapter.

**Stacked Draft on PR #7** (`e86c3844325b13092e1713290b079cfb63466cfb`). Fixed implementation: **`2009fae35d86579bb22c273fb97ec1bf0835b533`**, tree `9fc89f461f9edbdd3ebae3684412eb3bd20c1b3f`. Related to [PSM-WMA #26](https://github.com/wxwy/psm_wma/issues/26); companion implementation `c7ebb429074be5726ff9abead0e0d930a7e2138d`. Keep Draft and unmerged.

### Resulting behavior
- Export actual ColorCloudMap, native grid tri-state bytes, Room footprints/IDs, ObjectMap/SG IDs, source part/joint provenance, meshes and native hierarchy/portal relations. Source/build/frame identity and scene-transition locks reject stale or mixed captures.
- Initialize normal geometry from a separately evidenced frame-0 occupancy grid and precolored world cloud while keeping genuine RGB-D and native object processing active. No MuJoCo dependency or Cosmos images enter generic C++.
- Add a bounded recorded replay profile that requires genuine RGB-D/pose and model observations, exact source binding, first/final semantic frames, native ACK and current color-worker state. Existing N3 behavior stays active without the opt-in.
- Compute grouping in native C++ from strict 3D bbox gap <0.30 m within native Rooms. Floor/Wall roots never relay separate object components. Generic changes are mirrored to the historical mapping tree; recorded MapROS integration is limited to the active tree.

### Author validation
- Fresh active-tree ROS Noetic Catkin build PASS.
- **129 distinct C++ testcases PASS** across 18 XMLs, including 9 new cases; zero failure/error/skip. Catkin wrapper-inclusive total 258 is not the distinct count.
- Native Python regression: **449 passed, 73 skipped**; skips require optional CPU torch in existing model-service/pooling tests. Six new recorded-adapter checks pass.
- **6 TEST_ONLY native invocations**, rectangular/L-shaped/doorway × ESDFGrid/GVD, frame 0/200; **12 actual snapshots** sealed/rendered by G2. Native object IDs, 0.20 m saved-state movement and source part/joint fields checked.
- Four-frame synthetic normal prebuilt geometry/input smoke PASS; no genuine model execution is claimed.
- Generated build-source SHA256: `7a8ff690e150956d59f7b2773561034e4956a5344190f7e1d08135d4c92c4bae`. Published Git tree exactly matches the tested source; companion inventory verifies 43 native files.

### Open acceptance
**Ordinary native structural roots are NOT IMPLEMENTED.** Even genuine object observations remain structurally blocked for complete Floor/Upper/cardinal/Island output. Diagnostic source roots cannot bless normal perception. Oblique/complex walls are conservatively incomplete; the L-shaped test creates no Island, and the doorway still yields one Room.

Original Layout 1/10 frame 0/200, whole-house materials, genuine YOLOE/SigLIP replay and human visual acceptance remain pending. Issue #26 stays open. No parent PR, V3 source, Gitlink, cache, training, GPU task or production ref changes.

[Native contract and commands](https://github.com/wxwy/nav_sg/blob/codex/g2-n6-native-snapshot/docs/G2_N6_NATIVE_SNAPSHOT.md) · [Companion runbook and evidence](https://github.com/wxwy/psm_wma/blob/codex/g2-n6-prescan-native-views/docs/build/PSM-WMA_G2_N6_implementation_runbook_2026-11-08.md)
