"""F27 validates an entire hit pass before using it as material evidence."""

from types import SimpleNamespace

import mujoco
import numpy as np
import pytest

from g2.views import exact_compute
from g2.views.surface_registry import compile_surface_registry
from g2.views.surface_renderer import SurfaceRenderer, cpu_mesh_layers


def readback():
    return {
        "gids": np.array([[[0, 935]], [[935, -2]]], dtype=np.int32),
        "depth": np.array([[[0.1, 0.2]], [[0.3, np.nan]]]),
        "triangle_codes": np.array([[[1, 2]], [[2, -1]]], dtype=np.int32),
        "weights": np.full((2, 1, 2, 2), 0.25),
        "status": np.array([[3, 2]], dtype=np.int32),
        "owners": np.array([0, 935], dtype=np.int32),
        "faces": np.array([9, 17], dtype=np.int32),
    }


def test_readback_preserves_zero_geom_original_face_and_miss():
    face, bary, overflow = exact_compute._decode_surface_hits(**readback())
    np.testing.assert_array_equal(face, [[[9, 17]], [[17, -1]]])
    np.testing.assert_array_equal(overflow, [[True, False]])
    np.testing.assert_array_equal(bary[1, 0, 0], [0.25, 0.25, 0.5])
    assert np.isnan(bary[1, 0, 1]).all()


@pytest.mark.parametrize(
    "field,index,value,reason",
    [
        ("status", (0, 0), 0, "incomplete"),
        ("triangle_codes", (0, 0, 0), 0, "hit/miss"),
        ("triangle_codes", (1, 0, 1), 0, "hit/miss"),
        ("gids", (0, 0, 1), 0, "Geom/face"),
        ("triangle_codes", (0, 0, 1), 3, "Geom/face"),
        ("depth", (0, 0, 0), np.nan, "non-finite"),
        ("weights", (0, 0, 0, 0), np.nan, "non-finite"),
    ],
)
def test_readback_rejects_corrupt_evidence(field, index, value, reason):
    evidence = readback()
    evidence[field][index] = value
    with pytest.raises(exact_compute.RasterHitReadbackError, match=reason):
        exact_compute._decode_surface_hits(**evidence)


def test_missing_geom_zero_recovers_registered_translucent_layer(monkeypatch):
    model = mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom size=".1" pos="10 10 10"/>'
        '<geom type="box" size=".4 .4 .25" pos=".5 .5 .5" rgba=".2 .6 .4 .5"/>'
        "</worldbody></mujoco>"
    )
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    vertices = [
        [-0.4, -0.4, 0.25],
        [0.4, -0.4, 0.25],
        [-0.4, 0.4, 0.25],
        [-0.4, -0.4, -0.25],
        [0.4, -0.4, -0.25],
        [-0.4, 0.4, -0.25],
    ]
    room = {
        "uid": 0,
        "reference_frame": {
            "origin_world": [0, 0, 0],
            "axes_world": np.eye(3).tolist(),
        },
    }
    registry = compile_surface_registry(
        model,
        data,
        [{"g": 1, "vertices": vertices, "faces": [[0, 1, 2], [3, 4, 5]]}],
        {"entities": [], "rooms": []},
    )
    args = (registry, room, {1}, [0, 0, 0], [1, 1, 1], "floor_top", 0.1)
    expected, _ = SurfaceRenderer(model, "a" * 64, {1}, backend="cpu")._layer(
        *args, cacheable=True, multiple=True
    )

    def draw_corrupted_layers(*draw_args, max_hits):
        valid, depth, gids, _, _, faces, bary, flags = cpu_mesh_layers(
            *draw_args, max_hits=max_hits
        )
        # Readback has a supposedly occupied unregistered Geom 0. In the
        # original painter this reached registry["surfaces"][0]. Keep valid
        # hits behind it so dropping only the bad record cannot pass.
        gids[0, 0, 0] = 0
        depth[0, 0, 0] = 0
        uploaded_face = np.where(valid, faces + 1, -1)
        uploaded_face[0, 0, 0] = 1
        exact_compute._decode_surface_hits(
            gids,
            depth,
            uploaded_face,
            bary[..., :2],
            flags.astype(np.int32) + 2,
            np.array([1, 1]),
            np.array([0, 1]),
        )
        pytest.fail("unregistered Geom accepted")

    monkeypatch.setattr(
        exact_compute,
        "get_engine",
        lambda: SimpleNamespace(draw_layers=draw_corrupted_layers),
    )
    renderer = SurfaceRenderer(model, "a" * 64, {1}, backend="gpu")
    actual, receipt = renderer._layer(*args, cacheable=True, multiple=True)
    assert receipt["backend"] == "cpu" and "Geom/face" in receipt["gpu_readback_error"]
    assert len(actual) == len(expected) == 2
    for actual_layer, expected_layer in zip(actual, expected, strict=True):
        for key, values in expected_layer.items():
            np.testing.assert_array_equal(actual_layer[key], values, err_msg=key)
    assert np.any(actual[0]["color_valid"])
    assert (actual[0]["geom_id"][actual[0]["geometry_valid"]] == 1).all()
    _, reused_receipt = renderer._layer(*args, cacheable=True, multiple=True)
    assert reused_receipt["static_cache_hit"]
    assert reused_receipt["gpu_readback_error"] == receipt["gpu_readback_error"]
