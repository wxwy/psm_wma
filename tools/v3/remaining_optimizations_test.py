"""Standalone CPU contracts. These are not real-Cosmos, LeRobot or GPU Gates."""
from __future__ import annotations

import dataclasses
import hashlib
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from cosmos_framework.data.generator.action.utils.cached_pixel_geometry import (
    CachedGeometryResize, SOURCE_SHAPE, cached_pixel_placeholder, compact_cached_video_enabled,
    is_pixel_shape_proxy, move_cached_native_batch, pixel_shape_proxy,
)
from cosmos_framework.utils.singleflight_cache import SingleFlightLRU
from cosmos_framework.utils.training_audit import ConsumerAudit, fast_state_fingerprint, memory_inventory
from cosmos_framework.utils.rollout_evidence import atomic_json, run_recorded_episode, save_partial_video
from v3_evaluation_identity import claim_evaluation_run, screening_metrics, validate_task_results


def test_compact_shape_and_storage_not_logical_megabytes():
    view = cached_pixel_placeholder(compact=True)
    assert view.shape == SOURCE_SHAPE
    assert view.numel() == 6684672
    assert view.untyped_storage().nbytes() == 1
    assert is_pixel_shape_proxy(view)
    assert view.dtype == torch.uint8 and not view.any()


def test_sample_storage_never_aliases_another_sample():
    a, b = pixel_shape_proxy(SOURCE_SHAPE), pixel_shape_proxy(SOURCE_SHAPE)
    assert a.untyped_storage().data_ptr() != b.untyped_storage().data_ptr()
    a[0, 0, 0, 0] = 7
    assert not is_pixel_shape_proxy(a)
    assert b[0, 0, 0, 0].item() == 0


@pytest.mark.parametrize('shape', [(3,16,256,512),(3,17,0,512),(3,17,256),(1,3,17,256,512),(3,17,True,512)])
def test_invalid_proxy_geometry_rejected(shape):
    with pytest.raises(ValueError): pixel_shape_proxy(shape)


@pytest.mark.parametrize('value,expected', [('0',False),('1',True)])
def test_compact_switch(value,expected,monkeypatch):
    monkeypatch.setenv('PSM_V3_COMPACT_CACHED_VIDEO',value)
    assert compact_cached_video_enabled() is expected


@pytest.mark.parametrize('value',['true','-1','2',''])
def test_invalid_compact_switch(value,monkeypatch):
    monkeypatch.setenv('PSM_V3_COMPACT_CACHED_VIDEO',value)
    with pytest.raises(ValueError): compact_cached_video_enabled()


def _sample():
    return {'video':pixel_shape_proxy(SOURCE_SHAPE),'video_latent':torch.ones(5,48,12,20),
            'cached_latent_required':True,'action':torch.arange(17*15).reshape(17,15)}


def test_geometry_stage_has_no_pixel_resize_and_preserves_latent_action_rng():
    def forbidden(*args): raise AssertionError('dense resize called')
    stage=CachedGeometryResize(forbidden,(192,320,160,320))
    sample=_sample(); latent=sample['video_latent']; action=sample['action']
    py,pt=random.getstate(),torch.get_rng_state().clone()
    result=stage(sample,None)
    assert result is sample and result['video_latent'] is latent and result['action'] is action
    assert result['image_size'].tolist()==[192,320,160,320]
    assert result['video'].shape==(3,17,192,320)
    assert result['video'].untyped_storage().nbytes()==1
    assert random.getstate()==py and torch.equal(pt,torch.get_rng_state())


@pytest.mark.parametrize('bad', ['missing_latent','false_marker','wrong_resolution','poisoned'])
def test_compact_stage_fail_closed(bad):
    stage=CachedGeometryResize(lambda a,b:a,(192,320,160,320)); sample=_sample();resolution=None
    if bad=='missing_latent': del sample['video_latent']
    if bad=='false_marker': sample['cached_latent_required']=False
    if bad=='wrong_resolution': resolution=256
    if bad=='poisoned': sample['video'][0,0,0,0]=1
    with pytest.raises(ValueError):stage(sample,resolution)


def test_noncache_dense_calls_original_once():
    calls=[]
    stage=CachedGeometryResize(lambda a,b:calls.append((a,b)) or a,(192,320,160,320))
    item={'video':torch.zeros(3,17,8,8,dtype=torch.uint8)}
    assert stage(item,'256') is item and calls==[(item,'256')]


def _batch():
    return {'video':[[pixel_shape_proxy((3,17,192,320))]],
            'video_latent':[torch.ones(1,5,48,12,20)],
            'cached_latent_required':[torch.tensor([True])],
            'image_size':[torch.tensor([[192.,320.,160.,320.]])],
            'action':[[torch.ones(17,64)]]}


def test_compact_video_is_excluded_from_recursive_device_transfer():
    batch=_batch();calls=[]
    def move(value,**kwargs):
        assert 'video' not in value
        calls.append(kwargs)
        return dict(value)
    actual=move_cached_native_batch(batch,device='cuda:0',move=move)
    assert actual['video'] is batch['video'] and actual['video'][0][0].device.type=='cpu'
    assert actual['video_latent'][0] is batch['video_latent'][0]
    assert len(calls)==1 and calls[0]['device']=='cuda:0'


@pytest.mark.parametrize('kind',['marker','count','latent','size','fractional_size','mixed'])
def test_bad_compact_batch_rejected_before_transfer(kind):
    batch=_batch()
    if kind=='marker': batch['cached_latent_required']=[torch.tensor([False])]
    if kind=='count':batch['video_latent']=[]
    if kind=='latent':batch['video_latent']=[torch.ones(1,4,48,12,20)]
    if kind=='size':batch['image_size']=[torch.tensor([256,320,160,320])]
    if kind=='fractional_size':batch['image_size']=[torch.tensor([192.1,320,160,320])]
    if kind=='mixed':batch['video'].append([torch.zeros(3,17,192,320,dtype=torch.uint8)])
    with pytest.raises(ValueError):move_cached_native_batch(batch,device='cuda',move=lambda *a,**k:pytest.fail('transfer'))


def test_legacy_dense_transfer_unchanged():
    batch={'video':[[torch.zeros(3,17,4,4,dtype=torch.uint8)]]};calls=[]
    result=move_cached_native_batch(batch,device='cpu',move=lambda x,**k:calls.append(x) or x)
    assert result is batch and calls==[batch]


def test_singleflight_one_load_for_four_readers():
    cache=SingleFlightLRU(max_entries=8,max_bytes=4096,sizeof=len)
    release=threading.Event();entered=threading.Event();calls=[]
    def load():
        calls.append(1);entered.set();assert release.wait(3);return b'abc'
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures=[pool.submit(cache.get,'episode',load) for _ in range(4)]
        try:
            assert entered.wait(1)
            deadline=time.monotonic()+2
            while cache.stats()['coalesced']<3 and time.monotonic()<deadline:time.sleep(.001)
            assert cache.stats()['coalesced']==3
        finally:release.set()
        assert [f.result(timeout=3) for f in futures]==[b'abc']*4
    assert calls==[1] and cache.stats()['loads']==1
    assert cache.get('episode',lambda:pytest.fail('load'))==b'abc'


def test_different_keys_load_in_parallel():
    cache=SingleFlightLRU(max_entries=2,max_bytes=8,sizeof=len);barrier=threading.Barrier(2)
    def load():barrier.wait(timeout=2);return b'ab'
    with ThreadPoolExecutor(2) as pool:
        futures=[pool.submit(cache.get,k,load) for k in ('a','b')]
        assert [f.result(timeout=3) for f in futures]==[b'ab']*2


def test_cache_enforces_entry_and_byte_budgets_and_oversize():
    c=SingleFlightLRU(max_entries=2,max_bytes=5,sizeof=len)
    c.get('a',lambda:b'aa');c.get('b',lambda:b'bb');c.get('c',lambda:b'cccc')
    assert c.stats()['cached_entries']==1 and c.stats()['cached_bytes']==4
    assert c.stats()['evictions']==2
    assert c.get('big',lambda:b'x'*100)==b'x'*100
    assert c.stats()['cached_bytes']==4 and c.stats()['oversized']==1


def test_failed_load_not_cached_or_swallowed():
    c=SingleFlightLRU(max_entries=2,max_bytes=5,sizeof=len)
    def bad():raise OSError('disk read failed')
    with pytest.raises(OSError):c.get('a',bad)
    assert c.stats()['inflight_keys']==0 and c.stats()['failures']==1
    assert c.get('a',lambda:b'ok')==b'ok'


@pytest.mark.parametrize('n,b',[(-1,2),(True,2),(1,0),(1,False)])
def test_invalid_cache_limits(n,b):
    with pytest.raises(ValueError):SingleFlightLRU(max_entries=n,max_bytes=b,sizeof=len)


@dataclasses.dataclass(frozen=True)
class Identity:
    slot_id:int
    episode_id:str

@dataclasses.dataclass(frozen=True)
class Provenance:
    digest:str


def test_fast_fingerprint_reproducible_sensitive_readonly():
    state=(torch.tensor([1.,2.],requires_grad=True),torch.tensor([3.]))
    record=(Identity(0,'ep'),Provenance('source'),state)
    before=[v.clone() for v in state]
    a=fast_state_fingerprint([record]);b=fast_state_fingerprint([record])
    assert a==b and all(torch.equal(x,y) for x,y in zip(state,before))
    assert state[0].grad is None
    changed=(Identity(0,'ep'),Provenance('source'),(state[0]+1,state[1]))
    assert fast_state_fingerprint([changed])!=a


def test_memory_inventory_uses_storage_without_inventing_activation_bytes():
    model=torch.nn.Linear(4,2);optimizer=torch.optim.Adam(model.parameters())
    model(torch.ones(1,4)).sum().backward();optimizer.step()
    info=memory_inventory(model,optimizer)
    assert info['parameters_storage_bytes']==40 and info['gradients_storage_bytes']==40
    assert info['optimizer_storage_bytes']>0
    assert 'activation_bytes' not in info


def test_consumer_audit_counts_only_observed_trace(monkeypatch):
    monkeypatch.setenv('PSM_V3_STATE_AUDIT_EVERY','0')
    audit=ConsumerAudit()
    payload={'task_class':'CloseFridge','episode_index':2,'start_frame':3,
             'source_binding_digest':'a','cache_corpus_digest':'b'}
    audit.observe('native_forward',{'iteration':800,'member':0,'index':0,'payloads':[payload]},None)
    trainer=SimpleNamespace(_grouped_window=SimpleNamespace(plan=None))
    report=audit.report(trainer,800)
    assert report['task_consumer_counts_rank_local']=={'CloseFridge':1}
    assert report['task_exposure_start_iteration']==801
    assert report['state_fingerprint_sampled'] is False
    assert audit.report(trainer,800)['consumer_audit_status']=='NO_NEW_CONSUMER_TRACE'


def _manifest(seed=0,R=16):
    identity={'checkpoint':'fixture','protocol':{'seed':seed,'R':R}}
    digest=hashlib.sha256(json.dumps(identity,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False).encode()).hexdigest()
    return {'identity':identity,'digest':digest}


def test_evaluation_manifest_requires_same_exact_identity(tmp_path):
    first=_manifest();digest=claim_evaluation_run(tmp_path,first,resume=False)
    assert claim_evaluation_run(tmp_path,first,resume=True)==digest
    with pytest.raises(FileExistsError):claim_evaluation_run(tmp_path,first,resume=False)
    for other in [_manifest(seed=1),_manifest(R=4)]:
        with pytest.raises(ValueError):claim_evaluation_run(tmp_path,other,resume=True)


def test_legacy_results_are_not_silently_adopted(tmp_path):
    (tmp_path/'results.json').write_text('[]')
    with pytest.raises(ValueError):claim_evaluation_run(tmp_path,_manifest(),resume=True)


def _row(ep=0,digest='digest',outcome='success'):
    return {'ep':ep,'evaluation_run_digest':digest,'policy':outcome=='success',
            'outcome':outcome,'error':'bad' if outcome=='runtime_error' else None}


def test_result_validation_accepts_typed_runtime_failures():
    validate_task_results([_row(),_row(1,outcome='runtime_error')],digest='digest',expected_trials=2)


@pytest.mark.parametrize('rows',[[],[_row(digest='foreign')],[_row(1)],[_row(),_row()]])
def test_foreign_incomplete_or_duplicate_results_rejected(rows):
    with pytest.raises(ValueError):validate_task_results(rows,digest='digest',expected_trials=1)


def test_partial_screening_never_reports_a_complete_sr():
    results={'a':{'trials':1,'successes':1,'error':None}}
    report=screening_metrics(results,tasks=['a','b'],expected_trials=1)
    assert report['sr'] is None and report['partial_sr']==1 and report['missing_tasks']==['b']
    results['b']={'trials':1,'successes':0,'error':'runtime'}
    report=screening_metrics(results,tasks=['a','b'],expected_trials=1)
    assert report['sr']==.5 and report['task_failures']==1


def test_runtime_error_preserves_completed_actions_and_prediction(tmp_path):
    def runner(env,on_prediction,on_action,**kw):
        on_prediction({'action':[[1]*15],'local_memory':{'consumer_step':0}},12.)
        on_action({'source_step':0,'submitted_env12':[0]*12,'canonical_executed_raw15':[0]*15})
        raise RuntimeError('simulator failed')
    result=run_recorded_episode(runner,None,output_dir=tmp_path,episode=0,run_digest='digest')
    assert result['outcome']=='runtime_error' and not result['policy'] and result['steps']==1
    assert (tmp_path/'rollout00_actions.jsonl').read_text().count('\n')==1
    assert json.loads((tmp_path/'rollout00_episode.json').read_text())['error']=='RuntimeError: simulator failed'


def test_episode_interruption_records_then_propagates(tmp_path):
    def runner(*args,**kwargs):raise KeyboardInterrupt()
    with pytest.raises(KeyboardInterrupt):run_recorded_episode(runner,None,output_dir=tmp_path,episode=0,run_digest='digest')
    assert (tmp_path/'rollout00_episode.json').is_file()


def test_episode_artifacts_cannot_be_overwritten(tmp_path):
    def runner(*args,**kwargs):return True,1,'task'
    run_recorded_episode(runner,None,output_dir=tmp_path,episode=0,run_digest='digest')
    with pytest.raises(FileExistsError):run_recorded_episode(runner,None,output_dir=tmp_path,episode=0,run_digest='digest')


def test_partial_video_actual_serialization(tmp_path):
    import numpy as np
    frames=[np.zeros((32,32,3),dtype=np.uint8) for _ in range(2)]
    path=tmp_path/'partial.mp4'
    save_partial_video(frames,path,20)
    assert path.stat().st_size>0
    with pytest.raises(FileExistsError):save_partial_video(frames,path,20)


def test_atomic_episode_json_does_not_leave_temp_files(tmp_path):
    path=tmp_path/'results.json'
    atomic_json(path,[_row()]);atomic_json(path,[_row(outcome='runtime_error')])
    assert json.loads(path.read_text())[0]['outcome']=='runtime_error'
    assert not list(tmp_path.glob('*.tmp'))


def test_matched_local_intervention_restores_rng_and_changes_only_prefix():
    import numpy as np
    from cosmos_framework.inference.local_memory_intervention import run_matched_local_intervention
    class Model(torch.nn.Module):
        def __init__(self):
            super().__init__();self.net=torch.nn.Module();self.net.local_memory_runtime=torch.nn.Linear(2,2);self.calls=[]
        def generate_samples_from_batch(self,batch,**kwargs):
            selected=kwargs['_local_memory_prefixes'];self.calls.append(selected)
            noise=torch.rand(1,16,64)+random.random()+float(np.random.random())
            return {'action':[noise+(1 if selected is not None else 0)]}
    model=Model().eval();prefix=torch.ones(4,32);batch={'state':torch.ones(1,15)}
    py_state,pt_state,np_state=random.getstate(),torch.get_rng_state(),np.random.get_state()
    report=run_matched_local_intervention(model,batch,(prefix,),seed=0,num_steps=3,guidance=1)
    assert report['max_abs_difference']==pytest.approx(1,abs=1e-6)
    assert model.calls[0][0] is prefix and model.calls[1] is None
    assert random.getstate()==py_state and torch.equal(torch.get_rng_state(),pt_state)
    assert np.array_equal(np.random.get_state()[1],np_state[1])
    assert report['local_slow_state_bitwise_unchanged'] is True


def test_matched_local_intervention_rejects_train_mode():
    from cosmos_framework.inference.local_memory_intervention import run_matched_local_intervention
    with pytest.raises(ValueError):run_matched_local_intervention(torch.nn.Linear(2,2),{},(torch.ones(1),),seed=0,num_steps=3,guidance=1)


def test_observed_exposure_does_not_count_uninstrumented_history():
    from cosmos_framework.utils.observed_exposure import observed_task_exposure
    records=[{'iteration':1}, {'iteration':801,'consumer_audit_status':'OBSERVED',
             'task_consumer_counts_rank_local':{'CloseFridge':8},'actual_consumer_identity_count':8}]
    report=observed_task_exposure(records)
    assert report['task_first_audited_iteration']==801
    assert report['task_exposure_observed_rank_local']=={'CloseFridge':8}
    assert report['task_audited_records']==1


def test_task_count_mismatch_does_not_update_exposure(monkeypatch):
    monkeypatch.setenv('PSM_V3_STATE_AUDIT_EVERY','0')
    audit=ConsumerAudit()
    payload={'task_class':'CloseFridge','episode_index':2,'start_frame':3}
    audit.observe('native_forward',{'iteration':800,'member':0,'index':0,'payloads':[payload]},None)
    trainer=SimpleNamespace(_grouped_window=SimpleNamespace(plan=None))
    with pytest.raises(ValueError):audit.report(trainer,800,expected_count=2)
    assert not audit.exposure


def test_identity_changes_with_model_config_and_dataset_bytes(tmp_path,monkeypatch):
    import v3_evaluation_identity as identity
    root=tmp_path/'repo';root.mkdir();cp=tmp_path/'iter_000000800';model=cp/'model';model.mkdir(parents=True)
    (model/'.metadata').write_bytes(b'metadata');(model/'__0_0.distcp').write_bytes(b'shard')
    config=tmp_path/'config.yaml';config.write_text('x: 1\n')
    dataset=tmp_path/'dataset';(dataset/'extras').mkdir(parents=True)
    meta=dataset/'extras/dataset_meta.json';meta.write_text('{}')
    def git(path,*args):
        if args[0]=='rev-parse':return 'a'*40 if path==root else 'b'*40
        if args[0]=='ls-tree':return '160000 commit '+'b'*40+'\tcosmos-framework'
        return ''
    monkeypatch.setattr(identity,'_git',git)
    monkeypatch.setattr(identity.subprocess,'check_output',lambda *a,**k:'')
    def build():return identity.build_evaluation_identity(root=root,checkpoint=cp,config_file=config,tasks=[('Task',dataset)],protocol={'seed':0})
    first=build();assert first==build()
    config.write_text('x: 2\n');second=build();assert first['digest']!=second['digest']
    meta.write_text('{"changed":true}');third=build();assert second['digest']!=third['digest']
    (model/'.metadata').write_bytes(b'new metadata');assert third['digest']!=build()['digest']


def test_identity_rejects_mismatched_root_child(monkeypatch,tmp_path):
    import v3_evaluation_identity as identity
    monkeypatch.setattr(identity,'_git',lambda path,*a:('160000 commit '+'c'*40+'\tcosmos-framework') if a[0]=='ls-tree' else 'a'*40)
    with pytest.raises(ValueError):identity.build_evaluation_identity(root=tmp_path,checkpoint=tmp_path,config_file=tmp_path,tasks=[],protocol={})


@pytest.mark.parametrize('row',[{'trials':1,'successes':2},{'trials':-1,'successes':0},{'trials':True,'successes':0}])
def test_screening_rejects_invalid_counts(row):
    with pytest.raises(ValueError):screening_metrics({'a':row},tasks=['a'],expected_trials=1)



def test_memory_inventory_reads_official_container_without_state_dict():
    model = torch.nn.Linear(4, 2)
    optimizer = torch.optim.Adam(model.parameters())
    model(torch.ones(1, 4)).sum().backward()
    optimizer.step()
    expected = memory_inventory(model, optimizer)
    container = SimpleNamespace(optimizers=[optimizer], state={}, state_dict=lambda: pytest.fail("must not gather DCP state"))
    actual = memory_inventory(model, container)
    assert actual["optimizer_storage_bytes"] == expected["optimizer_storage_bytes"] > 0
    assert actual["optimizer_count"] == 1 and actual["optimizer_state_status"] == "OBSERVED"


def test_unknown_optimizer_memory_is_unavailable_not_zero():
    info = memory_inventory(torch.nn.Linear(2, 2), object())
    assert info["optimizer_storage_bytes"] is None
    assert info["optimizer_state_status"] == "UNAVAILABLE"


@pytest.mark.parametrize("status", [" M scripts/eval.py\0", "?? scripts/new.py\0", " M cosmos-framework\0", " D SESSION.md\0"])
def test_eval_identity_rejects_dirty_root_code(status):
    from v3_evaluation_identity import validate_root_source_status
    with pytest.raises(ValueError):
        validate_root_source_status(status)


def test_eval_identity_preserves_mm_notes_and_external_evidence():
    from v3_evaluation_identity import validate_root_source_status
    validate_root_source_status(" M SESSION.md\0 M TODO.md\0?? artifacts/gate.json\0")



@pytest.mark.parametrize("ep,expected", [(False, 1), (0, True), (0, 0)])
def test_evaluation_identity_rejects_boolean_episode_or_invalid_trial_count(ep, expected):
    with pytest.raises(ValueError):
        validate_task_results([_row(ep=ep)], digest="digest", expected_trials=expected)
