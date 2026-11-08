"""Self-authored material fixtures, not RoboCasa/house acceptance."""
import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError, write_json
from g2.sim.prescan import export
from g2.sim.source_geometry import load_model, surface_colors


@pytest.fixture
def textured(tmp_path):
    root = tmp_path / "own_materials"; root.mkdir()
    pixels = np.asarray([[[20 + x * 50, 30 + y * 50, 10 + (x + y) * 25]
                          for x in range(4)] for y in range(4)], np.uint8)
    Image.fromarray(pixels).save(root / "grid.png")
    face_colors = np.asarray([[240, 20, 30], [20, 230, 40], [30, 40, 220],
                              [210, 200, 30], [200, 40, 190], [30, 180, 170]], np.uint8)
    cube = np.concatenate([np.tile(c[None, None], (4, 4, 1)) for c in face_colors])
    Image.fromarray(cube).save(root / "cube.png")

    def make(*, kind="box", size=".2 .4 .6", texture="2d", uniform=False, repeat="1 1"):
        model = root / "model.xml"
        file = 'file="grid.png"' if texture == "2d" else 'file="cube.png" gridsize="6 1" gridlayout="RLUDFB"'
        model.write_text(f'''<mujoco><asset><texture name="t" type="{texture}" {file}/>
          <material name="m" texture="t" rgba="1 1 1 1" texuniform="{str(uniform).lower()}" texrepeat="{repeat}"/>
          </asset><worldbody><geom name="g" type="{kind}" size="{size}" material="m"/>
          </worldbody></mujoco>''')
        metadata = root / "roles.json"
        write_json(metadata, {"schema": "g2_sim_prescan_v1", "scene_id": "TEST_ONLY_F1B2_TEXTURE",
            "geoms": {"g": {"role": "visual", "source_kind": "mjcf", "geom_name": "g",
                             "classification_reason": "Own authored visible material fixture"}}})
        compiled, _ = load_model(model)
        return model, metadata, compiled
    return make


@pytest.mark.parametrize("kind,size", [("box", ".2 .4 .6"), ("cylinder", ".2 .6"),
                                       ("sphere", ".2"), ("ellipsoid", ".2 .4 .6")])
def test_textured_2d_primitives_export_actual_colors(textured, tmp_path, kind, size):
    model, metadata, _ = textured(kind=kind, size=size)
    result = export(model, metadata, tmp_path / "cloud", spacing=.3)
    rows = np.loadtxt(tmp_path / "cloud/precolored.txt", skiprows=7)
    assert result["point_count"] == len(rows) and np.all(rows[:, -1] == 1)
    assert len(np.unique(rows[:, 3:6], axis=0)) > 1
    assert result["visual_geoms"][0]["appearance"]["texture_sampled"]
    assert result["training_ready"] is False


@pytest.mark.parametrize("uniform,repeat", [(False, "1 1"), (False, "2 3"), (True, "1 1"), (True, "2 3")])
def test_planar_mapping_matches_pinned_mujoco_object_planes(textured, uniform, repeat):
    _, _, compiled = textured(uniform=uniform, repeat=repeat)
    # Reference GL_OBJECT_PLANE equations from MuJoCo3.3.7 render_gl3.c146-149.
    points = np.asarray([[.1, -.2, .6], [-.1, .2, .6], [.2, .07, -.3]])
    rgba, valid, appearance = surface_colors(compiled, 0, "box", np.zeros(3, int),
        np.tile([1., 0., 0.], (3, 1)), local_points=points)
    assert np.all(valid) and appearance["texture_sampled"]
    repeat_values = np.asarray([float(v) for v in repeat.split()])
    object_xy = points[:, :2] if uniform else points[:, :2] / [.2, .4]
    uv = object_xy * [.5, -.5] * repeat_values - .5
    texture = compiled.tex_data.reshape(4, 4, 3) / 255
    # Independent scalar four-neighbor reference, including repeat boundaries.
    expected = []
    for s, t in uv:
        x, y = (s % 1) * 4 - .5, (t % 1) * 4 - .5
        left, bottom = int(np.floor(x)), int(np.floor(y)); u, v = x - np.floor(x), y - np.floor(y)
        expected.append(sum(texture[(bottom + dy) % 4, (left + dx) % 4] *
            (u if dx else 1 - u) * (v if dy else 1 - v) for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))))
    np.testing.assert_allclose(rgba[:, :3], expected, atol=2e-7)


@pytest.mark.parametrize("uniform", [False, True])
def test_cube_axis_colors_match_compiled_six_face_upload_order(textured, uniform):
    _, _, compiled = textured(texture="cube", uniform=uniform)
    points = np.asarray([[.2, 0, 0], [-.2, 0, 0], [0, .4, 0], [0, -.4, 0], [0, 0, .6], [0, 0, -.6]])
    rgba, valid, _ = surface_colors(compiled, 0, "box", np.zeros(6, int),
        np.tile([1., 0., 0.], (6, 1)), local_points=points)
    assert np.all(valid)
    faces = compiled.tex_data.reshape(6, 4, 4, 3) / 255
    np.testing.assert_allclose(rgba[:, :3], faces[:, 1, 1], atol=1e-12)


def test_cube_corner_with_different_face_colors_retains_unknown_mask(textured, tmp_path):
    model, metadata, _ = textured(texture="cube")
    with pytest.raises(ContractError, match="partial"):
        export(model, metadata, tmp_path / "refused", spacing=.5)
    result = export(model, metadata, tmp_path / "partial", spacing=.5, allow_partial_color=True)
    rows = np.loadtxt(tmp_path / "partial/precolored.txt", skiprows=7)
    assert np.any(rows[:, -1] == 1) and np.any(rows[:, -1] == 0)
    coverage = result["visual_geoms"][0]["color_coverage"]
    assert 0 < coverage["color_valid_fraction"] < 1
    assert coverage["evaluated_retained_face_fraction"] == 1
    assert coverage["continuous_surface_color_coverage_certified"] is False
    assert result["status"] == "PARTIAL_COLOR" and result["training_ready"] is False
    assert not (tmp_path / "partial/COMPLETE").exists()


def test_cube_repeat_is_not_applied_as_a_2d_uv_repeat(textured):
    _, _, a = textured(texture="cube", repeat="1 1")
    _, _, b = textured(texture="cube", repeat="7 11")
    points = np.asarray([[.2, .03, .05]])
    arguments = (0, "box", np.asarray([0]), np.asarray([[1., 0., 0.]]))
    first, valid_a, _ = surface_colors(a, *arguments, local_points=points)
    later, valid_b, _ = surface_colors(b, *arguments, local_points=points)
    assert np.all(valid_a) and np.all(valid_b)
    np.testing.assert_array_equal(first, later)


def test_color_audit_preserves_point_geom_face_and_reason(textured, tmp_path):
    model, metadata, _ = textured(texture="cube")
    result = export(model, metadata, tmp_path / "partial", spacing=.5, allow_partial_color=True)
    with np.load(tmp_path / "partial/color_audit.npz", allow_pickle=False) as audit:
        cloud = np.loadtxt(tmp_path / "partial/precolored.txt", skiprows=7)
        assert len(audit["geom_id"]) == len(cloud)
        assert set(audit["geom_id"]) == {0}
        assert set(audit["local_face_id"]) == set(range(12))
        np.testing.assert_array_equal(audit["reason_code"] == 0, cloud[:, -1] == 1)
        assert set(audit["reason_code"]) == {0, 4}
        assert np.all(audit["input_triangle_area_weight_m2"] > 0)
        assert np.isclose(audit["input_triangle_area_weight_m2"].sum(), 8 * (.2 * .4 + .4 * .6 + .2 * .6))
    assert result["color_audit_file"]["path"] == "color_audit.npz"
