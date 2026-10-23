"""Real CPU process/HTTP boundaries for reserved batches, without models or Kitchen."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import eval_robocasa_18task_queue as queue_api  # noqa: E402
import robocasa_resume_execution as execution  # noqa: E402
from robocasa_eval_results import start_attempt  # noqa: E402
from robocasa_processes import group_members  # noqa: E402

SERVER = r"""
import json, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
info=json.loads(sys.argv[2])
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body=json.dumps(info).encode()
        self.send_response(200); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self,*args): pass
ThreadingHTTPServer(('127.0.0.1',int(sys.argv[1])),Handler).serve_forever()
"""

SIMULATOR = r"""
import json, os, signal, sys, time
from pathlib import Path
payload=json.loads(sys.argv[1]); directory=Path(payload['directory'])
def write(name,value): (directory/name).write_text(json.dumps(value)+'\n')
def jsonl(name,values): (directory/name).write_text(''.join(json.dumps(value)+'\n' for value in values))
write('runtime_attestation.json',payload['runtime'])
write('cpu_environment.json',{'seed':payload['seed'],'constructed':1,'public_resets':payload['count']})
count=1 if payload['mode']=='partial_exit' else payload['count']
rows=[]; progress=[]
for episode in range(count):
    common=dict(evaluation_run_digest=payload['digest'],evaluation_attempt_id=payload['attempt_id'],episode=episode)
    progress.append(dict(common,schema='psm_episode_progress_v1',event='start'))
    jsonl('episode_progress.jsonl',progress)
    if payload['mode']=='hang':
        signal.signal(signal.SIGTERM,signal.SIG_IGN)
        while True: time.sleep(.01)
    prefix=f'rollout{episode:02d}'
    row=dict(ep=episode,policy=True,steps=2,replans=1,completed_action_records=2,error=None,outcome='success',
      evaluation_run_digest=payload['digest'],evaluation_attempt_id=payload['attempt_id'],
      actions_file=prefix+'_actions.jsonl',predictions_file=prefix+'_predictions.jsonl',generated_videos=[])
    jsonl(row['actions_file'],[dict(common,source_step=step,predicted_raw15=[0.]*15,
       canonical_executed_raw15=[0.]*15,submitted_env12=[0.]*12,evidence_completed=True) for step in range(2)])
    jsonl(row['predictions_file'],[dict(common,step_before_query=0)])
    write(prefix+'_cleanup.json',dict(session_id='a'*32+':0:'+f'{episode+1:032x}',reset_ok=True,
      cleanup_error=None,rollout_error=None,media_error=None))
    write(prefix+'_episode.json',row); rows.append(row); write('results.json',rows)
    progress.append(dict(common,schema='psm_episode_progress_v1',event='end'))
    jsonl('episode_progress.jsonl',progress)
raise SystemExit(7 if payload['mode']=='partial_exit' else 0)
"""


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def write(path, value):
    path.write_text(json.dumps(value) + "\n")


def free_base():
    for port in range(24000, 60000, 2):
        sockets = [socket.socket(), socket.socket()]
        try:
            for index, connection in enumerate(sockets):
                connection.bind(("127.0.0.1", port + index))
            return port
        except OSError:
            pass
        finally:
            for connection in sockets:
                connection.close()
    raise AssertionError("no two free CPU test ports")


@pytest.fixture
def context(tmp_path):
    checkpoint, output = tmp_path / "checkpoint", tmp_path / "invocation"
    checkpoint.mkdir()
    (checkpoint / "model").mkdir()
    output.mkdir()
    config = tmp_path / "config.yaml"
    config.write_text("synthetic: true\n")
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    args = SimpleNamespace(
        num_steps=30,
        guidance=1.0,
        action_horizon=16,
        seed=0,
        num_test_episodes=5,
        progress=False,
        progress_interval_s=5.0,
        base_port=free_base(),
        terminate_grace_s=0.05,
        task_wall_timeout_s=5.0,
        episode_wall_timeout_s=3.0,
        server_start_timeout_s=3.0,
        predict_request_timeout_s=1.0,
        on_infrastructure_error="stop",
        server_python=Path(sys.executable),
        sim_python=Path(sys.executable),
        vendor_lock=tmp_path / "unused-lock.json",
        asset_manifest=None,
        save_generated_video="none",
        save_rollout_mp4=False,
        save_init_png=False,
    )
    runtime = {"schema": "synthetic_runtime", "tasks": ["CloseFridge", "NavigateKitchen"]}
    runtime["digest"] = hashlib.sha256(canonical(runtime)).hexdigest()
    return SimpleNamespace(
        checkpoint=checkpoint,
        config=config,
        output=output,
        dataset=dataset,
        args=args,
        runtime=runtime,
        server_commands=[],
        simulator_commands=[],
        phases=[],
        mode="healthy",
        info_override={},
    )


def job(context, *, identifier="batch1", slots=(0, 1, 2), seed=7, task="CloseFridge"):
    source = context.output / "sources" / task / identifier
    source.mkdir(parents=True)
    protocol = dict(
        seed=seed,
        trials=len(slots),
        R=16,
        num_steps=30,
        guidance=1.0,
        save_generated_video="none",
        save_rollout_mp4=False,
        save_init_png=False,
    )
    identity = {
        "checkpoint": str(context.checkpoint),
        "config_file": str(context.config),
        "protocol": protocol,
        "tasks": [{"task": "CloseFridge"}, {"task": "NavigateKitchen"}],
        "evaluation_runtime": context.runtime,
    }
    manifest = {"identity": identity, "digest": hashlib.sha256(canonical(identity)).hexdigest()}
    write(source / "evaluation_manifest.json", manifest)
    attempt = start_attempt(source / task, digest=manifest["digest"], resume=False)
    return dict(
        source_root=source,
        attempt_dir=attempt,
        source_manifest=manifest,
        dataset_dir=context.dataset,
        task=task,
        seed=seed,
        num_test_episodes=len(slots),
        episodes=[
            {"logical_episode_index": logical, "source_episode": physical} for physical, logical in enumerate(slots)
        ],
        reservation_path=source / "reservation.json",
    )


def callbacks(context):
    def server(args, checkpoint, config, port):
        command = queue_api.server_argv(args, checkpoint, config, port)
        context.server_commands.append(command)
        info = {
            "checkpoint": str(checkpoint / "model"),
            "config_file": str(config),
            "raw_action_dim": 15,
            "action_chunk_size": 16,
            "max_action_dim": 64,
            "num_steps": 30,
            "fps": 20,
            "seed": 0,
            "guidance": 1.0,
            "requires_state": True,
            "local_memory": {"enabled": True, "mode": "required", "action_dim": 15},
            **context.info_override,
        }
        return [sys.executable, "-c", SERVER, str(port), json.dumps(info)]

    def simulator(args, dataset, directory, port, digest, runtime, task_names):
        command = queue_api.simulator_argv(args, dataset, directory, port, digest, runtime, task_names)
        context.simulator_commands.append(command)
        payload = dict(
            directory=str(directory),
            seed=args.seed,
            count=args.num_test_episodes,
            digest=digest,
            attempt_id=f"{directory.parent.name}/{directory.name}",
            runtime=context.runtime,
            mode=context.mode,
        )
        return [sys.executable, "-c", SIMULATOR, json.dumps(payload)]

    return SimpleNamespace(
        CHILD=context.output,
        require_free_ports=queue_api.require_free_ports,
        server_argv=server,
        simulator_argv=simulator,
        wait_server=queue_api.wait_server,
        atomic_write_json=queue_api.atomic_write_json,
        EvaluationProgress=queue_api.EvaluationProgress,
    )


def execute(context, jobs, *, verify=None, api=None, **options):
    def default_verify(job, phase):
        context.phases.append((job["task"], phase))

    return execution.execute_planned_batches(
        args=context.args,
        checkpoint=context.checkpoint,
        config_file=context.config,
        jobs=jobs,
        gpus=["0"],
        output_root=context.output,
        simulation_env=os.environ.copy(),
        queue_api=api or callbacks(context),
        verify_inputs=verify or default_verify,
        **options,
    )


def assert_reclaimed(result):
    for row in result["jobs"]:
        for witness in row["cleanup"].values():
            assert witness["live_group"] is False and witness["remaining_pids"] == []
            assert group_members(witness["pgid"]) == {}
    assert not any(thread.name.startswith("robocasa-gpu-") for thread in threading.enumerate())


def test_fresh_batch_has_one_server_one_simulator_literal_seed_and_complete_c01(context):
    source = job(context)
    result = execute(context, [source])
    assert result["errors"] == [] and len(result["completed"]) == 1
    assert len(context.server_commands) == len(context.simulator_commands) == 1
    assert [phase for _, phase in context.phases] == ["pre_model_load", "post_model_load", "pre_commit"]
    argv = context.simulator_commands[0]
    assert argv[argv.index("--num-test-episodes") + 1] == "3"
    assert argv[argv.index("--seed") + 1] == "7"
    assert argv[argv.index("--runtime-tasks") + 1] == "CloseFridge,NavigateKitchen"
    server = context.server_commands[0]
    assert server[server.index("--action-chunk-size") + 1] == "16"
    assert server[server.index("--local-memory-max-sessions") + 1] == "1"
    attempt = source["attempt_dir"]
    assert json.loads((attempt / "attempt.json").read_text())["status"] == "COMPLETE"
    events = [json.loads(line) for line in (attempt / "episode_progress.jsonl").read_text().splitlines()]
    assert [(row["episode"], row["event"]) for row in events] == [
        (ep, event) for ep in range(3) for event in ("start", "end")
    ]
    assert json.loads((attempt / "cpu_environment.json").read_text()) == {
        "seed": 7,
        "constructed": 1,
        "public_resets": 3,
    }
    assert_reclaimed(result)


def test_gap_jobs_recycle_server_and_keep_each_physical_episode_zero(context):
    jobs = [job(context, identifier=f"gap{slot}", slots=(slot,), seed=100 + slot) for slot in (3, 4)]
    result = execute(context, jobs)
    assert result["errors"] == [] and len(result["completed"]) == 2
    assert len(context.server_commands) == len(context.simulator_commands) == 2
    assert len({row["cleanup"]["server"]["pid"] for row in result["jobs"]}) == 2
    for source in jobs:
        assert [row["ep"] for row in json.loads((source["attempt_dir"] / "results.json").read_text())] == [0]
    assert_reclaimed(result)


@pytest.mark.parametrize("phase", ["pre_model_load", "post_model_load", "pre_commit"])
def test_failed_input_recheck_never_commits_source_and_cleans_started_groups(context, phase):
    source = job(context)

    def verify(job, actual):
        if actual == phase:
            raise ValueError("identity changed")

    result = execute(context, [source], verify=verify)
    assert result["errors"] and result["completed"] == []
    assert "identity changed" in result["errors"][0]["error"]
    assert json.loads((source["attempt_dir"] / "attempt.json").read_text())["status"] == "FAILED"
    assert len(context.server_commands) == (0 if phase == "pre_model_load" else 1)
    assert len(context.simulator_commands) == (1 if phase == "pre_commit" else 0)
    assert_reclaimed(result)


def test_wrong_info_rejected_before_simulator_start(context):
    source = job(context)
    context.info_override = {"action_chunk_size": 32}
    result = execute(context, [source])
    assert result["errors"] and "action_chunk_size mismatch" in result["errors"][0]["error"]
    assert len(context.server_commands) == 1 and context.simulator_commands == []
    assert_reclaimed(result)


def test_failed_simulator_retains_closed_prefix_and_source_for_original_identity_scan(context):
    source = job(context)
    context.mode = "partial_exit"
    result = execute(context, [source])
    assert result["errors"] and result["completed"] == []
    assert result["source_attempts"] == [str(source["attempt_dir"])]
    assert len(json.loads((source["attempt_dir"] / "results.json").read_text())) == 1
    assert json.loads((source["attempt_dir"] / "attempt.json").read_text())["status"] == "FAILED"
    assert_reclaimed(result)


def test_episode_timeout_kills_ignored_sigterm_and_retains_error(context):
    source = job(context, slots=(2,))
    context.mode = "hang"
    context.args.episode_wall_timeout_s = 0.15
    result = execute(context, [source])
    assert result["errors"] and "episode wall timeout" in result["errors"][0]["error"]
    assert "SIGKILL" in result["jobs"][0]["cleanup"]["simulator"]["signals"]
    assert_reclaimed(result)


def test_worker_initialization_error_after_other_worker_covers_all_jobs_is_not_hidden(context, monkeypatch):
    source = job(context)
    original = Path.mkdir

    def mkdir(path, *args, **kwargs):
        if path.name == "_worker01_gpu1":
            until = time.monotonic() + 4
            while time.monotonic() < until:
                if json.loads((source["attempt_dir"] / "attempt.json").read_text())["status"] == "COMPLETE":
                    raise OSError("worker log directory failed after real source completion")
                time.sleep(0.01)
            raise AssertionError("healthy source never completed")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", mkdir)
    result = execution.execute_planned_batches(
        args=context.args,
        checkpoint=context.checkpoint,
        config_file=context.config,
        jobs=[source],
        gpus=["0", "1"],
        output_root=context.output,
        simulation_env=os.environ.copy(),
        queue_api=callbacks(context),
        verify_inputs=lambda job, phase: None,
    )
    assert len(result["completed"]) == 1
    assert any("worker log directory failed" in row["error"] for row in result["errors"])
    assert_reclaimed(result)


def test_partial_thread_start_failure_cancels_and_joins_started_worker(context, monkeypatch):
    source = job(context)
    original = threading.Thread.start

    def start(thread):
        if thread.name == "robocasa-gpu-1":
            raise RuntimeError("second Worker thread refused")
        return original(thread)

    monkeypatch.setattr(threading.Thread, "start", start)
    result = execution.execute_planned_batches(
        args=context.args,
        checkpoint=context.checkpoint,
        config_file=context.config,
        jobs=[source],
        gpus=["0", "1"],
        output_root=context.output,
        simulation_env=os.environ.copy(),
        queue_api=callbacks(context),
        verify_inputs=lambda job, phase: None,
    )
    assert any(row["stage"] == "thread_start" for row in result["errors"])
    assert_reclaimed(result)


def test_observer_failure_cannot_change_real_source_success(context):
    source = job(context)

    class BrokenObserver:
        def __init__(self, **kwargs):
            pass

        def start(self):
            raise OSError("UI unavailable")

        def update(self, *args, **kwargs):
            raise OSError("UI unavailable")

        def close(self):
            raise OSError("UI unavailable")

    api = callbacks(context)
    api.EvaluationProgress = BrokenObserver
    result = execute(context, [source], api=api)
    assert result["errors"] == [] and len(result["completed"]) == 1
    assert_reclaimed(result)


def test_catalog_callback_failure_preserves_complete_source_and_independent_invocation_error(context):
    source = job(context)

    def on_completed(job):
        raise OSError("catalog publish refused")

    result = execute(context, [source], on_completed=on_completed)
    assert len(result["completed"]) == 1 and result["errors"]
    assert "catalog publish refused" in result["errors"][0]["error"]
    assert json.loads((source["attempt_dir"] / "attempt.json").read_text())["status"] == "COMPLETE"
    assert_reclaimed(result)


def test_duplicate_reserved_logical_slot_rejected_before_worker_or_process(context):
    jobs = [job(context, identifier=f"batch{index}", slots=(2,)) for index in range(2)]
    result = execute(context, jobs)
    assert result["errors"][0]["stage"] == "reserved_input_validation"
    assert context.server_commands == context.simulator_commands == []
    assert not list(context.output.glob("_worker*"))


def test_changed_manifest_protocol_rejected_before_any_process(context):
    source = job(context)
    source["seed"] = 42
    result = execute(context, [source])
    assert result["errors"] and "seed disagrees" in result["errors"][0]["error"]
    assert context.server_commands == context.simulator_commands == []


def test_no_new_batches_requires_neither_workers_ports_nor_server(context):
    result = execution.execute_planned_batches(
        args=context.args,
        checkpoint=context.checkpoint,
        config_file=context.config,
        jobs=[],
        gpus=[],
        output_root=context.output,
        simulation_env={},
        queue_api=SimpleNamespace(),
        verify_inputs=lambda job, phase: pytest.fail("no model verification for all reused view"),
    )
    assert result["errors"] == result["source_attempts"] == []
    assert not list(context.output.glob("_worker*"))


def test_preexisting_process_output_cannot_be_overwritten(context):
    source = job(context)
    sentinel = source["attempt_dir"] / "eval.log"
    sentinel.write_text("historical bytes\n")
    result = execute(context, [source])
    assert result["errors"] and "untouched RUNNING" in result["errors"][0]["error"]
    assert sentinel.read_text() == "historical bytes\n"
    assert context.server_commands == []


def test_primary_simulator_error_and_cleanup_error_both_survive(context, monkeypatch):
    source = job(context)
    context.mode = "partial_exit"
    original = execution.OwnedProcess.close
    injected = []

    def close(owned):
        result = original(owned)
        if not injected:
            injected.append(owned.proc.pid)
            owned.cleanup["error"] = "synthetic cleanup refusal after real reap"
            raise OSError(owned.cleanup["error"])
        return result

    monkeypatch.setattr(execution.OwnedProcess, "close", close)
    result = execute(context, [source])
    row = result["errors"][0]
    assert "exited with code 7" in row["error"]
    assert any("synthetic cleanup refusal" in value for value in row["secondary_errors"])
    assert row["cleanup"]["simulator"]["error"] == "synthetic cleanup refusal after real reap"
    assert_reclaimed(result)


def test_cancellation_reclaims_both_groups_and_is_not_success(context):
    source = job(context, slots=(2,))
    context.mode = "hang"
    stop = threading.Event()
    timer = threading.Timer(0.2, stop.set)
    timer.start()
    try:
        result = execute(context, [source], stop=stop)
    finally:
        timer.cancel()
        timer.join()
    assert result["cancelled"] is True
    assert result["completed"] == [] and result["errors"]
    assert any("cancel" in row["error"] for row in result["errors"])
    assert_reclaimed(result)


def test_dotdot_source_escape_is_rejected_before_any_worker_or_process(context):
    source = job(context)
    escaped = context.output.parent / "escaped-source"
    source["source_root"].rename(escaped)
    source["source_root"] = context.output / ".." / "escaped-source"
    source["attempt_dir"] = source["source_root"] / source["task"] / "attempt_0001"
    result = execute(context, [source])
    assert result["errors"][0]["stage"] == "reserved_input_validation"
    assert context.server_commands == context.simulator_commands == []
    assert not list(context.output.glob("_worker*"))


@pytest.mark.parametrize("interruption", ["result_lock", "event_lock"])
def test_owner_signal_inside_main_thread_lock_cannot_deadlock_cleanup(context, interruption):
    source = job(context)
    arguments = dict(vars(context.args))
    payload = dict(
        args=arguments,
        checkpoint=str(context.checkpoint),
        config=str(context.config),
        output=str(context.output),
        job=source,
    )
    program = r"""
import json, linecache, signal, sys, threading
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,sys.argv[1])
import robocasa_resume_execution as execution
payload=json.loads(sys.argv[2]); interruption=sys.argv[3]; fired=[]
original=threading.Thread.start
def start(thread):
    if thread.name.startswith('robocasa-gpu-'):
        raise RuntimeError('synthetic Worker start failure')
    return original(thread)
threading.Thread.start=start
def trace(frame,event,arg):
    if event!='line' or fired or threading.current_thread() is not threading.main_thread(): return trace
    code=linecache.getline(frame.f_code.co_filename,frame.f_lineno)
    target=(interruption=='result_lock' and frame.f_code.co_name=='register' and 'errors.append(error)' in code)
    target=target or (interruption=='event_lock' and frame.f_code.co_name=='set' and 'self._flag = True' in code)
    if target:
        fired.append(interruption)
        signal.raise_signal(signal.SIGTERM)
    return trace
sys.settrace(trace)
try:
    result=execution.execute_planned_batches(args=SimpleNamespace(**payload['args']),
        checkpoint=Path(payload['checkpoint']),config_file=Path(payload['config']),jobs=[payload['job']],
        gpus=['0'],output_root=Path(payload['output']),simulation_env={},
        queue_api=SimpleNamespace(),verify_inputs=lambda job,phase:None)
finally: sys.settrace(None)
assert fired==[interruption],fired
assert any(row['stage']=='owner_cancel' for row in result['errors']),result
assert any(row['stage']=='thread_start' for row in result['errors']),result
assert result['cancelled'] is True and not result['source_attempts'],result
assert not any(thread.name.startswith('robocasa-gpu-') for thread in threading.enumerate())
print(json.dumps({'interrupted_while_locked':fired,'errors':result['errors']}))
"""
    # Independent OS watchdog makes a regression a bounded test failure, not a
    # pytest/main-thread deadlock. No model/server/simulator is launched here.
    process = subprocess.run(
        [
            sys.executable,
            "-c",
            program,
            str(Path(execution.__file__).parent),
            json.dumps(payload, default=str),
            interruption,
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=5,
    )
    assert json.loads(process.stdout)["interrupted_while_locked"] == [interruption]


def test_completed_callback_deadline_is_bound_and_late_return_is_an_invocation_error(context, monkeypatch):
    source = job(context)
    clock = [time.monotonic()]
    observed = []
    monkeypatch.setattr(execution, "time", SimpleNamespace(monotonic=lambda: clock[0]))

    def on_completed(callback_job):
        assert callback_job["validation_stop"].is_set() is False
        assert callback_job["validation_deadline"] == clock[0] + context.args.task_wall_timeout_s
        observed.append(callback_job["attempt_dir"])
        # No real long sleep: advance only this orchestration clock after the
        # actual native validator has committed COMPLETE and reclaimed groups.
        clock[0] = callback_job["validation_deadline"] + 0.001

    result = execute(context, [source], on_completed=on_completed)
    assert observed == [source["attempt_dir"]]
    assert len(result["completed"]) == 1
    assert result["errors"][0]["stage"] == "source_revalidation"
    assert "task wall timeout during completed source revalidation" in result["errors"][0]["error"]
    assert json.loads((source["attempt_dir"] / "attempt.json").read_text())["status"] == "COMPLETE"
    assert_reclaimed(result)
