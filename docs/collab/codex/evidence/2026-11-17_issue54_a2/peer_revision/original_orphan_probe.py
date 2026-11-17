import json
import multiprocessing
import os
import tempfile
from pathlib import Path
import torch
from g2.tests.test_stage_a_streaming import setup_case
from g2.offline.stage_a import package_stage_a
from g2.latent_cache.streaming import EventConsumer
from g2.tests.test_view_vae_builder import FakeEncoder

class LargerFake(FakeEncoder):
    def encode(self, rgb, preprocessing):
        _, prep=super().encode(rgb, preprocessing)
        return torch.zeros((3,64,64),dtype=torch.float32), prep

root=Path(tempfile.mkdtemp(prefix='orphan_budget_',dir='/tmp/issue54_a2_peer'))
kwargs,target,_,spool,job=setup_case(root,max_result_bytes=120000)
events=[]
package_stage_a(destination=target,event_sink=events.append,**kwargs)
spool.enqueue(job,events[0],timeout_s=0)

def interrupted_consumer():
    import g2.latent_cache.storage as storage
    original=storage.os.link
    def power_loss(src,dst,*args,**kwargs):
        if Path(src).name.startswith('.view-') and Path(dst).parent==spool.root/'records':
            os._exit(77)
        return original(src,dst,*args,**kwargs)
    storage.os.link=power_loss
    EventConsumer(spool,LargerFake()).step()

ctx=multiprocessing.get_context('fork')
crashes=[]
for _ in range(2):
    process=ctx.Process(target=interrupted_consumer)
    process.start()
    process.join(15)
    assert not process.is_alive()
    assert process.exitcode==77
    crashes.append(dict(exitcode=process.exitcode,tmp_files=len(list((spool.root/'records').glob('.view-*.tmp')))))
resumed=EventConsumer(spool,LargerFake()).step()
files={p.name:p.stat().st_size for p in (spool.root/'records').iterdir() if p.is_file()}
result=dict(root=str(root),max_result_bytes=spool.max_result_bytes,crashes=crashes,resumed_step=resumed,record_file_bytes=sum(files.values()),files=files,stats=spool.stats())
(root/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
