"""Own MJCF/constructor evidence ledger, never private role classification."""
import copy
import hashlib

import numpy as np
import pytest

from g2.io import ContractError, canonical, digest, read_json, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.role_review import analyze
from g2.sim.source_geometry import load_model, model_source_hash
from g2.tests.test_mesh_asset_audit import mesh_scene


@pytest.fixture
def evidence_case(mesh_scene, tmp_path):
    source, xml, metadata = mesh_scene
    original_specs = read_json(metadata)["geoms"]
    model, closure = load_model(xml)
    qpos = np.zeros((201, model.nq)); qpos[200] = .12
    states = source / "states.npz"; np.savez(states, qpos=qpos, time=np.arange(201) * .02)
    write_json(metadata, {"schema": "g2_sim_prescan_v1", "scene_id": "TEST_ONLY_ROLE_ANALYSIS",
        "geoms": {}, "state_source": {"model_source_sha256": model_source_hash(closure), "states_sha256": digest(states)}})
    paths = []
    for frame in (0, 200):
        out = tmp_path / ("inventory" + str(frame))
        inventory(xml, out, metadata=metadata, states=states, frame=frame)
        paths.append(out / "inventory.json")
    root = tmp_path / "own_generator"; root.mkdir()
    generator = root / "constructor.py"
    generator.write_text('def emit_component():\n    return {"role": "visual", "type": "mesh", "material": "mat"}\n')
    catalog = tmp_path / "catalog.json"
    write_json(catalog, {"schema": "g2_generator_role_catalog_v1", "sources": {
        "own": {"root": "own", "path": generator.name, "bytes": generator.stat().st_size,
                "sha256": digest(generator), "repository": "TEST_ONLY_OWN_GENERATOR", "commit": "TEST_ONLY"}},
        "rules": {"own_explicit_visual": {"allowed_roles": ["visual"],
            "generator_spans": [{"source_id": "own", "start_line": 1, "end_line": 2,
                                 "excerpt_sha256": digest(generator)}], "conditions": ["constructor_to_xml"]}}})
    first = read_json(paths[0]); node = first["geom_audit"][0]["role_evidence"]["source_geom_nodes"][0]
    entry = {"geom_id": 0, "role": "visual", "rule_id": "own_explicit_visual",
        "compiled_signature_sha256": first["geom_audit"][0]["role_evidence"]["compiled_signature_sha256"],
        "source_geom_node_sha256": node["source_geom_node_sha256"], "source_attributes": node["attributes"],
        "classification_reason": "Own emitted opaque mesh with original mat material, not its name/group",
        "emission_trace": "Own constructor emits this original mesh under the moving body",
        "condition_evidence": {"constructor_to_xml": "Own constructor type/material correspond to the original XML node"}}
    decisions = tmp_path / "hypotheses.json"
    write_json(decisions, {"schema": "g2_role_hypotheses_v1", "entries": [entry]})
    return {"paths": paths, "catalog": catalog, "decisions": decisions, "generator": generator,
            "roots": {"own": root}, "entry": entry, "tmp": tmp_path, "xml": xml, "metadata": metadata,
            "states": states, "original_specs": original_specs}


def run(case, name="analysis", *, hypotheses=True, roots=True):
    return analyze(case["paths"], case["catalog"], case["tmp"] / name,
                   decisions=case["decisions"] if hypotheses else None,
                   generator_roots=case["roots"] if roots else None)


def test_names_groups_alpha_and_existing_roles_do_not_classify_unknowns(evidence_case):
    report = run(evidence_case, hypotheses=False)
    assert report["compiled_geom_count"] == report["remaining_unclassified_count"] == 4
    assert report["review_state_counts"] == {"UNRESOLVED": 4}
    assert report["candidate_role_counts"] == {}
    assert all(row["candidate_role"] is None for row in report["geom_analysis"])
    # Deliberately named robot/collision/aux components remain unknown too.
    assert {row["geom_name"] for row in report["geom_analysis"]} == {"mesh", "robot", "collision", "aux"}
    template = read_json(evidence_case["tmp"] / "analysis/hypotheses_template.json")
    assert len(template["entries"]) == 4 and all(row["role"] is None for row in template["entries"])


def test_source_bound_candidate_preserves_unknown_and_requires_gpt(evidence_case):
    before = {p: digest(p) for p in [*evidence_case["paths"], evidence_case["catalog"],
                                    evidence_case["decisions"], evidence_case["generator"]]}
    report = run(evidence_case)
    row = report["geom_analysis"][0]
    assert row["role"] == "UNCLASSIFIED" and row["candidate_role"] == "visual"
    assert row["review_state"] == "EVIDENCE_BOUND_CANDIDATE_PENDING_GPT"
    assert report["remaining_unclassified_count"] == 4
    assert report["candidate_role_counts"] == {"visual": 1}
    assert report["frames"] == [0, 200]
    assert report["inventory_files"][1]["state"]["timestamp"] == 4.
    assert report["training_ready"] is report["full_scene_source_certified"] is False
    assert report["role_assignments_written"] is report["point_cloud_created"] is False
    assert {p.name for p in (evidence_case["tmp"] / "analysis").iterdir()} == {"role_analysis.json", "hypotheses_template.json"}
    assert before == {p: digest(p) for p in before}


@pytest.mark.parametrize("fault", ["compiled", "node", "attributes", "unknown_rule", "wrong_role",
                                  "no_reason", "no_trace", "no_conditions", "null_conditions", "list_conditions"])
def test_bad_individual_basis_is_rejected_without_hiding_other_components(evidence_case, fault):
    entry = copy.deepcopy(evidence_case["entry"])
    if fault == "compiled": entry["compiled_signature_sha256"] = "0" * 64
    elif fault == "node": entry["source_geom_node_sha256"] = "0" * 64
    elif fault == "attributes": entry["source_attributes"]["material"] = "invented_material"
    elif fault == "unknown_rule": entry["rule_id"] = "name_or_group_guess"
    elif fault == "wrong_role": entry["role"] = "auxiliary"
    elif fault == "no_reason": entry["classification_reason"] = " "
    elif fault == "no_trace": entry.pop("emission_trace")
    elif fault == "null_conditions": entry["condition_evidence"] = None
    elif fault == "list_conditions": entry["condition_evidence"] = []
    else: entry["condition_evidence"] = {}
    write_json(evidence_case["decisions"], {"schema": "g2_role_hypotheses_v1", "entries": [entry]})
    report = run(evidence_case)
    assert report["review_state_counts"] == {"EVIDENCE_REJECTED": 1, "UNRESOLVED": 3}
    assert report["remaining_unclassified_count"] == 4
    assert report["geom_analysis"][0]["candidate_role"] is None
    assert report["geom_analysis"][0]["reason"]


@pytest.mark.parametrize("fault", ["modified_code", "missing_root", "bad_excerpt", "escape", "missing_code"])
def test_generator_version_and_original_file_evidence_are_required(evidence_case, fault):
    if fault == "modified_code": evidence_case["generator"].write_text("# changed original generation rule\n")
    elif fault == "missing_code": evidence_case["generator"].unlink()
    elif fault in ("bad_excerpt", "escape"):
        catalog = read_json(evidence_case["catalog"])
        if fault == "bad_excerpt": catalog["rules"]["own_explicit_visual"]["generator_spans"][0]["excerpt_sha256"] = "0" * 64
        else: catalog["sources"]["own"]["path"] = "../constructor.py"
        write_json(evidence_case["catalog"], catalog)
    report = run(evidence_case, roots=fault != "missing_root")
    assert report["geom_analysis"][0]["review_state"] == "EVIDENCE_REJECTED"
    assert report["candidate_role_counts"] == {}
    assert report["remaining_unclassified_count"] == 4


@pytest.mark.parametrize("fault", ["string_roles", "null_rule", "string_spans", "null_source"])
def test_malformed_catalog_entry_rejects_only_its_candidate(evidence_case, fault):
    catalog = read_json(evidence_case["catalog"])
    if fault == "string_roles": catalog["rules"]["own_explicit_visual"]["allowed_roles"] = "visual"
    elif fault == "null_rule": catalog["rules"]["own_explicit_visual"] = None
    elif fault == "string_spans": catalog["rules"]["own_explicit_visual"]["generator_spans"] = "own"
    else: catalog["sources"]["own"] = None
    write_json(evidence_case["catalog"], catalog)
    result = run(evidence_case)
    assert result["review_state_counts"] == {"EVIDENCE_REJECTED": 1, "UNRESOLVED": 3}


@pytest.mark.parametrize("fault", ["audit", "signature", "source_node", "resigned_source_node", "scene", "frame",
                                  "state_frame", "state_archive", "producer", "source_kind", "include_context"])
def test_inventory_tampering_or_wrong_pair_refuses_analysis(evidence_case, fault):
    path = evidence_case["paths"][1]; inventory_value = read_json(path)
    if fault == "audit": inventory_value["geom_audit"][0]["group"] = 99
    elif fault == "signature":
        inventory_value["geom_audit"][0]["role_evidence"]["compiled_signature_sha256"] = "0" * 64
        inventory_value["geom_audit_sha256"] = hashlib.sha256(canonical(inventory_value["geom_audit"])).hexdigest()
    elif fault in ("source_node", "resigned_source_node"):
        node = inventory_value["geom_audit"][0]["role_evidence"]["source_geom_nodes"][0]
        node["attributes"]["name"] = "foreign"
        if fault == "resigned_source_node":
            node["source_geom_node_sha256"] = hashlib.sha256(canonical({k: v for k, v in node.items()
                                                                         if k != "source_geom_node_sha256"})).hexdigest()
        inventory_value["geom_audit_sha256"] = hashlib.sha256(canonical(inventory_value["geom_audit"])).hexdigest()
    elif fault == "scene": inventory_value["scene_id"] = "DIFFERENT_SCENE"
    elif fault == "frame": inventory_value["frame_id"] = 0
    elif fault == "state_frame": inventory_value["state"]["frame_id"] = 0
    elif fault == "state_archive": inventory_value["state"]["file_sha256"] = "0" * 64
    elif fault == "source_kind":
        next(source for source in inventory_value["sources"] if source["logical_id"] == "root.xml")["source_kind"] = "asset"
    elif fault == "include_context":
        next(source for source in inventory_value["sources"] if source["logical_id"] == "root.xml")["includes"] = [
            {"reference": "wrong.xml", "logical_id": "wrong.xml"}]
    else:
        inventory_value["source_identity"]["inventory_source_sha256"] = "0" * 64
        inventory_value["source_identity_sha256"] = hashlib.sha256(canonical(inventory_value["source_identity"])).hexdigest()
    write_json(path, inventory_value)
    with pytest.raises(ContractError): run(evidence_case)
    assert not (evidence_case["tmp"] / "analysis").exists()


@pytest.mark.parametrize("fault", ["duplicate", "foreign", "visible_auxiliary"])
def test_hypothesis_cannot_target_foreign_id_or_exclude_visible_surface(evidence_case, fault):
    ledger = read_json(evidence_case["decisions"])
    if fault == "duplicate": ledger["entries"].append(copy.deepcopy(ledger["entries"][0]))
    elif fault == "foreign": ledger["entries"][0]["geom_id"] = 99
    else:
        catalog = read_json(evidence_case["catalog"])
        rule = catalog["rules"]["own_explicit_visual"]
        rule.update(allowed_roles=["auxiliary"], require_transparent_noncontact=True)
        ledger["entries"][0]["role"] = "auxiliary"
        write_json(evidence_case["catalog"], catalog)
    write_json(evidence_case["decisions"], ledger)
    if fault == "visible_auxiliary":
        result = run(evidence_case)
        assert result["geom_analysis"][0]["review_state"] == "EVIDENCE_REJECTED"
        assert result["remaining_unclassified_count"] == 4
    else:
        with pytest.raises(ContractError): run(evidence_case)


def test_output_cannot_write_inside_original_xml_asset_tree(evidence_case):
    first = read_json(evidence_case["paths"][0])
    original = next(source for source in first["sources"] if source["logical_id"] == "root.xml")
    from pathlib import Path
    out = Path(original["path"]).parent / "analysis"
    with pytest.raises(ContractError, match="overlaps source"):
        analyze(evidence_case["paths"], evidence_case["catalog"], out)
    assert not out.exists()


@pytest.mark.parametrize("fault", ["scene_both", "negative_frames", "boolean_state_frame", "missing_row_sha",
                                  "null_archive_binding", "null_state", "clear_unknowns", "declaration_both"])
def test_both_frames_cannot_agree_on_a_fabricated_scene_or_state(evidence_case, fault):
    for index, path in enumerate(evidence_case["paths"]):
        value = read_json(path)
        if fault == "scene_both": value["scene_id"] = "WRONG_BUT_EQUAL_SCENE"
        elif fault == "negative_frames": value["frame_id"] = value["state"]["frame_id"] = (-200, -1)[index]
        elif fault == "boolean_state_frame" and index == 0: value["state"]["frame_id"] = False
        elif fault == "missing_row_sha": value["state"].pop("row_sha256")
        elif fault == "null_archive_binding":
            value["state"]["file_sha256"] = None
            value["source_identity"]["metadata"]["state_source"]["states_sha256"] = None
            value["source_identity_sha256"] = hashlib.sha256(canonical(value["source_identity"])).hexdigest()
        elif fault == "null_state": value["state"] = None
        elif fault in ("clear_unknowns", "declaration_both"):
            for row in value["geom_audit"]:
                if fault == "clear_unknowns": row["role"] = "visual"
                else: row["declaration_status"] = "DECLARED"
            value["geom_audit_sha256"] = hashlib.sha256(canonical(value["geom_audit"])).hexdigest()
        write_json(path, value)
    with pytest.raises(ContractError): run(evidence_case)
    assert not (evidence_case["tmp"] / "analysis").exists()


def test_original_explicit_role_declarations_remain_unreviewed(evidence_case):
    metadata = read_json(evidence_case["metadata"])
    metadata["geoms"] = evidence_case["original_specs"]
    write_json(evidence_case["metadata"], metadata)
    paths = []
    for frame in (0, 200):
        out = evidence_case["tmp"] / ("declared" + str(frame))
        inventory(evidence_case["xml"], out, metadata=evidence_case["metadata"], states=evidence_case["states"], frame=frame)
        paths.append(out / "inventory.json")
    result = analyze(paths, evidence_case["catalog"], evidence_case["tmp"] / "declared_analysis")
    assert result["remaining_unclassified_count"] == 0
    assert result["review_state_counts"] == {"DECLARED_NOT_RE_REVIEWED": 4}
    assert {row["role"] for row in result["geom_analysis"]} == {"visual", "collision", "robot", "auxiliary"}
    assert result["generator_semantics_independently_reviewed"] is False
    assert result["full_scene_source_certified"] is False
