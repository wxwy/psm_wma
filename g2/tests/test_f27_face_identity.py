"""Regression: UV-discontinuous coplanar triangles in one original Geom.

A Geom ID is an object/mesh identity, *not* a physical face ID. Transparent
K-hit samples can overlap at the exact depth while belonging to different
source triangles with different UV evidence; this must not be falsely treated
as a duplicate of the same surface. True conflicting same-face duplicates
must still fail closed.
"""
from types import SimpleNamespace
import numpy as np
import pytest

from g2.io import ContractError
from g2.views.surface_renderer import SurfaceRenderer
from g2.views.surface_composer import compose_surface_layers


class _Materials:
    def descriptor(self,gid,kind):
        return dict(material_id=5,alpha_min=.5,alpha_max=.5,reason="TEST")
    def sample(self,gid,kind,face_ids,bary,local_points=None):
        n=len(face_ids)
        color=np.zeros((n,3),float)
        color[:,0]=(np.asarray(face_ids)==0).astype(float)
        color[:,1]=(np.asarray(face_ids)==1).astype(float)
        return SimpleNamespace(
            rgb_linear=color,appearance_linear=color,
            alpha=np.full(n,.5), color_valid=np.ones(n,bool),
            alpha_valid=np.ones(n,bool), material_id=np.full(n,5,np.int32),
            reason_code=np.zeros(n,int),alpha_reason_code=np.zeros(n,int),
            evidence={"kind":"SOURCE_FACE_UV_EVIDENCE"})


def _face(renderer,face):
    registry={"surfaces":{7:dict(local_vertices=np.array(
        [[0.,0.,0.],[1.,0.,0.],[0.,1.,0.],[1.,1.,0.]]),
        faces=np.array([[0,1,2],[1,3,2]],np.int32),
        rotation=np.eye(3),kind="mesh",semantic_owner_index=2)}}
    room={"reference_frame":{"axes_world":np.eye(3).tolist()},
          "_current_view_axis":"floor_top"}
    return renderer._paint_hits(
        registry,room,{7:np.array([0,1],np.int32)},
        np.ones((1,1),bool),np.ones((1,1),float),
        np.full((1,1),7,np.int32),np.array([[face]],np.int32),
        np.array([[[.25,.25,.5]]]),np.zeros((1,1),bool),multi=True)[0]


def test_distinct_original_faces_can_share_geom_and_depth_without_duplicate():
    renderer=object.__new__(SurfaceRenderer)
    renderer.materials=_Materials()
    left=_face(renderer,0)
    right=_face(renderer,1)
    assert left["geom_id"][0,0]==right["geom_id"][0,0]==7
    assert left["depth"][0,0]==right["depth"][0,0]==1.
    assert left["face_id"][0,0]!=right["face_id"][0,0]
    assert left["surface_id"][0,0]!=right["surface_id"][0,0]
    assert left["surface_id"][0,0]>2**32 and right["surface_id"][0,0]>2**32
    output=compose_surface_layers(None,[left,right],
                                  background_rgb_linear=np.ones(3))
    assert output["deduplicated_layer_count"].item()==0
    # Different colors at identical depth remain explicitly ambiguous, not
    # silently overwritten by whichever triangle happened to be first.
    assert not output["composite_valid"].item()


def test_true_conflicting_same_face_same_depth_still_fails_closed():
    renderer=object.__new__(SurfaceRenderer)
    renderer.materials=_Materials()
    left=_face(renderer,0)
    right=_face(renderer,0)
    right["rgb_linear"][0,0]=[.1,.2,.3]
    with pytest.raises(ContractError,match="duplicate surface_id"):
        compose_surface_layers(None,[left,right])


def test_original_face_id_not_transparent_layer_index():
    renderer=object.__new__(SurfaceRenderer)
    renderer.materials=_Materials()
    left=_face(renderer,0)
    second=_face(renderer,1)
    assert left["surface_id"].item() == (8<<32)|1
    assert second["surface_id"].item() == (8<<32)|2
