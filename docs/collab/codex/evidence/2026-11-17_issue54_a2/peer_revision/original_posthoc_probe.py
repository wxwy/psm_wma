import json
import tempfile
from pathlib import Path
from g2.tests.test_stage_a_streaming import setup_case
from g2.offline.stage_a import package_stage_a,validate_profile_episode
from g2.latent_cache.streaming import ConsumerLimits,EventConsumer
from g2.latent_cache.production import build_profile
from g2.tests.test_view_vae_builder import PREPROCESS,FakeEncoder

root=Path(tempfile.mkdtemp(prefix='posthoc_handoff_',dir='/tmp/issue54_a2_peer'))
kwargs,target,encoder,spool,job=setup_case(root,png=False,limits=ConsumerLimits(max_events=1))
package_stage_a(destination=target,event_sink=lambda e:spool.deliver(job,e,root/'VAE_DELIVERY_PENDING.json',timeout_s=0),**kwargs)
spool.offer_source(job)
before=spool.stats()
posthoc=FakeEncoder()
built=build_profile(target,posthoc,preprocessing=PREPROCESS,cleanup=True)
profile=validate_profile_episode(target)
outcomes=[]
for attempt in range(2):
    if attempt:spool.retry(job)
    try:
        completed=EventConsumer(spool,encoder).step()
        outcomes.append(dict(attempt=attempt,step=completed,stats=spool.stats()))
    except Exception as exc:
        outcomes.append(dict(attempt=attempt,error_type=type(exc).__name__,error=str(exc),stats=spool.stats()))
result=dict(root=str(root),initial_stats=before,posthoc=built,profile_complete=profile['profile_complete'],temporary_pngs=len(list((target/'_spatial_inputs').rglob('*.png'))),consumer_outcomes=outcomes,consumer_encode_calls=encoder.calls,posthoc_encode_calls=posthoc.calls)
(root/'probe.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
