"""Read-only MJCF/state and visual appearance helpers for G2 pre-scans.

Source loading, primitives and UV sampling derive from nav_sg PR #7 e86c384.
G2 owns MuJoCo; native consumers receive only simulator-independent transports.
"""
import hashlib
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from g2.io import ContractError


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(payload):
    return hashlib.sha256(payload).hexdigest()


def model_source_hash(sources):
    """Portable complete XML/asset closure identity, independent of mountpoint."""
    return digest(canonical(sorted(({k:r[k] for k in ("logical_id","sha256","bytes")} for r in sources),key=lambda r:r["logical_id"])))


def xml_payload(path):
    raw=Path(path).read_bytes()
    if len(raw)>32*1024*1024:
        raise ContractError("MJCF exceeds 32 MiB")
    if str(path).endswith(".gz"):
        with gzip.open(path,"rb") as stream:
            raw=stream.read(32*1024*1024+1)
        if len(raw)>32*1024*1024:
            raise ContractError("expanded MJCF exceeds 32 MiB")
    return raw


def load_model(mjcf, asset_roots=()):
    """Resolve and hash the complete XML/asset closure before compiling a VFS.

    All file references are rewritten into a private MuJoCo VFS. No source files
    are edited, and files outside the explicitly supplied roots are rejected.
    """
    import mujoco
    mjcf = Path(mjcf).resolve(strict=True)
    roots = [mjcf.parent] + [Path(p).resolve(strict=True) for p in asset_roots]
    source_records, assets, names, active = {}, {}, {}, set()
    try:
        root = ET.fromstring(xml_payload(mjcf))
    except (OSError, ET.ParseError) as exc:
        raise ContractError("invalid MJCF: " + str(exc)) from exc
    compiler = root.find("compiler")
    dirs = {k: (compiler.get(k, "") if compiler is not None else "")
            for k in ("assetdir", "meshdir", "texturedir")}

    def resolve(ref, parent, tag):
        target = Path(ref)
        candidates = []
        if target.is_absolute():
            candidates = [target]
        else:
            specific = dirs["meshdir" if tag == "mesh" else "texturedir"] if tag in ("mesh", "texture") else ""
            prefix = specific or (dirs["assetdir"] if tag != "include" else "")
            candidates = [mjcf.parent / prefix / target, parent / target]
            candidates.extend(p / target for p in roots)
        existing = {p.resolve() for p in candidates if p.is_file()}
        if len(existing) != 1:
            raise ContractError("missing/ambiguous asset reference: " + ref)
        path = existing.pop()
        if not any(path == r or r in path.parents for r in roots):
            raise ContractError("asset escapes approved roots: " + str(path))
        return path

    def xml(path):
        if path in active:
            raise ContractError("cyclic MJCF include")
        active.add(path)
        raw = path.read_bytes()
        source_records[str(path)] = {"logical_id":names.get(path,"root.xml"),"path": str(path),
            "sha256": digest(raw), "bytes": len(raw),"source_kind":"mjcf_xml","includes":[]}
        try:
            doc = ET.fromstring(xml_payload(path))
        except ET.ParseError as exc:
            raise ContractError("invalid XML include") from exc
        for node in doc.iter():
            if node.tag == "compiler":
                for key in ("assetdir", "meshdir", "texturedir"):
                    node.attrib.pop(key, None)
            if "file" not in node.attrib:
                continue
            reference=node.get("file")
            resolved = resolve(reference, path.parent, node.tag)
            if resolved not in names:
                names[resolved] = "asset_%06d%s" % (len(names), resolved.suffix)
            alias = names[resolved]
            node.set("file", alias)
            if node.tag == "include":
                source_records[str(path)]["includes"].append({"reference":reference,"logical_id":alias})
                assets[alias] = xml(resolved)
            else:
                payload = resolved.read_bytes()
                source_records[str(resolved)] = {"logical_id":alias,"path": str(resolved),
                    "sha256": digest(payload), "bytes": len(payload),"source_kind":"asset"}
                assets[alias] = payload
        active.remove(path)
        return ET.tostring(doc, encoding="utf-8")

    rewritten = xml(mjcf)
    try:
        model = mujoco.MjModel.from_xml_string(rewritten.decode(), assets=assets)
    except ValueError as exc:
        raise ContractError("MuJoCo compile failed: " + str(exc)) from exc
    # Source paths remain provenance only; identity does not depend on mountpoint.
    records = sorted(source_records.values(), key=lambda item: item["logical_id"])
    return model, records


def apply_state(model, states=None, frame=0, state_format="qpos"):
    import mujoco
    if type(frame) is not int or frame < 0:
        raise ContractError("frame must be nonnegative integer")
    data = mujoco.MjData(model)
    record = {"frame_id": frame, "format": "mjcf_default", "timestamp": float(data.time),"timestamp_source":"mjcf_default"}
    if states is None:
        if frame != 0:
            raise ContractError("nonzero frame requires states")
    else:
        path = Path(states).resolve(strict=True)
        key = "qpos" if state_format == "qpos" else "states"
        with np.load(path, allow_pickle=False) as archive:
            if key not in archive:
                raise ContractError("states missing array: " + key)
            rows = archive[key]
            expected = model.nq if state_format == "qpos" else mujoco.mj_stateSize(model, mujoco.mjtState.mjSTATE_FULLPHYSICS)
            if (rows.ndim != 2 or rows.shape[1] != expected or frame >= rows.shape[0]
                    or rows.dtype.kind != "f" or not np.isfinite(rows[frame]).all()):
                raise ContractError("state shape/dtype/frame/nonfinite mismatch")
            row = np.asarray(rows[frame], dtype=np.float64)
            if state_format == "qpos":
                data.qpos[:] = row
                timestamp_source = "missing"
                if "time" in archive:
                    times = archive["time"]
                    if times.shape != (len(rows),) or not np.isfinite(times[frame]):
                        raise ContractError("invalid state time")
                    data.time = float(times[frame])
                    timestamp_source = "archive_time"
            elif state_format == "mujoco_fullphysics":
                mujoco.mj_setState(model, data, row, mujoco.mjtState.mjSTATE_FULLPHYSICS)
                timestamp_source = "mujoco_fullphysics"
            else:
                raise ContractError("unsupported state format")
        record = {"frame_id": frame, "format": state_format,"path":str(path), "file_sha256": digest(path.read_bytes()),
                  "row_sha256": digest(row.astype("<f8").tobytes()), "timestamp": float(data.time) if timestamp_source != "missing" else None,
                  "timestamp_source":timestamp_source}
    for joint in range(model.njnt):
        kind, address = int(model.jnt_type[joint]), int(model.jnt_qposadr[joint])
        if kind in (int(mujoco.mjtJoint.mjJNT_FREE),int(mujoco.mjtJoint.mjJNT_BALL)):
            address += 3 if kind == int(mujoco.mjtJoint.mjJNT_FREE) else 0
            if not np.isclose(np.linalg.norm(data.qpos[address:address+4]),1,rtol=0,atol=1e-6):
                raise ContractError("state quaternion must have unit norm")
    mujoco.mj_forward(model, data)
    if not np.isfinite(data.geom_xpos).all() or not np.isfinite(data.geom_xmat).all():
        raise ContractError("nonfinite kinematics")
    return data, record


def primitive_mesh(kind, size, rings=12, segments=24):
    if kind == "box":
        vertices = np.asarray([[x,y,z] for x in (-1,1) for y in (-1,1) for z in (-1,1)], float)*size
        faces = np.asarray([[0,1,3],[0,3,2],[4,6,7],[4,7,5],[0,4,5],[0,5,1],
                            [2,3,7],[2,7,6],[0,2,6],[0,6,4],[1,5,7],[1,7,3]])
        return vertices, faces
    if kind == "cylinder":
        vertices = [[0,0,-size[1]],[0,0,size[1]]]
        for z in (-size[1],size[1]):
            vertices += [[size[0]*np.cos(a),size[0]*np.sin(a),z] for a in np.arange(segments)*2*np.pi/segments]
        faces = []
        for i in range(segments):
            a,b,c,d = 2+i,2+(i+1)%segments,2+segments+i,2+segments+(i+1)%segments
            faces += [[0,b,a],[1,c,d],[a,b,d],[a,d,c]]
        return np.asarray(vertices), np.asarray(faces)
    if kind not in ("sphere", "ellipsoid", "capsule"):
        raise ContractError("unsupported primitive: " + kind)
    scale = size if kind == "ellipsoid" else np.repeat(size[0],3)
    height = size[1] if kind == "capsule" else 0
    vertices = [[0,0,-scale[2]-height],[0,0,scale[2]+height]]
    if kind == "capsule":
        half=max(2,rings//2)
        lat_rows=[(lat,-1) for lat in np.linspace(-np.pi/2,0,half+1)[1:]]
        lat_rows += [(lat,1) for lat in np.linspace(0,np.pi/2,half+1)[:-1]]
    else:
        lat_rows=[(lat,0) for lat in np.linspace(-np.pi/2,np.pi/2,rings+1)[1:-1]]
    for lat,side in lat_rows:
        for a in np.arange(segments)*2*np.pi/segments:
            point=np.asarray([np.cos(lat)*np.cos(a),np.cos(lat)*np.sin(a),np.sin(lat)])*scale
            point[2]+=side*height
            vertices.append(point)
    rows=len(lat_rows)
    faces=[]
    for i in range(segments):
        faces += [[0,2+(i+1)%segments,2+i],
                  [1,2+(rows-1)*segments+i,2+(rows-1)*segments+(i+1)%segments]]
    for row in range(rows-1):
        for i in range(segments):
            a,b=2+row*segments+i,2+row*segments+(i+1)%segments
            c,d=a+segments,b+segments
            faces += [[a,b,d],[a,d,c]]
    return np.asarray(vertices), np.asarray(faces)


def effective_rgba(model,g):
    """MuJoCo material color applies unless geom RGBA overrides its default."""
    rgba=model.geom_rgba[g].astype(float)
    material=int(model.geom_matid[g])
    if material >= 0 and np.array_equal(rgba,[.5,.5,.5,1.]):
        rgba=model.mat_rgba[material].astype(float)
    return rgba


def _legacy_surface_colors(model,g,kind,face_ids,weights):
    """Asset albedo only, with explicit invalid flags for unsupported projection.

    MuJoCo compiled 2D mesh UVs and repeat/bilinear filtering are supported.
    Procedural primitive/cube projections remain incomplete rather than silently
    assigning constant geom color to a textured surface.
    """
    import mujoco
    rgba=np.repeat(effective_rgba(model,g)[None,:],len(face_ids),axis=0)
    mat=int(model.geom_matid[g])
    if mat < 0:
        return rgba,True,{"mode":"geom_rgba_asset_albedo","texture_sampled":False}
    texture_ids=model.mat_texid[mat]
    rgb=int(texture_ids[int(mujoco.mjtTextureRole.mjTEXROLE_RGB)])
    full=int(texture_ids[int(mujoco.mjtTextureRole.mjTEXROLE_RGBA)])
    texture=full if full >= 0 else rgb
    if texture < 0:
        return rgba,True,{"mode":"constant_asset_albedo","texture_sampled":False}
    unsupported={"mode":"UNSUPPORTED_TEXTURE_PROJECTION","texture_id":texture,"texture_sampled":False}
    if kind != "mesh" or int(model.tex_type[texture]) != int(mujoco.mjtTexture.mjTEXTURE_2D) or bool(model.mat_texuniform[mat]):
        return rgba,False,unsupported
    if int(texture_ids[int(mujoco.mjtTextureRole.mjTEXROLE_OPACITY)]) >= 0:
        return rgba,False,dict(unsupported,reason="separate opacity texture")
    mid=int(model.geom_dataid[g]); face_start=int(model.mesh_faceadr[mid])
    uv_faces=model.mesh_facetexcoord[face_start:face_start+int(model.mesh_facenum[mid])]
    if np.any(uv_faces < 0):
        return rgba,False,dict(unsupported,reason="missing mesh UV coordinates")
    uv_start,uv_count=int(model.mesh_texcoordadr[mid]),int(model.mesh_texcoordnum[mid])
    uv_values=model.mesh_texcoord[uv_start:uv_start+uv_count]
    if not len(uv_values) or np.max(uv_faces) >= len(uv_values):
        return rgba,False,dict(unsupported,reason="invalid mesh UV coordinates")
    uv=np.einsum("bi,bij->bj",weights,uv_values[uv_faces[face_ids]])*model.mat_texrepeat[mat]
    width,height,channels=[int(getattr(model,key)[texture]) for key in ("tex_width","tex_height","tex_nchannel")]
    if channels not in (3,4):
        return rgba,False,dict(unsupported,reason="unsupported channel count")
    address=int(model.tex_adr[texture])
    pixels=model.tex_data[address:address+width*height*channels].reshape(height,width,channels).astype(float)/255
    # OpenGL repeat + bilinear texture coordinates, with compiled upload row order.
    xy=(uv%1)*[width,height]-.5
    lower=np.floor(xy).astype(np.int64); fraction=xy-lower
    colors=np.zeros((len(uv),channels))
    for dx,dy in ((0,0),(1,0),(0,1),(1,1)):
        weight=(fraction[:,0] if dx else 1-fraction[:,0])*(fraction[:,1] if dy else 1-fraction[:,1])
        colors+=pixels[(lower[:,1]+dy)%height,(lower[:,0]+dx)%width]*weight[:,None]
    rgba[:,:3]*=colors[:,:3]
    if channels == 4:
        rgba[:,3]*=colors[:,3]
    return rgba,True,{"mode":"mesh_uv_bilinear_asset_albedo","texture_id":texture,"texture_sampled":True,
                      "filter":"repeat_bilinear","texrepeat":model.mat_texrepeat[mat].tolist(),"camera_observation":False}


def surface_colors(model, g, kind, face_ids, weights, *, local_points=None, with_diagnostics=False):
    """Legacy mesh UVs plus pinned primitive projection and per-point validity."""
    import mujoco
    from .texture_projection import primitive_colors
    mat = int(model.geom_matid[g])
    textured = mat >= 0 and (int(model.mat_texid[mat, int(mujoco.mjtTextureRole.mjTEXROLE_RGB)]) >= 0
                             or int(model.mat_texid[mat, int(mujoco.mjtTextureRole.mjTEXROLE_RGBA)]) >= 0)
    if kind != "mesh" and textured:
        rgba = np.repeat(effective_rgba(model, g)[None], len(face_ids), axis=0)
        rgba, valid, appearance, reasons = primitive_colors(model, g, kind, local_points, len(face_ids), rgba)
    else:
        rgba, ok, appearance = _legacy_surface_colors(model, g, kind, face_ids, weights)
        valid = np.full(len(face_ids), bool(ok)); reasons = np.where(valid, 0, 1).astype(np.uint8)
        if kind=="mesh" and mat>=0 and int(model.mat_texid[mat,int(mujoco.mjtTextureRole.mjTEXROLE_RGBA)])>=0:
            valid[:]=False;reasons[:]=1
            rgba[:,:3]=0
            appearance=dict(appearance,mode="UNSUPPORTED_TEXTURE_PROJECTION",texture_sampled=False,
                            reason="RGBA mesh layer not verified by legacy UV path")
    translucent = rgba[:, 3] < 1 - 1e-7
    if np.any(translucent):
        valid[translucent] = False; reasons[translucent] = 3
        appearance = dict(appearance, unsupported="translucent_surface_requires_alpha_transport")
    if with_diagnostics:
        return rgba, valid, appearance, reasons
    return rgba, bool(np.all(valid)) if kind == "mesh" or not textured else valid, appearance
