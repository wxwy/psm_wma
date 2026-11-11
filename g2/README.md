# G2 spatial source and view prototype

This isolated implementation addresses [Issue #26](https://github.com/wxwy/psm_wma/issues/26).
It does not connect to Cosmos datasets, model conditioning, memory or training.

- `sim.prescan`: source MJCF/assets plus an explicit visual/collision role map and optional saved state → world XYZRGB, validity and provenance. MuJoCo is used only here; no camera rendering or physics rollout occurs.
- `sim.asset_inventory`: read-only all-geom preflight and an unfilled role template. Records actual body/geometry/material provenance and zero-face statistics; missing roles remain unclassified and material probes do not measure full surface coverage.
- `nav_bridge.recorded`: prepare a source-bound plan for the existing native recorded RGB-D/YOLOE/SigLIP path. It writes commands, never runs inference.
- `nav_bridge.snapshot`: seal actual native snapshots, preserving native Rooms, objects, roots, Island membership, meshes, source parts, relations, colored surfaces and the full tri-state occupancy grid.
- `views.render`: metric CPU projections of that retained native 3D bundle. House Floor/Upper are shared; every Room references those plus four cardinal assets. Each native Island gets four separate assets.

Run each repository's `g2` modules with that repository as the current directory.
The two `g2` packages are separate; do not combine their source roots on `PYTHONPATH`.

The ordinary object frontend still requires genuine recorded RGB/depth/pose and matching model observations. Source GT labels are provenance only. Ordinary native structural-root perception is not implemented in this draft: its output is explicitly `BLOCKED_NATIVE_STRUCTURAL_ROOTS`, even with genuine object observations. Oracle snapshots require explicit diagnostic opt-in and cannot certify normal perception.

The [runbook](../docs/build/PSM-WMA_G2_N6_implementation_runbook_2026-11-08.md) defines the interfaces, commands, test evidence and remaining server gates. Original Layout 1/10, complex/oblique walls, whole-house material completeness and human visual review remain open.

F1-A adds strict official fixture/object identity binding and a separate source-scope gate. `COMPLETE` covers declared visual surfaces only. Ordinary plans require an exact source/role/material review, or explicit `--allow-declared-subset` diagnostic mode. Reviewed bundles retain and revalidate actual source evidence; a status field alone cannot certify a house. See the [F1-A handoff](../docs/build/PSM-WMA_G2_N6_F1_A_source_scope_2026-11-08.md). All data-server files remain local to that server.

F1-B skips only triangles proved to have exactly zero area in compiled input coordinates. Original local face IDs still index UVs; nonzero near-degenerate meshes remain rejected. Per-geom discard counts/IDs/area and budget failures are auditable. See the [F1-B handoff](../docs/build/PSM-WMA_G2_N6_F1_B_mesh_audit_2026-11-08.md). Actual Layout 1/10 whole-house classifications/materials remain pending server review.

F1-B2 adds pinned MuJoCo 3.3.7 primitive 2D/cube projection, per-point color reasons/area estimates and source-bound role assertions. `--require-role-evidence` checks original XML/include/body and compiled signatures; `--allow-unclassified` keeps source gaps as `PARTIAL_SOURCE`. It never assigns a role. Advertised `color_audit.npz` is required by the hashed producer identity and survives reviewed bundle sealing. Explicit sRGB, opacity, unsupported transforms and ambiguous cube colors retain unknown masks. See the [F1-B2 handoff](../docs/build/PSM-WMA_G2_N6_F1_B2_texture_role_2026-11-08.md). Real role correctness, complete material coverage and native four-frame acceptance remain independent server gates.
