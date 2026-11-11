"""Source coverage evidence; a subset transport marker never certifies a house.

Reviews are explicit external assertions bound to exact artifacts, not a
cryptographic attestation or an automated human/GT acceptance decision.
"""
from collections import Counter
from datetime import datetime
import hashlib
import shlex
from pathlib import Path
from g2.io import ContractError, canonical, digest, read_json, sha, verified_file

DECLARED_SCOPE = "DECLARED_VISUAL_GEOMS_ONLY"
REVIEWED_SCOPE = "REVIEWED_FULL_SCENE_SOURCE"
SUBSET_SCOPE = "DECLARED_SUBSET_NOT_CERTIFIED"
EVIDENCE_MANIFEST = "source_evidence/manifest.json"
EVIDENCE_REVIEW = "source_evidence/review.json"
EVIDENCE_CLOUD = "source_evidence/precolored.txt"
EVIDENCE_COLOR_AUDIT = "source_evidence/color_audit.npz"
EVIDENCE_FILES = {EVIDENCE_MANIFEST, EVIDENCE_REVIEW, EVIDENCE_CLOUD}


def text(value):
    return isinstance(value,str) and bool(value.strip()) and not any(ord(c)<32 for c in value)


def audit_summary(rows):
    if not isinstance(rows,list) or not rows:
        raise ContractError("nonempty complete geom audit required")
    roles=Counter();colors=Counter();categories=Counter();modes=Counter();reasons=Counter();unsupported=Counter()
    valid_points=0;points=0;eligibility=[]
    for row in rows:
        if not isinstance(row,dict):raise ContractError("invalid geom audit row")
        role=row.get("role");status=row.get("color_status");n=row.get("surface_points")
        source=row.get("source",{})
        if (role not in ("visual","collision","robot","auxiliary","UNCLASSIFIED") or not isinstance(source,dict)
            or source.get("kind") not in ("mjcf","ep_meta","unclassified")
            or ((role=="UNCLASSIFIED")!=(source.get("kind")=="unclassified")) or type(n) is not int or n<0
            or (role=="visual" and (status not in ("VALID","UNSUPPORTED_APPEARANCE","TRANSPARENT")
                or (n==0)!=(status=="TRANSPARENT")))
            or (role!="visual" and (status!="EXCLUDED_"+role.upper() or n!=0))):
            raise ContractError("invalid geom role/color audit")
        roles[role]+=1;colors[status]+=1
        if role=="UNCLASSIFIED":eligibility.append({"geom_id":row["geom_id"],"reason":"UNCLASSIFIED_SOURCE_ROLE"})
        if source.get("category"):
            categories[canonical(source["category"]).decode()]+=1
        if not text(row.get("classification_reason")):
            eligibility.append({"geom_id":row["geom_id"],"reason":"MISSING_CLASSIFICATION_REASON"})
        if source["kind"]=="ep_meta" and source.get("body_binding",{}).get("status")!="VERIFIED":
            eligibility.append({"geom_id":row["geom_id"],"reason":"OFFICIAL_SOURCE_BODY_UNVERIFIED"})
        points+=n
        coverage=row.get("color_coverage")
        if coverage is not None:
            if not isinstance(coverage,dict):raise ContractError("invalid sampled color coverage")
            valid=coverage.get("color_valid_points")
            if (type(valid) is not int or not 0<=valid<=n or coverage.get("sampled_points")!=n
                or coverage.get("color_invalid_points")!=n-valid or (status=="VALID" and valid!=n)):
                raise ContractError("inconsistent sampled color coverage")
            valid_points+=valid
        elif status=="VALID":valid_points+=n
        appearance=row.get("appearance",{})
        if appearance:modes[appearance["mode"]]+=1
        if status=="UNSUPPORTED_APPEARANCE":
            unsupported[row.get("geometry_type","unknown")]+=1
            reason=appearance.get("unsupported") or appearance.get("reason") or appearance.get("mode")
            reasons[str(reason)]+=1
            eligibility.append({"geom_id":row["geom_id"],"reason":"UNSUPPORTED_APPEARANCE"})
    return {"compiled_geoms":len(rows),"role_counts":dict(roles),"color_status_counts":dict(colors),
            "category_provenance_counts":dict(categories),"appearance_mode_counts":dict(modes),
            "invalid_color_reason_counts":dict(reasons),"surface_points":points,
            "color_valid_points":valid_points,"color_valid_fraction":valid_points/points if points else 0,
            "color_valid_fraction_basis":"DECLARED_SAMPLED_SURFACE_POINTS_ONLY",
            "unsupported_visual_geom_fraction":colors["UNSUPPORTED_APPEARANCE"]/roles["visual"] if roles["visual"] else 0,
            "unsupported_geometry_type_counts":dict(unsupported),
            "full_scene_review_eligible":bool(points) and not eligibility,
            "review_blockers":eligibility,"full_scene_source_certified":False}


def verify_full_scene_review(manifest_path, review_path):
    """Validate a server-local source/role/material review; never infer one."""
    if review_path is None:
        raise ContractError("BLOCKED_FULL_SCENE_SOURCE_REVIEW: COMPLETE covers declared surfaces only")
    m=read_json(manifest_path);r=read_json(review_path)
    rows=m.get("geom_audit")
    if (m.get("schema")!="g2_prescan_manifest_v1" or m.get("status")!="COMPLETE"
        or m.get("completion_scope")!=DECLARED_SCOPE or not isinstance(rows,list) or not rows
        or type(m.get("compiled_geom_count")) is not int or len(rows)!=m["compiled_geom_count"]
        or any(not isinstance(row,dict) or type(row.get("geom_id")) is not int
               or not text(row.get("geom_name")) for row in rows)
        or [row["geom_id"] for row in rows]!=list(range(len(rows)))
        or len({row["geom_name"] for row in rows})!=len(rows)
        or type(m.get("frame_id")) is not int or m["frame_id"]<0):
        raise ContractError("invalid complete geom inventory for full-scene review")
    expected=hashlib.sha256(canonical(rows)).hexdigest()
    summary=audit_summary(rows)
    identity=m.get("source_identity",{})
    if not isinstance(identity,dict):raise ContractError("invalid visual source identity")
    declared=identity.get("metadata",{}).get("geoms",{})
    if (identity.get("schema")!="g2_prescan_source_v1"
        or hashlib.sha256(canonical(identity)).hexdigest()!=sha(m.get("visual_source_sha256"))
        or identity.get("metadata",{}).get("scene_id")!=m.get("scene_id")
        or identity.get("world_frame")!=m.get("world_frame")
        or type(m.get("state",{}).get("frame_id")) is not int
        or m.get("state",{}).get("frame_id")!=m["frame_id"]
        or not isinstance(declared,dict) or set(declared)!={row["geom_name"] for row in rows}
        or any(not isinstance(spec,dict) for spec in declared.values())
        or any(declared[row["geom_name"]].get("role")!=row["role"] for row in rows)
        or summary["surface_points"]!=m.get("point_count")):
        raise ContractError("full-scene audit does not match source identity or point count")
    from .prescan import source_binding
    from .source_geometry import model_source_hash
    from .source_roles import verify_embedded_role_evidence
    if model_source_hash(m.get("sources",[]))!=identity.get("model_source_sha256"):
        raise ContractError("complete asset closure differs from original source identity")
    for row in rows:
        spec=declared[row["geom_name"]]
        ancestry=row.get("body_ancestry")
        if not isinstance(ancestry,list) or not ancestry or any(not isinstance(body,dict) for body in ancestry):
            raise ContractError("actual geom body ancestry missing")
        body_names=[body.get("body_name") for body in ancestry
                    if spec.get("source_kind")=="mjcf" or body.get("body_id")!=0]
        binding=source_binding(spec,row["geom_name"],identity.get("ep_meta"),body_names=body_names)
        if row["source"]!=binding or row.get("classification_reason")!=spec.get("classification_reason"):
            raise ContractError("geom audit contradicts original source identity or classification")
        verify_embedded_role_evidence(m,row,spec)
    sha(m.get("source_sha256"))
    if m.get("file",{}).get("path")!="precolored.txt":
        raise ContractError("unexpected pre-scan transport path")
    cloud=verified_file(Path(manifest_path).parent,m["file"])
    with cloud.open(encoding="utf-8") as stream:
        if stream.readline().strip()!="NAV_SG_PRECOLORED_CLOUD_V1":
            raise ContractError("invalid reviewed source transport magic")
        for key in ("scene_id","source_sha256","frame_id","world_frame","points"):
            fields=shlex.split(stream.readline())
            expected_value=str(m["point_count"] if key=="points" else m[key])
            if fields!=[key,expected_value]:
                raise ContractError("reviewed source transport header mismatch: "+key)
        if stream.readline().strip()!="data":raise ContractError("invalid source data header")
    from .color_evidence import verify_color_evidence
    color_evidence_sha=verify_color_evidence(Path(manifest_path).parent,m,cloud)
    if sha(m.get("geom_audit_sha256"))!=expected or not summary["full_scene_review_eligible"]:
        raise ContractError("full-scene source inventory is unverified or incomplete")
    if (r.get("schema")!="g2_full_scene_source_review_v1" or r.get("decision")!="APPROVED"
        or r.get("scope")!="FULL_SCENE_SOURCE" or r.get("review_kind")!="SOURCE_ROLE_AND_MATERIAL_REVIEW"
        or not text(r.get("reviewer")) or not text(r.get("reviewed_utc"))
        or type(r.get("frame_id")) is not int):
        raise ContractError("explicit full-scene source review required")
    try:
        stamp=datetime.fromisoformat(r["reviewed_utc"].replace("Z","+00:00"))
        if stamp.utcoffset() is None:raise ValueError("timezone missing")
    except ValueError as error:
        raise ContractError("source review time must include a timezone") from error
    for key,value in {"manifest_sha256":digest(manifest_path),"scene_id":m["scene_id"],
                      "source_sha256":m["source_sha256"],"visual_source_sha256":m["visual_source_sha256"],
                      "geom_audit_sha256":expected,"frame_id":m["frame_id"]}.items():
        if r.get(key)!=value:raise ContractError("full-scene review belongs to another artifact: "+key)
    return {"status":REVIEWED_SCOPE,"review_sha256":digest(review_path),
            **({"color_audit_sha256":color_evidence_sha} if color_evidence_sha else {}),
            "manifest_sha256":digest(manifest_path),"geom_audit_sha256":expected,
            "scene_id":m["scene_id"],"source_sha256":m["source_sha256"],
            "world_frame":m["world_frame"],
            "visual_source_sha256":m["visual_source_sha256"],"reference_frame_id":m["frame_id"],
            "reviewer":r["reviewer"],"reviewed_utc":r["reviewed_utc"],
            "meaning":"EXTERNAL_SOURCE_REVIEW_ASSERTION_NOT_TRAINING_OR_HUMAN_VIEW_ACCEPTANCE"}


def verify_sealed_scope(root, bundle):
    """Re-read sealed evidence rather than trusting a scope field in a run/bundle."""
    packet=bundle.get("source_scope",{})
    if not isinstance(packet,dict):raise ContractError("invalid sealed source scope")
    if packet.get("status")!=REVIEWED_SCOPE:
        return
    if bundle.get("source_mode")!="perception":
        raise ContractError("ordinary source review cannot promote oracle geometry")
    if not EVIDENCE_FILES.issubset(bundle.get("files",{})):
        raise ContractError("reviewed source scope lacks sealed source evidence")
    proof=verify_full_scene_review(Path(root)/EVIDENCE_MANIFEST,Path(root)/EVIDENCE_REVIEW)
    source=read_json(Path(root)/EVIDENCE_MANIFEST)
    witness=bundle.get("observation_witness") or {}
    binding=witness.get("prescan_source_binding") or {}
    if not isinstance(binding,dict):raise ContractError("invalid original native source binding")
    if (proof!=packet or proof["scene_id"]!=bundle.get("scene_id")
        or proof["source_sha256"]!=bundle.get("source_sha256") or proof["reference_frame_id"]!=0
        or proof["world_frame"]!=bundle.get("world_frame")
        or proof["visual_source_sha256"]!=binding.get("visual_source_sha256")
        or source["file"]["sha256"]!=binding.get("prescan_cloud_sha256")):
        raise ContractError("sealed source evidence differs from actual initial native input")
