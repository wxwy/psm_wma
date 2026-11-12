"""General surface K-hit and same-depth source attribution: no asset names."""
import numpy as np
import pytest
from g2.views.surface_renderer import cpu_mesh_layers,_empty_layer,_merge_opaque
from g2.views.surface_composer import compose_surface_layers


def triangle_world(z):
    return np.array([[0.,0.,z],[.7,0,z],[0.,.7,z]])


def test_two_surfaces_of_one_geom_keep_both_layers():
    vertices=np.vstack([triangle_world(.7),triangle_world(.3)])
    out=cpu_mesh_layers([(7,vertices,[[0,1,2],[3,4,5]])],{7},
                        [0,0,0],[1,1,1],'floor_top',.1)
    valid,depth,ids,shape,info,face,bary,overflow=out
    two=np.sum(valid,axis=0)==2
    assert two.any() and not overflow.any()
    assert np.all(ids[0][two]==7) and np.all(ids[1][two]==7)
    assert np.all(depth[0][two]<depth[1][two])
    assert np.all(face[0][two]==0) and np.all(face[1][two]==1)


def test_different_opaque_colors_at_same_depth_remain_uncertain():
    red=_empty_layer((1,1));blue=_empty_layer((1,1))
    for obj,gid,color in ((red,3,[1,0,0]),(blue,4,[0,0,1])):
        obj['geometry_valid'][:]=True;obj['depth'][:]=.5;obj['geom_id'][:]=gid
        obj['alpha'][:]=1.;obj['alpha_valid'][:]=True
        obj['color_valid'][:]=True;obj['rgb_linear'][:]=color
        obj['appearance_linear'][:]=color
    merged=_merge_opaque(red,blue)
    assert not merged['color_valid'].any()
    assert merged['visibility_ambiguous'].all()


def test_matching_colored_opaque_tie_keeps_color_but_not_unique_identity():
    a=_empty_layer((1,1));b=_empty_layer((1,1))
    for layer,gid in ((a,3),(b,4)):
        layer['geometry_valid'][:]=True;layer['depth'][:]=.5;layer['geom_id'][:]=gid
        layer['alpha'][:]=1.;layer['alpha_valid'][:]=True
        layer['color_valid'][:]=True;layer['rgb_linear'][:]=[.1,.4,.7]
        layer['appearance_linear'][:]=[.1,.4,.7]
    result=_merge_opaque(a,b)
    assert result['color_valid'].all()
    assert result['visibility_ambiguous'].all()
    composed=compose_surface_layers(result,[])
    assert composed['composite_valid'].all()
    assert result['geom_id'].item()==3


def test_opaque_depth_barrier_stops_all_transparent_layers_behind_it():
    near=_empty_layer((1,1))
    near.update(geometry_valid=np.ones((1,1),bool),depth=np.ones((1,1)),
                geom_id=np.array([[3]]),alpha=np.ones((1,1)),
                color_valid=np.ones((1,1),bool),alpha_valid=np.ones((1,1),bool),
                rgb_linear=np.asarray([[[.1,.2,.3]]]))
    farther=dict(near,depth=np.full((1,1),2),geom_id=np.asarray([[4]]),
                 rgb_linear=np.asarray([[[1,0,0]]]),alpha=np.full((1,1),.5))
    output=compose_surface_layers(near,[farther])
    assert output['composite_valid'].all()
    np.testing.assert_allclose(output['composite_rgb_linear'],[[[.1,.2,.3]]])


def test_equal_surface_id_and_coplanar_face_is_not_double_alpha():
    near=triangle_world(.7)
    verts=np.vstack((near,near))
    geom,depth,ids,size,info,faces,bary,overflow=cpu_mesh_layers(
        [(17,verts,[[0,1,2],[3,4,5]])],{17},[0,0,0],[1,1,1],'floor_top',.1)
    assert (geom.sum(axis=0)<=1).all()
    assert not overflow.any()


def test_multi_hit_overflow_stays_flagged():
    meshes=[]
    for gid in range(42):
        meshes.append((gid,triangle_world(.05+gid*.015),[[0,1,2]]))
    result=cpu_mesh_layers(meshes,set(range(42)),[0,0,0],[1,1,1],'floor_top',.1,max_hits=8)
    assert result[-1].any() and (result[0].sum(axis=0)<=8).all()
