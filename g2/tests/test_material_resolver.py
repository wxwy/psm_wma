"""Independent small source/transfer cases, not scene-specific color fixtures."""

import mujoco
import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError
from g2.sim.material_resolver import MaterialResolver
from g2.sim.source_geometry import surface_colors


def _model(*, colorspace="linear", kind="box", alpha=1.0, second_geom=False):
    mesh = ('<mesh name="shape" vertex="0 0 0  1 0 0  0 1 0  0 0 1" '
            'face="0 2 1  0 1 3  0 3 2  1 2 3" '
            'texcoord=".5 .5  .5 .5  .5 .5  .5 .5"/>') if kind == "mesh" else ""
    shape = 'type="mesh" mesh="shape"' if kind == "mesh" else f'type="{kind}" size=".2 .3 .4"'
    extra = ('<geom type="box" size=".1 .1 .1" material="m" '
             'rgba=".2 .4 .8 .25"/>') if second_geom else ""
    result = mujoco.MjModel.from_xml_string(
        '<mujoco><asset><texture name="t" type="2d" builtin="checker" '
        f'width="2" height="2" rgb1="0 0 0" rgb2="1 1 1" colorspace="{colorspace}"/>'
        f'<material name="m" texture="t" rgba="1 1 1 {alpha}"/>{mesh}</asset>'
        f'<worldbody><geom {shape} material="m"/>{extra}</worldbody></mujoco>'
    )
    # A vertical two-texel stripe makes its midpoint exactly half black/white,
    # independently of image-row convention or primitive face orientation.
    result.tex_data[:] = np.tile([0, 0, 0, 255, 255, 255], 2)
    return result


def _sample(resolver, *, g=0, kind="box", points=None):
    if points is None:
        points = np.asarray([[0.0, 0.0, 0.4]])
    n = len(points)
    return resolver.sample(g, kind, np.zeros(n, np.int64),
                           np.tile([1.0, 0.0, 0.0], (n, 1)),
                           local_points=points)


@pytest.mark.parametrize("kind", ["box", "mesh"])
def test_srgb_texel_midpoint_is_linear_half_before_display_encoding(kind):
    samples = _sample(MaterialResolver(_model(colorspace="sRGB", kind=kind)), kind=kind)
    np.testing.assert_allclose(samples.rgb_linear[0], [0.5, 0.5, 0.5], atol=1e-12)
    # IEC output of linear half, not an encoded-byte average of 0.5.
    np.testing.assert_allclose(samples.rgb_compat[0], [0.7353569830524495] * 3, atol=1e-12)
    assert samples.color_valid.tolist() == [True]
    assert samples.alpha_mode.tolist() == ["OPAQUE"]


def test_known_black_and_unknown_texture_have_distinct_validity():
    plain = mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom type="box" size="1 1 1" rgba="0 0 0 1"/></worldbody></mujoco>'
    )
    known = _sample(MaterialResolver(plain))
    unknown = _sample(MaterialResolver(_model(kind="capsule")), kind="capsule")
    np.testing.assert_array_equal(known.rgb_linear, unknown.rgb_linear)
    assert known.color_valid.tolist() == [True]
    assert unknown.color_valid.tolist() == [False]
    assert unknown.alpha_valid.tolist() == [True]  # RGB texture has no alpha.
    assert unknown.alpha_mode.tolist() == ["OPAQUE"]


def test_transparency_is_independent_of_color_and_legacy_adapter_is_explicit():
    model = _model(colorspace="sRGB", alpha=0.25)
    result = _sample(MaterialResolver(model))
    assert result.color_valid.tolist() == result.alpha_valid.tolist() == [True]
    np.testing.assert_allclose(result.alpha, [0.25])
    assert result.alpha_mode.tolist() == ["BLEND"]
    # Legacy transport still excludes transparent samples; no implicit global
    # behavior change is needed for an existing producer of opaque F24 bytes.
    _, valid, _ = surface_colors(model, 0, "box", np.asarray([0]),
                                 np.asarray([[1.0, 0.0, 0.0]]),
                                 local_points=np.asarray([[0.0, 0.0, 0.4]]),
                                 enable_srgb_primitive=True)
    assert not valid[0]


def test_shared_material_keeps_each_geom_override_and_reuses_decoded_texture():
    model = _model(second_geom=True)
    model.tex_data[:] = 255
    resolver = MaterialResolver(model)
    first = _sample(resolver)
    override = _sample(resolver, g=1)
    np.testing.assert_allclose(first.rgb_linear, [[1, 1, 1]])
    np.testing.assert_allclose(override.rgb_linear, [[0.2, 0.4, 0.8]], atol=3e-8)
    np.testing.assert_allclose(override.alpha, [0.25])
    assert first.material_id == override.material_id
    assert resolver.texture_decode_count == 1 and resolver.texture_cache_hits == 1
    # Geom changes are not incorrectly hidden behind a material-ID cache.
    model.geom_rgba[1] = [0.1, 0.2, 0.3, 1.0]
    changed = _sample(resolver, g=1)
    np.testing.assert_allclose(changed.rgb_linear, [[0.1, 0.2, 0.3]], atol=3e-8)


def test_linear_source_and_legacy_display_appearance_are_not_conflated():
    model = _model(colorspace="linear")
    samples = _sample(MaterialResolver(model))
    np.testing.assert_allclose(samples.rgb_linear, [[0.5] * 3], atol=1e-12)
    # The legacy display byte convention stores this 0.5 directly. Its decoded
    # display-space value is different from true source albedo and labeled so.
    np.testing.assert_allclose(samples.rgb_compat, [[0.5] * 3], atol=1e-12)
    np.testing.assert_allclose(samples.appearance_linear, [[0.21404114048223255] * 3], atol=1e-12)
    assert samples.evidence["compatibility_is_physical_color"] is False


def test_texture_revision_can_explicitly_invalidate_cached_decode():
    model = _model(colorspace="sRGB")
    resolver = MaterialResolver(model)
    _sample(resolver)
    model.tex_data[:] = 255
    resolver.invalidate(0)
    samples = _sample(resolver)
    np.testing.assert_array_equal(samples.rgb_linear, [[1, 1, 1]])
    assert resolver.texture_decode_count == 2


def test_srgb_cube_decodes_face_texels_instead_of_claiming_raw_bytes_linear():
    model = mujoco.MjModel.from_xml_string(
        '<mujoco><asset><texture name="t" type="cube" builtin="flat" '
        'width="2" height="2" rgb1="1 1 1" colorspace="sRGB"/>'
        '<material name="m" texture="t" rgba="1 1 1 1"/></asset>'
        '<worldbody><geom type="box" size=".2 .3 .4" material="m"/></worldbody></mujoco>'
    )
    pixels = model.tex_data.reshape(6, 2, 2, 3)
    pixels[:] = 255
    pixels[0] = 128  # +X; other faces remain white, avoiding uniform fast path.
    samples = _sample(MaterialResolver(model), points=np.asarray([[0.2, 0.0, 0.0]]))
    np.testing.assert_allclose(samples.rgb_linear, [[0.21586050011389926] * 3], atol=1e-12)
    np.testing.assert_allclose(samples.rgb_compat, [[128.0 / 255.0] * 3], atol=1e-12)
    assert samples.color_valid.tolist() == [True]


def test_uniform_texture_is_uv_independent_without_object_name_exception():
    model = _model(colorspace="sRGB", kind="mesh", alpha=0.2)
    model.tex_data[:] = 255
    model.mesh_facetexcoord[:] = -1
    result = _sample(MaterialResolver(model), kind="mesh")
    assert result.color_valid.tolist() == result.alpha_valid.tolist() == [True]
    assert result.evidence["mode"] == "UNIFORM_TEXTURE_SOURCE_ALBEDO"
    assert result.alpha_mode.tolist() == ["BLEND"]


def test_rgba_alpha_is_filtered_linearly_without_srgb_transfer(tmp_path):
    image = np.asarray([[[0, 0, 0, 0], [255, 255, 255, 128]]], np.uint8)
    Image.fromarray(image).save(tmp_path / "rgba.png")
    model = mujoco.MjModel.from_xml_string(
        '<mujoco><asset><texture name="t" type="2d" file="rgba.png" '
        'nchannel="4" colorspace="sRGB"/><material name="m" texture="t" rgba="1 1 1 .5"/>'
        '</asset><worldbody><geom type="box" size=".2 .3 .4" material="m"/></worldbody></mujoco>',
        assets={"rgba.png": (tmp_path / "rgba.png").read_bytes()},
    )
    result = _sample(MaterialResolver(model))
    np.testing.assert_allclose(result.rgb_linear, [[0.5] * 3], atol=1e-12)
    np.testing.assert_allclose(result.alpha, [32.0 / 255.0], atol=1e-12)
    assert result.color_valid.tolist() == result.alpha_valid.tolist() == [True]


def test_invalid_surface_barycentric_data_is_rejected():
    resolver = MaterialResolver(_model())
    with pytest.raises(ContractError, match="coordinates"):
        resolver.sample(0, "box", np.asarray([0]), np.asarray([[1.0, 1.0, 1.0]]))


def test_descriptor_never_promotes_unknown_opacity_to_opaque():
    model = _model()
    opacity = int(mujoco.mjtTextureRole.mjTEXROLE_OPACITY)
    model.mat_texid[0, opacity] = 0
    resolver = MaterialResolver(model)
    descriptor = resolver.descriptor(0, "box")
    assert descriptor["alpha_mode"] == "UNKNOWN"
    assert not descriptor["guaranteed_opaque"] and not descriptor["alpha_valid"]
    samples = _sample(resolver)
    assert samples.color_valid.tolist() == [True]
    assert samples.alpha_valid.tolist() == [False]
    assert samples.alpha_mode.tolist() == ["UNKNOWN"]


def test_descriptor_preserves_missing_color_occlusion_and_known_alpha():
    resolver = MaterialResolver(_model(kind="capsule"))
    assert resolver.is_guaranteed_opaque(0)
    samples = _sample(resolver, kind="capsule")
    assert samples.color_valid.tolist() == [False]
    assert samples.alpha_valid.tolist() == [True]
    assert samples.alpha_mode.tolist() == ["OPAQUE"]
