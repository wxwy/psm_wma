"""Read-only independent CPU dispatch wiring probe. No native/VAE/resource run."""

from pathlib import Path
import subprocess

from g2.io import write_json
from g2.offline import atomic_6views_run as producer
from g2.offline import full_production as full
from g2.tests.test_one_shot_supervisor import config_case


def test_prepared_production_args_dispatch_original_queue(tmp_path, monkeypatch):
    cfg, _ = config_case(tmp_path)
    cfg.update(sample_mode=True,expected_selected_episodes=1,expected_task_count=1,
               tasks=['NavigateKitchen'],episodes_per_task=1,expected_episode_ids=[0])
    row=dict(episode_id=0,task_class='NavigateKitchen',source_fingerprint='a'*64,
             expected_relative_output='tasks/NavigateKitchen/episodes/episode_000000')
    rows=[row]
    run=Path(cfg['run_root'])
    write_json(run/'profile.json',cfg['profile'])
    index=dict(episodes_total=1,episodes_pending=1,tasks_selected=['NavigateKitchen'],
               batches_total=1,resume=False)

    def build(*args,**kwargs):
        root=run/'plan'
        root.mkdir(exist_ok=True)
        write_json(root/'index.json',index)
        write_json(root/'batch_000.json',dict(renderer='f27',episodes=rows))
        return index

    monkeypatch.setattr(producer.plan,'discover',lambda *a,**k:(rows,{}))
    monkeypatch.setattr(producer.plan,'build',build)
    completed=set()
    monkeypatch.setattr(producer,'_completed',lambda args,row,profile: row['episode_id'] in completed)
    args,selection,_=full.prepare_plan(cfg)  # Actual unmodified plan adapter.
    calls=[]
    def worker(command,check=False):
        calls.append(command)
        completed.add(int(command[command.index('--episode-id')+1]))
        return subprocess.CompletedProcess(command,0)
    producer.schedule(args,run_worker=worker)
    observation=dict(prepared_action=args.action,worker_calls=len(calls),selected=len(selection),
        scope='CPU_SYNTHETIC_SOURCE_INDEX_NO_GPU_NATIVE_OR_VAE')
    write_json(tmp_path/'dispatch_observed.json',observation)
    # A production handoff must leave plan-only mode. This regression catches
    # a previous dispatch bug, without rewriting tracked evidence files.
    assert args.action=='run' and args.manual_start and args.allow_experimental, observation
    assert len(calls)==1 and completed=={0}
