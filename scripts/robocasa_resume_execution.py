"""Execute reserved Resume batches with the existing owned-process safety boundary.

No allocation, historical-evidence migration, model import or GPU discovery lives
here. A reserved source keeps its original manifest/C01 physical Episode IDs.
"""

from __future__ import annotations

import copy
import hashlib
import json
import queue
import re
import signal
import subprocess
import threading
import time
from pathlib import Path

from robocasa_eval_progress import EvaluationProgress
from robocasa_eval_results import fail_attempt, finish_attempt
from robocasa_processes import EpisodeProgress, EvaluationInterrupted, OwnedProcess, supervise_simulator

_SHA = re.compile(r"[0-9a-f]{64}\Z")


def _safe(path):
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"Resume execution path contains a symlink: {path}")
    return path.resolve()


class _ExecutionStop:
    """Expose Event cancellation while keeping the signal handler lock-free."""

    def __init__(self, event):
        self.event, self.signals = event, []

    def is_set(self):
        return bool(self.signals) or self.event.is_set()

    def set(self):
        self.event.set()


def _positive_int(value, name, *, zero=False):
    if type(value) is not int or value < (0 if zero else 1):
        raise ValueError(f"{name} must be a {'nonnegative' if zero else 'positive'} integer")
    return value


def _prepare_job(job, *, args, checkpoint, config_file, output_root):
    """Validate allocation/command agreement before launching any reserved job."""
    result = dict(job)
    task = job.get("task")
    if not isinstance(task, str) or not task.isidentifier() or task == "all":
        raise ValueError("reserved batch has an invalid task")
    for name in ("source_root", "attempt_dir", "dataset_dir"):
        result[name] = _safe(job[name])
        if not result[name].is_dir():
            raise ValueError(f"reserved batch {name} is not an existing directory")
    result["source_root"].relative_to(output_root)
    result["attempt_dir"].relative_to(result["source_root"])
    if result["attempt_dir"].parent.name != task:
        raise ValueError("reserved batch task and physical Attempt directory disagree")
    manifest = job["source_manifest"]
    identity, digest = manifest["identity"], manifest["digest"]
    canonical = json.dumps(
        identity, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode()
    if not isinstance(digest, str) or not _SHA.fullmatch(digest) or hashlib.sha256(canonical).hexdigest() != digest:
        raise ValueError("reserved source manifest has an invalid original digest")
    if json.loads(_safe(result["source_root"] / "evaluation_manifest.json").read_text()) != manifest:
        raise ValueError("reserved source manifest differs from its persisted original")
    marker = json.loads(_safe(result["attempt_dir"] / "attempt.json").read_text())
    if (
        marker.get("schema") != "psm_robocasa_task_attempt_v1"
        or marker.get("attempt_id") != result["attempt_dir"].name
        or marker.get("evaluation_run_digest") != digest
        or marker.get("status") != "RUNNING"
        or set(path.name for path in result["attempt_dir"].iterdir()) != {"attempt.json"}
    ):
        raise ValueError("reserved execution requires an untouched RUNNING Attempt")
    if Path(identity["checkpoint"]).resolve() != checkpoint or Path(identity["config_file"]).resolve() != config_file:
        raise ValueError("reserved source checkpoint/config path disagrees with execution")
    protocol = identity["protocol"]
    count = _positive_int(job["num_test_episodes"], "reserved batch trials")
    seed = _positive_int(job["seed"], "reserved batch seed", zero=True)
    if type(protocol.get("trials")) is not int or protocol["trials"] != count:
        raise ValueError("reserved batch trials disagree with original source protocol")
    if type(protocol.get("seed")) is not int or protocol["seed"] != seed:
        raise ValueError("reserved batch seed disagrees with original source protocol")
    for name, expected in (("num_steps", args.num_steps), ("R", args.action_horizon), ("guidance", args.guidance)):
        if protocol.get(name) != expected:
            raise ValueError(f"reserved source model parameter {name} disagrees with execution")
    episodes = job["episodes"]
    if not isinstance(episodes, list) or len(episodes) != count:
        raise ValueError("reserved logical/physical Episode map has the wrong length")
    physical, logical = [], []
    for row in episodes:
        physical.append(_positive_int(row["source_episode"], "physical Episode", zero=True))
        logical.append(_positive_int(row["logical_episode_index"], "logical Episode", zero=True))
    if physical != list(range(count)) or len(set(logical)) != count:
        raise ValueError("reserved map must bind physical 0..N-1 to distinct logical Episodes")
    task_names = [row["task"] for row in identity["tasks"]]
    if task not in task_names or len(set(task_names)) != len(task_names):
        raise ValueError("reserved source task list is missing or ambiguous")
    runtime_digest = identity["evaluation_runtime"]["digest"]
    if not isinstance(runtime_digest, str) or not _SHA.fullmatch(runtime_digest):
        raise ValueError("reserved source runtime digest is invalid")
    batch_args = copy.copy(args)
    batch_args.seed, batch_args.num_test_episodes = seed, count
    for name in ("save_generated_video", "save_rollout_mp4", "save_init_png"):
        if protocol.get(name) != getattr(args, name):
            raise ValueError(f"reserved source media option {name} disagrees with current execution")
    result.update(
        batch_args=batch_args,
        source_digest=digest,
        runtime_digest=runtime_digest,
        runtime_tasks=task_names,
    )
    return result


def _error(error):
    return f"{type(error).__name__}: {error}"


def execute_planned_batches(
    *,
    args,
    checkpoint,
    config_file,
    jobs,
    gpus,
    output_root,
    simulation_env,
    queue_api,
    verify_inputs,
    on_completed=None,
    stop=None,
):
    """Run one fresh Server and Simulator per reserved execution batch.

    Queue callbacks retain actual command, /info and listener verification. The
    input verifier runs before model load, after /info and before committing a
    complete source. All started sources (including failures with closed
    prefixes) are returned for the caller's original-identity Episode re-scan.
    Observers never decide completion or erase infrastructure errors.
    """
    output_root, checkpoint, config_file = _safe(output_root), Path(checkpoint).resolve(), Path(config_file).resolve()
    stop = _ExecutionStop(stop if stop is not None else threading.Event())
    results, errors, completed = [], [], []
    lock = threading.RLock()
    planned = list(jobs)
    if not planned:
        return {"completed": [], "source_attempts": [], "jobs": [], "errors": [], "cancelled": stop.is_set()}
    prepared = []
    try:
        if (
            not isinstance(gpus, (list, tuple))
            or not gpus
            or any(type(gpu) not in (int, str) or not str(gpu).isdecimal() for gpu in gpus)
            or len({str(gpu) for gpu in gpus}) != len(gpus)
        ):
            raise ValueError("reserved execution requires distinct GPU workers")
        seen_paths, seen_slots = set(), set()
        for job in planned:
            prepared_job = _prepare_job(
                job, args=args, checkpoint=checkpoint, config_file=config_file, output_root=output_root
            )
            path = str(prepared_job["attempt_dir"])
            slots = {(job["task"], row["logical_episode_index"]) for row in job["episodes"]}
            if path in seen_paths or slots & seen_slots:
                raise ValueError("duplicate reserved Attempt or logical Episode execution")
            seen_paths.add(path)
            seen_slots.update(slots)
            prepared.append(prepared_job)
    except Exception as error:
        return {
            "completed": [],
            "source_attempts": [],
            "jobs": [],
            "errors": [{"stage": "reserved_input_validation", "error": _error(error)}],
            "cancelled": stop.is_set(),
        }
    work = queue.Queue()
    for job in prepared:
        work.put(job)
    try:
        observer = getattr(queue_api, "EvaluationProgress", EvaluationProgress)(
            enabled=args.progress, interval_s=args.progress_interval_s
        )
    except Exception:
        observer = None

    def report(worker_id, **fields):
        try:
            observer.update(worker_id, **fields)
        except Exception:
            pass

    def register(error):
        with lock:
            errors.append(error)

    def execute_job(job, worker_id, gpu, server_log, server_log_path):
        batch_args, attempt = job["batch_args"], job["attempt_dir"]
        digest, runtime = job["source_digest"], job["runtime_digest"]
        attempt_id = f"{attempt.parent.name}/{attempt.name}"
        started = time.monotonic()
        deadline = started + args.task_wall_timeout_s
        port, stage, failure, returncode = args.base_port + worker_id, "before_model_load", None, -1
        server_owned = sim_owned = None
        cleanup, secondary_errors = {}, []
        committed = False
        row = {
            "task": job["task"],
            "attempt_dir": str(attempt),
            "source_digest": digest,
            "worker": worker_id,
            "gpu": gpu,
        }
        try:
            if stop.is_set():
                raise EvaluationInterrupted("evaluation cancelled before reserved batch model load")
            verify_inputs(job, "pre_model_load")
            if time.monotonic() >= deadline:
                raise EvaluationInterrupted("task wall timeout during input verification")
            report(
                worker_id,
                task=job["task"],
                gpu=gpu,
                attempt_dir=attempt,
                attempt_id=attempt_id,
                run_digest=digest,
                episodes=batch_args.num_test_episodes,
                stage="model_loading",
            )
            queue_api.require_free_ports([port])
            server_env = simulation_env.copy()
            server_env["CUDA_VISIBLE_DEVICES"] = str(gpu)
            server_command = queue_api.server_argv(batch_args, checkpoint, config_file, port)
            stage = "server_start"
            server_owned = OwnedProcess(
                server_command,
                grace_s=args.terminate_grace_s,
                cwd=queue_api.CHILD,
                env=server_env,
                stdout=server_log,
                stderr=subprocess.STDOUT,
            )
            info = queue_api.wait_server(
                server_owned.proc,
                port,
                min(args.server_start_timeout_s, max(0.001, deadline - time.monotonic())),
                checkpoint=checkpoint,
                config_file=config_file,
                num_steps=args.num_steps,
                guidance=args.guidance,
                stop=stop,
            )
            verify_inputs(job, "post_model_load")
            if time.monotonic() >= deadline:
                raise EvaluationInterrupted("task wall timeout after model loading")
            queue_api.atomic_write_json(attempt / "server_info.json", info)
            queue_api.atomic_write_json(
                attempt / "server_process.json", {"pid": server_owned.proc.pid, "pgid": server_owned.pgid, "port": port}
            )
            command = queue_api.simulator_argv(
                batch_args, job["dataset_dir"], attempt, port, digest, runtime, job["runtime_tasks"]
            )
            queue_api.atomic_write_json(attempt / "commands.json", {"server": server_command, "simulator": command})
            sim_env = server_env.copy()
            sim_env["MUJOCO_GL"] = sim_env.get("MUJOCO_GL", "egl")
            stage = "simulator"
            report(worker_id, stage="environment_initialization")
            with (attempt / "eval.log").open("xb", buffering=0) as task_log:
                sim_owned = OwnedProcess(
                    command,
                    grace_s=args.terminate_grace_s,
                    cwd=queue_api.CHILD,
                    env=sim_env,
                    stdout=task_log,
                    stderr=subprocess.STDOUT,
                )
                progress = EpisodeProgress(
                    attempt / "episode_progress.jsonl",
                    digest=digest,
                    attempt_id=attempt_id,
                    episodes=batch_args.num_test_episodes,
                )
                returncode = supervise_simulator(
                    sim_owned,
                    server=server_owned.proc,
                    task_deadline=deadline,
                    episode_wall_s=args.episode_wall_timeout_s,
                    progress=progress,
                    stop=stop,
                )
            if returncode != 0:
                raise EvaluationInterrupted(f"closed_loop_eval exited with code {returncode}")
            if server_owned.proc.poll() is not None:
                raise EvaluationInterrupted("action server exited before batch validation")
        except BaseException as error:  # noqa: BLE001
            failure = _error(error)
        finally:
            report(worker_id, stage="process_cleanup")
            for name, owned in (("simulator", sim_owned), ("server", server_owned)):
                if owned is None:
                    continue
                try:
                    cleanup[name] = owned.close()
                except BaseException as error:  # noqa: BLE001
                    cleanup[name] = owned.cleanup
                    secondary_errors.append(f"cleanup {name}: {_error(error)}")
                    stop.set()
            failure = failure or (secondary_errors[0] if secondary_errors else None)
            try:
                queue_api.atomic_write_json(attempt / "process_cleanup.json", cleanup)
                if failure is None:
                    stage = "evidence_validation"
                    report(worker_id, stage="result_validation")
                    verify_inputs(job, "pre_commit")
                    finish_attempt(
                        attempt,
                        digest=digest,
                        runtime_digest=runtime,
                        expected_trials=batch_args.num_test_episodes,
                        video_mode=batch_args.save_generated_video,
                        rollout_enabled=batch_args.save_rollout_mp4,
                        init_png_enabled=batch_args.save_init_png,
                        sim_python=batch_args.sim_python,
                        deadline=deadline,
                        stop=stop,
                    )
                    committed = True
                    if on_completed is not None:
                        stage = "source_revalidation"
                        if stop.is_set():
                            raise EvaluationInterrupted("evaluation cancelled before completed source revalidation")
                        if time.monotonic() >= deadline:
                            raise EvaluationInterrupted("task wall timeout before completed source revalidation")
                        on_completed(dict(job, validation_deadline=deadline, validation_stop=stop))
                        if stop.is_set():
                            raise EvaluationInterrupted("evaluation cancelled during completed source revalidation")
                        if time.monotonic() >= deadline:
                            raise EvaluationInterrupted("task wall timeout during completed source revalidation")
                else:
                    fail_attempt(attempt, failure)
            except BaseException as error:  # noqa: BLE001
                message = f"{stage}: {_error(error)}"
                if failure is not None:
                    secondary_errors.append(message)
                failure = failure or message
                # COMPLETE remains a truthful native Attempt result if a later
                # catalog callback fails. The invocation still returns an error.
                if not committed:
                    try:
                        fail_attempt(attempt, failure)
                    except BaseException as marker_error:  # noqa: BLE001
                        secondary_errors.append(f"failure marker: {_error(marker_error)}")
            row.update(
                error=failure,
                secondary_errors=secondary_errors,
                returncode=returncode,
                cleanup=cleanup,
                committed=committed,
                elapsed_s=round(time.monotonic() - started, 3),
                stage=stage,
                server_log=str(server_log_path),
            )
            with lock:
                results.append(row)
                if committed:
                    completed.append(dict(row))
                if failure:
                    errors.append(dict(row, stage=stage, server_log=str(server_log_path)))
            if failure and args.on_infrastructure_error == "stop":
                stop.set()
            report(
                worker_id,
                event="task_error" if failure else "task_complete",
                stage="failed" if failure else "complete",
                error=failure,
            )

    def worker(worker_id, gpu):
        worker_dir = output_root / f"_worker{worker_id:02d}_gpu{gpu}"
        try:
            report(worker_id, gpu=gpu, stage="worker_initialization")
            _safe(worker_dir)
            worker_dir.mkdir()  # Invocation-local exclusive logs, never overwrite history.
            log_path = worker_dir / "action_server.log"
            with log_path.open("xb", buffering=0) as server_log:
                while not stop.is_set():
                    try:
                        job = work.get_nowait()
                    except queue.Empty:
                        break
                    try:
                        execute_job(job, worker_id, gpu, server_log, log_path)
                    finally:
                        work.task_done()
        except BaseException as error:  # noqa: BLE001
            stop.set()
            register(
                {"worker": worker_id, "gpu": gpu, "stage": "worker_initialization_or_loop", "error": _error(error)}
            )
            report(worker_id, event="error", stage="failed", error=_error(error))

    def cancel(signum, _frame):
        # Python invokes handlers on the main thread, including while that
        # thread holds a result/Event lock. Workers observe this plain flag via
        # is_set(); never re-enter threading locks from the signal callback.
        stop.signals.append(signum)

    handlers, threads = {}, []
    if threading.current_thread() is threading.main_thread():
        for signum in (signal.SIGTERM, signal.SIGINT):
            handlers[signum] = signal.signal(signum, cancel)
    try:
        try:
            observer.start()
        except Exception:
            pass
        try:
            for worker_id, gpu in enumerate(gpus):
                thread = threading.Thread(target=worker, args=(worker_id, gpu), name=f"robocasa-gpu-{gpu}")
                thread.start()
                threads.append(thread)
        except BaseException as error:  # noqa: BLE001
            register({"stage": "thread_start", "error": _error(error)})
            stop.set()
        try:
            for thread in threads:
                thread.join()
        except BaseException as error:  # noqa: BLE001
            register({"stage": "thread_join", "error": _error(error)})
            stop.set()
            for thread in threads:
                thread.join()
    finally:
        if any(thread.is_alive() for thread in threads):
            stop.set()
        for thread in threads:
            if thread.is_alive():
                thread.join()
        try:
            observer.close()
        except Exception:
            pass
        for signum, handler in handlers.items():
            signal.signal(signum, handler)
    for signum in stop.signals:
        register({"stage": "owner_cancel", "error": f"Owner signal {signum}"})
    finished = {row["attempt_dir"] for row in results}
    for job in prepared:
        if str(job["attempt_dir"]) not in finished:
            register(
                {
                    "task": job["task"],
                    "attempt_dir": str(job["attempt_dir"]),
                    "stage": "not_executed",
                    "error": "reserved source did not execute after worker failure or cancellation",
                }
            )
    return {
        "completed": sorted(completed, key=lambda row: row["attempt_dir"]),
        "source_attempts": [row["attempt_dir"] for row in results],
        "jobs": sorted(results, key=lambda row: row["attempt_dir"]),
        "errors": errors,
        "cancelled": stop.is_set(),
    }
