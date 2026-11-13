"""Full opt-in MaterialResolver parity: fresh models; no production mutation."""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
import numpy as np
import mujoco
import pytest

from g2.io import ContractError
from g2.sim.material_resolver import MaterialResolver as CandidateResolver

# Original eager implementation is preserved behind the default-off flag.
ProductionMaterialResolver=CandidateResolver


def eq(a,b):
    if isinstance(a,np.ndarray):
        assert isinstance(b,np.ndarray) and a.shape==b.shape and a.dtype==b.dtype
        np.testing.assert_array_equal(a,b,strict=True)
    elif dataclasses.is_dataclass(a):
        assert type(a).__name__==type(b).__name__
        for f in dataclasses.fields(a):eq(getattr(a,f.name),getattr(b,f.name))
    elif isinstance(a,(dict,list,tuple)):
        assert type(a)==type(b)
        if isinstance(a,dict):
            assert a.keys()==b.keys()
            for k in a: eq(a[k],b[k])
        else:
            assert len(a)==len(b)
            for x,y in zip(a,b):eq(x,y)
    else:
        assert a==b,(type(a),a,b)


def compare(model,geom,kind,faces,bary,pts):
    prod=ProductionMaterialResolver(model,source_sha256="e"*64)
    old_default=CandidateResolver(model,source_sha256="e"*64)
    lazy=CandidateResolver(model,source_sha256="e"*64,lazy_texel_decode=True)
    eq(prod.descriptor(geom,kind),old_default.descriptor(geom,kind))
    eq(prod.descriptor(geom,kind),lazy.descriptor(geom,kind))
    original=prod.sample(geom,kind,faces,bary,local_points=pts)
    default=old_default.sample(geom,kind,faces,bary,local_points=pts)
    candidate=lazy.sample(geom,kind,faces,bary,local_points=pts)
    eq(original,default)
    eq(original,candidate)
    assert len(lazy._textures)==0
    assert lazy._raw_textures or prod.texture_decode_count==0
    # After sampling a second time, lazy bytes remain cached and exact
    repeat=lazy.sample(geom,kind,faces,bary,local_points=pts)
    eq(original,repeat)
    return prod,lazy


def test_default_off_guard():
    m=mujoco.MjModel.from_xml_string(
        '<mujoco><worldbody><geom type="box" size=".2 .2 .2"/></worldbody></mujoco>')
    r=CandidateResolver(m)
    assert not r.lazy_texel_decode
    with pytest.raises(ContractError,match="boolean"):
        CandidateResolver(m,lazy_texel_decode=1)
    assert not r._raw_textures


@pytest.mark.parametrize("kind",["box","sphere","cylinder","ellipsoid","mesh","capsule"])
@pytest.mark.parametrize("space",["sRGB","linear"])
@pytest.mark.parametrize("alpha",[0.25,1.0])
def test_generated_2d_synthetic(kind,space,alpha):
    from g2.tests.test_material_resolver import _model
    model=_model(colorspace=space,kind=kind,alpha=alpha)
    n=30
    rng=np.random.default_rng(1729)
    face=np.zeros(n,np.int64)
    bary=rng.dirichlet([1,1,1],size=n)
    pts=rng.normal(size=(n,3)) * np.array([.2,.3,.4])
    # Include UV texture wrap and ties in valid primitives
    pts[:5]=[[0,0,0],[0,0,.4],[.2,.3,.4],[-.2,-.3,-.4],[.1,.2,.3]]
    compare(model,0,kind,face,bary,pts)


def test_compiled_srgb_cube_and_alpha_reference():
    model=mujoco.MjModel.from_xml_string(
        '<mujoco><asset><texture name="t" type="cube" builtin="flat"'
        ' width="2" height="2" rgb1="1 1 1" colorspace="sRGB"/>'
        '<material name="m" texture="t" rgba="1 1 1 .5"/></asset>'
        '<worldbody><geom type="box" size=".2 .3 .4" material="m"/></worldbody></mujoco>')
    raw=np.asarray(model.tex_data).reshape(6,2,2,3)
    raw[:]=255
    raw[0]=128
    points=np.asarray([[.2,0,0],[0,.3,0],[0,0,.4],[-.2,0,0],[0,0,0],[.2,.2,.2]])
    n=len(points)
    compare(model,0,"box",np.zeros(n,np.int64),np.tile([1.,0.,0.],(n,1)),points)


@pytest.mark.parametrize("space",["sRGB","linear"])
def test_varying_rgba_source_evidence(space):
    from PIL import Image
    import io
    image=np.asarray([[[0,0,0,0],[255,255,255,128]],
                      [[128,90,75,255],[40,255,20,100]]],np.uint8)
    b=io.BytesIO();Image.fromarray(image,"RGBA").save(b,format="PNG")
    model=mujoco.MjModel.from_xml_string(
        '<mujoco><asset><texture name="t" type="2d" file="rgba.png"'
        f' nchannel="4" colorspace="{space}"/>'
        '<material name="m" texture="t" rgba=".9 .6 .7 .5"/>'
        '</asset><worldbody><geom type="box" size=".2 .3 .4" material="m"/></worldbody></mujoco>',
        assets={"rgba.png":b.getvalue()})
    rng=np.random.default_rng(77)
    n=35
    pts=rng.uniform(-1,1,size=(n,3))
    compare(model,0,"box",np.zeros(n,np.int64),np.tile([1.,0.,0.],(n,1)),pts)


def test_shared_texture_mutation_invalidation_and_caching():
    from g2.tests.test_material_resolver import _model
    model=_model(colorspace="sRGB",second_geom=True)
    a=ProductionMaterialResolver(model)
    b=CandidateResolver(model,lazy_texel_decode=True)
    p=np.array([[0.,0.,.4]])
    bary=np.array([[1.,0.,0.]])
    faces=np.array([0])
    for geom in (0,1):
        eq(a.descriptor(geom,"box"),b.descriptor(geom,"box"))
        eq(a.sample(geom,"box",faces,bary,local_points=p),
           b.sample(geom,"box",faces,bary,local_points=p))
    assert len(b._raw_textures)==1 and len(b._textures)==0
    assert b.texture_decode_count==0
    assert b.raw_texture_load_count==1
    assert b.raw_texture_cache_hits>0
    model.tex_data[:]=255
    # Original and lazy caches must remain stale until explicit invalidation.
    old=b.sample(0,"box",faces,bary,local_points=p)
    b.invalidate(0)
    a.invalidate(0)
    assert not b._raw_textures
    fresh=b.sample(0,"box",faces,bary,local_points=p)
    eq(a.sample(0,"box",faces,bary,local_points=p),fresh)
    assert not np.array_equal(old.rgb_linear,fresh.rgb_linear)


def test_large_model_exact_real_texture_sample():
    # Gate is skipped unless a stable, independently completed source asset exists.
    source=os.environ.get("G2_F27_REAL_SOURCE_MJCF","")
    if not source:
        pytest.skip("set G2_F27_REAL_SOURCE_MJCF to enable real-asset parity")
    path=Path(source)
    if not path.is_file():
        pytest.skip("explicit real-asset source path is absent")
    model=mujoco.MjModel.from_xml_path(str(path))
    kind_map={
        int(getattr(mujoco.mjtGeom,"mjGEOM_"+k.upper())):k
        for k in ("box","sphere","cylinder","capsule","mesh","ellipsoid")}
    texture_role=int(mujoco.mjtTextureRole.mjTEXROLE_RGB)
    possible=[]
    for gid in range(model.ngeom):
        mid=int(model.geom_matid[gid])
        if mid<0:continue
        tid=int(model.mat_texid[mid,texture_role])
        kind=kind_map.get(int(model.geom_type[gid]))
        if tid>=0 and kind in ("box","sphere","cylinder","mesh","ellipsoid"):
            possible.append((gid,kind,tid))
    assert possible
    # Test two distinct, representative real textures; CPU memory safe under live GPU load.
    seen=set()
    tested=0
    for g,kind,t in possible:
        if t in seen:continue
        seen.add(t)
        n=256
        face=np.zeros(n,np.int64)
        rng=np.random.default_rng(145+t)
        bary=rng.dirichlet([1,1,1],size=n)
        pts=rng.uniform(-.1,.1,size=(n,3))
        compare(model,g,kind,face,bary,pts)
        tested+=1
        if tested>=2:break
    assert tested>=2
