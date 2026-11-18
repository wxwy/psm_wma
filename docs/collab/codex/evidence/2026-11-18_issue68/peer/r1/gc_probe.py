"""Genuine CPU cache/ACK/archival; expose legacy pixel-key sharing in batches."""
import json
import subprocess
import tempfile
from pathlib import Path

from g2.latent_cache.batch_engine import BatchEngine
from g2.latent_cache.batch_queue import BatchQueue
from g2.latent_cache.batch_worker import execute_claim
from g2.latent_cache.contract import CacheError
from g2.latent_cache.final_source import load_source
from g2.latent_cache.streaming import final_pixel_event
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a,validate_profile_episode
from g2.tests.batch_helpers import FakeBatchEncoder
from g2.tests.test_batch_engine import init
from g2.tests.test_stage_a_package import stage_case


def main():
    formal='87dd1bd8599003e2f6ea4d2b069c249d06d865e8'
    for path in ('g2/latent_cache/streaming.py','g2/latent_cache/batch_queue.py'):
        assert Path(path).read_bytes()==subprocess.check_output(['git','show',formal+':'+path])
    with tempfile.TemporaryDirectory(prefix='issue68-peer-gc-') as temp:
        base=Path(temp)
        spool,spec=init(base,mode='sync')
        kwargs,_=stage_case(base/'fixture',OutputProfile(selection_top_variant='clean',view_vae=True))
        target=base/'episode_A'
        job=spool.register(target,episode_key='NavigateKitchen/episode_000000',source_fingerprint=kwargs['source_fingerprint'],profile_id=kwargs['profile'].to_dict()['profile_id'])
        package_stage_a(destination=target,event_sink=lambda e:spool.enqueue(job,e),**kwargs)
        spool.offer_source(job);spool.seal(job)
        q=BatchQueue(spool,batch_wait_ms=0);q.register_worker('encoder',4)
        claim=q.claim('encoder')
        execute_claim(q,FakeBatchEncoder(),claim,physical_gpu=4)
        source=load_source(target)
        vid='sixview/floor_top'
        owner=source['views'][vid]['owners'][0]
        desc=source['final_pixel_events'][owner['event_id']]
        # Another legitimate producing job receives identical final RGB bytes;
        # it has not yet finished rendering/offered its source inventory.
        job_b=spool.register(base/'episode_B',episode_key='NavigateKitchen/episode_000001',source_fingerprint='b'*64,profile_id=source['profile_id'])
        event=final_pixel_event(target/owner['path'],episode_key='NavigateKitchen/episode_000001',source_fingerprint='b'*64,profile_id=source['profile_id'],view_id=vid,canonical_view_id=vid,variant='clean',expected_size=desc['size_wh'])
        assert event.pixel_record_key==desc['pixel_record_key']
        spool.enqueue(job_b,event)
        engine=BatchEngine(spool,spec,mode='sync')
        try:
            engine._finish_jobs()
            assert validate_profile_episode(target)['profile_complete']
            assert spool.stats()['completed_jobs']==1
            leftovers=list((spool.root/'records').rglob('*.pt'))
            assert len(leftovers)==1
            try:q.collect()
            except CacheError as e:
                assert 'unverified numeric staging' in str(e)
                error=str(e)
            else:raise AssertionError('unexpected successful completed-batch GC')
            result=dict(status='REPRODUCED',scope='GENUINE_CPU_FIXTURE_CACHE_ACK_TOMBSTONE_NOT_GPU',source_code_matches=formal,error=error,fully_verified_episode_A=True,genuine_completed_receipts=spool.stats()['completed_jobs'],pending_job_B_event=spool.stats()['pending_inputs'],leftover_A_chunk_count=len(leftovers),queue=q.stats())
        finally:engine._shutdown()
    Path(__file__).with_name('gc_observed.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
