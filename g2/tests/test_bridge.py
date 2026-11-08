import json
import pytest
from g2.io import ContractError,digest,read_json,write_json
from g2.nav_bridge.snapshot import capture,load_bundle,validate_snapshot


def test_oracle_requires_diagnostic_opt_in(native_factory,tmp_path):
    root,s=native_factory()
    with pytest.raises(ContractError,match="oracle"):
        capture(root,tmp_path/"forbidden")
    assert not (tmp_path/"forbidden").exists()
    result=capture(root,tmp_path/"bundle",allow_oracle_diagnostic=True)
    assert result["training_ready"] is False
    assert load_bundle(tmp_path/"bundle")[1]==s


def test_plain_color_does_not_certify_perception(native_factory,tmp_path):
    root,_=native_factory(mode="perception")
    with pytest.raises(ContractError,match="REAL_RGBD"):
        capture(root,tmp_path/"out")
    assert not (tmp_path/"out/BUNDLE_COMPLETE").exists()


def test_oracle_geometry_cannot_be_declared_normal_perception(native_factory):
    _,s=native_factory(mode="perception");s["geometry_source_mode"]="ORACLE_GRID"
    with pytest.raises(ContractError,match="mode conflict"):validate_snapshot(s)


def test_actual_tri_state_grid_cannot_be_dropped_or_corrupted(native_factory,tmp_path):
    root,_=native_factory()
    (root/"grid_states.raw").write_bytes(bytes([3]))
    with pytest.raises(ContractError,match="tri-state"):
        capture(root,tmp_path/"out",allow_oracle_diagnostic=True)
    assert not (tmp_path/"out/BUNDLE_COMPLETE").exists()


@pytest.mark.parametrize("field,value",[
    ("frame_id",-1),("source_sha256","bad"),("color_voxel_leaf",0),
    ("bounds_max",[0,float("inf"),1]),("source_mode","gt_as_normal")])
def test_bad_native_identity_rejected(native_factory,field,value):
    _,s=native_factory();s[field]=value
    with pytest.raises(ContractError):validate_snapshot(s)


def test_native_ids_and_membership_not_reclustered(native_factory,tmp_path):
    root,s=native_factory()
    capture(root,tmp_path/"bundle",allow_oracle_diagnostic=True)
    actual=load_bundle(tmp_path/"bundle")[1]
    assert [(e["id"],e["root_affiliations"],e["island_id"]) for e in actual["entities"]]==[
        (e["id"],e["root_affiliations"],e["island_id"]) for e in s["entities"]]


def test_tampered_and_cross_frame_artifact_rejected(native_factory,tmp_path):
    root,_=native_factory()
    capture(root,tmp_path/"bundle",allow_oracle_diagnostic=True)
    with (tmp_path/"bundle/surfaces.csv").open("a") as f:f.write("0,0,0,0,0,0,1,unknown\n")
    with pytest.raises(ContractError,match="hash"):
        load_bundle(tmp_path/"bundle")


@pytest.mark.parametrize("badrow",[
    "0,0,0,256,0,0,1,entity_1", "0,0,0,1,2,3,2,entity_1",
    "nan,0,0,1,2,3,1,entity_1", "0,0,0,1,2,3,1,foreign","0,0"])
def test_native_color_negative_inputs(native_factory,tmp_path,badrow):
    root,_=native_factory()
    (root/"surfaces.csv").write_text("x,y,z,red,green,blue,color_valid,entity_id\n"+badrow+"\n")
    with pytest.raises(ContractError):capture(root,tmp_path/"out",allow_oracle_diagnostic=True)
    assert not (tmp_path/"out/BUNDLE_COMPLETE").exists()


def test_dangling_native_group_rejected(native_factory):
    _,s=native_factory();s["entities"][1]["root_affiliations"]=["foreign"]
    with pytest.raises(ContractError,match="structural"):validate_snapshot(s)


def test_geometry_mesh_and_grid_not_dropped(native_factory,tmp_path):
    root,s=native_factory();capture(root,tmp_path/"bundle",allow_oracle_diagnostic=True)
    actual=load_bundle(tmp_path/"bundle")[1]
    assert actual["grid"]==s["grid"]
    assert actual["entities"][2]["triangles"]==s["entities"][2]["triangles"]


def witness(root,s):
    run=root.parent/"run";run.mkdir()
    row={"schema":"nav_sg_native_semantic_audit_v1","frame_index":s["frame_id"],
         "stamp_ns":s["timestamp_ns"],"pose_stamp_ns":s["timestamp_ns"],"camera_stamp_ns":s["timestamp_ns"],
         "world_frame_id":s["world_frame"],"semantic_success":True,"scene_id":s["scene_id"],
         "source_sha256":s["source_sha256"],"native_build_source_sha256":s["native_build_source_sha256"],
         "scene_graph":{"nodes":[{"type":"object","native_cluster_id":1}]},
         "clusters":[{"native_cluster_id":1,"room_uid":0,"bbox_min_world":s["entities"][0]["bbox_min"],
                      "bbox_max_world":s["entities"][0]["bbox_max"]}]}
    (run/"native_semantic_audit.jsonl").write_text(json.dumps(row)+"\n")
    m={"schema":"nav_sg_g2_native_semantic_run_v1","execution_kind":"ros1_native",
       "spatial_profile":"G2_N6_RECORDED","model_runtime":"recorded_model_prediction",
       "episode":s["scene_id"],"camera":"test_camera","source_digests":{"manifest.json":s["source_sha256"]},
       "audit_sha256":digest(run/"native_semantic_audit.jsonl")}
    write_json(run/"native_run.json",m)
    return run


def test_protocol_witness_binding_fixture_is_not_real_model_acceptance(native_factory,tmp_path):
    root,s=native_factory(mode="perception");run=witness(root,s)
    result=capture(root,tmp_path/"out",native_run=run/"native_run.json")
    assert result["structural_stage"]=="BLOCKED_NATIVE_WALL_ROOTS"
    assert result["training_ready"] is False


@pytest.mark.parametrize("key,value",[
    ("source_sha256","c"*64),("scene_id","another_scene"),
    ("native_build_source_sha256","d"*64),("stamp_ns",999)])
def test_other_recorded_run_cannot_bless_snapshot(native_factory,tmp_path,key,value):
    root,s=native_factory(mode="perception");run=witness(root,s)
    row=json.loads((run/"native_semantic_audit.jsonl").read_text());row[key]=value
    (run/"native_semantic_audit.jsonl").write_text(json.dumps(row)+"\n")
    m=read_json(run/"native_run.json");m["audit_sha256"]=digest(run/"native_semantic_audit.jsonl")
    write_json(run/"native_run.json",m)
    with pytest.raises(ContractError):capture(root,tmp_path/"out",native_run=run/"native_run.json")


def test_oracle_cannot_be_promoted_with_recorded_witness(native_factory,tmp_path):
    root,s=native_factory();run=witness(root,{**s,"entities":[s["entities"][1]]})
    with pytest.raises(ContractError,match="relabelled"):
        capture(root,tmp_path/"out",allow_oracle_diagnostic=True,native_run=run/"native_run.json")
