"""F13 isolated color-projection GPU compute: exact G2 lexsort pixel candidate.

All voxel color and object samples originate from the same persistent
ColorCloudMap-like input as G2. This kernel replaces only the expensive
per-view (selected xyz -> pixel -> depth/valid/RGB lexsort) stage, with a
3-dispatch deterministic min-reduction. Does not classify objects.
"""
import ctypes
import time
import numpy as np
from mujoco import egl
from OpenGL import GL as gl

SOURCE = """#version 460 core
#extension GL_ARB_gpu_shader_int64 : require
#extension GL_NV_shader_atomic_int64 : require
#extension GL_ARB_gpu_shader_fp64 : require
#pragma STDGL invariant(all)
layout(local_size_x=256) in;
layout(std430,binding=0) readonly buffer Position { double xyz[]; };
layout(std430,binding=1) readonly buffer PackedRGB { uint rgb[]; };
layout(std430,binding=2) readonly buffer Owner { int owner[]; };
layout(std430,binding=3) readonly buffer Valid { uint validity[]; };
layout(std430,binding=4) buffer BestDepth { uint64_t minZ[]; };
layout(std430,binding=5) buffer BestColor { uint minTie[]; };
layout(std430,binding=6) buffer BestIndex { uint firstIndex[]; };
layout(std430,binding=7) readonly buffer Selected { uint selected[]; };

uniform int N;
uniform int W;
uniform int H;
uniform int passIndex;
uniform precise dvec3 uRight;
uniform precise dvec3 uUp;
uniform precise dvec3 uForward;
uniform precise dvec3 uMin;
uniform precise dvec3 uMax;
uniform precise dvec2 uOrigin;
uniform precise double uMpp;

uint64_t depthKey(double z) {
 uvec2 bits = unpackDouble2x32(z);
 uint64_t u = (uint64_t(bits.y)<<32)|uint64_t(bits.x);
 uint64_t sign = 0x8000000000000000ul;
 return (u&sign)!=0ul ? ~u : (u ^ sign);
}
void main(){
 uint i=gl_GlobalInvocationID.x;
 if (i>=uint(N)) return;
 int id=owner[i];
 if(id<0 || id>=256 || selected[id]==0u) return;
 precise dvec3 p=dvec3(xyz[i*3],xyz[i*3+1],xyz[i*3+2]);
 if (any(lessThan(p,uMin-dvec3(1.e-9))) || any(greaterThan(p,uMax+dvec3(1.e-9))))return;
 precise double u=dot(p,uRight);
 precise double v=dot(p,uUp);
 int col=int(floor((u-uOrigin.x)/uMpp+1.e-8));
 int bottom=int(floor((v-uOrigin.y)/uMpp+1.e-8));
 int row=H-1-bottom;
 if (col<0||col>=W||row<0||row>=H)return;
 uint pixel=uint(row*W+col);
 precise double z=dot(p,uForward);
 uint64_t key=depthKey(z);
 uint tie=(validity[i]==0u?0x1000000u:0u)+rgb[i];
 if(passIndex==0){
    atomicMin(minZ[pixel],key);
 } else if(passIndex==1) {
    if(key==minZ[pixel])atomicMin(minTie[pixel],tie);
 } else {
    if(key==minZ[pixel] && tie==minTie[pixel])
       atomicMin(firstIndex[pixel],i);
 }
}
"""

def _shader(src):
    shader=gl.glCreateShader(gl.GL_COMPUTE_SHADER)
    gl.glShaderSource(shader,src)
    gl.glCompileShader(shader)
    if not gl.glGetShaderiv(shader,gl.GL_COMPILE_STATUS):
        raise RuntimeError("F13 GPU lexsort shader compile error "+str(gl.glGetShaderInfoLog(shader)))
    program=gl.glCreateProgram()
    gl.glAttachShader(program,shader)
    gl.glLinkProgram(program)
    gl.glDeleteShader(shader)
    if not gl.glGetProgramiv(program,gl.GL_LINK_STATUS):
        raise RuntimeError("F13 GPU lexsort shader link error "+str(gl.glGetProgramInfoLog(program)))
    return program

def _gpu_buffer(data,usage=gl.GL_DYNAMIC_DRAW):
    a=np.ascontiguousarray(data)
    name=gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,name)
    gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER,a.nbytes,a,usage)
    return name

class ColorProjector:
    def __init__(self):
        self.ctx=egl.GLContext(2048,2048)
        self.ctx.make_current()
        self.program=_shader(SOURCE)
        self.points_source=None
        self.n=0
        self.buffers=[]
        self.upload_s=0
    def bind_source(self,xyz,rgb,valid,owner):
        # Native room-frame 3D samples are FP64; do not round to FP32.
        self.ctx.make_current()
        t=time.perf_counter()
        xyz=np.asarray(xyz,dtype=np.float64)
        rgb=np.asarray(rgb,dtype=np.uint8)
        valid=np.asarray(valid,dtype=np.uint8)
        owner=np.asarray(owner,dtype=np.int32)
        assert xyz.ndim==2 and xyz.shape[1]==3
        n=len(xyz)
        assert rgb.shape==(n,3) and owner.shape==(n,) and valid.shape==(n,)
        # One persistent upload per episode/Room. Rebuilding per direction would
        # destroy the throughput benefit.
        packed=((rgb[:,0].astype(np.uint32)<<16) |
                (rgb[:,1].astype(np.uint32)<<8) |
                rgb[:,2].astype(np.uint32))
        inputs=(xyz.reshape(-1),packed,owner,valid.astype(np.uint32))
        if self.buffers:
            gl.glDeleteBuffers(len(self.buffers),self.buffers)
        self.buffers=[_gpu_buffer(a,gl.GL_STATIC_DRAW) for a in inputs]
        self.n=n
        # Retain the array so a later Room cannot accidentally reuse its id.
        self.points_source=xyz
        self.upload_s=time.perf_counter()-t
    def select(self,xyz,rgb,valid,owner,chosen,lo,hi,right,up,forward,origin,mpp,w,h):
        self.ctx.make_current()
        t0=time.perf_counter()
        xyz=np.asarray(xyz,dtype=np.float64)
        if self.points_source is not xyz or self.n!=len(xyz):
            self.bind_source(xyz,rgb,valid,owner)
        assert self.n and w*h<4_000_000
        mask=np.zeros(256,dtype=np.uint32)
        for i in chosen:
            if i<0 or i>=256:raise ValueError("F13 original G2 owner id not supported by shader")
            mask[i]=1
        pixels=w*h
        minz=np.full(pixels,0xffffffffffffffff,dtype=np.uint64)
        mincolor=np.full(pixels,0xffffffff,dtype=np.uint32)
        minindex=np.full(pixels,0xffffffff,dtype=np.uint32)
        dynamic=[_gpu_buffer(a) for a in (minz,mincolor,minindex,mask)]
        try:
            for binding,b in enumerate(self.buffers+dynamic):
                gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,binding,b)
            gl.glUseProgram(self.program)
            def set_int(key,value):
                gl.glUniform1i(gl.glGetUniformLocation(self.program,key),value)
            def set_dvec3(key,arr):
                gl.glUniform3dv(gl.glGetUniformLocation(self.program,key),1,np.asarray(arr,np.float64))
            def set_dvec2(key,arr):
                gl.glUniform2dv(gl.glGetUniformLocation(self.program,key),1,np.asarray(arr,np.float64))
            set_int("N",self.n)
            set_int("W",w)
            set_int("H",h)
            for key,a in [('uRight',right),('uUp',up),('uForward',forward),
                          ('uMin',lo),('uMax',hi)]:
                set_dvec3(key,a)
            set_dvec2("uOrigin",origin)
            gl.glUniform1d(gl.glGetUniformLocation(self.program,"uMpp"),float(mpp))
            start_kernel=time.perf_counter()
            for stage in (0,1,2):
                set_int("passIndex",stage)
                gl.glDispatchCompute((self.n+255)//256,1,1)
                gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT)
            gl.glFinish()
            kernel_s=time.perf_counter()-start_kernel
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,dynamic[2])
            out=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,minindex.nbytes)
            indices=np.frombuffer(out,dtype="<u4").copy()
            assert len(indices)==pixels
            # GPU returns a single source index for each pixel, arranged in
            # row-major order. CPU's lexsort would yield the same index set.
            mask=indices!=0xffffffff
            row,col=np.divmod(np.flatnonzero(mask),w)
            chosen_index=indices[mask].astype(np.int64)
            assert np.all(chosen_index<self.n)
            # Projection depth recomputed in FP64 for bitwise parity with
            # CPU subsequent acceptance/copy, not a model prediction.
            z=np.asarray(xyz[chosen_index],float)@np.asarray(forward,float)
            out_s=time.perf_counter()-t0
            return chosen_index,row,col,z,{
                "gpu_color_selection_wall_s":round(out_s,6),
                "gpu_color_kernel_s":round(kernel_s,6),
                "gpu_point_count":self.n,
                "gpu_selected_pixels":int(mask.sum()),
                "gpu_source_first_upload_s":round(self.upload_s,6)
            }
        finally:
            for i in range(8):gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,i,0)
            gl.glDeleteBuffers(len(dynamic),dynamic)
    def close(self):
        self.ctx.make_current()
        if hasattr(self,"_nearest_grid"):self._nearest_grid.close()
        if self.buffers:
            gl.glDeleteBuffers(len(self.buffers),self.buffers)
        gl.glDeleteProgram(self.program)
        self.ctx.free()

_CURRENT=None
def get_projector():
    global _CURRENT
    if _CURRENT is None:_CURRENT=ColorProjector()
    return _CURRENT
def close_projector():
    global _CURRENT
    if _CURRENT:
        _CURRENT.close()
        _CURRENT=None
