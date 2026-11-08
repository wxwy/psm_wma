"""MuJoCo visual surfaces -> simulator-independent XYZRGB transport.

This is a source adapter, not a robot camera or a semantic detection frontend.
Source labels remain provenance; no GT class is sent as normal perception.
"""
import argparse
import hashlib
from pathlib import Path
import re
import numpy as np
from g2.io import ContractError, canonical, digest, new_output, read_json, sha, write_json
from .source_geometry import (load_model, model_source_hash, apply_state,
                              primitive_mesh, surface_colors, effective_rgba)
from .surface_sampling import SamplingFailure, sample_surface, geometry_sha256


def pointer_tokens(path):
    if not isinstance(path, str) or (path and not path.startswith("/")):
        raise ContractError("expected RFC 6901 JSON Pointer")
    if path == "":
        return []
    tokens = path[1:].split("/")
    if any(re.search(r"~(?:[^01]|$)", token) for token in tokens):
        raise ContractError("invalid JSON Pointer escape")
    return [token.replace("~1", "/").replace("~0", "~") for token in tokens]


def pointer(document, path):
    current = document
    try:
        for key in pointer_tokens(path):
            if isinstance(current, list):
                if not re.fullmatch(r"0|[1-9][0-9]*", key):
                    raise ContractError("invalid JSON Pointer array index")
                current = current[int(key)]
            elif isinstance(current, dict):
                current = current[key]
            else:
                raise ContractError("JSON Pointer traverses a scalar")
    except ContractError:
        raise
    except (KeyError, IndexError, ValueError, TypeError) as error:
        raise ContractError("missing ep_meta record: " + path) from error
    return current


def source_text(value):
    return isinstance(value, str) and bool(value.strip()) and not any(ord(c) < 32 for c in value)


def source_binding(spec, name, ep_meta, *, body_names=None):
    if not isinstance(spec, dict) or spec.get("role") not in ("visual", "collision", "robot", "auxiliary"):
        raise ContractError("explicit valid geom role required")
    body = spec.get("source_body_name")
    if body is not None and (not source_text(body) or body_names is None or body not in body_names):
        raise ContractError("source body is absent from actual geom ancestry")
    body_binding = {"status":"VERIFIED", "body_name":body,
                    "basis":"DECLARED_BODY_MATCHES_COMPILED_GEOM_ANCESTRY"} if body is not None else {"status":"UNSPECIFIED"}
    if spec.get("source_kind") == "mjcf":
        official_fields = ("ep_meta_pointer", "source_instance_name", "source_collection",
                           "source_category", "source_category_field")
        if any(key in spec for key in official_fields):
            raise ContractError("MJCF source cannot replace official ep_meta assertions")
        if spec.get("geom_name") != name:
            raise ContractError("MJCF provenance must name the exact geom")
        return {"kind":"mjcf", "geom_name":name, "body_binding":body_binding}
    if spec.get("source_kind") != "ep_meta" or not isinstance(ep_meta, dict):
        raise ContractError("visual geom requires official ep_meta or exact MJCF provenance")
    tokens = pointer_tokens(spec.get("ep_meta_pointer"))
    instance = spec.get("source_instance_name")
    if len(tokens) != 2 or tokens[0] not in ("fixtures", "object_cfgs") or not source_text(instance):
        raise ContractError("official source requires a fixture entry or object_cfgs entry")
    collection = tokens[0]
    if spec.get("source_collection", collection) != collection or spec["role"] == "robot":
        raise ContractError("official fixture/object collection and role conflict")
    values = ep_meta.get(collection)
    if (collection == "fixtures" and not isinstance(values, dict)) or (collection == "object_cfgs" and not isinstance(values, list)):
        raise ContractError("official fixtures must be a dict and object_cfgs a list")
    record = pointer(ep_meta, spec["ep_meta_pointer"])
    if not isinstance(record, dict):
        raise ContractError("official source record must be an object")
    category_details = {}
    if collection == "fixtures":
        matches = tokens[1] == instance and record.get("name", instance) == instance
        field = spec.get("source_category_field", "cls")
        if field != "cls":
            raise ContractError("official fixture category must come from cls")
    else:
        matches = record.get("name") == instance and sum(
            isinstance(item, dict) and item.get("name") == instance for item in values) == 1
        info = record.get("info", {})
        if not isinstance(info, dict):
            raise ContractError("official object info must be an object")
        if "cat" in info:
            if not source_text(info["cat"]):
                raise ContractError("official object info.cat must be nonempty text")
            category_details["fine_category"] = {"field":"info.cat", "value":info["cat"]}
        if "type" in record:
            if not source_text(record["type"]):
                raise ContractError("official object coarse type must be nonempty text")
            category_details["coarse_type"] = {"field":"type", "value":record["type"]}
        field = spec.get("source_category_field")
        if field is None:
            field = next((key for key in ("obj_groups", "obj_type", "cls") if key in record), None)
            if field is None and "cat" in info:
                field = "info.cat"
        if field not in ("obj_groups", "obj_type", "cls", "info.cat"):
            raise ContractError("official object category provenance is missing")
    if not matches:
        raise ContractError("official fixture/object cfg identity mismatch")
    category = record.get("info", {}).get("cat") if field == "info.cat" else record.get(field)
    valid_category = source_text(category) or (field == "obj_groups" and isinstance(category, list)
                                              and bool(category) and all(source_text(v) for v in category))
    if not valid_category or ("source_category" in spec and spec["source_category"] != category):
        raise ContractError("official fixture/object category mismatch or malformed source")
    return {"kind":"ep_meta", "pointer":spec["ep_meta_pointer"], "collection":collection,
            "instance_name":instance, "category":{"field":field,"value":category},
            "record":record, "body_binding":body_binding, **category_details}


def compiled_geom_row(model, data, g, name, geometry_types):
    import mujoco
    ancestry = []
    body = int(model.geom_bodyid[g])
    while True:
        ancestry.append({"body_id":body, "body_name":mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_BODY, body)})
        if body == 0:
            break
        body = int(model.body_parentid[body])
    mat = int(model.geom_matid[g])
    return {"geom_id":g, "geom_name":name,
            "body_ancestry":ancestry, "geometry_type":geometry_types.get(int(model.geom_type[g]), "unsupported"),
            "geometry_data_id":int(model.geom_dataid[g]), "geom_size":model.geom_size[g].astype(float).tolist(),
            "world_position":data.geom_xpos[g].tolist(), "world_rotation":data.geom_xmat[g].tolist(),
            "group":int(model.geom_group[g]), "contype":int(model.geom_contype[g]),
            "conaffinity":int(model.geom_conaffinity[g]), "material_id":mat,
            "material_name":mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_MATERIAL, mat) if mat >= 0 else None,
            "compiled_rgba":model.geom_rgba[g].astype(float).tolist(),
            "effective_rgba":effective_rgba(model,g).tolist()}


def geom_audit_row(model, data, g, name, spec, geometry_types, ep_meta):
    row = compiled_geom_row(model, data, g, name, geometry_types)
    binding = source_binding(spec, name, ep_meta,
                             body_names=[b["body_name"] for b in row["body_ancestry"]
                                         if spec.get("source_kind")=="mjcf" or b["body_id"]!=0])
    return dict(row, role=spec["role"], source=binding,
                classification_reason=spec.get("classification_reason"), color_status="NOT_SAMPLED")


def adapter_source_sha256():
    return hashlib.sha256(b"".join(Path(__file__).with_name(name).read_bytes() for name in
        ("prescan.py", "source_geometry.py", "source_scope.py", "surface_sampling.py"))).hexdigest()


def geom_surface_mesh(model, g, kind):
    if kind == "mesh":
        mid = int(model.geom_dataid[g])
        va,vn,fa,fn = [int(getattr(model,k)[mid]) for k in
                       ("mesh_vertadr","mesh_vertnum","mesh_faceadr","mesh_facenum")]
        return model.mesh_vert[va:va+vn].copy(), model.mesh_face[fa:fa+fn].copy()
    return primitive_mesh(kind, model.geom_size[g].copy())


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
    surfaces, records, excluded, audit = [], [], [], []
    count = 0
    for g, name in enumerate(names):
        spec = meta["geoms"][name]
        if not isinstance(spec,dict):raise ContractError("geom role record must be an object")
        role = spec.get("role")
        if role not in ("visual","collision","robot","auxiliary"):
            raise ContractError("invalid or absent geom role")
        row = geom_audit_row(model, data, g, name, spec, geometry_types, ep)
        audit.append(row)
        binding = row["source"]
        if role != "visual" or effective_rgba(model,g)[3] <= 0:
            row["color_status"] = "TRANSPARENT" if role == "visual" else "EXCLUDED_" + role.upper()
            row["surface_points"] = 0
            excluded.append({"geom_name":name,"role":role,"reason":"explicit_role_or_transparency","source":binding})
            continue
        kind = geometry_types.get(int(model.geom_type[g]))
        if kind is None:
            raise ContractError("finite visual surface required; infinite plane/hfield is unsupported")
        vertices,faces = geom_surface_mesh(model, g, kind)
        try:
            points,face_ids,weights,sampling = sample_surface(vertices,faces,spacing,max_points-count,with_audit=True)
        except SamplingFailure as error:
            row.update(sampling=error.audit, surface_points=0, color_status="NOT_SAMPLED_GEOMETRY_REJECTED")
            out.mkdir(parents=True)
            write_json(out/"sampling_failure.json", {
                "schema":"g2_prescan_sampling_failure_v1", "status":"REJECTED", "training_ready":False,
                "scene_id":scene_id, "frame_id":frame, "world_frame":world_frame, "state":state,
                "model_source_sha256":closure, "sources":sources,
                "adapter_source_sha256":adapter_source_sha256(),
                "metadata_sha256":digest(metadata), "ep_meta_sha256":digest(ep_meta) if ep_meta else None,
                "spacing_m":spacing, "max_points":max_points, "previous_geom_point_count":count,
                "geom_id":g, "geom_name":name, "sampling":error.audit,
                "geom_audit_prefix":audit, "compiled_geom_count":int(model.ngeom),
                "audit_scope":"PREFIX_THROUGH_REJECTED_GEOM_NOT_COMPLETE_INVENTORY",
                "cloud_written":False, "full_scene_source_certified":False, "reason":str(error)})
            raise
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
        row.update(surface_points=len(world), color_status="VALID" if valid else "UNSUPPORTED_APPEARANCE",
                   appearance=appearance, sampling=sampling)
        count += len(world)
        records.append({"geom_id":g,"geom_name":name,"role":"visual","source":binding,
                        "surface_points":len(world),"color_valid":bool(valid),"appearance":appearance,
                        "sampling":sampling, "local_geometry_sha256":geometry_sha256(vertices,faces)})
    if not count:
        raise ContractError("no visual surface samples")
    complete = all(item[2] for item in surfaces)
    if not complete and not allow_partial_color:
        raise ContractError("unsupported texture projection; partial export requires --allow-partial-color")
    adapter_sha=adapter_source_sha256()
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
    from .source_scope import audit_summary
    summary = audit_summary(audit)
    manifest = {"schema":"g2_prescan_manifest_v1","status":"COMPLETE" if complete else "PARTIAL_COLOR",
                "completion_scope":"DECLARED_VISUAL_GEOMS_ONLY", "training_ready":False,
                "compiled_geom_count":int(model.ngeom), "geom_audit":audit,
                "geom_audit_sha256":hashlib.sha256(canonical(audit)).hexdigest(), "source_audit":summary,
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
                         "full_scene_source_certified":False,
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
