"""Independent peer probes on fixed Issue68 code; CPU fixture only."""
import json
import tempfile
from pathlib import Path

from g2.latent_cache.batch_engine import discover_published
from g2.latent_cache.batch_queue import BatchQueue
from g2.latent_cache.batch_worker import execute_claim
from g2.tests.test_batch_queue import events_case


def main():
    out={}
    with tempfile.TemporaryDirectory(prefix='issue68-peer-') as temp:
        base=Path(temp)
        data=base/'dataset'
        (data/'tasks/NewTask').mkdir(parents=True)
        try:
            found=discover_published(data)
            out['incomplete_task_directory']=dict(returned=[str(p) for p in found],accepted=True)
        except Exception as e:
            out['incomplete_task_directory']=dict(error_type=type(e).__name__,error=str(e),accepted=False)
        # The path-dependent job hash stays64 chars, so canonical context byte
        # size is identical in dry and actual cases. Pin a legitimate finite
        # budget at construction; no runtime config mutation is used.
        dry,_,_,_=events_case(base/'dry',35)
        q=BatchQueue(dry,batch_wait_ms=0)
        q.register_worker('dry',4)
        required=q.claim('dry')['reserved_bytes']
        spool,encoder,job,_=events_case(base/'actual',35,budget=required)
        queue=BatchQueue(spool,batch_wait_ms=0)
        queue.register_worker('real',4)
        claim=queue.claim('real')
        assert claim['reserved_bytes']==required
        execute_claim(queue,encoder,claim,physical_gpu=4)
        none=[queue.claim('real') is None for _ in range(3)]
        out['completed_batch_capacity_cycle']=dict(configured_max_result_bytes=required,claim_returns_none=none,queue=queue.stats(),spool=spool.stats(),job_finalizable=queue.finalizable(job))
    Path(__file__).with_name('observed.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
    print(json.dumps(out,sort_keys=True))


if __name__=='__main__':main()
