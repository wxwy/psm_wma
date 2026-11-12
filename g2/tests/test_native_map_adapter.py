import copy
import numpy as np
import pytest
from g2.io import ContractError
from g2.views.native_map_adapter import native_map_samples,voxel_cell_identity,project_native_map_view


def bundle():
    snapshot={"scene_id":"fixture","source_sha256":"a"*64,
              "frame_id":0,"world_frame":"world",
              "entities":[{"id":"entity_0"},{"id":"entity_1"}]}
    xyz=np.asarray([[.005,.005,.005],[.015,.005,.005],
                    [-.005,-.015,.005]])
    surface=(xyz,np.asarray([[0,0,0],[255,255,255],[0,0,0]],np.uint8),
             np.ones(3,bool),np.asarray([-1,0,1],np.int32),
             dict(scene_id="fixture",source_sha256="a"*64,frame_id=0,
                  world_frame="world",
                  source_mode="NATIVE_LONG_LIVED_DIRECT_COLOR_WORKER_10MM_FULL_SOURCE"))
    return surface,snapshot


def test_world_voxel_identity_is_stable_and_independent_of_semantics():
    surface,snapshot=bundle()
    points=native_map_samples(surface,snapshot,certified_opaque=True)
    assert len(set(points["geom_id"]))==3
    assert (points["geom_id"]>=0).all()
    assert points["semantic_owner"].tolist()==[-1,0,1]
    assert points["material_id"].tolist()==[-1,-1,-1]
    assert not points["provenance"]["source_geom_id_known"]
    np.testing.assert_array_equal(points["geom_id"],voxel_cell_identity(surface[0]))


def test_raw_native_black_is_valid_and_is_not_missing_color():
    surf,snap=bundle()
    room={"reference_frame":{"origin_world":[0,0,0],"axes_world":np.eye(3).tolist()}}
    result,proof=project_native_map_view(surf,snap,room,[0,0,0],[.02,.01,.01],"floor_top")
    assert result["composite_valid"].any()
    assert result["geometry_valid"].any()
    assert not proof["numeric_material_albedo_certified"]
    assert result["front_owner"][result["geometry_valid"]].min()==-1


def test_spatial_identity_rejects_duplicate_or_out_of_range_cell():
    surf,snap=bundle()
    duplicated=(np.repeat(surf[0][:1],2,axis=0),
                np.repeat(surf[1][:1],2,axis=0),
                np.ones(2,bool),np.asarray([0,1]),surf[4])
    with pytest.raises(ContractError,match="duplicate"):
        native_map_samples(duplicated,snap,certified_opaque=True)
    with pytest.raises(ContractError,match="range"):
        voxel_cell_identity(np.asarray([[1e6,0,0]]))


def test_forged_source_evidence_or_unknown_alpha_never_promotes():
    surf,snap=bundle()
    wrong=copy.deepcopy(surf)
    wrong[4]["source_sha256"]="b"*64
    with pytest.raises(ContractError,match="identity"):
        native_map_samples(wrong,snap,certified_opaque=True)
    with pytest.raises(ContractError,match="alpha"):
        native_map_samples(surf,snap,certified_opaque=False)
