"""Simulation-only MuJoCo GT Room/SG bootstrap with no 5cm color-point transport.

The actual Room/SG/connection calculation stays in native nav_sg. This module
only prepares a source-bound proof for its explicit geometry-only Oracle
entrance and seals its output after independently checking GT identity, the
complete tri-state occupancy grid, entity meshes and source file hashes.

Not a generic RGB-D/perception Bundle or a source of model observations.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil

from g2.io import ContractError, canonical, digest, new_output, read_json, sha, verified_file, write_json
from g2.nav_bridge.snapshot import validate_snapshot


SCHEMA="g2_full_map_geometry_bundle_v1"
STATUS="MUJOCO_FULL_MAP_GT_PENDING_HUMAN"
MODE="SOURCE_GT_GEOMETRY_ONLY_NO_PRESCAN"


def _source_manifest(manifest):
    manifest=Path(manifest).resolve(strict=True)
    gt=read_json(manifest)
    if (gt.get("schema")!="nav_sg_mujoco_oracle_v1"
            or gt.get("scene_id") is None
            or gt.get("source_sha256")!=hashlib.sha256(
                canonical(gt.get("source_identity"))).hexdigest()
            or gt.get("state",{}).get("format")!="mujoco_fullphysics"
            or gt["state"].get("frame_id")!=0
            or gt.get("training_ready") is not False
            or not gt.get("entities")):
        raise ContractError("not an original frame0 MuJoCo Full Map GT manifest")
    files=gt.get("files",{})
    if not isinstance(files,dict) or not {"grid.txt","objects.txt"}.issubset(files):
        raise ContractError("original GT grid/object file manifest missing")
    for name in ("grid.txt","objects.txt","occupancy.raw"):
        record=files.get(name)
        if name=="occupancy.raw" and record is None:
            # Legacy oracle manifolds also bind occupancy via grid hash.
            continue
        if not isinstance(record,dict) or record.get("sha256")!=digest(manifest.parent/name):
            raise ContractError("original GT transport/source hash mismatch: "+name)
    if not isinstance(gt["state"].get("timestamp"),(int,float)):
        raise ContractError("original GT timestamp missing")
    return manifest,gt


def prepare(source_manifest,output):
    """Create a strictly source-bound, no-color native execution proof."""
    source,gt=_source_manifest(source_manifest)
    out=new_output(output,[source,source.parent])
    fields=[
        ("scene_id",gt["scene_id"]),
        ("source_sha256",gt["source_sha256"]),
        ("frame_id",str(gt["state"]["frame_id"])),
        ("world_frame","world"),
        ("native_manifest_file",str(source)),
        ("native_manifest_sha256",digest(source)),
        ("grid_sha256",digest(source.parent/"grid.txt")),
        ("objects_sha256",digest(source.parent/"objects.txt")),
        ("timestamp_ns",str(round(gt["state"]["timestamp"]*1e9))),
    ]
    out.mkdir(parents=True)
    proof="NAV_SG_FULL_MAP_GEOMETRY_ONLY_V1\n"+"".join(
        key+" "+json.dumps(str(value),ensure_ascii=False)+"\n"
        for key,value in fields)
    (out/"source_proof.txt").write_text(proof,encoding="utf-8")
    record=dict(schema="g2_full_map_geometry_only_plan_v1",
                source_manifest=str(source),
                source_manifest_sha256=digest(source),
                proof_sha256=digest(out/"source_proof.txt"),
                scene_id=gt["scene_id"],source_sha256=gt["source_sha256"],
                grid_sha256=digest(source.parent/"grid.txt"),
                objects_sha256=digest(source.parent/"objects.txt"),
                source_frame_id=0,training_ready=False,
                source_color_transport="NONE_MUJOCO_DIRECT_VISUAL_MESH")
    write_json(out/"plan.json",record)
    return record


def capture(native_directory,prepared,output):
    """Seal a native no-color Full Map snapshot, fail closed on GT mismatch."""
    native=Path(native_directory).resolve(strict=True)
    prepared=Path(prepared).resolve(strict=True)
    out=new_output(output,[native,prepared])
    plan=read_json(prepared/"plan.json")
    if (plan.get("schema")!="g2_full_map_geometry_only_plan_v1"
            or plan.get("training_ready") is not False
            or plan.get("source_color_transport")!="NONE_MUJOCO_DIRECT_VISUAL_MESH"
            or digest(prepared/"source_proof.txt")!=plan.get("proof_sha256")):
        raise ContractError("unsealed Full Map geometry-only plan/proof")
    source,gt=_source_manifest(plan["source_manifest"])
    if (digest(source)!=plan["source_manifest_sha256"]
            or digest(source.parent/"grid.txt")!=plan["grid_sha256"]
            or digest(source.parent/"objects.txt")!=plan["objects_sha256"]
            or gt["source_sha256"]!=plan["source_sha256"]
            or gt["scene_id"]!=plan["scene_id"]):
        raise ContractError("source Full Map GT proof changed")
    if (native/"SNAPSHOT_COMPLETE").read_text()!="nav_sg_spatial_snapshot_v1\n":
        raise ContractError("native geometry-only frame incomplete")
    snap=validate_snapshot(read_json(native/"snapshot.json"))
    proof=snap.get("full_map_source",{})
    if (snap.get("scene_id")!=gt["scene_id"]
            or snap.get("source_sha256")!=gt["source_sha256"]
            or snap.get("frame_id")!=0 or snap.get("world_frame")!="world"
            or snap.get("source_mode")!="full_map_mujoco_source"
            or snap.get("geometry_source_mode")!="FULL_MAP_MUJOCO_SOURCE"
            or snap.get("surface_transport_mode")!=MODE
            or snap.get("surface_color_source")!="MUJOCO_GT_VISUAL_MESH_DIRECT_ONLY"
            or snap.get("color_voxel_leaf")!=.01
            or snap.get("completed_rgbd_observations")!=0
            or snap.get("training_ready",False) is True
            or proof.get("status")!=STATUS
            or proof.get("native_geometry_backend")!="ORACLE_GRID"
            or proof.get("model_observation") is not False
            or proof.get("source_proof_sha256")!=plan["proof_sha256"]
            or proof.get("native_manifest_sha256")!=plan["source_manifest_sha256"]
            or snap.get("timestamp_ns")!=round(gt["state"]["timestamp"]*1e9)):
        raise ContractError("native snapshot has incorrect Full Map geometry-only binding")
    if (native/"surfaces.csv").read_bytes()!=(
            b"x,y,z,red,green,blue,color_valid,entity_id\n"):
        raise ContractError("Full Map no-cloud snapshot contains a point payload")
    grid=gt["grid"]
    if (snap["grid"]["origin"]!=grid["origin"]
            or snap["grid"]["dimensions"]!=grid["dims"]
            or snap["grid"]["resolution"]!=grid["resolution"]
            or (native/"grid_states.raw").read_bytes()!=(
                source.parent/"occupancy.raw").read_bytes()):
        raise ContractError("native 10cm occupancy differs from GT source")
    originals={(e["instance_id"],e["part_id"]):e for e in gt["entities"]}
    current={(e["source_instance_id"],e["source_part_id"]):e
             for e in snap["entities"]}
    if (len(current)!=len(snap["entities"]) or set(current)!=set(originals)):
        raise ContractError("Full Map native GT object identities differ")
    for identity,e in current.items():
        original=originals[identity]
        for here,there in (("kind","kind"),("source_category_id","category_id"),
                           ("source_joint_id","joint_id"),
                           ("geometry_sha256","geometry_sha256"),
                           ("vertices","vertices"),("triangles","triangles"),
                           ("bbox_min","bounds_min"),("bbox_max","bounds_max")):
            if e[here]!=original[there]:
                raise ContractError("source GT entity property changed: "+here)
    payloads={
        "snapshot.json":native/"snapshot.json",
        "grid_states.raw":native/"grid_states.raw",
        "surfaces.csv":native/"surfaces.csv",  # header only, never a cloud
        "SNAPSHOT_COMPLETE":native/"SNAPSHOT_COMPLETE",
        "source_gt_manifest.json":source,
        "source_proof.txt":prepared/"source_proof.txt",
    }
    info={k:{"path":k,"sha256":digest(v),"bytes":v.stat().st_size}
          for k,v in payloads.items()}
    out.mkdir(parents=True)
    for name,path in payloads.items():
        shutil.copyfile(path,out/name)
        verified_file(out,info[name])
    result={k:snap[k] for k in (
        "scene_id","source_sha256","frame_id","timestamp_ns",
        "world_frame","source_mode","native_build_source_sha256",
        "geometry_source_mode")}
    result.update(schema=SCHEMA,
                  source_scope={"status":STATUS,
                                "full_scene_source_certified":False},
                  surface_transport_mode=MODE,surface_points=0,
                  semantic_stage="MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS",
                  structural_stage="SOURCE_GT_NATIVE_ROOM_GRAPH",
                  files=info,training_ready=False)
    result["version_sha256"]=hashlib.sha256(canonical(result)).hexdigest()
    write_json(out/"bundle.json",result)
    (out/"BUNDLE_COMPLETE").write_text("SOURCE_BOUND_NATIVE_SNAPSHOT\n")
    return result
