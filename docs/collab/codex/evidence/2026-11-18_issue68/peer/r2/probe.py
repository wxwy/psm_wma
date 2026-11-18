"""Final independent CPU closure; no real GPU or server acceptance."""
import json
import multiprocessing
import os
import subprocess
import tempfile
from pathlib import Path

from g2.io import digest,read_json
from g2.latent_cache.batch_engine import BatchEngine
from g2.latent_cache.batch_queue import BatchQueue
from g2.latent_cache.batch_worker import execute_claim
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import CacheError
from g2.latent_cache.posthoc import coordinator
from g2.latent_cache.storage import build_lock
from g2.latent_cache.streaming import EventSpool
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.batch_helpers import FakeBatchEncoder
from g2.tests.test_batch_engine import init
from g2.tests.test_batch_queue import events_case
from g2.tests.test_stage_a_package import stage_case

FORMAL='778022c8fcf431fa16e83a67256ba58b4b464052'


def inventory(root):
    return {str(p.relative_to(root)):digest(p) for p in root.rglob('*') if p.is_file() and 'vae_cache' not in p.relative_to(root).parts}


def published(base,eid=0):
    kwargs,_=stage_case(base/f'fixture{eid}',OutputProfile(selection_top_variant='clean',view_vae=False))
    kwargs['episode_id']=eid
    for caption in kwargs['captions'].values():caption['episode_index']=eid
    root=base/f'dataset/tasks/NavigateKitchen/episodes/episode_{eid:06d}'
    package_stage_a(destination=root,compress_source=True,**kwargs)
    return root


def register_exit(spool_path,target):
    spool=EventSpool.open(spool_path);m=read_json(Path(target)/'episode_manifest.json')
    spool.register(target,episode_key='NavigateKitchen/episode_000000',source_fingerprint=m['source_fingerprint'],profile_id=m['output_profile']['profile_id'])
    os._exit(77)


def numeric_exit(spool_path):
    spool=EventSpool.open(spool_path);q=BatchQueue(spool,batch_wait_ms=0)
    q.register_worker('first',4)
    execute_claim(q,FakeBatchEncoder(),q.claim('first',flush=True),physical_gpu=4,crash_once='numeric_fsynced')


def main():
    assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==FORMAL
    source_files=['g2/latent_cache/batch_engine.py','g2/latent_cache/batch_queue.py','g2/latent_cache/batch_worker.py','g2/latent_cache/streaming.py']
    for path in source_files:assert Path(path).read_bytes()==subprocess.check_output(['git','show',FORMAL+':'+path])
    results=dict(formal_root=FORMAL,scope='INDEPENDENT_CPU_FIXTURES_WITH_REAL_OS_CRASHES_NOT_GPU',real_gpu=False)
    mp=multiprocessing.get_context('spawn')
    with tempfile.TemporaryDirectory(prefix='issue68-peer-r2-') as temporary:
        base=Path(temporary)
        case=base/'register_resume';target=published(case);before=inventory(target)
        spool,spec=init(case)
        child=mp.Process(target=register_exit,args=(str(spool.root),str(target)))
        child.start();child.join(20);assert child.exitcode==77
        with spool._db() as db:assert db.execute('SELECT source_ready FROM jobs').fetchone()[0] is None
        report=BatchEngine(spool,spec,mode='independent',dataset_root=case/'dataset',resume=True).run()
        assert report['status']=='IDLE_TIMEOUT'
        assert verify_episode(target)['records_checked']==5
        assert spool.stats()['active_jobs']==spool.stats()['active_records']==0
        assert inventory(target)==before
        results['register_offer_crash_resume']=dict(status='PASS',child_exit=77,records=5,original_files_unchanged=True,spool=spool.stats())

        case=base/'conflict';target=published(case);before=inventory(target)
        spool,spec=init(case)
        m=read_json(target/'episode_manifest.json')
        spool.register(target,episode_key='NavigateKitchen/episode_000000',source_fingerprint='0'*64,profile_id=m['output_profile']['profile_id'])
        engine=BatchEngine(spool,spec,mode='independent',dataset_root=case/'dataset',resume=True)
        try:engine.run()
        except CacheError as exc:assert 'offered source differs' in str(exc)
        else:raise AssertionError('changed source accepted')
        with build_lock(coordinator(target)):pass
        assert inventory(target)==before and not (target/'vae_cache/COMPLETE.json').exists()
        results['source_conflict_and_startup_lease_cleanup']='PASS_REJECTED_AND_LEASE_REACQUIRED'

        case=base/'sync_producing';spool,spec=init(case,mode='sync')
        spool.register(case/'not_published',episode_key='NavigateKitchen/episode_000000',source_fingerprint='a'*64,profile_id='b'*64)
        engine=BatchEngine(spool,spec,mode='sync',resume=True)
        try:
            engine._recover()
            with spool._db() as db:assert db.execute('SELECT source_ready FROM jobs').fetchone()[0] is None
        finally:engine._shutdown()
        results['sync_not_yet_published_source']='PASS_NOT_OFFERED'

        case=base/'equal_pixels';targets=[published(case,eid) for eid in (0,1)]
        originals=[inventory(r) for r in targets]
        spool,spec=init(case)
        engine=BatchEngine(spool,spec,mode='independent',dataset_root=case/'dataset')
        try:
            engine._discover()
            with spool._db() as db:rows=[dict(r) for r in db.execute('SELECT * FROM jobs ORDER BY target')]
            engine._refill(rows[0])
            q=engine.queue;q.register_worker('encoder',4)
            first=q.claim('encoder',flush=True)
            engine._refill(rows[1])
            with spool._db() as db:
                descriptors=[json.loads(r[0]) for r in db.execute('SELECT descriptor FROM events WHERE job=?',(rows[1]['id'],))]
            assert any(m['event']['pixel_record_key']==d['pixel_record_key'] for m in first['context']['members'] for d in descriptors)
            execute_claim(q,FakeBatchEncoder(),first,physical_gpu=4)
            engine._finish_jobs();q.collect()
            assert spool.stats()['completed_jobs']==1 and spool.stats()['pending_inputs']==5
            assert not (spool.root/'records'/first['context']['batch_id']).exists()
            second=q.claim('encoder',flush=True)
            assert first['context']['batch_id']!=second['context']['batch_id']
            execute_claim(q,FakeBatchEncoder(),second,physical_gpu=4)
            engine._finish_jobs();q.collect()
            assert [verify_episode(r)['records_checked'] for r in targets]==[5,5]
            assert [inventory(r) for r in targets]==originals
            assert spool.stats()['active_jobs']==spool.stats()['active_records']==0
            assert q.stats()['batch_states']=={} and not list((spool.root/'records').rglob('*.pt'))
            results['identical_pixels_distinct_batch_gc']=dict(status='PASS',records=[5,5],completed_jobs=2,no_numeric_staging=True,source_files_unchanged=True)
        finally:engine._shutdown()

        case=base/'ack_only';spool,_,_,_=events_case(case,1)
        child=mp.Process(target=numeric_exit,args=(str(spool.root),))
        child.start();child.join(20);assert child.exitcode==77
        q=BatchQueue(spool,batch_wait_ms=0);q.expire_dead_worker(child.pid)
        q.register_worker('recovery',5)
        encoder=FakeBatchEncoder();replay=execute_claim(q,encoder,q.claim('recovery',flush=True),physical_gpu=5)
        assert encoder.calls==0 and replay['native_called'] is False and replay['reused_files']==1
        stats=q.stats()['gpu']['5']
        assert stats['records']==1 and stats['native_batches']==stats['native_records']==0
        assert stats['native_cuda_ms']==0
        results['ack_only_native_telemetry']=dict(status='PASS_ZERO_NATIVE_COUNTS',child_exit=77,encoder_calls=encoder.calls,gpu_completion_counters=stats)
    Path(__file__).with_name('observed.json').write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
    print(json.dumps(results,sort_keys=True))


if __name__=='__main__':main()
