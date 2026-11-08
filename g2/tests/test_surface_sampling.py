"""Own geometric fixtures only; zero-area handling is not house acceptance."""
from fractions import Fraction
from types import SimpleNamespace

import numpy as np
import pytest

from g2.io import ContractError
from g2.sim.prescan import sample_surface
from g2.sim.source_geometry import surface_colors


@pytest.fixture
def mixed():
    vertices = np.asarray([[0., 0., 0.], [1., 0., 0.], [0., 1., 0.],
                           [1., 1., 0.], [2., 0., 0.]])
    # Positive triangles deliberately have original IDs 1 and 3.
    faces = np.asarray([[0, 0, 1], [0, 1, 2], [0, 1, 4], [1, 3, 2]])
    return vertices, faces


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_exact_zero_faces_produce_no_points_and_keep_original_face_ids(mixed, dtype):
    vertices, faces = mixed
    points, face_ids, weights = sample_surface(vertices.astype(dtype), faces, .8, 100)
    assert set(face_ids) == {1, 3}
    assert len(points) == 12
    np.testing.assert_allclose(points, np.einsum("bi,bij->bj", weights, vertices[faces[face_ids]]))
    np.testing.assert_array_equal(weights.sum(axis=1), np.ones(len(points)))
    # A zero-area line extends past the actual surfaces, but must never add points.
    assert points[:, 0].max() == 1


def test_zero_face_discard_statistics_retain_input_geometry(mixed):
    vertices, faces = mixed
    before = vertices.tobytes(), faces.tobytes()
    points, face_ids, _, audit = sample_surface(vertices, faces, .8, 100, with_audit=True)
    assert audit["input_face_count"] == 4
    assert audit["retained_face_count"] == 2
    assert audit["discarded_zero_area_face_ids"] == [0, 2]
    assert audit["discarded_zero_area_face_count"] == 2
    assert audit["discarded_face_fraction"] == .5
    assert audit["discarded_area_m2"] == audit["discarded_area_fraction"] == 0
    assert audit["retained_area_m2"] == 1
    assert audit["face_id_basis"] == "INPUT_LOCAL_TRIANGLE_INDEX"
    assert audit["sampled_point_count"] == len(points)
    assert set(face_ids) == {1, 3}
    assert (vertices.tobytes(), faces.tobytes()) == before


def test_uv_lookup_uses_original_face_ids_after_zero_faces(mixed):
    import mujoco
    vertices, faces = mixed
    _, face_ids, weights = sample_surface(vertices, faces, .8, 100)
    texids = np.full((1, len(mujoco.mjtTextureRole.__members__)), -1, dtype=int)
    texids[0, int(mujoco.mjtTextureRole.mjTEXROLE_RGB)] = 0
    # Constant UV for each face isolates indexing from interpolation:
    # discarded 0/2 are blue, retained 1 red and retained 3 green.
    uv = np.asarray([[.125, .5], [.375, .5], [.625, .5], [.875, .5]])
    model = SimpleNamespace(
        geom_rgba=np.asarray([[.5, .5, .5, 1.]]), geom_matid=np.asarray([0]),
        mat_rgba=np.ones((1, 4)), mat_texid=texids, mat_texuniform=np.asarray([False]),
        mat_texrepeat=np.ones((1, 2)), tex_type=np.asarray([int(mujoco.mjtTexture.mjTEXTURE_2D)]),
        geom_dataid=np.asarray([0]), mesh_faceadr=np.asarray([0]), mesh_facenum=np.asarray([4]),
        mesh_facetexcoord=np.repeat(np.arange(4)[:, None], 3, axis=1),
        mesh_texcoordadr=np.asarray([0]), mesh_texcoordnum=np.asarray([4]), mesh_texcoord=uv,
        tex_width=np.asarray([4]), tex_height=np.asarray([1]), tex_nchannel=np.asarray([3]),
        tex_adr=np.asarray([0]), tex_data=np.asarray([0, 0, 255, 255, 0, 0, 0, 0, 255, 0, 255, 0], np.uint8))
    rgba, valid, appearance = surface_colors(model, 0, "mesh", face_ids, weights)
    assert valid and appearance["texture_sampled"]
    np.testing.assert_array_equal(rgba[face_ids == 1], np.tile([1, 0, 0, 1], (6, 1)))
    np.testing.assert_array_equal(rgba[face_ids == 3], np.tile([0, 1, 0, 1], (6, 1)))


def test_nonzero_surfaces_have_same_samples_with_or_without_interleaved_zero_faces(mixed):
    vertices, faces = mixed
    points, ids, weights = sample_surface(vertices, faces, .3, 1000)
    reference_points, reference_ids, reference_weights = sample_surface(vertices, faces[[1, 3]], .3, 1000)
    np.testing.assert_array_equal(points, reference_points)
    np.testing.assert_array_equal(weights, reference_weights)
    np.testing.assert_array_equal(ids, np.asarray([1, 3])[reference_ids])


@pytest.mark.parametrize("faces", [np.asarray([[0, 0, 1]]), np.asarray([[0, 1, 2]])])
def test_all_zero_mesh_refuses_completion(faces):
    with pytest.raises(ContractError):
        sample_surface(np.asarray([[0., 0, 0], [1., 0, 0], [2., 0, 0]]), faces, .1, 100)


@pytest.mark.parametrize("height", [1e-15, 1e-100, np.nextafter(0., 1.)])
def test_positive_near_degenerate_faces_remain_rejected(height):
    with pytest.raises(ContractError):
        sample_surface(np.asarray([[0., 0, 0], [1., 0, 0], [0., height, 0]]), np.asarray([[0, 1, 2]]), .1, 100)


def test_positive_small_surface_is_not_an_area_filter():
    points, ids, _ = sample_surface(np.asarray([[0., 0, 0], [1., 0, 0], [0., 2e-14, 0]]),
                                   np.asarray([[0, 1, 2]]), 2., 3)
    assert len(points) == 3 and set(ids) == {0}


def test_rounded_cross_zero_is_not_proof_of_exact_zero():
    # Both float64 products round to the same number; their exact rational cross differs.
    a = np.nextafter(1., 2.)
    vertices = np.asarray([[0., 0., 0.], [a, 1., 0.], [1., np.nextafter(1., 0.), 0.]])
    exact_cross = Fraction(float(a)) * Fraction(float(vertices[2, 1])) - 1
    assert exact_cross != 0
    with pytest.raises(ContractError):
        sample_surface(vertices, np.asarray([[0, 1, 2]]), .1, 100)


@pytest.mark.parametrize("fault", ["negative_index", "foreign_index", "float_index", "nan", "inf", "empty", "shape"])
def test_invalid_meshes_are_contract_errors(mixed, fault):
    vertices, faces = mixed
    if fault == "negative_index": faces[1, 0] = -1
    elif fault == "foreign_index": faces[1, 0] = len(vertices)
    elif fault == "float_index": faces = faces.astype(float)
    elif fault == "nan": vertices[1, 0] = np.nan
    elif fault == "inf": vertices[1, 0] = np.inf
    elif fault == "empty": faces = faces[:0]
    else: vertices = vertices[:, :2]
    with pytest.raises(ContractError):
        sample_surface(vertices, faces, .8, 100)


@pytest.mark.parametrize("spacing", [0., -1., np.nan, np.inf])
def test_invalid_spacing_refuses_sampling(mixed, spacing):
    vertices, faces = mixed
    with pytest.raises(ContractError):
        sample_surface(vertices, faces[[1, 3]], spacing, 100)


def test_zero_faces_consume_no_point_budget(mixed):
    vertices, faces = mixed
    assert len(sample_surface(vertices, faces, .8, 12)[0]) == 12
    with pytest.raises(ContractError, match="budget"):
        sample_surface(vertices, faces, .8, 11)
