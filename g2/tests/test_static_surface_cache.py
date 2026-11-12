"""Static render cache is based on verified motion, not sub-Ångström noise."""
import numpy as np
import pytest
import mujoco
from g2.io import ContractError
from g2.views.surface_renderer import SurfaceRenderer


def sample():
    model=mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom type="box" size=".2 .2 .2" rgba=".5 .5 .5 1"/></worldbody></mujoco>')
    renderer=SurfaceRenderer(model,'f'*64,{0},backend='cpu')
    reg={'surfaces':{0:dict(kind='box',position=np.zeros(3),
        rotation=np.eye(3),semantic_owner_index=None,
        material_id=-1,structural_role=None)}}
    room={'center':[0,0,0],'reference_frame':{
        'origin_world':[0,0,0],'axes_world':np.eye(3).tolist()}}
    return renderer,reg,room


def key(renderer,reg,room):
    return renderer._cache_key(reg,room,{0},[-1,-1,-1],[1,1,1],'floor_top',.01,False)


def test_sub_threshold_static_pose_jitter_does_not_invalidate():
    renderer,reg,room=sample()
    original=key(renderer,reg,room)
    reg['surfaces'][0]['position']=np.array([1e-12,-2e-12,1e-12])
    assert key(renderer,reg,room)==original


def test_disguised_moving_geom_is_rejected_instead_of_using_stale_pixels():
    renderer,reg,room=sample()
    key(renderer,reg,room)
    reg['surfaces'][0]['position']=np.array([0,0,1e-5])
    with pytest.raises(ContractError,match='static classification'):
        key(renderer,reg,room)


def test_material_owner_change_invalidates_cache_key():
    renderer,reg,room=sample()
    old=key(renderer,reg,room)
    reg['surfaces'][0]['semantic_owner_index']=1
    assert key(renderer,reg,room)!=old
