"""Opt-in production-like indexed package for G2 F27 FULL/ARROW_ONLY/REUSE_ALL.

Never invoked by legacy v1 production. Only accepts a complete F27 receipt
with source-GT movement proof, per-sample independent SG, and a validated
on-disk physical owner for every reused PNG. Writes to a NEW destination
atomically; never creates symlinks or copies duplicate views.
"""

from __future__ import annotations

import gzip
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

from g2.offline.atomic_6views_compact import (
    _relative,
    read_json,
    PackageError,
    _write_json,
)
from g2.offline.scene_view_event_index import ViewEvent, index_state


def _digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _validate_event_source(source):
    root = Path(source).resolve(strict=True)
    receipt = read_json(root / "episode_receipt.json")
    states = receipt.get("states")
    if (
        receipt.get("schema") != "g2_repository_native_view_episode_v1"
        or receipt.get("complete") is not True
        or receipt.get("scene_event_index_enabled") is not True
        or receipt.get("source_material_identity_per_pixel") is not True
        or receipt.get("view_opaque_geometry_source")
        != "SURFACE_REGISTRY_VISUAL_GEOMETRY"
        or receipt.get("scene_motion_translation_tol_m") != 0.001
        or receipt.get("scene_motion_rotation_tol_deg") != 1.0
        or not isinstance(states, list)
        or len(states) != receipt.get("spatial_state_count")
    ):
        raise PackageError("source is not an opt-in complete F27 P1 episode")
    if receipt.get("sim_direct_material") is True:
        model_sha = receipt.get("source_model_sha256")
        if (
            not isinstance(model_sha, str)
            or len(model_sha) != 64
            or receipt.get("native_color_voxel_stage_removed") is not True
            or receipt.get("native_color_transport_claimed") is not False
        ):
            raise PackageError("direct material source proof missing")
        for state in states:
            state_hash = state.get("direct_material_state_sha256")
            if (
                not isinstance(state_hash, str)
                or len(state_hash) != 64
                or state.get("native_color_sha256") is not None
            ):
                raise PackageError(
                    "direct-material per-frame GT/native claim inconsistent"
                )
    prior = -1
    keyframe = None
    last_floor = None
    rows = []
    expected_views = None
    for index, state in enumerate(states):
        frame = state.get("frame")
        if (
            type(frame) is not int
            or frame <= prior
            or state.get("state_id") != index
            or state.get("view_count", 0) < 1
        ):
            raise PackageError("source frame/sequence invalid")
        prior = frame
        folder = root / f"state_{index:06d}_frame_{frame:06d}"
        if not folder.is_dir() or folder.is_symlink():
            raise PackageError("source F27 frame folder absent")
        dc = read_json(folder / "direct_color_views.json")
        if (
            dc.get("frame_id") != frame
            or dc.get("view_count") != state["view_count"]
            or dc.get("visual_geometry_source") != "SURFACE_REGISTRY_VISUAL_GEOMETRY"
            or dc.get("surface_material_identity_per_pixel") is not True
            or dc.get("training_ready") is not False
        ):
            raise PackageError("source per-frame material/view proof missing")
        views = dc["views"]
        if not isinstance(views, list) or len(views) != state["view_count"]:
            raise PackageError("source view inventory invalid")
        paths = []
        for item in views:
            path = _relative(item["rgb_file"])
            if path.as_posix() in paths:
                raise PackageError("duplicate source View path")
            paths.append(path.as_posix())
        mode = state.get("scene_event_mode")
        if mode == "FULL":
            expected_views = paths
        elif expected_views is None or set(paths) != set(expected_views):
            # An image inventory can change only at an actual scene render;
            # a skipped state may not acquire views from nowhere.
            raise PackageError("skipped state has changed view inventory")
        if mode not in ("FULL", "ARROW_ONLY", "REUSE_ALL"):
            raise PackageError("missing scene event mode")
        if mode == "FULL":
            keyframe = index
            last_floor = index
        elif mode == "ARROW_ONLY":
            last_floor = index
        if (
            state.get("scene_keyframe_state") != keyframe
            or state.get("final_floor_png_state") != last_floor
        ):
            raise PackageError("source scene keyframe or floor marker refs unbound")
        event = ViewEvent(
            index,
            frame,
            mode,
            keyframe,
            keyframe,
            last_floor,
            state.get("object_translation_max_m", float("nan")),
            state.get("object_rotation_max_deg", float("nan")),
            0.0,
            0.0,
        )
        parsed = index_state(event, paths)
        if mode != "FULL" and dc.get("scene_view_refs") != parsed["view_refs"]:
            raise PackageError("source scene image ref differs from event")
        if mode != "FULL" and dc.get("scene_materialized_views") != parsed["view_pngs"]:
            raise PackageError("source physical view list differs from event")
        for rel in parsed["view_pngs"]:
            image = folder / rel
            if not image.is_file() or image.is_symlink():
                raise PackageError("materialized F27 image absent")
        sg = folder / "scene_graph.json"
        if not sg.is_file() or sg.is_symlink():
            raise PackageError("source independent SG absent")
        graph = read_json(sg)
        if (
            graph.get("frame_id") != frame
            or graph.get("scene_id") != dc.get("scene_id")
            or graph.get("source_sha256") != dc.get("source_sha256")
        ):
            raise PackageError("SG not attached to current real source frame")
        island_ids = sorted(
            {Path(x).parts[1] for x in paths if x.startswith("islands/")}
        )
        rows.append(
            dict(
                frame=frame,
                folder=folder,
                graph=sg,
                islands=island_ids,
                paths=paths,
                index=parsed,
                mode=mode,
                event=event,
            )
        )
    return receipt, rows


def package_indexed(source, destination, *, episode_id, task_class, selection=None):
    """New v2 output, never touches formal v1 source, existing output, or plan."""
    receipt, rows = _validate_event_source(source)
    fp = None
    if selection is not None:
        fp = selection.get("source_fingerprint")
        if (
            selection.get("episode_id") != episode_id
            or selection.get("task_class") != task_class
            or selection.get("spatial_frames") != [row["frame"] for row in rows]
            or not isinstance(fp, str)
            or len(fp) != 64
        ):
            raise PackageError("pinned Episode identity mismatch")
    dest = Path(destination).absolute()
    orig = Path(source).resolve(strict=True)
    if (
        dest.exists()
        or dest.is_symlink()
        or dest == orig
        or dest in orig.parents
        or orig in dest.parents
    ):
        raise PackageError("cannot overwrite or overlap original source or output")
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="._g2_p1_stage_", dir=dest.parent))
    committed = False
    try:
        manifest_rows = []
        for i, row in enumerate(rows):
            frame = row["frame"]
            stage = tmp / f"state_{i:06d}_frame_{frame:06d}"
            stage.mkdir()
            for relative in row["index"]["view_pngs"]:
                source_png = row["folder"] / relative
                target = stage / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source_png, target)
            sg = read_json(row["graph"])
            if not sg.get("source_sha256") or not sg.get("scene_id"):
                raise PackageError("source SG provenance missing")
            with gzip.open(stage / "scene_graph.json.gz", "wb", compresslevel=3) as f:
                f.write(row["graph"].read_bytes())
            manifest_rows.append(
                dict(
                    frame=frame,
                    view_pngs=row["index"]["view_pngs"],
                    view_refs=row["index"]["view_refs"],
                    scene_keyframe_state=row["event"].scene_source_state,
                    floor_background_ref_state=row["event"].raw_floor_source_state,
                    update_mode=row["mode"],
                    islands=row["islands"],
                    scene_graph="scene_graph.json.gz",
                )
            )
        summary = {
            "schema": "g2_atomic_compact_6views_v2",
            "episode_id": episode_id,
            "task_class": task_class,
            "source_inputs_sha256": receipt["source_inputs_sha256"],
            "source_fingerprint": fp,
            "selection_pinned_for_resume": fp is not None,
            "source_renderer": "f27",
            "source_mode": "full_map_mujoco_source",
            "source_20hz": True,
            "spatial_frequency_hz": 2,
            "view_resolution_mpp": 0.01,
            "island_four_views_enabled": True,
            "robot_pose_marker_enabled": receipt.get("robot_pose_marker_enabled")
            is True,
            "robot_pose_marker_style": receipt.get("robot_pose_marker_style"),
            "robot_pose_marker_recipe_version": receipt.get(
                "robot_pose_marker_recipe_version"
            ),
            "robot_pose_marker_appearance": receipt.get("robot_pose_marker_appearance"),
            "robot_pose_marker_appearance_sha256": receipt.get(
                "robot_pose_marker_appearance_sha256"
            ),
            "states": manifest_rows,
            "state_count": len(rows),
            "complete": True,
            "training_ready": False,
            "native_voxels_saved": False,
            "colored_point_cloud_saved": False,
            "audit_source_kept_separately": True,
            "indexed_views_enabled": True,
            "image_reuse_basis": "NONROBOT_GT_VISUAL_POSE_AND_ROBOT_BASE_XY_YAW",
            "scene_motion_translation_tol_m": 0.001,
            "scene_motion_rotation_tol_deg": 1.0,
            "native_color_voxel_stage_removed": receipt.get("sim_direct_material")
            is True,
            "native_color_transport_claimed": False
            if receipt.get("sim_direct_material")
            else True,
            "source_model_sha256": receipt.get("source_model_sha256")
            if receipt.get("sim_direct_material")
            else None,
        }
        _write_json(tmp / "episode_manifest.json", summary)
        _write_json(
            tmp / "COMPLETE.json",
            {
                "schema": summary["schema"],
                "complete": True,
                "episode_id": episode_id,
                "state_count": len(rows),
                "renderer": "f27",
                "training_ready": False,
                "source_fingerprint": fp,
                "episode_manifest_sha256": _digest(tmp / "episode_manifest.json"),
            },
        )
        from g2.offline.scene_view_index_package import validate_indexed_episode

        assert validate_indexed_episode(tmp) == len(rows)
        os.rename(tmp, dest)
        committed = True
        print("G2_P1_V2_PACKAGE_PASS", dest, len(rows), flush=True)
        return summary
    finally:
        if not committed:
            shutil.rmtree(tmp, ignore_errors=True)


def completed_output_indexed(row, output_root):
    """Explicit opt-in v2 resume guard. Old v1 completion untouched."""
    final = Path(output_root) / row["expected_relative_output"]
    if not final.exists() and not final.is_symlink():
        return False
    if not final.is_dir() or final.is_symlink():
        raise PackageError("invalid indexed output path")
    marker = read_json(final / "COMPLETE.json")
    summary = read_json(final / "episode_manifest.json")
    if (
        marker.get("schema") != "g2_atomic_compact_6views_v2"
        or summary.get("schema") != marker.get("schema")
        or marker.get("source_fingerprint") != row["source_fingerprint"]
        or summary.get("source_fingerprint") != row["source_fingerprint"]
        or marker.get("episode_id") != row["episode_id"]
        or summary.get("task_class") != row["task_class"]
        or [s.get("frame") for s in summary.get("states", [])] != row["spatial_frames"]
        or summary.get("scene_motion_translation_tol_m") != 0.001
        or summary.get("scene_motion_rotation_tol_deg") != 1.0
        or summary.get("indexed_views_enabled") is not True
        or summary.get("image_reuse_basis")
        != "NONROBOT_GT_VISUAL_POSE_AND_ROBOT_BASE_XY_YAW"
    ):
        raise PackageError("invalid indexed v2 completed identity/recipe")
    from g2.offline.scene_view_index_package import validate_indexed_episode

    if validate_indexed_episode(final) != len(row["spatial_frames"]):
        raise PackageError("indexed v2 completion invalid")
    return True
