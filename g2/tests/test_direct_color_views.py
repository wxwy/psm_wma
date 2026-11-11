"""Direct 10 mm transport binding and unchanged native View membership."""

import copy
import hashlib
import json

import numpy as np
import pytest
from PIL import Image

from g2.io import ContractError, canonical
from g2.tests.test_full_map_contract import full_case
from g2.views.direct_color import export_white_views, validate_surface_data
from g2.views.render_connections import render_v2


def source_case():
    snapshot = full_case()
    snapshot['surface_color_source'] = 'MUJOCO_SOURCE_SURFACES_WITH_ORIGINAL_INVALID_MASK'
    evidence = {key: snapshot[key] for key in ('scene_id', 'source_sha256', 'frame_id', 'world_frame')}
    evidence.update(entity_index_to_native_id=sorted(e['id'] for e in snapshot['entities']),
                    voxel_leaf_m=.01, dense_sample_spacing_m=.01, dense_small_sample_spacing_m=.01)
    data = (np.array([[.305, .305, .705]]), np.array([[75, 90, 160]], np.uint8),
            np.array([True]), np.array([2], np.int32), evidence)
    manifest = {'source_scope': {'status': 'MUJOCO_FULL_MAP_GT_PENDING_HUMAN'},
                'version_sha256': 'e' * 64, 'training_ready': False}
    return snapshot, manifest, data


@pytest.mark.parametrize('field', ['scene_id', 'source_sha256', 'frame_id', 'world_frame',
                                  'entity_index_to_native_id'])
def test_color_source_from_a_different_frame_or_owner_table_is_rejected(field):
    snapshot, _, data = source_case()
    data[4][field] = 'different'
    with pytest.raises(ContractError):
        validate_surface_data(data, snapshot)


@pytest.mark.parametrize('fault', ['owner', 'rgb_wrap', 'nonfinite', 'resolution'])
def test_direct_color_transport_rejects_values_that_would_change_geometry_or_rgb(fault):
    snapshot, _, data = source_case()
    data = list(data)
    if fault == 'owner':
        data[3][0] = 100
    elif fault == 'rgb_wrap':
        data[1] = np.array([[256, 90, 160]], np.int32)
    elif fault == 'nonfinite':
        data[0][0, 0] = np.nan
    else:
        data[4]['voxel_leaf_m'] = .005
    with pytest.raises(ContractError):
        validate_surface_data(data, snapshot)


def test_explicit_color_uses_no_legacy_text_source_and_keeps_native_membership(tmp_path):
    snapshot, manifest, data = source_case()
    before = copy.deepcopy(snapshot)
    source = tmp_path / 'verified_source'
    source.mkdir()  # Deliberately no surfaces.csv, chunks or source_inputs.json.
    result = render_v2(source, manifest, snapshot, tmp_path / 'views',
                       surface_data=data, meters_per_pixel=.2, renderer_backend='cpu')
    floor = result['views']['rooms/0/floor_top']
    assert floor['image_generated'] and floor['observed_object_color_pixels'] > 0
    assert snapshot == before
    assert data[2].tolist() == [True]
    assert result['room_six_refs']['0']['islands'] == ['island_0_entity_2', 'island_0_entity_5']
    assert 'entity_2' not in result['views']['rooms/0/minus_Y']['native_entity_ids']
    assert result['recipe_sha256'] == hashlib.sha256(canonical(result['recipe'])).hexdigest()


def test_privileged_color_cannot_enter_observed_rgbd_or_two_input_routes(tmp_path):
    snapshot, manifest, data = source_case()
    root = tmp_path / 'source'
    root.mkdir()
    with pytest.raises(ContractError, match='mutually exclusive'):
        render_v2(root, manifest, snapshot, tmp_path / 'both', surface_data=data,
                  dense_manifest='unused.json')
    snapshot['source_mode'] = 'perception'
    snapshot['surface_color_source'] = 'NATIVE_RGBD_FUSION_ONLY'
    with pytest.raises(ContractError, match='privileged'):
        render_v2(root, manifest, snapshot, tmp_path / 'sensor', surface_data=data)
    assert not (tmp_path / 'both').exists() and not (tmp_path / 'sensor').exists()


def test_white_export_keeps_multiple_rooms_and_island_directions_separate(tmp_path):
    paths = ['rooms/0/plus_X', 'rooms/1/plus_X',
             'rooms/0/islands/island_0_entity_2/plus_X']
    source = tmp_path / 'rendered'
    image = np.array([[[0, 0, 0], [17, 34, 51]]], np.uint8)
    geometry = np.array([[0, 255]], np.uint8)
    for path in paths:
        folder = source / path
        folder.mkdir(parents=True)
        Image.fromarray(image).save(folder / 'rgb.png')
        Image.fromarray(geometry).save(folder / 'geometry_valid.png')
        Image.fromarray(geometry).save(folder / 'color_valid.png')
    rendered = {'room_six_refs': {'0': {}, '1': {}},
                'views': {path: {'image_generated': True} for path in paths}}
    exported = export_white_views(rendered, source, tmp_path / 'export')
    assert len({row['rgb_file'] for row in exported}) == 3
    assert exported[2]['rgb_file'] == 'islands/island_0_entity_2/plus_X.png'
    for row in exported:
        actual = np.asarray(Image.open(tmp_path / 'export' / row['rgb_file']))
        np.testing.assert_array_equal(actual[0, 0], [255, 255, 255])
        np.testing.assert_array_equal(actual[0, 1], [17, 34, 51])
