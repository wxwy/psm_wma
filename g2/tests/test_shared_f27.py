"""Verify the shared F27 producer's clean-frame and marker ordering on CPU."""

import pytest

from g2.views import f27


def test_shared_material_keyframe_binds_rooms_and_audits_before_overlay(
    monkeypatch, tmp_path
):
    calls = []
    model, data, specs, renderer = object(), object(), [], object()
    snapshot = {
        "scene_id": "scene",
        "source_sha256": "a" * 64,
        "frame_id": 20,
        "rooms": [{"uid": 3}, {"uid": 5}],
    }
    registry = {"surfaces": {}}
    output = tmp_path / "frame"
    pose = {"position_world": [1, 2, 3]}

    def compile_registry(actual_model, actual_data, actual_specs, actual_snap):
        assert (actual_model, actual_data, actual_specs, actual_snap) == (
            model,
            data,
            specs,
            snapshot,
        )
        calls.append("compile")
        return registry

    def save(
        bundle, manifest, actual_snap, stage, *, visual_mesh_by_room, keep_gpu_context
    ):
        assert actual_snap is snapshot and stage == output
        assert keep_gpu_context
        assert set(visual_mesh_by_room) == {3, 5}
        for uid, room in visual_mesh_by_room.items():
            assert room == {
                "scene_id": "scene",
                "source_sha256": "a" * 64,
                "frame_id": 20,
                "room_uid": uid,
                "source_model_sha256": "b" * 64,
                "surface_registry": registry,
                "surface_renderer": renderer,
            }
        calls.append("render_clean")
        return {"views": ["clean"]}

    def audit(report, current_registry):
        assert report == {"views": ["clean"]} and current_registry is registry
        calls.append("audit_clean")
        return 4

    def overlay(stage, actual_pose, *, style, appearance, preserve_clean):
        assert stage == output and actual_pose is pose
        assert style == "classic" and preserve_clean is False
        calls.append("overlay")
        return {"drawn_views": 1}

    monkeypatch.setattr(f27, "compile_surface_registry", compile_registry)
    monkeypatch.setattr(f27, "save_direct_material_views", save)
    monkeypatch.setattr(f27, "overlay_final_top_views", overlay)
    result = f27.render_material_keyframe(
        tmp_path,
        {},
        snapshot,
        output,
        model=model,
        data=data,
        specs=specs,
        model_source_sha256="b" * 64,
        renderer=renderer,
        robot_pose=pose,
        marker_style="classic",
        preserve_clean=False,
        audit_clean=audit,
        restore_camera=lambda: calls.append("restore_camera"),
    )
    assert result == ({"views": ["clean"]}, registry, {"drawn_views": 1}, 4)
    assert calls == [
        "compile",
        "render_clean",
        "restore_camera",
        "audit_clean",
        "overlay",
    ]


def test_shared_material_keyframe_restores_camera_on_raster_error(
    monkeypatch, tmp_path
):
    calls = []
    monkeypatch.setattr(f27, "compile_surface_registry", lambda *args: {})

    def fail(*args, **kwargs):
        raise ValueError("raster unavailable")

    monkeypatch.setattr(f27, "save_direct_material_views", fail)
    with pytest.raises(ValueError, match="raster unavailable"):
        f27.render_material_keyframe(
            tmp_path,
            {},
            {
                "scene_id": "scene",
                "source_sha256": "a" * 64,
                "frame_id": 0,
                "rooms": [{"uid": 0}],
            },
            tmp_path / "frame",
            model=object(),
            data=object(),
            specs=[],
            model_source_sha256="b" * 64,
            renderer=object(),
            audit_clean=lambda *args: calls.append("audit"),
            restore_camera=lambda: calls.append("restore_camera"),
        )
    assert calls == ["restore_camera"]
