# G2 F2 source binding, Full Map and native connection views

Formal immutable code pair: PSM `c4c2a36431478825b2f1db8b0fa7b74c11ac9b2d`; native `c5825589cc748145819dfc17cfeb7a026aa08c46`. Later branch tips carry documentation/publication receipts only; source scopes remain identical to this pair.

Codex author implementation for [Issue26/6736467892](https://github.com/wxwy/psm_wma/issues/26#issuecomment-6736467892), paired with [nav_sg Issue8/6736440426](https://github.com/wxwy/nav_sg/issues/8#issuecomment-6736440426). Independent PSM branch `codex/g2-f2-source-views` starts at `feff0d54b04a4c669198ec48493736bbc5dcaa81`; native branch `codex/g2-f2-thin-floor-full-map` starts at `e15c4cc28a157526a53827f29aeb70f88c845a66`. Fixed publication SHAs are recorded in the canonical Inbox and the two Issue handoffs. No source branch is merged.

The user authorizes implementation now, followed by GPT independent server verification and Owner visual review. The historical V2/MM/Kimi workflow does not apply to this G2 handoff. This run uses no Remote Desktop Commander, server checkout, private scene files, GPU, model inference or training. The `cosmos-framework` Gitlink remains `1ca308055fc41fb69efaeb9efaa23808f164a18e`. Existing scene-release configurations remain frozen.

## Receiving and source contracts

`g2.sim.model_rebinding` records the original gzip bytes separately from the rebound XML. Exact canonical prefix rules are the only permitted transformation. It recursively replays includes into a temporary model, checks current asset bytes and closure, recompiles the transformed original, and restores each selected state row. Geometry, UV/material data, body names, official ep_meta, state archive/row/format and source time are bound. An original include must exist; missing historical XML is not invented. Asset closure and historical generator certification remain separate. Expanded XML, original/include hashing, asset and state archive reads have explicit budgets. Original and rebound include directories are protected from output overlap.

`recorded.prepare(..., model_rebinding_proof=...)` verifies this replay against the actual pre-scan and the recorded episode's original compressed model hash. Without a proof the previous exact root-hash comparison still applies. A legal qpos archive without time retains `timestamp=None` and `timestamp_source=missing`; recorded RGB-D supplies its own genuine timestamps. Full Map separately requires a real finite source-state time.

`g2.nav_bridge.full_map` is a separate source-GT route. It pins and reuses nav_sg's existing MuJoCo exporter/verifier, verifies actual XML/assets/auxiliary metadata, recompiles and restores source state, rechecks the complete compiled geom audit and role declarations, and recomputes source entity geometry. It accepts COMPLETE declared subsets or PARTIAL_COLOR with all geom identities classified and the original invalid-color attachment intact. Neither is upgraded to full-scene certification. It preserves the existing closed-solid/unsupported-geometry checks; it does not make arbitrary visual meshes eligible for solid GT export.

The native plan carries `NAV_SG_FULL_MAP_SOURCE_V1` with source/scene/frame/world/time, exact native manifest and grid/object/cloud hashes. The native entry parses the actual MuJoCo and color manifests and validates those identities; hashes correspond to the bytes actually parsed. It runs the existing native GT map/Room/scene graph and color reader/fusion. Its source mode is `FULL_MAP_MUJOCO_SOURCE`, snapshot mode `full_map_mujoco_source`, backend `ORACLE_GRID`, and object status `MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS`. Its completion marker is `FULL_MAP_PREVIEW_COMPLETE`, not the legacy diagnostic marker.

Full Map capture requires its dedicated source proof, actual source entities and unchanged raw occupancy. Every source point keeps XYZ (native float32 conversion), RGB, invalid bit and the original face/reason/area attachment order. A BVH verifies each supplied native owner using the exact C++ triangle-distance branches and unique-owner rule, including non-finite repeated-vertex face results. It rejects both substituting another legal entity ID and turning a unique owner into unknown. This validator emits no entity, Room or Island IDs. Re-signed files do not bypass source, scope or ownership checks.

Ordinary capture still requires genuine current RGB-D/model evidence. GT cannot pass it through an opt-in flag. Full Map, source-role review, observation acceptance, human review and training acceptance remain distinct; `training_ready=false` and `full_scene_source_certified=false` throughout this new route.

## Native connection and view contract

Native nav_sg supplies `NATIVE_BBOX_OBJECT_ROOT_CONNECTIONS_V2`. G2 validates its certificates, then renders the supplied membership and IDs:

- All edges use minimum 3D world-AABB Euclidean gap, strictly `< connection_distance` (default 0.30 m). Only eligible objects in the same native Room relay. Structural roots and robots never relay.
- BEV uses Floor YES objects. UP uses Floor NO objects, with no Ceiling requirement or Camera-Z cutoff. UNKNOWN remains excluded and recorded. A hanging cabinet can appear in a wall view and UP without joining BEV through Floor→Wall.
- Four Room directions use native wall-derived reference axes and actual adjacent Wall meshes. Only native paths to those Walls provide wall-view membership. Missing directions are explicitly OPEN within the declared source inventory, or UNKNOWN for incomplete observations; neither creates a physical wall. Absence in a declared inventory is not independent whole-scene absence certification.
- Island IDs and components remain native: Floor YES, any real Wall NO. Four Island views live under `rooms/<uid>/islands/<native_id>` and do not enter Room wall views.
- Native floor and ceiling display references retain source entity IDs/hashes. A wall-top/configured ceiling reference is explicitly not detected ceiling and does not classify height.

The normal native object cluster contains no certified robot/category identity by default. It therefore stays `UNKNOWN_NATIVE_IDENTITY_NO_RELAY`. A genuine producer can supply an explicit `SpatialRelayRole` with a source-evidence SHA; only a source-bound Object relays. This implementation does not claim that YOLOE/SigLIP has supplied that missing identity. The Full Map route can supply source-GT objects before model observations.

PNG RGB/color-valid/geometry-valid images, metric depth/owner arrays, per-view recipes and `index.html` are generated on the execution machine. `--reference-image` optionally attaches that machine's real MuJoCo comparison image and hash; none was supplied for this author's synthetic runs. All human gates remain pending.

## Commands and handoff

Use a fresh output directory for every command; set variables to server-local files without copying them out. Code updates come from the two fixed GitHub commits, not by editing a server checkout.

```bash
python -m g2.sim.model_rebinding create \
  --original-gzip "$ORIGINAL_MODEL_GZ" --rebased-xml "$REBASED_XML" \
  --states "$STATES_NPZ" --ep-meta "$EP_META_JSON" --rules "$EXACT_PREFIX_RULES_JSON" \
  --asset-root "$ASSET_ROOT" --frames 0 200 --output "$NEW_PROOF_DIR"

python -m g2.nav_bridge.full_map prepare \
  --native-manifest "$GT_FRAME_DIR/manifest.json" \
  --color-manifest "$COLOR_FRAME_DIR/manifest.json" --nav-repo "$NAV_F2" \
  --model-rebinding-proof "$NEW_PROOF_DIR/rebinding.json" \
  --room-source gvd --min-z .15 --max-z 1.8 --output "$NEW_PLAN_DIR"
```

Execute `plan.json`'s exact `argv`, `cwd` and `environment` in the isolated Noetic overlay; the plan itself does not run a native process. Repeat independently for frames 0 and 200, or use native_gate's existing next-frame arguments and the corresponding second proof/cloud environment variables. A frame200-only plan uses the first input slot but preserves actual frame_id=200. Port/ROS_HOME must be isolated. Native segmentation remains the existing seed16, width_cut0.4, geometry_only profile.

```bash
python -m g2.nav_bridge.full_map capture \
  --native-directory "$NATIVE_RUN/frame_$FRAME/spatial_snapshot" \
  --prepared "$NEW_PLAN_DIR" --expected-build-source-sha256 "$NATIVE_SOURCE_SHA256" \
  --output "$NEW_BUNDLE_DIR"
python -m g2.views.render --bundle "$NEW_BUNDLE_DIR" --output "$NEW_VIEWS_DIR" \
  --allow-full-map-mujoco --reference-image "$LOCAL_MUJOCO_REFERENCE_IMAGE"
```

For the genuine recorded route use `g2.nav_bridge.recorded` with the optional rebinding proof and the existing real RGB-D/pose/model sidecar. Do not fabricate observations to make the full-map preview render.

Author reproduction, CPU only:

```bash
python -m pytest -q g2/tests
python -m g2.tests.full_map_cpu_smoke prepare --nav-repo "$NAV_F2" --output "$NEW_OWN_SMOKE"
# In the native CPU overlay, execute each emitted plan.
python -m g2.tests.full_map_cpu_smoke collect --output "$NEW_OWN_SMOKE"
python -m g2.tests.full_map_cpu_smoke negative --output "$NEW_OWN_SMOKE"
```

Actual author results: **517/517 Python**, original **446/446** IDs retained; native **168/168 distinct C++**, original157 retained; related native Python/GT **100/100**, original53 retained. Two own MJCF scenes × frame0/200 produced source-bound native bundles and previews: rectangular25,208 points,14 views,2Islands per frame; notch27,344 points,10 views,1Island per frame. The notch's extra actual Wall correctly removes one source block from Island membership. Four actual native CSVs pass exact source and owner replay. Eight re-signed bundle/source negatives and eleven native input negatives reject. Two ordinary main backend runs each process4 RGB-D frames and export frame0/3 snapshots with only4 observed thin-floor columns,1196 unsupported columns and UNKNOWN below; independent G2 verification passes and genuine-model capture remains blocked. A separate default-off ordinary run passes4-frame ACK/nonempty-map checks.

Evidence is in `docs/evidence/g2_f2_2026-11-09/`: raw JUnit/logs, retention/source inventories, native/main/Full Map summaries, negative results, peer review and protected refs. All inputs here are author-created; no private Layout1/10 file is included. This does not close real-source, native real-scene, six-view, historical generator, full-color, H1 or training gates. GPT next checks fixed-source identity and real Layout1/10 frame0/200 locally, then Owner reviews actual Room/Wall/Object/six-view/Island comparisons. DS, Cosmos and training remain out of this handoff.
