# G2-N6 source adapter and native spatial preview runbook

Task: [PSM-WMA #26](https://github.com/wxwy/psm_wma/issues/26). Isolated V3 base: `7b8b733e1f585bb44a0eac7c14ad545c29355a86`. Native companion is stacked on nav_sg PR #7 `e86c3844325b13092e1713290b079cfb63466cfb`; neither parent nor production refs are modified.

## Implemented scope and open gates

The implemented diagnostic chain is source MJCF/assets/saved state → G2 visual XYZRGB → native ColorCloudMap/SDF/Room/SG → immutable G2 native 3D bundle → metric spatial assets. G2 reads native Room/Island memberships verbatim; it never clusters them. MuJoCo only provides source geometry/albedo here; there is no physics rollout or camera rendering.

The normal source adapter prepares commands for the existing genuine recorded RGB-D/pose and YOLOE/SigLIP path. Preparing a plan is not executing that path. A complete colored scan alone cannot certify perception. Native audits must match exact scene/source/build/frame/stamp/pose/camera, object IDs, bboxes and Room assignments before a normal bundle can be sealed.

**Normal native structural roots are absent in this draft.** Even a genuine recorded object run remains `BLOCKED_NATIVE_STRUCTURAL_ROOTS`: Floor/Upper/cardinal/Island completeness requires a separately reviewed native structural-root implementation. Diagnostic source roots stay privileged; they cannot be relabelled as normal perception. Issue #26 remains open. Original Layout 1/10, full-house visuals, oblique/complex walls, real model execution and human visual review are pending.

No Cosmos source, submodule/Gitlink, dataset, cache, model, training, simulation evaluation or production launcher is changed. All first-gate outputs have `training_ready=false`.

## Inputs and source contract

Use an isolated Python environment (author versions: Python 3.12.14, MuJoCo 3.3.7, NumPy 2.3.5, Pillow 11.3.0, pytest). Native tests use ROS Noetic/GCC 9 on Ubuntu 20.04; native C++ has no MuJoCo dependency.

```bash
python -m pip install -r g2/sim/requirements.txt pytest
python -m pytest g2/tests -q
```

The explicit `g2_sim_prescan_v1` role file must list every compiled geom. Example structure (replace identities with verified source records):

```json
{
  "schema": "g2_sim_prescan_v1",
  "scene_id": "Layout1",
  "state_source": {
    "model_source_sha256": "<complete XML/asset closure SHA256>",
    "states_sha256": "<original archive SHA256>"
  },
  "geoms": {
    "exact_visual_geom": {
      "role": "visual",
      "source_kind": "ep_meta",
      "ep_meta_pointer": "/fixtures/0",
      "source_instance_name": "<official cfg name>"
    },
    "exact_collision_geom": {
      "role": "collision",
      "source_kind": "mjcf",
      "geom_name": "exact_collision_geom"
    }
  }
}
```

Permitted roles are `visual`, `collision`, `robot`, `auxiliary`; all require explicit source provenance. `ep_meta` pointers retain the actual official record after checking its `name`. Exact `mjcf` binding is available for genuinely source-authored geoms and TEST_ONLY fixtures. Names/group IDs are not silently treated as semantic classes. Collision red is excluded by the explicit role declaration; the role mapping itself requires human source review.

All XML/includes/assets are loaded read-only into a private VFS and hashed. Gzip XML is supported with bounds. References must resolve uniquely inside explicit approved asset roots; unavailable absolute paths need a reviewed source/root mapping, not silent basename matching. Saved `qpos` or MuJoCo FULLPHYSICS state is restored with `mj_forward`, never `mj_step`; nonzero frames require the archive. Missing archive time is `null`/`missing`, not fabricated.

Finite box/sphere/ellipsoid/capsule/cylinder and mesh surfaces are sampled with a 5-million-point budget. Analytic primitive samples are projected onto the true surface. Constant source albedo and compiled 2D mesh UV repeat/bilinear texture sampling are supported. Primitive/cube texture projection, separate opacity textures, translucent surfaces, infinite planes and heightfields are unsupported. Default export fails on unsupported appearance; `--allow-partial-color` writes explicit invalid masks and **no COMPLETE marker**. A declared complete surface set still requires full-scene role/material human review.

## Simulation source export

Source/outputs must be separate, and every output must be new. `$GT` is the existing independently source-bound N5 tri-state export, whose legitimate free-region provenance must already be reviewed. Its grid wire-format name does not grant normal semantic oracle status. Color points alone never infer FREE space.

```bash
cd "$PSM_REPO"
python -m g2.sim.prescan --mjcf "$MODEL" --metadata "$VISUAL_ROLES" \
  --ep-meta "$EP_META" --states "$STATES" --frame 0 \
  --asset-root "$ASSET_ROOT" --spacing .05 \
  --native-manifest "$GT/frame0/manifest.json" --output "$NEW_COLOR0"
python -m g2.sim.prescan --mjcf "$MODEL" --metadata "$VISUAL_ROLES" \
  --ep-meta "$EP_META" --states "$STATES" --frame 200 \
  --asset-root "$ASSET_ROOT" --spacing .05 \
  --native-manifest "$GT/frame200/manifest.json" --output "$NEW_COLOR200"
```

The native manifest binding checks complete model closure, MuJoCo version, scene, archive hash and exact restored state format/row/time. It adopts the shared native geometry `source_sha256` and separately retains `visual_source_sha256`. Without a native manifest, the visual source identity is used directly.

Outputs: `precolored.txt` (`NAV_SG_PRECOLORED_CLOUD_V1`), `manifest.json`, and only for supported declared visual surfaces, `COMPLETE`. Manifest includes bounds, counts, source closure, adapter source SHA, actual appearance records, excluded roles, state and source raw-file hashes. No RGB image, robot trajectory, camera pose or native object detection is synthesized.

## Native processing and diagnostic roundtrip

Build the companion native branch in a **new** external Catkin workspace using its native runbook and pinned dependencies. In its activated Noetic overlay:

```bash
cd "$NAV_REPO"
export G2_GT_PROJECTION_MIN_Z=.2 G2_GT_PROJECTION_MAX_Z=1.8
export G2_GT_EXPORT_SPATIAL=true
export G2_GT_PRESCAN_FRAME0="$NEW_COLOR0/precolored.txt"
export G2_GT_PRESCAN_FRAME200="$NEW_COLOR200/precolored.txt"
bash g2/gt/native_gate.sh "$GT/frame0/grid.txt" "$GT/frame0/objects.txt" \
  "$NEW_NATIVE_OUTPUT" esdf_grid "$GT/frame200/grid.txt" "$GT/frame200/objects.txt"
```

Repeat with `gvd`, fresh master/output, and explicit slab appropriate to the actual source. This runs actual native map/Room/SceneGraph processing, including repeated-frame checks. Source object labels are explicitly oracle diagnostic. No generic room minimum-area filter is added; frozen GT seed 16, width cut 0.4 and geometry-only settings remain unchanged.

The snapshot contains native Building/Room/entity IDs, source instance/part/joint/category, mesh geometry, native grouping, relationships and world coordinates. Its full `grid_states.raw` preserves native UNKNOWN/FREE/OCCUPIED and exact grid geometry. `surfaces.csv` retains real native RGB plus entity ownership or `unknown`; uncolored object samples remain unknown color. Native bbox-gap grouping uses `<0.30 m`, object-only chains within native Rooms; Floor/Wall never relay separate components. Diagnostic oblique/complex walls conservatively make affiliations incomplete.

## Seal and render the native output

```bash
cd "$PSM_REPO"
python -m g2.nav_bridge.snapshot \
  --native-directory "$NEW_NATIVE_OUTPUT/frame_0/spatial_snapshot" \
  --output "$NEW_BUNDLE0" --allow-oracle-diagnostic
python -m g2.views.render --bundle "$NEW_BUNDLE0" \
  --output "$NEW_VIEWS0" --meters-per-pixel .05 --allow-oracle-diagnostic
```

Repeat for frame 200. The diagnostic switch is required at both boundaries. Ordinary capture instead requires `--native-run "$RUN/native_run.json"` and a genuine matching native audit; no diagnostic switch promotes GT semantics.

Sealing validates actual native IDs/references/finite geometry, point colors/masks, raw grid encoding and complete output, hashes every artifact before/after copying, and creates a content-addressed `bundle.json` plus `BUNDLE_COMPLETE`. The retained 3D bundle is the source for later multilayer/container queries; images do not replace it. This protocol binds evidence but is not a cryptographic model-execution attestation.

Rendering follows user-confirmed v1.5. House Floor top and Upper upward views are shared. Every Room references those plus four world-axis cardinal assets; no unsupported wall-aligned axis or four physical walls are invented. Missing boundaries reserve unknown slots. Native Island members are excluded from Room cardinals and receive four independent absolute-scale crops. Island grouping is never recomputed in G2.

All projections use fixed world metres per pixel, explicit axes/bounds, a 4-million-pixel budget, nearest visible geometry and separate `color_valid`/`geometry_valid` masks. Uncolored meshes occlude rear RGB; unassigned external samples cannot occlude filtered Island assets. Color support is the actual fused voxel, with an explicitly recorded half-leaf depth tolerance; this cannot resolve subvoxel surfaces and is not a per-camera pixel measurement. No semantic palette fills holes. Valid black/white stays valid. Each asset keeps depth and native entity indices in `geometry.npz`. `views.json` supplies the global index-to-native-ID table; negative sentinels are explicit. Island crop padding is at least half the actual color voxel size, even at finer image resolutions.

Outputs include RGB/mask PNGs, per-view metadata, `views.json` and `PREVIEW_COMPLETE`. They are spatial views, **not temporal video** or a Cosmos training dataset. Human comparison may use original MuJoCo overhead RGB only as a reference, never as the rendered nav_sg result.

## Genuine recorded object adapter

```bash
cd "$PSM_REPO"
python -m g2.nav_bridge.recorded --prescan-manifest "$NEW_COLOR0/manifest.json" \
  --grid "$GT/frame0/grid.txt" --nav-repo "$NAV_REPO" \
  --dataset-root "$RECORDED_ROOT" --episode "$EPISODE" --camera "$CAMERA" \
  --sidecar "$GENUINE_SIDECAR" --frames 201 \
  --projection-min-z .2 --projection-max-z 1.8 --output "$NEW_PLAN"
```

For this ordinary recorded path, first re-export frame 0 with `--world-frame world` to a separate `$NEW_WORLD_COLOR0` and use that manifest in place of `$NEW_COLOR0` above. The legacy N1/N3 recorded pose messages and native parameters both use `world`; a diagnostic `map` cloud is rejected rather than silently relabelled. The original source geometry/coordinates must match the recorded Episode.

This writes `PLAN_ONLY_NOT_EXECUTED`, `recorded_binding.json`, parameter/replay argv arrays, native working directory and launch plan. It requires exact original `model.xml.gz`, `states.npz`, `ep_meta.json` SHA equality with recorded source manifests, complete frame-0 visual input, matching grid/cloud and actual recorded files. It does not launch ROS or models. Both repositories have a `g2` package: execute each argv in the specified native cwd, not a combined Python path.

On an independently approved server runtime, run `parameters_argv`, launch `mapping g2_semantic_review.launch` with its emitted params, start the genuine matching sidecar service using the existing N3 procedure, then run `replay_argv`. The genuine sidecar must cover the bounded first/final frames (0/200 for 201 frames); a 459-frame sidecar cannot be silently truncated. Snapshot export waits for the actual native ACK, successful semantic audit and exact color-worker frame. Normal source initialization does not disable live RGB-D updates or switch the map to oracle mode.

Do not run that sequence without the separate server/model execution gate. Missing genuine data/model observations are `BLOCKED_REAL_RGBD_OBSERVATIONS`. Even after real observations pass, the separate native structural-root implementation remains required for complete normal six+Island assets.

## Validation, failure handling and server handoff

Author CPU/native results and artifact digests are in `docs/evidence/g2_n6_2026-11-08/`. TEST_ONLY rectangular/L-shaped/doorway sources exercise frame 0/200 and both ESDFGrid/GVD. They are **not** the private original Layout 1/10. The doorway result remains a small-room risk, not evidence that all rooms survive seed 16.

FAIL: source/frame/state/hash mismatch, invalid color/grid/membership, partial appearance, stale native work, missing audit or unexpected marker must produce no successful completion for the failed stage. Preserve the partial output, record the reason and use a fresh output after a concrete fix. Do not weaken validity checks to obtain PASS.

Server backfill must record exact PSM/native commit IDs, binaries/build source hash, source and role-map hashes, RGB-D/sidecar provenance if used, mode/slab/settings, frame 0/200 Room/ID/geometry/Island changes, native/bundle/view hashes, before/after human visual review and unresolved risks. Run original Layout 1 and Layout 10 in both native modes and retain source-derived overhead references separately. Keep whole-house color, real perception, structural completeness, H1 and Cosmos execution as distinct gates. Draft publication requests review only; it does not close Issue #26 or authorize a merge.
