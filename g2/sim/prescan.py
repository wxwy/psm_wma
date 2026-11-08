"""MuJoCo visual surfaces -> simulator-independent XYZRGB transport.

This is a source adapter, not a robot camera or a semantic detection frontend.
Source labels remain provenance; no GT class is sent as normal perception.
"""
import argparse
import hashlib
from pathlib import Path
import numpy as np
from g2.io import ContractError, canonical, digest, new_output, read_json, sha, write_json
from .source_geometry import (load_model, model_source_hash, apply_state,
                              primitive_mesh, surface_colors, effective_rgba)


def pointer(document, path):
    if not isinstance(path, str) or not path.startswith("/"):
        raise ContractError("ep_meta_pointer must be an explicit JSON pointer")
    current = document
    try:
        for key in path[1:].split("/"):
            key = key.replace("~1", "/").replace("~0", "~")
            current = current[int(key)] if isinstance(current, list) else current[key]
    except (KeyError, IndexError, ValueError, TypeError) as error:
        raise ContractError("missing ep_meta record: " + path) from error
    return current


def source_binding(spec, name, ep_meta):
    if spec.get("source_kind") == "mjcf":
        if spec.get("geom_name") != name:
            raise ContractError("MJCF provenance must name the exact geom")
        return {"kind": "mjcf", "geom_name": name}
    if spec.get("source_kind") != "ep_meta" or ep_meta is None:
        raise ContractError("visual geom requires official ep_meta or exact MJCF provenance")
    record = pointer(ep_meta, spec.get("ep_meta_pointer"))
    if not isinstance(record, dict) or record.get("name") != spec.get("source_instance_name"):
        raise ContractError("official fixture/object cfg identity mismatch")
    return {"kind": "ep_meta", "pointer": spec["ep_meta_pointer"], "record": record}


def sample_surface(vertices, faces, spacing, remaining):
    """Bounded barycentric sampling; retains even sub-resolution small surfaces."""
    if (vertices.ndim != 2 or vertices.shape[1] != 3 or not np.isfinite(vertices).all()
            or faces.ndim != 2 or faces.shape[1] != 3 or not len(faces)
            or np.any(faces < 0) or np.any(faces >= len(vertices))):
        raise ContractError("invalid visual mesh")
    points, face_ids, weights = [], [], []
    total = 0
    for index, tri in enumerate(vertices[faces]):
        if np.linalg.norm(np.cross(tri[1]-tri[0], tri[2]-tri[0])) <= 1e-14:
            raise ContractError("degenerate visual triangle")
        edge = max(np.linalg.norm(tri[i]-tri[j]) for i,j in ((0,1),(1,2),(2,0)))
        steps = max(1, int(np.ceil(edge / spacing)))
        count = (steps+1)*(steps+2)//2
        if total + count > remaining:
            raise ContractError("pre-scan point budget exceeded; choose coarser spacing")
        bary = np.asarray([[i/steps, j/steps, 1-(i+j)/steps]
                           for i in range(steps+1) for j in range(steps+1-i)])
        points.append(bary @ tri)
        face_ids.extend([index] * count)
        weights.append(bary)
        total += count
    return np.concatenate(points), np.asarray(face_ids), np.concatenate(weights)


def analytic_surface(points,kind,size,face_ids):
    points=points.copy()
    if kind in ("sphere","ellipsoid"):
        scale=size if kind=="ellipsoid" else np.repeat(size[0],3)
        directions=points/scale
        points=directions/np.linalg.norm(directions,axis=1)[:,None]*scale
    elif kind=="capsule":
        center=np.zeros_like(points);center[:,2]=np.clip(points[:,2],-size[1],size[1])
        directions=points-center
        points=center+directions/np.linalg.norm(directions,axis=1)[:,None]*size[0]
    elif kind=="cylinder":
        sides=np.isin(face_ids%4,[2,3])
        xy=points[sides,:2]
        points[sides,:2]=xy/np.linalg.norm(xy,axis=1)[:,None]*size[0]
    return points


def quote(value):
    if not isinstance(value, str) or not value or any(ord(c)<32 for c in value):
        raise ContractError("identity must be nonempty text without controls")
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def export(mjcf, metadata, output, *, states=None, frame=0, spacing=.05,
           asset_roots=(), ep_meta=None, state_format="qpos", world_frame="map",
           native_manifest=None, allow_partial_color=False, max_points=5_000_000):
    import mujoco
    mjcf, metadata = Path(mjcf).resolve(), Path(metadata).resolve()
    paths = [mjcf, metadata] + [Path(p).resolve() for p in (states, ep_meta, native_manifest) if p]
    out = new_output(output, [mjcf.parent, *asset_roots, *paths])
    if not np.isfinite(spacing) or spacing<=0 or type(max_points) is not int or not 0<max_points<=5_000_000:
        raise ContractError("invalid surface spacing/point budget")
    meta = read_json(metadata)
    if meta.get("schema") != "g2_sim_prescan_v1" or not isinstance(meta.get("geoms"), dict):
        raise ContractError("explicit g2_sim_prescan_v1 geom-role mapping required")
    scene_id = meta.get("scene_id")
    quote(scene_id); quote(world_frame)
    ep = read_json(ep_meta) if ep_meta else None
    model, sources = load_model(mjcf, asset_roots)
    closure = model_source_hash(sources)
    if states:
        if meta.get("state_source") != {"model_source_sha256": closure, "states_sha256": digest(states)}:
            raise ContractError("state_source must bind full model closure and states archive")
    data, state = apply_state(model, states, frame, state_format)
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, i) or "geom_%d"%i
             for i in range(model.ngeom)]
    if set(meta["geoms"]) != set(names):
        raise ContractError("every geom needs an explicit visual/collision/robot/auxiliary role")
    geometry_types = {int(getattr(mujoco.mjtGeom, "mjGEOM_"+kind.upper())):kind
                      for kind in ("box","sphere","ellipsoid","capsule","cylinder","mesh")}
    surfaces, records, excluded = [], [], []
    count = 0
    for g, name in enumerate(names):
        spec = meta["geoms"][name]
        role = spec.get("role")
        if role not in ("visual","collision","robot","auxiliary"):
            raise ContractError("invalid or absent geom role")
        binding = source_binding(spec, name, ep)
        if role != "visual" or effective_rgba(model,g)[3] <= 0:
            excluded.append({"geom_name":name,"role":role,"reason":"explicit_role_or_transparency","source":binding})
            continue
        kind = geometry_types.get(int(model.geom_type[g]))
        if kind is None:
            raise ContractError("finite visual surface required; infinite plane/hfield is unsupported")
        if kind == "mesh":
            mid = int(model.geom_dataid[g])
            va,vn,fa,fn = [int(getattr(model,k)[mid]) for k in
                           ("mesh_vertadr","mesh_vertnum","mesh_faceadr","mesh_facenum")]
            vertices = model.mesh_vert[va:va+vn].copy()
            faces = model.mesh_face[fa:fa+fn].copy()
        else:
            vertices,faces = primitive_mesh(kind,model.geom_size[g].copy())
        points,face_ids,weights = sample_surface(vertices,faces,spacing,max_points-count)
        if kind!="mesh":
            points=analytic_surface(points,kind,model.geom_size[g],face_ids)
        colors,valid,appearance = surface_colors(model,g,kind,face_ids,weights)
        if np.any(colors[:,3] < 1-1e-7):
            valid=False
            appearance=dict(appearance,unsupported="translucent_surface_requires_alpha_transport")
        world = points @ data.geom_xmat[g].reshape(3,3).T + data.geom_xpos[g]
        if not np.isfinite(world).all():
            raise ContractError("nonfinite world surface")
        rgba = np.rint(np.clip(colors,0,1)*255).astype(np.uint8)
        surfaces.append((world,rgba,bool(valid)))
        count += len(world)
        records.append({"geom_id":g,"geom_name":name,"role":"visual","source":binding,
                        "surface_points":len(world),"color_valid":bool(valid),"appearance":appearance,
                        "local_geometry_sha256":hashlib.sha256(vertices.astype("<f8").tobytes()+faces.astype("<i8").tobytes()).hexdigest()})
    if not count:
        raise ContractError("no visual surface samples")
    complete = all(item[2] for item in surfaces)
    if not complete and not allow_partial_color:
        raise ContractError("unsupported texture projection; partial export requires --allow-partial-color")
    adapter_sha=hashlib.sha256(Path(__file__).read_bytes()+Path(__file__).with_name("source_geometry.py").read_bytes()).hexdigest()
    visual_identity = {"schema":"g2_prescan_source_v1","adapter_source_sha256":adapter_sha,"model_source_sha256":closure,
                       "metadata":meta,"ep_meta":ep,"spacing_m":spacing,"world_frame":world_frame,
                       "mujoco_version":mujoco.__version__}
    visual_sha = hashlib.sha256(canonical(visual_identity)).hexdigest()
    source_sha = visual_sha
    native_binding = None
    if native_manifest:
        native = read_json(native_manifest)
        identity = native.get("source_identity",{})
        if (hashlib.sha256(canonical(identity)).hexdigest()!=native.get("source_sha256")
                or native.get("scene_id")!=scene_id or native.get("state",{}).get("frame_id")!=frame
                or identity.get("model_source_sha256")!=closure
                or identity.get("mujoco_version")!=mujoco.__version__
                or identity.get("metadata",{}).get("state_source",{}).get("states_sha256") !=
                   (digest(states) if states else None)):
            raise ContractError("native geometry and visual source/frame do not match")
        for key in ("format","row_sha256","timestamp","timestamp_source"):
            if native.get("state",{}).get(key)!=state.get(key):
                raise ContractError("restored state format/row/time differs from native geometry")
        source_sha = sha(native["source_sha256"])
        native_binding = {"path":str(Path(native_manifest).resolve()),"sha256":digest(native_manifest)}
    bounds = np.concatenate([p for p,_,_ in surfaces])
    out.mkdir(parents=True)
    cloud = out/"precolored.txt"
    with cloud.open("w",encoding="utf-8",newline="\n") as stream:
        stream.write("NAV_SG_PRECOLORED_CLOUD_V1\nscene_id %s\nsource_sha256 %s\nframe_id %d\nworld_frame %s\npoints %d\ndata\n"%
                     (quote(scene_id),source_sha,frame,quote(world_frame),count))
        for points,colors,valid in surfaces:
            for p,c in zip(points,colors):
                stream.write("%.17g %.17g %.17g %d %d %d %d\n"%(*p,int(c[0]),int(c[1]),int(c[2]),int(valid)))
    manifest = {"schema":"g2_prescan_manifest_v1","status":"COMPLETE" if complete else "PARTIAL_COLOR",
                "scene_id":scene_id,"source_sha256":source_sha,"visual_source_sha256":visual_sha,
                "source_identity":visual_identity,"sources":sources,"state":state,"frame_id":frame,
                "world_frame":world_frame,"bounds_min":bounds.min(axis=0).tolist(),
                "bounds_max":bounds.max(axis=0).tolist(),"point_count":count,"visual_geoms":records,
                "excluded":excluded,"native_geometry_binding":native_binding,
                "input_files":{name:{"path":str(Path(path).resolve()),"sha256":digest(path)}
                               for name,path in (("metadata",metadata),("ep_meta",ep_meta)) if path},
                "semantic_role":"SOURCE_PROVENANCE_ONLY_NOT_NATIVE_OBJECT_DETECTIONS",
                "appearance":"SOURCE_ASSET_ALBEDO_NOT_CAMERA_RGB","free_space":"NOT_INFERRED_FROM_COLOR_CLOUD",
                "file":{"path":"precolored.txt","bytes":cloud.stat().st_size,"sha256":digest(cloud)},
                "gates":{"object_perception":"REQUIRES_REAL_RGBD_POSE","declared_visual_geoms_complete":complete,
                         "full_scene_visual":"PENDING_SOURCE_ROLE_AND_VISUAL_REVIEW",
                         "private_layout_acceptance":"NOT_RUN"}}
    write_json(out/"manifest.json",manifest)
    if complete:
        (out/"COMPLETE").write_text("VISUAL_SURFACE_EXPORT_ONLY\n")
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mjcf",required=True);p.add_argument("--metadata",required=True)
    p.add_argument("--output",required=True);p.add_argument("--states");p.add_argument("--ep-meta")
    p.add_argument("--asset-root",action="append",default=[]);p.add_argument("--frame",type=int,default=0)
    p.add_argument("--spacing",type=float,default=.05);p.add_argument("--world-frame",default="map")
    p.add_argument("--state-format",choices=("qpos","mujoco_fullphysics"),default="qpos")
    p.add_argument("--native-manifest");p.add_argument("--allow-partial-color",action="store_true")
    args=p.parse_args()
    result=export(args.mjcf,args.metadata,args.output,states=args.states,frame=args.frame,
                  spacing=args.spacing,asset_roots=args.asset_root,ep_meta=args.ep_meta,
                  state_format=args.state_format,world_frame=args.world_frame,
                  native_manifest=args.native_manifest,allow_partial_color=args.allow_partial_color)
    print(result["status"],result["point_count"])


if __name__=="__main__":
    main()
