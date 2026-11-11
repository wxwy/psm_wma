"""F13 GPU same-object 3D nearest colored voxel recovery.

Transforms the expensive G2 per-owner SciPy cKDTree query into exact radius-
restricted dense-grid neighbor lookups over native uniformly quantized voxels.
This F13 prototype supports an axis-aligned regular voxel grid (as in the
certified RoboCasa Layout1/10) and FAILS CLOSED for irregular input.
Unknown native source owner (-1) is queried only after the same-owner pass,
never promoted to a semantic identity.
"""
import math
import time
import numpy as np
from OpenGL import GL as gl

BUILD="""#version 460 core
#extension GL_ARB_gpu_shader_fp64 : require
#pragma STDGL invariant(all)
layout(local_size_x=256) in;
layout(std430,binding=0) readonly buffer Position { double xyz[]; };
layout(std430,binding=8) buffer SpatialIndex { uint slot[]; };
layout(std430,binding=11) buffer Collisions { uint collision_count[]; };
uniform int uN;
uniform ivec3 uDims;
uniform precise dvec3 uMin;
uniform precise double uLeaf;
void main(){
 uint i=gl_GlobalInvocationID.x;
 if(i>=uint(uN))return;
 precise dvec3 p=dvec3(xyz[i*3],xyz[i*3+1],xyz[i*3+2]);
 ivec3 c=ivec3(round((p-uMin)/uLeaf));
 if(any(lessThan(c,ivec3(0)))||any(greaterThanEqual(c,uDims))){
   atomicAdd(collision_count[0],1u);return;
 }
 uint offset=uint(c.x + uDims.x*(c.y+uDims.y*c.z));
 uint previous=atomicCompSwap(slot[offset],0u,i+1u);
 if(previous!=0u&&previous!=i+1u)atomicAdd(collision_count[0],1u);
}
"""
SEARCH="""#version 460 core
#extension GL_ARB_gpu_shader_fp64 : require
#pragma STDGL invariant(all)
layout(local_size_x=128) in;
layout(std430,binding=0) readonly buffer Position { double xyz[]; };
layout(std430,binding=2) readonly buffer Owner { int owner[]; };
layout(std430,binding=3) readonly buffer Valid { uint validity[]; };
layout(std430,binding=8) readonly buffer SpatialIndex { uint slot[]; };
layout(std430,binding=9) readonly buffer QueryPos { double queries[]; };
layout(std430,binding=10) readonly buffer QueryOwner { int query_owner[]; };
layout(std430,binding=12) writeonly buffer Answers { int closest[]; };
uniform int uQueryCount;
uniform ivec3 uDims;
uniform precise dvec3 uMin;
uniform precise double uLeaf;
uniform precise double uRadiusSq;
uniform int uSearchCellRadius;
uniform int uFallbackToUnknown;
void main(){
 uint qi=gl_GlobalInvocationID.x;
 if(qi>=uint(uQueryCount))return;
 precise dvec3 query=dvec3(queries[qi*3],queries[qi*3+1],queries[qi*3+2]);
 int targetOwner=query_owner[qi];
 ivec3 center=ivec3(round((query-uMin)/uLeaf));
 int found=-1;
 precise double best=uRadiusSq;
 precise double second=uRadiusSq;
 for(int dz=-uSearchCellRadius;dz<=uSearchCellRadius;++dz){
  int iz=center.z+dz;
  if(iz<0||iz>=uDims.z)continue;
  for(int dy=-uSearchCellRadius;dy<=uSearchCellRadius;++dy){
   int iy=center.y+dy;
   if(iy<0||iy>=uDims.y)continue;
   for(int dx=-uSearchCellRadius;dx<=uSearchCellRadius;++dx){
    int ix=center.x+dx;
    if(ix<0||ix>=uDims.x)continue;
    uint id=slot[ix+uDims.x*(iy+uDims.y*iz)];
    if(id==0u)continue;
    int src=int(id-1u);
    if(validity[src]==0u)continue;
    if(uFallbackToUnknown==0) {
     if(owner[src]!=targetOwner) continue;
    } else {
     if(owner[src]!=-1)continue;
    }
    precise dvec3 p=dvec3(xyz[src*3],xyz[src*3+1],xyz[src*3+2]);
    precise dvec3 delta=p-query;
    precise double dsq=dot(delta,delta);
    if(dsq<best || (dsq==best && (found<0 || src<found))){
      second=best;
      best=dsq;found=src;
    } else if(dsq<second){
      second=dsq;
    }
   }
  }
 }
 // The old SciPy cKDTree can resolve near-equal lattice neighbors in
 // a different order from the GPU grid walk. Mark only those ambiguous
 // pixels for exact CPU parity arbitration. No threshold is relaxed
 // for accepting color; this only chooses between source samples.
 if(found>=0 && second<uRadiusSq && sqrt(second)-sqrt(best) <= 1.0e-6)
    closest[qi]=-2;
 else
    closest[qi]=found;
}
"""

def _program(src):
    shader=gl.glCreateShader(gl.GL_COMPUTE_SHADER)
    gl.glShaderSource(shader,src)
    gl.glCompileShader(shader)
    if not gl.glGetShaderiv(shader,gl.GL_COMPILE_STATUS):
        raise RuntimeError("F13 nearest shader compile "+str(gl.glGetShaderInfoLog(shader)))
    p=gl.glCreateProgram()
    gl.glAttachShader(p,shader)
    gl.glLinkProgram(p)
    gl.glDeleteShader(shader)
    if not gl.glGetProgramiv(p,gl.GL_LINK_STATUS):
        raise RuntimeError("F13 nearest shader link "+str(gl.glGetProgramInfoLog(p)))
    return p

def _buf(arr):
    v=np.ascontiguousarray(arr)
    idx=gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,idx)
    gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER,v.nbytes,v,gl.GL_DYNAMIC_DRAW)
    return idx

class NearestGrid:
    def __init__(self,projector):
        self.projector=projector
        self.projector.ctx.make_current()
        self.build_shader=_program(BUILD)
        self.query_shader=_program(SEARCH)
        self.grid=0
        self.source_id=None
        self.voxel_leaf=None
        self.min_xyz=None
        self.dims=None
        self.build_s=0.
        self.collision_count=0
    def ensure_grid(self,xyz,leaf):
        self.projector.ctx.make_current()
        src_id=id(xyz)
        if self.source_id==src_id and self.voxel_leaf==leaf and self.grid:
            return
        if leaf<=0 or leaf>.05: raise ValueError("F13 nearest voxel size invalid")
        # This memory-aware dense indexing is a GPU acceleration of an
        # already formed ColorCloudMap, NOT an additional persistent map file.
        points=np.asarray(xyz,np.float64)
        minimum=points.min(axis=0)
        maximum=points.max(axis=0)
        for start in range(0,len(points),200_000):
            lattice=(points[start:start+200_000]-minimum)/leaf
            if not np.all(np.abs(lattice-np.rint(lattice))<=1.e-5):
                raise ValueError('GPU nearest requires an axis-aligned regular voxel grid in the Room frame')
        dims=np.ceil((maximum-minimum)/leaf-1.e-6).astype(np.int32)+1
        if np.any(dims<1) or np.prod(dims,dtype=np.int64)>200_000_000:
            raise ValueError("F13 dense GPU index would exceed 800MB; no non-uniform fallback authorized")
        self.min_xyz=minimum
        self.dims=dims
        self.voxel_leaf=leaf
        if self.grid:
            gl.glDeleteBuffers(1,[self.grid]);self.grid=0
        start=time.perf_counter()
        self.grid=gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,self.grid)
        n=int(np.prod(dims,dtype=np.int64))
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER,n*4,None,gl.GL_DYNAMIC_DRAW)
        gl.glClearBufferData(gl.GL_SHADER_STORAGE_BUFFER,gl.GL_R32UI,gl.GL_RED_INTEGER,gl.GL_UNSIGNED_INT,np.asarray([0],np.uint32))
        counter=_buf(np.asarray([0],np.uint32))
        try:
            for i,b in enumerate(self.projector.buffers):
                gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,i,b)
            gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,8,self.grid)
            gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,11,counter)
            gl.glUseProgram(self.build_shader)
            gl.glUniform1i(gl.glGetUniformLocation(self.build_shader,"uN"),len(points))
            gl.glUniform3iv(gl.glGetUniformLocation(self.build_shader,"uDims"),1,dims)
            gl.glUniform3dv(gl.glGetUniformLocation(self.build_shader,"uMin"),1,minimum)
            gl.glUniform1d(gl.glGetUniformLocation(self.build_shader,"uLeaf"),leaf)
            gl.glDispatchCompute((len(points)+255)//256,1,1)
            gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT|gl.GL_BUFFER_UPDATE_BARRIER_BIT)
            gl.glFinish()
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,counter)
            collisions=np.frombuffer(gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,4),dtype=np.uint32)
            self.collision_count=int(collisions[0])
            if self.collision_count!=0:
                raise RuntimeError(f"F13 GPU nearest cannot index nonuniform/colliding voxel input, collisions={self.collision_count}")
        finally:
            gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,11,0)
            gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,8,0)
            gl.glDeleteBuffers(1,[counter])
        self.source_id=src_id
        self.trees={} # SciPy cKDTree only for rare near-equal-distance ties
        self.build_s=time.perf_counter()-start
    def lookup(self,targets,owners,leaf,radius,fallback=False):
        self.projector.ctx.make_current()
        assert self.grid and self.voxel_leaf==leaf
        t=np.asarray(targets,np.float64)
        o=np.asarray(owners,np.int32)
        assert t.ndim==2 and t.shape[1]==3 and o.shape==(len(t),)
        if not len(t):
            return np.empty(0,dtype=np.int32),0.
        src=(t.reshape(-1),o,np.full(len(t),-1,np.int32))
        temp=[_buf(x) for x in src]
        try:
            for i,b in enumerate(self.projector.buffers):
                gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,i,b)
            gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,8,self.grid)
            for k,b in zip((9,10,12),temp):
                gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,k,b)
            gl.glUseProgram(self.query_shader)
            p=self.query_shader
            gl.glUniform1i(gl.glGetUniformLocation(p,"uQueryCount"),len(t))
            gl.glUniform3iv(gl.glGetUniformLocation(p,"uDims"),1,self.dims)
            gl.glUniform3dv(gl.glGetUniformLocation(p,"uMin"),1,self.min_xyz)
            gl.glUniform1d(gl.glGetUniformLocation(p,"uLeaf"),leaf)
            gl.glUniform1d(gl.glGetUniformLocation(p,"uRadiusSq"),radius*radius)
            gl.glUniform1i(gl.glGetUniformLocation(p,"uSearchCellRadius"),math.ceil(radius/leaf)+1)
            gl.glUniform1i(gl.glGetUniformLocation(p,"uFallbackToUnknown"),int(fallback))
            start=time.perf_counter()
            gl.glDispatchCompute((len(t)+127)//128,1,1)
            gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT|gl.GL_BUFFER_UPDATE_BARRIER_BIT)
            gl.glFinish()
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,temp[2])
            ans=np.frombuffer(gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,len(t)*4),dtype=np.int32).copy()
            cost=time.perf_counter()-start
            return ans,cost
        finally:
            for k in (9,10,12):
                gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,k,0)
            gl.glDeleteBuffers(len(temp),temp)
    def close(self):
        self.projector.ctx.make_current()
        if self.grid:gl.glDeleteBuffers(1,[self.grid])
        gl.glDeleteProgram(self.build_shader)
        gl.glDeleteProgram(self.query_shader)

def recover(projector,xyz,rgb,color_valid,owners,geometry,valid,image,depth,owner_image,
            uv_origin,right,up,forward,mpp,radius,leaf):
    """Return same (image,valid,filled,fallback,metrics) as CPU G2 helper."""
    t0=time.perf_counter()
    if not np.isfinite(radius) or radius<=0:raise ValueError("invalid G2 asset fill radius")
    if not hasattr(projector,"_nearest_grid"):
        projector._nearest_grid=NearestGrid(projector)
    engine=projector._nearest_grid
    engine.ensure_grid(xyz,leaf)
    h,w=valid.shape
    def resolve_near_tie(candidate,query_points,query_owner,query_radius,unknown=False):
        # The GPU handles the vast majority of nearest-neighbor searches.
        # SciPy G2 arbitration is used only when 2+ source samples lie within
        # 1 micrometer of the same closest distance. This preserves the
        # golden cKDTree choice for texture seams and coplanar wall surfaces.
        from scipy.spatial import cKDTree
        positions=np.flatnonzero(candidate==-2)
        start=time.perf_counter()
        if not len(positions):
            return candidate,0,0.
        for obj_id in ([-1] if unknown else sorted(set(query_owner[positions].tolist()))):
            affected=positions if unknown else positions[query_owner[positions]==obj_id]
            if not len(affected):
                continue
            if obj_id not in engine.trees:
                sample=np.flatnonzero((owners==obj_id)&color_valid)
                engine.trees[obj_id]=(sample,cKDTree(xyz[sample])) if len(sample) else (sample,None)
            sample,tree=engine.trees[obj_id]
            if tree is None:
                candidate[affected]=-1
                continue
            dist,nearest=tree.query(query_points[affected],k=1,distance_upper_bound=query_radius,workers=1)
            found=np.isfinite(dist)
            candidate[affected]=-1
            candidate[affected[found]]=sample[nearest[found]].astype(np.int32)
        return candidate,len(positions),time.perf_counter()-start
    def query_surface(rows,cols):
        uv0=uv_origin[0]+(cols+.5)*mpp
        uv1=uv_origin[1]+(h-rows-.5)*mpp
        return (uv0[:,None]*right+uv1[:,None]*up+depth[rows,cols,None]*forward)
    missing=geometry&~valid&(owner_image>=0)
    rr,cc=np.nonzero(missing)
    target=query_surface(rr,cc)
    closest,cost_same=engine.lookup(target,owner_image[rr,cc],leaf,radius,False)
    closest,same_ties,same_tie_cpu_s=resolve_near_tie(closest,target,owner_image[rr,cc],radius,False)
    mask=closest>=0
    rows1,cols1=rr[mask],cc[mask]
    image[rows1,cols1]=rgb[closest[mask]]
    valid[rows1,cols1]=True
    filled=int(mask.sum())
    still=geometry&~valid&(owner_image>=0)
    rr,cc=np.nonzero(still)
    target=query_surface(rr,cc)
    unassigned_index,cost_unknown=engine.lookup(target,owner_image[rr,cc],leaf,min(.06,radius),True)
    unassigned_index,unknown_ties,unknown_tie_cpu_s=resolve_near_tie(
       unassigned_index,target,owner_image[rr,cc],min(.06,radius),True)
    mask=unassigned_index>=0
    rows1,cols1=rr[mask],cc[mask]
    image[rows1,cols1]=rgb[unassigned_index[mask]]
    valid[rows1,cols1]=True
    fallback=int(mask.sum())
    stats={
       "gpu_nearest_total_s":round(time.perf_counter()-t0,6),
       "gpu_nearest_same_query_s":round(cost_same,6),
       "gpu_nearest_unknown_query_s":round(cost_unknown,6),
       "gpu_nearest_index_build_s_once":round(engine.build_s,6),
       "gpu_nearest_voxel_index_cells":int(np.prod(engine.dims,dtype=np.int64)),
       "cpu_near_tie_same_count":same_ties,
       "cpu_near_tie_unknown_count":unknown_ties,
       "cpu_near_tie_only_recovery_s":round(same_tie_cpu_s+unknown_tie_cpu_s,6),
       "gpu_nearest_same_filled":filled,
       "gpu_nearest_unknown_filled":fallback,
    }
    return image,valid,filled,fallback,stats
