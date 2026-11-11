"""Chunked source-bound MuJoCo visual albedo at metric surface spacing.

GT input only. The *existing* nav_sg ColorCloudMap is the destination; this
module creates regular, source-authenticated PrecoloredCloudFrame pieces, NOT
an independent scene graph or runtime map. No camera image is ever read.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import time

import numpy as np

from g2.io import ContractError, digest, read_json, write_json
from .prescan import geom_surface_mesh, geometry_type_names, analytic_surface
from .source_geometry import load_model, apply_state, model_source_hash, surface_colors, effective_rgba

SCHEMA = "g2_mujoco_dense_visual_chunks_v1"


def count_face_samples(vertices, faces, spacing, *, select_faces=None):
    triangles = np.asarray(vertices, dtype=np.float64)[faces]
    edges = np.maximum.reduce([
        np.linalg.norm(triangles[:,i] - triangles[:,j], axis=1)
        for i,j in ((0,1),(1,2),(2,0))
    ])
    area = np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],
                                   triangles[:,2]-triangles[:,0]), axis=1)
    keep = area > 0.
    if select_faces is not None:
        select_faces=np.asarray(select_faces,dtype=np.bool_)
        if select_faces.shape!=(len(faces),):
            raise ContractError("source shell face selection shape mismatch")
        keep &= select_faces
    steps = np.maximum(1, np.ceil(edges[keep]/spacing)).astype(np.int64)
    if len(steps) and steps.max()>20000:
        raise ContractError("surface subdivision exceeds source budget")
    n = int(np.sum((steps+1)*(steps+2)//2,dtype=np.int64))
    return n, keep


def triangle_batches(vertices,faces,keep,spacing,max_batch):
    """Real 10mm/5mm triangle samples, streaming at bounded working memory."""
    triangles = np.asarray(vertices, dtype=np.float64)[faces]
    for face_id,tri in enumerate(triangles):
        if not keep[face_id]:
            continue
        longest = max(float(np.linalg.norm(tri[i]-tri[j]))
                      for i,j in ((0,1),(1,2),(2,0)))
        steps=max(1,int(math.ceil(longest/spacing)))
        counts=(steps+1-np.arange(steps+1,dtype=np.int64))
        count=int(counts.sum())
        # The original geometric triangle and the original face ID are kept.
        i=np.repeat(np.arange(steps+1,dtype=np.int64),counts)
        start=np.cumsum(counts)-counts
        j=np.arange(count,dtype=np.int64)-np.repeat(start,counts)
        weights=np.column_stack([i/steps,j/steps,1-(i+j)/steps])
        pts=weights@tri
        # Tessellation of one very long triangle may exceed the batch cap.
        for lo in range(0,count,max_batch):
            hi=min(count,lo+max_batch)
            yield pts[lo:hi],np.full(hi-lo,face_id,np.int64),weights[lo:hi]


def coalesced_batches(samples,max_rows):
    blocks=[]
    count=0
    for sample in samples:
        blocks.append(sample)
        count+=len(sample[0])
        if count>=max_rows:
            yield tuple(np.concatenate([block[k] for block in blocks]) for k in range(3))
            blocks=[];count=0
    if blocks:
        yield tuple(np.concatenate([block[k] for block in blocks]) for k in range(3))


def select_room_interior_shell_faces(vertices,faces,kind,instance,geom_position,
                                     geom_rotation,room_center):
    """Keep exactly the room-facing skin of floor/wall/ceiling Visual geometry.

    This only affects the dense colored cloud. The complete original MuJoCo
    geometry and native occupancy/Room/Wall/SG source remain untouched. The
    room center must come from the verified same-source native snapshot.
    Ambiguous structure fails closed rather than projecting an outside wall.
    """
    if not isinstance(instance,str) or not instance.startswith(("floor_","wall_","ceiling_")):
        return None,"ALL_OBJECT_SURFACES"
    if "backing" in instance:
        return np.zeros(len(faces),dtype=bool),"EXCLUDED_DUPLICATE_BACKING_SKIN"
    tri=np.asarray(vertices,dtype=np.float64)[faces]
    world=tri@geom_rotation.T+geom_position
    normals=np.cross(world[:,1]-world[:,0],world[:,2]-world[:,0])
    length=np.linalg.norm(normals,axis=1)
    healthy=length>0
    normals=np.divide(normals,length[:,None],out=np.zeros_like(normals),where=length[:,None]>0)
    tiny=1e-6
    face_z=world[:,:,2].mean(axis=1)
    if instance.startswith("floor_"):
        z_surface=world[:,:,2].max()
        select=(healthy &
                (np.ptp(world[:,:,2],axis=1)<tiny) &
                (np.abs(face_z-z_surface)<tiny) &
                (np.abs(normals[:,2])>.99))
        policy="INTERIOR_FLOOR_TOP_ONLY"
    elif instance.startswith("ceiling_"):
        z_surface=world[:,:,2].min()
        select=(healthy &
                (np.ptp(world[:,:,2],axis=1)<tiny) &
                (np.abs(face_z-z_surface)<tiny) &
                (np.abs(normals[:,2])>.99))
        policy="INTERIOR_CEILING_UNDERSIDE_ONLY"
    else:
        # MuJoCo geom orientation rotates local axes into world coordinates.
        # The slab's THIN dimension may be local Z even for a vertical wall
        # (as in the real RoboCasa wall_left_room_g0_vis model). Never assume
        # local x/y are the horizontal dimensions.
        widths=np.ptp(vertices,axis=0)
        axis=int(np.argmin(widths))
        thin=geom_rotation[:,axis]
        if (widths[axis]<=0 or np.sort(widths)[1]<3.*widths[axis] or
                abs(float(thin[2]))>=.15):
            raise ContractError("wall has no certified horizontal thin-axis normal: "+instance)
        center_local=(room_center-geom_position)@thin
        chosen=min([np.min(vertices[:,axis]),np.max(vertices[:,axis])],
                   key=lambda value:abs(value-center_local))
        plane=tri[:,:,axis]
        facing=np.abs(normals@thin)
        select=(healthy & (np.ptp(plane,axis=1)<tiny) &
                (np.abs(plane.mean(axis=1)-chosen)<tiny) &
                (facing>.99) & (np.abs(normals[:,2])<.15))
        policy="INTERIOR_WALL_ROOM_SIDE_ONLY"
    if not select.any():
        raise ContractError("no certified inward visual surface for "+instance)
    return select,policy



class ChunkWriter:
    """Native precolored transport, same 5-million-point bounded parser."""
    def __init__(self,output,scene,source,frame,limit):
        self.output=Path(output)
        self.scene=scene
        self.source=source
        self.frame=frame
        self.limit=limit
        self.parts=[]
        self._file=None
        self._count=0
        self.total=0
        self.valid=0

    def _open(self):
        path=self.output / f"precolored_{len(self.parts):04d}.txt"
        self._file=path.open("x+",encoding="utf-8",newline="\n")
        self._file.write("NAV_SG_PRECOLORED_CLOUD_V1\n")
        self._file.write("scene_id "+json.dumps(self.scene,ensure_ascii=True)+"\n")
        self._file.write("source_sha256 "+self.source+"\n")
        self._file.write(f"frame_id {self.frame}\nworld_frame \"world\"\n")
        self._file.write("points ")
        self._count_position=self._file.tell()
        self._file.write("0000000000\ndata\n")
        self._count=0

    def _finish(self):
        if self._file is None:
            return
        f=self._file
        f.seek(self._count_position)
        f.write(f"{self._count:010d}")
        f.flush()
        f.close()
        path=Path(f.name)
        self.parts.append({"path":str(path.resolve()),"bytes":path.stat().st_size,
                           "sha256":digest(path),"points":self._count})
        self._file=None

    def append(self,world,rgba,valid):
        n=len(world)
        i=0
        while i<n:
            if self._file is None:
                self._open()
            take=min(self.limit-self._count,n-i)
            p=world[i:i+take];c=rgba[i:i+take];m=valid[i:i+take]
            if p.shape!=(take,3) or c.shape!=(take,4) or m.shape!=(take,) or not np.isfinite(p).all():
                raise ContractError("invalid dense sample arrays")
            # Fast buffered text transport; no synthetic camera or palette.
            lines=("%.9g %.9g %.9g %d %d %d %d\n"%(float(v[0]),float(v[1]),float(v[2]),
                 int(rgb[0]),int(rgb[1]),int(rgb[2]),int(ok))
                 for v,rgb,ok in zip(p,c,m))
            self._file.writelines(lines)
            self._count+=take
            self.total+=take
            self.valid+=int(np.count_nonzero(m))
            i+=take
            if self._count==self.limit:
                self._finish()

    def close(self):
        self._finish()


def export(gt_manifest, role_map, output, *, spacing=.01, fine_spacing=.005,
           fine_max_size=.15, fine_small=True, chunk_points=1_000_000,
           max_total_points=100_000_000, max_batch=200_000, max_geoms=None,
           interior_shell_only=False,room_snapshot=None):
    import mujoco
    gt_manifest=Path(gt_manifest).resolve(strict=True)
    roles=Path(role_map).resolve(strict=True)
    out=Path(output).resolve()
    if out.exists() or gt_manifest.parent in out.parents or roles.parent in out.parents:
        raise ContractError("fresh isolated output required")
    if not (.002<=spacing<=.1 and .002<=fine_spacing<=spacing and
            .01<=fine_max_size<=.5 and 10000<=chunk_points<=5_000_000 and
            10000<=max_batch<=500_000 and max_total_points<=100_000_000):
        raise ContractError("invalid dense visual budget or spacing")
    gt=read_json(gt_manifest)
    metadata=read_json(roles)
    if gt.get("schema")!="nav_sg_mujoco_oracle_v1" or metadata.get("schema")!="g2_sim_prescan_v1":
        raise ContractError("expected reviewed native GT and visual role-map schemas")
    scene=gt["scene_id"]
    if metadata.get("scene_id")!=scene:
        raise ContractError("source role map and native scene differ")
    source=next(row["path"] for row in gt["sources"] if row["logical_id"]=="root.xml")
    roots=[Path(row["path"]).parent for row in gt["sources"]]
    model,sources=load_model(source,roots)
    if model_source_hash(sources)!=gt["source_identity"]["model_source_sha256"]:
        raise ContractError("native GT and visual assets differ")
    states=gt.get("state",{})
    if states.get("format")=="mjcf_default":
        data,state=apply_state(model)
    else:
        data,state=apply_state(model,states["path"],states["frame_id"],states["format"])
    if any(state.get(key)!=states.get(key) for key in ("frame_id","row_sha256","timestamp")):
        raise ContractError("restored MuJoCo scene state differs from GT")
    source_sha=gt["source_sha256"]
    if interior_shell_only:
        if room_snapshot is None:
            raise ContractError("interior shell requires explicit source-bound native Room snapshot")
        room_snapshot=Path(room_snapshot).resolve(strict=True)
        room_info=read_json(room_snapshot)
        if (room_info.get("schema")!="nav_sg_spatial_snapshot_v1" or
                room_info.get("scene_id")!=scene or
                room_info.get("source_sha256")!=source_sha or
                room_info.get("frame_id")!=states.get("frame_id") or
                room_info.get("source_mode")!="full_map_mujoco_source" or
                len(room_info.get("rooms",[]))!=1):
            raise ContractError("source-bound single-Room evidence is missing or inconsistent")
        room_center=np.asarray(room_info["rooms"][0]["reference_frame"]["origin_world"],float)
        if room_center.shape!=(3,) or not np.isfinite(room_center).all():
            raise ContractError("invalid original native room center")
    else:
        if room_snapshot is not None:
            raise ContractError("room snapshot must be opt-in alongside interior_shell_only")
        room_center=None
    kinds=geometry_type_names()
    all_geoms=[]
    by_instance={}
    for g in range(model.ngeom):
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,g) or f"geom_{g}"
        spec=metadata["geoms"].get(name)
        if not isinstance(spec,dict) or spec.get("role") not in ("visual","collision","robot","auxiliary"):
            raise ContractError("visual source role missing: "+name)
        if spec["role"]!="visual" or effective_rgba(model,g)[3]<=0:
            continue
        kind=kinds.get(int(model.geom_type[g]))
        if kind not in ("box","sphere","ellipsoid","capsule","cylinder","mesh"):
            raise ContractError("unsupported selected visual geometry: "+name)
        vertices,faces=geom_surface_mesh(model,g,kind)
        if len(vertices)==0 or len(faces)==0:
            raise ContractError("empty selected source geometry: "+name)
        world=vertices @ data.geom_xmat[g].reshape(3,3).T+data.geom_xpos[g]
        key=(spec.get("source_kind"),spec.get("source_instance_name"))
        bb=by_instance.setdefault(key,[np.full(3,np.inf),np.full(3,-np.inf)])
        bb[0][:]=np.minimum(bb[0],world.min(axis=0))
        bb[1][:]=np.maximum(bb[1],world.max(axis=0))
        all_geoms.append((g,name,kind,vertices,faces,key))
    fine_instances={key for key,bb in by_instance.items()
                    if fine_small and key[0]=="ep_meta" and
                    np.max(bb[1]-bb[0])<=fine_max_size}
    source_records=[]
    budget=0
    shell_rejected_points=0
    for g,name,kind,vertices,faces,key in all_geoms:
        s=fine_spacing if key in fine_instances else spacing
        original_points,_=count_face_samples(vertices,faces,s)
        if interior_shell_only:
            selected,policy=select_room_interior_shell_faces(
                vertices,faces,kind,key[1],data.geom_xpos[g],
                data.geom_xmat[g].reshape(3,3),room_center)
        else:
            selected,policy=None,"ALL_VISUAL_SURFACES"
        pts,keep=count_face_samples(vertices,faces,s,select_faces=selected)
        shell_rejected_points+=original_points-pts
        budget+=pts
        source_records.append((g,name,kind,vertices,faces,s,pts,keep,key,policy,original_points))
    if budget > max_total_points:
        raise ContractError(f"high density source exceeds hard point budget {budget}>{max_total_points}")
    if max_geoms is not None:
        source_records=source_records[:max_geoms]
    out.mkdir(parents=True,exist_ok=False)
    writer=ChunkWriter(out,scene,source_sha,int(states["frame_id"]),chunk_points)
    rows=[]
    started=time.monotonic()
    for i,(g,name,kind,vertices,faces,s,expected,keep,key,policy,original_points) in enumerate(source_records):
        good=0;total=0
        for local,faceids,bary in coalesced_batches(triangle_batches(vertices,faces,keep,s,max_batch),max_batch):
            if kind!="mesh":
                local=analytic_surface(local,kind,model.geom_size[g],faceids)
            color,valid,appearance,_=surface_colors(model,g,kind,faceids,bary,
                                                   local_points=local,with_diagnostics=True)
            rgba=np.rint(np.clip(color,0,1)*255).astype(np.uint8)
            valid=np.asarray(valid,dtype=bool)&(rgba[:,3]==255)
            world=local @ data.geom_xmat[g].reshape(3,3).T+data.geom_xpos[g]
            writer.append(world,rgba,valid)
            total+=len(local);good+=int(np.count_nonzero(valid))
        if total!=expected:raise ContractError("sample estimator differs from actual source: "+name)
        rows.append({"geom_id":g,"geom_name":name,"spacing_m":s,"points":total,
                     "valid_color_points":good,"source_instance":list(key),
                     "source_faces_policy":policy,
                     "total_source_triangles":len(faces),
                     "sampled_source_triangles":int(keep.sum()),
                     "all_surface_points_without_inward_filter":original_points})
        print("DENSE_GEOM",i+1,len(source_records),name,"sampled",total,"valid",good,
              "chunks_completed",len(writer.parts),"elapsed_s",round(time.monotonic()-started,1),flush=True)
    writer.close()
    result={"schema":SCHEMA,"source_mode":"mujoco_full_scene","scene_id":scene,
            "source_sha256":source_sha,"frame_id":int(states["frame_id"]),
            "world_frame":"world","model_source_sha256":model_source_hash(sources),
            "native_gt_manifest":{"path":str(gt_manifest),"sha256":digest(gt_manifest)},
            "visual_role_map":{"path":str(roles),"sha256":digest(roles)},
            "spacing_m":spacing,"small_spacing_m":fine_spacing,
            "fine_small_instances":[list(x) for x in fine_instances],
            "small_object_extent_threshold_m":fine_max_size,"max_total_points":max_total_points,
            "predicted_full_scene_points":budget,"exported_points":writer.total,
            "color_valid_points":writer.valid,"partial_geom_limit":max_geoms,
            "sampled_geoms":rows,"chunks":writer.parts,"status":"PREVIEW_NOT_HUMAN_ACCEPTED",
            "interior_shell_only":bool(interior_shell_only),
            "room_snapshot":({"path":str(room_snapshot),"sha256":digest(room_snapshot)}
                              if interior_shell_only else None),
            "one_sided_structure_rejected_points":shell_rejected_points,
            "training_ready":False,"oracle_source_not_real_perception":True}
    write_json(out/"dense_manifest.json",result)
    print("DENSE_DONE",scene,writer.total,len(writer.parts),
          "valid_color",writer.valid,"elapsed_s",round(time.monotonic()-started,1),flush=True)
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--gt-manifest",required=True)
    p.add_argument("--role-map",required=True)
    p.add_argument("--output",required=True)
    p.add_argument("--spacing",type=float,default=.01)
    p.add_argument("--fine-spacing",type=float,default=.005)
    p.add_argument("--small-extent",type=float,default=.15)
    p.add_argument("--no-small-refinement",action="store_true")
    p.add_argument("--chunk-points",type=int,default=1_000_000)
    p.add_argument("--max-total-points",type=int,default=100_000_000)
    p.add_argument("--max-geoms",type=int)
    p.add_argument("--interior-shell-only",action="store_true")
    p.add_argument("--room-snapshot")
    a=p.parse_args()
    result=export(a.gt_manifest,a.role_map,a.output,spacing=a.spacing,
        fine_spacing=a.fine_spacing,fine_max_size=a.small_extent,
        fine_small=not a.no_small_refinement,chunk_points=a.chunk_points,
        max_total_points=a.max_total_points,max_geoms=a.max_geoms,
        interior_shell_only=a.interior_shell_only,room_snapshot=a.room_snapshot)
    print(json.dumps({"status":result["status"],"points":result["exported_points"],
        "chunks":len(result["chunks"])},sort_keys=True))


if __name__=="__main__":
    main()
