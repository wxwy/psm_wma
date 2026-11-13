"""P1 offline event-driven views + compact index proof; no production modifications."""
from pathlib import Path
import sys
import numpy as np
import pytest
from PIL import Image

from g2.offline.scene_view_event_index import (
    SceneViewCursor, index_state, resolve_indexed_png, robot_pose_xy_yaw,
)

VIEWS=["sixview/floor_top.png","sixview/plus_Y.png","islands/island_0/plus_X.png"]


def p(x=0.):
    return np.asarray([[x,0.,0.],[5.,0.,0.]],dtype=np.float64)


def m():
    return np.broadcast_to(np.eye(3),(2,3,3)).copy()


def sample_events():
    c=SceneViewCursor([11,12])
    return [
      c.observe(0,0,p(),m(),[0.,0.,0.]),
      c.observe(1,10,p(),m(),[.2,0.,.1]),
      c.observe(2,20,p(),m(),[.2,0.,.1]),
      c.observe(3,30,p(.3),m(),[.2,0.,.1]),
      c.observe(4,40,p(.3),m(),[.2,0.,.1]),
      c.observe(5,50,p(.3),m(),[.2,0.,.2]),
    ]


def test_four_cases_and_direct_reference_locations():
    e=sample_events()
    assert [x.mode for x in e]==["FULL","ARROW_ONLY","REUSE_ALL","FULL","REUSE_ALL","ARROW_ONLY"]
    assert [x.scene_source_state for x in e]==[0,0,0,3,3,3]
    assert [x.final_floor_source_state for x in e]==[0,1,1,3,3,5]
    a=[index_state(x,VIEWS) for x in e]
    assert a[1]["view_pngs"]==["sixview/floor_top.png"]
    assert a[1]["view_refs"]["sixview/plus_Y.png"]["ref_state"]==0
    assert a[2]["view_pngs"]==[]
    assert a[2]["view_refs"]["sixview/floor_top.png"]["ref_state"]==1
    assert a[4]["view_refs"]["sixview/plus_Y.png"]["ref_state"]==3
    assert a[5]["view_pngs"]==["sixview/floor_top.png"]


def test_small_png_indexed_store(tmp_path):
    events=sample_events()
    rows=[index_state(x,VIEWS) for x in events]
    assert all(x["floor_background_ref_state"]==y for x,y in zip(rows,[0,0,0,3,3,3]))
    actual={}
    for row in rows:
        base=tmp_path/f"state_{row['state_id']:06d}_frame_{row['frame']:06d}"
        for rel in row["view_pngs"]:
            path=base/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            if rel=="sixview/floor_top.png":
                # Mock arrow drawing: physical base 0/3, marker moves at states 1/5
                rgb=(row["state_id"],100,0)
            else:
                rgb=(row["state_id"],0,100)
            Image.new("RGB",(6,5),rgb).save(path)
            actual[row["state_id"],rel]=path
    for i,row in enumerate(rows):
        for rel in VIEWS:
            path=resolve_indexed_png(rows,i,rel,tmp_path)
            if rel=="sixview/floor_top.png":
                owner=[0,1,1,3,3,5][i]
            else:
                owner=[0,0,0,3,3,3][i]
            assert path==actual[owner,rel]
    expected_total=len(VIEWS)*len(rows)
    stored_total=sum(len(row["view_pngs"]) for row in rows)
    assert expected_total==18 and stored_total==8
    # Every sampling state still stores its own independent Scene Graph.
    for row in rows:
        assert row["frame"]==row["state_id"]*10


def test_yaw_wrap_near_plus_minus_pi_is_not_false_motion():
    c=SceneViewCursor([1])
    c.observe(0,0,p()[:1],m()[:1],[0,0,np.pi-1e-9])
    e=c.observe(1,10,p()[:1],m()[:1],[0,0,-np.pi+1e-9])
    assert e.mode=="ARROW_ONLY"  # 2e-9 > default threshold
    assert e.robot_yaw_delta_rad<5e-9
    c=SceneViewCursor([1],robot_yaw_tol_rad=1e-8)
    c.observe(0,0,p()[:1],m()[:1],[0,0,np.pi-1e-9])
    assert c.observe(1,10,p()[:1],m()[:1],[0,0,-np.pi+1e-9]).mode=="REUSE_ALL"


def _yaw_rotation(degrees):
    a=np.deg2rad(degrees)
    return np.asarray([
        [np.cos(a),-np.sin(a),0.],
        [np.sin(a), np.cos(a),0.],
        [0.,0.,1.],
    ], dtype=np.float64).reshape(1,3,3)


def test_rotation_threshold_in_actual_degrees():
    c=SceneViewCursor([0])
    a=c.observe(0,0,p()[:1],_yaw_rotation(0),[0,0,0])
    b=c.observe(1,10,p()[:1],_yaw_rotation(0.9),[0,0,0])
    assert a.mode=="FULL"
    assert b.mode=="REUSE_ALL"
    assert 0.89<b.object_rotation_max_deg<0.91
    d=c.observe(2,20,p()[:1],_yaw_rotation(1.1),[0,0,0])
    assert d.mode=="FULL"
    assert 1.09<d.object_rotation_max_deg<1.11


def test_threshold_in_real_millimetres_and_accumulation():
    c=SceneViewCursor([0])
    assert c.observe(0,0,p()[:1],m()[:1],[0,0,0]).mode=="FULL"
    a=c.observe(1,10,p(.0006)[:1],m()[:1],[0,0,0])
    assert a.mode=="REUSE_ALL"
    assert a.scene_source_state==0
    b=c.observe(2,20,p(.0012)[:1],m()[:1],[0,0,0])
    assert b.mode=="FULL", "0.6+0.6 mm must not be ignored forever"
    assert b.scene_source_state==2
    x=c.observe(3,30,p(.0017)[:1],m()[:1],[0,0,0])
    assert x.mode=="REUSE_ALL" and x.scene_source_state==2


def test_translation_uses_3d_euclidean_norm_not_per_axis():
    c=SceneViewCursor([0])
    c.observe(0,0,p()[:1],m()[:1],[0,0,0])
    q=p()[:1].copy()
    q[0,:2]=[.0008,.0008]
    b=c.observe(1,10,q,m()[:1],[0,0,0])
    assert b.mode=="FULL"
    assert .0011<b.object_translation_max_m<.0012


def test_thresholds_are_strict_below_not_at_threshold():
    c=SceneViewCursor([0])
    c.observe(0,0,p()[:1],m()[:1],[0,0,0])
    # Binary floating representation: 0.001 from an exact zero origin
    # is exactly the same float as the configured threshold.
    assert c.observe(1,10,p(.001)[:1],m()[:1],[0,0,0]).mode=="FULL"
    d=SceneViewCursor([0])
    d.observe(0,0,p()[:1],m()[:1],[0,0,0])
    assert d.observe(1,10,p()[:1],_yaw_rotation(1.0),[0,0,0]).mode=="FULL"


def test_object_motion_does_not_require_robot_motion():
    c=SceneViewCursor([0])
    c.observe(0,0,p()[:1],m()[:1],[0,0,0])
    a=c.observe(1,10,p(.0008)[:1],m()[:1],[0.5,0,0])
    assert a.mode=="ARROW_ONLY" and a.scene_source_state==0
    b=c.observe(2,20,p(.0012)[:1],m()[:1],[0.5,0,0])
    assert b.mode=="FULL" and b.final_floor_source_state==2


def test_one_degree_rotation_is_relative_to_last_rendered_scene():
    c=SceneViewCursor([0])
    c.observe(0,0,p()[:1],_yaw_rotation(0),[0,0,0])
    assert c.observe(1,10,p()[:1],_yaw_rotation(.55),[0,0,0]).mode=="REUSE_ALL"
    assert c.observe(2,20,p()[:1],_yaw_rotation(1.10),[0,0,0]).mode=="FULL"


@pytest.mark.parametrize("t",[-1, float("inf"),float("nan"),None, "a"])
def test_invalid_threshold_rejected(t):
    with pytest.raises(ValueError):
        SceneViewCursor([1],translation_tol_m=t)


def test_missing_and_future_refs_rejected(tmp_path):
    c=SceneViewCursor([0])
    first=index_state(c.observe(0,0,p()[:1],m()[:1],[0,0,0]),VIEWS)
    second=index_state(c.observe(1,10,p()[:1],m()[:1],[0,0,0]),VIEWS)
    with pytest.raises(ValueError,match="missing"):
        resolve_indexed_png([first,second],1,"sixview/plus_Y.png",tmp_path)
    second["view_refs"]["sixview/plus_Y.png"]["ref_state"]=2
    with pytest.raises(ValueError,match="invalid direct"):
        resolve_indexed_png([first,second],1,"sixview/plus_Y.png",tmp_path)


def test_robot_pose_source():
    got=robot_pose_xy_yaw(dict(position_world=[1,2,3],forward_world=[0.,1.,0.]))
    np.testing.assert_allclose(got,[1.,2.,np.pi/2.])


def test_no_future_or_external_path():
    with pytest.raises(ValueError,match="unsafe"):
        index_state(sample_events()[0],["../../private.png","sixview/floor_top.png"])

def test_index_rejects_skip_event_exceeding_approved_physical_threshold():
    from dataclasses import replace
    base=sample_events()[2]
    assert base.mode=="REUSE_ALL"
    with pytest.raises(ValueError,match="exceeding"):
        index_state(replace(base,object_translation_max_m=.001),VIEWS)
    with pytest.raises(ValueError,match="exceeding"):
        index_state(replace(base,object_rotation_max_deg=1.0),VIEWS)
