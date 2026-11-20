"""Render a source-bound F27 keyframe for offline or live callers."""

from __future__ import annotations

from .direct_color import save_direct_material_views
from .robot_pose_marker import (
    DEFAULT_MARKER_STYLE,
    MarkerAppearance,
    overlay_final_top_views,
)
from .surface_registry import compile_surface_registry


def prepare_surface_rooms(
    model, data, specs, snapshot, *, model_source_sha256, renderer
):
    """Compile the current Visual registry and its native Room bindings once."""
    registry = compile_surface_registry(model, data, specs, snapshot)
    rooms = {
        room["uid"]: {
            "scene_id": snapshot["scene_id"],
            "source_sha256": snapshot["source_sha256"],
            "frame_id": snapshot["frame_id"],
            "room_uid": room["uid"],
            "source_model_sha256": model_source_sha256,
            "surface_registry": registry,
            "surface_renderer": renderer,
        }
        for room in snapshot["rooms"]
    }
    return registry, rooms


def render_material_keyframe(
    bundle,
    manifest,
    snapshot,
    output,
    *,
    model,
    data,
    specs,
    model_source_sha256,
    renderer,
    robot_pose=None,
    marker_style=DEFAULT_MARKER_STYLE,
    marker_appearance=None,
    preserve_clean=True,
    audit_clean=None,
    restore_camera=None,
):
    """Render source material, audit clean pixels, then optionally stamp a marker.

    The caller owns authoritative state and output lifecycle. Offline supplies
    its alpha/source audit before stamping. The live Actor restores its camera
    context after the raster's EGL operations.
    """
    registry, rooms = prepare_surface_rooms(
        model,
        data,
        specs,
        snapshot,
        model_source_sha256=model_source_sha256,
        renderer=renderer,
    )
    try:
        report = save_direct_material_views(
            bundle,
            manifest,
            snapshot,
            output,
            visual_mesh_by_room=rooms,
            keep_gpu_context=True,
        )
    finally:
        if restore_camera is not None:
            restore_camera()
    audit = audit_clean(report, registry) if audit_clean is not None else None
    marker = None
    if robot_pose is not None:
        marker = overlay_final_top_views(
            output,
            robot_pose,
            style=marker_style,
            appearance=marker_appearance
            if marker_appearance is not None
            else MarkerAppearance(),
            preserve_clean=preserve_clean,
        )
    return report, registry, marker, audit
