from pathlib import Path
import json
import numpy as np
import mujoco
ns={}
exec(Path('/tmp/g2_ray_audit_20261104/probe.py').read_text().split('\nout={}',1)[0],ns)
Sim,cases=ns['Sim'],ns['cases']
out={}
for key in ['mesh_outward','mesh_inward']:
 sim=Sim(cases[key])
 try:
  m,d=sim.model,sim.data;gid=1;mid=int(m.geom_dataid[gid]);fa=int(m.mesh_faceadr[mid]);fn=int(m.mesh_facenum[mid]);va=int(m.mesh_vertadr[mid]);vn=int(m.mesh_vertnum[mid]);faces=np.asarray(m.mesh_face[fa:fa+fn]);verts=np.asarray(m.mesh_vert[va:va+vn],np.float64)
  origin=d.cam_xpos[0];direction=d.cam_xmat[0].reshape(3,3)@np.array([0.,0.,-1.]);R=d.geom_xmat[gid].reshape(3,3);lo=R.T@(origin-d.geom_xpos[gid]);ld=R.T@direction
  tri=verts[faces];e1=tri[:,1]-tri[:,0];e2=tri[:,2]-tri[:,0];p=np.cross(ld,e2);det=np.einsum('ij,ij->i',e1,p);delta=lo-tri[:,0];q=np.cross(delta,e1)
  with np.errstate(divide='ignore',invalid='ignore'):
   u=np.einsum('ij,ij->i',delta,p)/det;v=(q@ld)/det;t=np.einsum('ij,ij->i',e2,q)/det
  eligible=(det>1e-12)&(u>=-1e-10)&(v>=-1e-10)&(u+v<=1+1e-10)&(t>=0)
  result=float(np.min(t[eligible])) if eligible.any() else None
  allface=float(mujoco.mj_rayMesh(m,d,gid,origin,direction))
  out[key]={'all_faces_distance':allface,'front_faces_mt_distance':result,'expected_front_face_distance':1.15 if key=='mesh_outward' else 1.45,'det_sign':'positive_for_front_faces','eligible_triangle_count':int(eligible.sum())}
 finally:sim.close()
Path('/tmp/g2_ray_audit_20261104/mt_probe.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
