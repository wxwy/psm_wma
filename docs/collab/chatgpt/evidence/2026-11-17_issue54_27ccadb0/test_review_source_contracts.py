"""Independent synthetic regressions matching observed source layouts.

These use invented names/text, not server private data. A failing assertion is
expected on 27ccadb0 and must become green on a corrected fixed candidate.
"""
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from g2.offline.language_context import load_flat_captions
from g2.offline.task_entities import bind_task_entities


def entity(eid, source, part='whole'):
    return dict(id=eid, source_instance_id=source, source_part_id=part)


def test_string_index_tasks_parquet_is_authoritative(tmp_path):
    original = 'Synthetic task: put the cup on the shelf.'
    (tmp_path / 'meta').mkdir()
    (tmp_path / 'data/chunk-000').mkdir(parents=True)
    # This is the actual flat table layout: integer task_index, string index.
    pq.write_table(pa.table({'task_index': [7], '__index_level_0__': [original]}),
                   tmp_path / 'meta/tasks.parquet')
    pq.write_table(pa.table({'episode_index': [9, 9], 'frame_index': [0, 1],
                            'task_index': [7, 7]}),
                   tmp_path / 'data/chunk-000/file-000.parquet')
    captions, authority = load_flat_captions(tmp_path, episode_id=9,
        frames=[0, 1], ep_meta_lang=original)
    assert captions[0]['original_text'] == original
    assert captions[1]['task_index'] == 7
    assert authority['authority'] == 'FLAT_FRAME_TASK_INDEX_TO_META_TASKS_PARQUET'


def test_close_blender_lid_binds_independent_auxiliary_fixture():
    metadata = dict(
        fixtures={
            'blender_A': {'cls': 'Blender'},
            'blender_A_aux': {'cls': 'BlenderLid'},
        },
        fixture_refs={}, object_cfgs=[],
    )
    graph = dict(entities=[
        entity('body_A', 'fixture:blender_A'),
        entity('lid_A', 'fixture:blender_A_aux'),
    ])
    result = bind_task_entities('CloseBlenderLid', metadata, graph)
    assert result['binding_status'] == 'BOUND'
    assert {'body_A', 'lid_A'} <= set(result['entity_ids']), (
        'The manipulated lid is a distinct source instance, not a blender part',
        result['entity_ids'],
    )


def test_counter_to_stove_binds_named_source_container():
    metadata = dict(
        fixtures={'stove_A': {'cls': 'Stove'}, 'counter_A': {'cls': 'Counter'}},
        fixture_refs={'stove': 'stove_A', 'counter': 'counter_A'},
        object_cfgs=[
            {'name': 'obj', 'info': {'cat': 'apple'}},
            {'name': 'container', 'info': {'cat': 'pan'}},
            {'name': 'obj_container', 'info': {'cat': 'plate'}},
            {'name': 'distr', 'info': {'cat': 'cup'}},
        ],
        lang='Pick the apple from the plate and place it in the pan.',
    )
    graph = dict(entities=[
        entity('stove_A', 'fixture:stove_A'),
        entity('counter_A', 'fixture:counter_A'),
        entity('apple_A', 'object:obj'),
        entity('pan_A', 'object:container'),
        entity('plate_A', 'object:obj_container'),
        entity('distr_A', 'object:distr'),
    ])
    result = bind_task_entities('PickPlaceCounterToStove', metadata, graph)
    assert result['binding_status'] == 'BOUND'
    assert {'apple_A', 'pan_A', 'plate_A'} <= set(result['entity_ids']), (
        'A named source-container role is missing but binding is BOUND',
        result['entity_ids'],
    )
    assert 'distr_A' not in result['entity_ids']
