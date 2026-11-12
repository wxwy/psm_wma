"""F24 C++ wire fixtures and refusal of incomplete episode completion.

The golden bytes below follow the packed C++ declarations in
mapping/src/gt/direct_layer_reader.h; they are independent of Python structs.
"""

import copy
import hashlib
import json

import numpy as np
import pytest

from g2.io import ContractError
from g2.offline.native_transport import (composed_digest, read_native_surface,
                                         sha_file, write_layer_batch, write_sequence)
from g2.views.direct_color import validate_surface_data


def test_layer_bytes_match_cpp_packed_headers_and_sorted_geom_inventory(tmp_path):
    scene = 'wire_fixture'
    specs = [{'g': 17, 'owner': -1}, {'g': 5, 'owner': 1}]
    layers = {17: None, 5: (np.array([[-1, 2, 3], [0, 0, 0]], np.int32),
                           np.array([[4, 5, 6], [7, 8, 9]], np.uint8))}
    output = tmp_path / 'initial.bin'
    write_layer_batch(output, frame=0, scene_id=scene, source_sha='a' * 64,
                      state_sha='b' * 64, expected_sha='c' * 64,
                      specs=specs, changed=specs, static_ids={5}, layers=layers)
    # Header size: 40 scalar bytes + four 64-byte ASCII SHA256 values = 296.
    prefix = bytes.fromhex('4732444c41593121 01000000 0a000000 0000000000000000 '
                           '01000000 02000000 0200000000000000')
    first_geom = bytes.fromhex('05000000 01000000 01000000 02000000')
    first_point = bytes.fromhex('ffffffff 02000000 03000000 04050601')
    second_point = bytes.fromhex('00000000 00000000 00000000 07080901')
    empty_geom = bytes.fromhex('11000000 ffffffff 00000000 00000000')
    expected = (prefix + hashlib.sha256(scene.encode()).hexdigest().encode()
                + b'a' * 64 + b'b' * 64 + b'c' * 64
                + first_geom + first_point + second_point + empty_geom)
    assert len(expected) == 296 + 16 + 32 + 16
    assert output.read_bytes() == expected


def cpp_view_fixture(tmp_path):
    scene = 'wire_fixture'
    # Packed native composed point: int32 XYZ, RGB/valid bytes, int32 owner.
    payload = bytes.fromhex('ffffffff 00000000 07000000 0a141e01 ffffffff')
    prefix = bytes.fromhex('4732434f4c313021 01000000 0a000000 '
                           '1400000000000000 0100000000000000')
    header = (prefix + hashlib.sha256(scene.encode()).hexdigest().encode()
              + b'a' * 64 + b'b' * 64)
    assert len(header) == 224 and len(payload) == 20
    path = tmp_path / 'native.g2col10.bin'
    path.write_bytes(header + payload)
    snapshot = dict(scene_id=scene, source_sha256='a' * 64, frame_id=20,
                    world_frame='world', entities=[{'id': 'entity_0'}, {'id': 'entity_1'}])
    expected = dict(frame=20, source_scene_id=scene, source_sha256='a' * 64,
                    source_state_sha256='b' * 64, expected_full_color_voxels=1,
                    expected_full_color_sha256=hashlib.sha256(payload).hexdigest(),
                    expected_unknown_owner_cells=1)
    return path, expected, snapshot


def test_cpp_view_bytes_bind_frame_and_roundtrip_to_renderer_contract(tmp_path):
    path, expected, snapshot = cpp_view_fixture(tmp_path)
    surface = read_native_surface(path, expected, snapshot)
    checked = validate_surface_data(surface, snapshot)
    np.testing.assert_allclose(checked[0], [[-.005, .005, .075]], rtol=0, atol=1e-15)
    np.testing.assert_array_equal(checked[1], [[10, 20, 30]])
    assert checked[3].tolist() == [-1]
    assert composed_digest(checked) == (expected['expected_full_color_sha256'], 1, 1)


@pytest.mark.parametrize('fault', ['scene', 'payload', 'trailing', 'invalid_owner'])
def test_native_tensor_refuses_changed_or_semantically_invalid_cpp_bytes(tmp_path, fault):
    path, expected, snapshot = cpp_view_fixture(tmp_path)
    raw = bytearray(path.read_bytes())
    if fault == 'scene':
        raw[32] = ord('0') if raw[32] != ord('0') else ord('1')
    elif fault == 'payload':
        raw[224 + 12] ^= 1
    elif fault == 'trailing':
        raw.extend(b'\x00')
    else:
        raw[-4:] = bytes.fromhex('02000000')  # Two entities: owner index 2 is invalid.
        expected['expected_full_color_sha256'] = hashlib.sha256(raw[224:]).hexdigest()
        expected['expected_unknown_owner_cells'] = 0
    path.write_bytes(raw)
    with pytest.raises(ContractError):
        read_native_surface(path, expected, snapshot)


def sequence_case(tmp_path):
    color = dict(layout=1, source_sha256='a' * 64, states=[])
    nav = dict(source_scene_sha256='a' * 64, source_known_region_NOT_CERTIFIED=True,
               training_ready=False, frames=[])
    for frame in (0, 20):
        files = {}
        for kind in ('color', 'grid', 'objects'):
            path = tmp_path / f'{kind}_{frame}.bin'
            path.write_bytes((kind + str(frame)).encode())
            files[kind] = (str(path), sha_file(path))
        color['states'].append(dict(frame=frame, source_scene_id='wire_fixture',
            source_sha256='a' * 64, source_state_sha256='b' * 64,
            initial_all_static_and_dynamic=frame == 0,
            data_file=files['color'][0], binary_sha256=files['color'][1],
            expected_full_color_sha256='c' * 64, expected_full_color_voxels=1,
            expected_unknown_owner_cells=0))
        nav['frames'].append(dict(frame=frame, source_state_row_sha256='b' * 64,
            source_grid_file=files['grid'][0], source_grid_sha256=files['grid'][1],
            source_objects_file=files['objects'][0], source_objects_sha256=files['objects'][1]))
    return color, nav


def test_sequence_refuses_nav_from_another_state_before_creating_plan(tmp_path):
    color, nav = sequence_case(tmp_path)
    nav['frames'][1]['source_state_row_sha256'] = 'd' * 64
    path = tmp_path / 'sequence.txt'
    with pytest.raises(ContractError, match='state row mismatch'):
        write_sequence(path, color, nav)
    assert not path.exists()


@pytest.mark.parametrize('fault', ['unsupported_layout', 'one_row', 'too_many_composed_voxels'])
def test_sequence_respects_current_native_adapter_limits(tmp_path, fault):
    color, nav = sequence_case(tmp_path)
    if fault == 'unsupported_layout':
        color['layout'] = 0
    elif fault == 'one_row':
        color['states'].pop()
        nav['frames'].pop()
    else:
        color['states'][0]['expected_full_color_voxels'] = 8_000_001
    output = tmp_path / 'sequence.txt'
    with pytest.raises(ContractError):
        write_sequence(output, color, nav)
    assert not output.exists()


def test_truncated_prepared_states_cannot_publish_a_complete_episode(tmp_path, monkeypatch):
    from g2.offline import direct_source, episode
    inputs = tmp_path / 'inputs.json'
    inputs.write_text(json.dumps({'states': [{'frame': 0}, {'frame': 20}]}))
    snapshots = [{'frame_id': 0}, {'frame_id': 20}]
    monkeypatch.setattr(direct_source, 'verify_input_config', lambda _: (None, None, None, snapshots))
    prepared = tmp_path / 'prepared'
    prepared.mkdir()
    colors = dict(complete=True, source_inputs_sha256=sha_file(inputs), frames=[0, 20],
                  complete_episode_states=2, states=[dict(frame=0, state_id=0)])
    (prepared / 'color_manifest.json').write_text(json.dumps(colors))
    native = tmp_path / 'native'
    native.mkdir()
    (native / 'F24_NATIVE_FULL_EPISODE_COMPLETE.json').write_text(json.dumps(dict(
        complete_state_count=2, native_color_full_F22_sha_equal_every_state=True,
        native_dual_map_same_process=True, source_known_region_is_TEST_ONLY_NOT_CERTIFIED=True)))
    output = tmp_path / 'output'
    with pytest.raises(ContractError, match='coverage|incomplete'):
        episode.render(inputs, prepared, native, output, backend='cpu')
    assert not output.exists()


@pytest.mark.parametrize("layout", [1, 2, 4, 10, 11, 42, 99999])
def test_sequence_supports_every_official_robocasa_layout(tmp_path, layout):
    color, nav = sequence_case(tmp_path)
    color["layout"] = layout
    output = tmp_path / "valid_layout.txt"
    result = write_sequence(output, color, nav)
    assert output.is_file()
    assert ("layout %s" % layout) in output.read_text().splitlines()
    assert result == sha_file(output)


@pytest.mark.parametrize("invalid", [0, -1, True, 1.0, "1", None])
def test_sequence_rejects_invalid_official_layout(tmp_path, invalid):
    color, nav = sequence_case(tmp_path)
    color["layout"] = invalid
    with pytest.raises(ContractError):
        write_sequence(tmp_path / "invalid_layout.txt", color, nav)
