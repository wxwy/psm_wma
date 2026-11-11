"""Source-mesh geometry must own visibility, source RGB only after proof gates."""

import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError
from g2.views.visual_mesh_zbuffer import compile_visual_geom_frame, view_source_zbuffer


def source_with_fake_geom():
    # Geom ID 0 is opaque, geom 1 has source invalid RGB, geom 2 translucent.
    attributes = {
        0: {
            "owner": 0,
            "native_id": "entity_0",
            "geom_name": "opaque",
            "material_opaque": True,
            "source_valid_color_sample_count": 100,
            "source_all_color_sample_count": 100,
        },
        1: {
            "owner": 1,
            "native_id": "entity_1",
            "geom_name": "opaque_unknown",
            "material_opaque": True,
            "source_valid_color_sample_count": 0,
            "source_all_color_sample_count": 100,
        },
        2: {
            "owner": 2,
            "native_id": "entity_2",
            "geom_name": "glass",
            "material_opaque": False,
            "source_valid_color_sample_count": 0,
            "source_all_color_sample_count": 100,
        },
    }
    sample = [0.0, 0.0, 0.0]
    faces = [[0, 1, 2]]
    return {
        "source_visual_schema": "SIGNED_MUJOCO_GT_VISUAL_GEOMETRY_PER_GEOM_V1",
        "opaque": [(0, [sample] * 3, faces), (1, [sample] * 3, faces)],
        "translucent": [(2, [sample] * 3, faces)],
        "attributes": attributes,
        "source_unbound_visual_geom_names": [],
        "native_owner_ids": ["entity_0", "entity_1", "entity_2"],
        "training_ready": False,
    }


def test_visual_source_zbuffer_cannot_steal_color_from_same_pixel_other_owner(
    monkeypatch,
):
    """Same 2D location from another native object must never repaint occluder."""
    source = source_with_fake_geom()

    class FakeEngine:
        def draw(self, meshes, selected, lo, hi, axis, mpp):
            assert selected == {0, 1}
            geom = np.ones((2, 2), bool)
            depth = np.zeros((2, 2), float)
            owner = np.asarray([[0, 0], [1, 1]], np.int32)
            return geom, depth, owner, (2, 2), {"triangles": 1}

    class FakeProjector:
        def select(self, *args):
            xyz, rgb, valid, owner, selected = args[:5]
            # Correct source (0) at 0,0; source owner1 can't be used for
            # visible owner0 at 0,1 even if color is present at that pixel.
            # At 1,0 source owner1 is unverified material and stays UNKNOWN;
            # at 1,1 color source1 is 2cm away in depth and stays unknown.
            return (
                np.asarray([0, 1, 2, 3]),
                np.asarray([0, 0, 1, 1]),
                np.asarray([0, 1, 0, 1]),
                np.asarray([0.0, 0.0, 0.0, 0.02]),
                {},
            )

    import g2.views.exact_compute as exact
    import g2.views.gpu_color_select as col

    monkeypatch.setattr(exact, "get_engine", lambda: FakeEngine())
    monkeypatch.setattr(col, "get_projector", lambda: FakeProjector())
    arrays = (
        np.asarray([[0, 0, 0], [0, 0, 0], [0, 0, 0], [0, 0, 0.02]], float),
        np.asarray(
            [[240, 250, 240], [120, 20, 10], [40, 40, 40], [40, 40, 40]], np.uint8
        ),
        np.ones(4, bool),
        np.asarray([0, 1, 1, 1], np.int32),
    )
    image, valid, geom, depth, owner, geomid, meta = view_source_zbuffer(
        source,
        *arrays,
        {0, 1},
        [0, 0, 0],
        [0.009, 0.009, 0.009],
        "floor_top",
        meters_per_pixel=0.01,
        backend="gpu",
    )
    assert geom.all()
    assert valid.tolist() == [[True, False], [False, False]]
    assert (image[0, 0] == [240, 250, 240]).all()
    assert np.array_equal(owner, np.asarray([[0, 0], [1, 1]], np.int32))
    assert meta["source_collision_geometry_used_for_zbuffer"] is False
    assert meta["visual_mesh_color_invalid_pixels"] == 3
    assert meta["training_ready"] is False


def test_visual_source_rejects_missing_gt_certification():
    src = source_with_fake_geom()
    del src["source_visual_schema"]
    with pytest.raises(ContractError):
        view_source_zbuffer(
            src,
            np.zeros((1, 3)),
            np.zeros((1, 3), np.uint8),
            np.ones(1, bool),
            np.zeros(1, np.int32),
            {0},
            [0, 0, 0],
            [1, 1, 1],
            "floor_top",
            backend="gpu",
        )


def test_compiled_visual_source_separates_translucent_from_opaque(monkeypatch):
    class Model:
        geom_xmat = np.asarray([np.eye(3).ravel()] * 3)
        geom_xpos = np.asarray([[0.0, 0.0, 0.0]] * 3)

    model = Model()
    specs = []
    for i in range(3):
        specs.append(
            {
                "owner": i,
                "g": i,
                "name": f"geom_{i}",
                "vertices": [[0, 0, 0], [0.02, 0, 0], [0.02, 0.02, 0.02]],
                "faces": [[0, 1, 2]],
                "original_valid_samples": 1 if i == 0 else 0,
                "original_dense_samples": 5,
            }
        )
    import g2.sim.source_geometry as source

    monkeypatch.setattr(
        source,
        "effective_rgba",
        lambda m, g: np.asarray([1, 1, 1, 0.2 if g == 2 else 1.0]),
    )
    room = {
        "uid": 0,
        "reference_frame": {
            "origin_world": [0, 0, 0],
            "axes_world": np.eye(3).tolist(),
        },
    }
    datum = type(
        "D", (), {"geom_xmat": model.geom_xmat, "geom_xpos": model.geom_xpos}
    )()
    result = compile_visual_geom_frame(
        model, datum, specs, room, ["entity_0", "entity_1", "entity_2"]
    )
    assert len(result["opaque"]) == 2
    assert len(result["translucent"]) == 1
    assert result["attributes"][2]["material_opaque"] is False
    assert result["training_ready"] is False


def test_source_alpha_is_projected_from_actual_transparent_visual_mesh_not_collision(
    monkeypatch, tmp_path
):
    from g2.views.alpha_source import save_source_alpha_sidecars
    from g2.tests.test_direct_color_views import source_case

    snapshot, _, _ = source_case()
    ids = sorted(e["id"] for e in snapshot["entities"])
    src = "entity_5"
    ix = ids.index(src)
    proof = {
        "schema": "g2_compiled_gt_alpha_only_source_v1",
        "scene_id": snapshot["scene_id"],
        "source_sha256": snapshot["source_sha256"],
        "model_source_sha256": "e" * 64,
        "supported_owner_materials": {
            src: {
                "owner_index": ix,
                "rgba": [1, 1, 1, 0.2],
                "geom_name": "source_glass_visual_geom",
                "source_model_sha256": "e" * 64,
            }
        },
        "skipped_mixed_or_textured_owners": {},
    }
    root = tmp_path / "render"
    folder = root / "rooms/0/plus_Y"
    folder.mkdir(parents=True)
    rgb = np.full((2, 3, 3), 0, np.uint8)
    rgb[0, 1] = [60, 70, 80]
    Image.fromarray(rgb).save(folder / "rgb.png")
    geom = np.zeros((2, 3), np.uint8)
    geom[0, 1] = 255
    Image.fromarray(geom).save(folder / "geometry_valid.png")
    color_valid = np.zeros((2, 3), np.uint8)
    color_valid[0, 1] = 255
    Image.fromarray(color_valid).save(folder / "color_valid.png")
    owner = np.full((2, 3), -2, np.int32)
    owner[0, 1] = 0  # opaque different object; glass is in front
    depth = np.full((2, 3), np.nan, np.float32)
    depth[0, 1] = 0.06
    np.savez_compressed(folder / "geometry.npz", native_entity_index=owner, depth=depth)
    translucent = {
        "attributes": {7: {"native_id": src, "geom_name": "source_glass_visual_geom"}},
        "translucent": [(7, [[0, 0, 0]] * 3, [[0, 1, 2]])],
        "opaque": [],
    }

    class FakeEngine:
        def draw(self, *args):
            mask = np.zeros((2, 3), bool)
            mask[0, 0] = True
            mask[0, 1] = True
            geometry_depth = np.full((2, 3), np.nan, dtype=float)
            geometry_depth[0, 0] = 0.01
            geometry_depth[0, 1] = 0.02
            which = np.full((2, 3), -2, dtype=np.int32)
            which[0, 0] = 7
            which[0, 1] = 7
            return mask, geometry_depth, which, (3, 2), {}

    import g2.views.exact_compute as exact

    monkeypatch.setattr(exact, "get_engine", lambda: FakeEngine())
    rendered = {
        "views": {
            "rooms/0/plus_Y": {
                "image_generated": True,
                "native_entity_ids": [src],
                "axis": "+Y",
                "room_bounds_min": [0, 0, 0],
                "room_bounds_max": [0.03, 0.02, 0.08],
            }
        }
    }
    result = save_source_alpha_sidecars(
        root,
        rendered,
        snapshot,
        proof,
        tmp_path / "alpha",
        visual_mesh_by_room={0: translucent},
    )
    assert result["view_count"] == 1
    assert result["source_visual_mesh_for_transparency"] is True
    assert result["view_alpha_layers"][0]["alpha_pixel_count"] == 2
    pix = np.asarray(
        Image.open(tmp_path / "alpha/rooms/0/plus_Y/source_rgba.png").convert("RGBA")
    )
    assert pix[0, 0].tolist() == pix[0, 1].tolist() == [255, 255, 255, 51]
    assert pix[1, 2, 3] == 0
    preview = np.asarray(
        Image.open(
            tmp_path / "alpha/rooms/0/plus_Y/checkerboard_unknown_preview.png"
        ).convert("RGB")
    )
    # Alpha in front of actual valid opaque RGB must use that background.
    expected = np.rint(
        np.asarray([255, 255, 255]) * 0.2 + np.asarray([60, 70, 80]) * 0.8
    ).astype(np.uint8)
    np.testing.assert_array_equal(preview[0, 1], expected)
    assert preview[0, 0].min() > 200
    assert result["training_ready"] is False


def test_visual_mesh_must_be_exact_source_and_frame_bound_in_production(tmp_path):
    from g2.views.render_connections import render_v2
    from g2.tests.test_direct_color_views import source_case

    snapshot, manifest, data = source_case()
    src = tmp_path / "bundle"
    src.mkdir()
    forged = {
        0: {
            "source_sha256": "not-the-source",
            "scene_id": snapshot["scene_id"],
            "frame_id": snapshot["frame_id"],
            "room_uid": 0,
        }
    }
    with pytest.raises(ContractError, match="identity differ"):
        render_v2(
            src,
            manifest,
            snapshot,
            tmp_path / "bad_output",
            meters_per_pixel=0.2,
            surface_data=data,
            renderer_backend="gpu",
            visual_mesh_by_room=forged,
        )
