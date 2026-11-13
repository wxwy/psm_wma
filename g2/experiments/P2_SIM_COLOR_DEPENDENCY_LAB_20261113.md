# G2 P2 — Sim-only native color voxel dependency audit (2026-11-13)

**Status: F27 final PNG independence demonstrated in one real asset/layout; NOT approved to remove native color production stages.**

Formal V3 and nav_sg unchanged. All tests run in isolated /tmp on GPU 7, no full dataset producer.

## Original pipeline and dependencies

The source Full Map simulation mode already avoids native 10 cm nav_states. F27's primary geometry and color are computed by surface_registry + exact GPU mesh hits + MaterialResolver from the compiled MuJoCo Visual Mesh and its source-bound state.

Nonetheless, atomic_6views_run still performs:
1. prepare_color: generates/records native 10 mm colored source voxels (high CPU cost);
2. native_color_only: decodes the source 10 mm colors into a color-only native map and per-state receipts;
3. episode.render: verifies color_manifest and native_receipt SHA/count/state proofs, reads every native_view_color_TEMP.g2col10.bin; save_direct_color_views validates native surface arrays before invoking surface_renderer.

In the unified surface_registry path, F27 RGB comes from MuJoCo Visual Mesh, not from the color-point cloud. The legacy surface_data remains attached to validation/metadata and may compute a display-only wall median in missing-ceiling views. The final exported View uses a white-background contract. No correctness claim should be removed before verifying related status/receipt fields.

## Real GPU source-bound dependency counterfactual

Read-only accepted RoboCasa NavigateKitchen Episode 002022, first sampled state, eight View directions (Room/Island).

- Branch A: original source-bound native color arrays, 3,093,134 native color voxels, source-bound model/GT.
- Branch B: same exact model, SG snapshot, visual Geom registry, source material/UV, GPU scene, native geometry/owner evidence, but native 10 mm RGB pixels replaced by zero and validity values set to all false **only in the isolated test's memory**.
- Both call identical unmodified SurfaceRenderer and save_direct_color_views in separate test outputs.
- **8/8 final exported sixview/island PNGs have identical SHA256; no pixel differences.**

This is a *dependency experiment*, not valid provenance! Branch B intentionally violates the source native-color evidence contract and must NEVER be published or trained on. The test demonstrates that the final images in this sample do not need the native color raster, not that provenance validation can be bypassed.

## Next implementation gate

For simulation only, replace the Color/native_color_only stage and native g2col10 receipt contract with a new direct MuJoCo Visual Mesh/Material/GT source proof, including model/source SHA, state SHA, material ID, UV, owner, original alpha unknown flags, full-map provenance and preserved Room/SG source. Test first-state and complete-Episode parity for Room/Island Views, no ceiling, transparent glass, original-frame mapping and independent SG. Keep real RGB-D and nav_sg native chain unchanged.

Do NOT drop color validation globally or substitute the intentionally zeroed test arrays. The running 9,126 producer remains stopped and unchanged.
