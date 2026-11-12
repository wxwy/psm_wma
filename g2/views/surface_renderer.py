"""Source-independent surface hits, material evidence and layered composition.

The MuJoCo adapter keeps original Visual mesh/face IDs as its surface geometry
and samples only that face's material. A sensor surface adapter below consumes
10 mm map samples without MuJoCo. Both produce the same composition contract.
Legacy fused owner colors and nearest-object recovery never enter this path.
"""
from __future__ import annotations

import hashlib
import time

import numpy as np

from g2.io import ContractError
from g2.views.render import AXES


def projection_grid(low, high, axis, mpp):
    if axis not in AXES or not np.isfinite(mpp) or mpp <= 0:
        raise ContractError("invalid surface projection")
    low, high = np.asarray(low, float), np.asarray(high, float)
    if low.shape != (3,) or high.shape != (3,) or not np.isfinite([low, high]).all() or np.any(high < low):
        raise ContractError("invalid surface projection bounds")
    right, up, forward = (np.asarray(v, float) for v in AXES[axis])
    corners = np.asarray([[x, y, z] for x in (low[0], high[0])
                          for y in (low[1], high[1]) for z in (low[2], high[2])])
    uv = corners @ np.stack((right, up), axis=1)
    origin = np.floor(uv.min(axis=0) / mpp) * mpp
    w, h = np.floor((uv.max(axis=0) - origin) / mpp + 1e-8).astype(int) + 1
    if min(w, h) < 1 or w * h > 4_000_000:
        raise ContractError("surface view exceeds pixel budget")
    return right, up, forward, origin, int(w), int(h), float((corners @ forward).min()), float((corners @ forward).max())


def _empty_layer(shape):
    return dict(depth=np.full(shape, np.nan), rgb_linear=np.zeros((*shape, 3)),
                appearance_linear=np.zeros((*shape, 3)), appearance_alpha=np.zeros(shape),
                preview_optical=np.zeros(shape,bool), hit_cosine=np.full(shape,np.nan), alpha=np.zeros(shape),
                geometry_valid=np.zeros(shape, bool), color_valid=np.zeros(shape, bool),
                alpha_valid=np.zeros(shape, bool), geom_id=np.full(shape, -1, np.int64),
                material_id=np.full(shape, -1, np.int32), semantic_owner=np.full(shape, -1, np.int32),
                surface_id=np.full(shape, -1, np.int64), face_id=np.full(shape, -1, np.int32),
                visibility_ambiguous=np.zeros(shape,bool))


def native_opaque_layer(room_samples, source_sha256, room_uid, low, high, axis, mpp,
                        *, backend='cpu'):
    """Convert verified 10 mm map surfels to the same composition contract.

    Cell identity is independent of SG semantics and intentionally distinct
    from a MuJoCo visual Geom ID. Missing cells remain missing geometry, not
    a white-colored physical plane.
    """
    provenance=room_samples.get('provenance',{})
    if (provenance.get('kind')!='NATIVE_10MM_OPAQUE_SURFACE_CELLS'
        or provenance.get('source_sha256')!=source_sha256
        or provenance.get('room_uid')!=room_uid
        or provenance.get('source_coordinates')!='NATIVE_ROOM_REFERENCE'):
        raise ContractError('native 10mm map does not match source renderer/Room')
    if backend == 'gpu':
        from g2.views.gpu_surface_map import get_projector
        ix,count,gpu_meta=get_projector().draw(room_samples['points'],low,high,axis,mpp)
        geometry=ix>=0
        shape=geometry.shape
        opaque=_empty_layer(shape)
        opaque['geometry_valid']=geometry.copy()
        entries=ix[geometry]
        selected=np.asarray(room_samples['geom_id'])
        opacity=np.asarray(room_samples['alpha'])
        color=np.asarray(room_samples['rgb_linear'])
        val=np.asarray(room_samples['color_valid'])
        owners=np.asarray(room_samples['semantic_owner'])
        if not np.all(opacity[entries]==1) or not np.all(room_samples['alpha_valid'][entries]):
            raise ContractError('unverified native map opacity')
        opaque['geom_id'][geometry]=selected[entries]
        opaque['surface_id'][geometry]=selected[entries]
        opaque['semantic_owner'][geometry]=owners[entries]
        opaque['color_valid'][geometry]=val[entries] & (count[geometry]==1)
        opaque['rgb_linear'][geometry]=color[entries]
        opaque['appearance_linear'][geometry]=color[entries]
        opaque['alpha'][geometry]=1.
        opaque['appearance_alpha'][geometry]=1.
        opaque['alpha_valid'][geometry]=True
        forward=np.asarray(AXES[axis][2],dtype=np.float64)
        opaque['depth'][geometry]=np.asarray(room_samples['points'])[entries] @ forward
        opaque['visibility_ambiguous'][geometry]=count[geometry]>1
        values=opaque['color_valid']
        info=gpu_meta
    elif backend=='cpu':
        result=project_surface_samples(room_samples,low,high,axis,mpp)
        geometry=result['geometry_valid']
        shape=geometry.shape
        opaque=_empty_layer(shape)
        opaque['geometry_valid']=geometry.copy()
        opaque['depth']=np.where(geometry,result['front_depth'],np.nan)
        opaque['geom_id']=np.where(geometry,result['front_geom_id'],-1)
        opaque['surface_id']=opaque['geom_id'].copy()
        opaque['material_id']=np.full(shape,-1,np.int32)
        opaque['semantic_owner']=result['front_owner']
        opaque['color_valid']=result['composite_valid'].copy()
        opaque['rgb_linear']=np.nan_to_num(result['composite_rgb_linear'],nan=0.0)
        opaque['appearance_linear']=opaque['rgb_linear'].copy()
        opaque['alpha']=np.where(geometry,1.0,0.0)
        opaque['appearance_alpha']=opaque['alpha'].copy()
        opaque['alpha_valid']=geometry.copy()
        values=result['composite_valid']
        info={'backend':'CPU_SURFEL_REFERENCE'}
    else:
        raise ContractError('invalid verified map projection backend')
    receipt=dict(source='NATIVE_10MM_OPAQUE_SURFACE_CELLS',
        independent_surface_identity='VOXEL_COORD_MORTON_NOT_MUJOCO_GEOM',
        valid_pixels=int(values.sum()),geometry_pixels=int(geometry.sum()),
        static_cache_hit=False,full_source_id=provenance['source_sha256'])
    receipt.update(info)
    return opaque,receipt


def cpu_mesh_hits(meshes, selected, low, high, axis, mpp):
    """Small-scene CPU surface backend, also a GL-independent hit oracle."""
    right, up, forward, origin, w, h, near, far = projection_grid(low, high, axis, mpp)
    ids = np.full((h, w), -2, np.int32)
    depths = np.full((h, w), np.inf)
    faces_out = np.full((h, w), -1, np.int32)
    bary_out = np.full((h, w, 3), np.nan)
    ambiguous=np.zeros((h,w),bool)
    triangles = 0
    for gid, vertices, faces in meshes:
        if gid not in selected:
            continue
        vertices = np.asarray(vertices, float)
        uv = np.column_stack((vertices @ right, vertices @ up))
        z = vertices @ forward
        for face_index, tri in enumerate(np.asarray(faces, int)):
            planar = uv[tri]
            matrix = np.vstack((planar.T, np.ones(3)))
            if abs(np.linalg.det(matrix)) < 1e-10 * mpp * mpp:
                continue
            xmin, ymin = np.maximum(0, np.floor((planar.min(axis=0) - origin) / mpp).astype(int))
            xmax, ymax = np.minimum([w - 1, h - 1], np.floor((planar.max(axis=0) - origin) / mpp).astype(int))
            if xmax < xmin or ymax < ymin:
                continue
            cc, yy = np.meshgrid(np.arange(xmin, xmax + 1), np.arange(ymin, ymax + 1))
            rr = h - 1 - yy
            query = np.stack((origin[0] + (cc + .5) * mpp,
                              origin[1] + (yy + .5) * mpp, np.ones_like(cc)), axis=0)
            weights = (np.linalg.inv(matrix) @ query.reshape(3, -1)).T.reshape(*cc.shape, 3)
            depth = weights @ z[tri]
            candidate=((weights >= -1e-10).all(axis=2) & (depth >= near - 1e-9) & (depth <= far + 1e-9))
            previous=depths[rr,cc]
            closer=candidate & (depth<previous-1e-9)
            ambiguous[rr[closer],cc[closer]]=False
            tie=candidate & (np.abs(depth-previous)<=1e-9) & (ids[rr,cc]>=0) & (ids[rr,cc]!=gid)
            ambiguous[rr[tie],cc[tie]]=True
            good=candidate & (depth<previous)
            r, c = rr[good], cc[good]
            depths[r, c], ids[r, c], faces_out[r, c] = depth[good], gid, face_index
            bary_out[r, c] = weights[good]
            triangles += 1
    depths[ids < 0] = np.nan
    return ids >= 0, depths, ids, (w, h), {"triangles": triangles, "backend": "cpu"}, faces_out, bary_out, ambiguous


def cpu_mesh_layers(meshes, selected, low, high, axis, mpp, *, max_hits=8):
    """Independent small-scene reference for up to 8 visible intersections.

    This CPU oracle is intentionally not optimized for entire RoboCasa rooms.
    It validates that two distinct depths of one source Geom survive, while
    coplanar triangulation seams do not multiply opacity.
    """
    right, up, forward, origin, w, h, near, far=projection_grid(low,high,axis,mpp)
    candidates={}
    count=0
    for gid,verts,faces in meshes:
        if gid not in selected: continue
        verts=np.asarray(verts,float)
        uv=np.column_stack((verts@right,verts@up))
        z=verts@forward
        for fi,face in enumerate(np.asarray(faces,int)):
            tri=uv[face]
            matrix=np.vstack((tri.T,np.ones(3)))
            if abs(np.linalg.det(matrix))<1e-10*mpp*mpp:continue
            xmin,ymin=np.maximum(0,np.floor((tri.min(axis=0)-origin)/mpp).astype(int))
            xmax,ymax=np.minimum([w-1,h-1],np.floor((tri.max(axis=0)-origin)/mpp).astype(int))
            if xmax<xmin or ymax<ymin:continue
            for iy in range(ymin,ymax+1):
                for ix in range(xmin,xmax+1):
                    weight=np.linalg.solve(matrix,[origin[0]+(ix+.5)*mpp,origin[1]+(iy+.5)*mpp,1])
                    if np.min(weight)<-1e-10:continue
                    depth=float(weight@z[face])
                    if not near-1e-9<=depth<=far+1e-9:continue
                    candidates.setdefault((h-1-iy,ix),[]).append((depth,gid,fi,weight))
                    count+=1
    if count==0:raise ValueError("no G2 selected projectable geometry")
    shape=(max_hits,h,w)
    ids=np.full(shape,-2,np.int32)
    depths=np.full(shape,np.nan)
    face_ids=np.full(shape,-1,np.int32)
    bary=np.full((*shape,3),np.nan)
    truncated=np.zeros((h,w),bool)
    for (y,x),rows in candidates.items():
        rows.sort(key=lambda v:(v[0],v[1],v[2]))
        dedup=[]
        for row in rows:
            if any(old[1]==row[1] and abs(old[0]-row[0])<=1e-9 for old in dedup):
                continue
            dedup.append(row)
        truncated[y,x]=len(dedup)>max_hits
        for level,(z,gid,fi,weight) in enumerate(dedup[:max_hits]):
            ids[level,y,x]=gid;depths[level,y,x]=z
            face_ids[level,y,x]=fi;bary[level,y,x]=weight
    return (ids>=0,depths,ids,(w,h),{"backend":"cpu","multi_hit_cap":max_hits,
            "multi_hit_overflow_pixels":int(truncated.sum())},face_ids,bary,truncated)


def _merge_opaque(first, second):
    """Select the actual nearest opaque hit; an unknown color still occludes."""
    choose = second["geometry_valid"] & (~first["geometry_valid"] | (second["depth"] < first["depth"]))
    result = {}
    for key, value in first.items():
        result[key] = value.copy()
        result[key][choose] = second[key][choose]
    tie=(first['geometry_valid'] & second['geometry_valid'] &
         (np.abs(first['depth']-second['depth'])<=1e-9) & (first['geom_id']!=second['geom_id']))
    same=(tie & first['color_valid'] & second['color_valid']
          & first['alpha_valid'] & second['alpha_valid']
          & (first['alpha']==1) & (second['alpha']==1)
          & np.all(np.abs(first['rgb_linear']-second['rgb_linear'])<=1e-7,axis=-1)
          & np.all(np.abs(first['appearance_linear']-second['appearance_linear'])<=1e-7,axis=-1))
    result['visibility_ambiguous'] |= tie
    # Color may be certain despite ambiguous semantic/Geom attribution.
    result['color_valid'][tie] = same[tie]
    return result


def selected_layer_field(layers, geom_ids, depths, field, default=-1):
    """Gather all evidence from the final winner, including pixel-opaque alpha."""
    result=np.full(geom_ids.shape,default,dtype=layers[0][field].dtype)
    for layer in layers:
        match=(layer['geometry_valid'] & (layer['geom_id']==geom_ids)
               & (layer['depth']==depths))
        result[match]=layer[field][match]
    return result


def single_hit_alpha_valid(descriptor, alpha, valid):
    """A varying-alpha mesh may hide another face of its own Geom.

    Until that adapter depth-peels a Geom, only a known opaque first hit can
    certify the ray. In particular, an alpha-zero first hit must not silently
    expose a supposedly complete background while its deeper faces are absent.
    """
    result = np.asarray(valid, bool).copy()
    if (descriptor.get('reason') == 'COMPILED_TEXTURE_ALPHA_RANGE'
            and descriptor.get('alpha_min') != descriptor.get('alpha_max')):
        result &= np.asarray(alpha) == 1.0
    return result


class SurfaceRenderer:
    """One episode's material decoder and static surface projection cache.

    Cached keys include selected geometry, source identity, pose, room frame,
    crop and resolution. Dynamic geometry is projected against the complete
    cached background each state, so vacated regions cannot leave a ghost.
    """
    def __init__(self, model, source_sha256, static_geom_ids=(), *, backend="gpu"):
        from g2.sim.material_resolver import MaterialResolver
        if backend not in ("gpu", "cpu"):
            raise ContractError("unknown surface renderer backend")
        self.model = model
        self.source_sha256 = source_sha256
        self.materials = MaterialResolver(model, source_sha256=source_sha256)
        self.static_ids = set(static_geom_ids)
        self.backend = backend
        self.cache = {}
        self._static_pose_reference = {}
        self.cache_hits = 0
        self.cache_misses = 0

    def invalidate_materials(self, texture_id=None):
        """Invalidate decoded texture and every projection that used its color."""
        self.materials.invalidate(texture_id)
        self.cache.clear()

    def _mesh_records(self, registry, room, ids):
        from g2.views.surface_registry import select_shell_faces
        axes = np.asarray(room["reference_frame"]["axes_world"], float)
        origin = np.asarray(room["reference_frame"]["origin_world"], float)
        center = np.asarray(room.get("center", origin), float)
        meshes, source_faces, shell_evidence = [], {}, {}
        for gid in sorted(ids):
            surface = registry["surfaces"][gid]
            vertices = np.asarray(surface["local_vertices"], float)
            faces = np.asarray(surface["faces"], np.int32)
            world = np.asarray(surface["world_vertices"], float)
            position = np.asarray(surface["position"], float)
            rotation = np.asarray(surface["rotation"], float)
            keep, receipt = select_shell_faces(vertices, faces, surface.get("structural_role"),
                                                position, rotation, center)
            keep = np.asarray(keep, bool)
            source_faces[gid] = np.flatnonzero(keep)
            shell_evidence[str(gid)] = receipt
            if keep.any():
                meshes.append((gid, (world - origin) @ axes.T, faces[keep]))
        return meshes, source_faces, shell_evidence

    def _cache_key(self, registry, room, ids, low, high, axis, mpp, multiple):
        """O(number of Geoms), not O(triangles). Source mesh topology is immutable.

        An explicit material invalidation clears this cache. Transform and all
        effective per-Geom material/tint parameters are part of the key.
        """
        digest=hashlib.sha256(self.source_sha256.encode())
        digest.update(b"DEPTH_LAYER_SET" if multiple else b"NEAREST_LAYER")
        for value in (low,high,room["reference_frame"]["origin_world"],
                      room["reference_frame"]["axes_world"],room.get("center",[0,0,0])):
            digest.update(np.asarray(value,dtype="<f8").tobytes())
        digest.update((axis+repr(float(mpp))).encode())
        for gid in sorted(ids):
            row=registry["surfaces"][gid]
            descriptor=self.materials.descriptor(gid,row["kind"])
            digest.update(np.asarray([gid,descriptor["material_id"]],dtype="<i8").tobytes())
            pose=np.concatenate((np.asarray(row["position"],dtype=np.float64),
                                 np.asarray(row["rotation"],dtype=np.float64).reshape(-1)))
            if gid in self.static_ids:
                if gid not in self._static_pose_reference:
                    self._static_pose_reference[gid]=pose.copy()
                canonical=self._static_pose_reference[gid]
                if np.max(np.abs(canonical-pose))>1e-10:
                    raise ContractError("source geom moved after static classification")
                # State replay may perturb static transforms below the source
                # preflight's 1e-10 tolerance. Hash the *verified canonical
                # pose*, not insignificant floating point jitter.
                pose=canonical
            digest.update(np.asarray(pose,dtype="<f8").tobytes())
            digest.update(np.asarray(descriptor["effective_rgba"],dtype="<f8").tobytes())
            digest.update(repr((descriptor, row.get("semantic_owner_index"),
                                row.get("structural_role"))).encode())
        return digest.digest()

    def _paint_hits(self, registry, room, source_faces, geometry, depth, gids,
                    face_ids, bary, ambiguous, *, multi=False):
        from g2.views.material_appearance import preview_optics
        layer=_empty_layer(geometry.shape)
        safe=np.where(geometry,gids,-1)
        # Source geometry identity is an ORIGINAL compiled (Geom, face)
        # pair, not the Geom alone. Two coplanar triangles of the SAME Geom
        # can have distinct UV/material evidence at identical depth, e.g.
        # near a mesh seam. They are different surfaces, not duplicates.
        # Reserve low IDs for sensor/native map layers and -1 for UNKNOWN.
        layer.update(depth=depth, geometry_valid=geometry, geom_id=safe,
                     surface_id=np.full(safe.shape,-1,dtype=np.int64))
        layer["visibility_ambiguous"]=np.asarray(ambiguous,bool).copy()
        receipts={}
        axes=np.asarray(room["reference_frame"]["axes_world"],float)
        # AXES is in the native Room frame; surface normals originate in
        # local geom coordinates and must be rotated into that Room frame.
        forward=np.asarray(AXES[room.get("_current_view_axis")],float)[2] if "_current_view_axis" in room else None
        for gid in np.unique(gids[geometry]):
            gid=int(gid)
            record=registry["surfaces"][gid]
            select=geometry & (gids==gid)
            source_face=source_faces[gid][face_ids[select]]
            weight=bary[select]
            tris=np.asarray(record["local_vertices"],float)[np.asarray(record["faces"],int)[source_face]]
            local=np.einsum("bi,bij->bj",weight,tris)
            sample=self.materials.sample(gid,record["kind"],source_face,weight,local_points=local)
            layer["rgb_linear"][select]=sample.rgb_linear
            layer["appearance_linear"][select]=sample.appearance_linear
            layer["alpha"][select]=sample.alpha
            layer["color_valid"][select]=sample.color_valid
            descriptor=self.materials.descriptor(gid,record["kind"])
            alpha_valid=(sample.alpha_valid if multi else
                         single_hit_alpha_valid(descriptor,sample.alpha,sample.alpha_valid))
            layer["alpha_valid"][select]=alpha_valid
            layer["appearance_alpha"][select]=sample.alpha
            normals=np.cross(tris[:,1]-tris[:,0],tris[:,2]-tris[:,0])
            lengths=np.linalg.norm(normals,axis=1)
            normal_valid=lengths>1e-12
            cosine=np.full(len(weight),np.nan)
            if forward is not None and normal_valid.any():
                normals[normal_valid]/=lengths[normal_valid,None]
                room_normals=normals[normal_valid] @ np.asarray(record["rotation"],float).T @ axes.T
                cosine[normal_valid]=np.clip(np.abs(room_normals @ forward),0.,1.)
            layer["hit_cosine"][select]=cosine
            optics_known=sample.color_valid & alpha_valid
            appearance,opacity,enhanced=preview_optics(
                sample.appearance_linear,sample.alpha,optics_known,cosine)
            layer["appearance_linear"][select]=appearance
            layer["appearance_alpha"][select]=opacity
            layer["preview_optical"][select]=enhanced
            layer["material_id"][select]=sample.material_id
            owner=record.get("semantic_owner_index")
            layer["semantic_owner"][select]=-1 if owner is None else owner
            layer["face_id"][select]=source_face
            if gid<0 or gid>=2**31 or np.any((source_face<0)|(source_face>=2**32-1)):
                raise ContractError("source face identity overflow")
            layer["surface_id"][select]=(
                (np.int64(gid+1)<<np.int64(32)) |
                (source_face.astype(np.int64)+np.int64(1)))
            reason,count=np.unique(sample.reason_code,return_counts=True)
            alpha_reason,alpha_count=np.unique(sample.alpha_reason_code,return_counts=True)
            receipts[str(gid)]=dict(evidence=sample.evidence,
                color_reasons={str(k):int(v) for k,v in zip(reason,count)},
                alpha_reasons={str(k):int(v) for k,v in zip(alpha_reason,alpha_count)},
                preview_optical_pixels=int(enhanced.sum()),
                intra_geom_alpha_layers_unresolved_pixels=int((sample.alpha_valid & ~alpha_valid).sum()))
        # The caller classifies different-Geom ties after evaluating every
        # same-depth material candidate. Do not invalidate RGB prematurely.
        return layer,receipts

    def _resolve_equivalent_depth_ties(self, registry, room, meshes, source_faces,
                                       selected, low, high, axis, mpp,
                                       layer, tie):
        """Certify color at equal-depth boundaries without certifying identity.

        Compare original source UV samples for all candidate Geoms at the same
        depth. Same RGB and display appearance -> color is deterministic.
        Different material appearance or an incomplete same-depth hit stack
        remains UNKNOWN. Semantic Owner is never used to choose a winner.
        """
        if not tie.any():
            return np.zeros(tie.shape,bool), {"tie_input_pixels":0}
        if self.backend == "gpu":
            from g2.views.exact_compute import get_engine
            draw=get_engine().draw_layers
        else:
            draw=cpu_mesh_layers
        hit, depth, gids, _, info, face, bary, overflow = draw(
            meshes, selected, low, high, axis, mpp,max_hits=32)
        # An alternate GL compute route may round a source coordinate to
        # float32 even when the nearest-hit route retains FP64 intermediates.
        # This tolerance only reconciles two hits on the *same pixel* that
        # the primary FP64 pass already marked as a <=1e-9 depth tie; it is
        # NOT a broader visibility or contact-distance threshold.
        recon_eps=2*np.finfo(np.float32).eps*np.maximum(
            1.,np.abs(layer['depth']))
        same=hit & (np.abs(depth-layer['depth'][None,:,:])<=recon_eps[None,:,:])
        # The saved first-hit source must appear in the candidate stack.
        owned=(gids==layer['geom_id'][None,:,:]) & same
        proved=tie & owned.any(axis=0) & layer['color_valid']
        # If every returned hit is co-depth AND the K-buffer overflowed, more
        # candidates might have been dropped. Do not certify a truncated ray.
        proved &= ~(overflow & same.all(axis=0))
        room_copy=dict(room,_current_view_axis=axis)
        candidates=0
        distinct=np.zeros(tie.shape,bool)
        for index in range(same.shape[0]):
            alternate=tie & same[index] & (gids[index]!=layer['geom_id'])
            distinct |= alternate
            if not alternate.any():
                continue
            colored,_=self._paint_hits(registry,room_copy,source_faces,
                alternate,depth[index],gids[index],face[index],bary[index],
                np.zeros(tie.shape,bool),multi=True)
            match=(colored['color_valid'] & colored['alpha_valid']
                   & (colored['alpha']==1)
                   & np.all(np.abs(colored['rgb_linear']-layer['rgb_linear'])<=1e-7,axis=-1)
                   & np.all(np.abs(colored['appearance_linear']-layer['appearance_linear'])<=1e-7,axis=-1))
            proved[alternate & ~match]=False
            candidates+=int(alternate.sum())
        approved=proved & distinct
        summary=dict(tie_input_pixels=int(tie.sum()),
            source_first_hit_in_multi_stack=int((tie&owned.any(axis=0)).sum()),
            multi_all_coplanar_truncated_pixels=int((tie&overflow&same.all(axis=0)).sum()),
            same_depth_distinct_source_pixels=int((tie&distinct).sum()),
            equivalent_color_pixels=int(approved.sum()),
            unresolvable_pixels=int((tie&~approved).sum()))
        return approved,summary

    def _layer(self,registry,room,ids,low,high,axis,mpp,*,cacheable,multiple=False):
        grid=projection_grid(low,high,axis,mpp)
        shape=(grid[5],grid[4])
        if not ids:
            return ([] if multiple else _empty_layer(shape)), {"empty":True}
        cache_key=self._cache_key(registry,room,ids,low,high,axis,mpp,multiple) if cacheable else None
        if cache_key is not None and cache_key in self.cache:
            self.cache_hits+=1
            cached,evidence=self.cache[cache_key]
            return cached,dict(evidence,static_cache_hit=True)
        started=time.perf_counter()
        meshes,source_faces,shell=self._mesh_records(registry,room,ids)
        if not meshes:
            return ([] if multiple else _empty_layer(shape)), {"empty":True,"shell":shell}
        if self.backend=="gpu":
            from g2.views.exact_compute import get_engine
            draw=get_engine().draw_layers if multiple else get_engine().draw_hits
        else:
            draw=cpu_mesh_layers if multiple else cpu_mesh_hits
        try:
            geometry,depth,gids,size,info,face_ids,bary,ambiguity=draw(
                meshes,ids,low,high,axis,mpp)
        except ValueError as exc:
            if str(exc)!="no G2 selected projectable geometry":
                raise
            return ([] if multiple else _empty_layer(shape)), {"empty":True,"shell":shell}
        room_copy=dict(room,_current_view_axis=axis)
        if multiple:
            layers=[]
            receipts={}
            for i in range(geometry.shape[0]):
                if not geometry[i].any(): continue
                entry,evidence=self._paint_hits(registry,room_copy,source_faces,
                    geometry[i],depth[i],gids[i],face_ids[i],bary[i],
                    np.zeros(shape,bool),multi=True)
                layers.append(entry)
                receipts.update(evidence)
            overflow=np.asarray(ambiguity,bool)
            if overflow.any() and layers:
                # Unknown unseen rear surfaces can carry nonzero opacity.
                # Poison only rays with a truly truncated K-hit stack.
                last=layers[-1]
                last["alpha_valid"][overflow & last["geometry_valid"]]=False
                last["appearance_alpha"][overflow & last["geometry_valid"]]=np.nan
            value=layers
        else:
            value,receipts=self._paint_hits(registry,room_copy,source_faces,
                    geometry,depth,gids,face_ids,bary,ambiguity)
            equivalent,tie_proof=self._resolve_equivalent_depth_ties(
                registry,room,meshes,source_faces,ids,low,high,axis,mpp,value,ambiguity)
            value['color_valid'][ambiguity & ~equivalent]=False
            info=dict(info,equivalent_depth_tie_pixels=int(equivalent.sum()),
                      unresolved_depth_tie_pixels=int((ambiguity & ~equivalent).sum()),
                      depth_tie_proof=tie_proof)
        evidence=dict(info,surface_geom_ids=sorted(ids),shell=shell,
                      materials=receipts,
                      hit_and_material_s=round(time.perf_counter()-started,6),
                      static_cache_hit=False)
        if cache_key is not None:
            self.cache_misses+=1
            if len(self.cache)>=128:self.cache.pop(next(iter(self.cache)))
            self.cache[cache_key]=(value,evidence)
        return value,evidence

    def render(self, registry, room, members, low, high, axis, mpp=.01, *,
               island=False, opaque_surface_map=None):
        from g2.sim.texture_projection import linear_to_srgb
        from g2.views.surface_registry import select_surface_ids
        from g2.views.surface_composer import compose_surface_layers
        selected = select_surface_ids(registry, room["uid"], axis, members, low, high, island=island)
        opaque_ids = {gid for gid in selected if self.materials.is_guaranteed_opaque(gid)}
        transparent_ids = selected - opaque_ids
        if opaque_surface_map is None:
            static, static_info = self._layer(registry, room, opaque_ids & self.static_ids,
                                              low, high, axis, mpp, cacheable=True)
            dynamic, dynamic_info = self._layer(registry, room, opaque_ids - self.static_ids,
                                                low, high, axis, mpp, cacheable=False)
            opaque = _merge_opaque(static, dynamic)
        else:
            # Simulation Full Map: independently verified native 10mm color
            # cells can be the opaque input. Transparent GT Visual surfaces
            # still enter through their ordinary material layers.
            opaque, static_info = native_opaque_layer(
                opaque_surface_map,self.source_sha256,room['uid'],
                low,high,axis,mpp,backend=self.backend)
            dynamic_info = {'empty':True,'reason':'MAP_SUPPLIES_OPAQUE_GEOMETRY'}
        # All translucent geoms are depth-sorted together. Each Geom may
        # contribute multiple physical surfaces (front and rear shell faces).
        static_alpha, static_alpha_info=self._layer(
            registry,room,transparent_ids & self.static_ids,low,high,axis,mpp,
            cacheable=True,multiple=True)
        dynamic_alpha,dynamic_alpha_info=self._layer(
            registry,room,transparent_ids-self.static_ids,low,high,axis,mpp,
            cacheable=False,multiple=True)
        transparent=static_alpha+dynamic_alpha
        alpha_info=[static_alpha_info,dynamic_alpha_info]
        composed = compose_surface_layers(opaque, transparent, background_rgb_linear=np.ones(3))
        def appearance(layer):
            return dict(layer, rgb_linear=layer["appearance_linear"],
                        alpha=layer["appearance_alpha"])
        display = compose_surface_layers(appearance(opaque), [appearance(l) for l in transparent],
                                         background_rgb_linear=np.ones(3))
        image = np.rint(np.clip(linear_to_srgb(display["display_rgb_linear"]), 0, 1) * 255).astype(np.uint8)
        front = composed["front_geom_id"]
        geometry = front >= 0
        valid = composed["composite_valid"] & geometry
        # An unknown opaque color is visibly distinct from valid black.
        unknown_opaque = geometry & ~valid & (front == composed["opaque_geom_id"])
        image[unknown_opaque] = [210, 64, 210]
        spec_index = np.full(front.shape, -2, np.int32)
        material = np.full(front.shape, -1, np.int32)
        # Native map IDs are one-per-voxel (often >100k unique per View).
        # Never loop over them as if they were MuJoCo Geoms: that was an
        # accidental O(unique_cells * pixels) performance regression.
        native_cells=geometry & (front >= (1<<62))
        if native_cells.any() and opaque_surface_map is None:
            raise ContractError("native Morton surface ID without source map")
        spec_index[native_cells]=-1
        material[native_cells]=-1
        for gid in np.unique(front[geometry & ~native_cells]):
            record=registry["surfaces"].get(int(gid))
            if record is None:
                raise ContractError("unregistered Visual Geom in source View")
            spec_index[front==gid]=record["spec_index"]
            material[front==gid]=record["material_id"]
        right, up, forward, origin, w, h, _, _ = projection_grid(low, high, axis, mpp)
        foreground = [registry["surfaces"][g]["spec_index"] for g in selected
                      if registry["surfaces"][g].get("structural_role") is None]
        pixel_evidence = dict(composite_rgb_linear=composed["composite_rgb_linear"].astype(np.float32),
                              composite_valid=valid, front_depth=composed["front_depth"].astype(np.float32),
                              front_geom_id=front, front_material_id=material,
                              front_semantic_owner=composed["front_owner"],
                              opaque_depth=composed["opaque_depth"].astype(np.float32),
                              opaque_geom_id=composed["opaque_geom_id"],
                              opaque_semantic_owner=selected_layer_field([opaque,*transparent],composed['opaque_geom_id'],composed['opaque_depth'],'semantic_owner'),
                              opaque_material_id=selected_layer_field([opaque,*transparent],composed['opaque_geom_id'],composed['opaque_depth'],'material_id'),
                              opaque_color_valid=selected_layer_field([opaque,*transparent],composed['opaque_geom_id'],composed['opaque_depth'],'color_valid',False),
                              front_face_id=np.where(front == opaque["geom_id"], opaque["face_id"], -1))
        ambiguity=selected_layer_field([opaque,*transparent],front,composed['front_depth'],'visibility_ambiguous',False)
        pixel_evidence['visibility_ambiguous']=ambiguity
        pixel_evidence['preview_optical_approximation']=(
            selected_layer_field([opaque,*transparent],front,composed['front_depth'],
                                 'preview_optical',False))
        composed['front_valid'][ambiguity]=False
        for layer in transparent:
            chosen = geometry & layer["geometry_valid"] & (front == layer["geom_id"])
            pixel_evidence["front_face_id"][chosen] = layer["face_id"][chosen]
        for key in ("alpha", "unknown_mask", "coverage_alpha", "alpha_valid", "front_alpha", "front_alpha_valid", "front_valid"):
            if key in composed:
                pixel_evidence[key] = composed[key]
        meta = dict(axis=axis, right_world=right.tolist(), up_world=up.tolist(), forward_world=forward.tolist(),
                    uv_min_world=origin.tolist(), world_bounds_min=np.asarray(low).tolist(),
                    world_bounds_max=np.asarray(high).tolist(), width=w, height=h, meters_per_pixel=mpp,
                    pixel_centers="uv_min+(column+0.5,bottom_row+0.5)*mpp", depth_kind="signed_world_dot_forward",
                    surface_registry_schema=registry["schema"], surface_registry_geom_ids=sorted(selected),
                    surface_registry_unbound_selected=[g for g in sorted(selected)
                                                       if registry["surfaces"][g].get("semantic_owner_index") is None],
                    source_subgeom_rgb_identity_proof=True, source_collision_geometry_used_for_zbuffer=False,
                    source_transparency_composited=True, transparent_surface_count=len(transparent_ids),
                    transparent_visible_pixels=int(np.isin(front, list(transparent_ids)).sum()),
                    transparency_model="GPU_MULTI_HIT_K8_DEPTH_SORTED_ALPHA_WITH_TRUNCATION_GUARD",
                    preview_optical_policy="BLEND_ONLY_DIELECTRIC_FRESNEL_STUDIO_ENV_DISPLAY_ONLY",
                    preview_optical_approximation_pixels=int(sum(
                        layer["preview_optical"].sum() for layer in transparent)),
                    equivalent_depth_tie_pixels=int(static_info.get(
                        "equivalent_depth_tie_pixels",0)+dynamic_info.get(
                        "equivalent_depth_tie_pixels",0)),
                    output_rgb_policy="SOURCE_APPEARANCE_COMPAT_SRGB_LINEAR_COMPOSITE",
                    numeric_rgb_policy="SOURCE_MATERIAL_LINEAR_COMPOSITE",
                    source_material_evidence="EXACT_VISUAL_GEOM_FACE_BARYCENTRIC_UV",
                    geometry_source=("VERIFIED_NATIVE_10MM_OPAQUE_MAP_PLUS_VISUAL_MATERIAL_LAYERS"
                        if opaque_surface_map is not None
                        else "REGISTRY_VISUAL_SURFACE_MESH_ADAPTER"),
                    opaque_map_material_identity_known=False if opaque_surface_map is not None else True,
                    opaque_map_source_provenance=(opaque_surface_map['provenance']
                        if opaque_surface_map is not None else None),
                    valid_color_pixels=int(valid.sum()), unknown_color_pixels=int((geometry & ~valid).sum()),
                    unbound_visible_pixels=int((geometry & (composed['front_owner'] == -1)).sum()),
                    non_background_surface_indices=foreground,
                    stage_static=static_info, stage_dynamic=dynamic_info, stage_alpha=alpha_info,
                    static_cache_hits=self.cache_hits, static_cache_misses=self.cache_misses,
                    _pixel_evidence=pixel_evidence, training_ready=False)
        native_owner=np.where(geometry,composed["front_owner"],-2).astype(np.int32)
        return image, valid, geometry, composed["front_depth"], native_owner, spec_index, meta


def project_surface_samples(samples, low, high, axis, mpp=.01, *, background_rgb_linear=None):
    """RGB-D/Partial Map adapter for explicit high-resolution surface samples.

    A map must retain each surface's identity and separate opacity evidence.
    Observed RGB of already mixed transparent backgrounds must not be passed as
    an intrinsic transparent material. No MuJoCo, owner lookup or name is used.
    """
    from g2.views.surface_composer import compose_surface_layers
    xyz = np.asarray(samples["points"], float)
    gids = np.asarray(samples["geom_id"])
    n = len(xyz)
    if xyz.shape != (n, 3) or not np.isfinite(xyz).all() or gids.shape != (n,) or gids.dtype.kind not in "iu" or np.any(gids < 0):
        raise ContractError("invalid observed surface geometry/identity")
    right, up, forward, origin, w, h, near, far = projection_grid(low, high, axis, mpp)
    uv = np.column_stack((xyz @ right, xyz @ up))
    cc, yy = np.floor((uv - origin) / mpp).astype(np.int64).T
    depth = xyz @ forward
    inside = (cc >= 0) & (cc < w) & (yy >= 0) & (yy < h) & (depth >= near) & (depth <= far)
    fields = {}
    for key in ("rgb_linear", "alpha", "color_valid", "alpha_valid", "material_id", "semantic_owner"):
        fallback = np.full(n, -1, np.int32) if key in ("material_id", "semantic_owner") else None
        value = np.asarray(samples.get(key, fallback))
        if value.shape != ((n, 3) if key == "rgb_linear" else (n,)):
            raise ContractError("invalid observed surface field " + key)
        if key in ('color_valid','alpha_valid') and (value.dtype.kind not in 'biuf' or not np.isin(value,(0,1)).all()):
            raise ContractError('invalid observed surface boolean '+key)
        if key in ('material_id','semantic_owner') and (value.dtype.kind not in 'iu' or np.any(value < -1)):
            raise ContractError('invalid observed surface integer '+key)
        fields[key] = value
    # Keep distinct depths, including multiple surfaces of one semantic geom.
    # Known zero-alpha samples do not consume a visibility layer.
    indices=np.flatnonzero(inside & ~(fields['alpha_valid'].astype(bool) & (fields['alpha']==0)))
    pixels=(h-1-yy[indices])*w+cc[indices]
    order=np.lexsort((depth[indices],pixels))
    indices,pixels=indices[order],pixels[order]
    starts=np.r_[True,pixels[1:]!=pixels[:-1]] if len(indices) else np.empty(0,bool)
    rank=np.arange(len(indices))-np.maximum.accumulate(np.where(starts,np.arange(len(indices)),0)) if len(indices) else np.empty(0,int)
    cutoff=np.full(h*w,np.iinfo(np.int64).max,np.int64)
    solid=fields['alpha_valid'][indices].astype(bool) & (fields['alpha'][indices]==1)
    np.minimum.at(cutoff,pixels[solid],rank[solid])
    keep=rank<=cutoff[pixels]
    indices,pixels,rank=indices[keep],pixels[keep],rank[keep]
    count=int(rank.max())+1 if len(rank) else 0
    if count>64:
        raise ContractError('observed transparent surfaces exceed 64-layer budget')
    opaque=_empty_layer((h,w));transparent=[]
    for level in range(count):
        ix=indices[rank==level]
        rr, col = h - 1 - yy[ix], cc[ix]
        layer = _empty_layer((h, w))
        layer.pop('surface_id')  # No trustworthy primitive identity supplied.
        layer["geometry_valid"][rr, col] = True
        layer["depth"][rr, col] = depth[ix]
        layer["geom_id"][rr, col] = gids[ix]
        for key, values in fields.items():
            layer[key][rr, col] = values[ix]
        layer["appearance_linear"] = layer["rgb_linear"].copy()
        transparent.append(layer)
    return compose_surface_layers(opaque, transparent, background_rgb_linear=background_rgb_linear)
