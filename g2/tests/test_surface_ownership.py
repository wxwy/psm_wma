import pytest
import numpy as np

from g2.io import ContractError
from g2.nav_bridge.surface_ownership import SurfaceOwnerVerifier
from g2.tests.test_connections import connection_case


def test_legal_entity_replacement_and_dropping_a_unique_owner_are_rejected():
    entities=connection_case()['entities'];checker=SurfaceOwnerVerifier(entities,.045)
    # Cup top is uniquely on the cup, far from table, wall and floor.
    p=[[-.05,0,1.]];checker.verify(p,['entity_3'])
    for wrong in ('entity_2','entity_1','unknown'):
        with pytest.raises(ContractError,match='owner'):checker.verify(p,[wrong])


def test_overlapping_source_surfaces_must_remain_unknown_and_cannot_steal_color():
    entities=connection_case()['entities'];checker=SurfaceOwnerVerifier(entities,.045)
    point=[[-.3,-.3,0.]]  # table and actual Floor share the surface
    checker.verify(point,['unknown'])
    with pytest.raises(ContractError):checker.verify(point,['entity_2'])


@pytest.mark.parametrize('distance,owner',[(.044,'entity_3'),(.046,'unknown')])
def test_owner_threshold_is_actual_3d_triangle_distance_not_bbox_interior(distance,owner):
    entities=connection_case()['entities'];checker=SurfaceOwnerVerifier(entities,.045)
    checker.verify([[-.05,0,1.+distance]],[owner])


def test_bvh_retains_all_source_triangles_and_matches_dense_and_sparse_chunks():
    entities=connection_case()['entities'];checker=SurfaceOwnerVerifier(entities,.045)
    points=np.tile([-.05,0,1.],(4097,1));owners=['entity_3']*len(points)
    checker.verify(points,owners);checker.verify(points[:1],owners[:1])


@pytest.mark.parametrize('second_mesh',[False,True])
def test_repeated_vertex_face_matches_native_nonfinite_branch_without_new_owner(second_mesh):
    degenerate={'id':'entity_0','vertices':[[0,0,0],[0,0,0],[1,0,0]],'triangles':[[0,1,2]],
        'bbox_min':[0,0,0],'bbox_max':[1,0,0]}
    entities=[degenerate]
    if second_mesh:entities.append({'id':'entity_1','vertices':[[.4,-1,0],[.6,-1,0],[.5,1,0]],'triangles':[[0,1,2]],
        'bbox_min':[.4,-1,0],'bbox_max':[.6,1,0]})
    checker=SurfaceOwnerVerifier(entities,.045)
    checker.verify([[.5,0,0]],['entity_1' if second_mesh else 'unknown'])
    assert degenerate['triangles']==[[0,1,2]]
