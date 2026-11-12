"""Hand-computed color/visibility oracles for the source-independent compositor."""

import copy

import numpy as np
import pytest

from g2.io import ContractError
from g2.views.surface_composer import CompositeUnknown, compose_surface_layers


def layer(depth, rgb, alpha=1.0, *, geom=1, owner=-1, **fields):
    depth = np.asarray(depth, dtype=float)
    if depth.ndim == 0:
        depth = depth.reshape(1, 1)
    result = {
        "depth": depth,
        "rgb_linear": np.broadcast_to(np.asarray(rgb, dtype=float), (*depth.shape, 3)),
        "geometry_valid": np.ones(depth.shape, dtype=bool),
        "color_valid": True,
        "alpha": alpha,
        "alpha_valid": True,
        "geom_id": geom,
        "material_id": geom + 100,
        "semantic_owner": owner,
    }
    result.update(fields)
    return result


def test_two_layers_match_hand_computed_linear_source_over():
    # Half red, then one-quarter green of the remaining half, then blue.
    near = layer(1, [1, 0, 0], 0.5, geom=10)
    far = layer(2, [0, 1, 0], 0.25, geom=20)
    back = layer(3, [0, 0, 1], geom=30)
    result = compose_surface_layers(back, [far, near])
    np.testing.assert_allclose(result["composite_rgb_linear"], [[[0.5, 0.125, 0.375]]])
    assert result["composite_valid"].all()
    assert result["front_geom_id"].item() == 10
    assert result["front_material_id"].item() == 110
    assert result["front_owner"].item() == -1  # semantic owner is never a gate
    assert result["front_depth"].item() == 1
    assert result["opaque_geom_id"].item() == 30
    assert result["opaque_depth"].item() == 3
    assert result["alpha"].item() == 1


def test_depth_order_is_per_pixel_and_input_permutation_invariant():
    red = layer([[1, 2]], [1, 0, 0], 0.5, geom=1)
    green = layer([[2, 1]], [0, 1, 0], 0.5, geom=2)
    blue = layer([[3, 3]], [0, 0, 1], geom=3)
    first = compose_surface_layers(blue, [red, green])
    second = compose_surface_layers(blue, [green, red])
    expected = [[[0.5, 0.25, 0.25], [0.25, 0.5, 0.25]]]
    np.testing.assert_allclose(first["composite_rgb_linear"], expected)
    np.testing.assert_array_equal(first["composite_rgb_linear"], second["composite_rgb_linear"])
    np.testing.assert_array_equal(first["front_geom_id"], [[1, 2]])


def test_unknown_opaque_color_still_blocks_a_rear_colored_surface():
    back = layer(1, [np.nan] * 3, color_valid=False, geom=10)
    hidden = layer(2, [1, 0, 0], 0.9, geom=20)
    result = compose_surface_layers(back, [hidden])
    assert not result["composite_valid"].any()
    assert np.isnan(result["composite_rgb_linear"]).all()
    assert result["unknown_mask"].item() == int(CompositeUnknown.COLOR)
    assert result["front_geom_id"].item() == 10
    assert result["contributing_layer_count"].item() == 1


def test_unknown_layers_behind_opaque_do_not_poison_visible_evidence():
    back = layer(1, [0.2, 0.4, 0.6], geom=10)
    hidden = layer(2, [np.nan] * 3, np.nan, geom=20,
                   color_valid=False, alpha_valid=False)
    result = compose_surface_layers(back, [hidden])
    np.testing.assert_allclose(result["composite_rgb_linear"], [[[0.2, 0.4, 0.6]]])
    assert result["unknown_mask"].item() == 0


def test_known_zero_alpha_ignores_unknown_color_and_does_not_set_front():
    hole = layer(1, [np.nan] * 3, 0, geom=1, color_valid=False)
    back = layer(2, [0, 0, 0], geom=2)
    result = compose_surface_layers(back, [hole])
    np.testing.assert_array_equal(result["composite_rgb_linear"], [[[0, 0, 0]]])
    assert result["composite_valid"].all()
    assert result["front_geom_id"].item() == 2


def test_unknown_alpha_has_no_fabricated_rgb_or_certified_front_identity():
    uncertain = layer(1, [1, 0, 0], 0, alpha_valid=False, geom=1)
    back = layer(2, [0, 0, 1], geom=2)
    result = compose_surface_layers(back, [uncertain], background_rgb_linear=[1, 1, 1])
    assert not result["composite_valid"].any()
    assert np.isnan(result["composite_rgb_linear"]).all()
    assert not result["front_valid"].any()
    assert result["front_geom_id"].item() == 1  # explicitly an uncertified candidate
    assert result["unknown_mask"].item() == int(CompositeUnknown.ALPHA)
    assert result["alpha"].item() == 1  # opaque backing makes total coverage certain
    assert result["alpha_valid"].all()


def test_alpha_one_transparent_layer_is_also_an_opaque_barrier():
    solid = layer(1, [0.1, 0.2, 0.3], 1, geom=1)
    hidden = layer(2, [np.nan] * 3, np.nan, geom=2,
                   color_valid=False, alpha_valid=False)
    result = compose_surface_layers(None, [hidden, solid])
    assert result["composite_valid"].all()
    np.testing.assert_allclose(result["composite_rgb_linear"], [[[0.1, 0.2, 0.3]]])
    assert result["opaque_depth"].item() == 1
    assert result["opaque_geom_id"].item() == 1


def test_white_display_background_never_certifies_unobserved_background():
    glass = layer(1, [1, 0, 0], 0.5)
    result = compose_surface_layers(None, [glass], background_rgb_linear=[1, 1, 1])
    np.testing.assert_allclose(result["display_rgb_linear"], [[[1, 0.5, 0.5]]])
    assert np.isnan(result["composite_rgb_linear"]).all()
    assert not result["composite_valid"].any()
    assert result["unknown_mask"].item() == int(CompositeUnknown.BACKGROUND)
    assert result["coverage_alpha"].item() == 0.5
    assert result["front_valid"].all()


def test_unknown_alpha_retains_coverage_bounds():
    uncertain = layer(1, [1, 0, 0], np.nan, alpha_valid=False, geom=1)
    glass = layer(2, [0, 1, 0], 0.5, geom=2)
    result = compose_surface_layers(None, [uncertain, glass])
    assert result["coverage_min"].item() == 0.5
    assert result["coverage_max"].item() == 1.0
    assert np.isnan(result["alpha"]).all()
    assert not result["alpha_valid"].any()


def test_transmission_underflow_cannot_create_a_certified_opaque_surface():
    almost_opaque = [
        layer(index, [1, 0, 0], 1 - 2.0 ** -52, geom=index)
        for index in range(1, 23)
    ]
    uncertain = layer(30, [0, 0, 1], np.nan, geom=30, alpha_valid=False)
    result = compose_surface_layers(None, [*almost_opaque, uncertain])
    assert not result["composite_valid"].any()
    assert not result["alpha_valid"].any()
    assert result["unknown_mask"].item() & int(CompositeUnknown.ALPHA)
    assert result["unknown_mask"].item() & int(CompositeUnknown.BACKGROUND)
    assert np.isinf(result["opaque_depth"]).all()


def test_empty_projection_preserves_white_display_and_invalid_training():
    empty = layer([[np.inf, np.inf]], [np.nan] * 3,
                  geometry_valid=False, color_valid=False, geom=-1)
    result = compose_surface_layers(empty, [], background_rgb_linear=[1, 1, 1])
    np.testing.assert_array_equal(result["display_rgb_linear"], np.ones((1, 2, 3)))
    assert not result["composite_valid"].any()
    assert not result["geometry_valid"].any()
    assert (result["front_geom_id"] == -1).all()
    assert np.isinf(result["front_depth"]).all()
    assert (result["alpha"] == 0).all()
    assert (result["unknown_mask"] == int(
        CompositeUnknown.NO_SURFACE | CompositeUnknown.BACKGROUND
    )).all()


def test_no_layers_use_spatial_background_only_for_image_dimensions():
    result = compose_surface_layers(None, [], background_rgb_linear=np.ones((2, 3, 3)))
    assert result["composite_valid"].shape == (2, 3)
    assert not result["composite_valid"].any()
    np.testing.assert_array_equal(result["display_rgb_linear"], np.ones((2, 3, 3)))
    with pytest.raises(ContractError, match="specify size"):
        compose_surface_layers(None, [])


def test_duplicate_surface_with_exact_identity_and_depth_is_composed_once():
    glass = layer(1, [1, 0, 0], 0.5, surface_id="face-7")
    back = layer(2, [0, 0, 1], geom=2)
    result = compose_surface_layers(back, [glass, copy.deepcopy(glass)])
    np.testing.assert_allclose(result["composite_rgb_linear"], [[[0.5, 0, 0.5]]])
    assert result["deduplicated_layer_count"].item() == 1
    assert result["contributing_layer_count"].item() == 2


def test_missing_surface_identity_never_deduplicates_equal_depth_samples():
    glass = layer(1, [1, 0, 0], 0.5)
    result = compose_surface_layers(None, [glass, copy.deepcopy(glass)])
    assert result["deduplicated_layer_count"].item() == 0
    assert result["contributing_layer_count"].item() == 2
    assert result["coverage_alpha"].item() == 0.75
    assert result["unknown_mask"].item() & int(CompositeUnknown.DEPTH_TIE)


def test_same_surface_at_distinct_depths_is_not_deduplicated():
    front = layer(1, [1, 0, 0], 0.5, surface_id=4)
    rear = layer(2, [1, 0, 0], 0.5, surface_id=4)
    back = layer(3, [0, 0, 1], geom=2)
    result = compose_surface_layers(back, [front, rear])
    np.testing.assert_allclose(result["composite_rgb_linear"], [[[0.75, 0, 0.25]]])
    assert result["deduplicated_layer_count"].item() == 0


@pytest.mark.parametrize("change", [
    {"alpha": 0.75}, {"rgb_linear": [0, 1, 0]}, {"geom_id": 9},
    {"material_id": 9}, {"semantic_owner": 9}, {"color_valid": False},
])
def test_conflicting_duplicate_evidence_fails_closed(change):
    first = layer(1, [1, 0, 0], 0.5, surface_id="face")
    second = dict(first, **change)
    with pytest.raises(ContractError, match="conflicting evidence"):
        compose_surface_layers(None, [first, second])


def test_per_pixel_surface_ids_only_remove_the_verified_duplicate_pixel():
    first = layer([[1, 1]], [1, 0, 0], 0.5, surface_id=np.array([[7, 8]]))
    second = layer([[1, 2]], [1, 0, 0], 0.5, surface_id=np.array([[7, 8]]))
    back = layer([[3, 3]], [0, 0, 1], geom=2)
    result = compose_surface_layers(back, [first, second])
    np.testing.assert_allclose(result["composite_rgb_linear"], [[[0.5, 0, 0.5], [0.75, 0, 0.25]]])
    np.testing.assert_array_equal(result["deduplicated_layer_count"], [[1, 0]])


def test_valid_black_is_a_valid_color():
    result = compose_surface_layers(layer(1, [0, 0, 0]), [])
    assert result["composite_valid"].all()
    np.testing.assert_array_equal(result["composite_rgb_linear"], [[[0, 0, 0]]])


def test_distinct_equal_depth_surfaces_have_no_certified_order():
    red = layer(1, [1, 0, 0], 0.5, surface_id="red")
    blue = layer(1, [0, 0, 1], geom=2, surface_id="blue")
    result = compose_surface_layers(blue, [red])
    assert not result["composite_valid"].any()
    assert not result["front_valid"].any()
    assert result["unknown_mask"].item() == int(CompositeUnknown.DEPTH_TIE)


@pytest.mark.parametrize("change", [{"alpha": 0.5}, {"alpha_valid": False}])
def test_declared_opaque_input_must_have_certified_full_opacity(change):
    with pytest.raises(ContractError, match="opaque geometry"):
        compose_surface_layers(layer(1, [1, 1, 1], **change), [])


@pytest.mark.parametrize("change, reason", [
    ({"alpha": 1.1}, "valid alpha"),
    ({"alpha": np.nan}, "valid alpha"),
    ({"geom_id": -1}, "independent geom_id"),
    ({"geom_id": 1.5}, "integer IDs"),
    ({"depth": np.array([[np.nan]])}, "finite depth"),
    ({"rgb_linear": [np.nan, 0, 0]}, "valid linear RGB"),
    ({"color_valid": 2}, "boolean values"),
])
def test_malformed_certified_evidence_fails_closed(change, reason):
    malformed = dict(layer(1, [1, 0, 0], 0.5), **change)
    with pytest.raises(ContractError, match=reason):
        compose_surface_layers(None, [malformed])


def test_composition_does_not_mutate_caller_masks_or_colors():
    glass = layer(1, [1, 0, 0], 0.5, surface_id="same")
    duplicate = copy.deepcopy(glass)
    originals = copy.deepcopy([glass, duplicate])
    compose_surface_layers(layer(2, [0, 0, 1], geom=2), [glass, duplicate])
    for actual, expected in zip([glass, duplicate], originals):
        for key in actual:
            np.testing.assert_array_equal(actual[key], expected[key])
