"""GPU FP64 G2-compatible mesh Z-buffer, generated from native selected geometries.

Uses real G2 projection coordinates and CPU mesh iteration order. Each GPU
pixel checks only triangles crossing its 16x16 tile. Depth/owner semantics
mirror G2 rasterize() instead of approximate hardware interpolated Z.
"""
import time
import math
from pathlib import Path
import numpy as np
from mujoco import egl
from OpenGL import GL as gl
from g2.views.render import AXES

GLSL = """#version 460 core
#extension GL_ARB_gpu_shader_fp64 : require
#pragma STDGL invariant(all)
layout(local_size_x=16, local_size_y=16,local_size_z=1) in;
layout(std430,binding=0) readonly buffer Triangles { double vals[]; };
layout(std430,binding=1) readonly buffer Owners { int tri_owner[]; };
layout(std430,binding=2) readonly buffer TileOffsets { int tile_off[]; };
layout(std430,binding=3) readonly buffer TileIndices { int tri_ids[]; };
layout(std430,binding=4) writeonly buffer OutputOwners { int owner_out[]; };
layout(std430,binding=5) writeonly buffer OutputDepths { double depth_out[]; };
layout(std430,binding=6) writeonly buffer OutputTriangles { int triangle_out[]; };
layout(std430,binding=7) writeonly buffer OutputBarycentric { double bary_out[]; };
layout(std430,binding=8) writeonly buffer OutputAmbiguity { int ambiguity_out[]; };
uniform int uWidth, uHeight, uTilesX;
const int MULTI_HIT_MAX = 32;
uniform int uHitCap;
uniform int uReturnHits;
uniform double uNear, uFar;
void main(){
 int x = int(gl_GlobalInvocationID.x);
 int y = int(gl_GlobalInvocationID.y);
 if(x >= uWidth || y >= uHeight) return;
 int pix = y * uWidth + x;
 int tile = (y / 16) * uTilesX + (x / 16);
 precise double px=double(x)+0.5;
 precise double py=double(y)+0.5;
 int hit_id[32]; int hit_tri[32]; double hit_z[32]; double hit_wa[32]; double hit_wb[32];
 bool truncated = false;
 if(uReturnHits == 2) {
   for(int j=0;j<uHitCap;++j){hit_id[j]=-2;hit_tri[j]=-1;hit_z[j]=1.0e30;hit_wa[j]=0.;hit_wb[j]=0.;}
 }
 int winner = -2;
 int winner_tri = -1;
 double winner_a = 0.0, winner_b = 0.0;
 int ambiguous = 0;
 precise double best=1.0e30;
 for(int offset=tile_off[tile];offset<tile_off[tile+1];++offset) {
  int tri=tri_ids[offset];
  int base=tri*9;
  precise double ax=vals[base],ay=vals[base+1],az=vals[base+2];
  double bx=vals[base+3],by=vals[base+4],bz=vals[base+5];
  double cx=vals[base+6],cy=vals[base+7],cz=vals[base+8];
  precise double det=(by-cy)*(ax-cx)+(cx-bx)*(ay-cy);
  if(abs(det)<1e-10) continue;
  precise double wa=((by-cy)*(px-cx)+(cx-bx)*(py-cy))/det;
  precise double wb=((cy-ay)*(px-cx)+(ax-cx)*(py-cy))/det;
  precise double wc=1.0-wa-wb;
  if(wa < -1e-10 || wb < -1e-10 || wc < -1e-10)continue;
  precise double z=wa*az+wb*bz+wc*cz;
  if(uReturnHits == 2) {
    if(z < uNear-1e-9 || z > uFar+1e-9) continue;
    // A triangulation edge must not double a material surface. Distinct
    // Geoms at the same depth remain distinct uncertain candidates.
    bool same_surface=false;
    for(int j=0;j<uHitCap;++j)
      if(hit_id[j]==tri_owner[tri] && abs(hit_z[j]-z)<=1e-9) same_surface=true;
    if(same_surface) continue;
    int insertion=0;
    // Preserve strict numerical depth ordering. Tolerance applies only to
    // same-Geom seam deduplication, never to front/back rank ordering.
    while(insertion<uHitCap && z>=hit_z[insertion]) ++insertion;
    if(insertion<uHitCap){
      if(hit_id[uHitCap-1]>=0) truncated=true;
      for(int j=uHitCap-1;j>insertion;--j){
        hit_id[j]=hit_id[j-1];hit_tri[j]=hit_tri[j-1];
        hit_z[j]=hit_z[j-1];hit_wa[j]=hit_wa[j-1];hit_wb[j]=hit_wb[j-1];
      }
      hit_id[insertion]=tri_owner[tri]; hit_tri[insertion]=tri;
      hit_z[insertion]=z;hit_wa[insertion]=wa;hit_wb[insertion]=wb;
    } else truncated=true;
    continue;
  }
  if(z<best && z>=uNear-1e-9 && z<=uFar+1e-9){
    if(best-z>1e-9) ambiguous=0;
    else if(winner>=0 && winner!=tri_owner[tri]) ambiguous=1;
    best=z;winner=tri_owner[tri];winner_tri=tri;winner_a=wa;winner_b=wb;
  }else if(abs(z-best)<=1e-9 && z>=uNear-1e-9 && z<=uFar+1e-9 && winner!=tri_owner[tri]){
    ambiguous=1;
  }
 }
 if(uReturnHits==2){
  int stride=uWidth*uHeight;
  for(int j=0;j<uHitCap;++j){
    int slot=pix+j*stride;
    owner_out[slot]=hit_id[j];
    depth_out[slot]=hit_z[j];
    triangle_out[slot]=hit_tri[j];
    bary_out[slot*2]=hit_wa[j];bary_out[slot*2+1]=hit_wb[j];
  }
  ambiguity_out[pix]=truncated ? 1 : 0;
  return;
 }
 owner_out[pix]=winner;
 depth_out[pix]=best;
 if(uReturnHits!=0){
   triangle_out[pix]=winner_tri;
   bary_out[pix*2]=winner_a;bary_out[pix*2+1]=winner_b;
   ambiguity_out[pix]=ambiguous;
 }
}
"""

def glbuf(arr):
    arr=np.ascontiguousarray(arr)
    b=gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,b)
    gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER,arr.nbytes,arr,gl.GL_DYNAMIC_DRAW)
    return b

class ExactGPURaster:
    def __init__(self):
        self.ctx=egl.GLContext(2048,2048)
        self.ctx.make_current()
        src=gl.glCreateShader(gl.GL_COMPUTE_SHADER)
        gl.glShaderSource(src,GLSL)
        gl.glCompileShader(src)
        if not gl.glGetShaderiv(src,gl.GL_COMPILE_STATUS):
            raise RuntimeError(f"GLSL compile failed: {gl.glGetShaderInfoLog(src)}")
        self.program=gl.glCreateProgram()
        gl.glAttachShader(self.program,src)
        gl.glLinkProgram(self.program)
        gl.glDeleteShader(src)
        if not gl.glGetProgramiv(self.program,gl.GL_LINK_STATUS):
            raise RuntimeError(f"GLSL link failed: {gl.glGetProgramInfoLog(self.program)}")
    def draw_layers(self,meshes,selected,low,high,axis,mpp,*,max_hits=8):
        # A full source ray can carry several distinct front/back interfaces.
        # Use small K=8 for real-time transparency; K=32 on rare depth ties.
        if max_hits not in (8,32):
            raise ValueError("unsupported verified multi-hit capacity")
        return self.draw(meshes,selected,low,high,axis,mpp,return_hits=True,
                         return_layers=max_hits)

    def draw_hits(self,meshes,selected,low,high,axis,mpp):
        """Return exact original face index/barycentric with the winning surface.

        IDs are caller-defined nonnegative surface indices, independent of SG
        owners. The legacy draw tuple stays unchanged unless hits are requested.
        """
        return self.draw(meshes,selected,low,high,axis,mpp,return_hits=True)

    def draw(self,meshes,selected,low,high,axis,mpp,*,return_hits=False,return_layers=0):
        self.ctx.make_current()
        start=time.perf_counter()
        right,up,forward=(np.asarray(v,dtype=np.float64) for v in AXES[axis])
        lo=np.asarray(low,dtype=np.float64)
        hi=np.asarray(high,dtype=np.float64)
        corners=np.asarray([[x,y,z] for x in (lo[0],hi[0])
                              for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
        uv=corners@np.stack([right,up],axis=1)
        origin=np.floor(uv.min(axis=0)/mpp)*mpp
        dimensions=np.floor((uv.max(axis=0)-origin)/mpp+1e-8).astype(np.int64)+1
        w,h=map(int,dimensions)
        if w*h>4_000_000 or w<1 or h<1:raise ValueError("G2 view dimensions out of bounds")
        near=float((corners@forward).min())
        far=float((corners@forward).max())
        tiles_x=(w+15)//16
        tiles_y=(h+15)//16
        bins=[[] for _ in range(tiles_x*tiles_y)]
        alltri=[]
        allowner=[]
        allface=[]
        tris_tested=0
        bucketed=0
        for entity,vertices,triangles in meshes:
            if entity not in selected:continue
            vertices=np.asarray(vertices,dtype=np.float64)
            faces=np.asarray(triangles,dtype=np.int32)
            if not vertices.size or not faces.size:continue
            projected=np.column_stack([
                (vertices@right-origin[0])/mpp,
                (vertices@up-origin[1])/mpp,
                vertices@forward
            ])
            triangles_proj=projected[faces]
            x0=np.maximum(0,np.floor(triangles_proj[:,:,0].min(axis=1)).astype(np.int32))
            x1=np.minimum(w-1,np.floor(triangles_proj[:,:,0].max(axis=1)).astype(np.int32))
            y0=np.maximum(0,np.floor(triangles_proj[:,:,1].min(axis=1)).astype(np.int32))
            y1=np.minimum(h-1,np.floor(triangles_proj[:,:,1].max(axis=1)).astype(np.int32))
            eligible=(x1>=x0)&(y1>=y0)
            # All nontrivial triangles get unique IDs in the original G2
            # object-and-face order, even when they do not intersect a pixel.
            for i in np.flatnonzero(eligible):
                t=triangles_proj[i]
                det=(t[1,1]-t[2,1])*(t[0,0]-t[2,0])+(t[2,0]-t[1,0])*(t[0,1]-t[2,1])
                if abs(det)<1e-10:continue
                index=len(alltri)
                alltri.append(t.reshape(-1))
                allowner.append(int(entity))
                allface.append(int(i))
                for ty in range(y0[i]//16,y1[i]//16+1):
                    for tx in range(x0[i]//16,x1[i]//16+1):
                        bins[ty*tiles_x+tx].append(index)
                        bucketed+=1
                tris_tested+=1
        prep_s=time.perf_counter()-start
        if not alltri: raise ValueError("no G2 selected projectable geometry")
        coords=np.ascontiguousarray(np.asarray(alltri,dtype=np.float64).reshape(-1))
        owners=np.ascontiguousarray(np.asarray(allowner,dtype=np.int32))
        tile_counts=np.fromiter(map(len,bins),dtype=np.int32,count=len(bins))
        offsets=np.empty(len(bins)+1,dtype=np.int32)
        offsets[0]=0
        offsets[1:]=np.cumsum(tile_counts)
        triids=np.ascontiguousarray(
            np.fromiter((i for bucket in bins for i in bucket),dtype=np.int32,count=int(offsets[-1])))
        n=w*h
        slots=n*(return_layers if return_layers else 1)
        buffers=[]
        start=time.perf_counter()
        try:
            for x in (coords,owners,offsets,triids,np.empty(slots,np.int32),np.empty(slots,np.float64),
                      np.empty(slots if return_hits else 1,np.int32),
                      np.empty(slots*2 if return_hits else 1,np.float64),
                      np.empty(n if return_hits else 1,np.int32)):
                buffers.append(glbuf(x))
            for i,b in enumerate(buffers):gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,i,b)
            gl.glUseProgram(self.program)
            gl.glUniform1i(gl.glGetUniformLocation(self.program,"uWidth"),w)
            gl.glUniform1i(gl.glGetUniformLocation(self.program,"uHeight"),h)
            gl.glUniform1i(gl.glGetUniformLocation(self.program,"uTilesX"),tiles_x)
            gl.glUniform1i(gl.glGetUniformLocation(self.program,"uReturnHits"),2 if return_layers else int(return_hits))
            gl.glUniform1i(gl.glGetUniformLocation(self.program,"uHitCap"),
                           int(return_layers) if return_layers else 1)
            gl.glUniform1d(gl.glGetUniformLocation(self.program,"uNear"),near)
            gl.glUniform1d(gl.glGetUniformLocation(self.program,"uFar"),far)
            start_kernel=time.perf_counter()
            gl.glDispatchCompute(tiles_x,tiles_y,1)
            gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT|gl.GL_BUFFER_UPDATE_BARRIER_BIT)
            gl.glFinish()
            kernel_s=time.perf_counter()-start_kernel
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,buffers[4])
            owner_bytes=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,slots*4)
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,buffers[5])
            depth_bytes=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,slots*8)
            owners_img=np.frombuffer(owner_bytes,dtype="<i4").reshape((-1,h,w) if return_layers else (h,w))
            depth_img=np.frombuffer(depth_bytes,dtype="<f8").reshape((-1,h,w) if return_layers else (h,w))
            if return_layers:
                owners_img=owners_img[:,::-1].copy()
                depth_img=depth_img[:,::-1].copy()
            else:
                owners_img=owners_img[::-1].copy()
                depth_img=depth_img[::-1].copy()
            depth_img[owners_img<0]=np.nan
            if return_hits:
                gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,buffers[6])
                triangle_bytes=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,slots*4)
                gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,buffers[7])
                bary_bytes=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,slots*16)
                gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,buffers[8])
                ambiguity_bytes=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,n*4)
                hit_tri=np.frombuffer(triangle_bytes,dtype="<i4").reshape((-1,h,w) if return_layers else (h,w))
                hit_tri=hit_tri[:,::-1].copy() if return_layers else hit_tri[::-1].copy()
                hit_faces=np.full(hit_tri.shape,-1,np.int32)
                occupied=hit_tri>=0
                hit_faces[occupied]=np.asarray(allface,dtype=np.int32)[hit_tri[occupied]]
                weights=np.frombuffer(bary_bytes,dtype="<f8").reshape((-1,h,w,2) if return_layers else (h,w,2))
                weights=weights[:,::-1].copy() if return_layers else weights[::-1].copy()
                hit_weights=np.concatenate((weights,1-weights.sum(axis=-1,keepdims=True)),axis=-1)
                hit_weights[~occupied]=np.nan
                hit_ambiguity=np.frombuffer(ambiguity_bytes,dtype='<i4').reshape(h,w)[::-1].astype(bool)
            total_gpu_s=time.perf_counter()-start
        finally:
            for i in range(9):gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,i,0)
            if buffers:gl.glDeleteBuffers(len(buffers),buffers)
        info={
            "triangles":tris_tested,
            "tile_references":bucketed,
            "tile_count":len(bins),
            "tile_p95_candidates":int(np.percentile(tile_counts,95)),
            "prepare_geometry_tiles_s":round(prep_s,6),
            "GPU_upload_dispatch_readback_s":round(total_gpu_s,6),
            "GPU_kernel_s":round(kernel_s,6),
            "dimensions":[w,h],
            "multi_hit_cap":return_layers if return_layers else 1,
            "multi_hit_overflow_pixels":int(hit_ambiguity.sum()) if return_layers else 0
        }
        result=(owners_img>=0,depth_img,owners_img,(w,h),info)
        return (*result,hit_faces,hit_weights,hit_ambiguity) if return_hits else result
    def close(self):
        self.ctx.make_current()
        gl.glDeleteProgram(self.program)
        self.ctx.free()


_ENGINE=None
def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE=ExactGPURaster()
    return _ENGINE

def close_engine():
    global _ENGINE
    if _ENGINE is not None:
        _ENGINE.close()
        _ENGINE=None
