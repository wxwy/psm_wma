"""Seal actual native nav_sg snapshots; never cluster Rooms or Islands in G2."""
import argparse
import csv
import hashlib
import math
from pathlib import Path
import re
import shutil
import struct
import itertools
from g2.io import parse_json
from g2.sim.source_scope import (REVIEWED_SCOPE, EVIDENCE_FILES, EVIDENCE_MANIFEST,
    EVIDENCE_REVIEW, EVIDENCE_CLOUD, EVIDENCE_COLOR_AUDIT, verify_full_scene_review, verify_sealed_scope)
from g2.io import ContractError, canonical, digest, new_output, read_json, sha, write_json, verified_file

ENTITY = re.compile(r"entity_[0-9]+\Z")
NATIVE_BOX_TRIANGLES = [[0,2,1],[1,2,3],[4,5,6],[5,7,6],[0,1,4],[1,5,4],
    [2,6,3],[3,6,7],[0,4,2],[2,4,6],[1,3,5],[3,7,5]]


def _f64(values):
    return b"".join(struct.pack("<d", 0.0 if v == 0 else float(v)) for v in values)


def _native_structure_header(s):
    roots=[e for e in s["entities"] if e["kind"]!="object"]
    native=s.get("structure_mode")=="NATIVE_OCCUPANCY_PATCHES_V1"
    if s["source_mode"]!="perception":
        if native or any("native_structure_evidence" in e for e in s["entities"]):
            raise ContractError("oracle structures cannot be relabelled as native perception")
        return None
    if not native and not roots:
        if s["affiliations_complete"] or any(e.get("floor_member") or e.get("upper_member") or e.get("island_id") for e in s["entities"]):
            raise ContractError("normal rootless geometry cannot certify structural memberships")
        return None
    if not native or s.get("native_geometry_refreshed") is not True:
        raise ContractError("normal structures require current native occupancy provenance")
    if len(roots)>1000 or len(s["entities"])-len(roots)>5000:
        raise ContractError("native structure/object budget exceeded")
    if type(s.get("geometry_update_sequence")) is not int or s["geometry_update_sequence"]<0:
        raise ContractError("native geometry refresh sequence missing")
    meta=s.get("native_structures",{})
    if not isinstance(meta,dict):raise ContractError("native structural evidence must be an object")
    statuses={"NO_OBSERVED_STRUCTURAL_SUPPORT","BLOCKED_NATIVE_SENSOR_FLOOR_EVIDENCE",
        "NO_OBSERVED_NATIVE_ROOM_FREE_COLUMNS","BLOCKED_HIGHER_THAN_OBSERVED_ROOM_GROUND",
        "BLOCKED_UNOBSERVED_GROUND_FOUNDATION","PARTIAL_OBSERVED_AXIS_ALIGNED_PATCHES","OBSERVED_AXIS_ALIGNED_BOUNDARY_COVERAGE"}
    if meta.get("status") not in statuses:
        raise ContractError("unsupported or overclaimed native structural status")
    sha(meta.get("grid_sha256"));sha(meta.get("occupancy_sha256"))
    if (meta.get("semantic_certification") is not False or
            meta.get("geometry_resolution")!=s["grid"]["resolution"] or
            any(type(meta.get(k)) is not bool for k in ("boundary_coverage_complete","known_object_height_coverage")) or
            any(type(meta.get(k)) is not int or meta[k]<0 for k in
                ("unsupported_floor_cells","unsupported_boundary_cells","supported_voxel_count"))):
        raise ContractError("native structure scope or uncertainty differs")
    if s["affiliations_complete"] and (not meta["boundary_coverage_complete"] or not meta["known_object_height_coverage"] or
            meta["unsupported_floor_cells"] or meta["unsupported_boundary_cells"]):
        raise ContractError("partial native geometry cannot certify complete affiliations")
    probe=meta.get("floor_probe",{})
    if not isinstance(probe,dict):raise ContractError("native sensor floor evidence must be an object")
    if (type(probe.get("provided")) is not bool or type(probe.get("verified")) is not bool or
            probe["verified"] and not probe["provided"] or any(type(probe.get(k)) not in (float,int) or
                not math.isfinite(probe[k]) or probe[k]<=0 for k in ("max_depth","min_floor_height"))):
        raise ContractError("invalid native sensor floor evidence")
    if probe["provided"]:
        vector(probe.get("sensor_position"),"native floor sensor pose")
        if type(probe.get("floor_z")) not in (int,float) or not math.isfinite(probe["floor_z"]):
            raise ContractError("native floor height must be finite")
    elif probe.get("floor_z") is not None or probe.get("sensor_position") is not None:
        raise ContractError("unavailable native probe cannot provide guessed pose/height")
    if roots and (not probe["verified"] or meta.get("floor_evidence_source")!="NATIVE_SENSOR_PROBE_AND_OBSERVED_ROOM_FOUNDATION"):
        raise ContractError("native Floor/Wall roots lack observed ground foundation")
    last=s.get("last_rgbd_observation_timestamp_ns")
    if type(last) is not int or not 0<=last<=s["timestamp_ns"]:
        raise ContractError("native current observation timestamp missing")
    if s.get("object_frontend_status")=="OBSERVED" and (not s["completed_rgbd_observations"] or last!=s["timestamp_ns"]):
        raise ContractError("past model observations cannot attest current native frame")
    total=0
    for e in s["entities"]:
        proof=e.get("native_structure_evidence")
        if e["kind"]=="object":
            if proof is not None:raise ContractError("native objects cannot impersonate structural roots")
            continue
        if e["kind"] not in ("floor","wall") or not isinstance(proof,dict):
            raise ContractError("native structures must carry finite observed box proof")
        adjacent=e.get("adjacent_room_uids")
        room_ids={r["uid"] for r in s["rooms"]}
        if (not isinstance(adjacent,list) or not adjacent or any(type(uid) is not int or uid not in room_ids for uid in adjacent) or
                len(adjacent)!=len(set(adjacent))):
            raise ContractError("native patch requires actual native adjacent Room identities")
        if (proof.get("kind")!="OCCUPIED_VOXEL_BOX" or proof.get("semantic_certification") is not False or
                type(proof.get("frame_id")) is not int or proof["frame_id"]!=s["frame_id"] or proof.get("scene_id")!=s["scene_id"] or
                proof.get("source_sha256")!=s["source_sha256"] or proof.get("grid_sha256")!=meta["grid_sha256"] or
                proof.get("occupancy_sha256")!=meta["occupancy_sha256"]):
            raise ContractError("native root belongs to another source/frame/grid")
        sha(e.get("geometry_sha256"))
        support=proof.get("occupied_voxel_addresses")
        if (not isinstance(support,list) or not 0<len(support)<=500000 or
                any(type(a) is not int or not 0<=a<math.prod(s["grid"]["dimensions"]) for a in support) or
                support!=sorted(set(support))):
            raise ContractError("native occupied support IDs invalid or exceed budget")
        total+=len(support)
        expected=[[e["bbox_max"][a] if i&(1<<a) else e["bbox_min"][a] for a in range(3)] for i in range(8)]
        if e["vertices"]!=expected or e["triangles"]!=NATIVE_BOX_TRIANGLES or any(
                b<=a for a,b in zip(e["bbox_min"],e["bbox_max"])):
            raise ContractError("native patch mesh differs from its finite occupied box")
        payload=b"NAV_SG_NATIVE_VOXEL_BOX_V1\n"+_f64(itertools.chain.from_iterable(e["vertices"]))
        payload+=b"".join(struct.pack("<Q",i) for i in itertools.chain.from_iterable(e["triangles"]))
        if hashlib.sha256(payload).hexdigest()!=e["geometry_sha256"]:
            raise ContractError("native observed box geometry hash differs")
    if total>2000000 or total!=meta["supported_voxel_count"]:
        raise ContractError("native structural support closure/budget differs")
    floors=[e for e in roots if e["kind"]=="floor"];walls=[e for e in roots if e["kind"]=="wall"]
    heights=bool(floors and walls)
    if heights:
        low=min(e["bbox_min"][2] for e in floors);high=min(e["bbox_max"][2] for e in walls)
        heights=all(e["bbox_min"][2]>=low-1e-9 and e["bbox_max"][2]<=high+1e-9
            for e in s["entities"] if e["kind"]=="object")
    if heights!=meta["known_object_height_coverage"]:
        raise ContractError("native vertical coverage does not support observed object heights")
    return meta


def _verify_native_observed_coverage(s,raw,cells,boxes):
    """Verify supplied patch coverage, not Room segmentation or new geometry."""
    meta=s["native_structures"];probe=meta["floor_probe"]
    if not probe["verified"]:return
    grid=s["grid"];dims=grid["dimensions"];origin=grid["origin"];res=grid["resolution"]
    def address(x,y,z):return (x*dims[1]+y)*dims[2]+z
    def state(x,y,z):
        return raw[address(x,y,z)] if all(0<=a<n for a,n in zip((x,y,z),dims)) else 0
    def index(value,axis):
        n=(value-origin[axis])/res
        if not math.isfinite(n) or not 0<=n<dims[axis]:
            raise ContractError("native floor probe is outside the actual observed grid")
        return math.floor(n)
    pose=probe["sensor_position"];sx,sy,sz=[index(v,a) for a,v in enumerate(pose)]
    floor=index(probe["floor_z"],2)
    if state(sx,sy,sz)!=1 or pose[2]-probe["floor_z"]<probe["min_floor_height"]:
        raise ContractError("native floor probe lacks known-free sensor height/pose")
    lower=(pose[2]-probe["max_depth"]-origin[2])/res
    if not math.isfinite(lower):raise ContractError("native floor probe depth overflow")
    observed=[]
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            for z in range(sz,max(0,math.floor(lower))-1,-1):
                if state(sx+dx,sy+dy,z)==2:
                    observed.append(origin[2]+(z+.5)*res);break
    if not observed or abs(min(observed)-probe["floor_z"])>res*1e-6:
        raise ContractError("native verified floor probe differs from actual occupied support")
    # These constants define NATIVE_OCCUPANCY_PATCHES_V1 in nav_sg, not a new
    # G2 classifier. Only native-provided Room cells and patches are checked.
    span=1.60/res
    height_cells=min(dims[2]-floor-1,max(0,math.ceil(span))) if math.isfinite(span) else dims[2]-floor-1
    interior={xy:uid_local[0] for xy,uid_local in cells.items() if any(
        (z-floor)*res<=1.60 and state(*xy,z)==1 for z in range(floor+1,floor+height_cells+1))}
    floors={};walls={};owners=set()
    required_height=min(dims[2],max(1,math.ceil((1.60-1e-9)/res))) if math.isfinite(span) else dims[2]
    for e,lo,hi,uid,axis in boxes:
        owners.add(uid)
        support=e["native_structure_evidence"]["occupied_voxel_addresses"]
        if e["kind"]=="floor":
            if lo[2]!=floor or hi[2]!=floor or any(interior.get((x,y))!=uid or
                    state(x,y,floor+1)!=1 for x in range(lo[0],hi[0]+1) for y in range(lo[1],hi[1]+1)):
                raise ContractError("native floor patch is not its Room's observed ground interface")
            floors.setdefault(uid,set()).update(support)
        else:
            if axis not in (0,1) or hi[axis]!=lo[axis] or lo[2]<=floor:
                raise ContractError("native wall patch is not an observed vertical boundary plane")
            along=1-axis
            if (hi[along]-lo[along]+1)*res+1e-9<.30:
                raise ContractError("native wall patch is shorter than its native evidence contract")
            offsets=((-1,0),(1,0)) if axis==0 else ((0,-1),(0,1))
            if any(interior.get((x,y))==uid or not any(interior.get((x+dx,y+dy))==uid for dx,dy in offsets)
                    for x in range(lo[0],hi[0]+1) for y in range(lo[1],hi[1]+1)):
                raise ContractError("native wall patch is not adjacent to its actual Room")
            if any(any(state(x,y,z)!=2 for z in range(floor+1,max(hi[2],floor+required_height)+1))
                    for x in range(lo[0],hi[0]+1) for y in range(lo[1],hi[1]+1)):
                raise ContractError("native wall patch lacks continuous occupied boundary height from ground")
            walls.setdefault(uid,set()).update(support)
    for (x,y),uid in interior.items():
        if uid in owners and any(state(x,y,z)!=2 for z in range(floor+1)):
            raise ContractError("native structural roots lack the whole Room's observed foundation")
    missing_floor=sum(address(x,y,floor) not in floors.get(uid,set()) for (x,y),uid in interior.items())
    if missing_floor and not meta["unsupported_floor_cells"]:
        raise ContractError("native floor coverage gaps cannot be reported as zero")
    missing_boundary=False
    for (x,y),uid in interior.items():
        support=walls.get(uid,set())
        for dx,dy in ((-1,0),(1,0),(0,-1),(0,1)):
            nx,ny=x+dx,y+dy
            if interior.get((nx,ny))==uid:continue
            if not (0<=nx<dims[0] and 0<=ny<dims[1] and floor+required_height<dims[2]) or any(
                    address(nx,ny,z) not in support for z in range(floor+1,floor+required_height+1)):
                missing_boundary=True
    if missing_boundary and not meta["unsupported_boundary_cells"]:
        raise ContractError("native boundary coverage gaps cannot be reported as zero")
    if meta["boundary_coverage_complete"] and (not boxes or not interior or missing_floor or missing_boundary):
        raise ContractError("native complete coverage is unsupported by actual Room/grid/patch evidence")


def verify_native_structure_grid(s,raw):
    """Check native output against actual occupancy; never infer or rebuild roles."""
    meta=_native_structure_header(s)
    grid=s["grid"];dims=grid["dimensions"];origin=grid["origin"];res=grid["resolution"]
    if len(raw)!=math.prod(dims) or any(x>2 for x in raw):
        raise ContractError("native structure occupancy encoding/size differs")
    if meta is None:return None
    if hashlib.sha256(raw).hexdigest()!=meta["occupancy_sha256"]:
        raise ContractError("native structure occupancy bytes/hash differ")
    cells={};locals_seen=set()
    for room in s["rooms"]:
        uid,local=room["uid"],room.get("local_id")
        if type(local) is not int or not 0<=local<2**31 or not 0<=uid<2**31 or local in locals_seen:
            raise ContractError("native Room local identity missing")
        locals_seen.add(local)
        footprint=room.get("footprint")
        if not isinstance(footprint,list):raise ContractError("native Room footprint missing")
        if len(cells)+len(footprint)>1000000:raise ContractError("native Room footprint budget exceeded")
        for xy in footprint:
            if (not isinstance(xy,list) or len(xy)!=2 or any(type(v) is not int for v in xy) or
                    not 0<=xy[0]<dims[0] or not 0<=xy[1]<dims[1] or tuple(xy) in cells):
                raise ContractError("native Room footprint is invalid or overlaps another label")
            cells[tuple(xy)]=(uid,local)
    if len(cells)>1000000:raise ContractError("native Room footprint budget exceeded")
    mode=s["geometry_source_mode"].encode();probe=meta["floor_probe"]
    data=b"NAV_SG_NATIVE_STRUCTURE_GRID_V1\n"+_f64([*origin,res])
    data+=struct.pack("<3QQ",*dims,len(raw))+raw+struct.pack("<Q",len(mode))+mode+bytes([probe["provided"]])
    if probe["provided"]:data+=_f64([probe["floor_z"],*probe["sensor_position"]])
    data+=_f64([probe["max_depth"],probe["min_floor_height"]])+struct.pack("<Q",len(cells))
    data+=b"".join(struct.pack("<4Q",x,y,*cells[(x,y)]) for x,y in sorted(cells))
    if hashlib.sha256(data).hexdigest()!=meta["grid_sha256"]:
        raise ContractError("native structural grid/Room/probe fingerprint differs")
    boxes=[]
    for e in s["entities"]:
        if e["kind"]=="object":continue
        low=[round((x-o)/res) for x,o in zip(e["bbox_min"],origin)]
        high=[round((x-o)/res)-1 for x,o in zip(e["bbox_max"],origin)]
        if any(not 0<=a<=b<n or abs(x-(o+a*res))>max(1e-8,res*1e-6) or
                abs(y-(o+(b+1)*res))>max(1e-8,res*1e-6) for a,b,n,x,y,o in
                zip(low,high,dims,e["bbox_min"],e["bbox_max"],origin)):
            raise ContractError("native patch box is not aligned to the actual native grid")
        support=e["native_structure_evidence"]["occupied_voxel_addresses"]
        if math.prod(b-a+1 for a,b in zip(low,high))!=len(support):
            raise ContractError("native patch would bridge a hole in observed support")
        expected=[(x*dims[1]+y)*dims[2]+z for x in range(low[0],high[0]+1)
            for y in range(low[1],high[1]+1) for z in range(low[2],high[2]+1)]
        if support!=expected or any(raw[a]!=2 for a in support):
            raise ContractError("native structure fills FREE/UNKNOWN or omits actual box cells")
        # deriveNativeStructures emits this numeric key from the exact native
        # patch owner/normal/voxel bounds. It is a wire identity, not a simulator
        # name/category heuristic. Display adjacency/axis can be many/null.
        key=e.get("source_instance_id","")
        if not isinstance(key,str):raise ContractError("native occupied patch key must be text")
        match=re.fullmatch(r"(floor|wall)_([0-9]+)_(-1|0|1)_"+r"_".join([r"([0-9]+)"]*6),key)
        if not match:raise ContractError("native occupied patch key is missing or malformed")
        kind,uid,axis,*bounds=match.groups();uid=int(uid);axis=int(axis);bounds=list(map(int,bounds))
        expected=e["kind"]+'_'+str(uid)+'_'+str(axis)+'_'+'_'.join(map(str,low+high))
        if key!=expected or kind!=e["kind"] or bounds!=low+high or uid not in e["adjacent_room_uids"] or (
                e["kind"]=="floor" and axis!=-1):
            raise ContractError("native patch key differs from owner/kind/voxel geometry")
        boxes.append((e,low,high,uid,axis))
    _verify_native_observed_coverage(s,raw,cells,boxes)
    return {"grid_sha256":meta["grid_sha256"],"occupancy_sha256":meta["occupancy_sha256"],
        "root_count":sum(e["kind"]!="object" for e in s["entities"]),"semantic_certification":False}


def _read_native_grid(s,path):
    expected=math.prod(s["grid"]["dimensions"])
    if path.is_symlink() or path.stat().st_size!=expected:
        raise ContractError("native tri-state occupancy file size differs from bounded grid")
    with path.open('rb') as stream:raw=stream.read(expected+1)
    if len(raw)!=expected:raise ContractError("native occupancy changed during bounded read")
    return raw


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
    if any(not math.isfinite(o+n*resolution) for o,n in zip(grid["origin"],dims)):
        raise ContractError("native grid world extent overflow")
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
    _native_structure_header(s)
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
    source_scope={"status":"SENSOR_INCREMENTAL_PARTIAL_COVERAGE"}
    prescan_source_binding=None
    if binding:
        if not isinstance(binding,dict):raise ContractError("invalid native prescan binding")
        if (binding.get("scene_id")!=snapshot["scene_id"] or binding.get("source_sha256")!=snapshot["source_sha256"]
            or binding.get("episode")!=run.get("episode") or binding.get("camera")!=run.get("camera")
            or binding.get("recorded_manifest_sha256")!=run.get("source_digests",{}).get("manifest.json")
            or binding.get("recorded_frames_sha256")!=run.get("source_digests",{}).get("frames.jsonl")):
            raise ContractError("prescan/recorded dataset witness mismatch")
        # A claimed review in native_run is not source review evidence.
        source_scope={"status":"LEGACY_PRESCAN_SOURCE_UNREVIEWED"}
        prescan_source_binding={key:sha(binding.get(key)) for key in
            ("prescan_cloud_sha256","visual_source_sha256")}
    elif snapshot["scene_id"]!=run.get("episode") or snapshot["source_sha256"]!=run.get("source_digests",{}).get("manifest.json"):
        raise ContractError("recorded-only scene identity mismatch")
    if snapshot["geometry_source_mode"]=="PRESCAN_PREBUILT" and not binding:
        raise ContractError("prebuilt map requires its original prescan source binding")
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
            "model_runtime":run["model_runtime"],"source_scope":source_scope,
            "prescan_source_binding":prescan_source_binding}


def capture(native_directory,output,*,native_run=None,allow_oracle_diagnostic=False,
            expected_build_source_sha256=None,prescan_manifest=None,full_scene_review=None):
    native=Path(native_directory).resolve()
    if (prescan_manifest is None)!=(full_scene_review is None):
        raise ContractError("source manifest and full-scene review must be provided together")
    sources=[native]+([Path(prescan_manifest).resolve().parent,Path(full_scene_review)] if prescan_manifest else [])
    out=new_output(output,sources)
    marker=native/"SNAPSHOT_COMPLETE"
    if marker.read_text()!="nav_sg_spatial_snapshot_v1\n":
        raise ContractError("native snapshot has no valid completion marker")
    s=validate_snapshot(read_json(native/"snapshot.json"))
    if expected_build_source_sha256 and s["native_build_source_sha256"]!=sha(expected_build_source_sha256):
        raise ContractError("native build source mismatch")
    witness=None
    if s["source_mode"]=="oracle_diagnostic":
        if prescan_manifest:raise ContractError("oracle snapshot cannot certify ordinary full-scene source")
        if not allow_oracle_diagnostic:
            raise ContractError("oracle snapshot forbidden in normal perception; explicit diagnostic opt-in required")
        if native_run:
            raise ContractError("oracle source cannot be relabelled by adding RGB-D evidence")
    else:
        if (not native_run or s["completed_rgbd_observations"]<1 or s["object_frontend_status"]!="OBSERVED"):
            raise ContractError("BLOCKED_REAL_RGBD_OBSERVATIONS")
        witness=observation_witness(native_run,s)
    if prescan_manifest:
        witness["source_scope"]=verify_full_scene_review(prescan_manifest,full_scene_review)
    grid_bytes=_read_native_grid(s,native/"grid_states.raw")
    files={}
    source_paths={name:native/name for name in ("snapshot.json","surfaces.csv","grid_states.raw","SNAPSHOT_COMPLETE")}
    if prescan_manifest:
        source_paths.update({EVIDENCE_MANIFEST:Path(prescan_manifest),EVIDENCE_REVIEW:Path(full_scene_review),
                             EVIDENCE_CLOUD:Path(prescan_manifest).parent/"precolored.txt"})
        if read_json(prescan_manifest).get("color_audit_file"):
            source_paths[EVIDENCE_COLOR_AUDIT]=Path(prescan_manifest).parent/"color_audit.npz"
    for name,p in source_paths.items():
        if p.is_symlink() or not p.is_file():
            raise ContractError("native snapshot files must be regular files")
        files[name]={"path":name,"bytes":p.stat().st_size,"sha256":digest(p)}
    if len(grid_bytes)!=math.prod(s["grid"]["dimensions"]) or any(value>2 for value in grid_bytes):
        raise ContractError("invalid actual native tri-state occupancy grid")
    structural_proof=verify_native_structure_grid(s,grid_bytes)
    count=sum(1 for _ in iter_surfaces(native/"surfaces.csv",{e["id"] for e in s["entities"]}))
    out.mkdir(parents=True)
    for name,record in files.items():
        (out/name).parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source_paths[name],out/name)
        verified_file(out,record)
        if digest(source_paths[name])!=record["sha256"]:
            raise ContractError("native snapshot changed during capture")
    manifest={"schema":"g2_native_bundle_v1","scene_id":s["scene_id"],"source_sha256":s["source_sha256"],
              "frame_id":s["frame_id"],"timestamp_ns":s["timestamp_ns"],"world_frame":s["world_frame"],
              "native_build_source_sha256":s["native_build_source_sha256"],"source_mode":s["source_mode"],
              "geometry_source_mode":s["geometry_source_mode"],
              "native_structure_proof":structural_proof,
              "source_scope":witness["source_scope"] if witness else
                 {"status":"ORACLE_DIAGNOSTIC_NOT_FULL_SCENE_CERTIFICATION"},
              "files":files,"surface_points":count,"observation_witness":witness,
              "semantic_stage":"ORACLE_DIAGNOSTIC" if witness is None else "REAL_RECORDED_INPUT_OBSERVED",
              "structural_stage":"AVAILABLE" if s["affiliations_complete"] else "BLOCKED_NATIVE_WALL_ROOTS",
              "training_ready":False}
    verify_sealed_scope(out,manifest)
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
    expected_files={"snapshot.json","surfaces.csv","grid_states.raw","SNAPSHOT_COMPLETE"}
    scope=manifest.get("source_scope",{})
    if not isinstance(scope,dict):raise ContractError("invalid source scope packet")
    if scope.get("status")==REVIEWED_SCOPE:expected_files|=EVIDENCE_FILES
    if scope.get("status")==REVIEWED_SCOPE and scope.get("color_audit_sha256"):
        expected_files.add(EVIDENCE_COLOR_AUDIT)
    if manifest.get("schema")!="g2_native_bundle_v1" or set(manifest.get("files",{}))!=expected_files:
        raise ContractError("invalid native bundle file inventory")
    snapshot=validate_snapshot(read_json(root/"snapshot.json"))
    grid_bytes=_read_native_grid(snapshot,root/"grid_states.raw")
    for name,record in manifest["files"].items():
        if record.get("path")!=name:raise ContractError("bundle file identity mismatch")
        verified_file(root,record)
    structural_proof=verify_native_structure_grid(snapshot,grid_bytes)
    if manifest.get("native_structure_proof")!=structural_proof:
        raise ContractError("sealed native structural proof differs from its actual inputs")
    for k in ("scene_id","source_sha256","frame_id","timestamp_ns","world_frame","source_mode","native_build_source_sha256","geometry_source_mode"):
        if snapshot[k]!=manifest[k]:
            raise ContractError("bundle/source frame mismatch")
    verify_sealed_scope(root,manifest)
    return manifest,snapshot


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--native-directory",required=True);p.add_argument("--output",required=True)
    p.add_argument("--native-run");p.add_argument("--allow-oracle-diagnostic",action="store_true")
    p.add_argument("--expected-build-source-sha256")
    p.add_argument("--prescan-manifest");p.add_argument("--full-scene-review")
    a=p.parse_args()
    r=capture(a.native_directory,a.output,native_run=a.native_run,
              allow_oracle_diagnostic=a.allow_oracle_diagnostic,
              expected_build_source_sha256=a.expected_build_source_sha256,
              prescan_manifest=a.prescan_manifest,full_scene_review=a.full_scene_review)
    print(r["semantic_stage"],r["structural_stage"])


if __name__=="__main__":
    main()
