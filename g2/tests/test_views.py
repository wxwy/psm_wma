import json
import numpy as np
import pytest
from PIL import Image
from g2.io import ContractError
from g2.nav_bridge.snapshot import capture
from g2.views.render import rasterize,render


def raster(points,colors,valid,axis="floor_top",owners=None,**kw):
    return rasterize(np.asarray(points,float).reshape(-1,3),np.asarray(colors,np.uint8).reshape(-1,3),
                     np.asarray(valid,bool),np.zeros(len(points),np.int32) if owners is None else owners,
                     {0},[-.1,-.1,-.1],[1.1,1.1,1.1],axis,meters_per_pixel=1,**kw)


def test_floor_highest_upper_lowest_visible_surface():
    args=([[0,0,0],[0,0,1]],[[200,0,0],[0,200,0]],[1,1])
    assert [0,200,0] in raster(*args)[0].reshape(-1,3).tolist()
    assert [200,0,0] in raster(*args,axis="upper_up")[0].reshape(-1,3).tolist()


def test_uncolored_front_geometry_occludes_rear_color():
    image,valid,geom,*_=raster([[0,0,0],[0,0,1]],[[200,0,0],[0,0,0]],[1,0])
    assert geom.sum()==1 and valid.sum()==0 and image.sum()==0


@pytest.mark.parametrize("rgb",[[0,0,0],[255,255,255]])
def test_real_black_and_white_remain_valid(rgb):
    _,valid,geom,*_=raster([[0,0,0]],[rgb],[1])
    assert valid.sum()==geom.sum()==1


def test_input_order_does_not_change_depth_test():
    p=np.asarray([[0,0,.1],[0,0,.9],[1,1,.5]])
    c=np.asarray([[100,0,0],[0,200,0],[0,0,200]])
    a=raster(p,c,[1,1,1]);b=raster(p[::-1],c[::-1],[1,1,1])
    np.testing.assert_equal(a[0],b[0]);np.testing.assert_equal(a[3],b[3])


def test_unknown_exterior_cannot_occlude_independent_island():
    a=raster([[0,0,0]],[[200,0,0]],[1],axis="+X")
    b=raster([[0,0,0],[-10,0,0]],[[200,0,0],[0,0,0]],[1,0],axis="+X",owners=np.asarray([0,-1]))
    np.testing.assert_equal(a[1],b[1])
    assert b[1].sum()==1


def test_selected_points_outside_full_world_crop_do_not_occlude():
    a=raster([[0,0,0],[-10,0,0]],[[200,0,0],[0,0,200]],[1,1],axis="+X")
    assert [200,0,0] in a[0].reshape(-1,3).tolist()


def test_geometry_only_empty_selected_samples_is_valid_unknown():
    result=raster([[0,0,0]],[[200,0,0]],[1],owners=np.asarray([1]))
    assert result[1].sum()==0
    result=raster([],[],[])
    assert result[1].sum()==0


def test_reverse_color_cannot_paint_uncolored_front_mesh():
    vertices=[[0,-1,-1],[0,2,-1],[0,2,2],[0,-1,2]]
    data=raster([[.06,0,0]],[[0,0,200]],[1],axis="+X",
                meshes=[(0,vertices,[[0,1,2],[0,2,3]])],surface_tolerance=.0250001)
    assert data[2].sum()>0 and data[1].sum()==0


def test_pixel_budget_fails_closed():
    with pytest.raises(ContractError,match="budget"):
        rasterize(np.zeros((1,3)),np.zeros((1,3)),np.ones(1),np.zeros(1),{0},
                  [0,0,0],[100,100,100],"floor_top",meters_per_pixel=.001)


def test_six_refs_and_islands_are_independent_native_assets(native_factory,tmp_path):
    native,s=native_factory()
    capture(native,tmp_path/"bundle",allow_oracle_diagnostic=True)
    with pytest.raises(ContractError,match="oracle"):render(tmp_path/"bundle",tmp_path/"bad")
    result=render(tmp_path/"bundle",tmp_path/"views",meters_per_pixel=.1,allow_oracle_diagnostic=True)
    assert len(result["room_six_refs"]["0"])==6
    assert len(result["views"])==10 and len(result["islands"])==1
    for name,view in result["views"].items():
        if name.startswith("rooms/"):
            assert "entity_3" not in view["native_entity_ids"]
    assert result["islands"]["island_0_entity_3"]["member_entity_ids"]==["entity_3"]
    assert result["temporal_video"] is False and result["training_ready"] is False
    assert Image.open(tmp_path/"views/house/floor_top/rgb.png").mode=="RGB"
    assert (tmp_path/"bundle/surfaces.csv").exists()
    indices=np.load(tmp_path/"views/islands/island_0_entity_3/minus_X/geometry.npz")["native_entity_index"]
    assert {result["entity_index_to_native_id"][int(i)] for i in np.unique(indices) if i>=0}=={"entity_3"}


def test_missing_wall_stays_unknown_reserved_slot(native_factory,tmp_path):
    native,_=native_factory();capture(native,tmp_path/"bundle",allow_oracle_diagnostic=True)
    r=render(tmp_path/"bundle",tmp_path/"views",meters_per_pixel=.2,allow_oracle_diagnostic=True)
    assert r["views"]["rooms/0/minus_X"]["boundary_type"]=="unknown"
    assert r["views"]["rooms/0/minus_X"]["observed_color_pixels"]==0


def test_fine_island_crop_retains_owned_native_voxel_center(native_factory,tmp_path):
    native,_=native_factory()
    path=native/"surfaces.csv"
    path.write_text(path.read_text().replace("0.5,0.5,0.2,200", "0.625,0.5,0.2,200"))
    capture(native,tmp_path/"bundle",allow_oracle_diagnostic=True)
    r=render(tmp_path/"bundle",tmp_path/"views",meters_per_pixel=.01,allow_oracle_diagnostic=True)
    view=r["views"]["islands/island_0_entity_3/minus_X"]
    assert view["observed_color_pixels"]>0
    assert view["world_bounds_max"][0]>.625
