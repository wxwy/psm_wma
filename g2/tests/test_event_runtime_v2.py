"""Opt-in P0/P1/P2 functional boundaries. No RoboCasa simulator needed."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from PIL import Image

from g2.io import ContractError
from g2.offline.atomic_6views_compact import PackageError
from g2.offline.atomic_6views_compact_v2 import (
    package_indexed,completed_output_indexed,
)
from g2.offline.scene_view_index_package import validate_indexed_episode
from g2.offline import atomic_6views_plan as plan
from g2.offline import atomic_6views_run as runner
from g2.views.direct_color import save_direct_material_views


def _json(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,sort_keys=True,separators=(",",":"))+"\n")


def _source(tmp_path,*,bad_reference=False,view_set_change=False):
    root=tmp_path/"full_f27"
    root.mkdir()
    views=["sixview/floor_top.png","sixview/plus_Y.png"]
    rows=[]
    previous=0
    for i,frame in enumerate((0,10,20)):
        stage=root/f"state_{i:06d}_frame_{frame:06d}"
        stage.mkdir()
        mode=("FULL","ARROW_ONLY","REUSE_ALL")[i]
        members=views+["sixview/plus_X.png"] if i==2 and view_set_change else views
        actual=(members if i==0 or (i==2 and view_set_change) else
                ["sixview/floor_top.png"] if i==1 else [])
        for rel in actual:
            image=stage/rel
            image.parent.mkdir(parents=True,exist_ok=True)
            Image.new("RGB",(6,4),(25+i,105,203)).save(image)
        if i==2 and view_set_change:
            mode="FULL"
            previous=i
        (stage/"scene_graph.json").write_text(json.dumps({
            "frame_id":frame,"scene_id":"robot_scene_123",
            "source_sha256":"a"*64,"entities":[{"id":str(i)}]})+"\n")
        refs={}
        if mode=="ARROW_ONLY":
            refs={"sixview/plus_Y.png":{"ref_state":0,"path":"sixview/plus_Y.png"}}
        elif mode=="REUSE_ALL":
            refs={"sixview/plus_Y.png":{"ref_state":0,"path":"sixview/plus_Y.png"},
                  "sixview/floor_top.png":{"ref_state":1,"path":"sixview/floor_top.png"}}
        if i==1 and bad_reference:
            refs["sixview/plus_Y.png"]["ref_state"]=5
        dc=dict(frame_id=frame,scene_id="robot_scene_123",source_sha256="a"*64,
                view_count=len(members),visual_geometry_source="SURFACE_REGISTRY_VISUAL_GEOMETRY",
                surface_material_identity_per_pixel=True,training_ready=False,
                views=[{"native_view":"rooms/0/"+Path(p).stem,"rgb_file":p} for p in members])
        if mode!="FULL":
            dc.update(scene_event_mode=mode,scene_view_refs=refs,scene_materialized_views=actual)
        _json(stage/"direct_color_views.json",dc)
        rows.append(dict(frame=frame,state_id=i,view_count=len(members),
            scene_event_mode=mode,
            scene_keyframe_state=previous,final_floor_png_state=(i if mode in ("FULL","ARROW_ONLY") else 1),
            object_translation_max_m=0.,object_rotation_max_deg=0.))
    _json(root/"episode_receipt.json",dict(
        schema="g2_repository_native_view_episode_v1",
        complete=True,spatial_state_count=3,states=rows,
        scene_event_index_enabled=True,source_material_identity_per_pixel=True,
        view_opaque_geometry_source="SURFACE_REGISTRY_VISUAL_GEOMETRY",
        source_inputs_sha256="b"*64,
        scene_motion_translation_tol_m=.001,
        scene_motion_rotation_tol_deg=1.))
    return root


def _row():
    return dict(episode_id=7,task_class="MockTask",spatial_frames=[0,10,20],
                source_fingerprint="b"*64,
                expected_relative_output="tasks/MockTask/episodes/episode_000007")


def test_live_v2_build_and_resume_proves_all_three_modes(tmp_path):
    source=_source(tmp_path)
    output_root=tmp_path/"output"
    output=output_root/_row()["expected_relative_output"]
    doc=package_indexed(source,output,episode_id=7,task_class="MockTask",selection=_row())
    assert len(doc["states"])==3
    assert [len(x["view_pngs"]) for x in doc["states"]]==[2,1,0]
    assert [len(x["view_refs"]) for x in doc["states"]]==[0,1,2]
    assert len(list(output.glob("state_*/scene_graph.json.gz")))==3
    assert validate_indexed_episode(output)==3
    assert completed_output_indexed(_row(),output_root)
    assert plan.completed_output(_row(),output_root,allow_index_v2=True)
    with pytest.raises(plan.PlanError,match="indexed v2"):
        plan.completed_output(_row(),output_root)


def test_live_v2_rejects_bad_future_ref(tmp_path):
    src=_source(tmp_path,bad_reference=True)
    out=tmp_path/"out"
    with pytest.raises((ValueError,PackageError)):
        package_indexed(src,out,episode_id=7,task_class="MockTask")
    assert not out.exists()


def test_full_render_can_change_the_view_set(tmp_path):
    src=_source(tmp_path,view_set_change=True)
    output=tmp_path/"packed"
    doc=package_indexed(src,output,episode_id=7,task_class="MockTask")
    assert len(doc["states"][-1]["view_pngs"])==3
    assert doc["states"][-1]["view_refs"]=={}
    assert validate_indexed_episode(output)==3


def test_resume_rejects_wrong_source_fingerprint(tmp_path):
    src=_source(tmp_path)
    root=tmp_path/"output"
    package_indexed(src,root/_row()["expected_relative_output"],episode_id=7,
                    task_class="MockTask",selection=_row())
    bad={**_row(),"source_fingerprint":"0"*64}
    with pytest.raises((ValueError,PackageError,plan.PlanError)):
        plan.completed_output(bad,root,allow_index_v2=True)


def test_direct_material_requires_signed_source_without_color(tmp_path):
    with pytest.raises(ContractError):
        save_direct_material_views(tmp_path,{},dict(source_mode="native_observation"),
                                   tmp_path/"invalid",visual_mesh_by_room={})
    assert not (tmp_path/"invalid").exists()


def test_production_default_remains_v1_and_p2_requires_explicit_optin():
    assert runner.WorkerConfig.__dataclass_fields__["scene_event_index"].default is False
    assert runner.WorkerConfig.__dataclass_fields__["sim_direct_material"].default is False
    with pytest.raises(ContractError,match="P2 direct material requires"):
        runner.main(["work","--sim-direct-material","--manual-start","--allow-experimental"])
