"""Portable reviewed-input episode -> native dual-map -> G2 View workflow.

This entry consumes a materialized source manifest and verified spatial
snapshots. Dataset-wide discovery and snapshot/Room certification remain
separate stages. It never imports nav_sg's duplicate top-level g2 package.
"""
import argparse
import hashlib
import shutil
import time
from pathlib import Path

import numpy as np

from g2.io import ContractError, new_output, read_json, write_json
from .native_transport import (composed_digest, read_native_surface, sha_file,
                               write_layer_batch, write_sequence)


def bound_json(ref):
    path = Path(ref["path"]).resolve(strict=True)
    if sha_file(path) != ref["sha256"]:
        raise ContractError("input JSON bytes differ: " + str(path))
    return read_json(path)


def _source_paths(config):
    paths = [Path(config[k]["path"]) for k in ("source_manifest", "visual_inventory", "role_map")]
    paths.extend(Path(row["snapshot"]["path"]) for row in config["states"])
    return paths


def prepare(inputs, nav_manifest, output, *, color_only=False):
    from .direct_source import (build_one, get_data, identify_dynamic_geoms,
        load_source, prepare_visual_specs, verify_input_config)
    from .fast_static_dynamic_merge import aggregate, combine
    started = time.perf_counter()
    config = read_json(inputs)
    gt, _, _, snapshots = verify_input_config(config)
    frames = [row["frame"] for row in config["states"]]
    if type(config.get("layout")) is not int or config["layout"] <= 0 or not 2 <= len(frames) <= 300:
        raise ContractError("native episode adapter requires a positive layout ID and 2..300 states")
    if type(color_only) is not bool:
        raise ContractError("native color-only mode must be explicit")
    if color_only:
        if (nav_manifest is not None
                or gt["state"].get("format")!="mujoco_fullphysics"
                or any(s["source_mode"]!="full_map_mujoco_source"
                       or s.get("geometry_source_mode")!="FULL_MAP_MUJOCO_SOURCE"
                       or s.get("surface_transport_mode")!="SOURCE_GT_GEOMETRY_ONLY_NO_PRESCAN"
                       or s.get("surface_color_source")!="MUJOCO_GT_VISUAL_MESH_DIRECT_ONLY"
                       or s.get("completed_rgbd_observations")!=0
                       for s in snapshots)):
            raise ContractError("color-only requires proven MuJoCo Full Map without RGB-D or nav states")
        nav=None
    else:
        if nav_manifest is None:
            raise ContractError("legacy native dual-map mode requires nav_manifest")
        nav=read_json(nav_manifest)
        if (nav["source_scene_sha256"] != gt["source_sha256"]
                or frames != [row["frame"] for row in nav["frames"]]
                or nav.get("source_known_region_NOT_CERTIFIED") is not True):
            raise ContractError("navigation input differs from the requested episode states")
    reference = None
    if config.get("reference_color_manifest"):
        reference = bound_json(config["reference_color_manifest"])
        if (reference["source_sha256"] != gt["source_sha256"]
                or reference["frames"] != frames):
            raise ContractError("reference color episode/source differs")
    output = new_output(output, _source_paths(config) + [inputs] +
                        ([] if color_only else [nav_manifest]))
    model, initial, dense, role, states = load_source(config)
    if color_only:
        if (sha_file(gt["state"]["path"])!=gt["state"]["file_sha256"]
                or hashlib.sha256(np.asarray(states[0],dtype="<f8").tobytes()).hexdigest()!=
                   gt["state"]["row_sha256"]):
            raise ContractError("color-only original FULLPHYSICS source has changed")
        if frames[-1]>=len(states):
            raise ContractError("color-only frame exceeds source FULLPHYSICS episode")
    specs = prepare_visual_specs(model, initial, dense, role)
    moving, fixed, planning_s = identify_dynamic_geoms(model, states, frames, specs)
    output.mkdir(parents=True)
    (output / "payloads").mkdir()
    previous, layers, records = {}, {}, []
    static_cache = None
    for state_id, (frame, snapshot) in enumerate(zip(frames, snapshots)):
        tick = time.perf_counter()
        data = get_data(model, states[frame])
        center = np.asarray(snapshot["rooms"][0]["reference_frame"]["origin_world"], float)
        changed = []
        for spec in specs:
            geom = spec["g"]
            pose = np.concatenate([data.geom_xpos[geom], data.geom_xmat[geom].reshape(9)])
            if geom in previous and np.max(np.abs(previous[geom] - pose)) <= 1e-10:
                continue
            if state_id and geom in fixed:
                raise ContractError("source geom moved after static classification")
            layers[geom], _ = build_one(model, data, spec, center)
            previous[geom] = pose.copy()
            changed.append(spec)
        if state_id == 0:
            static_cache, _ = aggregate(layers, specs, fixed)
        dynamic_cache, _ = aggregate(layers, specs, moving)
        surface, _ = combine(static_cache, dynamic_cache)
        expected_sha, count, unknown = composed_digest(surface)
        state_sha = hashlib.sha256(np.asarray(states[frame], dtype="<f8").tobytes()).hexdigest()
        if not color_only and state_sha != nav["frames"][state_id]["source_state_row_sha256"]:
            raise ContractError("navigation and color source state rows differ")
        if reference is not None:
            ref = reference["states"][state_id]
            if ((expected_sha, count, unknown, state_sha) !=
                    (ref["expected_full_color_sha256"], ref["expected_full_color_voxels"],
                     ref["expected_unknown_owner_cells"], ref["source_state_sha256"])):
                raise ContractError("direct color map differs from independent reference")
        file = output / "payloads" / f"state_{state_id:06d}_frame_{frame:06d}.g2layer10.bin"
        encoded = write_layer_batch(file, frame=frame, scene_id=initial["scene_id"],
            source_sha=initial["source_sha256"], state_sha=state_sha, expected_sha=expected_sha,
            specs=specs, changed=changed, static_ids=fixed, layers=layers)
        row = dict(state_id=state_id, frame=frame, source_scene_id=initial["scene_id"],
            source_sha256=initial["source_sha256"], source_state_sha256=state_sha,
            source_state_file_sha256=gt["state"]["file_sha256"],
            expected_full_color_sha256=expected_sha, expected_full_color_voxels=count,
            expected_unknown_owner_cells=unknown, all_source_visual_geoms=len(specs),
            static_geom_count=len(fixed), dynamic_geom_count=len(moving),
            initial_all_static_and_dynamic=state_id == 0, native_color_leaf_m=.01,
            stage_prepare_s=round(time.perf_counter() - tick, 6), **encoded)
        records.append(row)
        print("G2_COLOR_STATE_PREPARED", frame, "voxels", count, "changed_geoms", len(changed),
              "reference_exact", reference is not None, flush=True)
    report = dict(schema="g2_direct_color_episode_prepared_v1", layout=config["layout"],
        source_sha256=initial["source_sha256"], source_model_sha256=dense["model_source_sha256"],
        source_inputs_sha256=sha_file(inputs),
        navigation_manifest_sha256=None if color_only else sha_file(nav_manifest),
        complete_episode_states=len(records), frames=frames, source_frame_count=len(states),
        preclassified_static_geoms=len(fixed), preclassified_dynamic_geoms=len(moving),
        dynamic_preplan_s=planning_s, states=records, training_ready=False,
        reference_color_exact=reference is not None, total_wall_s=round(time.perf_counter() - started, 6))
    if color_only:
        from .native_transport import write_color_only_sequence
        report["native_color_only_without_10cm_nav"] = True
        report["original_states_file_sha256"] = gt["state"]["file_sha256"]
        report["sequence_sha256"] = write_color_only_sequence(
            output / "native_sequence.txt", report)
    else:
        report["sequence_sha256"] = write_sequence(output / "native_sequence.txt", report, nav)
    report["complete"] = True
    write_json(output / "color_manifest.json", report)
    print("G2_EPISODE_SOURCE_PREPARED", output / "color_manifest.json", flush=True)
    return report


def _view_manifest(row, snapshot):
    reference = row["bundle_manifest"]
    manifest = bound_json(reference)
    bundle = Path(reference["path"]).resolve().parent
    if (manifest.get("source_sha256") != snapshot["source_sha256"]
            or manifest.get("scene_id") != snapshot["scene_id"]
            or manifest.get("world_frame") != snapshot["world_frame"]):
        raise ContractError("view bundle belongs to a different source scene")
    if manifest.get("frame_id") == snapshot["frame_id"]:
        if manifest.get("source_sha256") != snapshot["source_sha256"]:
            raise ContractError("view bundle source differs")
        if manifest["files"]["snapshot.json"]["sha256"] != row["snapshot"]["sha256"]:
            raise ContractError("view bundle snapshot bytes differ")
        return bundle, manifest
    # The verified dynamic snapshot supplies the current geometry/affiliations.
    # Bundle directory is retained only for legacy renderer metadata.
    dynamic = dict(schema="g2_dynamic_rederived_oracle_v1",
        version_sha256=hashlib.sha256((snapshot["source_sha256"] + ":" +
            str(snapshot["frame_id"]) + ":" + row["snapshot"]["sha256"]).encode()).hexdigest(),
        source_scope=dict(status="MUJOCO_FULL_MAP_GT_PENDING_HUMAN", full_scene_source_certified=False),
        training_ready=False)
    return bundle, dynamic


def _compare_views(stage, references):
    from PIL import Image
    expected = {row["relative_path"]: row for row in references}
    actual = {str(p.relative_to(stage)) for root in (stage / "sixview", stage / "islands")
              for p in root.rglob("*.png")}
    if not expected or len(expected) != len(references) or actual != set(expected):
        raise ContractError("reference/generated view directions differ")
    for relative, row in expected.items():
        if sha_file(row["path"]) != row["sha256"]:
            raise ContractError("reference image bytes changed")
        a = np.asarray(Image.open(row["path"]).convert("RGB"))
        b = np.asarray(Image.open(stage / relative).convert("RGB"))
        if a.shape != b.shape or not np.array_equal(a, b):
            raise ContractError("rendered RGB differs from reference: " + relative)
    return len(expected)


def _render(inputs, prepared, native_output, output, backend="gpu", *,
           visual_mesh_source=False, surface_registry_source=False,
           color_only=False, robot_pose_marker=True,
           robot_pose_marker_style="game_arrow"):
    from .direct_source import (verify_input_config, load_source, get_data,
                                prepare_visual_specs, certified_opaque_color_owner_indices)
    from g2.views.direct_color import save_direct_color_views
    from g2.views.alpha_source import compiled_translucent_only_owner_proof, save_source_alpha_sidecars
    started = time.perf_counter()
    config = read_json(inputs)
    _, _, _, snapshots = verify_input_config(config)
    prepared, native_output = Path(prepared), Path(native_output)
    colors = read_json(prepared / "color_manifest.json")
    if type(color_only) is not bool:
        raise ContractError("color-only View mode must be explicit")
    if color_only:
        if not surface_registry_source or any(
                s["source_mode"]!="full_map_mujoco_source"
                or s.get("surface_transport_mode")!="SOURCE_GT_GEOMETRY_ONLY_NO_PRESCAN"
                or s.get("surface_color_source")!="MUJOCO_GT_VISUAL_MESH_DIRECT_ONLY"
                or s.get("completed_rgbd_observations")!=0 for s in snapshots):
            raise ContractError("color-only F27 requires source-proved Full Map/Visual Mesh")
        complete = read_json(native_output / "G2_NATIVE_COLOR_ONLY_COMPLETE.json")
        if (colors.get("native_color_only_without_10cm_nav") is not True
                or colors.get("navigation_manifest_sha256") is not None
                or complete.get("schema")!="G2_NATIVE_COLOR_ONLY_EPISODE_V1"
                or complete.get("native_color_only_without_10cm_nav") is not True
                or complete.get("native_dual_map_same_process") is not False
                or complete.get("source_sha256")!=snapshots[0]["source_sha256"]
                or complete.get("scene_id")!=snapshots[0]["scene_id"]):
            raise ContractError("native GT color-only completion/source is invalid")
    else:
        complete = read_json(native_output / "F24_NATIVE_FULL_EPISODE_COMPLETE.json")
        if colors.get("native_color_only_without_10cm_nav"):
            raise ContractError("legacy dual-map cannot consume color-only GT source")
    configured_frames = [row["frame"] for row in config["states"]]
    expected_rows = colors.get("states")
    if (not isinstance(expected_rows, list) or len(expected_rows) != len(configured_frames)
            or colors.get("complete_episode_states") != len(configured_frames)
            or [row.get("frame") for row in expected_rows] != configured_frames
            or [row.get("state_id") for row in expected_rows] != list(range(len(configured_frames)))):
        raise ContractError("prepared state coverage/order is incomplete")
    if (colors.get("complete") is not True or colors["source_inputs_sha256"] != sha_file(inputs)
            or complete.get("complete_state_count") != len(snapshots)
            or complete.get("native_color_full_F22_sha_equal_every_state") is not True
            or (not color_only and complete.get("native_dual_map_same_process") is not True)
            or (not color_only and complete.get("source_known_region_is_TEST_ONLY_NOT_CERTIFIED") is not True)
            or colors["frames"] != configured_frames
            or sha_file(prepared / "native_sequence.txt") != colors["sequence_sha256"]):
        raise ContractError("native episode/source completion is missing or inconsistent")
    # Rebuild only the compiled identity/geom-role roster once; every source
    # file and state archive is verified by load_source before color recovery.
    model, initial, dense, role, states = load_source(config)
    if surface_registry_source:
        visual_mesh_source = True
    if visual_mesh_source and backend != "gpu" and not surface_registry_source:
        raise ContractError("GT visual-mesh geometry prototype requires GPU")
    visual_specs = prepare_visual_specs(model, initial, dense, role)
    opaque_ray_owner_indices = certified_opaque_color_owner_indices(model, visual_specs, initial)
    alpha_proof = None if surface_registry_source else compiled_translucent_only_owner_proof(
        model, visual_specs, initial, dense['model_source_sha256'])
    source_renderer = None
    if surface_registry_source:
        from .direct_source import identify_dynamic_geoms
        from g2.views.surface_renderer import SurfaceRenderer
        _, static_ids, planning_s = identify_dynamic_geoms(model, states, configured_frames, visual_specs)
        source_renderer = SurfaceRenderer(model, initial['source_sha256'], static_ids, backend=backend)
    output = new_output(output, _source_paths(config) + [inputs, prepared, native_output])
    output.mkdir(parents=True)
    rows = []
    native_fields = ("native_nav_10cm_occupancy_cells_verified", "rooms", "scene_graph_objects",
                     "scene_graph_assigned", "scene_graph_root_structures", "footprint_sha256",
                     "source_color_map_sha256", "native_total_color_voxels")
    for row, expected, snapshot in zip(config["states"], colors["states"], snapshots):
        state_started = time.perf_counter()
        frame = row["frame"]
        if expected["frame"] != frame:
            raise ContractError("prepared frame order differs")
        native = native_output / f"frame_{frame}"
        receipt = read_json(native / "native_receipt.json")
        if (receipt.get("frame") != frame or receipt.get("F22_F21_direct_10mm_map_RGB_owner_exact") is not True
                or receipt.get("source_color_map_sha256") != expected["expected_full_color_sha256"]):
            raise ContractError("native map receipt differs")
        if color_only:
            if (receipt.get("schema")!="G2_NATIVE_COLOR_ONLY_FRAME_V1"
                    or receipt.get("native_color_only_without_10cm_nav") is not True
                    or receipt.get("native_nav_10cm_occupancy_cells_verified","missing") is not None
                    or receipt.get("scene_id")!=snapshot["scene_id"]
                    or receipt.get("source_sha256")!=snapshot["source_sha256"]
                    or receipt.get("source_state_row_sha256")!=expected["source_state_sha256"]
                    or receipt.get("native_total_color_voxels")!=expected["expected_full_color_voxels"]
                    or receipt.get("native_unknown_owner_cells")!=expected["expected_unknown_owner_cells"]
                    or receipt.get("training_ready") is not False):
                raise ContractError("native-only 10mm color source is not state-bound")
        if row.get("reference_native_receipt"):
            reference = bound_json(row["reference_native_receipt"])
            compare = (("source_color_map_sha256","native_total_color_voxels")
                       if color_only else native_fields)
            if any(receipt.get(k) != reference.get(k) for k in compare):
                raise ContractError("native reference color/Room evidence differs")
        surface = read_native_surface(native / "native_view_color_TEMP.g2col10.bin", expected, snapshot)
        evidence=dict(surface[4], opaque_ray_owner_indices=opaque_ray_owner_indices,
                      opaque_ray_cert_schema="g2_verified_compiled_gt_opaque_owner_v1")
        surface = (*surface[:4], evidence)
        bundle, manifest = _view_manifest(row, snapshot)
        stage = output / f"state_{expected['state_id']:06d}_frame_{frame:06d}"
        visual_by_room=None
        registry = None
        if surface_registry_source:
            from g2.views.surface_registry import compile_surface_registry
            state=get_data(model, states[frame])
            registry=compile_surface_registry(model,state,visual_specs,snapshot)
            visual_by_room={r['uid']:dict(
                scene_id=snapshot['scene_id'],source_sha256=snapshot['source_sha256'],
                frame_id=frame,room_uid=r['uid'],source_model_sha256=dense['model_source_sha256'],
                surface_registry=registry,surface_renderer=source_renderer)
                for r in snapshot['rooms']}
        elif visual_mesh_source:
            from g2.views.visual_mesh_zbuffer import compile_visual_geom_frame
            state=get_data(model, states[frame])
            ids=sorted(e['id'] for e in snapshot['entities'])
            visual_by_room={
                r['uid']:compile_visual_geom_frame(
                    model,state,visual_specs,r,ids)
                for r in snapshot['rooms']
            }
            for source_geometry in visual_by_room.values():
                source_geometry.update(
                    scene_id=snapshot["scene_id"],
                    source_sha256=snapshot["source_sha256"],
                    frame_id=frame,
                    source_model_sha256=dense["model_source_sha256"])
        result = save_direct_color_views(bundle, manifest, snapshot, surface, stage,
                                        meters_per_pixel=.01, renderer_backend=backend,
                                        visual_mesh_by_room=visual_by_room,
                                        keep_gpu_context=surface_registry_source)
        # Native 10mm RGB remains opaque. RGBA alpha evidence is written as a
        # separate, explicitly not-training-ready layer; no fake background.
        if surface_registry_source:
            alpha_sidecar={'view_alpha_layers':[{'alpha_pixel_count':result['transparent_visible_pixels']}]}
            write_json(stage/'surface_registry.json',dict(
                schema=registry['schema'],scene_id=snapshot['scene_id'],source_sha256=snapshot['source_sha256'],
                frame_id=frame,native_scene_graph_modified=False,
                uncertain_surface_ids=registry.get('uncertain_surface_ids',[]),
                surfaces=[{k:v for k,v in record.items() if k in (
                    'surface_id','geom_id','spec_index','kind','semantic_owner_index','semantic_owner_id',
                    'material_id','structural_role','structural_role_evidence','source_evidence',
                    'room_affiliations','affiliation_status')} for record in registry['surfaces'].values()]))
        else:
            alpha_sidecar = save_source_alpha_sidecars(
                stage / "g2_original_gpu",
                read_json(stage / "g2_original_gpu/views.json"), snapshot, alpha_proof,
                stage / "alpha_source_layer", visual_mesh_by_room=visual_by_room)
        exact_views = _compare_views(stage, row["reference_views"]) if row.get("reference_views") else 0
        # Overlay the chassis only AFTER raw View pixel-parity verification.
        # This never enters native rendering, view geometry, or scene-graph data.
        marker = None
        if robot_pose_marker:
            from g2.views.robot_pose_marker import chassis_pose, overlay_final_top_views
            robot_data = (state if visual_mesh_source or surface_registry_source
                          else get_data(model, states[frame]))
            marker = overlay_final_top_views(
                stage, chassis_pose(model, robot_data), style=robot_pose_marker_style)
        if row.get("scene_graph"):
            sg = row["scene_graph"]
            graph = bound_json(sg)
            if graph["frame_id"] != frame or graph["scene_id"] != snapshot["scene_id"]:
                raise ContractError("source scene graph belongs to another frame/scene")
            shutil.copyfile(sg["path"], stage / "scene_graph.json")
        record = dict(frame=frame, state_id=expected["state_id"], view_count=result["view_count"],
            reference_pixel_exact_images=exact_views, native_color_sha256=receipt["source_color_map_sha256"],
            native_reference_exact=bool(row.get("reference_native_receipt")),
            view_render_s=result["gpu_render_and_export_s"],
            robot_pose_marker_drawn_views=marker["drawn_views"] if marker else 0,
            alpha_sidecar_count=sum(x["alpha_pixel_count"] for x in
                                    alpha_sidecar["view_alpha_layers"]),
            alpha_layers_have_unknown_background=True)
        record['state_wall_s']=round(time.perf_counter()-state_started,6)
        if surface_registry_source:
            record.update(unbound_visible_pixels=result['unbound_visible_pixels'],
                transparent_visible_pixels=result['transparent_visible_pixels'],
                surface_registry_count=len(registry['surfaces']),
                static_cache_hits=source_renderer.cache_hits,static_cache_misses=source_renderer.cache_misses)
        if visual_mesh_source:
            record.update(
                view_opaque_visual_geometry_from_source=True,
                source_surfel_geom_color_training_ready=False)
        rows.append(record)
        print("G2_NATIVE_VIEW_STATE_PASS", frame, "pixel_exact_images", exact_views, flush=True)
    if len(rows) != len(configured_frames):
        raise ContractError("episode render did not cover every requested state")
    report = dict(schema="g2_repository_native_view_episode_v1", complete=True,
        source_inputs_sha256=sha_file(inputs), spatial_state_count=len(rows), states=rows,
        renderer_backend=backend, color_leaf_m=.01, view_meters_per_pixel=.01,
        robot_pose_marker_enabled=robot_pose_marker,
        robot_pose_marker_style=robot_pose_marker_style if robot_pose_marker else None,
        training_ready=False, native_inputs_retained_for_audit=True,
        actual_wall_s=round(time.perf_counter() - started, 6))
    if color_only:
        report["native_color_only_without_10cm_nav"]=True
        report["native_nav_10cm_update_claimed"]=False
    if visual_mesh_source:
        report['view_opaque_geometry_source']='SOURCE_BOUND_VISUAL_MESH'
    if surface_registry_source:
        durations=np.asarray([r['state_wall_s'] for r in rows],float)
        report.update(view_opaque_geometry_source='SURFACE_REGISTRY_VISUAL_GEOMETRY',
            semantic_owner_optional=True,source_material_identity_per_pixel=True,
            native_scene_graph_modified=False,static_preplan_s=planning_s,
            static_cache_hits=source_renderer.cache_hits,static_cache_misses=source_renderer.cache_misses,
            state_latency_p50_s=float(np.percentile(durations,50)),state_latency_p95_s=float(np.percentile(durations,95)),
            first_state_s=float(durations[0]),warm_state_p50_s=float(np.median(durations[1:])) if len(durations)>1 else None,
            source_alpha_model='FRONT_SURFACE_PER_GEOM_SORTED_ALPHA_NO_REFRACTION',
            source_color_policy='SOURCE_LINEAR_NUMERIC_AND_APPEARANCE_COMPAT_PNG')
    write_json(output / "episode_receipt.json", report)
    print("G2_REPOSITORY_EPISODE_PASS", output / "episode_receipt.json", flush=True)
    return report


def render(inputs, prepared, native_output, output, backend="gpu", *,
           visual_mesh_source=False, surface_registry_source=False,
           color_only=False, robot_pose_marker=True,
           robot_pose_marker_style="game_arrow"):
    """Run a pinned episode with one renderer lifetime, including error cleanup."""
    try:
        return _render(inputs, prepared, native_output, output, backend,
                       visual_mesh_source=visual_mesh_source,
                       surface_registry_source=surface_registry_source,
                       color_only=color_only, robot_pose_marker=robot_pose_marker,
                       robot_pose_marker_style=robot_pose_marker_style)
    finally:
        if surface_registry_source:
            from g2.views.direct_color import close_gpu_renderers
            close_gpu_renderers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    p = commands.add_parser("prepare")
    p.add_argument("--inputs", required=True)
    p.add_argument("--nav-manifest")
    p.add_argument("--color-only",action="store_true")
    p.add_argument("--output", required=True)
    p = commands.add_parser("render")
    p.add_argument("--inputs", required=True)
    p.add_argument("--prepared", required=True)
    p.add_argument("--native-output", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--backend", choices=("cpu", "gpu"), default="gpu")
    p.add_argument("--color-only",action="store_true")
    p.add_argument("--robot-pose-marker", action=argparse.BooleanOptionalAction,
                   default=True, help="draw chassis position/heading on exported floor_top (default: on)")
    p.add_argument("--robot-pose-marker-style", choices=("classic", "game_arrow"),
                   default="game_arrow", help="final floor_top marker style (default: game_arrow)")
    p.add_argument("--renderer", choices=("f27", "legacy", "native"), default="f27",
                   help="F27 material/surface view (default); legacy Visual Mesh; native 10mm map diagnostic")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.inputs, args.nav_manifest, args.output,
                color_only=args.color_only)
    else:
        render(args.inputs, args.prepared, args.native_output, args.output, args.backend,
               visual_mesh_source=args.renderer in ("f27", "legacy"),
               surface_registry_source=args.renderer == "f27",
               color_only=args.color_only, robot_pose_marker=args.robot_pose_marker,
               robot_pose_marker_style=args.robot_pose_marker_style)


if __name__ == "__main__":
    main()
