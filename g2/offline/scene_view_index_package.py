"""P1 experimental indexed compact package for already-completed F27 Episodes.

This is an offline packaging/integrity oracle, NOT the production F27 runner.
Runtime decisions must be supplied by SceneViewCursor (nonrobot objects + base);
SHA is used solely for exact-output A/B certification, never for decisions.

Creates a NEW output directory atomically; never mutates source/output roots.
Existing v1 compact reader and producer remain unchanged.
"""
from __future__ import annotations
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile

from g2.offline.scene_view_event_index import ViewEvent,index_state,resolve_indexed_png


def _sha(path):
    hasher=hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda:file.read(1<<20),b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _write(path,data):
    with Path(path).open("x",encoding="utf-8") as out:
        json.dump(data,out,ensure_ascii=False,sort_keys=True,
                  separators=(",",":"),allow_nan=False)
        out.write("\n")


def repackage_indexed(source_episode, destination, events, *, strict_audit=True):
    """Materialize only changed PNGs; SG remains per-state and unchanged."""
    source=Path(source_episode).resolve(strict=True)
    output=Path(destination).absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("destination already exists")
    if source==output or source in output.parents or output in source.parents:
        raise ValueError("source/destination overlap")
    complete=json.loads((source/"COMPLETE.json").read_text())
    src_bytes=(source/"episode_manifest.json").read_bytes()
    manifest=json.loads(src_bytes)
    if (not complete.get("complete") or not manifest.get("complete")
            or manifest.get("schema")!="g2_atomic_compact_6views_v1"
            or complete.get("episode_manifest_sha256")!=hashlib.sha256(src_bytes).hexdigest()):
        raise ValueError("source is not a completed v1 F27 package")
    src_rows=manifest["states"]
    if len(src_rows)!=len(events) or len(src_rows)<1:
        raise ValueError("events do not cover source")
    output.parent.mkdir(parents=True,exist_ok=True)
    staging=Path(tempfile.mkdtemp(prefix="._g2_p1_index_",dir=output.parent))
    good=False
    counters=dict(files_materialized=0,bytes_materialized=0,
                  images_indexed=0,images_audited=0)
    indexed=[]
    try:
        for i,(src_row,event) in enumerate(zip(src_rows,events)):
            if (not isinstance(event,ViewEvent) or event.state_id!=i
                    or event.frame!=src_row["frame"]):
                raise ValueError("wrong event identity")
            views=src_row["view_pngs"]
            if len(views)!=len(set(views)) or not views:
                raise ValueError("invalid source View inventory")
            new_row=index_state(event,views)
            state_dir=f"state_{i:06d}_frame_{event.frame:06d}"
            root=source/state_dir
            target=staging/state_dir
            target.mkdir()
            graph=src_row.get("scene_graph")
            if not isinstance(graph,str) or graph!="scene_graph.json.gz":
                raise ValueError("per-frame SG is required")
            original_graph=root/graph
            with gzip.open(original_graph,"rt",encoding="utf-8") as f:
                sg=json.load(f)
            if sg.get("frame_id")!=event.frame:
                raise ValueError("SG frame does not match source state")
            shutil.copyfile(original_graph,target/graph)
            counters["files_materialized"]+=1
            counters["bytes_materialized"]+=original_graph.stat().st_size
            for relative in new_row["view_pngs"]:
                a=root/relative
                if not a.is_file() or a.is_symlink():
                    raise ValueError("missing physical source View")
                b=target/relative
                b.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(a,b)
                counters["files_materialized"]+=1
                counters["bytes_materialized"]+=a.stat().st_size
            for rel,ref in new_row["view_refs"].items():
                src_index=ref["ref_state"]
                original_row=src_rows[src_index]
                physical=source/f"state_{src_index:06d}_frame_{original_row['frame']:06d}"/rel
                current=root/rel
                if (not physical.is_file() or physical.is_symlink()
                        or not current.is_file() or current.is_symlink()):
                    raise ValueError("referenced or current source PNG absent")
                if strict_audit and _sha(physical)!=_sha(current):
                    raise ValueError(f"EXACT_IMAGE_AUDIT_FAILED state={i} view={rel}")
                counters["images_indexed"]+=1
                counters["images_audited"]+=int(strict_audit)
            indexed.append({
                "frame":event.frame,
                "view_pngs":new_row["view_pngs"],
                "view_refs":new_row["view_refs"],
                "update_mode":event.mode,
                "floor_background_ref_state":new_row["floor_background_ref_state"],
                "islands":src_row["islands"],
                "scene_graph":graph,
            })
        out_manifest=dict(manifest)
        out_manifest.update(
            schema="g2_atomic_compact_6views_v2",
            states=indexed,
            indexed_views_enabled=True,
            image_reuse_basis="NONROBOT_GT_VISUAL_POSE_AND_ROBOT_BASE_XY_YAW",
            image_reuse_oracle_sha_verified=bool(strict_audit),
            original_complete_manifest_sha256=complete["episode_manifest_sha256"],
        )
        _write(staging/"episode_manifest.json",out_manifest)
        marker=dict(complete)
        marker.update(schema=out_manifest["schema"],
            episode_manifest_sha256=_sha(staging/"episode_manifest.json"))
        _write(staging/"COMPLETE.json",marker)
        validate_indexed_episode(staging)
        os.rename(staging,output)
        good=True
        return counters
    finally:
        if not good:
            shutil.rmtree(staging,ignore_errors=True)


def validate_indexed_episode(root):
    """No missing refs, no cycles, every SG current, manifest/content identity."""
    root=Path(root).resolve(strict=True)
    complete=json.loads((root/"COMPLETE.json").read_text())
    data=json.loads((root/"episode_manifest.json").read_text())
    if (complete.get("schema")!="g2_atomic_compact_6views_v2"
            or data.get("schema")!=complete.get("schema")
            or data.get("complete") is not True
            or complete.get("complete") is not True
            or complete.get("episode_manifest_sha256")!=_sha(root/"episode_manifest.json")
            or len(data["states"])!=complete["state_count"]):
        raise ValueError("indexed output is not a completed F27 v2 package")
    rows=data["states"]
    previous=-1
    for i,row in enumerate(rows):
        if type(row["frame"]) is not int or row["frame"]<=previous:
            raise ValueError("invalid frame ordering")
        previous=row["frame"]
        output=root/f"state_{i:06d}_frame_{row['frame']:06d}"
        sg=output/"scene_graph.json.gz"
        if not sg.is_file() or sg.is_symlink():
            raise ValueError("per-frame SG missing")
        with gzip.open(sg,"rt",encoding="utf-8") as f:
            if json.load(f).get("frame_id")!=row["frame"]:
                raise ValueError("current frame SG corrupt")
        all_paths=set(row["view_pngs"])|set(row["view_refs"])
        if set(row["view_pngs"])&set(row["view_refs"]):
            raise ValueError("physical and indexed view collision")
        if not any(s.startswith("sixview/") and Path(s).name=="floor_top.png"
                   for s in all_paths):
            raise ValueError("missing floor view")
        for path in all_paths:
            resolve_indexed_png(rows,i,path,root)
    return len(rows)
