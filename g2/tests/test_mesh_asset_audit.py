"""Self-created MJCF/UV/state fixtures, never actual RoboCasa evidence."""
import hashlib
import subprocess
import sys

import numpy as np
import pytest

from g2.io import ContractError, canonical, digest, read_json, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.prescan import export
from g2.sim.source_geometry import load_model, model_source_hash, primitive_mesh
from g2.sim.surface_sampling import SamplingFailure, audit_surface, geometry_sha256, sample_surface


@pytest.fixture
def mesh_scene(tmp_path):
    root = tmp_path / "own_source"; root.mkdir()
    vertices, faces = primitive_mesh("box", np.asarray([.2, .3, .4]))
    faces = np.concatenate([faces[:1], [[0, 0, 1]], faces[1:], [[2, 2, 2]]])
    uv = "".join("vt %.17g .25\n" % (.25 if i % 2 else .75) for i in range(len(faces)))
    obj = "".join("v %.17g %.17g %.17g\n" % tuple(v) for v in vertices) + uv
    obj += "".join("f %d/%d %d/%d %d/%d\n" % (a + 1, i + 1, b + 1, i + 1, c + 1, i + 1)
                   for i, (a, b, c) in enumerate(faces))
    (root / "mesh.obj").write_text(obj)
    model = root / "model.xml"
    model.write_text('''<mujoco><asset><mesh name="m" file="mesh.obj"/>
      <texture name="t" type="2d" builtin="checker" rgb1="1 0 0" rgb2="0 1 0" width="2" height="2"/>
      <material name="mat" texture="t" rgba="1 1 1 1"/></asset><worldbody>
      <body name="moving"><joint type="slide" axis="1 0 0"/>
        <geom name="mesh" type="mesh" mesh="m" material="mat"/></body>
      <geom name="collision" type="box" size=".1 .1 .1"/>
      <geom name="robot" type="sphere" size=".1"/>
      <geom name="aux" type="box" size=".1 .1 .1" rgba="1 0 1 0"/>
      </worldbody></mujoco>''')
    metadata = root / "roles.json"
    roles = {"mesh": "visual", "collision": "collision", "robot": "robot", "aux": "auxiliary"}
    write_json(metadata, {"schema": "g2_sim_prescan_v1", "scene_id": "TEST_ONLY_F1B",
        "geoms": {name: {"role": role, "source_kind": "mjcf", "geom_name": name,
                          "classification_reason": "Own test fixture explicitly authored for " + role}
                  for name, role in roles.items()}})
    return root, model, metadata


def test_native_compiled_mesh_export_keeps_zero_face_ids_uv_and_source_hash(mesh_scene, tmp_path):
    _, model, metadata = mesh_scene
    compiled, sources = load_model(model)
    result = export(model, metadata, tmp_path / "export", spacing=.4)
    mesh = result["visual_geoms"][0]
    sampling = mesh["sampling"]
    # MuJoCo retains both input zero faces; IDs refer to its compiled local table.
    assert sampling["input_face_count"] == 14
    assert sampling["discarded_zero_area_face_ids"] == [1, 13]
    assert sampling["discarded_area_m2"] == 0
    assert mesh["local_geometry_sha256"] == geometry_sha256(compiled.mesh_vert, compiled.mesh_face)
    assert sampling["local_geometry_sha256"] == mesh["local_geometry_sha256"]
    assert result["source_identity"]["model_source_sha256"] == model_source_hash(sources)
    assert result["geom_audit_sha256"] == hashlib.sha256(canonical(result["geom_audit"])).hexdigest()
    cloud = np.loadtxt(tmp_path / "export/precolored.txt", skiprows=7)
    # The constant per-face UVs address exact red/green texel centers.
    assert {tuple(c) for c in cloud[:, 3:6]} == {(255, 0, 0), (0, 255, 0)}
    assert np.all(cloud[:, -1] == 1)
    assert len(cloud) == sampling["sampled_point_count"]
    assert result["completion_scope"] == "DECLARED_VISUAL_GEOMS_ONLY"
    assert result["training_ready"] is False
    assert result["gates"]["full_scene_source_certified"] is False
    assert len(result["geom_audit"]) == compiled.ngeom == 4
    assert (tmp_path / "export/COMPLETE").is_file()


def test_mesh_frame0_200_fullphysics_identity_uv_and_motion_are_preserved(mesh_scene, tmp_path):
    import mujoco
    root, model, metadata = mesh_scene
    compiled, sources = load_model(model)
    data = mujoco.MjData(compiled)
    state_kind = mujoco.mjtState.mjSTATE_FULLPHYSICS
    rows = np.zeros((201, mujoco.mj_stateSize(compiled, state_kind)))
    for frame, distance in ((0, 0.), (200, .12)):
        data.qpos[:] = distance; data.time = frame * .02
        mujoco.mj_getState(compiled, data, rows[frame], state_kind)
    states = root / "states.npz"; np.savez(states, states=rows)
    meta = read_json(metadata)
    meta["state_source"] = {"model_source_sha256": model_source_hash(sources), "states_sha256": digest(states)}
    write_json(metadata, meta)
    first = export(model, metadata, tmp_path / "f0", states=states, state_format="mujoco_fullphysics", spacing=.4)
    later = export(model, metadata, tmp_path / "f200", states=states, frame=200, state_format="mujoco_fullphysics", spacing=.4)
    assert first["source_sha256"] == later["source_sha256"]
    assert first["state"]["row_sha256"] != later["state"]["row_sha256"]
    assert later["state"]["timestamp"] == 4.
    assert first["visual_geoms"] == later["visual_geoms"]
    a = np.loadtxt(tmp_path / "f0/precolored.txt", skiprows=7)
    b = np.loadtxt(tmp_path / "f200/precolored.txt", skiprows=7)
    np.testing.assert_allclose(b[:, :3] - a[:, :3], np.tile([.12, 0, 0], (len(a), 1)), atol=1e-15)
    np.testing.assert_array_equal(a[:, 3:], b[:, 3:])
    assert first["geom_audit"][0]["body_ancestry"] == later["geom_audit"][0]["body_ancestry"]


def test_budget_failure_seals_discard_evidence_without_a_cloud(mesh_scene, tmp_path):
    _, model, metadata = mesh_scene
    out = tmp_path / "rejected"
    with pytest.raises(SamplingFailure, match="budget"):
        export(model, metadata, out, spacing=.4, max_points=10)
    failure = read_json(out / "sampling_failure.json")
    assert failure["status"] == "REJECTED"
    assert failure["sampling"]["discarded_zero_area_face_ids"] == [1, 13]
    assert failure["sampling"]["discarded_area_m2"] == 0
    assert failure["metadata_sha256"] == digest(metadata)
    assert failure["geom_name"] == "mesh" and failure["compiled_geom_count"] == 4
    assert failure["spacing_m"] == failure["sampling"]["spacing_m"] == .4
    assert failure["max_points"] == failure["sampling"]["point_budget"] == 10
    assert failure["previous_geom_point_count"] == 0
    assert failure["sampling"]["required_points_at_rejection"] > 10
    assert failure["sampling"]["rejection_face_id"] not in [1, 13]
    assert failure["cloud_written"] is failure["training_ready"] is False
    assert {path.name for path in out.iterdir()} == {"sampling_failure.json"}


def test_all_zero_rejection_carries_original_face_evidence():
    vertices = np.asarray([[0., 0., 0.], [1., 0., 0.], [2., 0., 0.]])
    faces = np.asarray([[0, 1, 2], [0, 0, 0]])
    with pytest.raises(SamplingFailure) as caught:
        sample_surface(vertices, faces, .5, 100)
    audit = caught.value.audit
    assert audit["discarded_zero_area_face_ids"] == [0, 1]
    assert audit["retained_face_count"] == audit["sampled_point_count"] == 0
    assert audit["discarded_area_fraction"] is None


def test_nonzero_near_degenerate_face_is_reported_not_discarded():
    audit = audit_surface(np.asarray([[0., 0, 0], [1., 0, 0], [0, 1e-15, 0]]), np.asarray([[0, 1, 2]]))
    assert audit["status"] == "GEOMETRY_VALID"
    assert audit["discarded_zero_area_face_ids"] == []
    assert audit["retained_near_positive_face_ids"] == [0]


def test_float32_cancellation_cannot_promote_an_exact_tiny_positive_face():
    # Independent review case: float32 rounded norm is ~7.63e-6, while the
    # represented-input rational cross is nonzero but only ~1.12e-44.
    vertices = np.asarray([[3.9999990463256836, 11.99999713897705, 0.],
                           [-3.9999961853027344, -11.999988555908203, 0.],
                           [0., np.nextafter(np.float32(0), np.float32(1)), 0.]], np.float32)
    faces = np.asarray([[0, 1, 2]])
    assert np.linalg.norm(np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])) > 1e-14
    # Preserve the historical case ID: rounded arithmetic must not relabel its
    # exact-positive geometry. F1-C now retains it rather than rejecting it.
    points, ids, _, audit = sample_surface(vertices, faces, 100., 3, with_audit=True)
    assert len(points) == 3 and set(ids) == {0}
    assert audit["discarded_zero_area_face_ids"] == []
    assert audit["retained_near_positive_face_ids"] == [0]


def test_exact_collinear_float32_face_with_rounded_nonzero_cross_is_skipped():
    vertices = np.asarray([[3.9999990463256836, 11.99999713897705, 0.],
                           [-3.9999961853027344, -11.999988555908203, 0.], [0., 0., 0.],
                           [0., 1., 0.], [1., 0., 0.]], np.float32)
    assert np.linalg.norm(np.cross(vertices[1] - vertices[0], vertices[2] - vertices[0])) > 1e-14
    points, face_ids, _, audit = sample_surface(vertices, np.asarray([[0, 1, 2], [2, 3, 4]]),
                                               100., 3, with_audit=True)
    assert audit["discarded_zero_area_face_ids"] == [0]
    assert len(points) == 3 and set(face_ids) == {1}


def test_zero_face_with_missing_uv_does_not_relax_material_validation(mesh_scene, monkeypatch, tmp_path):
    import g2.sim.prescan as prescan
    _, model, metadata = mesh_scene
    compiled, sources = load_model(model)
    # A discarded face remains subject to the existing whole-mesh UV contract.
    compiled.mesh_facetexcoord[1] = -1
    monkeypatch.setattr(prescan, "load_model", lambda *args: (compiled, sources))
    with pytest.raises(ContractError, match="unsupported texture projection"):
        export(model, metadata, tmp_path / "rejected")
    partial = export(model, metadata, tmp_path / "partial", allow_partial_color=True)
    assert partial["status"] == "PARTIAL_COLOR"
    assert partial["visual_geoms"][0]["appearance"]["reason"] == "missing mesh UV coordinates"
    assert partial["source_audit"]["color_valid_points"] == 0
    assert not (tmp_path / "partial/COMPLETE").exists()


def test_inventory_without_roles_never_guesses_or_produces_cloud(mesh_scene, tmp_path):
    _, model, _ = mesh_scene
    result = inventory(model, tmp_path / "inventory", scene_id="TEST_ONLY_F1B")
    assert result["status"] == "AUDIT_ONLY"
    assert result["summary"]["role_counts"] == {"UNCLASSIFIED": 4}
    assert result["summary"]["compiled_geom_count"] == 4
    assert len(result["summary"]["preflight_blockers"]) == 4
    assert result["training_ready"] is result["summary"]["surface_color_coverage_measured"] is False
    assert result["summary"]["discarded_zero_area_face_count"] == 2
    assert {path.name for path in (tmp_path / "inventory").iterdir()} == {"inventory.json", "roles_template.json"}
    template = read_json(tmp_path / "inventory/roles_template.json")
    assert all(spec["role"] is None for spec in template["geoms"].values())
    with pytest.raises(ContractError, match="invalid or absent geom role"):
        export(model, tmp_path / "inventory/roles_template.json", tmp_path / "unfilled")
    assert not (tmp_path / "unfilled/COMPLETE").exists()


def test_inventory_includes_explicit_roles_material_and_body_at_actual_frame(mesh_scene, tmp_path):
    root, model, metadata = mesh_scene
    compiled, sources = load_model(model)
    states = root / "states.npz"; np.savez(states, qpos=np.full((201, 1), .12), time=np.arange(201) * .02)
    meta = read_json(metadata)
    meta["state_source"] = {"model_source_sha256": model_source_hash(sources), "states_sha256": digest(states)}
    write_json(metadata, meta)
    result = inventory(model, tmp_path / "inventory", metadata=metadata, states=states, frame=200)
    rows = {row["geom_name"]: row for row in result["geom_audit"]}
    assert result["summary"]["role_counts"] == {"visual": 1, "collision": 1, "robot": 1, "auxiliary": 1}
    assert result["summary"]["preflight_blockers"] == []
    assert result["state"]["frame_id"] == 200 and result["state"]["timestamp"] == 4
    np.testing.assert_allclose(rows["mesh"]["world_position"], [.12, 0, 0], atol=1e-15)
    assert rows["mesh"]["body_ancestry"][0]["body_name"] == "moving"
    assert rows["mesh"]["sampling"]["discarded_zero_area_face_ids"] == [1, 13]
    assert rows["mesh"]["material_probe"]["status"] == "PROBE_VALID"
    assert rows["mesh"]["material"]["texture_bindings"][0]["texture_name"] == "t"
    assert rows["aux"]["effective_rgba"][3] == 0
    assert result["point_cloud_created"] is False
    assert result["summary"]["full_scene_source_certified"] is False


def test_inventory_continues_after_unsupported_surface_and_material(mesh_scene, tmp_path):
    _, model, metadata = mesh_scene
    text = model.read_text().replace('</worldbody>',
        '<geom name="plane" type="plane" size="0 0 .1"/>'
        '<geom name="textured_primitive" type="capsule" size=".1 .2" material="mat"/>'
        '<geom name="later" type="sphere" size=".1"/></worldbody>')
    model.write_text(text)
    meta = read_json(metadata)
    for name in ("plane", "textured_primitive", "later"):
        meta["geoms"][name] = {"role": "visual", "source_kind": "mjcf", "geom_name": name,
                               "classification_reason": "Explicit own fixture visual"}
    write_json(metadata, meta)
    result = inventory(model, tmp_path / "inventory", metadata=metadata)
    rows = {row["geom_name"]: row for row in result["geom_audit"]}
    assert len(rows) == 7
    assert rows["plane"]["geometry_status"] == "UNSUPPORTED_FINITE_SURFACE"
    assert rows["textured_primitive"]["material_probe"]["status"] == "UNSUPPORTED_OR_TRANSLUCENT"
    assert rows["later"]["geometry_status"] == "GEOMETRY_VALID"
    assert any(b["reason"].startswith("VISUAL_GEOMETRY_") for b in result["summary"]["preflight_blockers"])
    assert any(b["reason"].startswith("VISUAL_MATERIAL_PROBE_") for b in result["summary"]["preflight_blockers"])
    assert result["summary"]["full_scene_source_certified"] is False


@pytest.mark.parametrize("fault", ["absent", "bad_role", "wrong_name", "wrong_body", "scalar", "wrong_ep_category"])
def test_inventory_marks_bad_declarations_without_hiding_other_geoms(mesh_scene, tmp_path, fault):
    root, model, metadata = mesh_scene
    meta = read_json(metadata)
    if fault == "absent": del meta["geoms"]["mesh"]
    elif fault == "bad_role": meta["geoms"]["mesh"]["role"] = "guessed"
    elif fault == "wrong_name": meta["geoms"]["mesh"]["geom_name"] = "foreign"
    elif fault == "wrong_body": meta["geoms"]["mesh"]["source_body_name"] = "foreign"
    elif fault == "scalar": meta["geoms"]["mesh"] = "visual"
    else:
        meta["geoms"]["mesh"] = {"role": "visual", "source_kind": "ep_meta", "ep_meta_pointer": "/object_cfgs/0",
            "source_instance_name": "distr", "source_category": "wrong", "source_body_name": "moving"}
    write_json(metadata, meta)
    ep = root / "ep_meta.json"
    write_json(ep, {"object_cfgs": [{"name": "distr", "type": "object", "info": {"cat": "own_schema_category"}}]})
    result = inventory(model, tmp_path / "inventory", metadata=metadata, ep_meta=ep)
    rows = {row["geom_name"]: row for row in result["geom_audit"]}
    assert rows["mesh"]["role"] == "UNCLASSIFIED"
    assert rows["mesh"]["declaration_status"] == ("MISSING" if fault == "absent" else "INVALID")
    assert rows["collision"]["declaration_status"] == "DECLARED"
    assert len(rows) == 4
    assert result["summary"]["preflight_blockers"]


@pytest.mark.parametrize("fault", ["no_state_binding", "foreign_closure", "foreign_archive", "unknown_geom", "scene_conflict"])
def test_inventory_fails_closed_on_ambiguous_source_or_state(mesh_scene, tmp_path, fault):
    root, model, metadata = mesh_scene
    _, sources = load_model(model)
    states = root / "states.npz"; np.savez(states, qpos=np.zeros((1, 1)))
    meta = read_json(metadata)
    meta["state_source"] = {"model_source_sha256": model_source_hash(sources), "states_sha256": digest(states)}
    if fault == "no_state_binding": del meta["state_source"]
    elif fault == "foreign_closure": meta["state_source"]["model_source_sha256"] = "0" * 64
    elif fault == "foreign_archive": meta["state_source"]["states_sha256"] = "0" * 64
    elif fault == "unknown_geom": meta["geoms"]["not_compiled"] = {}
    write_json(metadata, meta)
    with pytest.raises(ContractError):
        inventory(model, tmp_path / "out", metadata=metadata, states=states,
                  scene_id="wrong" if fault == "scene_conflict" else None)
    assert not (tmp_path / "out").exists()


def test_inventory_cli_runs_as_audit_only(mesh_scene, tmp_path):
    _, model, metadata = mesh_scene
    output = tmp_path / "cli"
    result = subprocess.run([sys.executable, "-m", "g2.sim.asset_inventory", "--mjcf", str(model),
                             "--metadata", str(metadata), "--output", str(output)],
                            capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "AUDIT_ONLY 4"
    assert read_json(output / "inventory.json")["training_ready"] is False
    assert not (output / "COMPLETE").exists()
