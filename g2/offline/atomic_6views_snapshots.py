"""Reconstruct native-source-bound 2 Hz RoboCasa spatial snapshots per episode.

Every state uses its own ORIGINAL MuJoCo FULLPHYSICS row; static Room footprint
and reference axes are copied from the current episode's native nav_sg frame 0
(not from another layout or episode). Object/root bboxes and meshes are updated
from actual source GT; Room/Island affiliations use the independently
cross-checked nav_sg C++ connection semantics, not a scene-specific classifier.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np

from g2.io import ContractError, read_json, write_json
from g2.nav_bridge.connections import verify_connection_evidence
from g2.nav_bridge.snapshot import validate_snapshot
from .atomic_6views_connections import compute


def source_sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):
            h.update(block)
    return h.hexdigest()


def reference(path):
    p=Path(path).resolve(strict=True)
    if not p.is_file():
        raise ContractError("required source reference is not a regular file")
    return {"path":str(p), "sha256":source_sha(p)}


def _native_source(nav_repo):
    source=Path(nav_repo).resolve(strict=True)/"g2/gt/mujoco_scene.py"
    if not source.is_file():
        raise ContractError("nav_sg native GT source unavailable")
    name="_g2_atomic_native_oracle_source"
    spec=importlib.util.spec_from_file_location(name,source)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


def _state_summary(snapshot, row, frame, source_sha, ns):
    """Summarize geometry-bound entity/room relationships; no inferred contact."""
    entities=[]
    for e in snapshot["entities"]:
        entities.append({
            "id":e["id"], "source_instance_id":e["source_instance_id"],
            "source_category_id":e["source_category_id"],
            "source_part_id":e["source_part_id"],
            "kind":e["kind"], "label":e["label"],
            "room_uid":e["room_uid"], "bbox_min":e["bbox_min"],
            "bbox_max":e["bbox_max"],
            "centroid":[(a+b)*.5 for a,b in zip(e["bbox_min"],e["bbox_max"])],
            "root_affiliations":e["root_affiliations"],
            "floor_member":e["floor_member"], "upper_member":e["upper_member"],
            "island_id":e["island_id"],
        })
    return {
        "schema":"g2_robocasa_original_source_spatial_scene_graph_v1",
        "scene_id":snapshot["scene_id"],
        "source_sha256":source_sha,
        "frame_id":frame,
        "timestamp_ns":ns,
        "original_state_row_sha256":hashlib.sha256(
            np.asarray(row,dtype="<f8").tobytes()).hexdigest(),
        "room_source":"CURRENT_EPISODE_NATIVE_NAV_SG_FRAME0_ROOM",
        "room_footprint_update_policy":"STATIC_KITCHEN_GEOMETRY_ROOM_REFERENCE",
        "semantic_on_inside":"NOT_OBSERVABLE_FROM_SOURCE_BBOX",
        "rooms":[{
            "uid":r["uid"],"center":r["center"],"label":r["label"],
            "footprint_cell_count":len(r["footprint"]),
        } for r in snapshot["rooms"]],
        "entities":entities,
        "connections":snapshot["connections"],
        "relations":snapshot["relations"],
        "training_ready":False,
    }


def generate(base_snapshot, source_manifest, frames, *,
             nav_repo, role_map, visual_inventory, bundle_manifest,
             layout_id, output):
    import mujoco
    if not isinstance(frames,list) or len(frames)<2 or frames[0]!=0 or frames!=sorted(set(frames)):
        raise ContractError("source frames must be distinct increasing and start at zero")
    out=Path(output)
    if out.exists() or out.is_symlink():
        raise ContractError("snapshot output already exists; do not overwrite")
    base=validate_snapshot(read_json(base_snapshot))
    gt=read_json(source_manifest)
    if (gt.get("schema")!="nav_sg_mujoco_oracle_v1"
            or gt.get("scene_id")!=base["scene_id"]
            or gt.get("source_sha256")!=base["source_sha256"]
            or gt.get("state",{}).get("frame_id")!=0):
        raise ContractError("native frame0 source and snapshot identity mismatch")
    identity=gt["source_identity"]
    if identity["mujoco_version"]!=mujoco.__version__:
        raise ContractError("MuJoCo source build runtime differs")
    # Reuse the exact opt-in collision topology policy recorded in the native
    # frame-0 source identity. Otherwise later GT frames diverge or fail on
    # the original zero-area triangle.
    repair_policy=identity.get("collision_mesh_repair_policy")
    if repair_policy not in (None,"exact_collinear_edge_v1"):
        raise ContractError("unsupported collision mesh repair policy in native source identity")
    oracle=_native_source(nav_repo)
    sources=gt["sources"]
    root=next(x["path"] for x in sources if x["logical_id"]=="root.xml")
    model,loaded=oracle.load_model(root,[Path(s["path"]).parent for s in sources])
    if oracle.model_source_hash(loaded)!=identity["model_source_sha256"]:
        raise ContractError("loaded source assets changed")
    state=gt["state"]
    with np.load(state["path"],allow_pickle=False) as npz:
        if "states" not in npz:
            raise ContractError("source FULLPHYSICS state archive missing")
        rows=npz["states"]
    expected=mujoco.mj_stateSize(model,mujoco.mjtState.mjSTATE_FULLPHYSICS)
    if rows.ndim!=2 or rows.shape[1]!=expected or frames[-1]>=len(rows):
        raise ContractError("source frame count or dimensions differ")
    ref_by_key={(r["source_instance_id"],r["source_part_id"]):r for r in base["entities"]}
    if len(ref_by_key)!=len(base["entities"]):
        raise ContractError("native source instance key must be unique")
    far=oracle.Grid((1,1,1),(1e8,1e8,1e8),float(gt["grid"]["resolution"]))
    out.mkdir(parents=True)
    states_dir=out/"snapshots"
    graphs_dir=out/"scene_graph"
    states_dir.mkdir()
    graphs_dir.mkdir()
    sequence=[]
    data=mujoco.MjData(model)
    timer=time.monotonic()
    for i,frame in enumerate(frames):
        before=time.monotonic()
        row=rows[frame]
        mujoco.mj_setState(model,data,row,mujoco.mjtState.mjSTATE_FULLPHYSICS)
        mujoco.mj_forward(model,data)
        _,actual,_,_=oracle.extract(
            model,data,far,identity["metadata"],None,identity["geometry"],
            include_surfaces=False,
            repair_exact_collinear_collision=(repair_policy=="exact_collinear_edge_v1"))
        now={(r["instance_id"],r["part_id"]):r for r in actual}
        if set(now)!=set(ref_by_key):
            raise ContractError("current GT entity roster differs from native frame0")
        snap=copy.deepcopy(base)
        snap["frame_id"]=frame
        snap["timestamp_ns"]=round(float(row[0])*1e9)
        snap["geometry_update_sequence"]=i
        changed=0
        for entity in snap["entities"]:
            source=now[(entity["source_instance_id"],entity["source_part_id"])]
            if any(entity[key]!=source[skey] for key,skey in (
                    ("kind","kind"),("geometry_sha256","geometry_sha256"),
                    ("source_joint_id","joint_id"),
                    ("source_category_id","category_id"))):
                raise ContractError("original geometry or source semantics changed")
            previous=(entity["bbox_min"],entity["bbox_max"])
            entity["vertices"]=source["vertices"]
            entity["triangles"]=source["triangles"]
            entity["bbox_min"]=source["bounds_min"]
            entity["bbox_max"]=source["bounds_max"]
            if previous!=(entity["bbox_min"],entity["bbox_max"]):
                changed+=1
        snap["connections"],snap["entities"],snap["affiliations_complete"]=compute(
            snap["entities"],[r["uid"] for r in snap["rooms"]],
            connection_distance=snap["connection_distance"],known=True)
        verify_connection_evidence(snap)
        validate_snapshot(snap)
        if frame == 0:
            # The first frame is the EXACT source-proved native bundle.
            # Re-encoding/rederiving it would change snapshot SHA and make
            # _view_manifest reject the current native frame0 binding.
            for a,b in zip(snap["entities"],base["entities"]):
                if any(a[key]!=b[key] for key in
                       ("bbox_min","bbox_max","kind","source_instance_id","source_part_id")):
                    raise ContractError("original native frame0 entity geometry differs")
            snap=copy.deepcopy(base)
            snapshot_ref=reference(base_snapshot)
        else:
            snapshot_path=states_dir/f"frame_{frame:06d}.json"
            write_json(snapshot_path,snap)
            snapshot_ref=reference(snapshot_path)
        graph_path=graphs_dir/f"frame_{frame:06d}.json"
        write_json(graph_path,_state_summary(
            snap,row,frame,gt["source_sha256"],snap["timestamp_ns"]))
        sequence.append({
            "frame":frame,"snapshot":snapshot_ref,
            "scene_graph":reference(graph_path),
            "bundle_manifest":reference(bundle_manifest),
        })
        print(f"G2_SNAPSHOT state={i+1}/{len(frames)} frame={frame} "
              f"source_gt_entities={len(actual)} changed={changed} "
              f"rooms={len(snap['rooms'])} "
              f"islands={len({e['island_id'] for e in snap['entities'] if e['island_id']})} "
              f"elapsed_s={time.monotonic()-before:.2f}",flush=True)
    config={
        "schema":"g2_direct_color_episode_inputs_v1",
        "layout":layout_id,
        "source_manifest":reference(source_manifest),
        "role_map":reference(role_map),
        "visual_inventory":reference(visual_inventory),
        "states":sequence,
    }
    input_file=out/"episode_inputs.json"
    write_json(input_file,config)
    report={
        "schema":"g2_atomic_native_gt_dynamic_snapshot_v1",
        "complete":True,"training_ready":False,
        "scene_id":gt["scene_id"],"source_sha256":gt["source_sha256"],
        "state_count":len(frames),"frames":frames,
        "episode_inputs":str(input_file),"episode_inputs_sha256":source_sha(input_file),
        "room_footprints_reused_from_current_episode_native_frame0":True,
        "entity_geometry_rederived_per_frame":True,
        "elapsed_s":round(time.monotonic()-timer,2),
    }
    write_json(out/"COMPLETE.json",report)
    return report


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base-snapshot",required=True)
    p.add_argument("--source-manifest",required=True)
    p.add_argument("--frames",required=True,
                   help="JSON array of selected original 20Hz frame IDs")
    p.add_argument("--nav-repo",required=True)
    p.add_argument("--role-map",required=True)
    p.add_argument("--visual-inventory",required=True)
    p.add_argument("--bundle-manifest",required=True)
    p.add_argument("--layout-id",type=int,required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args(argv)
    print(json.dumps(generate(
        args.base_snapshot,args.source_manifest,json.loads(args.frames),
        nav_repo=args.nav_repo,role_map=args.role_map,
        visual_inventory=args.visual_inventory,
        bundle_manifest=args.bundle_manifest,
        layout_id=args.layout_id,output=args.output),
        ensure_ascii=False,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
