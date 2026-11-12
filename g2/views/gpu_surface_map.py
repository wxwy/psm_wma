"""GPU ortho-projection for persistent 10 mm opaque surface-map points.

Uses the existing EGL surface renderer context, no extra persistent map.
Two shader passes: monotonic float depth min, then deterministic winning cell
index. Geometry coordinates and projection are FP64, depth arbitration float32
(with honest tie uncertainty). This never reads Scene Graph membership.
"""
import time
import numpy as np
from OpenGL import GL as gl

from g2.io import ContractError
from g2.views.exact_compute import get_engine
from g2.views.surface_renderer import projection_grid


SHADER = """#version 460 core
#extension GL_ARB_gpu_shader_fp64 : require
layout(local_size_x=256) in;
layout(std430,binding=0) readonly buffer Points { dvec4 xyz[]; };
layout(std430,binding=1) buffer DepthKey { uint depth_keys[]; };
layout(std430,binding=2) buffer IndexKey { uint winning_indices[]; };
layout(std430,binding=3) buffer TieCount { uint tie_count[]; };
uniform int stage;
uniform uint N;
uniform int width, height;
uniform dvec3 right, up, forward;
uniform dvec2 uv_origin;
uniform double mpp, near_z, far_z;
uint ordered(float value) {
    uint bits=floatBitsToUint(value);
    return (bits & 0x80000000u)!=0u ? ~bits : bits^0x80000000u;
}
void main(){
    uint i=gl_GlobalInvocationID.x;
    if(i>=N)return;
    dvec3 p=xyz[i].xyz;
    dvec2 pixel=dvec2(dot(p,right),dot(p,up));
    dvec2 loc=floor((pixel-uv_origin)/mpp);
    int x=int(loc.x), y=int(loc.y);
    if(x<0||x>=width||y<0||y>=height)return;
    double z=dot(p,forward);
    if(z<near_z||z>far_z)return;
    uint pos=uint(height-1-y)*uint(width)+uint(x);
    uint key=ordered(float(z));
    if(stage==0) atomicMin(depth_keys[pos],key);
    else if(key==depth_keys[pos]){
        atomicMin(winning_indices[pos],i);
        atomicAdd(tie_count[pos],1u);
    }
}"""


def _ssbo(arr):
    src=np.ascontiguousarray(arr)
    obj=gl.glGenBuffers(1)
    gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,obj)
    gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER,src.nbytes,src,gl.GL_DYNAMIC_DRAW)
    return obj


class MapProjector:
    def __init__(self):
        self.context=get_engine().ctx
        self.context.make_current()
        shader=gl.glCreateShader(gl.GL_COMPUTE_SHADER)
        gl.glShaderSource(shader,SHADER)
        gl.glCompileShader(shader)
        if not gl.glGetShaderiv(shader,gl.GL_COMPILE_STATUS):
            raise RuntimeError("map projection GLSL compile: "+str(gl.glGetShaderInfoLog(shader)))
        self.program=gl.glCreateProgram()
        gl.glAttachShader(self.program,shader)
        gl.glLinkProgram(self.program)
        gl.glDeleteShader(shader)
        if not gl.glGetProgramiv(self.program,gl.GL_LINK_STATUS):
            raise RuntimeError("map projection GLSL link: "+str(gl.glGetProgramInfoLog(self.program)))

    def draw(self,points,low,high,axis,mpp=.01):
        self.context.make_current()
        points=np.asarray(points,dtype=np.float64)
        if points.ndim!=2 or points.shape[1]!=3 or not np.isfinite(points).all():
            raise ContractError("invalid GPU map source point array")
        n=len(points)
        if n>10000000: raise ContractError("native surface map exceeds 10M budget")
        right,up,forward,origin,w,h,near,far=projection_grid(low,high,axis,mpp)
        if not n:
            return np.full((h,w),-1,np.int64),np.zeros((h,w),np.int32),{"empty":True}
        payload=np.empty((n,4),dtype=np.float64)
        payload[:,:3]=points;payload[:,3]=0.
        size=w*h
        keys=np.full(size,0xffffffff,dtype=np.uint32)
        winners=np.full(size,0xffffffff,dtype=np.uint32)
        counts=np.zeros(size,dtype=np.uint32)
        handles=[]
        start=time.perf_counter()
        try:
            for k,array in enumerate((payload,keys,winners,counts)):
                handle=_ssbo(array);handles.append(handle)
                gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,k,handle)
            gl.glUseProgram(self.program)
            def scalar(name,value):
                gl.glUniform1i(gl.glGetUniformLocation(self.program,name),value)
            scalar("width",w);scalar("height",h)
            gl.glUniform1ui(gl.glGetUniformLocation(self.program,"N"),n)
            gl.glUniform3d(gl.glGetUniformLocation(self.program,"right"),*right)
            gl.glUniform3d(gl.glGetUniformLocation(self.program,"up"),*up)
            gl.glUniform3d(gl.glGetUniformLocation(self.program,"forward"),*forward)
            gl.glUniform2d(gl.glGetUniformLocation(self.program,"uv_origin"),*origin)
            gl.glUniform1d(gl.glGetUniformLocation(self.program,"mpp"),mpp)
            gl.glUniform1d(gl.glGetUniformLocation(self.program,"near_z"),near)
            gl.glUniform1d(gl.glGetUniformLocation(self.program,"far_z"),far)
            passes=[]
            for stage in (0,1):
                scalar("stage",stage)
                start_pass=time.perf_counter()
                gl.glDispatchCompute((n+255)//256,1,1)
                gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT|gl.GL_BUFFER_UPDATE_BARRIER_BIT)
                gl.glFinish()
                passes.append(time.perf_counter()-start_pass)
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,handles[2])
            winners=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,size*4)
            gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER,handles[3])
            ties=gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER,0,size*4)
            winners=np.frombuffer(winners,dtype="<u4").astype(np.int64).reshape(h,w)
            count=np.frombuffer(ties,dtype="<u4").astype(np.int32).reshape(h,w)
            winners[winners==0xffffffff]=-1
            if np.any((winners>=n)|(winners<-1)):
                raise ContractError("GPU map projector returned invalid cell index")
            if np.any((count==0)!=(winners<0)):
                raise ContractError("GPU map projector depth/index disagreement")
            return winners,count,dict(backend="G2_GPU_ATOMIC_MIN_10MM_SURFELS",
                input_points=n,pixels=size,geometry_pixels=int((winners>=0).sum()),
                quantized_depth_tie_pixels=int((count>1).sum()),
                compute_pass_s=[round(s,6) for s in passes],
                wall_s=round(time.perf_counter()-start,6))
        finally:
            for k in range(4): gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER,k,0)
            if handles:gl.glDeleteBuffers(len(handles),handles)

    def close(self):
        self.context.make_current()
        gl.glDeleteProgram(self.program)


_PROJECTOR=None


def get_projector():
    global _PROJECTOR
    if _PROJECTOR is None: _PROJECTOR=MapProjector()
    return _PROJECTOR


def close_projector():
    global _PROJECTOR
    if _PROJECTOR is not None:
        _PROJECTOR.close()
        _PROJECTOR=None
