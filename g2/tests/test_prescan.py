"""CPU TEST_ONLY MJCF sources; no private house or camera/model evidence."""
import gzip
import json
import numpy as np
import pytest
from g2.io import ContractError, digest, read_json, write_json
from g2.sim.prescan import export
from g2.sim.source_geometry import load_model, model_source_hash


@pytest.fixture
def scene(tmp_path):
    root=tmp_path/"source";root.mkdir()
    model=root/"model.xml"
    model.write_text('''<mujoco><worldbody>
      <geom name="visual" type="box" size=".2 .3 .1" rgba=".1 .6 .2 1"/>
      <geom name="collision" type="box" size=".3 .4 .2" rgba="1 0 0 1"/>
      <body name="moving"><joint type="slide" axis="1 0 0"/>
      <geom name="object" type="sphere" size=".08" rgba="0 0 1 1"/></body>
      </worldbody></mujoco>''')
    meta=root/"roles.json"
    write_json(meta,{"schema":"g2_sim_prescan_v1","scene_id":"TEST_ONLY_surfaces",
        "geoms":{name:{"role":"collision" if name=="collision" else "visual",
                        "source_kind":"mjcf","geom_name":name}
                 for name in ("visual","collision","object")}})
    return root,model,meta


def test_real_surface_colors_and_explicit_collision_exclusion(scene,tmp_path):
    _,model,meta=scene
    m=export(model,meta,tmp_path/"out",spacing=.1)
    rows=np.loadtxt(tmp_path/"out/precolored.txt",skiprows=7)
    assert {r["geom_name"] for r in m["visual_geoms"]}=={"visual","object"}
    assert m["excluded"][0]["geom_name"]=="collision"
    assert not np.any(np.all(rows[:,3:6]==[255,0,0],axis=1))
    assert np.all(rows[:,-1]==1) and len(rows)==m["point_count"]
    assert m["gates"]["object_perception"]=="REQUIRES_REAL_RGBD_POSE"
    assert (tmp_path/"out/COMPLETE").is_file()


def test_frame200_restores_archive_without_stepping(scene,tmp_path):
    root,model,meta=scene
    _,sources=load_model(model)
    states=root/"states.npz"
    qpos=np.zeros((201,1));qpos[200]=1.2
    np.savez(states,qpos=qpos,time=np.arange(201)*.02)
    m=read_json(meta);m["state_source"]={"model_source_sha256":model_source_hash(sources),"states_sha256":digest(states)}
    write_json(meta,m)
    result=export(model,meta,tmp_path/"out",states=states,frame=200,spacing=.1)
    assert result["state"]["timestamp"]==4 and result["state"]["frame_id"]==200
    assert result["bounds_max"][0]>1.27


@pytest.mark.parametrize("fault",["missing_role","foreign_geom","source_name","source_state"])
def test_invalid_source_declarations_never_complete(scene,tmp_path,fault):
    root,model,meta=scene;m=read_json(meta);kwargs={}
    if fault=="missing_role":del m["geoms"]["collision"]
    elif fault=="foreign_geom":m["geoms"]["foreign"]=m["geoms"]["visual"]
    elif fault=="source_name":m["geoms"]["visual"]["geom_name"]="guessed"
    else:
        states=root/"states.npz";np.savez(states,qpos=np.zeros((1,1)))
        kwargs["states"]=states
    write_json(meta,m)
    with pytest.raises(ContractError):export(model,meta,tmp_path/"out",**kwargs)
    assert not (tmp_path/"out/COMPLETE").exists()


def test_official_ep_meta_pointer_is_provenance_only(scene,tmp_path):
    root,model,meta=scene;ep=root/"ep_meta.json"
    write_json(ep,{"fixtures":{"cabinet_source":{"cls":"test_source_label"}}})
    m=read_json(meta);m["geoms"]["visual"]={"role":"visual","source_kind":"ep_meta",
        "ep_meta_pointer":"/fixtures/cabinet_source","source_instance_name":"cabinet_source"}
    write_json(meta,m)
    result=export(model,meta,tmp_path/"out",ep_meta=ep,spacing=.1)
    assert result["visual_geoms"][0]["source"]["category"]=={"field":"cls","value":"test_source_label"}
    assert "test_source_label" not in (tmp_path/"out/precolored.txt").read_text()


def test_gzip_source_hash_retains_original_bytes(scene,tmp_path):
    root,model,meta=scene;compressed=root/"model.xml.gz"
    compressed.write_bytes(gzip.compress(model.read_bytes()))
    result=export(compressed,meta,tmp_path/"out",spacing=.1)
    assert result["sources"][0]["sha256"]==digest(compressed)


def test_translucency_needs_partial_status(scene,tmp_path):
    _,model,meta=scene;model.write_text(model.read_text().replace('.1 .6 .2 1','.1 .6 .2 .5'))
    with pytest.raises(ContractError):export(model,meta,tmp_path/"refused")
    result=export(model,meta,tmp_path/"partial",allow_partial_color=True,spacing=.1)
    assert result["status"]=="PARTIAL_COLOR"
    assert not (tmp_path/"partial/COMPLETE").exists()


def test_point_budget_rejected_before_completion(scene,tmp_path):
    _,model,meta=scene
    with pytest.raises(ContractError,match="budget"):export(model,meta,tmp_path/"out",max_points=10)
    assert not (tmp_path/"out/COMPLETE").exists()


def test_mesh_uses_compiled_uv_and_source_texture_pixels(tmp_path):
    import mujoco
    from g2.sim.source_geometry import primitive_mesh,surface_colors
    root=tmp_path/"source";root.mkdir()
    vertices,faces=primitive_mesh("box",np.asarray([.2,.3,.4]))
    (root/"mesh.obj").write_text(''.join('v %g %g %g\n'%tuple(v) for v in vertices)+
        'vt 0 0\nvt 1 0\nvt 0 1\n'+''.join('f %d/1 %d/2 %d/3\n'%tuple(f+1) for f in faces))
    model=root/"scene.xml"
    model.write_text('<mujoco><asset><mesh name="mesh" file="mesh.obj"/>'
        '<texture name="t" type="2d" builtin="checker" rgb1="1 0 0" rgb2="0 1 0" width="2" height="2"/>'
        '<material name="m" texture="t" rgba="1 1 1 1"/></asset><worldbody>'
        '<geom name="g" type="mesh" mesh="mesh" material="m"/></worldbody></mujoco>')
    compiled,_=load_model(model)
    colors,valid,appearance=surface_colors(compiled,0,"mesh",np.asarray([0]),np.asarray([[.5,.25,.25]]))
    tid=int(compiled.mat_texid[0,int(mujoco.mjtTextureRole.mjTEXROLE_RGB)])
    address=int(compiled.tex_adr[tid])+int(compiled.tex_width[tid])*3
    assert valid and appearance["texture_sampled"]
    np.testing.assert_allclose(colors[0,:3],compiled.tex_data[address:address+3]/255)


def test_native_manifest_cannot_bind_a_different_restored_state(scene,tmp_path):
    import hashlib,mujoco
    from g2.io import canonical
    _,model,meta=scene
    _,sources=load_model(model)
    identity={"model_source_sha256":model_source_hash(sources),"mujoco_version":mujoco.__version__,"metadata":{}}
    native=tmp_path/"native.json"
    write_json(native,{"scene_id":"TEST_ONLY_surfaces","source_identity":identity,
        "source_sha256":hashlib.sha256(canonical(identity)).hexdigest(),
        "state":{"frame_id":0,"format":"qpos","timestamp":0,"timestamp_source":"mjcf_default"}})
    with pytest.raises(ContractError,match="restored state"):
        export(model,meta,tmp_path/"out",native_manifest=native,spacing=.1)
    assert not (tmp_path/"out/COMPLETE").exists()


@pytest.mark.parametrize("kind,size",[("sphere",".2"),("ellipsoid",".2 .3 .4"),
                                      ("capsule",".2 .4"),("cylinder",".2 .4")])
def test_samples_stay_on_analytic_primitive_surface(tmp_path,kind,size):
    root=tmp_path/"source";root.mkdir();model=root/"model.xml";meta=root/"roles.json"
    model.write_text('<mujoco><worldbody><geom name="g" type="%s" size="%s"/></worldbody></mujoco>'%(kind,size))
    write_json(meta,{"schema":"g2_sim_prescan_v1","scene_id":"TEST_ONLY_analytic",
                     "geoms":{"g":{"role":"visual","source_kind":"mjcf","geom_name":"g"}}})
    export(model,meta,tmp_path/"out",spacing=.1)
    xyz=np.loadtxt(tmp_path/"out/precolored.txt",skiprows=7)[:,:3]
    if kind=="sphere":assert np.allclose(np.linalg.norm(xyz,axis=1),.2)
    elif kind=="ellipsoid":assert np.allclose(np.linalg.norm(xyz/[.2,.3,.4],axis=1),1)
    elif kind=="capsule":
        center=np.zeros_like(xyz);center[:,2]=np.clip(xyz[:,2],-.4,.4)
        assert np.allclose(np.linalg.norm(xyz-center,axis=1),.2)
    else:
        assert np.all(np.isclose(np.linalg.norm(xyz[:,:2],axis=1),.2)|np.isclose(abs(xyz[:,2]),.4))
