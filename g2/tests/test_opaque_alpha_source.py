"""Source-bound opaque ray constraints and proof gating."""
import copy
import numpy as np
import pytest
from g2.views import gpu_nearest_recovery as nearest
from g2.views.direct_color import validate_surface_data
from g2.tests.test_direct_color_views import source_case
from g2.offline.direct_source import certified_opaque_color_owner_indices

def test_same_ray_behind_geometry_depth_gap_is_allowed():
    d=np.asarray([[0,.025,0],[.005,.025,0],[0,.031,0],[.008,.025,0],[0,-.006,0]],float)
    result=nearest.ray_behind_surface_mask(d,np.asarray([0.,1.,0.]))
    assert result.tolist()==[True,True,False,False,False]

@pytest.mark.parametrize('value',[-1,100,['0'],[2,2],None])
def test_opaque_source_proof_fail_closed(value):
    snap,_,data=source_case()
    if value is None: return  # old source remains compatible
    evidence=copy.deepcopy(data[4])
    evidence.update(opaque_ray_owner_indices=value if isinstance(value,list) else [value],
                    opaque_ray_cert_schema='g2_verified_compiled_gt_opaque_owner_v1')
    with pytest.raises(Exception):
        validate_surface_data((*data[:4],evidence),snap)

def test_transparent_entity_never_eligible_for_opaque_ray():
    snap,_,data=source_case()
    specs=[
       {'owner':2,'g':0,'original_valid_samples':100},
       {'owner':2,'g':1,'original_valid_samples':0},
       {'owner':3,'g':2,'original_valid_samples':100},
       {'owner':3,'g':3,'original_valid_samples':100},
    ]
    class FakeM:
      def __init__(self):self.order={0:1.,1:1.,2:1.,3:.2}
    import g2.sim.source_geometry as sg
    saved=sg.effective_rgba
    sg.effective_rgba=lambda model,g:np.asarray([1.,1.,1.,model.order[g]])
    try:
       got=certified_opaque_color_owner_indices(FakeM(),specs,snap)
       assert 2 in got and 3 not in got
    finally:
       sg.effective_rgba=saved


def test_transparent_source_rgba_keeps_unknown_background_and_never_relabels_rgb(
        tmp_path):
    from PIL import Image
    from g2.views.alpha_source import save_source_alpha_sidecars
    snapshot, _, data = source_case()
    ids = sorted(e['id'] for e in snapshot['entities'])
    target_id = 'entity_5'
    proof = {
        'schema': 'g2_compiled_gt_alpha_only_source_v1',
        'scene_id': snapshot['scene_id'],
        'source_sha256': snapshot['source_sha256'],
        'model_source_sha256': 'e' * 64,
        'supported_owner_materials': {
            target_id: {'owner_index': ids.index(target_id),
                        'rgba': [1.,1.,1.,.2],
                        'geom_name': 'exact_source_geom',
                        'source_model_sha256': 'e' * 64}
        },
        'skipped_mixed_or_textured_owners': {'entity_3': 'MIXED_ALPHA'},
        'training_ready': False,
    }
    native = tmp_path / 'existing_rendered'
    target = native / 'rooms/0/plus_Y'
    target.mkdir(parents=True)
    arr = np.zeros((2, 3, 3), np.uint8)
    arr[0, 1] = [12, 24, 36]
    Image.fromarray(arr).save(target / 'rgb.png')
    geom = np.zeros((2,3), np.uint8)
    geom[0,:3] = 255
    Image.fromarray(geom).save(target / 'geometry_valid.png')
    valid = np.zeros((2,3), np.uint8)
    valid[0,1] = 255
    Image.fromarray(valid).save(target / 'color_valid.png')
    native_owner = np.full((2,3), -2, np.int32)
    native_owner[0,0] = ids.index(target_id)
    native_owner[0,1] = ids.index(target_id)
    native_owner[0,2] = 2
    np.savez_compressed(target / 'geometry.npz', native_entity_index=native_owner,
                        depth=np.zeros((2,3), np.float32))
    before = (target / 'rgb.png').read_bytes()
    result = save_source_alpha_sidecars(
        native, {'views': {'rooms/0/plus_Y': {'image_generated':True}}},
        snapshot, proof, tmp_path / 'alpha')
    assert result['view_count']==1
    assert result['view_alpha_layers'][0]['alpha_pixel_count']==1
    dest = tmp_path / 'alpha/rooms/0/plus_Y'
    layer = np.asarray(Image.open(dest / 'source_rgba.png').convert('RGBA'))
    assert layer[0,0].tolist()==[255,255,255,51]
    assert layer[0,1,3]==0 and layer[0,2,3]==0
    assert (target / 'rgb.png').read_bytes()==before
    assert result['background_compositing_status']=='UNKNOWN_BACKGROUND_NOT_YET_RENDERED'
    assert result['training_ready'] is False


@pytest.mark.parametrize('alpha', [0.0, 1.0, -0.1, 1.1])
def test_invalid_alpha_source_proof_fails_closed(tmp_path,alpha):
    from g2.views.alpha_source import save_source_alpha_sidecars
    snapshot,_,_=source_case()
    eid='entity_5'
    ids=sorted(e['id'] for e in snapshot['entities'])
    proof={'schema':'g2_compiled_gt_alpha_only_source_v1',
           'scene_id':snapshot['scene_id'],'source_sha256':snapshot['source_sha256'],
           'model_source_sha256':'e'*64,'supported_owner_materials':{
               eid:{'owner_index':ids.index(eid),
                    'rgba':[1,1,1,alpha],'source_model_sha256':'e'*64}},
           'skipped_mixed_or_textured_owners':{}}
    with pytest.raises(Exception):
        save_source_alpha_sidecars(tmp_path, {'views':{}},snapshot,proof,tmp_path/'out')
    assert not (tmp_path/'out').exists()
