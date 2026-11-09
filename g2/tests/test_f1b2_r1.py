"""R1 own CPU sources: unsupported sRGB mesh and ignored include wrappers."""
import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError, digest, read_json, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.prescan import export
from g2.sim.source_geometry import load_model, surface_colors
from g2.tests.test_mesh_asset_audit import mesh_scene


def mesh_material(scene, colorspace):
    root, xml, metadata = scene
    Image.fromarray(np.full((8, 8, 3), 128, np.uint8)).save(root / "albedo.png")
    space = '' if colorspace == "default" else ' colorspace="' + colorspace + '"'
    xml.write_text(xml.read_text().replace(
        'type="2d" builtin="checker" rgb1="1 0 0" rgb2="0 1 0" width="2" height="2"',
        'type="2d" file="albedo.png"' + space))
    return xml, metadata


@pytest.mark.parametrize("colorspace", ["sRGB", "linear", "default"])
def test_mesh_color_space_mask_and_reason_are_conservative(mesh_scene, colorspace):
    import mujoco
    xml, _ = mesh_material(mesh_scene, colorspace)
    model, _ = load_model(xml)
    g = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "mesh")
    rgba, valid, appearance, reasons = surface_colors(model, g, "mesh", np.asarray([0]),
        np.asarray([[.2, .3, .5]]), with_diagnostics=True)
    if colorspace == "sRGB":
        assert not valid[0] and reasons[0] != 0
        assert appearance["mode"] == "UNSUPPORTED_TEXTURE_PROJECTION"
        assert not appearance["texture_sampled"] and "sRGB" in appearance["reason"]
    else:
        assert valid[0] and reasons[0] == 0
        np.testing.assert_allclose(rgba[0], [128 / 255, 128 / 255, 128 / 255, 1], atol=1e-15)


@pytest.mark.parametrize("colorspace", ["sRGB", "linear", "default"])
@pytest.mark.parametrize("partial", [False, True])
def test_mesh_export_strict_partial_and_linear_contract(mesh_scene, tmp_path, colorspace, partial):
    xml, metadata = mesh_material(mesh_scene, colorspace)
    out = tmp_path / "export"
    if colorspace == "sRGB" and not partial:
        with pytest.raises(ContractError, match="partial"):
            export(xml, metadata, out, spacing=.4)
        assert not out.exists()
        return
    result = export(xml, metadata, out, spacing=.4, allow_partial_color=partial)
    points = np.loadtxt(out / "precolored.txt", skiprows=7)
    expected_valid = colorspace != "sRGB"
    assert np.all(points[:, -1] == int(expected_valid))
    assert result["status"] == ("COMPLETE" if expected_valid else "PARTIAL_COLOR")
    assert (out / "COMPLETE").exists() == expected_valid
    coverage = result["visual_geoms"][0]["color_coverage"]
    assert coverage["color_valid_points"] == (len(points) if expected_valid else 0)
    assert coverage["color_invalid_points"] == (0 if expected_valid else len(points))
    if expected_valid:
        np.testing.assert_array_equal(points[:, 3:6], np.full((len(points), 3), 128))
    else:
        assert "sRGB" in result["visual_geoms"][0]["appearance"]["reason"]
    with np.load(out / "color_audit.npz", allow_pickle=False) as proof:
        assert set(proof["local_face_id"]) == set(range(14)) - {1, 13}
        np.testing.assert_array_equal(proof["reason_code"] == 0, points[:, -1] == 1)
    assert result["completion_scope"] == "DECLARED_VISUAL_GEOMS_ONLY"
    assert result["training_ready"] is False and result["gates"]["full_scene_source_certified"] is False


def included_scene(root, wrapper, *, nested=False):
    root.mkdir()
    attrs = ' name="ignored_wrapper"' if wrapper == "body" else ' class="ignored_wrapper"' if wrapper == "default" else ''
    fragment = root / "part.inc"
    if nested:
        (root / "inner.mjcf").write_text('<asset><geom name="visible" type="box" size=".2 .3 .4"/></asset>')
        children = '<body name="inner_body"><include file="inner.mjcf"/></body>'
    else:
        children = '<geom name="visible" type="box" size=".2 .3 .4"/><geom name="collision" type="sphere" size=".1"/>'
    fragment.write_text('<' + wrapper + attrs + '>' + children + '</' + wrapper + '>')
    xml = root / "model.xml"
    xml.write_text('<mujoco><worldbody><body name="fixture_body"><include file="part.inc"/></body></worldbody></mujoco>')
    metadata = root / "roles.json"
    declared = (("visible", "visual"),) if nested else (("visible", "visual"), ("collision", "collision"))
    geoms = {name: {"role": role, "source_kind": "mjcf", "geom_name": name,
        "source_body_name": "inner_body" if nested else "fixture_body",
        "classification_reason": "Own explicitly authored test " + role} for name, role in declared}
    write_json(metadata, {"schema": "g2_sim_prescan_v1", "scene_id": "TEST_ONLY_R1_WRAPPER", "geoms": geoms})
    return xml, metadata, fragment


@pytest.mark.parametrize("wrapper", ["mujocoinclude", "body", "default", "asset"])
def test_included_root_is_ignored_but_paths_hashes_and_parent_context_survive(tmp_path, wrapper):
    import mujoco
    xml, metadata, fragment = included_scene(tmp_path / "own_source", wrapper)
    model, _ = load_model(xml)
    assert model.nbody == 2 and model.ngeom == 2
    assert mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, "ignored_wrapper") == -1
    for g in range(model.ngeom):
        assert mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[g])) == "fixture_body"
    audit = inventory(xml, tmp_path / "audit", metadata=metadata)
    control_xml, control_meta, _ = included_scene(tmp_path / "control", "mujocoinclude")
    control = inventory(control_xml, tmp_path / "control_audit", metadata=control_meta)
    for row, reference in zip(audit["geom_audit"], control["geom_audit"]):
        evidence = row["role_evidence"]
        assert evidence["status"] == "SOURCE_BOUND"
        assert evidence["compiled_signature_sha256"] == reference["role_evidence"]["compiled_signature_sha256"]
        node = evidence["source_geom_nodes"][0]
        assert node["body_ancestors"] == ["fixture_body"]
        assert node["source_sha256"] == digest(fragment)
        assert node["xml_path"] == '/' + wrapper + '/geom[' + str(row["geom_id"]) + ']'
        assert node["inclusion_chain"][0]["source_sha256"] == digest(xml)
        assert node["inclusion_chain"][0]["reference"] == "part.inc"
    definitions = [entry for document in audit["source_role_documents"] for entry in document["source_defaults"]]
    assert not any(entry["attributes"].get("class") == "ignored_wrapper" for entry in definitions)
    write_json(metadata, read_json(tmp_path / "audit/roles_template.json"))
    for label, partial in (("strict", False), ("diagnostic", True)):
        result = export(xml, metadata, tmp_path / label, require_role_evidence=True, allow_unclassified=partial, spacing=.4)
        assert result["status"] == "COMPLETE" and result["unclassified_geom_count"] == 0
        assert result["training_ready"] is False and result["gates"]["full_scene_source_certified"] is False


def test_nested_wrappers_preserve_real_child_body_and_include_chain(tmp_path):
    import mujoco
    xml, metadata, _ = included_scene(tmp_path / "own_source", "body", nested=True)
    model, _ = load_model(xml)
    assert mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, int(model.geom_bodyid[0])) == "inner_body"
    result = inventory(xml, tmp_path / "audit", metadata=metadata)
    evidence = result["geom_audit"][0]["role_evidence"]
    assert evidence["status"] == "SOURCE_BOUND"
    node = evidence["source_geom_nodes"][0]
    assert node["body_ancestors"] == ["fixture_body", "inner_body"]
    assert node["xml_path"] == "/asset/geom[0]"
    assert [edge["reference"] for edge in node["inclusion_chain"]] == ["part.inc", "inner.mjcf"]
    write_json(metadata, read_json(tmp_path / "audit/roles_template.json"))
    assert export(xml, metadata, tmp_path / "export", require_role_evidence=True)["unclassified_geom_count"] == 0


def test_real_child_default_is_preserved_while_default_wrapper_is_ignored(tmp_path):
    root = tmp_path / "own_source"; root.mkdir()
    fragment = root / "defaults.inc"
    fragment.write_text('<default class="ignored_wrapper"><default><default class="actual_default">'
        '<geom type="box" size=".2 .3 .4" rgba=".1 .2 .3 1"/></default></default></default>')
    xml = root / "model.xml"
    xml.write_text('<mujoco><include file="defaults.inc"/><worldbody><body name="fixture_body">'
        '<geom name="visible" class="actual_default"/></body></worldbody></mujoco>')
    model, _ = load_model(xml)
    np.testing.assert_allclose(model.geom_size[0], [.2, .3, .4])
    result = inventory(xml, tmp_path / "audit", scene_id="TEST_ONLY_R1_DEFAULT")
    definitions = [entry["attributes"].get("class") for document in result["source_role_documents"] for entry in document["source_defaults"]]
    assert "actual_default" in definitions and "ignored_wrapper" not in definitions
    assert result["geom_audit"][0]["role_evidence"]["status"] == "SOURCE_BOUND"
