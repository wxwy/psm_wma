"""Compiled/source role evidence, never an automatic semantic classifier.

Original XML nodes and compiled body/geometry bind an explicit role assertion.
Independent full-source role/material review remains the existing source Gate.
"""
import gzip
import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from g2.io import ContractError, canonical
from .surface_sampling import geometry_sha256


def _sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def source_geom_nodes(sources):
    """Read only hashed source closure XML; defaults are facts, not role labels."""
    result,documents,parsed = {},[],{}
    for record in sources:
        path = Path(record["path"])
        if not (record.get("source_kind")=="mjcf_xml" or ("source_kind" not in record and
                (record["logical_id"].endswith(".xml") or str(path).endswith((".xml", ".xml.gz"))))):
            continue
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != record["sha256"]:
            raise ContractError("source changed during role evidence collection")
        payload = gzip.decompress(raw) if str(path).endswith(".gz") else raw
        if len(payload) > 32 * 1024 * 1024:
            raise ContractError("role source XML exceeds byte limit")
        root = ET.fromstring(payload)
        defaults = [{"attributes": dict(node.attrib), "children": [
            {"tag": child.tag, "attributes": dict(child.attrib)} for child in node if child.tag != "default"]}
            for node in root.iter("default")]
        defaults_sha=_sha(defaults)
        documents.append({"source_logical_id":record["logical_id"],"source_sha256":record["sha256"],
                          "source_defaults_sha256":defaults_sha,"source_defaults":defaults,
                          "includes":record.get("includes",[])})
        parsed[record["logical_id"]]=(record,root,defaults_sha)

    def walk(logical_id,node,location,body_names,excluded,chain):
        record,_,defaults_sha=parsed[logical_id]
        excluded=excluded or node.tag in ("default","asset")
        if node.tag=="body" and node.get("name"):body_names=[*body_names,node.get("name")]
        if node.tag=="include":
            targets={entry["logical_id"] for entry in record.get("includes",[]) if entry["reference"]==node.get("file")}
            if len(targets)!=1:raise ContractError("source include context is unresolved or ambiguous")
            target=targets.pop()
            if target not in parsed or target in [entry["source_logical_id"] for entry in chain]:
                raise ContractError("invalid source include evidence context")
            included=parsed[target][1]
            edge={"source_logical_id":logical_id,"source_sha256":record["sha256"],"xml_path":location,
                  "reference":node.get("file"),"included_logical_id":target}
            walk(target,included,"/"+included.tag,body_names,excluded,[*chain,edge])
        if node.tag=="geom" and node.get("name") and not excluded:
            evidence={"source_logical_id":logical_id,"source_sha256":record["sha256"],"xml_path":location,
                "attributes":dict(node.attrib),"body_ancestors":body_names,"source_defaults_sha256":defaults_sha,
                "inclusion_chain":chain}
            evidence["source_geom_node_sha256"]=_sha(evidence)
            result.setdefault(node.get("name"),[]).append(evidence)
        counters={}
        for child in node:
            index=counters.get(child.tag,0);counters[child.tag]=index+1
            walk(logical_id,child,location+"/"+child.tag+"["+str(index)+"]",body_names,excluded,chain)
    if "root.xml" not in parsed:raise ContractError("root MJCF evidence missing")
    root=parsed["root.xml"][1]
    walk("root.xml",root,"/"+root.tag,[],False,[])
    return {"nodes":result,"documents":documents}


def role_evidence(model, g, row, nodes, spec):
    """Facts remain separate from the asserted role and its independent review."""
    fields = ("geom_id", "geom_name", "body_ancestry", "geometry_type", "geometry_type_id","geometry_data_id",
              "geom_size", "group", "contype", "conaffinity", "material_id", "compiled_rgba")
    compiled = {key: row[key] for key in fields}
    compiled.update(local_position=model.geom_pos[g].tolist(), local_quaternion=model.geom_quat[g].tolist())
    if row["geometry_type"] == "mesh":
        mid = int(model.geom_dataid[g]); va, vn, fa, fn = [int(getattr(model, key)[mid])
            for key in ("mesh_vertadr", "mesh_vertnum", "mesh_faceadr", "mesh_facenum")]
        compiled["local_geometry_sha256"] = geometry_sha256(model.mesh_vert[va:va + vn], model.mesh_face[fa:fa + fn])
    body_names = [body["body_name"] for body in reversed(row["body_ancestry"]) if body["body_id"] != 0]
    candidates = []
    for node in nodes["nodes"].get(row["geom_name"], []):
        chain = iter(body_names)
        if all(any(actual == expected for actual in chain) for expected in node["body_ancestors"]):
            candidates.append(node)
    status = "SOURCE_BOUND" if len(candidates) == 1 else "SOURCE_AMBIGUOUS" if candidates else "SOURCE_UNRESOLVED"
    return {"schema": "g2_source_role_evidence_v1", "status": status,
        "compiled_signature_sha256": _sha(compiled), "compiled_properties": compiled,
        "source_geom_nodes": candidates,
        "asserted_role": spec.get("role") if isinstance(spec, dict) else None,
        "independent_role_review": "PENDING_EXTERNAL_FULL_SOURCE_REVIEW", "role_certified": False,
        "basis": "ORIGINAL_HASHED_XML_AND_COMPILED_GEOM_BODY_NOT_GROUP_OR_NAME_CLASSIFICATION"}


def proof_template(evidence):
    nodes = evidence["source_geom_nodes"]
    return {"compiled_signature_sha256": evidence["compiled_signature_sha256"],
            "source_geom_node_sha256": nodes[0]["source_geom_node_sha256"] if len(nodes) == 1 else None,
            "asserted_role": evidence["asserted_role"]}


def verify_role_assertion(spec, evidence):
    """Check source-bound declaration, not the truth of a human role decision."""
    proof = spec.get("role_evidence")
    if evidence["status"] != "SOURCE_BOUND" or not isinstance(proof, dict):
        raise ContractError("unambiguous source-bound role evidence required")
    if proof != proof_template(evidence):
        raise ContractError("role assertion differs from compiled/source evidence")
    reason = spec.get("classification_reason")
    if not isinstance(reason, str) or not reason.strip():
        raise ContractError("source-bound role classification reason required")
    if spec.get("role") == "robot" or spec.get("source_kind")=="ep_meta":
        root = spec.get("source_body_name")
        bodies = evidence["source_geom_nodes"][0]["body_ancestors"]
        if not isinstance(root, str) or root not in bodies:
            label="robot exclusion" if spec.get("role")=="robot" else "official identity"
            raise ContractError(label+" requires original source body ancestry evidence")


def verify_embedded_role_evidence(manifest, row, spec):
    evidence=row.get("role_evidence")
    required=manifest["source_identity"].get("require_role_evidence",False)
    if evidence is None:
        if required:raise ContractError("required source role evidence missing")
        return  # legacy manifest
    if not isinstance(evidence,dict):raise ContractError("invalid source role evidence")
    properties=evidence.get("compiled_properties")
    if (not isinstance(properties,dict) or evidence.get("compiled_signature_sha256")!=_sha(properties)
        or any(properties.get(key)!=row.get(key) for key in ("geom_id","geom_name","body_ancestry",
            "geometry_type","geometry_type_id","geometry_data_id","geom_size","group","contype","conaffinity","material_id","compiled_rgba"))
        or evidence.get("asserted_role")!=row["role"]):
        raise ContractError("source role evidence contradicts compiled inventory")
    sources={record["logical_id"]:record for record in manifest["sources"]}
    documents={record["source_logical_id"]:record for record in manifest.get("source_role_documents",[])}
    for node in evidence.get("source_geom_nodes",[]):
        content={key:value for key,value in node.items() if key!="source_geom_node_sha256"}
        source=sources.get(node.get("source_logical_id"),{});document=documents.get(node.get("source_logical_id"),{})
        if (node.get("source_geom_node_sha256")!=_sha(content) or node.get("source_sha256")!=source.get("sha256")
            or node.get("source_sha256")!=document.get("source_sha256")
            or node.get("source_defaults_sha256")!=_sha(document.get("source_defaults"))
            or node.get("attributes",{}).get("name")!=row["geom_name"]):
            raise ContractError("original source node evidence binding mismatch")
        previous="root.xml"
        for edge in node.get("inclusion_chain",[]):
            parent=sources.get(edge.get("source_logical_id"),{})
            if (edge.get("source_logical_id")!=previous or edge.get("source_sha256")!=parent.get("sha256")
                or {"reference":edge.get("reference"),"logical_id":edge.get("included_logical_id")} not in parent.get("includes",[])):
                raise ContractError("source role inclusion chain mismatch")
            previous=edge["included_logical_id"]
        if previous!=node["source_logical_id"]:raise ContractError("source role inclusion endpoint mismatch")
    if required:verify_role_assertion(spec,evidence)
