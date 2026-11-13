"""CPU small-View exact A/B against the original F27 SurfaceRenderer.

All render output in memory; original PSM-WMA/SG and 9,126 production untouched.
"""
from __future__ import annotations
import importlib
import os
from pathlib import Path
import numpy as np
import mujoco
import pytest

from g2.sim.material_resolver import MaterialResolver as CandidateResolver
from g2.tests.test_material_resolver import _model
from g2.sim.source_geometry import primitive_mesh
from g2.views.surface_registry import compile_surface_registry
from g2.views.surface_renderer import SurfaceRenderer


def one_geom_view(model, geom, *, source_sha="d"*64):
    data=mujoco.MjData(model)
    mujoco.mj_forward(model,data)
    gid=int(geom)
    kind_code=int(model.geom_type[gid])
    kindmap={
        int(getattr(mujoco.mjtGeom,"mjGEOM_"+name.upper())):name
        for name in ("box","sphere","cylinder","mesh","ellipsoid")}
    kind=kindmap[kind_code]
    if kind=="mesh":
        mid=int(model.geom_dataid[gid])
        vertices=np.asarray(model.mesh_vert[int(model.mesh_vertadr[mid]):int(model.mesh_vertadr[mid])+int(model.mesh_vertnum[mid])],float).copy()
        faces=np.asarray(model.mesh_face[int(model.mesh_faceadr[mid]):int(model.mesh_faceadr[mid])+int(model.mesh_facenum[mid])],int).copy()
    else:
        vertices,faces=primitive_mesh(kind,np.asarray(model.geom_size[gid],float))
    vertices=np.asarray(vertices,float)
    faces=np.asarray(faces,int)
    p=data.geom_xpos[gid]
    geom_world=vertices@data.geom_xmat[gid].reshape(3,3).T+p
    minimum=geom_world.min(0);maximum=geom_world.max(0)
    margin=.05
    lo=minimum-margin
    hi=maximum+margin
    # For the sake of bounded CPU sample sizes, cap total image pixels.
    xy=hi-lo
    if np.any(xy[:2]>1.0):
        raise ValueError("real geom too large for this isolated small-view test")
    room={
        "uid":0,"center":[0.,0.,0.],
        "reference_frame":{"origin_world":[0.,0.,0.],
                           "axes_world":np.eye(3).tolist()}}
    entity={"id":"entity_0","kind":"object","room_uid":0,
            "island_id":None,"root_affiliations":[]}
    snapshot={
        "scene_id":"tiny_f27_material_lab","source_sha256":source_sha,
        "entities":[entity],"rooms":[room],
        "connections":{"threshold_m":.3,"objects":[
            {"entity_id":"entity_0","floor_state":"YES"}]}}
    spec={"g":gid,"owner":0,"kind":kind,"vertices":vertices,"faces":faces,
          "source_kind":"source","source_instance":["geom",str(gid)]}
    registry=compile_surface_registry(model,data,[spec],snapshot)
    a=SurfaceRenderer(model,source_sha,{gid},backend="cpu")
    b=SurfaceRenderer(model,source_sha,{gid},backend="cpu",lazy_texel_decode=True)
    def render(r):
        return r.render(registry,room,{0},lo.tolist(),hi.tolist(),"floor_top",.02)
    base=render(a)
    alt=render(b)
    assert len(base)==len(alt)==7
    for idx in range(6):
        np.testing.assert_array_equal(base[idx],alt[idx],strict=True,err_msg=f"F27 view field #{idx}")
    em=base[6]["_pixel_evidence"]
    cm=alt[6]["_pixel_evidence"]
    assert em.keys()==cm.keys()
    for key in em:
        np.testing.assert_array_equal(em[key],cm[key],err_msg=f"pixel evidence {key}")
    assert base[6]["valid_color_pixels"] == alt[6]["valid_color_pixels"]
    assert base[6]["unknown_color_pixels"] == alt[6]["unknown_color_pixels"]
    assert base[6]["transparent_visible_pixels"] == alt[6]["transparent_visible_pixels"]
    assert len(a.materials._textures)==0 or b.materials._raw_textures
    assert len(b.materials._textures)==0
    return base


@pytest.mark.parametrize("alpha",[1.,.5])
@pytest.mark.parametrize("space",["sRGB","linear"])
def test_tiny_full_view_rgb_2d(alpha,space):
    model=_model(colorspace=space,kind="box",alpha=alpha)
    result=one_geom_view(model,0)
    assert result[0].shape[2]==3
    assert result[0].size>0


def test_small_real_compiled_mesh_view():
    source=os.environ.get("G2_F27_REAL_SOURCE_MJCF","")
    if not source:
        pytest.skip("set G2_F27_REAL_SOURCE_MJCF to enable real-asset view parity")
    path=Path(source)
    if not path.exists():
        pytest.skip("explicit real-asset source absent")
    model=mujoco.MjModel.from_xml_path(str(path))
    role=int(mujoco.mjtTextureRole.mjTEXROLE_RGB)
    selected=None
    for gid in range(model.ngeom):
        if int(model.geom_type[gid]) != int(mujoco.mjtGeom.mjGEOM_BOX):
            continue
        mat=int(model.geom_matid[gid])
        if mat<0:continue
        tid=int(model.mat_texid[mat,role])
        if tid<0 or int(model.tex_type[tid])!=int(mujoco.mjtTexture.mjTEXTURE_2D):
            continue
        s=model.geom_size[gid]
        if max(s)<=.25 and min(s)>.01:
            selected=gid
            break
    if selected is None:pytest.skip("no small textured geom for CPU raster oracle")
    result=one_geom_view(model,selected)
    assert result[0].shape[2]==3
