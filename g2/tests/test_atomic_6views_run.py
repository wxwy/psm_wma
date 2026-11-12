"""CPU-only tests: manual worker gate, live progress, reusable stage receipts,
native geometry from a new scene, distinct Room/Island source membership.
"""
import json
from pathlib import Path

import pytest

from g2.offline import atomic_6views_run as runner
from g2.offline import atomic_6views_connections as links
from g2.offline import atomic_6views_geometry as geometry


def sample_row():
    return {"episode_id": 123, "task_class": "OpenDrawer",
            "source_fingerprint": "a"*64}


def test_partial_stage_rebuilt_but_completed_source_reused(tmp_path, capsys):
    row = sample_row()
    work = tmp_path / "work"
    work.mkdir()
    called = []
    def builder(dst):
        called.append(1)
        dst.mkdir()
        (dst/"payload.json").write_text(json.dumps({"hello":"world"}))
    path = runner.stage(work,"source",row,builder,required=("payload.json",))
    assert len(called)==1
    assert runner.stage(work,"source",row,builder,required=("payload.json",))==path
    assert len(called)==1
    (path/runner.RECEIPT).unlink()
    runner.stage(work,"source",row,builder,required=("payload.json",))
    assert len(called)==2
    log=capsys.readouterr().out
    assert "G2_STAGE_START" in log and "G2_STAGE_REUSE" in log
    assert "G2_STAGE_REBUILD" in log


def test_invalid_manual_start_is_rejected_before_dataset_scan(tmp_path):
    with pytest.raises(Exception,match="manual-only"):
        runner.main(["run","--raw-root",str(tmp_path/"nonexistent"),
                     "--plan-root",str(tmp_path/"plan")])
    with pytest.raises(Exception,match="manual-only"):
        runner.main(["work","--raw-root",str(tmp_path/"nonexistent"),
                     "--episode-id","123","--plan-root",str(tmp_path/"plan")])


def test_gpu_worker_slots_have_distinct_ros_masters():
    result=runner._ports([4,5,6,7],2,21500)
    assert len(result)==8
    assert sorted(x[0] for x in result)==[4,4,5,5,6,6,7,7]
    assert len({x[2] for x in result})==8
    with pytest.raises(Exception):
        runner._ports([4,4],2,21500)


def test_scene_bound_geometry_without_layout_whitelist():
    mujoco=pytest.importorskip("mujoco")
    xml="""<mujoco><worldbody>
      <body name="floor"><geom name="floor_main" type="box"
        pos="0 0 -.05" size="1 1 .05"/></body>
      <body name="wall"><geom name="wall_main" type="box"
        pos="0 -1 1" size="1 .05 1.1"/></body>
      <body name="object"><geom name="item_main" type="box"
        pos=".3 .2 .3" size=".1 .1 .1"/></body>
    </worldbody></mujoco>"""
    model=mujoco.MjModel.from_xml_string(xml)
    data=mujoco.MjData(model)
    mujoco.mj_forward(model,data)
    meta={"schema":"nav_sg_gt_metadata_v1",
          "geoms":{"floor_main":{"kind":"floor"},
                   "wall_main":{"kind":"wall"},
                   "item_main":{"kind":"object"}}}
    plan=geometry.grid_from_source(model,data,meta)
    assert plan["original_floor_geom_count"]==1
    assert plan["original_wall_geom_count"]==1
    assert plan["voxel_count"]>100
    assert plan["known_free_space_is_test_only"] is True
    assert plan["known_region"]["regions"][0]["type"]=="box"


def _entity(i, kind, lo, hi, room=0):
    return {"id":f"entity_{i}","kind":kind,"room_uid":room,
            "bbox_min":lo,"bbox_max":hi,"triangles":[[0,1,2]],
            "label":"something","source_category_id":"unknown",
            "connection_relay_allowed":True}


def test_native_island_object_uses_explicit_wall_gap_and_transitive_links():
    entities=[
        _entity(0,"object",[3,0,.2],[3.1,.1,.3]),
        _entity(1,"object",[3.12,0,.2],[3.2,.1,.3]),
        _entity(2,"object",[.1,0,.2],[.2,.1,.3]),
        _entity(3,"floor",[-5,-5,-.1],[5,5,0],room=-1),
        _entity(4,"wall",[0,-5,0],[.05,5,2],room=-1),
    ]
    packet,out,complete=links.compute(entities,[0],connection_distance=.30,known=True)
    assert complete
    by={r["id"]:r for r in out}
    assert by["entity_0"]["island_id"] is not None
    assert by["entity_1"]["island_id"]==by["entity_0"]["island_id"]
    assert by["entity_2"]["island_id"] is None
    assert by["entity_2"]["root_affiliations"]
    assert packet["threshold_m"]==.30
