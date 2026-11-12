"""Independent small projections and observed-map use of the shared compositor."""
import numpy as np
import pytest

from g2.io import ContractError
from g2.views.surface_renderer import cpu_mesh_hits, project_surface_samples, _merge_opaque, _empty_layer, selected_layer_field


def test_original_face_and_barycentric_and_large_surface_id():
    near=np.array([[0.,0.,.7],[2.,0.,.7],[0.,2.,.7]])
    far=near.copy();far[:,2]=.2
    result=cpu_mesh_hits([(1,far,[[0,1,2]]),(501,near,[[0,1,2]])],{1,501},
                         [0,0,0],[2,2,1],'floor_top',1.)
    geometry,depth,ids,_,_,faces,bary,ambiguity=result
    assert geometry[2,0] and ids[2,0]==501 and faces[2,0]==0
    np.testing.assert_allclose(depth[2,0],-.7)
    np.testing.assert_allclose(bary[2,0],[.5,.25,.25],atol=1e-14)
    assert not geometry[0,2]
    assert not ambiguity.any()


def test_coplanar_distinct_geoms_keep_ambiguity_evidence():
    vertices=np.array([[0.,0.,.7],[2.,0.,.7],[0.,2.,.7]])
    result=cpu_mesh_hits([(1,vertices,[[0,1,2]]),(2,vertices,[[0,1,2]])],{1,2},
                         [0,0,0],[2,2,1],'floor_top',1.)
    assert result[-1][2,0]


def observed(points,ids,rgb,alpha):
    n=len(points)
    return dict(points=np.array(points,float),geom_id=np.array(ids,int),
        rgb_linear=np.array(rgb,float),alpha=np.array(alpha,float),
        color_valid=np.ones(n,bool),alpha_valid=np.ones(n,bool))


def test_rgbd_surfaces_have_no_semantic_dependency_and_no_256_limit():
    samples=observed([[.5,.5,.2],[.5,.5,.7]],[3,501],[[0,0,1],[1,0,0]],[1,.5])
    result=project_surface_samples(samples,[0,0,0],[1,1,1],'floor_top',1.)
    np.testing.assert_allclose(result['composite_rgb_linear'][1,0],[.5,0,.5])
    assert result['composite_valid'][1,0]
    assert result['front_geom_id'][1,0]==501
    assert result['front_owner'][1,0]==-1
    assert result['opaque_geom_id'][1,0]==3


def test_observed_same_voxel_different_materials_are_not_averaged():
    samples=observed([[.505,.505,.505],[.505,.505,.508]],[7,8],[[1,0,0],[0,1,0]],[1,1])
    result=project_surface_samples(samples,[.5,.5,.5],[.51,.51,.51],'floor_top',.01)
    assert result['composite_valid'][1,0]
    np.testing.assert_array_equal(result['composite_rgb_linear'][1,0],[0,1,0])
    assert result['front_geom_id'][1,0]==8


def test_dynamic_background_restored_when_front_moves_out():
    background=_empty_layer((1,2));background['geometry_valid'][:]=True
    background['depth'][:]=2;background['geom_id'][:]=3;background['alpha'][:]=1
    background['alpha_valid'][:]=True;background['color_valid'][:]=True
    background['rgb_linear'][:]=[0,0,1]
    moving=_empty_layer((1,2));moving['geometry_valid'][0,0]=True
    moving['depth'][0,0]=1;moving['geom_id'][0,0]=9
    first=_merge_opaque(background,moving)
    assert first['geom_id'][0,0]==9
    second=_merge_opaque(background,_empty_layer((1,2)))
    np.testing.assert_array_equal(second['geom_id'],[[3,3]])
    np.testing.assert_array_equal(background['geom_id'],[[3,3]])


def test_observed_unknown_color_still_occludes_background():
    samples=observed([[.5,.5,.2],[.5,.5,.7]],[3,501],[[0,0,1],[0,0,0]],[1,1])
    samples['color_valid'][1]=False
    result=project_surface_samples(samples,[0,0,0],[1,1,1],'floor_top',1.,background_rgb_linear=np.ones(3))
    assert not result['composite_valid'][1,0]
    assert result['opaque_geom_id'][1,0]==501
    assert np.isnan(result['composite_rgb_linear'][1,0]).all()


def test_observed_adapter_rejects_missing_material_evidence():
    samples=observed([[.5,.5,.2]],[3],[[0,0,1]],[1])
    del samples['alpha_valid']
    with pytest.raises(ContractError,match='alpha_valid'):
        project_surface_samples(samples,[0,0,0],[1,1,1],'floor_top',1.)


@pytest.mark.parametrize('key,bad',[('color_valid',[.5]),('alpha_valid',[float('nan')]),('semantic_owner',[1.9])])
def test_observed_adapter_rejects_lossy_evidence_conversions(key,bad):
    samples=observed([[.5,.5,.2]],[3],[[0,0,1]],[1]);samples[key]=np.array(bad)
    with pytest.raises(ContractError):
        project_surface_samples(samples,[0,0,0],[1,1,1],'floor_top',1.)


@pytest.mark.parametrize('front_alpha',[0.,.5])
def test_same_geom_retains_deeper_surface_after_zero_or_blend(front_alpha):
    samples=observed([[.5,.5,.7],[.5,.5,.2]],[3,3],[[1,0,0],[0,0,1]],[front_alpha,1])
    result=project_surface_samples(samples,[0,0,0],[1,1,1],'floor_top',1.)
    np.testing.assert_allclose(result['composite_rgb_linear'][1,0],[front_alpha,0,1-front_alpha])
    assert result['composite_valid'][1,0]


def test_pixel_opaque_alpha_winner_has_matching_material_and_owner():
    from g2.views.surface_composer import compose_surface_layers
    back=_empty_layer((1,1));front=_empty_layer((1,1))
    for layer,gid,mat,owner,depth in ((back,1,10,100,2.),(front,2,20,-1,1.)):
        layer['geometry_valid'][:]=True;layer['color_valid'][:]=True;layer['alpha_valid'][:]=True
        layer['depth'][:]=depth;layer['geom_id'][:]=gid;layer['alpha'][:]=1
        layer['material_id'][:]=mat;layer['semantic_owner'][:]=owner
        layer.pop('surface_id')
    composed=compose_surface_layers(back,[front])
    actual=selected_layer_field([back,front],composed['opaque_geom_id'],composed['opaque_depth'],'material_id')
    owner=selected_layer_field([back,front],composed['opaque_geom_id'],composed['opaque_depth'],'semantic_owner')
    assert actual.item()==20 and owner.item()==-1


def test_varying_alpha_first_hit_cannot_certify_unseen_same_geom_background():
    from g2.views.surface_renderer import single_hit_alpha_valid
    from g2.views.surface_composer import compose_surface_layers
    layer=_empty_layer((1,3));layer.pop('surface_id')
    layer['geometry_valid'][:]=True;layer['depth'][:]=1.;layer['geom_id'][:]=9
    layer['color_valid'][:]=True;layer['alpha'][:]=[0.,.5,1.]
    layer['alpha_valid']=single_hit_alpha_valid(
        dict(reason='COMPILED_TEXTURE_ALPHA_RANGE',alpha_min=0.,alpha_max=1.),
        layer['alpha'],np.ones((1,3),bool))
    result=compose_surface_layers(_empty_layer((1,3)),[layer],background_rgb_linear=np.ones(3))
    np.testing.assert_array_equal(result['composite_valid'],[[False,False,True]])
    constant=single_hit_alpha_valid(
        dict(reason='COMPILED_TEXTURE_ALPHA_RANGE',alpha_min=.5,alpha_max=.5),
        np.array([.5]),np.array([True]))
    assert constant.item()
