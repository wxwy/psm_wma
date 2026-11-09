"""Server-local source-role analysis ledger; never assigns production roles.

Pair existing AUDIT_ONLY inventories, retain every unknown component, and bind
explicit analyst hypotheses to original XML/compiled identity and inspected
generator bytes. Matching evidence is a candidate for GPT, not semantic truth.
No scene reconstruction, generator execution, network or data upload occurs.
"""
import argparse
from collections import Counter
import hashlib
from pathlib import Path

from g2.io import ContractError, canonical, digest, new_output, read_json, sha, verified_file, write_json
from .source_geometry import model_source_hash
from .source_roles import source_geom_nodes
from .prescan import source_binding


def _hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _inventory(path, xml_cache):
    value = read_json(path)
    if not isinstance(value, dict):
        raise ContractError("inventory must be an object")
    rows = value.get("geom_audit")
    identity = value.get("source_identity", {})
    metadata = identity.get("metadata") if isinstance(identity, dict) else None
    records = value.get("sources")
    if (value.get("schema") != "g2_sim_asset_inventory_v1" or value.get("status") != "AUDIT_ONLY"
        or value.get("training_ready") is not False or not isinstance(rows, list) or not rows
        or not isinstance(identity, dict) or any(not isinstance(row, dict) for row in rows)
        or not isinstance(metadata, dict) or not isinstance(value.get("scene_id"), str)
        or not isinstance(metadata.get("geoms"), dict)
        or value["scene_id"] != metadata.get("scene_id")
        or type(value.get("frame_id")) is not int or value["frame_id"] < 0
        or not isinstance(records, list) or not records or any(not isinstance(s, dict) for s in records)
        or value.get("geom_audit_sha256") != _hash(rows)
        or value.get("source_identity_sha256") != _hash(identity)
        or identity.get("model_source_sha256") != model_source_hash(value.get("sources", []))
        or [row.get("geom_id") for row in rows] != list(range(len(rows)))
        or len({row.get("geom_name") for row in rows}) != len(rows)):
        raise ContractError("inventory identity, row order or audit hash differs")
    state = value.get("state", {})
    if (not isinstance(state, dict) or type(state.get("frame_id")) is not int
        or state["frame_id"] != value["frame_id"] or state.get("format") not in ("qpos", "mujoco_fullphysics")
        or metadata.get("state_source") != {
            "model_source_sha256": identity["model_source_sha256"], "states_sha256": state.get("file_sha256")}):
        raise ContractError("inventory frame/state archive binding differs")
    sha(state.get("file_sha256"), "state archive hash")
    sha(state.get("row_sha256"), "state row hash")
    # Portable closure identity intentionally omits parsing context. This cache
    # must include it so a changed source_kind/include edge cannot reuse XML.
    key = _hash(records)
    if key not in xml_cache:
        xml_cache[key] = source_geom_nodes(value["sources"])
    for row in rows:
        evidence = row.get("role_evidence", {})
        if not isinstance(evidence, dict):
            raise ContractError("inventory role evidence must be an object")
        properties = evidence.get("compiled_properties", {})
        if (not isinstance(evidence, dict) or not isinstance(properties, dict)
            or evidence.get("compiled_signature_sha256") != _hash(properties)
            or any(properties.get(key) != row.get(key) for key in
                   ("geom_id", "geom_name", "body_ancestry", "geometry_type", "geometry_type_id",
                    "geometry_data_id", "geom_size", "group", "contype", "conaffinity", "material_id", "compiled_rgba"))):
            raise ContractError("inventory compiled signature differs from row")
        for node in evidence.get("source_geom_nodes", []):
            payload = {k: v for k, v in node.items() if k != "source_geom_node_sha256"}
            source = [record for record in value["sources"] if record["logical_id"] == node.get("source_logical_id")]
            if (node.get("source_geom_node_sha256") != _hash(payload) or len(source) != 1
                or source[0]["sha256"] != node.get("source_sha256")):
                raise ContractError("inventory original XML node identity differs")
        bodies = [body["body_name"] for body in reversed(row["body_ancestry"]) if body["body_id"] != 0]
        matches = []
        for node in xml_cache[key]["nodes"].get(row["geom_name"], []):
            chain = iter(bodies)
            if all(any(actual == expected for actual in chain) for expected in node["body_ancestors"]):
                matches.append(node)
        status = "SOURCE_BOUND" if len(matches) == 1 else "SOURCE_AMBIGUOUS" if matches else "SOURCE_UNRESOLVED"
        if evidence.get("source_geom_nodes") != matches or evidence.get("status") != status:
            raise ContractError("inventory nodes differ from original hashed XML")
        spec = metadata["geoms"].get(row["geom_name"])
        role, declaration, binding, reason = "UNCLASSIFIED", "MISSING", None, None
        if spec is not None:
            try:
                binding = source_binding(spec, row["geom_name"], identity.get("ep_meta"), body_names=[
                    body["body_name"] for body in row["body_ancestry"] if isinstance(spec, dict)
                    and (spec.get("source_kind") == "mjcf" or body["body_id"] != 0)])
                role, declaration, reason = spec["role"], "DECLARED", spec.get("classification_reason")
            except ContractError:
                declaration = "INVALID"
        if (row.get("role") != role or row.get("declaration_status") != declaration
            or row.get("source") != binding or row.get("classification_reason") != reason
            or evidence.get("asserted_role") != (spec.get("role") if isinstance(spec, dict) else None)):
            raise ContractError("inventory role differs from original hashed declaration")
    return value


def analyze(inventories, catalog, output, *, decisions=None, generator_roots=None):
    """Create immutable analysis only; never emit metadata usable as a role map."""
    paths = [Path(p).resolve(strict=True) for p in inventories]
    if len(paths) != 2:
        raise ContractError("two independently generated frame inventories are required")
    xml_cache = {}
    values = [_inventory(path, xml_cache) for path in paths]
    first, later = values
    context = lambda value: sorted([{k: v for k, v in source.items() if k != "path"}
                                     for source in value["sources"]], key=lambda source: source["logical_id"])
    if (first["scene_id"] != later["scene_id"] or first["world_frame"] != later["world_frame"]
        or first["source_identity_sha256"] != later["source_identity_sha256"]
        or type(first.get("frame_id")) is not int or type(later.get("frame_id")) is not int
        or first["frame_id"] >= later["frame_id"]
        or context(first) != context(later)
        or len(first["geom_audit"]) != len(later["geom_audit"])):
        raise ContractError("paired inventory scene, source or frame identity differs")
    for before, after in zip(first["geom_audit"], later["geom_audit"]):
        a, b = before["role_evidence"], after["role_evidence"]
        if (a != b or before["role"] != after["role"] or before.get("source") != after.get("source")):
            raise ContractError("paired inventory source-role or compiled identity changed")
    catalog_path = Path(catalog).resolve(strict=True)
    reference = read_json(catalog_path)
    if (not isinstance(reference, dict) or reference.get("schema") != "g2_generator_role_catalog_v1"
        or not isinstance(reference.get("sources"), dict) or not isinstance(reference.get("rules"), dict)):
        raise ContractError("unknown generator role catalog")
    sources, rules = reference["sources"], reference["rules"]
    roots = {name: Path(root).resolve(strict=True) for name, root in (generator_roots or {}).items()}
    ledger = read_json(decisions) if decisions else {"schema": "g2_role_hypotheses_v1", "entries": []}
    if (not isinstance(ledger, dict) or ledger.get("schema") != "g2_role_hypotheses_v1"
        or not isinstance(ledger.get("entries"), list)):
        raise ContractError("unknown per-component role hypotheses")
    proposed = {}
    unknown_ids = {row["geom_id"] for row in first["geom_audit"] if row["role"] == "UNCLASSIFIED"}
    for entry in ledger["entries"]:
        if not isinstance(entry, dict):
            raise ContractError("per-component hypothesis must be an object")
        key = entry.get("geom_id")
        if type(key) is not int or key not in unknown_ids or key in proposed:
            raise ContractError("hypothesis targets duplicate, declared or foreign geom")
        proposed[key] = entry
    original_roots = {Path(source["path"]).resolve(strict=True).parent for value in values for source in value["sources"]}
    out = new_output(output, [*paths, catalog_path, *original_roots, *roots.values(), *([decisions] if decisions else [])])
    rows, templates, verified = [], [], {}

    def generator_evidence(rule):
        facts = []
        spans = rule.get("generator_spans")
        if not isinstance(spans, list) or any(not isinstance(span, dict) for span in spans):
            raise ContractError("generator spans must be explicit objects")
        for span in spans:
            key = span["source_id"]
            if key not in verified:
                source = sources[key]
                if not isinstance(source, dict):
                    raise ContractError("generator source must be an object")
                if source["root"] not in roots:
                    raise ContractError("generator root missing: " + source["root"])
                if type(source.get("bytes")) is not int or not 0 < source["bytes"] <= 8 * 1024 * 1024:
                    raise ContractError("generator evidence file exceeds byte limit")
                path = verified_file(roots[source["root"]], source)
                payload = path.read_bytes()
                if len(payload) != source["bytes"] or hashlib.sha256(payload).hexdigest() != source["sha256"]:
                    raise ContractError("generator source changed while collecting evidence")
                verified[key] = payload.splitlines(keepends=True)
            lines = verified[key]
            start, end = span["start_line"], span["end_line"]
            if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(lines)
                or hashlib.sha256(b"".join(lines[start - 1:end])).hexdigest() != span["excerpt_sha256"]):
                raise ContractError("generator evidence excerpt differs")
            facts.append(dict(span, source_sha256=sources[key]["sha256"], repository=sources[key]["repository"],
                              reference_commit=sources[key]["commit"]))
        if not facts:
            raise ContractError("classification lacks inspected generator code")
        return facts

    for row in first["geom_audit"]:
        evidence = row["role_evidence"]
        nodes = evidence.get("source_geom_nodes", [])
        item = {key: row.get(key) for key in ("geom_id", "geom_name", "role", "source", "body_ancestry",
                "geometry_type", "geom_size", "group", "contype", "conaffinity", "effective_rgba",
                "material", "geometry_status", "material_probe", "sampling")}
        item.update(role_evidence=evidence, candidate_role=None, role_certified=False,
                    review_state="UNRESOLVED" if row["role"] == "UNCLASSIFIED" else "DECLARED_NOT_RE_REVIEWED")
        if row["role"] == "UNCLASSIFIED":
            template = {"geom_id": row["geom_id"], "compiled_signature_sha256": evidence["compiled_signature_sha256"],
                "source_geom_node_sha256": nodes[0]["source_geom_node_sha256"] if len(nodes) == 1 else None,
                "source_attributes": nodes[0]["attributes"] if len(nodes) == 1 else None,
                "rule_id": None, "role": None, "classification_reason": None,
                "emission_trace": None, "condition_evidence": {}}
            templates.append(template)
            entry = proposed.get(row["geom_id"])
            if entry is not None:
                try:
                    if evidence.get("status") != "SOURCE_BOUND" or len(nodes) != 1:
                        raise ContractError("original source node is unresolved or ambiguous")
                    if any(entry.get(k) != template[k] for k in
                           ("compiled_signature_sha256", "source_geom_node_sha256", "source_attributes")):
                        raise ContractError("hypothesis differs from original XML or compiled signature")
                    rule = rules.get(entry.get("rule_id"), {})
                    roles = rule.get("allowed_roles") if isinstance(rule, dict) else None
                    conditions = rule.get("conditions") if isinstance(rule, dict) else None
                    if (not isinstance(roles, list) or any(r not in ("visual", "collision", "auxiliary", "robot") for r in roles)
                        or entry.get("role") not in roles):
                        raise ContractError("rule does not justify proposed role")
                    for key in ("classification_reason", "emission_trace"):
                        if not isinstance(entry.get(key), str) or not entry[key].strip():
                            raise ContractError("explicit generator-to-component explanation required")
                    checks = entry.get("condition_evidence", {})
                    if (not isinstance(checks, dict) or not isinstance(conditions, list) or not conditions
                        or any(not isinstance(k, str) or not isinstance(checks.get(k), str) or not checks[k].strip() for k in conditions)):
                        raise ContractError("generator conditions lack per-component source evidence")
                    if rule.get("require_transparent_noncontact") and (row["effective_rgba"][3] != 0
                            or row["contype"] != 0 or row["conaffinity"] != 0):
                        raise ContractError("region exclusion has unresolved visible or contact behavior")
                    facts = generator_evidence(rule)
                    item.update(candidate_role=entry["role"], review_state="EVIDENCE_BOUND_CANDIDATE_PENDING_GPT",
                                hypothesis=entry, generator_evidence=facts)
                except (ContractError, KeyError, TypeError, OSError, ValueError) as error:
                    item.update(review_state="EVIDENCE_REJECTED", rejected_hypothesis=entry, reason=str(error))
            else:
                item["reason"] = "NO_PER_COMPONENT_GENERATOR_HYPOTHESIS"
        rows.append(item)
    counts = Counter(row["review_state"] for row in rows)
    report = {"schema": "g2_source_role_analysis_v1", "status": "AUDIT_ONLY", "scene_id": first["scene_id"],
        "frames": [first["frame_id"], later["frame_id"]], "inventory_files": [{"sha256": digest(path),
            "frame_id": value["frame_id"], "state": value["state"]} for path, value in zip(paths, values)],
        "model_source_sha256": first["source_identity"]["model_source_sha256"],
        "catalog_sha256": digest(catalog_path), "hypotheses_sha256": digest(decisions) if decisions else None,
        "analysis_source_sha256": digest(Path(__file__)), "compiled_geom_count": len(rows),
        "remaining_unclassified_count": len(unknown_ids), "review_state_counts": dict(counts),
        "candidate_role_counts": dict(Counter(row["candidate_role"] for row in rows if row["candidate_role"])),
        "geom_analysis": rows, "role_assignments_written": False, "generator_semantics_independently_reviewed": False,
        "training_ready": False, "full_scene_source_certified": False, "point_cloud_created": False,
        "scope": "SOURCE_EVIDENCE_LEDGER_ONLY_NOT_NATIVE_DETECTIONS_OR_ROLE_APPROVAL"}
    out.mkdir(parents=True)
    write_json(out / "role_analysis.json", report)
    write_json(out / "hypotheses_template.json", {"schema": "g2_role_hypotheses_v1", "entries": templates})
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", action="append", required=True)
    parser.add_argument("--catalog", required=True); parser.add_argument("--hypotheses")
    parser.add_argument("--generator-root", action="append", default=[], metavar="NAME=PATH")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(); roots = {}
    for item in args.generator_root:
        name, separator, path = item.partition("=")
        if not separator or not name or not path or name in roots:
            parser.error("generator-root must be unique NAME=PATH")
        roots[name] = path
    result = analyze(args.inventory, args.catalog, args.output, decisions=args.hypotheses, generator_roots=roots)
    print(result["status"], result["compiled_geom_count"], result["remaining_unclassified_count"])


if __name__ == "__main__":
    main()
