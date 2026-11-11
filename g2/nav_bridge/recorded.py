"""Prepare an auditable real RGB-D replay plan; never run a model or simulation."""
import argparse
import hashlib
from pathlib import Path
import shlex
from g2.io import ContractError, canonical, digest, new_output, read_json, sha, verified_file, write_json
from g2.sim.source_scope import SUBSET_SCOPE, verify_full_scene_review


def prepare(prescan_manifest, grid, *, nav_repo, dataset_root, episode, camera,
            sidecar, output, native_python="python3", min_z=.15,max_z=1.8,frames=201,
            full_scene_review=None, allow_declared_subset=False, allow_partial_color=False,
            native_structures=False, room_source="gvd",model_rebinding_proof=None):
    import math
    if any(type(flag) is not bool for flag in (allow_partial_color,allow_declared_subset,native_structures)):
        raise ContractError("replay opt-in flags must be booleans")
    manifest_path=Path(prescan_manifest).resolve()
    m=read_json(manifest_path)
    partial=m.get("status")=="PARTIAL_COLOR"
    if (m.get("schema")!="g2_prescan_manifest_v1" or m.get("status") not in ("COMPLETE","PARTIAL_COLOR") or
            type(m.get("frame_id")) is not int or m["frame_id"]!=0):
        raise ContractError("recorded replay requires a complete frame0 surface export")
    if partial and (not allow_partial_color or not allow_declared_subset or full_scene_review is not None):
        raise ContractError("PARTIAL_COLOR requires explicit diagnostic subset opt-in and cannot claim full-scene review")
    if m.get("world_frame")!="world":
        raise ContractError("recorded RGB-D uses world frame; re-export the source with --world-frame world")
    marker=manifest_path.parent/"COMPLETE"
    if partial:
        from g2.sim.source_scope import audit_summary, DECLARED_SCOPE
        rows=m.get('geom_audit',[])
        if (not isinstance(rows,list) or not rows or type(m.get('compiled_geom_count')) is not int or
                len(rows)!=m['compiled_geom_count'] or any(not isinstance(row,dict) or
                    type(row.get('geom_id')) is not int or not isinstance(row.get('geom_name'),str) or
                    not row['geom_name'].strip() for row in rows) or
                [row['geom_id'] for row in rows]!=list(range(len(rows))) or
                len({row['geom_name'] for row in rows})!=len(rows)):
            raise ContractError("partial-color diagnostic requires complete unique geom identities")
        summary=audit_summary(rows)
        if (marker.exists() or m.get('completion_scope')!=DECLARED_SCOPE or m.get('training_ready') is not False or
                type(m.get('unclassified_geom_count')) is not int or m['unclassified_geom_count']!=0 or
                summary['role_counts'].get('UNCLASSIFIED',0)!=0 or
                hashlib.sha256(canonical(rows)).hexdigest()!=m.get('geom_audit_sha256') or
                m.get('source_audit')!=summary):
            raise ContractError("partial-color diagnostic inventory/uncertainty differs")
    elif marker.read_text()!="VISUAL_SURFACE_EXPORT_ONLY\n":
        raise ContractError("pre-scan has no valid source completion marker")
    sha(m.get("source_sha256"))
    if hashlib.sha256(canonical(m.get("source_identity"))).hexdigest()!=sha(m.get("visual_source_sha256")):
        raise ContractError("pre-scan visual source identity hash mismatch")
    cloud=verified_file(manifest_path.parent,m["file"])
    color_sha=None
    if partial:
        from g2.sim.color_evidence import verify_color_evidence
        color_sha=verify_color_evidence(manifest_path.parent,m,cloud)
        if not color_sha:raise ContractError("partial-color diagnostic requires original per-point color evidence")
    source_scope=(verify_full_scene_review(manifest_path,full_scene_review)
                  if full_scene_review is not None or not allow_declared_subset else
                  {"status":SUBSET_SCOPE,"meaning":"EXPLICIT_DIAGNOSTIC_SUBSET_ONLY"})
    grid=Path(grid).resolve()
    with grid.open(encoding="utf-8") as f:
        if f.readline().strip()!="NAV_SG_ORACLE_GRID_V1":
            raise ContractError("unsupported prebuilt occupancy bridge")
        header={}
        for _ in range(7):
            fields=shlex.split(f.readline())
            if not fields:break
            header[fields[0]]=fields[1:]
            if fields[0]=="data":break
    if header.get("scene_id")!=[m["scene_id"]] or header.get("source_sha256")!=[m["source_sha256"]] or header.get("frame_id")!=["0"]:
        raise ContractError("prebuilt geometry and visual pre-scan disagree")
    if not all(math.isfinite(v) for v in (min_z,max_z)) or min_z>=max_z or type(frames) is not int or frames<1:
        raise ContractError("invalid navigation slab/frame cutoff")
    if type(native_structures) is not bool or room_source not in ('gvd','esdf_grid'):
        raise ContractError("invalid native structural replay option")
    nav_repo=Path(nav_repo).resolve();dataset_root=Path(dataset_root).resolve();sidecar=Path(sidecar).resolve()
    if not (nav_repo/"g2/semantic/replay.py").is_file() or not dataset_root.is_dir() or not sidecar.is_dir():
        raise ContractError("native source, real recorded dataset and genuine model sidecar required")
    episode_path=(dataset_root/episode).resolve()
    if dataset_root not in episode_path.parents:
        raise ContractError("recorded episode escapes dataset root")
    recorded_manifest=read_json(episode_path/"manifest.json")
    records=recorded_manifest.get("identity",{}).get("source_files",[])
    source_by_name={}
    for record in records:
        source_by_name.setdefault(Path(record.get("path","")).name,[]).append(record)
    roots=[r for r in m.get("sources",[]) if r.get("logical_id")=="root.xml"]
    if len(roots)!=1 or not m.get("state",{}).get("file_sha256") or not m.get("input_files",{}).get("ep_meta"):
        raise ContractError("pre-scan lacks original model/states/official ep_meta binding")
    derivation=None
    if model_rebinding_proof is not None:
        from g2.sim.model_rebinding import verify
        originals=source_by_name.get('model.xml.gz',[])
        if len(originals)!=1:raise ContractError('unique original compressed episode model required')
        derivation=verify(model_rebinding_proof,prescan=m,recorded_model_sha256=originals[0].get('sha256'))
    expected={"model.xml.gz":derivation['original_compressed_sha256'] if derivation else roots[0]["sha256"],"states.npz":m["state"]["file_sha256"],
              "ep_meta.json":m["input_files"]["ep_meta"]["sha256"]}
    for name,expected_sha in expected.items():
        candidates=source_by_name.get(name,[])
        if len(candidates)!=1 or candidates[0].get("sha256")!=expected_sha:
            raise ContractError("pre-scan and recorded RGB-D use different source "+name)
    out=new_output(output,[nav_repo,dataset_root,sidecar,manifest_path.parent,grid])
    base=[native_python,"-m","g2.semantic.replay","--dataset-root",str(dataset_root),
          "--episode",episode,"--camera",camera,"--sidecar",str(sidecar),"--max-frames",str(frames),
          "--spatial-output",str(out/"native_run/spatial"),
          "--prescan-cloud",str(cloud),"--prescan-grid",str(grid),
          "--prescan-scene-id",m["scene_id"],"--prescan-source-sha256",m["source_sha256"],
          "--prescan-projection-min-z",str(min_z),"--prescan-projection-max-z",str(max_z)]
    if native_structures:base += ['--native-structures','--native-room-source',room_source]
    binding={"schema":"g2_prescan_recorded_binding_v1","scene_id":m["scene_id"],"source_sha256":m["source_sha256"],
             "episode":episode,"camera":camera,"recorded_manifest_sha256":digest(episode_path/"manifest.json"),
             "recorded_frames_sha256":digest(episode_path/"frames.jsonl"),"prescan_cloud_sha256":digest(cloud),
             "prescan_grid_sha256":digest(grid),"original_sources":expected,
             "visual_source_sha256":m["visual_source_sha256"],"source_scope":source_scope,
             "appearance_status":m['status'],"color_audit_sha256":color_sha}
    if derivation:binding['model_source_derivation']=derivation
    base += ["--prescan-recorded-binding",str(out/"recorded_binding.json")]
    plan={"schema":"g2_recorded_adapter_plan_v1","status":"DIAGNOSTIC_SUBSET_PLAN_ONLY_NOT_EXECUTED"
          if source_scope["status"]==SUBSET_SCOPE else "PLAN_ONLY_NOT_EXECUTED","cwd":str(nav_repo),
          "source_scope":source_scope,
          "scene_id":m["scene_id"],"source_sha256":m["source_sha256"],
          "inputs":{"prescan_manifest_sha256":digest(manifest_path),"grid_sha256":digest(grid)},
          "parameters_argv":base+["--output-dir",str(out/"params"),"--params-only"],
          "replay_argv":base+["--output-dir",str(out/"native_run")],
          "native_launch":{"package":"mapping","launch":"g2_semantic_review.launch",
                           "params_file":str(out/"params/mapping_params.json")},
          "dependencies":["approved ROS Noetic overlay","genuine recorded RGB/depth/pose",
                          "genuine matching YOLOE/SigLIP sidecar/service","new native snapshot export API"],
          "blocked_without":"REAL_RECORDED_RGBD_POSE_AND_MODEL_OBSERVATIONS",
          "source_labels_are_native_detections":False,"training_ready":False}
    plan.update(native_structures_enabled=native_structures,appearance_status=m['status'],
        invalid_colors_preserved=partial,full_scene_source_certified=False)
    out.mkdir(parents=True)
    write_json(out/"recorded_binding.json",binding)
    write_json(out/"plan.json",plan)
    return plan


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("prescan-manifest","grid","nav-repo","dataset-root","episode","camera","sidecar","output"):
        p.add_argument("--"+name,required=True)
    p.add_argument("--frames",type=int,default=201)
    p.add_argument("--projection-min-z",type=float,default=.15)
    p.add_argument("--projection-max-z",type=float,default=1.8)
    p.add_argument("--full-scene-review",help="server-local review bound to exact source/geom/material manifest")
    p.add_argument("--allow-declared-subset",action="store_true",help="explicit diagnostic plan; never certify full-scene coverage")
    p.add_argument("--allow-partial-color",action="store_true",help="explicit PARTIAL_COLOR diagnostic; requires --allow-declared-subset")
    p.add_argument("--native-structures",action="store_true")
    p.add_argument("--room-source",choices=('gvd','esdf_grid'),default='gvd')
    p.add_argument('--model-rebinding-proof',help='replay original gzip to rebound XML/assets/state/ep_meta proof')
    a=p.parse_args()
    r=prepare(a.prescan_manifest,a.grid,nav_repo=a.nav_repo,dataset_root=a.dataset_root,
              episode=a.episode,camera=a.camera,sidecar=a.sidecar,output=a.output,
              frames=a.frames,min_z=a.projection_min_z,max_z=a.projection_max_z,
              full_scene_review=a.full_scene_review,allow_declared_subset=a.allow_declared_subset,
              allow_partial_color=a.allow_partial_color,native_structures=a.native_structures,room_source=a.room_source,
              model_rebinding_proof=a.model_rebinding_proof)
    print(r["status"])


if __name__=="__main__":
    main()
