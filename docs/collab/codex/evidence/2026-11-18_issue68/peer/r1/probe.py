"""Independent R1 closure probes; CPU fixtures, never GPU evidence."""
import ast
import json
import subprocess
import tempfile
import time
from pathlib import Path

from g2.latent_cache.batch_engine import BatchEngine,discover_published,engine_config
from g2.latent_cache.batch_queue import BatchQueue
from g2.latent_cache.batch_worker import execute_claim
from g2.latent_cache.contract import CacheError
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.test_batch_queue import events_case
from g2.tests.test_stage_a_package import stage_case

FORMAL='87dd1bd8599003e2f6ea4d2b069c249d06d865e8'


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==FORMAL
    observed=dict(formal_root=FORMAL,scope='CPU_FIXTURE_AND_SYNTHETIC_LOG_CLASSIFIER_ONLY',real_gpu=False)
    with tempfile.TemporaryDirectory(prefix='issue68-peer-r1-') as temp:
        base=Path(temp)
        data=base/'inprogress'
        (data/'tasks/NewTask').mkdir(parents=True)
        assert discover_published(data)==[]
        (data/'tasks/NewTask/episodes').write_text('not a directory')
        try:discover_published(data)
        except CacheError:pass
        else:raise AssertionError('existing non-directory accepted')
        observed['incomplete_task_directory']='PASS_MISSING_SKIPPED_NONDIR_REJECTED'
        kwargs,_=stage_case(base/'fixture',OutputProfile(selection_top_variant='clean',view_vae=False))
        root=base/'published'
        package_stage_a(destination=root,compress_source=True,**kwargs)
        assert discover_published(root,tasks=['DifferentTask'])==[]
        assert discover_published(root,episodes=[999])==[]
        assert discover_published(root,tasks=['NavigateKitchen'],episodes=[0])==[root]
        observed['direct_root_scope']='PASS_WRONG_TASK_WRONG_EP_REJECTED_CORRECT_ACCEPTED'
        dry,_,_,_=events_case(base/'dry',35)
        q=BatchQueue(dry,batch_wait_ms=0);q.register_worker('dry',4)
        budget=q.claim('dry')['reserved_bytes']
        spool,encoder,job,events=events_case(base/'actual',35,budget=budget)
        queue=BatchQueue(spool,batch_wait_ms=0);queue.register_worker('initial',4)
        claim=queue.claim('initial')
        execute_claim(queue,encoder,claim,physical_gpu=4)
        before={str(p.relative_to(base/'actual')):p.read_bytes() for p in (base/'actual').glob('pixel_*.png')}
        assert queue.claim('initial') is None and queue.capacity_pressure()['blocked']
        assert not queue.finalizable(job)
        spec=dict(engine_config(dict(gpus=[4],batch_wait_ms=0,min_free_disk_bytes=0,poll_interval_s=.01,discovery_interval_s=.01,worker_timeout_s=.2)),weights=str(base/'TEST_ONLY'),cosmos_root=str(base),_test_encoder_factory='g2.tests.batch_helpers:FakeBatchEncoder')
        engine=BatchEngine(spool,spec,mode='sync',clock=lambda:time.monotonic()*200)
        started=time.monotonic()
        try:engine.run()
        except CacheError as exc:
            assert 'numeric capacity cannot progress' in str(exc),str(exc)
            error=str(exc)
        else:raise AssertionError('capacity cycle did not fail explicitly')
        assert {p:p.read_bytes() for p in (base/'actual').glob('pixel_*.png')}=={base/'actual'/p:b for p,b in before.items()}
        assert len(list((spool.root/'records').rglob('*.pt')))==32
        assert spool.stats()['pending_inputs']==3 and not (base/'actual/unpublished/COMPLETE.json').exists()
        observed['original_completed32_pending3_cycle']=dict(status='PASS_BOUNDED_EXPLICIT_FAILURE',wall_seconds=time.monotonic()-started,error=error,queue=queue.stats(),source_pngs_preserved=True,completed_numeric_files_preserved=32)

        # A pure log-classifier test, not a claim that these synthetic rows came
        # from CUDA. Its purpose is to reject ACK-only multi-card evidence.
        code=subprocess.check_output(['git','show',FORMAL+':docs/collab/codex/evidence/2026-11-18_issue68/real_gate.py'],text=True)
        node=next(n for n in ast.parse(code).body if isinstance(n,ast.FunctionDef) and n.name=='native_trace')
        namespace={'json':json}
        exec(compile(ast.Module(body=[node],type_ignores=[]),'<formal87-native-trace>','exec'),namespace)
        logs=base/'synthetic_trace/worker_logs';logs.mkdir(parents=True)
        a=dict(native_called=True,test_only=False,physical_gpu='4',native_input_shape=[32,3,1,256,256],encode_api_started_unix=10,encode_api_completed_unix=20,metrics=dict(native_calls=1,native_cuda_ms=1))
        b=dict(a,physical_gpu='5',encode_api_started_unix=15,encode_api_completed_unix=25)
        cases=[('ack_only_second',dict(b,native_called=False),False),('nonoverlap_second',dict(b,encode_api_started_unix=21),False),('overlap_second',b,True)]
        result={}
        for name,second,accepted in cases:
            (logs/'synthetic.jsonl').write_text('\n'.join(json.dumps(row) for row in [a,second])+'\n')
            try:value=namespace['native_trace'](logs.parent)
            except AssertionError:assert not accepted;result[name]='REJECTED'
            else:assert accepted;result[name]=value['overlap_scope']
        observed['SYNTHETIC_NOT_GPU_native_trace_classifier']=result
    Path(__file__).with_name('observed.json').write_text(json.dumps(observed,sort_keys=True,indent=2)+'\n')
    print(json.dumps(observed,sort_keys=True))


if __name__=='__main__':main()
