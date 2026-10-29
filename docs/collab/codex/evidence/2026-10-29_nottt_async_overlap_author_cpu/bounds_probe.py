"""Extra author CPU smoke: owned PIDs, RSS, declared IPC/mmap bounds; synthetic data only."""
from pathlib import Path
import json,os,sys,io
ROOT=Path('/workspace/psm-wma-nottt-async')
sys.path[:0]=[str(ROOT/'cosmos-framework'),str(ROOT/'scripts')]

def main():
 import torch
 from cosmos_framework.model.generator.mot.robocasa_exact_window_local import ExactWindowRankPlanner
 from cosmos_framework.trainer.no_ttt_async_loader import NoTTTAsyncLoader,PreparedDataset,AsyncJob
 from cosmos_framework.trainer.no_ttt_async_recipe import AsyncWorkerState
 from cosmos_framework.trainer.no_ttt_async_test_support import SyntheticAsyncRecipe,build_synthetic_producer
 from cosmos_framework.utils.no_ttt_loader_profile import LoaderProfile
 out=Path(sys.argv[1]); assert not out.exists();out.mkdir(parents=True)
 profile=LoaderProfile(8,1,True,120)
 recipe=SyntheticAsyncRecipe(count=17,t=16,world=4)
 producer=build_synthetic_producer(count=17,t=16,world=4)
 planner=ExactWindowRankPlanner(producer.catalog,rank=0,world_size=4,b_stream=8,active_ga=4)
 loader=NoTTTAsyncLoader(producer,profile,planner,recipe=recipe)
 plan=planner.plan_window(planner.initial_frontier())
 try:
  loader.begin(plan)
  for member in plan.members:
   for request in member:loader.materialize(request)
  metrics=loader.finish();assert len(metrics['worker_pids'])==8
 finally:loader.close()
 assert all(row['exitcode'] is not None and not Path(f"/proc/{row['pid']}").exists() for row in loader.last_cleanup)
 dataset=PreparedDataset(recipe,profile.max_packet_bytes)
 dataset.state=AsyncWorkerState(build_synthetic_producer(count=17,t=16,world=4,rate=0),rate=recipe.rate,cache_reader=None)
 sample=dataset[AsyncJob(0,0,plan.members[0][0])]
 result=dict(schema='nottt_async_cpu_bounds_author_probe_v1',real_gpu=False,real_assets=False,
  profile=profile.async_identity(),worker_pids=metrics['worker_pids'],worker_cache_last=metrics['worker_cache_last'],
  last_cleanup=loader.last_cleanup,observed_one_sample_packet_bytes=len(sample['packet']),
  native_ram_qualification='NOT_RUN; synthetic RSS is not a world4 native memory prediction',
  formal_root='e0fe911dfb9fd34957234828195cf051713f6c3d',child_gitlink='f6a92d47b6dac7998ddc58b3da26ef93f8068dc7')
 (out/'bounds.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))

if __name__=='__main__':main()
