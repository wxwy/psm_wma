"""Causal native color trace and six-view policies, using only own fixtures."""
import copy
from pathlib import Path
import pytest
from g2.io import ContractError,write_json
from g2.nav_bridge.observed_color import check_worker
from g2.tests.test_connections import connection_case
from g2.views.render_connections import render_v2


def trace_case():
    b={'projection_provider':'depth','voxel_leaf_m':.02,'frames':[{'frame_id':0,'header_seq':1,'timestamp_ns':100,'rgb_sha256':'a'*64,
        'depth_sha256':'b'*64,'pose_sha256':'c'*64,'intrinsics':[5.,5.,2.,2.,4.,4.,1.],
        'rgb_encoding':'rgb8','depth_encoding':'32FC1','rgb_layout':[4,4,12,0],'depth_layout':[4,4,16,0]}]}
    r=dict(b['frames'][0]);r.update(sequence=1,source_header_seq=1,rgb_stamp_ns=100,depth_stamp_ns=100,pose_stamp_ns=100,
        outcome='INTEGRATED',input_wall_ns=1,dequeue_wall_ns=2,projection_start_wall_ns=3,projection_end_wall_ns=4,
        integration_start_wall_ns=5,integration_end_wall_ns=6,finish_wall_ns=7)
    w={'projection_provider':'depth','schema':'nav_sg_color_worker_metrics_v1','enabled':True,'trace_truncated':False,'voxel_leaf_m':.02,
        'last_integrated_stamp_ns':100,'received':1,'dequeued':1,'integrated':1,'skipped':0,'overwritten_pending':0,
        'rejected_enqueue':0,'cleared_pending':0,'stopped_pending':0,'pending':False,'frames':[r]}
    return w,b


def test_native_trace_closes_against_actual_recorded_prefix():
    w,b=trace_case();assert check_worker(w,b,0,100)==w['frames'][0]


@pytest.mark.parametrize('fault',['rgb_sha256','depth_sha256','pose_sha256','intrinsics','rgb_stamp_ns',
    'depth_stamp_ns','pose_stamp_ns','source_header_seq','outcome','clock','received','integrated','dequeued',
    'overwritten_pending','cleared_pending','stopped_pending','rejected_enqueue','pending','trace_truncated','voxel_leaf_m','rgb_layout','depth_layout'])
def test_bad_native_color_trace_rejected(fault):
    w,b=trace_case()
    if fault in w:w[fault]=True if fault in ('pending','trace_truncated') else w[fault]+1
    elif fault=='clock':w['frames'][0]['integration_end_wall_ns']=2
    else:w['frames'][0][fault]='PENDING' if fault=='outcome' else [1]*4 if fault.endswith('_layout') else [0]*7 if fault=='intrinsics' else 200 if fault.endswith('_ns') or fault=='source_header_seq' else 'd'*64
    with pytest.raises(ContractError):check_worker(w,b,0,100)


def own_surface(root,s):
    root.mkdir();lines=['x,y,z,red,green,blue,color_valid,entity_id']
    # Observe all vertices for a fixture, not an inference/source acceptance.
    for e in s['entities']:
        for p in e['vertices']:lines.append(','.join(map(str,[*p,200,40,30,1,e['id']])))
    (root/'surfaces.csv').write_text('\n'.join(lines)+'\n')
    return len(lines)-1


def test_floor_wall_only_direction_skips_all_png_but_retains_six_metadata(tmp_path):
    s=connection_case();root=tmp_path/'bundle';n=own_surface(root,s)
    m={'surface_points':n,'version_sha256':'f'*64,'source_scope':{'status':'MUJOCO_GT_STRUCTURE_NATIVE_RGBD_COLOR_PENDING_HUMAN'}}
    s['surface_color_source']='NATIVE_RGBD_FUSION_ONLY'
    result=render_v2(root,m,s,tmp_path/'views',meters_per_pixel=.2)
    v=result['views']['rooms/0/plus_X']
    assert v['status']=='SKIPPED_NO_PROJECTABLE_OBJECT' and not v['image_generated']
    assert not (tmp_path/'views/rooms/0/plus_X/rgb.png').exists()
    assert len(result['room_six_refs']['0']['missing_view_mask'])==6
    assert result['views']['rooms/0/floor_top']['status']=='OBSERVED_PARTIAL_RGBD'
    assert (tmp_path/'views/rooms/0/floor_top/rgb.png').exists()
    assert result['training_ready'] is False


def test_asset_color_is_unknown_observation_never_an_empty_room(tmp_path):
    s=connection_case();root=tmp_path/'bundle';n=own_surface(root,s)
    s['surface_color_source']='MUJOCO_SOURCE_SURFACES_WITH_ORIGINAL_INVALID_MASK'
    result=render_v2(root,{'surface_points':n,'version_sha256':'f'*64,'source_scope':{}},s,tmp_path/'views',meters_per_pixel=.2)
    v=result['views']['rooms/0/floor_top']
    assert v['status']=='UNKNOWN_NOT_OBSERVED' and v['projectable_object_geometry'] is True
    assert not list((tmp_path/'views').rglob('*.png'))
    assert result['views']['rooms/0/plus_X']['status']=='SKIPPED_NO_PROJECTABLE_OBJECT'


def test_duplicate_binding_tail_cannot_replace_past_input_with_future_payload():
    w,b=trace_case();b['frames'].append(copy.deepcopy(b['frames'][0]));b['frames'][-1]['rgb_sha256']='d'*64
    w['frames'][0]['rgb_sha256']='d'*64
    with pytest.raises(ContractError,match='unique ordered'):check_worker(w,b,0,100)


def test_model_witness_cannot_certify_legacy_prescan_color(tmp_path):
    s=connection_case();s['source_mode']='perception';root=tmp_path/'bundle';n=own_surface(root,s)
    s['native_structures']={'boundary_coverage_complete':True,'known_object_height_coverage':True}
    for e in s['entities']:
        if e['kind']=='object':e.update(connection_role_status='SOURCE_BOUND_NATIVE_OBJECT' if e['connection_relay_allowed'] else
            'SOURCE_BOUND_NATIVE_ROBOT_NO_RELAY',connection_role_evidence_sha256='e'*64)
    m={'surface_points':n,'version_sha256':'f'*64,'source_scope':{},'semantic_stage':'REAL_RECORDED_INPUT_OBSERVED',
        'observation_witness':{'source':'TEST_ONLY_MODEL_WITNESS_WITH_MIXED_OLD_COLORS'}}
    result=render_v2(root,m,s,tmp_path/'views',meters_per_pixel=.2)
    assert result['views']['rooms/0/floor_top']['status']=='UNKNOWN_NOT_OBSERVED'
    assert not list((tmp_path/'views').rglob('rgb.png'))


def test_same_owner_depth_tolerance_cannot_paint_opposite_thin_face():
    import numpy as np
    from g2.views.render import rasterize
    # Observe +X face only; +X view looks at the unobserved -X face.
    xyz=np.asarray([[.02,.5,.5]]);rgb=np.asarray([[200,40,30]],np.uint8);valid=np.asarray([True]);owners=np.asarray([0])
    from g2.tests.conftest import box
    vertices,triangles=box([0,0,0],[.02,1,1]);mesh=[(0,vertices,triangles)]
    front=rasterize(xyz,rgb,valid,owners,{0},[0,0,0],[.02,1,1],'-X',meters_per_pixel=.1,meshes=mesh,surface_tolerance=0.)
    back=rasterize(xyz,rgb,valid,owners,{0},[0,0,0],[.02,1,1],'+X',meters_per_pixel=.1,meshes=mesh,surface_tolerance=0.)
    assert front[1].sum()==1 and back[1].sum()==0


def test_ab_comparison_requires_same_inputs_build_and_nonempty_capture_set():
    from g2.views.color_ab_report import compare
    rows=[{'leaf_m':leaf,'scene_id':'TEST_ONLY','common_inputs_sha256':'a'*64,'base_params_sha256':'b'*64,
        'native_build_source_sha256':'c'*64,'requested_view_source_hz':1.,'integrated_source_frame_ids':[0,1],
        'navigation_evidence':{'0':{'geometry_grid.raw':'d'*64,'native_scene_graph.json':'e'*64}},
        'requested_capture_count':1,'successful_capture_count':1} for leaf in (.05,.02,.01)]
    assert compare(rows)['comparison_complete'] is True
    for key in ('common_inputs_sha256','base_params_sha256','native_build_source_sha256'):
        bad=copy.deepcopy(rows);bad[1][key]='f'*64
        with pytest.raises(ContractError):compare(bad)
    for empty in (False,True):
        bad=copy.deepcopy(rows)
        for row in (bad if empty else [bad[0]]):row['navigation_evidence']={};row['requested_capture_count']=0;row['successful_capture_count']=0
        with pytest.raises(ContractError):compare(bad)


@pytest.mark.parametrize('provider',['lidar','lidar_fov','unknown'])
def test_lidar_payload_cannot_be_certified_as_rgbd(provider):
    w,b=trace_case();w['projection_provider']=provider;b['projection_provider']=provider
    with pytest.raises(ContractError,match='telemetry'):check_worker(w,b,0,100)
