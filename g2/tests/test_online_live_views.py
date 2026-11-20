"""CPU checks for F27 owner/projection handoff and bounded diagnostic retention."""

from types import SimpleNamespace

import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError, digest, read_json, write_json
from g2.online import live_views


@pytest.fixture
def native(tmp_path, monkeypatch):
    axes = np.eye(3).tolist()
    reference = {"axes_world": axes, "origin_world": [0, 0, 0]}
    data = SimpleNamespace(
        geom_xpos=np.zeros((1, 3)),
        geom_xmat=np.eye(3).reshape(1, 9),
        robot_position=[0.3, 0.3, 0.1],
    )
    model = SimpleNamespace(geom_bodyid=[0])
    draws = []
    restores = []

    def save(
        bundle, manifest, snapshot, output, *, visual_mesh_by_room, keep_gpu_context
    ):
        draws.append(snapshot["frame_id"])
        assert manifest["version_sha256"] == digest(bundle / "snapshot.json")
        assert keep_gpu_context and 0 in visual_mesh_by_room
        native = "rooms/0/floor_top"
        rel = "sixview/floor_top.png"
        raw = output / "g2_original_gpu" / native
        raw.mkdir(parents=True)
        projection = {
            "axis": "floor_top",
            "reference_frame": snapshot["rooms"][0]["reference_frame"],
            "coordinate_frame": "NATIVE_ROOM_REFERENCE",
            "right_world": axes[0],
            "up_world": axes[1],
            "forward_world": axes[2],
            "uv_min_room": [0, 0],
            "width": 128,
            "height": 128,
            "meters_per_pixel": 0.01,
            "native_entity_ids": ["entity_1"],
        }
        write_json(raw / "view.json", projection)
        write_json(
            output / "g2_original_gpu" / "views.json", {"views": {native: projection}}
        )
        png = output / rel
        png.parent.mkdir()
        Image.new("RGB", (128, 128), "white").save(png)
        write_json(
            output / "direct_color_views.json",
            {
                "views": [
                    {"rgb_file": rel, "native_view": native, "sha256": digest(png)}
                ]
            },
        )

    monkeypatch.setattr(live_views, "save_direct_material_views", save)
    monkeypatch.setattr(
        live_views, "prepare_live_visual_specs", lambda *args: [{"g": 0}]
    )
    monkeypatch.setattr(live_views, "compile_surface_registry", lambda *args: {})
    monkeypatch.setattr(
        live_views,
        "renderer_member_sets",
        lambda _: {
            "rooms/0/floor_top": {
                "native_entity_ids": ["entity_1"],
                "room_uid": 0,
                "island_id": None,
            }
        },
    )
    monkeypatch.setattr(
        live_views,
        "SurfaceRenderer",
        lambda model, source, *args, **kwargs: SimpleNamespace(source_sha256=source),
    )
    monkeypatch.setattr(
        live_views,
        "chassis_pose",
        lambda model, data: {
            "position_world": data.robot_position,
            "forward_world": [1, 0, 0],
            "source_body": "mobilebase0_wheeled_base",
            "forward_axis": "body_local_positive_X",
        },
    )
    adapter = live_views.LiveF27(
        root=tmp_path / "f27",
        model=model,
        role_map={
            "scene_id": "live_scene",
            "state_source": {
                "model_source_sha256": "1" * 64,
                "states_sha256": "2" * 64,
            },
        },
        model_sha256="1" * 64,
        restore_camera=lambda: restores.append(len(draws)),
    )

    def publish(frame, *, live=True, room=reference):
        snapshot = {
            "scene_id": "live_scene",
            "source_sha256": "3" * 64,
            "frame_id": frame,
            "timestamp_ns": frame * 50_000_000,
            "world_frame": "world",
            "surface_color_source": "MUJOCO_GT_VISUAL_MESH_DIRECT_ONLY",
            "surface_transport_mode": "SOURCE_GT_GEOMETRY_ONLY_NO_PRESCAN",
            "rooms": [{"uid": 0, "reference_frame": room}],
            "entities": [{"id": "entity_1", "kind": "object"}],
            "full_map_source": {
                "live_frame": live,
                "live_state_sha256": "2" * 64 if frame == 0 else "4" * 64,
                "online_episode_id": "live_episode",
                "status": "MUJOCO_FULL_MAP_GT_PENDING_HUMAN",
            },
        }
        path = tmp_path / "snapshot.json"
        write_json(path, snapshot)
        return adapter.publish(snapshot, data=data, snapshot_path=path)

    return adapter, data, draws, restores, publish


def test_live_f27_maps_clean_and_marked_owner_frames(native):
    runtime, data, draws, restores, publish = native
    first = publish(0)
    assert first["event"] == "FULL"
    data.robot_position = [0.35, 0.3, 0.1]
    moved = publish(20)
    assert moved["event"] == "ARROW_ONLY"
    stationary = publish(40)
    assert stationary["event"] == "REUSE_ALL"
    assert moved["view_version"] == stationary["view_version"]
    assert draws == [0]
    views = stationary["spatial_metadata"]["views"]
    clean = views["sixview/floor_top"]
    marked = views["sixview/floor_top_w_rbs"]
    assert clean["image_owner"]["frame"] == 0
    assert marked["image_owner"]["frame"] == 20
    assert clean["image_projection"] == marked["image_projection"]
    assert clean["image_owner"]["sha256"] != marked["image_owner"]["sha256"]
    data.geom_xpos[0, 0] = 0.005
    changed = publish(60)
    assert changed["event"] == "FULL"
    assert draws == [0, 60]
    assert {p.name for p in runtime.root.iterdir() if p.is_dir()} == {"frame_60"}
    assert read_json(runtime.root / "latest_spatial_views.json") == changed
    runtime.close()
    assert restores == [1, 2, 2]


def test_nonlive_snapshot_rejected_before_renderer(native):
    _, _, draws, _, publish = native
    with pytest.raises(ContractError, match="verified native snapshot"):
        publish(0, live=False)
    assert draws == []


def test_changed_native_room_reference_gets_fresh_projection(native):
    _, _, draws, _, publish = native
    publish(0)
    changed = publish(
        20, room={"axes_world": np.eye(3).tolist(), "origin_world": [0.05, 0, 0]}
    )
    assert changed["event"] == "FULL"
    assert draws == [0, 20]
    floor = changed["spatial_metadata"]["views"]["sixview/floor_top"]
    assert floor["image_owner"]["frame"] == 20
    assert floor["image_projection"]["reference_frame"]["origin_world"] == [0.05, 0, 0]
