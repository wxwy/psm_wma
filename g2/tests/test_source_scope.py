"""Synthetic source-review protocol tests, never real scene/human acceptance."""
import gzip
import hashlib
import numpy as np
import pytest
from g2.io import ContractError, canonical, digest, read_json, write_json
from g2.sim.prescan import export
from g2.sim.source_scope import REVIEWED_SCOPE, verify_full_scene_review


@pytest.fixture
def exported(tmp_path):
    source=tmp_path/"source";source.mkdir()
    model=source/"model.xml"
    model.write_text('''<mujoco><worldbody><body name="fixture_body">
      <geom name="visual" type="box" size=".1 .1 .1" rgba=".2 .3 .4 1"/>
      <geom name="collision" type="box" size=".1 .1 .1" rgba="1 0 0 1"/>
      </body><geom name="robot" type="sphere" size=".05"/></worldbody></mujoco>''')
    ep=source/"ep_meta.json"
    write_json(ep,{"fixtures":{"outlet_room":{"cls":"WallAccessory"}}})
    meta=source/"roles.json"
    write_json(meta,{"schema":"g2_sim_prescan_v1","scene_id":"TEST_ONLY_scope",
        "geoms":{
            "visual":{"role":"visual","source_kind":"ep_meta","ep_meta_pointer":"/fixtures/outlet_room",
                "source_instance_name":"outlet_room","source_body_name":"fixture_body",
                "classification_reason":"TEST_ONLY explicitly authored visible source"},
            "collision":{"role":"collision","source_kind":"mjcf","geom_name":"collision",
                "classification_reason":"TEST_ONLY separately authored collision proxy"},
            "robot":{"role":"robot","source_kind":"mjcf","geom_name":"robot",
                "classification_reason":"TEST_ONLY explicitly authored robot exclusion"}}})
    output=tmp_path/"prescan"
    m=export(model,meta,output,ep_meta=ep,spacing=.2,world_frame="world")
    return source,model,meta,ep,output,m


def review_for(output,m):
    path=output.parent/"TEST_ONLY_review.json"
    write_json(path,{"schema":"g2_full_scene_source_review_v1","decision":"APPROVED",
        "scope":"FULL_SCENE_SOURCE","review_kind":"SOURCE_ROLE_AND_MATERIAL_REVIEW",
        "reviewer":"TEST_ONLY_SCHEMA_FIXTURE_NOT_A_HUMAN_REVIEW","reviewed_utc":"2026-11-08T00:00:00Z",
        "manifest_sha256":digest(output/"manifest.json"),"scene_id":m["scene_id"],
        "source_sha256":m["source_sha256"],"visual_source_sha256":m["visual_source_sha256"],
        "geom_audit_sha256":m["geom_audit_sha256"],"frame_id":m["frame_id"]})
    return path


def test_declared_complete_retains_every_geom_and_stays_uncertified(exported):
    _,_,_,_,out,m=exported
    assert (out/"COMPLETE").is_file()
    assert m["completion_scope"]=="DECLARED_VISUAL_GEOMS_ONLY"
    assert m["compiled_geom_count"]==len(m["geom_audit"])==3
    assert m["source_audit"]["role_counts"]=={"visual":1,"collision":1,"robot":1}
    assert m["source_audit"]["color_valid_fraction"]==1
    assert m["source_audit"]["full_scene_source_certified"] is False
    assert m["gates"]["full_scene_source_certified"] is False
    assert m["training_ready"] is False
    row=next(row for row in m["geom_audit"] if row["geom_name"]=="visual")
    assert row["source"]["category"]["value"]=="WallAccessory"
    assert row["body_ancestry"][0]["body_name"]=="fixture_body"
    assert len(row["world_position"])==3 and len(row["world_rotation"])==9
    with pytest.raises(ContractError,match="BLOCKED_FULL_SCENE_SOURCE_REVIEW"):
        verify_full_scene_review(out/"manifest.json",None)


def test_schema_review_can_bind_exact_artifact_without_certifying_training(exported):
    _,_,_,_,out,m=exported
    packet=verify_full_scene_review(out/"manifest.json",review_for(out,m))
    assert packet["status"]==REVIEWED_SCOPE
    assert packet["manifest_sha256"]==digest(out/"manifest.json")
    assert "NOT_TRAINING" in packet["meaning"]


@pytest.mark.parametrize("field,value",[
    ("scope","DECLARED_SUBSET"),("decision","PENDING"),("reviewer",""),
    ("scene_id","another"),("source_sha256","e"*64),("visual_source_sha256","e"*64),
    ("manifest_sha256","e"*64),("geom_audit_sha256","e"*64),("frame_id",200),
    ("frame_id",False),("reviewed_utc","2026-11-08T00:00:00")])
def test_unbound_or_incomplete_review_rejected(exported,field,value):
    _,_,_,_,out,m=exported;p=review_for(out,m)
    data=read_json(p);data[field]=value;write_json(p,data)
    with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",p)


@pytest.mark.parametrize("fault",["category","body","reason","missing_geom","duplicate_id","role","color_status"])
def test_internally_contradictory_audit_cannot_be_self_certified(exported,fault):
    _,_,_,_,out,m=exported
    row=next(row for row in m["geom_audit"] if row["geom_name"]=="visual")
    if fault=="category":row["source"]["category"]["value"]="invented"
    elif fault=="body":row["source"]["body_binding"]["body_name"]="world"
    elif fault=="reason":row["classification_reason"]="invented"
    elif fault=="missing_geom":m["geom_audit"].pop()
    elif fault=="duplicate_id":m["geom_audit"][1]["geom_id"]=0
    elif fault=="role":m["geom_audit"][0]["role"]="auxiliary"
    else:m["geom_audit"][0]["color_status"]="NOT_SAMPLED"
    m["geom_audit_sha256"]=hashlib.sha256(canonical(m["geom_audit"])).hexdigest()
    m["source_audit"]["full_scene_review_eligible"]=True
    write_json(out/"manifest.json",m)
    with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",review_for(out,m))


def recorded_fixture(native_factory, exported):
    """TEST_ONLY existing audit protocol; no real model/native execution."""
    from g2.tests.test_bridge import witness
    _,_,_,_,out,m=exported
    native,s=native_factory(mode="perception")
    s.update(scene_id=m["scene_id"],source_sha256=m["source_sha256"],world_frame=m["world_frame"],
             geometry_source_mode="PRESCAN_PREBUILT")
    write_json(native/"snapshot.json",s)
    run=witness(native,s)
    r=read_json(run/"native_run.json")
    r["source_digests"]["frames.jsonl"]="d"*64
    r["prescan_recorded_binding"]={"scene_id":s["scene_id"],"source_sha256":s["source_sha256"],
        "episode":r["episode"],"camera":r["camera"],
        "recorded_manifest_sha256":r["source_digests"]["manifest.json"],"recorded_frames_sha256":"d"*64,
        "visual_source_sha256":m["visual_source_sha256"],"prescan_cloud_sha256":m["file"]["sha256"],
        "source_scope":{"status":REVIEWED_SCOPE,"review_sha256":"a"*64}}
    write_json(run/"native_run.json",r)
    return native,run,out,m


def test_run_scope_field_cannot_certify_full_scene(native_factory,exported,tmp_path):
    from g2.nav_bridge.snapshot import capture
    from g2.views.render import render
    native,run,_,_=recorded_fixture(native_factory,exported)
    b=capture(native,tmp_path/"bundle",native_run=run/"native_run.json")
    assert b["source_scope"]["status"]=="LEGACY_PRESCAN_SOURCE_UNREVIEWED"
    v=render(tmp_path/"bundle",tmp_path/"views",meters_per_pixel=.2)
    assert v["full_scene_source_certified"] is False and v["training_ready"] is False


def test_capture_retains_and_revalidates_actual_review_artifacts(native_factory,exported,tmp_path):
    from g2.nav_bridge.snapshot import capture,load_bundle
    native,run,out,m=recorded_fixture(native_factory,exported)
    packet=capture(native,tmp_path/"bundle",native_run=run/"native_run.json",
        prescan_manifest=out/"manifest.json",full_scene_review=review_for(out,m))
    sealed=load_bundle(tmp_path/"bundle")[0]
    assert len(packet["files"])==8
    assert sealed["source_scope"]["status"]==REVIEWED_SCOPE
    assert (tmp_path/"bundle/source_evidence/precolored.txt").read_bytes()==(out/"precolored.txt").read_bytes()
    assert sealed["training_ready"] is False


@pytest.mark.parametrize("fault",["missing_evidence","rejected_review"])
def test_bundle_fields_and_recomputed_hash_cannot_replace_review(native_factory,exported,tmp_path,fault):
    from g2.nav_bridge.snapshot import capture,load_bundle
    native,run,out,m=recorded_fixture(native_factory,exported)
    kwargs={} if fault=="missing_evidence" else {
        "prescan_manifest":out/"manifest.json","full_scene_review":review_for(out,m)}
    root=tmp_path/"bundle"
    capture(native,root,native_run=run/"native_run.json",**kwargs)
    b=read_json(root/"bundle.json")
    if fault=="missing_evidence":b["source_scope"]={"status":REVIEWED_SCOPE}
    else:
        p=root/"source_evidence/review.json";review=read_json(p);review["decision"]="REJECTED";write_json(p,review)
        record=b["files"]["source_evidence/review.json"]
        record.update(sha256=digest(p),bytes=p.stat().st_size)
        b["source_scope"]["review_sha256"]=digest(p)
    b.pop("version_sha256")
    b["version_sha256"]=hashlib.sha256(canonical(b)).hexdigest();write_json(root/"bundle.json",b)
    with pytest.raises(ContractError):load_bundle(root)


def test_review_of_other_native_initial_cloud_cannot_certify_snapshot(native_factory,exported,tmp_path):
    from g2.nav_bridge.snapshot import capture
    native,run,out,m=recorded_fixture(native_factory,exported)
    r=read_json(run/"native_run.json");r["prescan_recorded_binding"]["prescan_cloud_sha256"]="e"*64
    write_json(run/"native_run.json",r)
    with pytest.raises(ContractError,match="actual initial native input"):
        capture(native,tmp_path/"bundle",native_run=run/"native_run.json",
            prescan_manifest=out/"manifest.json",full_scene_review=review_for(out,m))
    assert not (tmp_path/"bundle/BUNDLE_COMPLETE").exists()


def test_raw_color_transport_is_part_of_review_evidence(exported):
    _,_,_,_,out,m=exported;p=review_for(out,m)
    (out/"precolored.txt").write_text("tampered")
    with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",p)


def test_world_label_cannot_differ_from_frozen_identity(exported):
    _,_,_,_,out,m=exported
    m["world_frame"]="map"
    cloud=out/"precolored.txt";cloud.write_text(cloud.read_text().replace('world_frame "world"','world_frame "map"'))
    m["file"].update(bytes=cloud.stat().st_size,sha256=digest(cloud))
    write_json(out/"manifest.json",m)
    with pytest.raises(ContractError,match="source identity"):
        verify_full_scene_review(out/"manifest.json",review_for(out,m))


def test_state_frame_boolean_is_not_an_integer_identity(exported):
    _,_,_,_,out,m=exported
    m["state"]["frame_id"]=False;write_json(out/"manifest.json",m)
    with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",review_for(out,m))


def test_reviewed_source_can_prepare_plan_but_never_execute_model(exported,tmp_path):
    from g2.nav_bridge.recorded import prepare
    from g2.sim.source_geometry import load_model,model_source_hash
    source,model,meta,ep,_,_=exported
    compressed=source/"model.xml.gz";compressed.write_bytes(gzip.compress(model.read_bytes()))
    states=source/"states.npz";np.savez(states,qpos=np.zeros((1,0)),time=np.zeros(1))
    _,sources=load_model(compressed)
    roles=read_json(meta);roles["state_source"]={"model_source_sha256":model_source_hash(sources),"states_sha256":digest(states)}
    write_json(meta,roles)
    out=tmp_path/"recorded_color"
    m=export(compressed,meta,out,ep_meta=ep,states=states,spacing=.2,world_frame="world")
    grid=tmp_path/"grid.txt"
    grid.write_text('NAV_SG_ORACLE_GRID_V1\nscene_id "'+m["scene_id"]+'"\nsource_sha256 '+m["source_sha256"]+
        '\nframe_id 0\nresolution .1\norigin 0 0 0\ndimensions 1 1 1\ndata\n0\n')
    nav=tmp_path/"nav";(nav/"g2/semantic").mkdir(parents=True);(nav/"g2/semantic/replay.py").write_text('# TEST_ONLY\n')
    dataset=tmp_path/"dataset";episode=dataset/"TEST_ONLY";episode.mkdir(parents=True)
    write_json(episode/"manifest.json",{"identity":{"source_files":[
        {"path":p.name,"sha256":digest(p)} for p in (compressed,states,ep)]}})
    (episode/"frames.jsonl").write_text('{}\n')
    sidecar=tmp_path/"sidecar";sidecar.mkdir()
    plan=prepare(out/"manifest.json",grid,nav_repo=nav,dataset_root=dataset,episode="TEST_ONLY",
        camera="TEST_ONLY",sidecar=sidecar,output=tmp_path/"plan",full_scene_review=review_for(out,m))
    assert plan["status"]=="PLAN_ONLY_NOT_EXECUTED" and plan["training_ready"] is False
    assert plan["source_scope"]["status"]==REVIEWED_SCOPE
    assert not (tmp_path/"plan/native_run").exists()


@pytest.mark.parametrize("body",[None,"not_the_actual_body","world"])
def test_official_geom_body_must_be_explicit_and_real_for_full_scope(exported,tmp_path,body):
    _,model,meta,ep,_,_=exported
    roles=read_json(meta)
    if body is None:roles["geoms"]["visual"].pop("source_body_name")
    else:roles["geoms"]["visual"]["source_body_name"]=body
    write_json(meta,roles)
    out=tmp_path/"new"
    if body is not None:
        with pytest.raises(ContractError,match="source body"):export(model,meta,out,ep_meta=ep,spacing=.2)
    else:
        m=export(model,meta,out,ep_meta=ep,spacing=.2)
        assert (out/"COMPLETE").is_file()  # legitimate declared subset transport
        assert m["source_audit"]["full_scene_review_eligible"] is False
        with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",review_for(out,m))


def test_partial_texture_audit_reports_missing_color_and_no_complete(exported,tmp_path):
    _,model,meta,ep,_,_=exported
    xml=model.read_text().replace('<worldbody>','''<asset><texture name="checker" type="2d"
        builtin="checker" width="2" height="2"/><material name="m" texture="checker"/></asset><worldbody>''')
    model.write_text(xml.replace('name="visual" type="box" size=".1 .1 .1"',
                                'name="visual" material="m" type="capsule" size=".1 .1"'))
    out=tmp_path/"partial"
    m=export(model,meta,out,ep_meta=ep,spacing=.2,allow_partial_color=True)
    assert m["status"]=="PARTIAL_COLOR" and not (out/"COMPLETE").exists()
    assert m["source_audit"]["color_valid_fraction"]==0
    assert m["source_audit"]["invalid_color_reason_counts"]
    with pytest.raises(ContractError):verify_full_scene_review(out/"manifest.json",review_for(out,m))


def test_fullphysics_frame0_200_preserves_identity_and_reports_motion(exported,tmp_path):
    import mujoco
    from g2.sim.source_geometry import load_model,model_source_hash
    source,path,meta,ep,_,_=exported
    path.write_text(path.read_text().replace('<body name="fixture_body">',
        '<body name="fixture_body"><freejoint name="fixture_joint"/>'))
    model,sources=load_model(path);data=mujoco.MjData(model)
    state_kind=mujoco.mjtState.mjSTATE_FULLPHYSICS
    initial=np.zeros(mujoco.mj_stateSize(model,state_kind));mujoco.mj_getState(model,data,initial,state_kind)
    rows=np.repeat(initial[None,:],201,axis=0)
    data.qpos[0]=.2;data.time=2.;mujoco.mj_forward(model,data)
    mujoco.mj_getState(model,data,rows[200],state_kind)
    states=source/"states.npz";np.savez(states,states=rows)
    roles=read_json(meta);roles["state_source"]={"model_source_sha256":model_source_hash(sources),"states_sha256":digest(states)}
    write_json(meta,roles)
    results=[export(path,meta,tmp_path/("frame_"+str(frame)),ep_meta=ep,states=states,
        frame=frame,state_format="mujoco_fullphysics",spacing=.2) for frame in (0,200)]
    visual=[next(row for row in m["geom_audit"] if row["geom_name"]=="visual") for m in results]
    assert visual[0]["geom_id"]==visual[1]["geom_id"]
    assert visual[0]["source"]==visual[1]["source"]
    assert results[0]["source_sha256"]==results[1]["source_sha256"]
    np.testing.assert_allclose(np.subtract(visual[1]["world_position"],visual[0]["world_position"]),[.2,0,0])
    assert [m["state"]["timestamp"] for m in results]==[0,2]
