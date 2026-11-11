"""Metric orthographic views of native 3D content, with independent Island assets."""
import argparse
import hashlib
import math
import time
from pathlib import Path
import re
import numpy as np
from PIL import Image
from g2.io import ContractError, canonical, digest, new_output, write_json
from g2.nav_bridge.snapshot import iter_surfaces, load_bundle
from g2.sim.source_scope import REVIEWED_SCOPE, SUBSET_SCOPE

AXES={
    "floor_top":([1,0,0],[0,1,0],[0,0,-1]),
    "upper_up":([1,0,0],[0,1,0],[0,0,1]),
    "+X":([0,-1,0],[0,0,1],[1,0,0]),
    "-X":([0,1,0],[0,0,1],[-1,0,0]),
    "+Y":([1,0,0],[0,0,1],[0,1,0]),
    "-Y":([-1,0,0],[0,0,1],[0,-1,0]),
}
CARDINAL=("+X","-X","+Y","-Y")


def rasterize(xyz,rgb,color_valid,owners,selected,bounds_min,bounds_max,axis, *,
              meters_per_pixel=.05,meshes=(),surface_tolerance=0,max_pixels=4_000_000,
              asset_fill_radius_m=None, renderer_backend="cpu",
              opaque_ray_owner_indices=None):
    if renderer_backend not in ("cpu","gpu"):
        raise ContractError("unsupported G2 rasterizer backend")
    if axis not in AXES or not math.isfinite(meters_per_pixel) or meters_per_pixel<=0:
        raise ContractError("invalid orthographic recipe")
    right,up,forward=np.asarray(AXES[axis],float)
    lo,hi=np.asarray(bounds_min,float),np.asarray(bounds_max,float)
    if lo.shape!=(3,) or hi.shape!=(3,) or not np.isfinite([lo,hi]).all() or np.any(hi<lo):
        raise ContractError("invalid projection bounds")
    corners=np.asarray([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
    uv=corners@np.stack([right,up],axis=1)
    origin=np.floor(uv.min(axis=0)/meters_per_pixel)*meters_per_pixel
    dimensions=np.floor((uv.max(axis=0)-origin)/meters_per_pixel+1e-8).astype(np.int64)+1
    width,height=map(int,dimensions)
    if width<1 or height<1 or width*height>max_pixels:
        raise ContractError("projection exceeds pixel budget")
    depth=np.full((height,width),np.inf)
    geometry=np.zeros((height,width),bool)
    owner_image=np.full((height,width),-2,np.int32)
    image=np.zeros((height,width,3),np.uint8)
    valid=np.zeros((height,width),bool)
    metadata={"axis":axis,"right_world":right.tolist(),"up_world":up.tolist(),
              "forward_world":forward.tolist(),"uv_min_world":origin.tolist(),
              "meters_per_pixel":meters_per_pixel,"width":width,"height":height,
              "depth_kind":"signed_world_dot_forward","pixel_centers":"uv_min+(column+0.5,bottom_row+0.5)*mpp",
              "color_depth_tolerance_m":surface_tolerance,
              "color_support":"NATIVE_VOXEL_COLOR_NOT_CAMERA_PIXEL",
              "world_bounds_min":lo.tolist(),"world_bounds_max":hi.tolist()}
    if not selected:
        return image,valid,geometry,np.full_like(depth,np.nan),owner_image,metadata
    if renderer_backend == "cpu":
        # Geometry can occlude without RGB. Never paint source GT/semantic palettes.
        for entity,vertices,triangles in meshes:
            if entity not in selected:
                continue
            vertices=np.asarray(vertices,float)
            triangles=np.asarray(triangles,int)
            if not vertices.size or not triangles.size:
                continue
            projected=np.column_stack([(vertices@right-origin[0])/meters_per_pixel,
                                       (vertices@up-origin[1])/meters_per_pixel,
                                       vertices@forward])
            for triangle in projected[triangles]:
                a,b,c=triangle
                determinant=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
                if abs(determinant)<1e-10:
                    continue
                x0=max(0,int(np.floor(triangle[:,0].min())));x1=min(width-1,int(np.floor(triangle[:,0].max())))
                y0=max(0,int(np.floor(triangle[:,1].min())));y1=min(height-1,int(np.floor(triangle[:,1].max())))
                if x1<x0 or y1<y0:
                    continue
                xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5)
                wa=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/determinant
                wb=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/determinant
                wc=1-wa-wb
                z=wa*a[2]+wb*b[2]+wc*c[2]
                rows=height-1-np.arange(y0,y1+1)
                target=depth[np.ix_(rows,np.arange(x0,x1+1))]
                near,far=(corners@forward).min(),(corners@forward).max()
                replace=(wa>=-1e-10)&(wb>=-1e-10)&(wc>=-1e-10)&(z<target)&(z>=near-1e-9)&(z<=far+1e-9)
                rr,cc=np.nonzero(replace);rr=height-1-(rr+y0);cc=cc+x0
                depth[rr,cc]=z[replace];geometry[rr,cc]=True;owner_image[rr,cc]=entity
    else:
        # F12 candidate: replace ONLY the original G2 triangle/depth raster with
        # GPU FP64 deterministic per-pixel evaluation of the same triangle formula.
        # Keep all native G2 selection, colored-voxel projection, ownership, masks,
        # KDTree recovery, and empty-direction rules below unchanged.
        from .exact_compute import get_engine
        gpu_start=time.perf_counter()
        geometry, gpu_depth, owner_image, gpu_dims, gpu_info=get_engine().draw(
            meshes,selected,lo,hi,axis,meters_per_pixel)
        if gpu_dims != (width,height):
            raise ContractError("F12 GPU geometry pixel bounds differ from G2 CPU")
        depth=np.where(geometry,gpu_depth,np.inf)
        metadata["gpu_geometry_kernel"] = gpu_info
        metadata["gpu_geometry_wall_seconds"] = time.perf_counter()-gpu_start
    xyz=np.asarray(xyz,float);rgb=np.asarray(rgb,np.uint8);color_valid=np.asarray(color_valid,bool)
    owners=np.asarray(owners,np.int32)
    if xyz.ndim!=2 or xyz.shape[1]!=3 or rgb.shape!=(len(xyz),3) or color_valid.shape!=(len(xyz),) or owners.shape!=(len(xyz),) or not np.isfinite(xyz).all():
        raise ContractError("invalid surface arrays")
    if renderer_backend == "gpu" and len(xyz):
        from .gpu_color_select import get_projector
        indices,rows,columns,z,color_info = get_projector().select(
            xyz,rgb,color_valid,owners,selected,lo,hi,
            right,up,forward,origin,meters_per_pixel,width,height)
        metadata.update(color_info)
        metadata["color_pixel_selector_backend"]="gpu_lexsort_exact"
    else:
        members=np.isin(owners,list(selected)) & np.all((xyz>=lo-1e-9)&(xyz<=hi+1e-9),axis=1)
        indices=np.flatnonzero(members)
        p=xyz[indices]
        columns=np.floor((p@right-origin[0])/meters_per_pixel+1e-8).astype(np.int64)
        rows=height-1-np.floor((p@up-origin[1])/meters_per_pixel+1e-8).astype(np.int64)
        inside=(columns>=0)&(columns<width)&(rows>=0)&(rows<height)
        indices=indices[inside];columns=columns[inside];rows=rows[inside]
        if len(indices):
            z=xyz[indices]@forward
            pixel=rows*width+columns
            packed_rgb=rgb[indices].astype(np.uint32)@np.asarray([65536,256,1],np.uint32)
            # Deterministic ties, with valid observed color winning identical geometry.
            order=np.lexsort((packed_rgb,-color_valid[indices].astype(int),z,pixel))
            first=np.r_[True,pixel[order][1:]!=pixel[order][:-1]]
            order=order[first]
            indices=indices[order];rows=rows[order];columns=columns[order];z=z[order]
    if len(indices):
        old=depth[rows,columns];old_owner=owner_image[rows,columns]
        accepted=(z<=old+1e-9) | ((owners[indices]==old_owner)&(z<=old+surface_tolerance))
        indices=indices[accepted];rows=rows[accepted];columns=columns[accepted];z=z[accepted]
        geometry[rows,columns]=True
        depth[rows,columns]=np.minimum(depth[rows,columns],z)
        owner_image[rows,columns]=owners[indices]
        observed=color_valid[indices] & (owners[indices]>=0)
        image[rows[observed],columns[observed]]=rgb[indices[observed]]
        valid[rows[observed],columns[observed]]=True
    # Only for full-scene ASSET color, never for unobserved camera RGB-D.
    # Reproject a nearby real asset surface sample to the visible mesh point,
    # using the SAME native object ID; don't spread colors across objects.
    if renderer_backend=="gpu" and asset_fill_radius_m is not None:
        from .gpu_color_select import get_projector
        from .gpu_nearest_recovery import recover
        image,valid,filled,fallback,nn_meta=recover(
            get_projector(),xyz,rgb,color_valid,owners,
            geometry,valid,image,depth,owner_image,
            origin,right,up,forward,meters_per_pixel,
            asset_fill_radius_m,meters_per_pixel,
            opaque_ray_owner_indices=opaque_ray_owner_indices)
        metadata["asset_unassigned_near_surface_pixels"]=fallback
        metadata["unassigned_color_not_promoted_to_entity_identity"]=True
        metadata["asset_surface_reprojected_pixels"]=filled
        metadata["asset_fill_radius_m"]=asset_fill_radius_m
        metadata["asset_fill_provenance"]="NEAREST_SAME_ENTITY_3D_MUJOCO_ASSET_SURFACE_SAMPLE_NOT_CAMERA"
        metadata.update(nn_meta)
    else:
        if asset_fill_radius_m is not None:
            if not math.isfinite(asset_fill_radius_m) or asset_fill_radius_m <= 0:
                raise ContractError("invalid asset surface recovery radius")
            try:
                from scipy.spatial import cKDTree
            except ImportError as exc:
                raise ContractError("asset surface recovery requires scipy") from exc
            missing=geometry & ~valid & (owner_image>=0)
            filled=0
            for owner_id in np.unique(owner_image[missing]):
                sample=np.flatnonzero((owners==owner_id)&color_valid)
                targets=np.argwhere(missing & (owner_image==owner_id))
                if not len(sample) or not len(targets):
                    continue
                tree=cKDTree(xyz[sample])
                for group in np.array_split(targets,max(1,int(math.ceil(len(targets)/100000)))):
                    rows2,cols2=group[:,0],group[:,1]
                    uv0=origin[0]+(cols2+.5)*meters_per_pixel
                    uv1=origin[1]+(height-rows2-.5)*meters_per_pixel
                    surface=uv0[:,None]*right+uv1[:,None]*up+depth[rows2,cols2,None]*forward
                    distances,nearest=tree.query(surface,k=1,distance_upper_bound=asset_fill_radius_m,workers=1)
                    inside=np.isfinite(distances)
                    rr,cc=rows2[inside],cols2[inside]
                    image[rr,cc]=rgb[sample[nearest[inside]]]
                    valid[rr,cc]=True
                    filled+=int(inside.sum())
            # F2 asset samples contain valid scene RGB with an UNKNOWN native
            # owner (e.g. visual floor vs collision floor ID). Spatially bind only
            # when a source sample physically lies on the projected GT surface.
            # The inferred identity is NOT promoted to the SG or point cloud.
            unassigned=np.flatnonzero((owners==-1)&color_valid)
            fallback=0
            if len(unassigned):
                targets=np.argwhere(geometry & ~valid & (owner_image>=0))
                if len(targets):
                    tree=cKDTree(xyz[unassigned])
                    for group in np.array_split(targets,max(1,int(math.ceil(len(targets)/100000)))):
                        rows2,cols2=group[:,0],group[:,1]
                        uv0=origin[0]+(cols2+.5)*meters_per_pixel
                        uv1=origin[1]+(height-rows2-.5)*meters_per_pixel
                        surface=uv0[:,None]*right+uv1[:,None]*up+depth[rows2,cols2,None]*forward
                        distances,nearest=tree.query(surface,k=1,distance_upper_bound=min(.06,asset_fill_radius_m),workers=1)
                        close=np.isfinite(distances)
                        rr,cc=rows2[close],cols2[close]
                        image[rr,cc]=rgb[unassigned[nearest[close]]]
                        valid[rr,cc]=True
                        fallback+=int(close.sum())
            metadata["asset_unassigned_near_surface_pixels"]=fallback
            metadata["unassigned_color_not_promoted_to_entity_identity"]=True
            metadata["asset_surface_reprojected_pixels"]=filled
            metadata["asset_fill_radius_m"]=asset_fill_radius_m
            metadata["asset_fill_provenance"]="NEAREST_SAME_ENTITY_3D_MUJOCO_ASSET_SURFACE_SAMPLE_NOT_CAMERA"
    depth[~geometry]=np.nan
    return image,valid,geometry,depth,owner_image,metadata


def render(bundle,output,*,meters_per_pixel=.05,allow_oracle_diagnostic=False,
           allow_full_map_mujoco=False,reference_image=None,dense_manifest=None,
           surface_data=None,renderer_backend="cpu"):
    root=Path(bundle).resolve();out=new_output(output,[root])
    manifest,s=load_bundle(root)
    oracle=s["source_mode"]=="oracle_diagnostic"
    full=s['source_mode']=='full_map_mujoco_source'
    if oracle and not allow_oracle_diagnostic:
        raise ContractError("oracle native snapshot requires explicit diagnostic rendering")
    if full and not allow_full_map_mujoco:raise ContractError('Full Map source GT requires explicit rendering opt-in')
    if (dense_manifest is not None or surface_data is not None) and not full:
        raise ContractError('dense MuJoCo assets cannot enter RGB-D/perception view paths')
    if not oracle and not full and (manifest.get("semantic_stage")!="REAL_RECORDED_INPUT_OBSERVED" or
                       not manifest.get("observation_witness")):
        raise ContractError("BLOCKED_REAL_RGBD_OBSERVATIONS")
    if 'connection_protocol' in s:
        from .render_connections import render_v2
        return render_v2(root,manifest,s,output,meters_per_pixel=meters_per_pixel,
                         reference_image=reference_image,dense_manifest=dense_manifest,
                         surface_data=surface_data,renderer_backend=renderer_backend)
    if full:raise ContractError('Full Map requires native connection V2 evidence')
    by_id={e["id"]:e for e in s["entities"]}
    numeric={name:i for i,name in enumerate(sorted(by_id))}
    n=manifest["surface_points"]
    xyz=np.empty((n,3));rgb=np.empty((n,3),np.uint8);valid=np.empty(n,bool);owners=np.empty(n,np.int32)
    count=0
    for i,row in enumerate(iter_surfaces(root/"surfaces.csv",set(by_id))):
        if i>=n:raise ContractError("bundle surface count mismatch")
        xyz[i]=row[:3];rgb[i]=row[3:6];valid[i]=row[6];owners[i]=numeric.get(row[7],-1);count+=1
    if count!=n:
        raise ContractError("bundle surface count mismatch")
    meshes=[(numeric[e["id"]],e.get("vertices",[]),e.get("triangles",[])) for e in s["entities"]]
    out.mkdir(parents=True)
    views={}
    def emit(name,axis,members,lo=None,hi=None,boundary="not_applicable"):
        selected={numeric[e] for e in members}
        data=rasterize(xyz,rgb,valid,owners,selected,lo or s["bounds_min"],hi or s["bounds_max"],axis,
                       meters_per_pixel=meters_per_pixel,meshes=meshes,
                       surface_tolerance=s["color_voxel_leaf"]*.5+1e-7,
                       renderer_backend=renderer_backend)
        image,mask,geom,depth,owner,meta=data
        folder=out/name;folder.mkdir(parents=True)
        Image.fromarray(image).save(folder/"rgb.png")
        Image.fromarray(mask.astype(np.uint8)*255).save(folder/"color_valid.png")
        Image.fromarray(geom.astype(np.uint8)*255).save(folder/"geometry_valid.png")
        np.savez_compressed(folder/"geometry.npz",depth=depth.astype(np.float32),native_entity_index=owner)
        meta.update(native_entity_ids=sorted(members),boundary_type=boundary,
                    observed_color_pixels=int(mask.sum()),known_geometry_pixels=int(geom.sum()),
                    status="OBSERVED_PARTIAL_SURFACES" if mask.any() else "UNKNOWN_NO_OBSERVED_COLOR",
                    unassigned_points_excluded=int(np.count_nonzero(owners==-1)))
        write_json(folder/"view.json",meta)
        views[name]=meta
    emit("house/floor_top","floor_top",{e["id"] for e in s["entities"] if e["floor_member"]})
    emit("house/upper_up","upper_up",{e["id"] for e in s["entities"] if e["upper_member"] or e["kind"]=="ceiling"})
    room_refs={}
    island_refs={}
    for room in s["rooms"]:
        uid=room["uid"];center=np.asarray(room["center"])
        refs=["house/floor_top","house/upper_up"]
        for axis in CARDINAL:
            walls=set()
            for e in s["entities"]:
                if e["kind"]!="wall" or uid not in e.get("adjacent_room_uids",[]) or e.get("wall_axis") not in ("x","y"):
                    continue
                dim=0 if e["wall_axis"]=="x" else 1
                side=("+" if (e["bbox_min"][dim]+e["bbox_max"][dim])/2>=center[dim] else "-")+("X" if dim==0 else "Y")
                if side==axis:walls.add(e["id"])
            members=walls | {e["id"] for e in s["entities"] if e["kind"]=="object" and e["room_uid"]==uid and
                              e.get("island_id") is None and walls.intersection(e["root_affiliations"])}
            name="rooms/%d/%s"%(uid,axis.replace("+","plus_").replace("-","minus_"))
            emit(name,axis,members,boundary="physical_wall" if walls else "unknown")
            refs.append(name)
        room_refs[str(uid)]=refs
    # Group only by the native ID already supplied; no G2 connected components.
    for e in s["entities"]:
        island=e.get("island_id")
        if island:
            if not re.fullmatch(r"island_[0-9]+_entity_[0-9]+",island):
                raise ContractError("unsafe native Island identifier")
            island_refs.setdefault(island,{"room_uid":e["room_uid"],"member_entity_ids":[],"views":[]})["member_entity_ids"].append(e["id"])
    for island,record in island_refs.items():
        members=set(record["member_entity_ids"])
        padding=max(meters_per_pixel,s["color_voxel_leaf"]*.5+1e-7)
        lo=np.min([by_id[e]["bbox_min"] for e in members],axis=0)-padding
        hi=np.max([by_id[e]["bbox_max"] for e in members],axis=0)+padding
        record.update(world_bbox_min=lo.tolist(),world_bbox_max=hi.tolist(),center=((lo+hi)/2).tolist())
        for axis in CARDINAL:
            name="islands/%s/%s"%(island,axis.replace("+","plus_").replace("-","minus_"))
            emit(name,axis,members,lo.tolist(),hi.tolist());record["views"].append(name)
    recipe={"schema":"g2_six_island_recipe_v1","contract":"G2-v1.5-independent-islands",
            "meters_per_pixel":meters_per_pixel,"axes":AXES,"occlusion":"nearest_surface_including_uncolored_geometry",
            "room_frame":"world_axes_explicit","islands_in_room_cardinals":False}
    scope=manifest.get("source_scope",{"status":"LEGACY_PRESCAN_SOURCE_UNREVIEWED"})
    status="ORACLE_DIAGNOSTIC_ONLY" if oracle else "BLOCKED_NATIVE_STRUCTURAL_ROOTS"
    if not oracle and s["affiliations_complete"]:
        status="RECORDED_SPATIAL_PREVIEW"
        if ((s["geometry_source_mode"]=="PRESCAN_PREBUILT" and scope["status"]!=REVIEWED_SCOPE)
            or scope["status"] in (SUBSET_SCOPE,"LEGACY_PRESCAN_SOURCE_UNREVIEWED")):
            status="BLOCKED_FULL_SCENE_SOURCE_REVIEW"
    result={"schema":"g2_spatial_views_v1","status":status,
            "source_scope":scope,"full_scene_source_certified":not oracle and scope["status"]==REVIEWED_SCOPE,
            "scene_id":s["scene_id"],"source_sha256":s["source_sha256"],"frame_id":s["frame_id"],
            "native_bundle_version_sha256":manifest["version_sha256"],
            "entity_index_to_native_id":sorted(by_id),
            "native_entity_index_sentinels":{"background":-2,"unassigned_source":-1},
            "recipe":recipe,"recipe_sha256":hashlib.sha256(canonical(recipe)).hexdigest(),
            "room_six_refs":room_refs,"islands":island_refs,"views":views,
            "original_3d_bundle":str(root),"training_ready":False,
            "temporal_video":False,"private_layout_human_gate":"NOT_RUN"}
    result["files"]={str(p.relative_to(out)):{"sha256":digest(p),"bytes":p.stat().st_size}
                     for p in sorted(out.rglob("*")) if p.is_file()}
    write_json(out/"views.json",result)
    (out/"PREVIEW_COMPLETE").write_text("SPATIAL_VIEWS_NOT_TRAINING_ACCEPTANCE\n")
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle",required=True);p.add_argument("--output",required=True)
    p.add_argument("--meters-per-pixel",type=float,default=.05)
    p.add_argument("--allow-oracle-diagnostic",action="store_true")
    p.add_argument('--allow-full-map-mujoco',action='store_true');p.add_argument('--reference-image')
    p.add_argument('--dense-manifest',help='source-bound MuJoCo 10mm Visual color chunks; Full Map only')
    p.add_argument('--renderer-backend',choices=('cpu','gpu'),default='cpu')
    a=p.parse_args()
    result=render(a.bundle,a.output,meters_per_pixel=a.meters_per_pixel,
                  allow_oracle_diagnostic=a.allow_oracle_diagnostic,
                  allow_full_map_mujoco=a.allow_full_map_mujoco,
                  reference_image=a.reference_image,dense_manifest=a.dense_manifest,
                  renderer_backend=a.renderer_backend)
    print(result["status"],len(result["views"]))


if __name__=="__main__":
    main()
