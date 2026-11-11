"""Pinned material-slot/alpha guards and compensated area evidence."""
import numpy as np
import pytest
from PIL import Image

from g2.sim.source_geometry import load_model,surface_colors
from g2.sim.surface_sampling import sample_surface
from g2.sim.surface_coverage import color_coverage
from g2.tests.test_texture_projection import textured
from g2.tests.test_mesh_asset_audit import mesh_scene
from g2.io import read_json,write_json,digest
from g2.sim.source_geometry import model_source_hash


@pytest.mark.parametrize("layers,expected",[("both","rgb"),("rgb","rgb"),("rgba","unknown")])
def test_pinned_primitive_binds_rgb_slot_and_never_prefers_rgba(tmp_path,layers,expected):
    source=tmp_path/"source";source.mkdir()
    Image.fromarray(np.tile([255,0,0],(4,4,1)).astype(np.uint8)).save(source/"red.png")
    Image.fromarray(np.tile([0,0,255],(4,4,1)).astype(np.uint8)).save(source/"blue.png")
    material=('' if layers=="rgba" else '<layer role="rgb" texture="red"/>')+('' if layers=="rgb" else '<layer role="rgba" texture="blue"/>')
    xml=source/"model.xml";xml.write_text('<mujoco><asset><texture name="red" type="2d" file="red.png"/>'
        '<texture name="blue" type="2d" file="blue.png"/><material name="m">'+material+'</material></asset>'
        '<worldbody><geom type="box" size=".2 .3 .4" material="m"/></worldbody></mujoco>')
    model,_=load_model(xml)
    colors,valid,_,reasons=surface_colors(model,0,"box",np.asarray([0]),np.asarray([[1.,0,0]]),
        local_points=np.asarray([[0.,0,.4]]),with_diagnostics=True)
    if expected=="rgb":
        assert valid[0] and reasons[0]==0
        np.testing.assert_array_equal(colors[0],[1,0,0,1])
    else:
        assert not valid[0] and reasons[0]!=0
        np.testing.assert_array_equal(colors[0,:3],[0,0,0])


def test_rgb_slot_four_channel_texture_does_not_drop_alpha(tmp_path):
    source=tmp_path/"source";source.mkdir()
    rgba=np.tile([255,0,0,0],(4,4,1)).astype(np.uint8);Image.fromarray(rgba).save(source/"alpha.png")
    xml=source/"model.xml";xml.write_text('<mujoco><asset><texture name="t" type="2d" file="alpha.png" nchannel="4"/>'
        '<material name="m" texture="t"/></asset><worldbody><geom type="box" size=".2 .3 .4" material="m"/></worldbody></mujoco>')
    model,_=load_model(xml)
    assert model.tex_nchannel[0]==4
    colors,valid,_,reasons=surface_colors(model,0,"box",np.asarray([0]),np.asarray([[1.,0,0]]),
        local_points=np.asarray([[0.,0,.4]]),with_diagnostics=True)
    assert colors[0,3]==0 and not valid[0] and reasons[0]==3


def test_coverage_area_matches_exact_sampler_despite_cancellation():
    vertices=np.asarray([[3.9999990463256836*32,11.99999713897705*32,0.],
                         [-3.9999961853027344*32,-11.999988555908203*32,0.],
                         [0.,1e-15,0.]],np.float32)
    faces=np.asarray([[0,1,2]])
    points,ids,_,sampling=sample_surface(vertices,faces,1000.,3,with_audit=True)
    weights,coverage=color_coverage(vertices,faces,ids,np.ones(len(points),bool),np.zeros(len(points),np.uint8))
    assert np.all(weights>0)
    assert coverage["sampled_input_triangle_area_m2"]==sampling["retained_area_m2"]
    assert coverage["area_weighted_valid_sample_fraction"]==1


def test_legacy_rgb_mesh_four_channel_alpha_is_not_promoted_to_valid(mesh_scene):
    import mujoco
    root,xml,_=mesh_scene
    Image.fromarray(np.tile([255,0,0,0],(4,4,1)).astype(np.uint8)).save(root/"alpha.png")
    xml.write_text(xml.read_text().replace('type="2d" builtin="checker" rgb1="1 0 0" rgb2="0 1 0" width="2" height="2"',
        'type="2d" file="alpha.png" nchannel="4"'))
    model,_=load_model(xml);g=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_GEOM,"mesh")
    rgba,valid,_,reasons=surface_colors(model,g,"mesh",np.asarray([0]),np.asarray([[1.,0,0]]),with_diagnostics=True)
    assert rgba[0,3]==0 and not valid[0] and reasons[0]==3


def test_rotated_primitive_material_follows_body_state_without_world_uv_shift(textured,tmp_path):
    from g2.sim.prescan import export
    xml,meta,_=textured()
    xml.write_text(xml.read_text().replace('<worldbody>','<worldbody><body name="moving"><joint type="slide" axis="1 0 0"/>')
        .replace('name="g" type="box"','name="g" euler="0 0 45" type="box"').replace('</worldbody>','</body></worldbody>'))
    _,sources=load_model(xml)
    states=xml.parent/"states.npz";qpos=np.zeros((201,1));qpos[200]=.12
    np.savez(states,qpos=qpos,time=np.arange(201)*.02)
    values=read_json(meta);values["state_source"]={"model_source_sha256":model_source_hash(sources),"states_sha256":digest(states)}
    write_json(meta,values)
    first=export(xml,meta,tmp_path/"f0",states=states,spacing=.3)
    later=export(xml,meta,tmp_path/"f200",states=states,frame=200,spacing=.3)
    a=np.loadtxt(tmp_path/"f0/precolored.txt",skiprows=7);b=np.loadtxt(tmp_path/"f200/precolored.txt",skiprows=7)
    np.testing.assert_array_equal(a[:,3:],b[:,3:])
    np.testing.assert_allclose(b[:,:3]-a[:,:3],np.tile([.12,0,0],(len(a),1)),atol=1e-14)
    assert first["visual_geoms"]==later["visual_geoms"]


def test_explicit_srgb_is_unsupported_instead_of_unverified_valid_color(textured):
    import mujoco
    xml,_,_=textured()
    xml.write_text(xml.read_text().replace('type="2d" file="grid.png"','type="2d" file="grid.png" colorspace="sRGB"'))
    model,_=load_model(xml)
    assert model.tex_colorspace[0]==int(mujoco.mjtColorSpace.mjCOLORSPACE_SRGB)
    _,valid,appearance,reasons=surface_colors(model,0,"box",np.asarray([0]),np.asarray([[1.,0,0]]),
        local_points=np.asarray([[0.,0,.6]]),with_diagnostics=True)
    assert not valid[0] and reasons[0]==1 and "sRGB" in appearance["reason"]
