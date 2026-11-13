"""P1 indexed Episode tests: independent scene GT events and frame-linked PNG reuse."""
import gzip
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from g2.offline.scene_view_event_index import (
    SceneViewCursor,index_state,resolve_indexed_png,robot_pose_xy_yaw,
)
from g2.offline.scene_view_index_package import (
    repackage_indexed,validate_indexed_episode,
)


def _write_json(path,body):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(body,sort_keys=True,separators=(",",":"))+"\n")


def create_legacy(root):
    frames=[0,10,20]
    views=["sixview/floor_top.png","sixview/plus_Y.png"]
    rows=[]
    for i,frame in enumerate(frames):
        p=root/f"state_{i:06d}_frame_{frame:06d}"
        (p/"sixview").mkdir(parents=True)
        # Static environment: plus_Y is always green. Robot arrow is part
        # of final floor_top, changes in state 1, remains unchanged in state 2.
        Image.new("RGB",(12,8),(255 if i==0 else 100,0,0)).save(p/views[0])
        Image.new("RGB",(12,8),(0,200,0)).save(p/views[1])
        with gzip.open(p/"scene_graph.json.gz","wb") as f:
            f.write(json.dumps({"frame_id":frame,"entities":[{"id":str(i)}]}).encode())
        rows.append({"frame":frame,"view_pngs":views,"scene_graph":"scene_graph.json.gz","islands":[]})
    doc={"schema":"g2_atomic_compact_6views_v1","states":rows,
         "episode_id":999,"task_class":"MockTask","source_renderer":"f27",
         "complete":True,"state_count":3,"source_fingerprint":"a"*64,
         "training_ready":False}
    _write_json(root/"episode_manifest.json",doc)
    digest=hashlib.sha256((root/"episode_manifest.json").read_bytes()).hexdigest()
    _write_json(root/"COMPLETE.json",{"schema":doc["schema"],"episode_id":999,
                "complete":True,"state_count":3,"renderer":"f27",
                "source_fingerprint":doc["source_fingerprint"],
                "episode_manifest_sha256":digest})
    return frames,views


def events():
    c=SceneViewCursor([10])
    p=np.zeros((1,3))
    r=np.eye(3).reshape(1,3,3)
    return [c.observe(0,0,p,r,[0.,0.,0.]),
            c.observe(1,10,p,r,[0.5,0.,0.]),
            c.observe(2,20,p,r,[0.5,0.,0.])]


def test_indexed_export_and_frame_specific_sg(tmp_path):
    orig=tmp_path/"legacy";orig.mkdir()
    frames,views=create_legacy(orig)
    content_hash=hashlib.sha256((orig/"episode_manifest.json").read_bytes()).hexdigest()
    out=tmp_path/"indexed"
    receipt=repackage_indexed(orig,out,events(),strict_audit=True)
    assert receipt["images_indexed"]==3
    assert validate_indexed_episode(out)==3
    d=json.loads((out/"episode_manifest.json").read_text())
    assert d["schema"]=="g2_atomic_compact_6views_v2"
    assert [s["update_mode"] for s in d["states"]]==["FULL","ARROW_ONLY","REUSE_ALL"]
    assert [len(s["view_pngs"]) for s in d["states"]]==[2,1,0]
    assert [len(s["view_refs"]) for s in d["states"]]==[0,1,2]
    p=resolve_indexed_png(d["states"],2,"sixview/floor_top.png",out)
    assert p.name=="floor_top.png" and "state_000001" in str(p)
    p=resolve_indexed_png(d["states"],2,"sixview/plus_Y.png",out)
    assert "state_000000" in str(p)
    for index in range(3):
        scene=out/f"state_{index:06d}_frame_{frames[index]:06d}"/"scene_graph.json.gz"
        with gzip.open(scene,"rt") as f:
            assert json.load(f)["frame_id"]==frames[index]
    assert content_hash==hashlib.sha256((orig/"episode_manifest.json").read_bytes()).hexdigest()


def test_reuse_fails_closed_if_gt_motion_incorrect(tmp_path):
    orig=tmp_path/"legacy";orig.mkdir()
    create_legacy(orig)
    # Candidate event detector says scene unchanged; source changes plus_Y.
    changed=orig/"state_000001_frame_000010/sixview/plus_Y.png"
    Image.new("RGB",(12,8),(233,200,1)).save(changed)
    out=tmp_path/"wrong"
    with pytest.raises(ValueError,match="EXACT_IMAGE_AUDIT_FAILED"):
        repackage_indexed(orig,out,events(),strict_audit=True)
    assert not out.exists(), "bad indexing must never publish a partial Episode"


def test_bad_ref_is_rejected_at_read_time(tmp_path):
    orig=tmp_path/"legacy";orig.mkdir()
    create_legacy(orig)
    out=tmp_path/"indexed"
    repackage_indexed(orig,out,events())
    m=json.loads((out/"episode_manifest.json").read_text())
    m["states"][2]["view_refs"]["sixview/plus_Y.png"]["ref_state"]=2
    with pytest.raises(ValueError,match="invalid direct"):
        resolve_indexed_png(m["states"],2,"sixview/plus_Y.png",out)


def test_older_schema_does_not_silently_accept_v2_as_v1(tmp_path):
    orig=tmp_path/"legacy";orig.mkdir()
    create_legacy(orig)
    out=tmp_path/"indexed"
    repackage_indexed(orig,out,events())
    d=json.loads((out/"episode_manifest.json").read_text())
    assert d["schema"]!="g2_atomic_compact_6views_v1"
