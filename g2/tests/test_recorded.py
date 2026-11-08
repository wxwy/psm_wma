"""TEST_ONLY planning fixtures; no execution of RGB-D replay or inference."""
from pathlib import Path
import hashlib
import pytest
from g2.io import ContractError,canonical,digest,read_json,write_json
from g2.nav_bridge.recorded import prepare


@pytest.fixture
def inputs(tmp_path):
    source=tmp_path/"prescan";source.mkdir()
    cloud=source/"precolored.txt";cloud.write_text("TEST_ONLY_NO_NATIVE_EXECUTION\n")
    manifest=source/"manifest.json"
    identity={"schema":"TEST_ONLY_SOURCE_NOT_A_RENDERED_DATASET"}
    write_json(manifest,{"schema":"g2_prescan_manifest_v1","status":"COMPLETE","frame_id":0,
        "scene_id":"TEST_ONLY_house","world_frame":"world","source_sha256":"a"*64,"source_identity":identity,
        "visual_source_sha256":hashlib.sha256(canonical(identity)).hexdigest(),
        "file":{"path":cloud.name,"bytes":cloud.stat().st_size,"sha256":digest(cloud)},
        "sources":[{"logical_id":"root.xml","sha256":"b"*64}],
        "state":{"file_sha256":"c"*64},"input_files":{"ep_meta":{"sha256":"e"*64}}})
    (source/"COMPLETE").write_text("VISUAL_SURFACE_EXPORT_ONLY\n")
    grid=source/"grid.txt"
    grid.write_text('NAV_SG_ORACLE_GRID_V1\nscene_id "TEST_ONLY_house"\nsource_sha256 '+"a"*64+
                    '\nframe_id 0\nresolution .1\norigin 0 0 0\ndimensions 1 1 1\ndata\n0\n')
    nav=tmp_path/"nav";(nav/"g2/semantic").mkdir(parents=True)
    (nav/"g2/semantic/replay.py").write_text("# TEST_ONLY planning target\n")
    dataset=tmp_path/"recorded";episode=dataset/"TEST_ONLY_episode";episode.mkdir(parents=True)
    write_json(episode/"manifest.json",{"identity":{"source_files":[
        {"path":"source/"+name,"sha256":sha} for name,sha in
        [("model.xml.gz","b"*64),("states.npz","c"*64),("ep_meta.json","e"*64)]]}})
    (episode/"frames.jsonl").write_text("{}\n")
    sidecar=tmp_path/"sidecar";sidecar.mkdir()
    return manifest,grid,dict(nav_repo=nav,dataset_root=dataset,episode=episode.name,
                             camera="TEST_ONLY_camera",sidecar=sidecar,output=tmp_path/"plan",
                             allow_declared_subset=True)


def test_plan_binds_original_sources_and_uses_native_launch(inputs):
    manifest,grid,kwargs=inputs
    plan=prepare(manifest,grid,**kwargs)
    assert plan["status"]=="DIAGNOSTIC_SUBSET_PLAN_ONLY_NOT_EXECUTED"
    assert plan["source_scope"]["status"]=="DECLARED_SUBSET_NOT_CERTIFIED"
    assert plan["cwd"]==str(kwargs["nav_repo"])
    assert plan["native_launch"]["launch"]=="g2_semantic_review.launch"
    assert "--prescan-recorded-binding" in plan["replay_argv"]
    assert not (kwargs["output"]/"native_run").exists()
    binding=read_json(kwargs["output"]/"recorded_binding.json")
    assert binding["prescan_grid_sha256"]==digest(grid)


@pytest.mark.parametrize("source",["model.xml.gz","states.npz","ep_meta.json"])
def test_foreign_recorded_scene_is_rejected(inputs,source):
    manifest,grid,kwargs=inputs
    path=kwargs["dataset_root"]/kwargs["episode"]/"manifest.json"
    data=read_json(path)
    for record in data["identity"]["source_files"]:
        if Path(record["path"]).name==source:record["sha256"]="f"*64
    write_json(path,data)
    with pytest.raises(ContractError,match="different source"):prepare(manifest,grid,**kwargs)
    assert not kwargs["output"].exists()


@pytest.mark.parametrize("fault",["frame","grid","cloud","missing_source","world_frame"])
def test_plan_refuses_mixed_incomplete_inputs(inputs,fault):
    manifest,grid,kwargs=inputs
    data=read_json(manifest)
    if fault=="frame":data["frame_id"]=200
    elif fault=="grid":grid.write_text(grid.read_text().replace('frame_id 0','frame_id 200'))
    elif fault=="cloud":(manifest.parent/"precolored.txt").write_text("tampered")
    elif fault=="world_frame":data["world_frame"]="map"
    else:data["input_files"]={}
    write_json(manifest,data)
    with pytest.raises(ContractError):prepare(manifest,grid,**kwargs)


@pytest.mark.parametrize("fault",["marker","identity"])
def test_plan_requires_completed_source_identity(inputs,fault):
    manifest,grid,kwargs=inputs
    if fault=="marker":(manifest.parent/"COMPLETE").write_text("NOT_COMPLETE\n")
    else:
        data=read_json(manifest);data["source_identity"]={"tampered":True};write_json(manifest,data)
    with pytest.raises(ContractError):prepare(manifest,grid,**kwargs)
    assert not kwargs["output"].exists()


def test_complete_marker_alone_cannot_create_full_scene_plan(inputs):
    manifest,grid,kwargs=inputs;kwargs.pop("allow_declared_subset")
    with pytest.raises(ContractError,match="BLOCKED_FULL_SCENE_SOURCE_REVIEW"):
        prepare(manifest,grid,**kwargs)
    assert not kwargs["output"].exists()
