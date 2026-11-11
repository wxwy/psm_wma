"""TEST_ONLY role-release contracts; fabricated approval fixture is not real review."""
import copy

import numpy as np
import pytest

from g2.io import ContractError, digest, read_json, write_json
from g2.sim.asset_inventory import inventory
from g2.sim.role_review import analyze
from g2.sim.scene_release import FILES, VERDICT, package, verify
from g2.sim import scene_release
from g2.tests.test_mesh_asset_audit import mesh_scene
from g2.tests.test_role_review import evidence_case


@pytest.fixture
def release_case(evidence_case, tmp_path, monkeypatch):
    case = evidence_case
    meta = read_json(case["metadata"])
    meta["geoms"] = {k: v for k, v in case["original_specs"].items() if k != "mesh"}
    write_json(case["metadata"], meta)
    paths = []
    for frame in (0, 200):
        root = tmp_path / ("release_inventory" + str(frame))
        inventory(case["xml"], root, metadata=case["metadata"], states=case["states"], frame=frame)
        paths.append(root / "inventory.json")
    first = read_json(paths[0])
    row = next(r for r in first["geom_audit"] if r["geom_name"] == "mesh")
    node = row["role_evidence"]["source_geom_nodes"][0]
    entry = copy.deepcopy(case["entry"])
    entry.update(geom_id=row["geom_id"], compiled_signature_sha256=row["role_evidence"]["compiled_signature_sha256"],
        source_geom_node_sha256=node["source_geom_node_sha256"], source_attributes=node["attributes"])
    decisions = tmp_path / "mesh_decisions.json"
    write_json(decisions, {"schema": "g2_role_hypotheses_v1", "entries": [entry]})
    root = tmp_path / "own_component_analysis"
    report = analyze(paths, case["catalog"], root, decisions=decisions, generator_roots=case["roots"])
    assert report["candidate_role_counts"] == {"visual": 1}
    rolemap = copy.deepcopy(meta)
    rolemap["geoms"]["mesh"] = copy.deepcopy(case["original_specs"]["mesh"])
    rolemap["geoms"]["mesh"]["classification_reason"] = "TEST_ONLY own reviewed visual mesh"
    rolemap["geoms"]["mesh"]["role_evidence"] = {
        "compiled_signature_sha256": entry["compiled_signature_sha256"],
        "source_geom_node_sha256": entry["source_geom_node_sha256"], "asserted_role": "visual"}
    roles = tmp_path / "roles.json"; write_json(roles, rolemap)
    approval = tmp_path / "TEST_ONLY_approval.json"
    write_json(approval, {"scope": "TEST_ONLY_FABRICATED_APPROVAL_NOT_GPT", "testcase": "own_mesh"})
    profile = {"layout": 1, "compiled_geom_count": 4, "classified_unknown_count": 1,
        "source_identity_sha256": first["source_identity_sha256"],
        "model_source_sha256": first["source_identity"]["model_source_sha256"],
        "frames": [{"frame_id": f, "inventory_sha256": digest(p),
            "state_archive_sha256": read_json(p)["state"]["file_sha256"],
            "state_row_sha256": read_json(p)["state"]["row_sha256"], "state_format": "qpos"}
            for f, p in zip((0, 200), paths)], "proposed_counts": {"visual": 1},
        "files": {"proposed_roles.json": digest(roles), "hypotheses.json": digest(decisions)},
        "analysis_sha256": digest(root / "role_analysis.json")}
    profiles = tmp_path / "profiles.json"
    write_json(profiles, {"schema": "g2_scene_role_profiles_v1", "version": "TEST_ONLY",
        "profiles": {"1": profile}, "classification_source": {"commit": "a" * 40, "tree": "b" * 40,
            "catalog_sha256": digest(case["catalog"])},
        "review": {"verdict": VERDICT, "commit": "c" * 40, "blob": "d" * 40,
            "file": "TEST_ONLY_review.md", "evidence_sha256": digest(approval), "issue_comment": 0},
        "historical_generator_revision_certified": False, "full_scene_source_certified": False, "training_ready": False})
    inputs = {"roles": roles, "hypotheses": decisions, "catalog": case["catalog"],
        "analysis": root / "role_analysis.json", "approval": approval, "frame0": paths[0], "frame200": paths[1]}
    production_pin = scene_release.TRUSTED_PROFILE_SHA256
    monkeypatch.setattr(scene_release, "TRUSTED_PROFILE_SHA256", digest(profiles))
    return {"profiles": profiles, "inputs": inputs, "source": case, "out": tmp_path / "release",
            "production_pin": production_pin}


def build(case):
    return package(case["profiles"], 1, case["inputs"], case["out"])


def test_exact_private_artifacts_and_pending_source_proofs_are_preserved(release_case):
    c = release_case
    before = {p: digest(p) for p in [*c["inputs"].values(), c["source"]["states"], c["source"]["xml"]]}
    result = build(c)
    assert result["classified_unknown_count"] == 1 and result["role_counts"] == {"visual": 1}
    assert all(digest(p) == h for p, h in before.items())
    assert verify(c["out"], c["profiles"]) == result
    config = read_json(c["out"] / "config.json")
    assert config["status"] == "REVIEWED_SCENE_ROLE_INPUT_FOR_INTEGRATION_ONLY"
    assert config["state_source"] == read_json(c["inputs"]["roles"])["state_source"]
    assert config["training_ready"] is config["gt_structural_labels_provided"] is False
    assert config["native_object_observations_provided"] is config["full_scene_source_certified"] is False
    for key, filename in FILES.items():
        assert (c["out"] / filename).read_bytes() == c["inputs"][key].read_bytes()
    proof = read_json(c["out"] / FILES["analysis"])
    candidates = [r for r in proof["geom_analysis"] if r["candidate_role"]]
    assert candidates[0]["review_state"] == "EVIDENCE_BOUND_CANDIDATE_PENDING_GPT"
    assert candidates[0]["role_certified"] is False
    # Public summary contains counters/hashes, no component names, source paths or scene payload.
    assert not {"scene_id", "sources", "geoms", "external_sources"}.intersection(result)


@pytest.mark.parametrize("key", list(FILES))
def test_any_reviewed_input_tamper_refuses_before_output(release_case, key):
    c = release_case; p = c["inputs"][key]
    p.write_bytes(p.read_bytes() + b"\n")
    with pytest.raises(ContractError, match="reviewed input hash"):
        build(c)
    assert not c["out"].exists()


def test_original_asset_mutation_invalidates_existing_release(release_case):
    c = release_case; build(c)
    first = read_json(c["inputs"]["frame0"])
    from pathlib import Path
    asset = next(Path(r["path"]) for r in first["sources"] if r["source_kind"] == "asset")
    asset.write_bytes(asset.read_bytes() + b"changed")
    with pytest.raises(ContractError, match="original model/state/input"):
        verify(c["out"], c["profiles"])


def test_actual_state_archive_is_required_not_only_inventory_claim(release_case):
    c = release_case; build(c)
    p = c["source"]["states"]
    with np.load(p, allow_pickle=False) as archive:
        payload = {k: archive[k] for k in archive.files}
    payload["qpos"][200] += .25
    np.savez(p, **payload)
    with pytest.raises(ContractError, match="state row changed"):
        verify(c["out"], c["profiles"])


@pytest.mark.parametrize("flag", ["training_ready", "full_scene_source_certified",
    "historical_generator_revision_certified", "native_object_observations_provided", "gt_structural_labels_provided"])
def test_resealing_manifest_cannot_promote_certification(release_case, flag):
    c = release_case; build(c)
    config = c["out"] / "config.json"; value = read_json(config); value[flag] = True; write_json(config, value)
    manifest = c["out"] / "release.json"; value = read_json(manifest)
    value["config"].update(bytes=config.stat().st_size, sha256=digest(config)); write_json(manifest, value)
    (c["out"] / "RELEASE_COMPLETE").write_text(digest(manifest) + "\n")
    with pytest.raises(ContractError, match="overclaims"):
        verify(c["out"], c["profiles"])


def test_even_rehashed_role_input_cannot_change_previously_classified_parts(release_case, monkeypatch):
    c = release_case; roles = c["inputs"]["roles"]; value = read_json(roles)
    value["geoms"]["collision"]["role"] = "auxiliary"; write_json(roles, value)
    profiles = read_json(c["profiles"]); profiles["profiles"]["1"]["files"]["proposed_roles.json"] = digest(roles)
    write_json(c["profiles"], profiles)
    monkeypatch.setattr(scene_release, "TRUSTED_PROFILE_SHA256", digest(c["profiles"]))
    with pytest.raises(ContractError, match="outside reviewed unknown scope"):
        build(c)


def test_callers_cannot_self_sign_profiles_or_reuse_verdict_text(release_case, monkeypatch):
    c = release_case
    monkeypatch.setattr(scene_release, "TRUSTED_PROFILE_SHA256", c["production_pin"])
    with pytest.raises(ContractError, match="pinned scene-bound review authority"):
        build(c)
    assert not c["out"].exists()


def test_role_source_assertion_must_match_original_proof(release_case, monkeypatch):
    c = release_case; roles = c["inputs"]["roles"]; value = read_json(roles)
    value["geoms"]["mesh"]["role_evidence"]["source_geom_node_sha256"] = "f" * 64
    write_json(roles, value)
    profiles = read_json(c["profiles"]); profiles["profiles"]["1"]["files"]["proposed_roles.json"] = digest(roles)
    write_json(c["profiles"], profiles)
    monkeypatch.setattr(scene_release, "TRUSTED_PROFILE_SHA256", digest(c["profiles"]))
    with pytest.raises(ContractError, match="source assertion differs"):
        build(c)


def test_resealed_wrong_config_schema_is_rejected(release_case):
    c = release_case; build(c)
    config = c["out"] / "config.json"; value = read_json(config); value["schema"] = "other"; write_json(config, value)
    manifest = c["out"] / "release.json"; value = read_json(manifest)
    value["config"].update(bytes=config.stat().st_size, sha256=digest(config)); write_json(manifest, value)
    (c["out"] / "RELEASE_COMPLETE").write_text(digest(manifest) + "\n")
    with pytest.raises(ContractError, match="overclaims"):
        verify(c["out"], c["profiles"])


def test_existing_release_and_source_overlap_cannot_be_overwritten(release_case):
    c = release_case; build(c); saved = digest(c["out"] / "release.json")
    with pytest.raises(ContractError, match="output must be new"):
        build(c)
    with pytest.raises(ContractError, match="overlaps source"):
        package(c["profiles"], 1, c["inputs"], c["source"]["xml"].parent / "bad_release")
    assert digest(c["out"] / "release.json") == saved


def test_symlink_to_unsealed_role_file_is_rejected(release_case):
    c = release_case; build(c)
    p = c["out"] / "role_map.json"; p.unlink(); p.symlink_to(c["inputs"]["roles"])
    with pytest.raises(ContractError, match="escapes bundle"):
        verify(c["out"], c["profiles"])


def test_wrong_profile_or_missing_evidence_cannot_reuse_approval(release_case):
    c = release_case; build(c)
    original_profile = c["profiles"].read_bytes()
    profiles = read_json(c["profiles"]); profiles["review"]["commit"] = "f" * 40; write_json(c["profiles"], profiles)
    with pytest.raises(ContractError, match="profile/evidence closure"):
        verify(c["out"], c["profiles"])
    c["profiles"].write_bytes(original_profile)
    reduced = dict(c["inputs"]); reduced.pop("approval")
    with pytest.raises(ContractError, match="complete fixed evidence"):
        package(c["profiles"], 1, reduced, c["out"].with_name("missing"))


@pytest.mark.parametrize("kind", ["roles", "config"])
def test_valid_substitute_cannot_hide_a_changed_consumed_canonical_file(release_case, kind):
    c = release_case; build(c)
    name = "role_map.json" if kind == "roles" else "config.json"
    original = c["out"] / name; substitute = c["out"] / ("approved_" + name)
    substitute.write_bytes(original.read_bytes())
    bad = read_json(original)
    if kind == "config":
        bad["training_ready"] = True
    else:
        bad["geoms"]["mesh"]["role"] = "auxiliary"
    write_json(original, bad)
    manifest = c["out"] / "release.json"; value = read_json(manifest)
    record = value["files"]["roles"] if kind == "roles" else value["config"]
    record["path"] = substitute.name; write_json(manifest, value)
    (c["out"] / "RELEASE_COMPLETE").write_text(digest(manifest) + "\n")
    with pytest.raises(ContractError, match="profile/evidence closure"):
        verify(c["out"], c["profiles"])


def _repin_test_inventory(c, monkeypatch):
    """Own test authority injection only; production profile pin cannot be changed by CLI."""
    report = read_json(c["inputs"]["analysis"])
    profiles = read_json(c["profiles"])
    for frame in profiles["profiles"]["1"]["frames"]:
        path = c["inputs"]["frame" + str(frame["frame_id"])]
        value = read_json(path); frame["inventory_sha256"] = digest(path)
        record = next(r for r in report["inventory_files"] if r["frame_id"] == frame["frame_id"])
        record.update(sha256=digest(path), state=value["state"])
    write_json(c["inputs"]["analysis"], report)
    profiles["profiles"]["1"]["analysis_sha256"] = digest(c["inputs"]["analysis"])
    write_json(c["profiles"], profiles)
    monkeypatch.setattr(scene_release, "TRUSTED_PROFILE_SHA256", digest(c["profiles"]))


def test_second_frame_distinct_archive_is_sealed_in_full(release_case, monkeypatch):
    c = release_case
    second = c["out"].parent / "second_originals"; second.mkdir()
    archive = second / "states.npz"; archive.write_bytes(c["source"]["states"].read_bytes())
    inv = c["inputs"]["frame200"]; value = read_json(inv); value["state"]["path"] = str(archive)
    write_json(inv, value); _repin_test_inventory(c, monkeypatch)
    build(c)
    manifest = read_json(c["out"] / "release.json")
    assert str(archive) in {r["path"] for r in manifest["external_sources"]}
    with np.load(archive, allow_pickle=False) as saved:
        data = {k: saved[k] for k in saved.files}
    data["qpos"][10] += .5  # Unselected row; hashes must protect the whole archive.
    np.savez(archive, **data)
    with pytest.raises(ContractError, match="original model/state/input"):
        verify(c["out"], c["profiles"])


def test_conflicting_expected_hashes_for_one_source_path_are_not_overwritten(release_case, monkeypatch):
    c = release_case
    inv = c["inputs"]["frame0"]; value = read_json(inv)
    value["input_files"]["metadata"]["path"] = str(c["source"]["states"])
    write_json(inv, value); _repin_test_inventory(c, monkeypatch)
    with pytest.raises(ContractError, match="conflicting external source record"):
        build(c)
