"""Source-verified reader of nav_sg native 10mm MuJoCo asset color chunks.

The binary-less transport is imported into the *existing* G2 six-view recipe.
The GT source and object identity never masquerade as RGB-D perception.
"""
import json
from pathlib import Path

import numpy as np

from g2.io import ContractError, digest, read_json

SCHEMA="g2_mujoco_dense_visual_chunks_v1"


def load_dense_surfaces(dense_manifest, snapshot, bundle_source_inputs):
    root=Path(dense_manifest).resolve(strict=True)
    dense=read_json(root)
    if dense.get("schema")!=SCHEMA or dense.get("source_mode")!="mujoco_full_scene":
        raise ContractError("expected MuJoCo asset-colored dense source")
    if (dense.get("scene_id")!=snapshot["scene_id"] or
            dense.get("source_sha256")!=snapshot["source_sha256"] or
            dense.get("frame_id")!=snapshot["frame_id"] or
            dense.get("world_frame")!=snapshot["world_frame"] or
            dense.get("training_ready") is not False or
            dense.get("oracle_source_not_real_perception") is not True or
            dense.get("partial_geom_limit") is not None):
        raise ContractError("dense GT source scene/state/provenance mismatch")
    native=bundle_source_inputs.get("files",{}).get("native_manifest",{})
    if native.get("sha256")!=dense.get("native_gt_manifest",{}).get("sha256"):
        raise ContractError("dense asset colors do not bind original nav_sg GT geometry")
    n=dense.get("exported_points")
    if type(n) is not int or not 0<n<=100_000_000 or dense.get("predicted_full_scene_points")!=n:
        raise ContractError("invalid dense color source point inventory")
    parts=dense.get("chunks")
    if not isinstance(parts,list) or not 1<=len(parts)<=256 or sum(p.get("points",0) for p in parts)!=n:
        raise ContractError("invalid dense source chunk inventory")
    entities={e["source_instance_id"]:e["id"] for e in snapshot["entities"]}
    sorted_ids=sorted(e["id"] for e in snapshot["entities"])
    numeric={k:i for i,k in enumerate(sorted_ids)}
    owner=np.full(n,-1,np.int32)
    begin=0
    unmapped=0
    for geom in dense["sampled_geoms"]:
        count=geom["points"]
        name=geom.get("source_instance",[None,None])[1]
        possibilities=[key for key in entities if name and key.endswith(":"+name)]
        if len(possibilities)>1:
            raise ContractError("ambiguous native asset instance binding")
        if len(possibilities)==1:
            owner[begin:begin+count]=numeric[entities[possibilities[0]]]
        else:
            unmapped+=count
        begin+=count
    if begin!=n:
        raise ContractError("dense color source geometry ranges differ from source count")
    xyz=np.empty((n,3),np.float32)
    rgb=np.empty((n,3),np.uint8)
    valid=np.empty(n,bool)
    cursor=0
    for i,record in enumerate(parts):
        file=Path(record["path"]).resolve(strict=True)
        if (file.parent!=root.parent or file.name!=f"precolored_{i:04d}.txt" or
                not 0<record.get("points",0)<=5_000_000 or
                record.get("bytes")!=file.stat().st_size or
                record.get("sha256")!=digest(file)):
            raise ContractError("dense source original chunk file mismatch")
        with file.open("rb") as stream:
            head=[stream.readline().decode("ascii").strip() for _ in range(7)]
            expected=["NAV_SG_PRECOLORED_CLOUD_V1",
                      "scene_id "+json.dumps(snapshot["scene_id"],ensure_ascii=True),
                      "source_sha256 "+snapshot["source_sha256"],
                      "frame_id "+str(snapshot["frame_id"]),
                      'world_frame "'+snapshot["world_frame"]+'"',
                      f'points {record["points"]:010d}',"data"]
            if head!=expected:
                raise ContractError("dense source chunk header/identity differs")
            body=stream.read().decode("ascii")
        a=np.fromstring(body,sep=" ",dtype=np.float32)
        num=record["points"]
        if a.size!=7*num:
            raise ContractError("dense source chunk truncated/malformed")
        a=a.reshape(num,7)
        if (not np.isfinite(a).all() or
                not np.all((a[:,3:6]>=0)&(a[:,3:6]<=255)) or
                not np.all((a[:,6]==0)|(a[:,6]==1))):
            raise ContractError("dense source color or XYZ invalid")
        xyz[cursor:cursor+num]=a[:,:3]
        rgb[cursor:cursor+num]=a[:,3:6].astype(np.uint8)
        valid[cursor:cursor+num]=a[:,6]==1
        cursor+=num
    if cursor!=n or np.count_nonzero(valid)!=dense["color_valid_points"]:
        raise ContractError("dense source color count does not match bound manifest")
    evidence={"native_dense_source_manifest_sha256":digest(root),
              "dense_sample_spacing_m":dense["spacing_m"],
              "dense_small_sample_spacing_m":dense["small_spacing_m"],
              "dense_source_points":n,
              "dense_valid_color_points":int(valid.sum()),
              "unassigned_source_instance_points":unmapped,
              "provenance":"SOURCE_BOUND_MUJOCO_VISUAL_ASSET_NOT_ROBOT_RGBD"}
    return xyz,rgb,valid,owner,evidence
