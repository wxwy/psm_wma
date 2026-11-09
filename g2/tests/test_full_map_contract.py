"""Full Map profile negatives; actual source/native replay is a separate smoke."""
import pytest

from g2.io import ContractError,write_json
from g2.nav_bridge.full_map import _native_modules,verify_inputs,verify_bundle
from g2.nav_bridge.snapshot import capture,validate_snapshot
from g2.tests.test_connections import connection_case


def full_case():
    s=connection_case();s.update(source_mode='full_map_mujoco_source',geometry_source_mode='FULL_MAP_MUJOCO_SOURCE',
        structure_mode='MUJOCO_FULL_MAP_GT_V1',object_frontend_status='MUJOCO_GT_SOURCE_NOT_MODEL_PREDICTIONS',
        full_map_source={'native_manifest_sha256':'c'*64,'source_proof_sha256':'d'*64,'native_geometry_backend':'ORACLE_GRID',
            'status':'MUJOCO_FULL_MAP_GT_PENDING_HUMAN','model_observation':False,'training_ready':False})
    for e in s['entities']:e['observation_source']='MUJOCO_FULL_MAP_GT'
    return s


def test_gt_profile_needs_no_fabricated_camera_or_ceiling_but_remains_explicit():
    s=full_case();validate_snapshot(s)
    assert s['completed_rgbd_observations']==0 and not any(e['kind']=='ceiling' for e in s['entities'])


@pytest.mark.parametrize('fault',['model_count','model_status','model_stamp','source_mode','backend',
    'missing_manifest','training','model_claim','entity_observation'])
def test_full_map_cannot_be_laundered_into_model_or_sensor_observations(fault):
    s=full_case()
    if fault=='model_count':s['completed_rgbd_observations']=1
    elif fault=='model_status':s['object_frontend_status']='OBSERVED'
    elif fault=='model_stamp':s['last_rgbd_observation_timestamp_ns']=1
    elif fault=='source_mode':s['source_mode']='perception'
    elif fault=='backend':s['full_map_source']['native_geometry_backend']='SENSOR_INCREMENTAL'
    elif fault=='missing_manifest':s['full_map_source']['native_manifest_sha256']=''
    elif fault=='training':s['full_map_source']['training_ready']=True
    elif fault=='model_claim':s['full_map_source']['model_observation']=True
    else:s['entities'][2]['observation_source']='YOLOE'
    with pytest.raises(ContractError):validate_snapshot(s)


def test_normal_capture_does_not_accept_gt_by_a_boolean_or_oracle_flag(tmp_path):
    native=tmp_path/'native';native.mkdir();write_json(native/'snapshot.json',full_case())
    (native/'SNAPSHOT_COMPLETE').write_text('nav_sg_spatial_snapshot_v1\n')
    with pytest.raises(ContractError,match='dedicated source-proof'):
        capture(native,tmp_path/'bundle',allow_oracle_diagnostic=True)
    assert not (tmp_path/'bundle').exists()


def test_arbitrary_source_manifest_flag_and_unpinned_loader_do_not_create_a_proof(tmp_path):
    with pytest.raises(ContractError):verify_inputs({'schema':'fake','source_mode':'FULL_MAP_MUJOCO_SOURCE'})
    path=tmp_path/'g2/gt';path.mkdir(parents=True);(path/'mujoco_scene.py').write_text('# altered code\n')
    with pytest.raises(ContractError,match='version differs'):_native_modules(tmp_path)
    with pytest.raises(ContractError):verify_bundle(tmp_path,{'source_scope':{'status':'MUJOCO_FULL_MAP_GT_PENDING_HUMAN'}})
