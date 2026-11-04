import os,json,sys
from types import SimpleNamespace
import numpy as np
import mujoco

H=W=96
class Sim:
    def __init__(self,xml):
        self.model=mujoco.MjModel.from_xml_string(xml)
        self.data=mujoco.MjData(self.model)
        mujoco.mj_forward(self.model,self.data)
        self.gl=mujoco.GLContext(W,H);self.gl.make_current()
        self.scene=mujoco.MjvScene(self.model,maxgeom=1000)
        self.camera=mujoco.MjvCamera();self.camera.type=mujoco.mjtCamera.mjCAMERA_FIXED;self.camera.fixedcamid=0
        self.vopt=mujoco.MjvOption();self.vopt.geomgroup[:]=[1,1,1,0,0,0]
        self._render_context_offscreen=SimpleNamespace(vopt=self.vopt)
        self.context=mujoco.MjrContext(self.model,mujoco.mjtFontScale.mjFONTSCALE_100)
        mujoco.mjr_setBuffer(mujoco.mjtFramebuffer.mjFB_OFFSCREEN,self.context)
        self.rect=mujoco.MjrRect(0,0,W,H)
    def render(self,*,segmentation=False,depth=False,**kwargs):
        mujoco.mjv_updateScene(self.model,self.data,self.vopt,None,self.camera,mujoco.mjtCatBit.mjCAT_ALL,self.scene)
        if segmentation:
            self.scene.flags[mujoco.mjtRndFlag.mjRND_SEGMENT]=1;self.scene.flags[mujoco.mjtRndFlag.mjRND_IDCOLOR]=1
        mujoco.mjr_render(self.rect,self.scene,self.context)
        if segmentation:
            self.scene.flags[mujoco.mjtRndFlag.mjRND_SEGMENT]=0;self.scene.flags[mujoco.mjtRndFlag.mjRND_IDCOLOR]=0
        rgb=np.empty((H,W,3),dtype=np.uint8);buffer=np.empty((H,W),np.float32) if depth else None
        mujoco.mjr_readPixels(rgb,buffer,self.rect,self.context)
        if segmentation:
            packed=rgb.astype(np.int32);ids=packed[:,:,0]+packed[:,:,1]*256+packed[:,:,2]*65536
            ids[ids>=self.scene.ngeom+1]=0
            lookup=np.full((self.scene.ngeom+1,2),-1,np.int32)
            for geom in list(self.scene.geoms)[:self.scene.ngeom]:
                if geom.segid!=-1:lookup[geom.segid+1]=[geom.objtype,geom.objid]
            rgb=lookup[ids]
        return (rgb,buffer) if depth else rgb
    def close(self):self.context.free();self.gl.free()

