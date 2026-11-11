"""Own native wire fixtures, not real model/scene acceptance or Room reconstruction."""
import copy
import hashlib
import itertools
import struct

import pytest

from g2.io import ContractError, write_json
from g2.nav_bridge.snapshot import (NATIVE_BOX_TRIANGLES, capture, validate_snapshot,
                                   verify_native_structure_grid, _read_native_grid)


def floats(values):
    return b"".join(struct.pack("<d",0.0 if x==0 else float(x)) for x in values)


def seal(s,raw):
    """TEST_ONLY independent encoder for the documented native binary wire recipe."""
    g=s["grid"];m=s["native_structures"];p=m["floor_probe"];mode=s["geometry_source_mode"].encode()
    cells=sorted((x,y,r["uid"],r["local_id"]) for r in s["rooms"] for x,y in r["footprint"])
    payload=b"NAV_SG_NATIVE_STRUCTURE_GRID_V1\n"+floats([*g["origin"],g["resolution"]])
    payload+=struct.pack("<4Q",*g["dimensions"],len(raw))+raw+struct.pack("<Q",len(mode))+mode+bytes([p["provided"]])
    if p["provided"]:payload+=floats([p["floor_z"],*p["sensor_position"]])
    payload+=floats([p["max_depth"],p["min_floor_height"]])+struct.pack("<Q",len(cells))
    payload+=b"".join(struct.pack("<4Q",*c) for c in cells)
    m["grid_sha256"]=hashlib.sha256(payload).hexdigest();m["occupancy_sha256"]=hashlib.sha256(raw).hexdigest()
    m["supported_voxel_count"]=0
    for e in s["entities"]:
        proof=e.get("native_structure_evidence")
        if proof:
            proof.update(grid_sha256=m["grid_sha256"],occupancy_sha256=m["occupancy_sha256"])
            m["supported_voxel_count"]+=len(proof["occupied_voxel_addresses"])


@pytest.fixture
def native_case(tmp_path):
    dims=[5,5,5];raw=bytearray(125)
    for x in range(5):
        for y in range(5):
            for z in range(5):raw[(x*5+y)*5+z]=2 if z==0 or x in (0,4) or y in (0,4) else 1
    def entity(i,kind,lo,hi,low,high):
        vertices=[[hi[a] if n&(1<<a) else lo[a] for a in range(3)] for n in range(8)]
        triangles=copy.deepcopy(NATIVE_BOX_TRIANGLES)
        geometry=b"NAV_SG_NATIVE_VOXEL_BOX_V1\n"+floats(itertools.chain.from_iterable(vertices))
        geometry+=b"".join(struct.pack("<Q",n) for n in itertools.chain.from_iterable(triangles))
        support=[(x*5+y)*5+z for x in range(low[0],high[0]+1)
            for y in range(low[1],high[1]+1) for z in range(low[2],high[2]+1)]
        return {"id":"entity_"+str(i),"native_id":i,"kind":kind,"room_uid":-1,
            "adjacent_room_uids":[0],"wall_axis":"x" if kind=="wall" else None,
            "source_instance_id":kind+'_0_'+('-1' if kind=='floor' else '0')+'_'+'_'.join(map(str,low+high)),
            "bbox_min":lo,"bbox_max":hi,"vertices":vertices,"triangles":triangles,
            "geometry_sha256":hashlib.sha256(geometry).hexdigest(),"floor_member":kind=="floor",
            "upper_member":False,"root_affiliations":[],"island_id":None,
            "native_structure_evidence":{"kind":"OCCUPIED_VOXEL_BOX","scene_id":"TEST_ONLY_NATIVE_PROOF",
                "source_sha256":"a"*64,"frame_id":0,"semantic_certification":False,
                "occupied_voxel_addresses":support}}
    footprint=[[x,y] for x in range(1,4) for y in range(1,4)]
    footprint+=[[0,y] for y in range(1,4)]+[[4,y] for y in range(1,4)]+[[x,0] for x in range(1,4)]+[[x,4] for x in range(1,4)]
    s={"schema":"nav_sg_spatial_snapshot_v1","scene_id":"TEST_ONLY_NATIVE_PROOF","source_sha256":"a"*64,
        "native_build_source_sha256":"b"*64,"frame_id":0,"timestamp_ns":100,"world_frame":"map",
        "source_mode":"perception","geometry_source_mode":"PRESCAN_PREBUILT","completed_rgbd_observations":0,
        "last_rgbd_observation_timestamp_ns":0,"object_frontend_status":"BLOCKED_CURRENT_FRAME_RGBD_OBSERVATIONS",
        "native_geometry_refreshed":True,"geometry_update_sequence":1,"color_voxel_leaf":.1,
        "bounds_min":[0,0,0],"bounds_max":[5,5,5],"connection_distance":.3,"affiliations_complete":False,
        "grid":{"origin":[0,0,0],"resolution":1.,"dimensions":dims,"states":{"unknown":0,"free":1,"occupied":2},
            "state_file":"grid_states.raw","state_order":"xyz_z_fastest"},"structure_mode":"NATIVE_OCCUPANCY_PATCHES_V1",
        "native_structures":{"status":"PARTIAL_OBSERVED_AXIS_ALIGNED_PATCHES","semantic_certification":False,"geometry_resolution":1.,"boundary_coverage_complete":False,
            "known_object_height_coverage":True,"unsupported_floor_cells":0,"unsupported_boundary_cells":1,
            "floor_evidence_source":"NATIVE_SENSOR_PROBE_AND_OBSERVED_ROOM_FOUNDATION",
            "floor_probe":{"provided":True,"verified":True,"max_depth":3.,"min_floor_height":.3,"floor_z":.5,
                "sensor_position":[2.5,2.5,2.5]}},
        "rooms":[{"uid":0,"local_id":0,"center":[2.5,2.5,2.5],"frame_axes":"world_axes","footprint":footprint}],
        "entities":[entity(0,"floor",[1,1,0],[4,4,1],[1,1,0],[3,3,0]),
                    entity(1,"wall",[0,1,1],[1,4,5],[0,1,1],[0,3,4])],
        "building":None,"relations":[],"surface_file":"surfaces.csv"}
    seal(s,bytes(raw));return s,raw,tmp_path


def check(case):
    s,raw,_=case;validate_snapshot(s);return verify_native_structure_grid(s,bytes(raw))


def thin_case(case):
    s,raw,path=case;old=bytes(raw);s['grid']['origin'][2]=-1;s['grid']['dimensions'][2]=6
    thin=bytearray(150)
    for x in range(5):
        for y in range(5):
            for z in range(5):thin[(x*5+y)*6+z+1]=old[(x*5+y)*5+z]
    selected={(1,1),(1,3),(3,1),(3,3)}
    for x in range(1,4):
        for y in range(1,4):
            if (x,y) not in selected:thin[(x*5+y)*6+1]=0
    template=s['entities'][0];wall=s['entities'][1]
    wall['native_structure_evidence']['occupied_voxel_addresses']=[(n//5)*6+n%5+1 for n in wall['native_structure_evidence']['occupied_voxel_addresses']]
    wall['source_instance_id']='wall_0_0_0_1_2_0_3_5'
    floors=[]
    for i,(x,y) in enumerate(sorted(selected)):
        e=copy.deepcopy(template);e.update(id='entity_'+str(i+2),native_id=i+2,
            bbox_min=[x,y,0],bbox_max=[x+1,y+1,1],source_instance_id='floor_0_-1_'+
            '_'.join(map(str,[x,y,1,x,y,1])))
        e['vertices']=[[e['bbox_max'][a] if n&(1<<a) else e['bbox_min'][a] for a in range(3)] for n in range(8)]
        geometry=b'NAV_SG_NATIVE_VOXEL_BOX_V1\n'+floats(itertools.chain.from_iterable(e['vertices']))
        geometry+=b''.join(struct.pack('<Q',n) for n in itertools.chain.from_iterable(e['triangles']))
        e['geometry_sha256']=hashlib.sha256(geometry).hexdigest()
        e['native_structure_evidence']['occupied_voxel_addresses']=[(x*5+y)*6+1];floors.append(e)
    s['entities']=[*floors,wall]
    s['native_structures'].update(floor_support_policy='LOCAL_THIN_SURFACE_V2',observed_floor_cells=4,
        unknown_below_floor_cells=4,rejected_free_below_cells=0,unsupported_floor_cells=5,
        floor_evidence_source='NATIVE_SENSOR_PROBE_AND_LOCAL_OBSERVED_SURFACES')
    seal(s,bytes(thin));return s,thin,path


def test_four_thin_floor_columns_preserve_five_unknown_holes_and_unknown_below(native_case):
    case=thin_case(native_case);before=bytes(case[1]);result=check(case)
    assert result['root_count']==5 and bytes(case[1])==before
    assert case[0]['native_structures']['unsupported_floor_cells']==5


@pytest.mark.parametrize('fault',['free_below','unknown_support','wrong_observed_count','wrong_unknown_count','wrong_rejection_count','filled_holes'])
def test_thin_floor_evidence_rejects_tabletops_missing_support_and_extrapolated_counts(native_case,fault):
    case=thin_case(native_case);s,raw,_=case;meta=s['native_structures']
    if fault=='free_below':raw[(1*5+1)*6]=1
    elif fault=='unknown_support':raw[(1*5+1)*6+1]=0
    elif fault=='wrong_observed_count':meta['observed_floor_cells']=9
    elif fault=='wrong_unknown_count':meta['unknown_below_floor_cells']=0
    elif fault=='wrong_rejection_count':meta['rejected_free_below_cells']=1
    else:meta['unsupported_floor_cells']=0
    seal(s,bytes(raw))
    with pytest.raises(ContractError):check(case)


def test_native_observed_geometry_is_separate_from_model_or_semantic_acceptance(native_case):
    result=check(native_case)
    assert result["root_count"]==2 and result["semantic_certification"] is False
    assert native_case[0]["object_frontend_status"]=="BLOCKED_CURRENT_FRAME_RGBD_OBSERVATIONS"


@pytest.mark.parametrize("change",["missing_mode","oracle","stale_frame","future_model","past_model",
    "semantic_true","not_refreshed","mesh_hash","mesh_vertex","bool_frame","fake_complete"])
def test_native_structure_contract_rejects_mixed_or_overclaimed_proofs(native_case,change):
    s,raw,_=native_case;proof=s["entities"][0]["native_structure_evidence"]
    if change=="missing_mode":s.pop("structure_mode")
    elif change=="oracle":s["geometry_source_mode"]="ORACLE_GRID"
    elif change=="stale_frame":proof["frame_id"]=200
    elif change=="future_model":s["last_rgbd_observation_timestamp_ns"]=200
    elif change=="past_model":s.update(completed_rgbd_observations=1,last_rgbd_observation_timestamp_ns=50,object_frontend_status="OBSERVED")
    elif change=="semantic_true":proof["semantic_certification"]=True
    elif change=="not_refreshed":s["native_geometry_refreshed"]=False
    elif change=="mesh_hash":s["entities"][0]["geometry_sha256"]="f"*64
    elif change=="mesh_vertex":s["entities"][0]["vertices"][0][0]+=.1
    elif change=="bool_frame":proof["frame_id"]=False
    elif change=="fake_complete":s["affiliations_complete"]=True
    with pytest.raises(ContractError):check(native_case)


@pytest.mark.parametrize("state",[0,1])
def test_resealed_grid_cannot_fill_free_or_unknown_as_structure(native_case,state):
    s,raw,_=native_case;address=s["entities"][0]["native_structure_evidence"]["occupied_voxel_addresses"][0]
    raw[address]=state;seal(s,bytes(raw))
    with pytest.raises(ContractError,match="fills FREE/UNKNOWN"):check(native_case)


def test_missing_box_support_cannot_bridge_a_hole(native_case):
    s,raw,_=native_case;s["entities"][0]["native_structure_evidence"]["occupied_voxel_addresses"].pop()
    seal(s,bytes(raw))
    with pytest.raises(ContractError,match="bridge a hole"):check(native_case)


def test_room_labels_are_bound_even_when_occupancy_is_unchanged(native_case):
    s,raw,_=native_case;s["rooms"][0]["footprint"].pop()
    with pytest.raises(ContractError,match="Room/probe fingerprint"):check(native_case)


def test_occupied_bytes_cannot_be_changed_without_their_proof(native_case):
    _,raw,_=native_case;raw[0]=1
    with pytest.raises(ContractError,match="occupancy bytes/hash"):check(native_case)


def test_native_geometry_does_not_bypass_the_real_object_observation_gate(native_case):
    s,raw,root=native_case;native=root/"native";native.mkdir()
    write_json(native/"snapshot.json",s);(native/"grid_states.raw").write_bytes(bytes(raw))
    (native/"SNAPSHOT_COMPLETE").write_text("nav_sg_spatial_snapshot_v1\n")
    (native/"surfaces.csv").write_text("x,y,z,red,green,blue,color_valid,entity_id\n2,2,.9,1,2,3,1,entity_0\n")
    with pytest.raises(ContractError,match="BLOCKED_REAL_RGBD_OBSERVATIONS"):
        capture(native,root/"bundle")
    assert not (root/"bundle").exists()


def test_combined_self_report_cannot_promote_a_missing_boundary(native_case):
    s,_,_=native_case
    s['affiliations_complete']=True
    s['native_structures'].update(boundary_coverage_complete=True,unsupported_boundary_cells=0,
        status='OBSERVED_AXIS_ALIGNED_BOUNDARY_COVERAGE')
    with pytest.raises(ContractError,match='boundary coverage gaps'):check(native_case)


@pytest.mark.parametrize('change',['free_floor','outside_sensor','occupied_sensor','wrong_probe','foundation_hole'])
def test_resealed_probe_cannot_replace_observed_native_evidence(native_case,change):
    s,raw,_=native_case;p=s['native_structures']['floor_probe']
    if change=='free_floor':p['floor_z']=1.5
    elif change=='outside_sensor':p['sensor_position'][0]=-1
    elif change=='occupied_sensor':p['sensor_position'][0]=.5
    elif change=='wrong_probe':p['floor_z']=.6
    elif change=='foundation_hole':
        # Insert an UNKNOWN bottom layer while retaining every emitted world
        # coordinate and occupied face. A floor-like top alone is insufficient.
        expanded=bytearray(150)
        for xy in range(25):expanded[xy*6+1:xy*6+6]=raw[xy*5:xy*5+5]
        raw[:]=expanded;s['grid'].update(origin=[0,0,-1],dimensions=[5,5,6])
        for e in s['entities']:
            proof=e['native_structure_evidence']
            proof['occupied_voxel_addresses']=[(a//5)*6+(a%5)+1 for a in proof['occupied_voxel_addresses']]
            parts=e['source_instance_id'].split('_');parts[5]=str(int(parts[5])+1);parts[8]=str(int(parts[8])+1)
            e['source_instance_id']='_'.join(parts)
    seal(s,bytes(raw))
    with pytest.raises(ContractError):check(native_case)


def test_conflicting_native_local_room_ids_are_rejected_before_cells(native_case):
    s,_,_=native_case;r=copy.deepcopy(s['rooms'][0]);r.update(uid=1,footprint=[]);s['rooms'].append(r)
    with pytest.raises(ContractError,match='local identity'):check(native_case)


def test_native_world_extent_cannot_overflow(native_case):
    s,_,_=native_case;s['grid']['resolution']=1e308
    with pytest.raises(ContractError,match='world extent'):check(native_case)


def test_native_room_cell_budget_is_checked_before_materializing_labels(native_case):
    s,_,_=native_case;s['rooms'][0]['footprint']=[[1,1]]*1000001
    with pytest.raises(ContractError,match='footprint budget'):check(native_case)


def test_native_grid_size_is_rejected_before_open_or_hash(native_case,monkeypatch):
    s,_,root=native_case;path=root/'grid_states.raw';path.write_bytes(b'bad')
    def forbidden(*a,**k):raise AssertionError('wrong-size grid must not be opened')
    monkeypatch.setattr(type(path),'open',forbidden)
    with pytest.raises(ContractError,match='bounded grid'):_read_native_grid(s,path)


def test_native_multi_room_display_adjacency_is_not_a_patch_owner(native_case):
    s,raw,_=native_case
    s['rooms'].append({'uid':1,'local_id':1,'center':[4.5,4.5,.5],
        'frame_axes':'world_axes','footprint':[[4,4]]})
    for e in s['entities']:e['adjacent_room_uids']=[0,1]
    seal(s,bytes(raw));assert check(native_case)['root_count']==2


def test_native_numeric_patch_key_retains_axis_when_display_axis_is_null(native_case):
    s,_,_=native_case;s['entities'][1]['wall_axis']=None
    assert check(native_case)['root_count']==2


def test_native_interior_wall_laundering_is_rejected_after_resealing(native_case):
    s,raw,_=native_case
    # An occupied upper slab is inside a known-free Room column, not the
    # outside boundary where native deriveNativeStructures creates walls.
    e=s['entities'][1];lo=[1,1,2];hi=[2,4,5]
    e['bbox_min']=lo;e['bbox_max']=hi
    e['vertices']=[[hi[a] if n&(1<<a) else lo[a] for a in range(3)] for n in range(8)]
    e['geometry_sha256']=hashlib.sha256(b'NAV_SG_NATIVE_VOXEL_BOX_V1\n'+floats(itertools.chain.from_iterable(e['vertices']))+
        b''.join(struct.pack('<Q',n) for n in itertools.chain.from_iterable(e['triangles']))).hexdigest()
    e['native_structure_evidence']['occupied_voxel_addresses']=[(1*5+y)*5+z for y in range(1,4) for z in range(2,5)]
    for a in e['native_structure_evidence']['occupied_voxel_addresses']:raw[a]=2
    e['source_instance_id']='wall_0_0_1_1_2_1_3_4'
    seal(s,bytes(raw))
    with pytest.raises(ContractError,match='not adjacent'):check(native_case)


def test_native_floating_wall_cannot_replace_ground_connected_boundary(native_case):
    s,raw,_=native_case;raw[(0*5+2)*5+1]=0
    # Keep the emitted upper slab occupied and internally valid.
    e=s['entities'][1];e['bbox_min'][2]=2
    e['vertices']=[[e['bbox_max'][a] if n&(1<<a) else e['bbox_min'][a] for a in range(3)] for n in range(8)]
    e['geometry_sha256']=hashlib.sha256(b'NAV_SG_NATIVE_VOXEL_BOX_V1\n'+floats(itertools.chain.from_iterable(e['vertices']))+
        b''.join(struct.pack('<Q',n) for n in itertools.chain.from_iterable(e['triangles']))).hexdigest()
    e['native_structure_evidence']['occupied_voxel_addresses']=[(0*5+y)*5+z for y in range(1,4) for z in range(2,5)]
    e['source_instance_id']='wall_0_0_0_1_2_0_3_4'
    seal(s,bytes(raw))
    with pytest.raises(ContractError,match='continuous occupied boundary'):check(native_case)


def test_native_blocked_snapshot_keeps_exact_wall_height_comparison(native_case):
    s,raw,_=native_case
    # C++ uses the exact product <=1.60, so a 1.6000000001m voxel cannot
    # contribute even its first FREE cell to the native structural interior.
    resolution=1.6000000001;s['grid']['resolution']=resolution;s['entities']=[]
    m=s['native_structures'];m.update(status='NO_OBSERVED_NATIVE_ROOM_FREE_COLUMNS',
        geometry_resolution=resolution,known_object_height_coverage=False,unsupported_boundary_cells=0,
        floor_evidence_source='UNAVAILABLE_NATIVE_SENSOR_FLOOR_PROBE')
    m['floor_probe']['floor_z']=resolution*.5
    seal(s,bytes(raw));assert check(native_case)['root_count']==0
