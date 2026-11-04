import os,json,sys
from types import SimpleNamespace
import numpy as np
import mujoco
sys.path.insert(0,'/workspace/psm-wma-g2-rgbd-stage1')
from tools.g2.rgbd_pose.replay import Replay

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

head='<mujoco><visual><global offwidth="96" offheight="96"/><quality offsamples="4"/><map znear="0.01" zfar="30"/></visual><worldbody><light pos="0 0 3"/><camera name="cam" pos="0 0 2" fovy="60"/>'
back='<geom name="background" type="box" pos="0 0 -0.1" size="3 3 .1" rgba=".2 .2 .7 1"/>'
tail='</worldbody></mujoco>'
cases={
 'plane':head+back+tail,
 'opaque':head+back+'<geom name="foreground" type="box" pos="0 0 .7" size=".4 .4 .15" rgba=".7 .1 .1 1"/>'+tail,
 'transparent':head+back+'<geom name="foreground" type="box" pos="0 0 .7" size=".4 .4 .15" rgba=".7 .1 .1 .3"/>'+tail,
}
verts=[[-.4,-.4,-.15],[.4,-.4,-.15],[.4,.4,-.15],[-.4,.4,-.15],[-.4,-.4,.15],[.4,-.4,.15],[.4,.4,.15],[-.4,.4,.15]]
faces=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
for orient in ['outward','inward']:
    f=faces if orient=='outward' else [r[::-1] for r in faces]
    asset='<asset><mesh name="layer" vertex="'+' '.join(str(x) for v in verts for x in v)+'" face="'+' '.join(str(x) for v in f for x in v)+'"/></asset>'
    cases['mesh_'+orient]=head.replace('<worldbody>',asset+'<worldbody>')+back+'<geom name="foreground" type="mesh" mesh="layer" pos="0 0 .7" rgba=".7 .1 .1 1"/>'+tail
out={}
for name,xml in cases.items():
    sim=None
    try:
        sim=Sim(xml)
        rgb0=sim.render()[::-1].copy();rgbd,buf=sim.render(depth=True);rgbd=rgbd[::-1].copy();buf=buf[::-1].copy()
        near=float(sim.model.vis.map.znear*sim.model.stat.extent);far=float(sim.model.vis.map.zfar*sim.model.stat.extent)
        z=near/(1-buf.astype(np.float64)*(1-near/far))
        K=np.array([[.5*H/np.tan(np.pi/6),0,W/2],[0,.5*H/np.tan(np.pi/6),H/2],[0,0,1.]])
        T=np.eye(4);T[:3,:3]=sim.data.cam_xmat[0].reshape(3,3)@np.diag([1,-1,-1]);T[:3,3]=sim.data.cam_xpos[0]
        sample={'depth_m':z,'valid':buf<1,'K':K,'T_world_camera_cv':T}
        replay=object.__new__(Replay);replay.env=SimpleNamespace(sim=sim)
        result=replay.ray_check('cam',sample)
        seg=sim.render(segmentation=True)[::-1].copy();rgb1=sim.render()[::-1].copy()
        result.update(rgb_depth_mode_mae=float(np.mean(np.abs(rgb0.astype(float)-rgbd))),rgb_segmentation_cycle_mae=float(np.mean(np.abs(rgb0.astype(float)-rgb1))),near=near,far=far,center_depth=float(z[H//2,W//2]),center_segmentation=seg[H//2,W//2].tolist(),context_cull_face=int(sim.scene.flags[mujoco.mjtRndFlag.mjRND_CULL_FACE]),offscreen_samples=int(sim.context.offSamples),render_scene=[{'objid':int(g.objid),'type':int(g.objtype),'alpha':float(g.rgba[3]),'transparent':bool(g.transparent)} for g in list(sim.scene.geoms)[:sim.scene.ngeom]])
        out[name]=result
    except Exception as ex:out[name]={'error':type(ex).__name__+':'+str(ex)}
    finally:
        if sim:sim.close()
report={'native_cpu_osmesa':True,'mujoco_version':mujoco.__version__,'real_data':False,'cases':out}
with open('/tmp/g2_ray_audit_20261104/probe.json','w') as f:json.dump(report,f,indent=2)
print(json.dumps(report,indent=2))
