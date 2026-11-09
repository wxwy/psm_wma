"""Seal reviewed, scene-bound role inputs on the data host; never promote production.

Only immutable public profiles carry review authority. Detailed role maps,
original inventories, component proofs and the GPT ledger remain server-local.
No cloud generation, MuJoCo execution, native detections or network access.
"""
import argparse
from collections import Counter
import copy
import hashlib
from pathlib import Path
import shutil

import numpy as np

from g2.io import ContractError, canonical, digest, new_output, read_json, sha, verified_file, write_json
from .role_review import _inventory
from .prescan import source_binding


VERDICT = "APPROVE_SCENE_BOUND_ROLE_CANDIDATES_LAYOUT1_LAYOUT10_ONLY"
# Review authority is part of the versioned implementation, never supplied by
# a caller's self-signed JSON. Tests replace this constant only via monkeypatch.
TRUSTED_PROFILE_SHA256 = "3d881440e05853d862a814172d821fd245c182478631590c2f2e16e2401eefb9"
FILES = {"roles": "role_map.json", "hypotheses": "hypotheses.json",
         "analysis": "component_evidence.json", "catalog": "generator_catalog.json",
         "approval": "gpt_acceptance.json", "frame0": "inventory_frame_0.json",
         "frame200": "inventory_frame_200.json"}


def _hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _profile(path, layout):
    if digest(path) != TRUSTED_PROFILE_SHA256:
        raise ContractError("profile is not the pinned scene-bound review authority")
    data = read_json(path)
    if (type(layout) is not int or layout not in (1, 10) or
            data.get("schema") != "g2_scene_role_profiles_v1" or
            any(data.get(k) is not False for k in ("historical_generator_revision_certified",
                "full_scene_source_certified", "training_ready")) or
            data.get("review", {}).get("verdict") != VERDICT or
            str(layout) not in data.get("profiles", {})):
        raise ContractError("unsupported or overclaimed scene-role profile")
    for record in (data["review"], data["classification_source"]):
        for key in ("commit", "tree", "blob"):
            if key in record and (len(record[key]) != 40 or any(c not in "0123456789abcdef" for c in record[key])):
                raise ContractError("invalid review/source Git identity")
    profile = data["profiles"][str(layout)]
    if profile.get("layout") != layout or [x.get("frame_id") for x in profile.get("frames", [])] != [0, 200]:
        raise ContractError("scene profile must bind exactly frames0/200")
    counts = profile.get("proposed_counts", {})
    if (type(profile.get("compiled_geom_count")) is not int or profile["compiled_geom_count"] <= 0 or
            type(profile.get("classified_unknown_count")) is not int or
            not 0 < profile["classified_unknown_count"] <= profile["compiled_geom_count"] or
            not counts or set(counts) - {"visual", "collision", "auxiliary", "robot"} or
            any(type(v) is not int or v <= 0 for v in counts.values()) or
            sum(counts.values()) != profile["classified_unknown_count"]):
        raise ContractError("invalid fixed scene role counts")
    return data, profile


def _external(first):
    records = {}
    def add(record):
        path = Path(record["path"]).resolve(strict=True)
        expected = {"path": str(path), "bytes": record.get("bytes", path.stat().st_size), "sha256": record["sha256"]}
        if str(path) in records and records[str(path)] != expected:
            raise ContractError("conflicting external source record")
        records[str(path)] = expected
    for record in first["sources"]:
        add(record)
    for record in first.get("input_files", {}).values():
        add(record)
    add({"path": first["state"]["path"], "sha256": first["state"]["file_sha256"]})
    for record in records.values():
        path = Path(record["path"])
        if path.stat().st_size != record["bytes"] or digest(path) != sha(record["sha256"]):
            raise ContractError("original model/state/input changed since independent review")
    return [records[k] for k in sorted(records)]


def _validate(profile_file, layout, inputs):
    data, profile = _profile(profile_file, layout)
    if set(inputs) != set(FILES):
        raise ContractError("release requires the complete fixed evidence set")
    paths = {k: Path(v).resolve(strict=True) for k, v in inputs.items()}
    expected = {"roles": profile["files"]["proposed_roles.json"],
        "hypotheses": profile["files"]["hypotheses.json"], "analysis": profile["analysis_sha256"],
        "catalog": data["classification_source"]["catalog_sha256"],
        "approval": data["review"]["evidence_sha256"]}
    expected.update({"frame" + str(f["frame_id"]): f["inventory_sha256"] for f in profile["frames"]})
    for name, path in paths.items():
        if digest(path) != sha(expected[name]):
            raise ContractError("reviewed input hash differs: " + name)
    # Re-read source XML and independently preserved compiled/declaration contracts.
    cache = {}
    values = [_inventory(paths["frame" + str(f["frame_id"])], cache) for f in profile["frames"]]
    first = values[0]
    for value, frame in zip(values, profile["frames"]):
        state = value["state"]
        if (value["scene_id"] != first["scene_id"] or value["world_frame"] != first["world_frame"] or
                value["source_identity_sha256"] != profile["source_identity_sha256"] or
                value["source_identity"]["model_source_sha256"] != profile["model_source_sha256"] or
                len(value["geom_audit"]) != profile["compiled_geom_count"] or
                any(state.get(k) != v for k, v in (("frame_id", frame["frame_id"]),
                    ("file_sha256", frame["state_archive_sha256"]), ("format", frame["state_format"]),
                    ("row_sha256", frame["state_row_sha256"])))):
            raise ContractError("profile differs from original scene/frame identity")
        with np.load(state["path"], allow_pickle=False) as archive:
            rows = archive["qpos" if state["format"] == "qpos" else "states"]
            if (rows.ndim != 2 or rows.dtype.kind != "f" or state["frame_id"] >= len(rows) or
                    not np.isfinite(rows[state["frame_id"]]).all() or
                    hashlib.sha256(rows[state["frame_id"]].astype("<f8").tobytes()).hexdigest() != state["row_sha256"]):
                raise ContractError("original state row changed")
    original = first["source_identity"]["metadata"]
    rolemap = read_json(paths["roles"])
    unknown = {r["geom_id"]: r for r in first["geom_audit"] if r["role"] == "UNCLASSIFIED"}
    unknown_names = {r["geom_name"] for r in unknown.values()}
    if len(unknown) != profile["classified_unknown_count"] or not isinstance(rolemap.get("geoms"), dict):
        raise ContractError("review scope or role-map shape differs")
    if {k: v for k, v in rolemap.items() if k != "geoms"} != {k: v for k, v in original.items() if k != "geoms"}:
        raise ContractError("role map changed unrelated source metadata")
    before, after = original["geoms"], rolemap["geoms"]
    if ({k for k in set(before) | set(after) if before.get(k) != after.get(k)} != unknown_names or
            set(after) != {r["geom_name"] for r in first["geom_audit"]}):
        raise ContractError("role map changed outside reviewed unknown scope")
    hypotheses = read_json(paths["hypotheses"])["entries"]
    analysis = read_json(paths["analysis"])
    if (analysis.get("inventory_files") != [{"sha256": digest(paths["frame" + str(v["frame_id"])]),
            "frame_id": v["frame_id"], "state": v["state"]} for v in values] or
            analysis.get("scene_id") != first["scene_id"] or analysis.get("frames") != [0, 200] or
            analysis.get("model_source_sha256") != profile["model_source_sha256"] or
            analysis.get("compiled_geom_count") != profile["compiled_geom_count"]):
        raise ContractError("component ledger differs from scene/frame inventory closure")
    proposals = {e["geom_id"]: e for e in hypotheses}
    bound = {r["geom_id"]: r for r in analysis["geom_analysis"] if r["role"] == "UNCLASSIFIED"}
    if (len(proposals) != len(hypotheses) or set(proposals) != set(unknown) or set(bound) != set(unknown) or
            analysis["catalog_sha256"] != expected["catalog"] or
            analysis["hypotheses_sha256"] != expected["hypotheses"]):
        raise ContractError("component evidence coverage differs")
    for geom, row in unknown.items():
        entry, evidence = proposals[geom], bound[geom]
        spec = after[row["geom_name"]]
        if (entry["role"] != spec["role"] or evidence["candidate_role"] != spec["role"] or
                evidence["review_state"] != "EVIDENCE_BOUND_CANDIDATE_PENDING_GPT" or
                evidence["role_certified"] is not False or
                entry["compiled_signature_sha256"] != row["role_evidence"]["compiled_signature_sha256"] or
                entry["source_geom_node_sha256"] != row["role_evidence"]["source_geom_nodes"][0]["source_geom_node_sha256"]):
            raise ContractError("role differs from reviewed original per-component proof")
        if spec.get("role_evidence") != {"compiled_signature_sha256": entry["compiled_signature_sha256"],
                "source_geom_node_sha256": entry["source_geom_node_sha256"], "asserted_role": entry["role"]}:
            raise ContractError("role map source assertion differs from component proof")
    for row in first["geom_audit"]:
        source_binding(after[row["geom_name"]], row["geom_name"], first["source_identity"].get("ep_meta"),
            body_names=[b["body_name"] for b in row["body_ancestry"] if b["body_id"] != 0 or
                        after[row["geom_name"]].get("source_kind") == "mjcf"])
    counts = dict(Counter(after[n]["role"] for n in unknown_names))
    if counts != profile["proposed_counts"]:
        raise ContractError("reviewed role totals differ")
    external = {}
    for value in values:
        for record in _external(value):
            if record["path"] in external and external[record["path"]] != record:
                raise ContractError("paired inventories conflict on original source bytes")
            external[record["path"]] = record
    return data, profile, paths, first, [external[k] for k in sorted(external)]


def package(profile_file, layout, inputs, output):
    """New immutable server-local candidate input; originals are never overwritten."""
    profile_file = Path(profile_file).resolve(strict=True)
    data, profile, paths, first, external = _validate(profile_file, layout, inputs)
    protected = [profile_file, *paths.values(), *[Path(e["path"]).parent for e in external]]
    out = new_output(output, protected)
    out.mkdir(parents=True)
    records = {}
    for name, filename in FILES.items():
        shutil.copyfile(paths[name], out / filename)
        records[name] = {"path": filename, "bytes": (out / filename).stat().st_size,
                         "sha256": digest(out / filename)}
    config = {"schema": "g2_scene_role_candidate_config_v1", "scene_id": first["scene_id"],
        "world_frame": first["world_frame"], "layout": layout, "role_map": FILES["roles"],
        "frames": copy.deepcopy(profile["frames"]), "state_source": first["source_identity"]["metadata"]["state_source"],
        "role_map_sha256": records["roles"]["sha256"], "profiles_sha256": digest(profile_file),
        "review": copy.deepcopy(data["review"]), "classification_source": copy.deepcopy(data["classification_source"]),
        "status": "REVIEWED_SCENE_ROLE_INPUT_FOR_INTEGRATION_ONLY", "training_ready": False,
        "full_scene_source_certified": False, "historical_generator_revision_certified": False,
        "native_object_observations_provided": False, "gt_structural_labels_provided": False,
        "production_map_applied": False, "point_cloud_generated": False}
    write_json(out / "config.json", config)
    manifest = {"schema": "g2_scene_role_release_v1", "layout": layout,
        "profiles_sha256": digest(profile_file), "files": records, "external_sources": external,
        "config": {"path": "config.json", "bytes": (out / "config.json").stat().st_size,
                   "sha256": digest(out / "config.json")}}
    write_json(out / "release.json", manifest)
    # Revalidate disk copies and original closure before writing the final marker.
    verify(out, profile_file, require_marker=False)
    (out / "RELEASE_COMPLETE").write_text(digest(out / "release.json") + "\n", encoding="ascii")
    return _summary(profile, out)


def _summary(profile, root):
    return {"schema": "g2_scene_role_release_summary_v1", "layout": profile["layout"],
        "classified_unknown_count": profile["classified_unknown_count"], "role_counts": profile["proposed_counts"],
        "release_sha256": digest(root / "release.json"), "config_sha256": digest(root / "config.json"),
        "role_map_sha256": digest(root / FILES["roles"]), "production_map_applied": False,
        "private_individual_files_exported": False, "training_ready": False, "full_scene_source_certified": False}


def verify(root, profile_file, *, require_marker=True):
    root, profile_file = Path(root).resolve(strict=True), Path(profile_file).resolve(strict=True)
    if require_marker and (root / "RELEASE_COMPLETE").read_text(encoding="ascii") != digest(root / "release.json") + "\n":
        raise ContractError("release completion hash differs")
    manifest = read_json(root / "release.json")
    if (manifest.get("schema") != "g2_scene_role_release_v1" or
            manifest.get("profiles_sha256") != digest(profile_file) or set(manifest.get("files", {})) != set(FILES) or
            any(manifest["files"][key].get("path") != name for key, name in FILES.items()) or
            manifest.get("config", {}).get("path") != "config.json"):
        raise ContractError("release profile/evidence closure differs")
    paths = {k: verified_file(root, r) for k, r in manifest["files"].items()}
    data, profile, _, first, external = _validate(profile_file, manifest["layout"], paths)
    config = read_json(verified_file(root, manifest["config"]))
    if (config.get("schema") != "g2_scene_role_candidate_config_v1" or
            manifest["external_sources"] != external or config.get("review") != data["review"] or
            config.get("classification_source") != data["classification_source"] or
            config.get("profiles_sha256") != digest(profile_file) or config.get("layout") != profile["layout"] or
            config.get("role_map") != FILES["roles"] or config.get("role_map_sha256") != digest(paths["roles"]) or
            config.get("scene_id") != first["scene_id"] or config.get("world_frame") != first["world_frame"] or
            config.get("frames") != profile["frames"] or
            config.get("state_source") != first["source_identity"]["metadata"]["state_source"] or
            config.get("status") != "REVIEWED_SCENE_ROLE_INPUT_FOR_INTEGRATION_ONLY" or
            any(config.get(k) is not False for k in ("training_ready", "full_scene_source_certified",
                "historical_generator_revision_certified", "native_object_observations_provided",
                "gt_structural_labels_provided", "production_map_applied", "point_cloud_generated"))):
        raise ContractError("candidate config overclaims certification or differs from reviewed scope")
    return _summary(profile, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("package", "verify"))
    parser.add_argument("--profiles", required=True)
    parser.add_argument("--layout", type=int)
    parser.add_argument("--inputs")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = (package(args.profiles, args.layout, read_json(args.inputs), args.output)
              if args.action == "package" else verify(args.output, args.profiles))
    import json
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
