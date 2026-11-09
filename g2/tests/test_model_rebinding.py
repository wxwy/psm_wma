"""Own gzip/mesh/state fixtures; no private RoboCasa files or model inference."""
import gzip
import hashlib
from pathlib import Path

import numpy as np
import pytest

from g2.io import ContractError,canonical,digest,write_json
from g2.sim.model_rebinding import create,verify
from g2.sim.source_geometry import apply_state,load_model,model_source_hash
from g2.tests.test_recorded import inputs as recorded_inputs


@pytest.fixture
def model_pair(tmp_path):
    source=tmp_path/'source';source.mkdir();assets=source/'assets';assets.mkdir()
    mesh=assets/'shape.obj';mesh.write_text('v 0 0 0\nv .2 0 0\nv 0 .2 0\nv 0 0 .2\nf 1 3 2\nf 1 2 4\nf 1 4 3\nf 2 3 4\n')
    old='/archive/TEST_ONLY/assets'
    original_xml='<mujoco model="own"><asset><mesh name="shape" file="'+old+'/shape.obj"/></asset><worldbody><geom name="visual" type="mesh" mesh="shape"/></worldbody></mujoco>'
    original=source/'model.xml.gz';original.write_bytes(gzip.compress(original_xml.encode(),mtime=0))
    rebound=source/'scene_rebased.xml';rebound.write_text(original_xml.replace(old,str(assets)))
    states=source/'states.npz';np.savez(states,qpos=np.zeros((201,0)),time=np.arange(201)*.01)
    ep=source/'ep_meta.json';write_json(ep,{'fixtures':{},'object_cfgs':[]})
    return dict(original_gzip=original,rebased_xml=rebound,output=tmp_path/'proof',
        path_prefixes=[{'from':old,'to':str(assets)}],states=states,ep_meta=ep,asset_roots=[assets])


def test_original_gzip_path_rebinding_is_independently_replayed_for_both_frames(model_pair):
    body=create(**model_pair);result=verify(model_pair['output']/'rebinding.json')
    assert result['original_compressed_sha256']==digest(model_pair['original_gzip'])
    assert result['rebased_xml_sha256']==digest(model_pair['rebased_xml'])
    assert result['original_compressed_sha256']!=result['rebased_xml_sha256']
    assert [r['frame_id'] for r in body['frames']]==[0,200]
    assert body['training_ready'] is False and body['historical_generator_revision_certified'] is False


@pytest.mark.parametrize('change',['geometry','material','body','mesh_bytes','states','ep_meta','original','rules'])
def test_changed_source_or_state_cannot_reuse_a_rebinding_proof(model_pair,change):
    create(**model_pair)
    if change=='geometry':
        p=model_pair['rebased_xml'];p.write_text(p.read_text().replace('type="mesh"','type="mesh" pos=".1 0 0"'))
    elif change=='material':
        p=model_pair['rebased_xml'];p.write_text(p.read_text().replace('type="mesh"','type="mesh" rgba="1 0 0 1"'))
    elif change=='body':
        p=model_pair['rebased_xml'];p.write_text(p.read_text().replace('name="visual"','name="other"'))
    elif change=='mesh_bytes':(model_pair['asset_roots'][0]/'shape.obj').write_text('not the original mesh')
    elif change=='states':np.savez(model_pair['states'],qpos=np.zeros((201,0)),time=np.arange(201)*.02)
    elif change=='ep_meta':write_json(model_pair['ep_meta'],{'fixtures':{'new':{}}})
    elif change=='original':model_pair['original_gzip'].write_bytes(gzip.compress(b'<mujoco/>',mtime=0))
    else:
        import json
        path=model_pair['output']/'rebinding.json';value=json.loads(path.read_text())
        value['configuration']['path_prefixes'][0]['from']='/different'
        value.pop('version_sha256');value['version_sha256']=hashlib.sha256(canonical(value)).hexdigest();write_json(path,value)
    with pytest.raises((ContractError,ValueError)):verify(model_pair['output']/'rebinding.json')


def test_recorded_model_identity_is_not_replaced_by_the_rebound_root_hash(model_pair):
    create(**model_pair)
    with pytest.raises(ContractError,match='another original'):
        verify(model_pair['output']/'rebinding.json',recorded_model_sha256=digest(model_pair['rebased_xml']))


def test_prescan_requires_exact_rebound_closure_state_row_and_ep_meta(model_pair):
    create(**model_pair);model,sources=load_model(model_pair['rebased_xml'],model_pair['asset_roots'])
    _,state=apply_state(model,model_pair['states'],0)
    manifest={'frame_id':0,'sources':sources,'source_identity':{'model_source_sha256':model_source_hash(sources)},'state':state,
        'input_files':{'ep_meta':{'sha256':digest(model_pair['ep_meta'])}}}
    verify(model_pair['output']/'rebinding.json',prescan=manifest)
    manifest['state']['row_sha256']='f'*64
    with pytest.raises(ContractError,match='pre-scan source/state'):verify(model_pair['output']/'rebinding.json',prescan=manifest)


@pytest.mark.parametrize('change',['other_frame','other_format','truncated_assets','timestamp','timestamp_source'])
def test_legal_proof_rows_cannot_bless_a_mixed_prescan_frame_or_closure(model_pair,change):
    create(**model_pair);model,sources=load_model(model_pair['rebased_xml'],model_pair['asset_roots'])
    _,state=apply_state(model,model_pair['states'],0)
    manifest={'frame_id':0,'sources':sources,'source_identity':{'model_source_sha256':model_source_hash(sources)},'state':state,
        'input_files':{'ep_meta':{'sha256':digest(model_pair['ep_meta'])}}}
    if change=='other_frame':manifest['state']['frame_id']=200
    elif change=='other_format':manifest['state']['format']='mujoco_fullphysics'
    elif change=='timestamp':manifest['state']['timestamp']=1.5
    elif change=='timestamp_source':manifest['state']['timestamp_source']='claimed_time'
    else:manifest['sources']=[r for r in sources if r['logical_id']=='root.xml']
    with pytest.raises(ContractError):verify(model_pair['output']/'rebinding.json',prescan=manifest)


@pytest.mark.parametrize('rules',[[{'from':'/a','to':'/b'},{'from':'/a/c','to':'/d'}],
    [{'from':'/archive/TEST_ONLY','to':'/escape/../else'}]])
def test_ambiguous_or_noncanonical_path_rules_are_rejected(model_pair,rules):
    model_pair['path_prefixes']=rules
    with pytest.raises(ContractError):create(**model_pair)


def include_pair(pair,tmp_path):
    old=tmp_path/'original_includes';new=pair['rebased_xml'].parent/'rebound_includes'
    old.mkdir();new.mkdir();asset=pair['asset_roots'][0]
    child='<mujocoinclude><asset><mesh name="shape" file="/archive/TEST_ONLY/assets/shape.obj"/></asset><worldbody><geom name="visual" type="mesh" mesh="shape"/></worldbody></mujocoinclude>'
    (old/'part.xml').write_text(child);(new/'part.xml').write_text(child.replace('/archive/TEST_ONLY/assets',str(asset)))
    root='<mujoco><include file="'+str(old/'part.xml')+'"/></mujoco>'
    pair['original_gzip'].write_bytes(gzip.compress(root.encode(),mtime=0))
    pair['rebased_xml'].write_text(root.replace(str(old),str(new)))
    pair['path_prefixes'].append({'from':str(old),'to':str(new)})
    return old,new


def test_original_include_closure_is_transformed_and_compiled_independently(model_pair,tmp_path):
    old,_=include_pair(model_pair,tmp_path);body=create(**model_pair)
    assert len(body['original_xml_closure'])==2
    verify(model_pair['output']/'rebinding.json')
    path=old/'part.xml';path.write_text(path.read_text().replace('name="visual"','name="changed"'))
    with pytest.raises(ContractError):verify(model_pair['output']/'rebinding.json')


def test_output_cannot_overwrite_an_original_include_directory(model_pair,tmp_path):
    old,_=include_pair(model_pair,tmp_path);model_pair['output']=old/'proof'
    with pytest.raises(ContractError,match='overlaps'):create(**model_pair)
    assert not model_pair['output'].exists()


@pytest.mark.parametrize('budget',['xml','asset','state'])
def test_read_budgets_are_enforced_before_loading_oversized_sources(model_pair,monkeypatch,budget):
    from g2.sim import model_rebinding as module
    if budget=='xml':monkeypatch.setattr(module,'XML_BYTE_LIMIT',8)
    elif budget=='asset':monkeypatch.setattr(module,'ASSET_BYTE_LIMIT',8)
    else:
        np.savez_compressed(model_pair['states'],qpos=np.zeros((201,0)),time=np.arange(201)*.01,junk=np.zeros(20000,np.uint8))
        monkeypatch.setattr(module,'CLOSURE_BYTE_LIMIT',1000)
    with pytest.raises(ContractError,match='budget'):create(**model_pair)
    assert not model_pair['output'].exists()


def test_recorded_adapter_accepts_replayed_gzip_derivation_but_keeps_default_hash_strict(model_pair,recorded_inputs):
    from g2.nav_bridge.recorded import prepare
    from g2.io import read_json
    create(**model_pair);manifest,grid,kwargs=recorded_inputs;m=read_json(manifest)
    model,sources=load_model(model_pair['rebased_xml'],model_pair['asset_roots']);_,state=apply_state(model,model_pair['states'],0)
    m.update(sources=sources,state=state,input_files={'ep_meta':{'sha256':digest(model_pair['ep_meta'])}})
    m['source_identity']['model_source_sha256']=model_source_hash(sources)
    m['visual_source_sha256']=hashlib.sha256(canonical(m['source_identity'])).hexdigest();write_json(manifest,m)
    cache=kwargs['dataset_root']/kwargs['episode']/'manifest.json';cached=read_json(cache)
    original={'model.xml.gz':model_pair['original_gzip'],'states.npz':model_pair['states'],'ep_meta.json':model_pair['ep_meta']}
    for record in cached['identity']['source_files']:record['sha256']=digest(original[Path(record['path']).name])
    write_json(cache,cached)
    with pytest.raises(ContractError,match='different source model'):prepare(manifest,grid,**kwargs)
    prepare(manifest,grid,model_rebinding_proof=model_pair['output']/'rebinding.json',**kwargs)
    binding=read_json(kwargs['output']/'recorded_binding.json')
    assert binding['original_sources']['model.xml.gz']==digest(model_pair['original_gzip'])
    assert binding['model_source_derivation']['rebased_xml_sha256']==digest(model_pair['rebased_xml'])


def test_legal_missing_qpos_time_is_preserved_without_inventing_a_source_clock(model_pair):
    np.savez(model_pair['states'],qpos=np.zeros((201,0)))
    create(**model_pair);model,sources=load_model(model_pair['rebased_xml'],model_pair['asset_roots'])
    _,state=apply_state(model,model_pair['states'],0)
    manifest={'frame_id':0,'sources':sources,'source_identity':{'model_source_sha256':model_source_hash(sources)},
        'state':state,'input_files':{'ep_meta':{'sha256':digest(model_pair['ep_meta'])}}}
    assert state['timestamp'] is None and state['timestamp_source']=='missing'
    verify(model_pair['output']/'rebinding.json',prescan=manifest)
    manifest['state']['timestamp']=0.
    with pytest.raises(ContractError):verify(model_pair['output']/'rebinding.json',prescan=manifest)


def test_oversized_include_is_rejected_before_either_original_or_target_is_hashed(model_pair,tmp_path,monkeypatch):
    from g2.sim import model_rebinding as module
    old,new=include_pair(model_pair,tmp_path)
    for folder in (old,new):
        path=folder/'part.xml';path.write_text(path.read_text()+' '*4096)
    monkeypatch.setattr(module,'XML_BYTE_LIMIT',1024);original_digest=module.digest
    def guarded(path):
        if Path(path).name=='part.xml':raise AssertionError('oversized include must not be hashed')
        return original_digest(path)
    monkeypatch.setattr(module,'digest',guarded)
    with pytest.raises(ContractError,match='budget'):create(**model_pair)
