"""Small per-episode visual-Geom source roster for F27 (no dense TXT cache).

F27 casts ORIGINAL compiled Visual Mesh with material/UV sampling. Its per-geom
membership list must be source-bound, but generating tens of millions of dense
ASCII points first is redundant. The optional F24 10mm map still maintains its
own independent native source, constructed on demand.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.io import ContractError, digest, read_json, write_json
from g2.sim.source_geometry import load_model, model_source_hash, effective_rgba
from g2.sim.prescan import geom_surface_mesh, geometry_type_names

SCHEMA="g2_source_visual_geom_roster_without_dense_point_cache_v1"


def build(gt_manifest,role_map,output,*,asset_roots=None):
    import mujoco
    gt_manifest=Path(gt_manifest).resolve(strict=True)
    role_map=Path(role_map).resolve(strict=True)
    out=Path(output)
    if out.exists() or out.is_symlink():
        raise ContractError("visual roster output already exists")
    gt=read_json(gt_manifest)
    roles=read_json(role_map)
    if (gt.get("schema")!="nav_sg_mujoco_oracle_v1"
            or roles.get("schema")!="g2_sim_prescan_v1"
            or roles.get("scene_id")!=gt["scene_id"]):
        raise ContractError("visual roster requires matching actual GT source and role map")
    records=gt["sources"]
    root=next(x["path"] for x in records if x["logical_id"]=="root.xml")
    roots=asset_roots or sorted({str(Path(x["path"]).parent) for x in records})
    model,loaded=load_model(root,roots)
    if model_source_hash(loaded)!=gt["source_identity"]["model_source_sha256"]:
        raise ContractError("compiled material/mesh source hash differs")
    kinds=geometry_type_names()
    rows=[]
    for g in range(model.ngeom):
        name=mujoco.mj_id2name(model,mujoco.mjtObj.mjOBJ_GEOM,g) or f"geom_{g}"
        role=roles["geoms"].get(name)
        if not isinstance(role,dict) or role.get("role") not in (
                "visual","collision","robot","auxiliary"):
            raise ContractError("source geom role missing: "+name)
        if role["role"]!="visual" or float(effective_rgba(model,g)[3])<=0:
            continue
        kind=kinds.get(int(model.geom_type[g]))
        if kind not in ("box","sphere","ellipsoid","capsule","cylinder","mesh"):
            raise ContractError("unsupported visual source geometry "+name)
        vertices,faces=geom_surface_mesh(model,g,kind)
        if not len(vertices) or not len(faces):
            raise ContractError("empty visual source geometry "+name)
        rows.append({
            "geom_id":g,"geom_name":name,
            "source_instance":[role.get("source_kind"),role.get("source_instance_name")],
            # The F27 source registry uses true faces/materials. No synthetic
            # sampled-point counters may be claimed as real data.
            "points":0,"valid_color_points":0,
            "source_triangles":len(faces),
            "source_geometry_kind":kind,
        })
    if not rows:
        raise ContractError("no visual geom available for material source F27")
    out.mkdir(parents=True)
    manifest={
        "schema":SCHEMA,"source_mode":"compiled_visual_geometry_no_surfel_cache",
        "scene_id":gt["scene_id"],
        "source_sha256":gt["source_sha256"],
        "model_source_sha256":gt["source_identity"]["model_source_sha256"],
        "native_gt_manifest":{"path":str(gt_manifest),"sha256":digest(gt_manifest)},
        "visual_role_map":{"path":str(role_map),"sha256":digest(role_map)},
        "sampled_geoms":rows,
        "no_dense_point_cache_created":True,
        "source_mesh_material_sampled_at_render_time":True,
        "training_ready":False,
    }
    write_json(out/"dense_manifest.json",manifest)
    return manifest


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--gt-manifest",required=True)
    p.add_argument("--role-map",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args(argv)
    result=build(a.gt_manifest,a.role_map,a.output)
    print(json.dumps({"scene_id":result["scene_id"],
        "visual_geoms":len(result["sampled_geoms"]),
        "dense_txt_generated":False},sort_keys=True),flush=True)


if __name__=="__main__":
    main()
