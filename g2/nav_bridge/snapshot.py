"""Seal actual native nav_sg snapshots; never cluster Rooms or Islands in G2."""
import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
import shutil
from g2.io import parse_json
from g2.io import ContractError, canonical, digest, new_output, read_json, sha, write_json, verified_file

ENTITY = re.compile(r"entity_[0-9]+\Z")


def vector(value, name):
    if not isinstance(value,list) or len(value)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in value):
        raise ContractError("invalid finite vector: "+name)
    return value


def validate_snapshot(s):
    if s.get("schema")!="nav_sg_spatial_snapshot_v1":
        raise ContractError("unsupported native snapshot schema")
    sha(s.get("source_sha256"));sha(s.get("native_build_source_sha256"))
    if (not isinstance(s.get("scene_id"),str) or not s["scene_id"] or
            not isinstance(s.get("world_frame"),str) or not s["world_frame"]):
        raise ContractError("missing scene/world identity")
    for k in ("frame_id","timestamp_ns","completed_rgbd_observations"):
        if type(s.get(k)) is not int or s[k]<0:
            raise ContractError("invalid native "+k)
    if s.get("source_mode") not in ("perception","oracle_diagnostic"):
        raise ContractError("native source mode must be explicit")
    if type(s.get("affiliations_complete")) is not bool:
        raise ContractError("native affiliation status required")
    lo,hi=vector(s.get("bounds_min"),"bounds_min"),vector(s.get("bounds_max"),"bounds_max")
    if any(b<a for a,b in zip(lo,hi)):
        raise ContractError("invalid native bounds")
    leaf=s.get("color_voxel_leaf")
    if type(leaf) not in (float,int) or not math.isfinite(leaf) or leaf<=0:
        raise ContractError("native actual color voxel size required")
    grid=s.get("grid",{})
    vector(grid.get("origin"),"grid origin")
    resolution=grid.get("resolution")
    if type(resolution) not in (float,int) or not math.isfinite(resolution) or resolution<=0:
        raise ContractError("invalid native grid resolution")
    dims=grid.get("dimensions")
    if not isinstance(dims,list) or len(dims)!=3 or any(type(n) is not int or n<=0 for n in dims) or math.prod(dims)>10_000_000:
        raise ContractError("invalid native grid dimensions")
    if grid.get("state_file")!="grid_states.raw" or grid.get("state_order")!="xyz_z_fastest" or grid.get("states")!={"unknown":0,"free":1,"occupied":2}:
        raise ContractError("native tri-state grid encoding required")
    rooms=s.get("rooms");entities=s.get("entities")
    if not isinstance(rooms,list) or not rooms or len(rooms)>1000 or not isinstance(entities,list) or len(entities)>6000:
        raise ContractError("invalid native Rooms/entities")
    room_ids=set()
    for r in rooms:
        uid=r.get("uid")
        if type(uid) is not int or uid<0 or uid in room_ids:
            raise ContractError("duplicate/invalid native Room UID")
        room_ids.add(uid);vector(r.get("center"),"Room center")
        if r.get("frame_axes")!="world_axes":
            raise ContractError("unsupported Room frame; do not guess a wall-aligned axis")
    by_id={}
    for e in entities:
        name=e.get("id")
        if (not isinstance(name,str) or not ENTITY.fullmatch(name) or name in by_id
                or type(e.get("native_id")) is not int or name!="entity_"+str(e["native_id"])
                or e.get("kind") not in ("object","floor","wall","ceiling")):
            raise ContractError("invalid/duplicate native entity identity")
        a,b=vector(e.get("bbox_min"),"entity min"),vector(e.get("bbox_max"),"entity max")
        if any(y<x for x,y in zip(a,b)):
            raise ContractError("invalid entity bounds")
        if e.get("room_uid") not in room_ids | {-1}:
            raise ContractError("entity references absent native Room")
        for k in ("floor_member","upper_member"):
            if type(e.get(k)) is not bool:
                raise ContractError("native membership boolean missing")
        vertices=e.get("vertices",[]);triangles=e.get("triangles",[])
        if not isinstance(vertices,list) or not isinstance(triangles,list) or len(vertices)>2_000_000 or len(triangles)>4_000_000:
            raise ContractError("native mesh budget/arrays invalid")
        for vertex in vertices:vector(vertex,"native mesh vertex")
        for tri in triangles:
            if not isinstance(tri,list) or len(tri)!=3 or any(type(v) is not int or not 0<=v<len(vertices) for v in tri):
                raise ContractError("invalid native triangle indices")
        by_id[name]=e
    for e in entities:
        roots=e.get("root_affiliations")
        if not isinstance(roots,list) or len(set(roots))!=len(roots):
            raise ContractError("invalid native affiliation references")
        if any(r not in by_id or by_id[r]["kind"]=="object" for r in roots):
            raise ContractError("affiliation must refer to native structural roots")
        if e.get("island_id") is not None and (not isinstance(e["island_id"],str) or e["kind"]!="object" or e["room_uid"]<0):
            raise ContractError("invalid native Island reference")
        if e.get("island_id") and (not s["affiliations_complete"] or any(by_id[r]["kind"]=="wall" for r in roots)):
            raise ContractError("Island cannot be invented from unknown/wall membership")
    nodes=set(by_id) | {"room_"+str(uid) for uid in room_ids}
    if s.get("building"):
        if s["building"].get("id")!="building_0":raise ContractError("invalid native Building ID")
        nodes.add("building_0")
    if s.get("geometry_source_mode") not in ("ORACLE_GRID","PRESCAN_PREBUILT","SENSOR_INCREMENTAL"):
        raise ContractError("native geometry source must be explicit")
    if (s["source_mode"]=="perception") == (s["geometry_source_mode"]=="ORACLE_GRID"):
        raise ContractError("native oracle/perception geometry mode conflict")
    relations=s.get("relations")
    if not isinstance(relations,list):
        raise ContractError("native relation list missing")
    for r in relations:
        if r.get("source") not in nodes or r.get("target") not in nodes:
            raise ContractError("native relation has dangling endpoints")
    if s.get("surface_file")!="surfaces.csv":
        raise ContractError("unexpected native surface path")
    return s


def iter_surfaces(path, entities, max_points=5_000_000):
    expected=["x","y","z","red","green","blue","color_valid","entity_id"]
    with Path(path).open(encoding="utf-8",newline="") as stream:
        reader=csv.reader(stream,strict=True)
        if next(reader,None)!=expected:
            raise ContractError("native surface header mismatch")
        count=0
        for row in reader:
            count+=1
            if len(row)!=8 or count>max_points:
                raise ContractError("surface fields/point budget exceeded")
            try:
                xyz=[float(x) for x in row[:3]]
                if any(not re.fullmatch(r"[0-9]+",x) for x in row[3:7]):
                    raise ValueError("integer colors required")
                rgb=[int(x) for x in row[3:6]];valid=int(row[6])
            except ValueError as error:
                raise ContractError("invalid surface number") from error
            if (not all(math.isfinite(x) and abs(x)<1e9 for x in xyz) or
                    any(x>255 for x in rgb) or valid not in (0,1) or
                    row[7] not in entities | {"unknown"}):
                raise ContractError("invalid surface coordinates/color/mask/entity")
            yield (*xyz,*rgb,valid,row[7])
        if not count:
            raise ContractError("empty native surface cloud")


def observation_witness(run_path,snapshot):
    """Read existing genuine N3 replay proof, selecting only the exact frame."""
    run_path=Path(run_path)
    run=read_json(run_path)
    if (run.get("schema")!="nav_sg_g2_native_semantic_run_v1" or
            run.get("execution_kind")!="ros1_native" or run.get("spatial_profile")!="G2_N6_RECORDED" or
            run.get("model_runtime")!="recorded_model_prediction"):
        raise ContractError("ordinary perception requires genuine native recorded RGB-D/model run")
    binding=run.get("prescan_recorded_binding")
    if binding:
        if (binding.get("scene_id")!=snapshot["scene_id"] or binding.get("source_sha256")!=snapshot["source_sha256"]
            or binding.get("episode")!=run.get("episode") or binding.get("camera")!=run.get("camera")
            or binding.get("recorded_manifest_sha256")!=run.get("source_digests",{}).get("manifest.json")
            or binding.get("recorded_frames_sha256")!=run.get("source_digests",{}).get("frames.jsonl")):
            raise ContractError("prescan/recorded dataset witness mismatch")
    elif snapshot["scene_id"]!=run.get("episode") or snapshot["source_sha256"]!=run.get("source_digests",{}).get("manifest.json"):
        raise ContractError("recorded-only scene identity mismatch")
    audit=run_path.parent/"native_semantic_audit.jsonl"
    if digest(audit)!=run.get("audit_sha256"):
        raise ContractError("native semantic audit hash mismatch")
    selected=[]
    with audit.open(encoding="utf-8") as stream:
        for line in stream:
            if len(line)>64*1024*1024:
                raise ContractError("oversized native audit row")
            row=parse_json(line)
            if row.get("frame_index")==snapshot["frame_id"]:
                selected.append(row)
    if len(selected)!=1:
        raise ContractError("exact native semantic frame missing/duplicated")
    row=selected[0]
    if (row.get("schema")!="nav_sg_native_semantic_audit_v1" or row.get("semantic_success") is not True
            or row.get("stamp_ns")!=snapshot["timestamp_ns"]
            or row.get("pose_stamp_ns")!=row["stamp_ns"]
            or row.get("camera_stamp_ns")!=row["stamp_ns"]
            or row.get("world_frame_id")!=snapshot["world_frame"]):
        raise ContractError("native RGB-D/pose/semantic snapshot is stale or mismatched")
    for key in ("scene_id","source_sha256","native_build_source_sha256"):
        if row.get(key)!=snapshot[key]:
            raise ContractError("native semantic audit belongs to another scene/source/build")
    native_objects={e["native_id"]:e for e in snapshot["entities"] if e["kind"]=="object"}
    audit_objects={n["native_cluster_id"]:n for n in row.get("scene_graph",{}).get("nodes",[])
                   if n.get("type")=="object"}
    if set(native_objects)!=set(audit_objects):
        raise ContractError("native semantic object IDs do not match spatial snapshot")
    clusters={c["native_cluster_id"]:c for c in row.get("clusters",[])}
    for key,e in native_objects.items():
        c=clusters.get(key,{})
        if c.get("room_uid")!=e["room_uid"] or any(c.get(k+"_world")!=e[k] for k in ("bbox_min","bbox_max")):
            raise ContractError("native semantic geometry/Room assignment differs from snapshot")
    return {"run_sha256":digest(run_path),"audit_sha256":digest(audit),"frame_id":row["frame_index"],
            "stamp_ns":row["stamp_ns"],"episode":run.get("episode"),"camera":run.get("camera"),
            "model_runtime":run["model_runtime"]}


def capture(native_directory,output,*,native_run=None,allow_oracle_diagnostic=False,
            expected_build_source_sha256=None):
    native=Path(native_directory).resolve()
    out=new_output(output,[native])
    marker=native/"SNAPSHOT_COMPLETE"
    if marker.read_text()!="nav_sg_spatial_snapshot_v1\n":
        raise ContractError("native snapshot has no valid completion marker")
    s=validate_snapshot(read_json(native/"snapshot.json"))
    if expected_build_source_sha256 and s["native_build_source_sha256"]!=sha(expected_build_source_sha256):
        raise ContractError("native build source mismatch")
    witness=None
    if s["source_mode"]=="oracle_diagnostic":
        if not allow_oracle_diagnostic:
            raise ContractError("oracle snapshot forbidden in normal perception; explicit diagnostic opt-in required")
        if native_run:
            raise ContractError("oracle source cannot be relabelled by adding RGB-D evidence")
    else:
        if (not native_run or s["completed_rgbd_observations"]<1 or s["object_frontend_status"]!="OBSERVED"):
            raise ContractError("BLOCKED_REAL_RGBD_OBSERVATIONS")
        witness=observation_witness(native_run,s)
    files={}
    for name in ("snapshot.json","surfaces.csv","grid_states.raw","SNAPSHOT_COMPLETE"):
        p=native/name
        if p.is_symlink() or not p.is_file():
            raise ContractError("native snapshot files must be regular files")
        files[name]={"path":name,"bytes":p.stat().st_size,"sha256":digest(p)}
    grid_bytes=(native/"grid_states.raw").read_bytes()
    if len(grid_bytes)!=math.prod(s["grid"]["dimensions"]) or any(value>2 for value in grid_bytes):
        raise ContractError("invalid actual native tri-state occupancy grid")
    count=sum(1 for _ in iter_surfaces(native/"surfaces.csv",{e["id"] for e in s["entities"]}))
    out.mkdir(parents=True)
    for name,record in files.items():
        shutil.copyfile(native/name,out/name)
        verified_file(out,record)
        if digest(native/name)!=record["sha256"]:
            raise ContractError("native snapshot changed during capture")
    manifest={"schema":"g2_native_bundle_v1","scene_id":s["scene_id"],"source_sha256":s["source_sha256"],
              "frame_id":s["frame_id"],"timestamp_ns":s["timestamp_ns"],"world_frame":s["world_frame"],
              "native_build_source_sha256":s["native_build_source_sha256"],"source_mode":s["source_mode"],
              "geometry_source_mode":s["geometry_source_mode"],
              "files":files,"surface_points":count,"observation_witness":witness,
              "semantic_stage":"ORACLE_DIAGNOSTIC" if witness is None else "REAL_RECORDED_INPUT_OBSERVED",
              "structural_stage":"AVAILABLE" if s["affiliations_complete"] else "BLOCKED_NATIVE_WALL_ROOTS",
              "training_ready":False}
    manifest["version_sha256"]=hashlib.sha256(canonical(manifest)).hexdigest()
    write_json(out/"bundle.json",manifest)
    (out/"BUNDLE_COMPLETE").write_text("SOURCE_BOUND_NATIVE_SNAPSHOT\n")
    return manifest


def load_bundle(directory):
    root=Path(directory)
    if (root/"BUNDLE_COMPLETE").read_text()!="SOURCE_BOUND_NATIVE_SNAPSHOT\n":
        raise ContractError("incomplete native bundle")
    manifest=read_json(root/"bundle.json")
    expected=manifest.pop("version_sha256",None)
    if hashlib.sha256(canonical(manifest)).hexdigest()!=sha(expected):
        raise ContractError("bundle identity hash mismatch")
    manifest["version_sha256"]=expected
    if type(manifest.get("surface_points")) is not int or not 0<manifest["surface_points"]<=5_000_000:
        raise ContractError("invalid sealed surface count")
    if manifest.get("schema")!="g2_native_bundle_v1" or set(manifest.get("files",{}))!={"snapshot.json","surfaces.csv","grid_states.raw","SNAPSHOT_COMPLETE"}:
        raise ContractError("invalid native bundle file inventory")
    for name,record in manifest["files"].items():
        if record.get("path")!=name:raise ContractError("bundle file identity mismatch")
        verified_file(root,record)
    snapshot=validate_snapshot(read_json(root/"snapshot.json"))
    for k in ("scene_id","source_sha256","frame_id","timestamp_ns","world_frame","source_mode","native_build_source_sha256","geometry_source_mode"):
        if snapshot[k]!=manifest[k]:
            raise ContractError("bundle/source frame mismatch")
    return manifest,snapshot


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-directory",required=True);p.add_argument("--output",required=True)
    p.add_argument("--native-run");p.add_argument("--allow-oracle-diagnostic",action="store_true")
    p.add_argument("--expected-build-source-sha256")
    a=p.parse_args()
    r=capture(a.native_directory,a.output,native_run=a.native_run,
              allow_oracle_diagnostic=a.allow_oracle_diagnostic,
              expected_build_source_sha256=a.expected_build_source_sha256)
    print(r["semantic_stage"],r["structural_stage"])


if __name__=="__main__":
    main()
