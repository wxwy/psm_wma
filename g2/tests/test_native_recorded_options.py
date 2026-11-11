"""Own transport/plan fixtures; no real source review or model inference."""
import hashlib

import numpy as np
import pytest

from g2.io import ContractError,canonical,digest,read_json,write_json
from g2.nav_bridge.recorded import prepare
from g2.sim.source_scope import DECLARED_SCOPE,audit_summary
from g2.sim.texture_projection import REASONS
from g2.tests.test_recorded import inputs


@pytest.fixture
def partial_inputs(inputs):
    manifest,grid,kwargs=inputs;m=read_json(manifest);root=manifest.parent
    cloud=root/'precolored.txt'
    cloud.write_text('NAV_SG_PRECOLORED_CLOUD_V1\nscene_id "TEST_ONLY_house"\nsource_sha256 '+
        'a'*64+'\nframe_id 0\nworld_frame "world"\npoints 2\ndata\n0 0 0 10 20 30 1\n1 0 0 0 0 0 0\n')
    reason=next(i for i in REASONS if i!=0)
    audit=root/'color_audit.npz'
    np.savez_compressed(audit,geom_id=np.array([0,0]),local_face_id=np.array([0,1]),
        reason_code=np.array([0,reason]),input_triangle_area_weight_m2=np.array([1.,1.]))
    coverage={'sampled_points':2,'color_valid_points':1,'color_invalid_points':1,'color_valid_fraction':.5,
        'retained_input_face_count':2,'evaluated_retained_face_count':2,'evaluated_retained_face_fraction':1,
        'continuous_surface_color_coverage_certified':False,'invalid_point_reason_counts':{REASONS[reason]:1},
        'sampled_input_triangle_area_m2':2.,'area_weighted_valid_sample_fraction':.5}
    rows=[{'geom_id':0,'geom_name':'TEST_ONLY_visual','role':'visual','color_status':'UNSUPPORTED_APPEARANCE',
        'surface_points':2,'source':{'kind':'mjcf'},'classification_reason':'TEST_ONLY_EXPLICIT_FIXTURE',
        'geometry_type':'capsule','appearance':{'mode':'TEST_ONLY','unsupported':REASONS[reason]},
        'color_coverage':coverage,'sampling':{'input_face_count':2,'retained_face_count':2,
            'discarded_zero_area_face_ids':[]}}]
    m['source_identity']['color_evidence_protocol']='g2_sample_color_audit_v1'
    m.update(status='PARTIAL_COLOR',completion_scope=DECLARED_SCOPE,training_ready=False,
        compiled_geom_count=1,unclassified_geom_count=0,geom_audit=rows,
        geom_audit_sha256=hashlib.sha256(canonical(rows)).hexdigest(),source_audit=audit_summary(rows),
        visual_source_sha256=hashlib.sha256(canonical(m['source_identity'])).hexdigest(),point_count=2,
        file={'path':cloud.name,'bytes':cloud.stat().st_size,'sha256':digest(cloud)},
        color_audit_file={'path':audit.name,'bytes':audit.stat().st_size,'sha256':digest(audit)},
        color_reason_codes={str(k):v for k,v in REASONS.items()})
    write_json(manifest,m);(root/'COMPLETE').unlink()
    kwargs.update(allow_partial_color=True,native_structures=True)
    return manifest,grid,kwargs


@pytest.mark.parametrize('backend',['gvd','esdf_grid'])
def test_explicit_partial_color_plan_keeps_masks_model_dependency_and_uncertainty(partial_inputs,backend):
    manifest,grid,kwargs=partial_inputs;kwargs['room_source']=backend
    p=prepare(manifest,grid,**kwargs)
    assert p['status']=='DIAGNOSTIC_SUBSET_PLAN_ONLY_NOT_EXECUTED'
    assert p['appearance_status']=='PARTIAL_COLOR' and p['invalid_colors_preserved'] is True
    assert p['full_scene_source_certified'] is False and p['training_ready'] is False
    assert '--native-structures' in p['replay_argv']
    assert p['replay_argv'][p['replay_argv'].index('--native-room-source')+1]==backend
    assert '--sidecar' in p['replay_argv'] and p['blocked_without']=='REAL_RECORDED_RGBD_POSE_AND_MODEL_OBSERVATIONS'
    binding=read_json(kwargs['output']/'recorded_binding.json')
    assert binding['color_audit_sha256']==digest(manifest.parent/'color_audit.npz')
    assert not (manifest.parent/'COMPLETE').exists() and not (kwargs['output']/'native_run').exists()


@pytest.mark.parametrize('fault',['not_opted','not_subset','full_review','fake_complete','unknown_role','bad_mask','bad_audit'])
def test_partial_color_cannot_be_promoted_or_lose_its_point_evidence(partial_inputs,fault):
    manifest,grid,kwargs=partial_inputs;m=read_json(manifest)
    if fault=='not_opted':kwargs['allow_partial_color']=False
    elif fault=='not_subset':kwargs['allow_declared_subset']=False
    elif fault=='full_review':kwargs['full_scene_review']='TEST_ONLY_NEVER_READ_REVIEW'
    elif fault=='fake_complete':(manifest.parent/'COMPLETE').write_text('VISUAL_SURFACE_EXPORT_ONLY\n')
    elif fault=='unknown_role':m['unclassified_geom_count']=1
    elif fault=='bad_audit':(manifest.parent/'color_audit.npz').write_bytes(b'corrupted')
    elif fault=='bad_mask':
        cloud=manifest.parent/'precolored.txt';cloud.write_text(cloud.read_text().replace('1 0 0 0 0 0 0','1 0 0 0 0 0 1'))
        m['file'].update(bytes=cloud.stat().st_size,sha256=digest(cloud))
    write_json(manifest,m)
    with pytest.raises(ContractError):prepare(manifest,grid,**kwargs)
    assert not kwargs['output'].exists()


def test_native_structure_plan_is_explicit_and_legacy_plan_remains_off(inputs):
    manifest,grid,kwargs=inputs;p=prepare(manifest,grid,**kwargs)
    assert '--native-structures' not in p['replay_argv'] and p['native_structures_enabled'] is False


@pytest.mark.parametrize('fault',['hidden_unknown','duplicate_id','duplicate_name'])
def test_partial_inventory_cannot_relabel_unresolved_or_duplicate_components(partial_inputs,fault):
    manifest,grid,kwargs=partial_inputs;m=read_json(manifest)
    row={'geom_id':1,'geom_name':'TEST_ONLY_excluded','role':'auxiliary','color_status':'EXCLUDED_AUXILIARY',
        'surface_points':0,'source':{'kind':'mjcf'},'classification_reason':'TEST_ONLY'}
    if fault=='hidden_unknown':row.update(role='UNCLASSIFIED',color_status='EXCLUDED_UNCLASSIFIED',source={'kind':'unclassified'})
    elif fault=='duplicate_id':row['geom_id']=0
    elif fault=='duplicate_name':row['geom_name']=m['geom_audit'][0]['geom_name']
    m['geom_audit'].append(row);m['compiled_geom_count']=2
    m['geom_audit_sha256']=hashlib.sha256(canonical(m['geom_audit'])).hexdigest()
    m['source_audit']=audit_summary(m['geom_audit']);write_json(manifest,m)
    with pytest.raises(ContractError):prepare(manifest,grid,**kwargs)
    assert not kwargs['output'].exists()


@pytest.mark.parametrize('flag',['allow_partial_color','allow_declared_subset','native_structures'])
def test_string_false_never_enables_a_replay_opt_in(partial_inputs,flag):
    manifest,grid,kwargs=partial_inputs;kwargs[flag]='false'
    with pytest.raises(ContractError,match='booleans'):prepare(manifest,grid,**kwargs)
