"""Real coordinator registration-boundary crash; CPU fixture, no GPU."""
import json
import multiprocessing
import os
import subprocess
import tempfile
from pathlib import Path

from g2.io import read_json
from g2.latent_cache.batch_engine import BatchEngine
from g2.latent_cache.streaming import EventSpool
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import package_stage_a
from g2.tests.test_batch_engine import init
from g2.tests.test_stage_a_package import stage_case


def register_and_exit(spool_path,target,manifest):
    spool=EventSpool.open(spool_path)
    spool.register(target,episode_key='NavigateKitchen/episode_000000',source_fingerprint=manifest['source_fingerprint'],profile_id=manifest['output_profile']['profile_id'])
    os._exit(77)


def main():
    formal=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    assert formal=='87dd1bd8599003e2f6ea4d2b069c249d06d865e8'
    with tempfile.TemporaryDirectory(prefix='issue68-peer-coordinator-') as temp:
        base=Path(temp)
        kwargs,_=stage_case(base/'fixture',OutputProfile(selection_top_variant='clean',view_vae=False))
        data=base/'dataset'
        target=data/'tasks/NavigateKitchen/episodes/episode_000000'
        package_stage_a(destination=target,compress_source=True,**kwargs)
        manifest=read_json(target/'episode_manifest.json')
        spool,spec=init(base)
        process=multiprocessing.get_context('spawn').Process(target=register_and_exit,args=(str(spool.root),str(target),manifest))
        process.start();process.join(20)
        assert process.exitcode==77
        engine=BatchEngine(spool,spec,mode='independent',dataset_root=data,resume=True)
        snapshots=[]
        try:
            engine._recover()
            for _ in range(3):
                engine._last_discovery=float('-inf')
                engine._new_work=False
                engine._discover();engine._finish_jobs();engine.queue.collect()
                with spool._db() as db:rows=[dict(r) for r in db.execute('SELECT done,source_ready,sealed,error FROM jobs')]
                stats=spool.stats()
                snapshots.append(dict(jobs=rows,spool=stats,batch=engine.queue.stats(),capacity=engine.queue.capacity_pressure()))
            assert all(s['jobs']==[dict(done=0,source_ready=None,sealed=None,error=None)] for s in snapshots)
            assert all(s['spool']['active_records']==0 and s['spool']['active_jobs']==1 and not s['capacity']['blocked'] for s in snapshots)
            assert not engine._idle.observe(0,busy=True)
            assert not engine._idle.observe(10**9,busy=True)
            result=dict(formal_root=formal,coordinator_exit_code=77,scope='CPU_FIXTURE_REAL_OS_EXIT',status='STALLED_RESUME_REPRODUCED',snapshots=snapshots,cache_published=(target/'vae_cache/COMPLETE.json').exists())
        finally:engine._shutdown()
    Path(__file__).with_name('coordinator_observed.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))


if __name__=='__main__':main()
