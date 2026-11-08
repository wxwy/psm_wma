"""Server-local all-geom source preflight; no cloud, auto roles or certification.

Use an optional, possibly incomplete prescan role map. Missing/invalid entries
remain visible for review, while unsupported geometry does not truncate the
inventory. A single material probe is explicitly not surface color coverage.
"""
import argparse
from collections import Counter
import hashlib
from pathlib import Path

import numpy as np

from g2.io import ContractError, canonical, digest, new_output, read_json, write_json
from .prescan import (adapter_source_sha256, compiled_geom_row, geom_surface_mesh,
                      quote, source_binding, source_text)
from .source_geometry import apply_state, load_model, model_source_hash, surface_colors
from .surface_sampling import audit_surface


def _material(model, g):
    import mujoco
    mat = int(model.geom_matid[g])
    if mat < 0:
        return {"texture_bindings": [], "mode": "GEOM_RGBA"}
    roles = {int(role): name for name, role in mujoco.mjtTextureRole.__members__.items()}
    textures = []
    for role, texture in enumerate(model.mat_texid[mat]):
        texture = int(texture)
        if texture < 0:
            continue
        width, height, channels, address = [int(getattr(model, key)[texture])
            for key in ("tex_width", "tex_height", "tex_nchannel", "tex_adr")]
        pixels = model.tex_data[address:address + width * height * channels]
        textures.append({"role_id": role, "role_name": roles.get(role), "texture_id": texture,
            "texture_name": mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_TEXTURE, texture),
            "type_id": int(model.tex_type[texture]), "width": width, "height": height,
            "channels": channels, "compiled_pixels_sha256": hashlib.sha256(pixels.tobytes()).hexdigest()})
    return {"mode": "MATERIAL", "rgba": model.mat_rgba[mat].astype(float).tolist(),
            "texuniform": bool(model.mat_texuniform[mat]), "texrepeat": model.mat_texrepeat[mat].tolist(),
            "texture_bindings": textures}


def inventory(mjcf, output, *, metadata=None, scene_id=None, ep_meta=None,
              states=None, frame=0, state_format="qpos", asset_roots=(), world_frame="map"):
    """Inspect complete compiled geometry at one restored state, read-only."""
    import mujoco
    mjcf = Path(mjcf).resolve(strict=True)
    paths = [Path(p).resolve(strict=True) for p in (metadata, ep_meta, states) if p]
    out = new_output(output, [mjcf.parent, *asset_roots, *paths])
    meta = read_json(metadata) if metadata else {"schema": "g2_sim_prescan_v1", "scene_id": scene_id, "geoms": {}}
    if meta.get("schema") != "g2_sim_prescan_v1" or not isinstance(meta.get("geoms"), dict):
        raise ContractError("expected possibly incomplete g2_sim_prescan_v1 role map")
    if scene_id is not None and scene_id != meta.get("scene_id"):
        raise ContractError("scene id conflicts with metadata")
    scene_id = meta.get("scene_id")
    quote(scene_id); quote(world_frame)
    ep = read_json(ep_meta) if ep_meta else None
    model, sources = load_model(mjcf, asset_roots)
    closure = model_source_hash(sources)
    if states and meta.get("state_source") != {"model_source_sha256": closure, "states_sha256": digest(states)}:
        raise ContractError("state_source must bind full model closure and states archive")
    data, state = apply_state(model, states, frame, state_format)
    names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_GEOM, g) or "geom_%d" % g for g in range(model.ngeom)]
    if len(set(names)) != len(names):
        raise ContractError("compiled geom names are not unique")
    if set(meta["geoms"]) - set(names):
        raise ContractError("role map includes unknown geom names")
    kinds = {int(getattr(mujoco.mjtGeom, "mjGEOM_" + kind.upper())): kind
             for kind in ("box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh", "plane", "hfield")}
    supported = {"box", "sphere", "ellipsoid", "capsule", "cylinder", "mesh"}
    rows, template, blockers = [], {}, []
    for g, name in enumerate(names):
        row = compiled_geom_row(model, data, g, name, kinds)
        spec = meta["geoms"].get(name)
        row.update(role="UNCLASSIFIED", declaration_status="MISSING", source=None,
                   classification_reason=None, material=_material(model, g))
        template[name] = {"role": None, "source_kind": None, "geom_name": name, "classification_reason": None}
        if spec is not None:
            try:
                binding = source_binding(spec, name, ep, body_names=[b["body_name"] for b in row["body_ancestry"]
                    if isinstance(spec, dict) and (spec.get("source_kind") == "mjcf" or b["body_id"] != 0)])
                row.update(role=spec["role"], declaration_status="DECLARED", source=binding,
                           classification_reason=spec.get("classification_reason"))
                template[name] = spec
                if not source_text(spec.get("classification_reason")):
                    blockers.append({"geom_id": g, "reason": "MISSING_CLASSIFICATION_REASON"})
                if binding["kind"] == "ep_meta" and binding["body_binding"]["status"] != "VERIFIED":
                    blockers.append({"geom_id": g, "reason": "OFFICIAL_SOURCE_BODY_UNVERIFIED"})
            except ContractError as error:
                row.update(declaration_status="INVALID", declaration_error=str(error), rejected_declaration=spec)
        if row["declaration_status"] != "DECLARED":
            blockers.append({"geom_id": g, "reason": row["declaration_status"] + "_ROLE_DECLARATION"})
        kind = row["geometry_type"]
        row["material_probe"] = {"status": "NOT_RUN", "basis": "ONE_RETAINED_FACE_CENTROID_ONLY",
                                 "surface_color_coverage_measured": False}
        if kind not in supported:
            row["geometry_status"] = "UNSUPPORTED_FINITE_SURFACE"
        else:
            try:
                vertices, faces = geom_surface_mesh(model, g, kind)
                sampling = audit_surface(vertices, faces)
                row.update(geometry_status=sampling["status"], sampling=sampling)
                if sampling["status"] != "REJECTED":
                    discarded = set(sampling["discarded_zero_area_face_ids"])
                    face_id = next(i for i in range(len(faces)) if i not in discarded)
                    colors, valid, appearance = surface_colors(model, g, kind, np.asarray([face_id]),
                                                               np.asarray([[1 / 3, 1 / 3, 1 / 3]]))
                    opaque = bool(np.all(colors[:, 3] >= 1 - 1e-7))
                    row["material_probe"].update(status="PROBE_VALID" if valid and opaque else "UNSUPPORTED_OR_TRANSLUCENT",
                        original_face_id=face_id, appearance=appearance, rgba=colors[0].tolist())
            except ContractError as error:
                row.update(geometry_status="REJECTED", geometry_error=str(error))
        if row["role"] == "visual" and row["effective_rgba"][3] > 0:
            if row["geometry_status"] != "GEOMETRY_VALID":
                blockers.append({"geom_id": g, "reason": "VISUAL_GEOMETRY_" + row["geometry_status"]})
            if row["material_probe"]["status"] != "PROBE_VALID":
                blockers.append({"geom_id": g, "reason": "VISUAL_MATERIAL_PROBE_" + row["material_probe"]["status"]})
        rows.append(row)
    identity = {"adapter_source_sha256": adapter_source_sha256(),
                "inventory_source_sha256": digest(Path(__file__)), "model_source_sha256": closure,
                "metadata": meta, "ep_meta": ep, "mujoco_version": mujoco.__version__}
    summary = {"compiled_geom_count": len(rows),
        "role_counts": dict(Counter(row["role"] for row in rows)),
        "declaration_status_counts": dict(Counter(row["declaration_status"] for row in rows)),
        "geometry_status_counts": dict(Counter(row["geometry_status"] for row in rows)),
        "material_probe_status_counts": dict(Counter(row["material_probe"]["status"] for row in rows)),
        "discarded_zero_area_face_count": sum(row.get("sampling", {}).get("discarded_zero_area_face_count", 0) for row in rows),
        "preflight_blockers": blockers, "surface_color_coverage_measured": False,
        "source_roles_independently_reviewed": False, "full_scene_source_certified": False}
    result = {"schema": "g2_sim_asset_inventory_v1", "status": "AUDIT_ONLY", "training_ready": False,
        "scene_id": scene_id, "world_frame": world_frame, "frame_id": frame, "state": state,
        "source_identity": identity, "source_identity_sha256": hashlib.sha256(canonical(identity)).hexdigest(),
        "sources": sources, "geom_audit": rows, "geom_audit_sha256": hashlib.sha256(canonical(rows)).hexdigest(),
        "summary": summary, "point_cloud_created": False, "completion_scope": "NONE_AUDIT_ONLY",
        "semantic_role": "SOURCE_PROVENANCE_ONLY_NOT_NATIVE_OBJECT_DETECTIONS",
        "input_files": {name: {"path": str(Path(path).resolve()), "sha256": digest(path)}
                        for name, path in (("metadata", metadata), ("ep_meta", ep_meta)) if path}}
    role_template = {"schema": "g2_sim_prescan_v1", "scene_id": scene_id, "geoms": template}
    if "state_source" in meta:
        role_template["state_source"] = meta["state_source"]
    out.mkdir(parents=True)
    write_json(out / "inventory.json", result)
    write_json(out / "roles_template.json", role_template)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mjcf", required=True); parser.add_argument("--output", required=True)
    parser.add_argument("--metadata"); parser.add_argument("--scene-id"); parser.add_argument("--ep-meta")
    parser.add_argument("--states"); parser.add_argument("--frame", type=int, default=0)
    parser.add_argument("--state-format", choices=("qpos", "mujoco_fullphysics"), default="qpos")
    parser.add_argument("--asset-root", action="append", default=[]); parser.add_argument("--world-frame", default="map")
    args = parser.parse_args()
    result = inventory(args.mjcf, args.output, metadata=args.metadata, scene_id=args.scene_id,
        ep_meta=args.ep_meta, states=args.states, frame=args.frame, state_format=args.state_format,
        asset_roots=args.asset_root, world_frame=args.world_frame)
    print(result["status"], result["summary"]["compiled_geom_count"])


if __name__ == "__main__":
    main()
