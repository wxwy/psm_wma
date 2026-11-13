"""G2 F27 lazy texel decoding microbenchmark — isolated, READ-ONLY.
Never changes PSM-WMA, nav_sg, production work trees or any running process.
"""
from __future__ import annotations

import argparse
import time
import numpy as np
import mujoco

from g2.sim.material_resolver import MaterialResolver
from g2.sim.texture_projection import _bilinear, _cube, srgb_to_linear


def raw_texture(model, tex):
    w=int(model.tex_width[tex]); h=int(model.tex_height[tex])
    c=int(model.tex_nchannel[tex]); start=int(model.tex_adr[tex])
    raw=np.asarray(model.tex_data)[start:start+w*h*c].reshape(h,w,c)
    return raw


def decode_texels(texels, srgb):
    out=np.asarray(texels,dtype=np.float64)/255.0
    if srgb:
        out[...,:3]=srgb_to_linear(out[...,:3])
    return out


def lazy_bilinear(pixels_uint8, uv, repeat, srgb=False):
    """Byte-preserving sparse texture decode matching historical _bilinear order."""
    height,width=pixels_uint8.shape[:2]
    uv=np.asarray(uv,dtype=np.float64)
    xy=(uv%1 if repeat else np.clip(uv,0,1))*[width,height]-.5
    lower=np.floor(xy).astype(np.int64)
    fraction=xy-lower
    colors=np.zeros((len(uv),pixels_uint8.shape[2]),dtype=np.float64)
    for dx,dy in ((0,0),(1,0),(0,1),(1,1)):
        x,y=lower[:,0]+dx,lower[:,1]+dy
        x=x%width if repeat else np.clip(x,0,width-1)
        y=y%height if repeat else np.clip(y,0,height-1)
        weight=(fraction[:,0] if dx else 1-fraction[:,0])*(fraction[:,1] if dy else 1-fraction[:,1])
        pixels=decode_texels(pixels_uint8[y,x],srgb)
        colors+=pixels*weight[:,None]
    return colors


def lazy_cube(pixels_uint8, direction, srgb=False):
    """Same face priority/ambiguity semantics as g2.sim.texture_projection._cube."""
    magnitude=np.max(np.abs(direction),axis=1)
    usable=np.isfinite(direction).all(axis=1)&(magnitude>0)
    tied=np.isclose(np.abs(direction),magnitude[:,None],rtol=1e-12,atol=0)
    transforms=((2,-1,1,-1),(2,1,1,-1),(0,1,2,1),
                (0,1,2,-1),(0,1,1,-1),(0,-1,1,-1))
    c=np.zeros((len(direction),3)); assigned=np.zeros(len(direction),bool)
    uncertain=np.zeros(len(direction),bool)
    for face,(s_axis,s_sign,t_axis,t_sign) in enumerate(transforms):
        axis=face//2
        selected=usable&tied[:,axis]&((direction[:,axis]>=0) if face%2==0 else (direction[:,axis]<0))
        indices=np.flatnonzero(selected)
        if not len(indices):continue
        uv=np.column_stack([direction[indices,s_axis]*s_sign,direction[indices,t_axis]*t_sign])
        uv=.5*(uv/magnitude[indices,None]+1)
        panel=pixels_uint8[face] if pixels_uint8.ndim==4 else pixels_uint8
        candidate=lazy_bilinear(panel,uv,False,srgb=srgb)
        different=np.max(np.abs(c[indices]-candidate),axis=1)>1e-12
        uncertain[indices]|=assigned[indices]&different
        new=~assigned[indices]
        c[indices[new]]=candidate[new]
        assigned[indices]=True
    return c,usable&~uncertain,uncertain


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',required=True)
    p.add_argument('--n',type=int,default=16020)
    args=p.parse_args()
    started=time.perf_counter()
    model=mujoco.MjModel.from_xml_path(args.model)
    print('MODEL_LOAD_S',round(time.perf_counter()-started,2),'NGEOMS',model.ngeom,'NTEX',model.ntex,flush=True)
    selected=[3,23,4]
    spaces=np.asarray(model.tex_colorspace)
    srgb_tag=int(mujoco.mjtColorSpace.mjCOLORSPACE_SRGB)
    srgb_ids=np.flatnonzero(spaces==srgb_tag)
    if len(srgb_ids) and int(srgb_ids[0]) not in selected:selected.append(int(srgb_ids[0]))
    selected=[v for v in selected if v<model.ntex]
    rng=np.random.default_rng(20261113)
    uv=rng.uniform(-3.,3.,size=(args.n,2))
    uv[:12,:]=np.array([[0.,0.],[1.,1.],[.5,.5],[-1.,-.5],[2.,3.],[-1e-12,1e-12]])[[i%6 for i in range(12)]]
    direction=rng.normal(size=(max(3000,args.n//2),3))
    direction[:7]=[[0,0,0],[1,1,1],[-1,-1,-1],[1,0,0],[0,-1,0],[0,0,1],[0,0,-1]]
    resolver=MaterialResolver(model,source_sha256='0'*64)
    total_eager=0.
    total_lazy=0.
    for texture in selected:
        raw=raw_texture(model,texture)
        nraw=raw.nbytes
        srgb=bool(int(model.tex_colorspace[texture])==srgb_tag)
        t=time.perf_counter()
        uniform=not np.any(raw!=raw[0,0])
        detect=time.perf_counter()-t
        t=time.perf_counter()
        eager,space,eager_uniform=resolver._texture(texture,mujoco)
        eager_seconds=time.perf_counter()-t
        assert uniform==eager_uniform
        assert bool(space=='sRGB')==srgb
        total_eager+=eager_seconds
        print('TEXTURE',texture,'RAW_MIB',round(nraw/1048576,2),
              'FULL_FLOAT64_MIB',round(eager.nbytes/1048576,2),
              'SRGB',srgb,'UNIFORM',uniform,
              'RAW_CONSTANT_CHECK_S',round(detect,4),
              'FULL_TEXTURE_DECODE_S',round(eager_seconds,3),flush=True)
        # For uniform texture, neither path samples UVs in the production material resolver.
        # Check exact returned constant texel, not UV behavior.
        if uniform:
            got=decode_texels(raw[0,0],srgb)
            assert np.array_equal(got,eager[0,0])
            print('  CONSTANT_EXACT_PASS',flush=True)
            continue
        t=time.perf_counter()
        expect=_bilinear(eager,uv,True)
        full_sample_s=time.perf_counter()-t
        t=time.perf_counter()
        got=lazy_bilinear(raw,uv,True,srgb)
        lazy_s=time.perf_counter()-t
        total_lazy+=lazy_s
        if not np.array_equal(expect,got):
            mismatch=np.count_nonzero(expect!=got)
            delta=np.max(np.abs(expect-got))
            raise AssertionError(f'BILINEAR_EXACT_MISMATCH texture={texture} pixels={mismatch} delta={delta}')
        print('  BILINEAR_EXACT_PASS','SAMPLES',len(uv),
              'EAGER_SAMPLE_S',round(full_sample_s,4),'LAZY_SAMPLE_S',round(lazy_s,4),
              'SAME_BITS',True,flush=True)
        # Cube access pattern (6 faces) only for cube-type compiled textures.
        if int(model.tex_type[texture])==int(mujoco.mjtTexture.mjTEXTURE_CUBE):
            height,width=eager.shape[:2]
            if height in (width,6*width) and eager.shape[2]==3:
                faces=(np.repeat(eager[None],6,axis=0) if height==width else eager.reshape(6,width,width,3))
                raw_faces=(np.repeat(raw[None],6,axis=0) if height==width else raw.reshape(6,width,width,3))
                expect_cube=_cube(faces,direction)
                lazy_out=lazy_cube(raw_faces,direction,srgb)
                for left,right in zip(expect_cube,lazy_out):
                    if not np.array_equal(left,right):
                        raise AssertionError(f'CUBE_EXACT_MISMATCH texture={texture}')
                print('  CUBE_EXACT_PASS','SAMPLES',len(direction),flush=True)
    print('LAB_VALIDATION_COMPLETE','EAGER_TOTAL_DECODE_S',round(total_eager,2),
          'LAZY_TOTAL_S',round(total_lazy,2),
          'ELAPSED_S',round(time.perf_counter()-started,2),flush=True)


if __name__=='__main__':
    main()
