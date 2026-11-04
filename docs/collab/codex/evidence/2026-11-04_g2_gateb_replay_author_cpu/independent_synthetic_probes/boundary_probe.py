import sys,json
import numpy as np
import mujoco
from probe import Sim,H,W,head,back,tail,verts,faces

# Two disconnected boxes in one visual mesh: a near occluder and a far backing plate.
v0=np.array(verts)*[.9,.9,1]+[.13,0,.7]
v1=np.array(verts)*[5,5,1]+[0,0,-.15]
v=np.concatenate([v0,v1]);f=np.concatenate([np.array(faces),np.array(faces)+8])
asset='<asset><mesh name="compound" vertex="'+' '.join(str(x) for r in v for x in r)+'" face="'+' '.join(str(x) for r in f for x in r)+'"/></asset>'
base=head.replace('<worldbody>',asset+'<worldbody>')+'<geom type="mesh" mesh="compound" rgba=".7 .2 .2 1" euler="0 0 13"/>'+tail
out={}
for samples in [0,4]:
    xml=base.replace('offsamples="4"',f'offsamples="{samples}"')
    sim=Sim(xml)
    try:
        _,buf=sim.render(depth=True);buf=buf[::-1].copy()
        near=float(sim.model.vis.map.znear*sim.model.stat.extent);far=float(sim.model.vis.map.zfar*sim.model.stat.extent)
        depth=near/(1-buf.astype(float)*(1-near/far));seg=sim.render(segmentation=True)[::-1].copy()
        K=np.array([[.5*H/np.tan(np.pi/6),0,W/2],[0,.5*H/np.tan(np.pi/6),H/2],[0,0,1.]])
        rot=sim.data.cam_xmat[0].reshape(3,3)@np.diag([1,-1,-1]);origin=sim.data.cam_xpos[0].copy()
        errors=np.full((H,W),np.nan)
        geomgroups=np.array([1,1,1,0,0,0],np.uint8)
        for row,col in zip(*np.nonzero(buf<1)):
            ray=np.linalg.solve(K,[col+.5,row+.5,1]);norm=np.linalg.norm(ray);direction=rot@ray/norm;hit=np.array([-1],np.int32)
            distance=mujoco.mj_ray(sim.model,sim.data,origin,direction,geomgroups,True,-1,hit)
            if distance>=0 and hit[0]==seg[row,col,1]:errors[row,col]=abs(distance/norm-depth[row,col])
        interior=np.zeros((H,W),bool);interior[1:-1,1:-1]=True
        smooth=np.ones_like(interior)
        for dy in [-1,0,1]:
            for dx in [-1,0,1]:
                smooth &= np.roll(np.roll(seg[:,:,1],dy,axis=0),dx,axis=1)==seg[:,:,1]
        smooth &= interior
        depth_spread=np.zeros_like(depth)
        for dy in [-1,0,1]:
            for dx in [-1,0,1]:depth_spread=np.maximum(depth_spread,np.abs(depth-np.roll(np.roll(depth,dy,axis=0),dx,axis=1)))
        smooth_depth=smooth & (depth_spread<=.01)
        out[str(samples)]={'valid_same_id':int(np.isfinite(errors).sum()),'max_abs_z_error_m':float(np.nanmax(errors)), 'over_1cm':int(np.nansum(errors>.01)), 'seg_interior_over_1cm':int(np.nansum((errors>.01)&smooth)), 'seg_depth_interior_over_1cm':int(np.nansum((errors>.01)&smooth_depth)), 'seg_depth_interior_samples':int(np.sum(np.isfinite(errors)&smooth_depth)), 'max_abs_z_error_interior_m':float(np.nanmax(np.where(smooth_depth,errors,np.nan)))}
    finally:sim.close()
with open('/tmp/g2_ray_audit_20261104/boundary_probe.json','w') as f:json.dump(out,f,indent=2)
print('BOUNDARY',json.dumps(out,indent=2))
