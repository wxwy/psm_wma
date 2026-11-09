"""F1-C represented-input geometry fixtures; no private scene acceptance."""
from fractions import Fraction

import numpy as np
import pytest

from g2.io import ContractError, digest, read_json, write_json
from g2.sim.color_evidence import verify_color_evidence
from g2.sim.prescan import export
from g2.sim.source_geometry import load_model, model_source_hash
from g2.sim.surface_coverage import color_coverage
from g2.sim.surface_sampling import SamplingFailure, geometry_sha256, sample_surface
from g2.sim.texture_projection import REASONS
from g2.tests.test_mesh_asset_audit import mesh_scene


@pytest.mark.parametrize("scale", [1e-8, 1e-100, 1e-200, np.nextafter(0., 1.)])
def test_pure_micropositive_mesh_is_sampled_by_default(scale):
    vertices = np.asarray([[0., 0., 0.], [scale, 0., 0.], [0., scale, 0.]])
    faces = np.asarray([[0, 1, 2]])
    assert Fraction(float(scale)) ** 2 > 0
    original = vertices.tobytes(), faces.tobytes()
    points, ids, bary, audit = sample_surface(vertices, faces, 1., 3, with_audit=True)
    assert len(points) == 3 and ids.tolist() == [0, 0, 0]
    np.testing.assert_array_equal(bary.sum(axis=1), np.ones(3))
    assert audit["retained_near_positive_face_ids"] == [0]
    assert audit["discarded_zero_area_face_ids"] == []
    assert audit["retained_face_count"] == 1
    assert audit["policy"] == "EXACT_ZERO_ONLY_RETAIN_ALL_POSITIVE"
    assert "positive_face_cross_norm_min_exclusive" not in audit
    assert "rejected_nonzero_near_degenerate_face_ids" not in audit
    assert audit["local_geometry_sha256"] == geometry_sha256(vertices, faces)
    assert original == (vertices.tobytes(), faces.tobytes())


def test_long_thin_positive_face_obeys_edge_spacing_and_exact_budget():
    vertices = np.asarray([[0., 0., 0.], [10., 0., 0.], [0., 1e-100, 0.]])
    faces = np.asarray([[0, 1, 2]])
    # Longest edge / spacing = 10, hence 66 points regardless of area.
    points, ids, _ = sample_surface(vertices, faces, 1., 66)
    assert len(points) == 66 and set(ids) == {0}
    with pytest.raises(SamplingFailure, match="budget") as caught:
        sample_surface(vertices, faces, 1., 65)
    assert caught.value.audit["required_points_at_rejection"] == 66
    assert caught.value.audit["rejection_face_id"] == 0


@pytest.mark.parametrize("dtype,scale", [(np.float32, 1e-30), (np.float64, 1e-200)])
def test_underflowed_squared_edge_does_not_bypass_subdivision_budget(dtype, scale):
    vertices = np.asarray([[0., 0., 0.], [scale, 0., 0.], [0., scale, 0.]], dtype)
    with pytest.raises(SamplingFailure, match="budget") as caught:
        sample_surface(vertices, np.asarray([[0, 1, 2]]), scale / 10, 3)
    assert caught.value.audit["required_points_at_rejection"] > 3


@pytest.mark.parametrize("dtype,scale,spacing", [(np.float32, 4.1e-23, 5.5e-23),
                                               (np.float64, 2.4e-162, 3.2e-162)])
def test_nonzero_squared_edge_underflow_keeps_the_correct_budget(dtype, scale, spacing):
    vertices = np.asarray([[0., 0., 0.], [scale, 0., 0.], [0., scale, 0.]], dtype)
    assert 0 < np.linalg.norm(vertices[1] - vertices[2]) < spacing
    assert np.hypot(float(vertices[1, 0]), float(vertices[2, 1])) > spacing
    with pytest.raises(SamplingFailure, match="budget") as caught:
        sample_surface(vertices, np.asarray([[0, 1, 2]]), spacing, 3)
    assert caught.value.audit["required_points_at_rejection"] == 6


def test_zero_micropositive_and_normal_faces_keep_original_ids_and_allocation():
    vertices = np.asarray([[0., 0., 0.], [1e-8, 0., 0.], [0., 1e-8, 0.],
                           [1., 0., 0.], [0., 1., 0.]])
    faces = np.asarray([[0, 0, 1], [0, 1, 2], [1, 1, 2], [0, 3, 4]])
    points, ids, _, audit = sample_surface(vertices, faces, 2., 6, with_audit=True)
    assert ids.tolist() == [1, 1, 1, 3, 3, 3] and len(points) == 6
    assert audit["discarded_zero_area_face_ids"] == [0, 2]
    assert audit["retained_near_positive_face_ids"] == [1]
    with pytest.raises(SamplingFailure, match="budget") as caught:
        sample_surface(vertices, faces, 2., 5)
    assert caught.value.audit["rejection_face_id"] == 3
    assert caught.value.audit["allocated_point_count_before_rejection"] == 3


def _tiny_color_evidence(tmp_path):
    vertices = np.asarray([[0., 0., 0.], [1e-200, 0., 0.], [0., 1e-200, 0.]])
    faces = np.asarray([[0, 1, 2]])
    points, ids, _, sampling = sample_surface(vertices, faces, 1., 3, with_audit=True)
    valid = np.asarray([True, False, True]); codes = np.asarray([0, 1, 0], np.uint8)
    weights, coverage = color_coverage(vertices, faces, ids, valid, codes)
    cloud = tmp_path / "precolored.txt"
    cloud.write_text("own fixture\n" * 7 + "".join("%.17g %.17g %.17g 128 128 128 %d\n" % (*p, int(v))
                                                        for p, v in zip(points, valid)))
    proof = tmp_path / "color_audit.npz"
    np.savez_compressed(proof, geom_id=np.zeros(3, np.int32), local_face_id=ids,
                        reason_code=codes, input_triangle_area_weight_m2=weights)
    manifest = {"point_count": 3,
        "source_identity": {"color_evidence_protocol": "g2_sample_color_audit_v2"},
        "color_reason_codes": {str(k): v for k, v in REASONS.items()},
        "geom_audit": [{"geom_id": 0, "surface_points": 3, "sampling": sampling, "color_coverage": coverage}],
        "color_audit_file": {"path": proof.name, "sha256": digest(proof), "bytes": proof.stat().st_size}}
    return cloud, manifest, coverage, sampling


def test_positive_area_weight_underflow_is_explicit_and_disk_verifiable(tmp_path):
    cloud, manifest, coverage, sampling = _tiny_color_evidence(tmp_path)
    assert sampling["retained_area_underflow_face_ids"] == [0]
    assert sampling["discarded_zero_area_face_ids"] == []
    assert coverage["retained_input_face_count"] == coverage["evaluated_retained_face_count"] == 1
    assert coverage["area_weight_underflow_face_ids"] == [0]
    assert coverage["area_weight_underflow_point_count"] == 3
    assert coverage["area_weighted_valid_sample_fraction"] is None
    assert coverage["sampled_input_triangle_area_m2"] == 0.  # float64 approximation, not exact area
    assert coverage["color_valid_fraction"] == 2 / 3
    assert verify_color_evidence(tmp_path, manifest, cloud) == manifest["color_audit_file"]["sha256"]


@pytest.mark.parametrize("fault", ["legacy_protocol", "missing_annotation", "wrong_face", "wrong_count", "negative_weight"])
def test_zero_or_negative_area_weights_cannot_silently_pass(tmp_path, fault):
    cloud, manifest, coverage, _ = _tiny_color_evidence(tmp_path)
    if fault == "legacy_protocol":
        manifest["source_identity"]["color_evidence_protocol"] = "g2_sample_color_audit_v1"
    elif fault == "missing_annotation":
        coverage.pop("area_weight_underflow_face_ids")
    elif fault == "wrong_face":
        coverage["area_weight_underflow_face_ids"] = [1]
    elif fault == "wrong_count":
        coverage["area_weight_underflow_point_count"] = 0
    else:
        proof = tmp_path / "color_audit.npz"
        with np.load(proof, allow_pickle=False) as archive:
            values = {key: archive[key] for key in archive.files}
        values["input_triangle_area_weight_m2"][0] = -1.
        np.savez_compressed(proof, **values)
        manifest["color_audit_file"].update(sha256=digest(proof), bytes=proof.stat().st_size)
    with pytest.raises(ContractError):
        verify_color_evidence(tmp_path, manifest, cloud)


def test_compiled_micropositive_face_keeps_uv_hash_and_dynamic_identity(mesh_scene, tmp_path):
    import mujoco
    root, xml, metadata = mesh_scene
    obj = root / "mesh.obj"
    # IDs14/15 are respectively a positive microface and exact zero; original
    # UV slot15 addresses the same green texel as the original odd UV slots.
    obj.write_text(obj.read_text() + "v 0 0 0\nv 1e-8 0 0\nv 0 1e-8 0\n"
        "vt .25 .25\nvt .75 .25\nf 9/15 10/15 11/15\nf 9/16 9/16 10/16\n")
    model, sources = load_model(xml)
    data = mujoco.MjData(model); state_kind = mujoco.mjtState.mjSTATE_FULLPHYSICS
    states = np.zeros((201, mujoco.mj_stateSize(model, state_kind)))
    for frame, distance in ((0, 0.), (200, .12)):
        data.qpos[:] = distance; data.time = frame * .02
        mujoco.mj_getState(model, data, states[frame], state_kind)
    archive = root / "states.npz"; np.savez(archive, states=states)
    meta = read_json(metadata)
    meta["state_source"] = {"model_source_sha256": model_source_hash(sources), "states_sha256": digest(archive)}
    write_json(metadata, meta)
    outputs = []
    for frame in (0, 200):
        out = tmp_path / ("frame" + str(frame))
        export(xml, metadata, out, states=archive, frame=frame,
               state_format="mujoco_fullphysics", spacing=.4)
        manifest = read_json(out / "manifest.json")
        row = manifest["visual_geoms"][0]; sampling = row["sampling"]
        assert sampling["retained_near_positive_face_ids"] == [14]
        assert sampling["discarded_zero_area_face_ids"] == [1, 13, 15]
        assert sampling["local_geometry_sha256"] == geometry_sha256(model.mesh_vert, model.mesh_face)
        cloud = np.loadtxt(out / "precolored.txt", skiprows=7)
        with np.load(out / "color_audit.npz", allow_pickle=False) as evidence:
            ids = evidence["local_face_id"]; selected = ids == 14
            assert selected.sum() == 3 and not np.isin(ids, [1, 13, 15]).any()
            np.testing.assert_array_equal(cloud[selected, 3:6], np.tile([0, 255, 0], (3, 1)))
            assert np.all(evidence["reason_code"][selected] == 0)
        assert verify_color_evidence(out, manifest, out / "precolored.txt")
        assert manifest["training_ready"] is False
        assert manifest["completion_scope"] == "DECLARED_VISUAL_GEOMS_ONLY"
        outputs.append((manifest, cloud))
    first, later = outputs
    assert first[0]["source_sha256"] == later[0]["source_sha256"]
    assert first[0]["state"]["row_sha256"] != later[0]["state"]["row_sha256"]
    assert first[0]["geom_audit"][0]["body_ancestry"] == later[0]["geom_audit"][0]["body_ancestry"]
    np.testing.assert_allclose(later[1][:, :3] - first[1][:, :3],
                               np.tile([.12, 0., 0.], (len(first[1]), 1)), atol=1e-15)
    np.testing.assert_array_equal(first[1][:, 3:], later[1][:, 3:])
