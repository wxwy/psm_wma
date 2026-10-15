#!/usr/bin/env python3
"""Run the V3 RoboCasa target-atomic screening with persistent per-GPU workers.

Each worker owns one GPU, one action-policy server and one simulator subprocess at a time.
Workers pull tasks from a shared deterministic queue; the model is loaded once per GPU, not
once per task.  The child evaluator owns rollout semantics and Local-TTT telemetry.
"""

from __future__ import annotations

import argparse
import ctypes
import json
import math
import os
import queue
import signal
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.request
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v3_evaluation_identity import (
    build_evaluation_identity,
    claim_evaluation_run,
    screening_metrics,
    validate_task_results,
)

ROOT = Path(__file__).resolve().parents[1]
CHILD = ROOT / "cosmos-framework"


def _read_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as response:  # noqa: S310 - localhost only
        return json.loads(response.read().decode("utf-8"))


def discover_task_datasets(dataset_root: Path, expected_tasks: int) -> list[tuple[str, Path]]:
    """Discover one eval LeRobot dir per underlying RoboCasa task via dataset_meta env_name."""
    mapping: dict[str, Path] = {}
    for meta in sorted(dataset_root.glob("**/extras/dataset_meta.json")):
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
            env_name = str(payload["env_args"]["env_name"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise ValueError(f"invalid RoboCasa dataset metadata: {meta}: {error}") from error
        lerobot = meta.parent.parent.resolve()
        previous = mapping.get(env_name)
        if previous is not None and previous != lerobot:
            raise ValueError(
                f"task {env_name!r} resolves to multiple eval datasets: {previous} and {lerobot}; "
                "provide a dataset root with exactly one canonical eval source per task"
            )
        mapping[env_name] = lerobot
    if len(mapping) != expected_tasks:
        raise ValueError(
            f"expected exactly {expected_tasks} underlying RoboCasa eval tasks, found {len(mapping)} "
            f"under {dataset_root}: {sorted(mapping)}"
        )
    return sorted(mapping.items())


def wait_server(proc: subprocess.Popen, port: int, timeout: float, stop: threading.Event) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/info"
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        if stop.is_set():
            raise ExecutionCancelled("server startup cancelled")
        if proc.poll() is not None:
            raise RuntimeError(f"action server exited early with code {proc.returncode}")
        try:
            info = _read_json(url, timeout=min(5.0, max(0.001, deadline - time.monotonic())))
            if (info.get("local_memory") or {}).get("mode") != "required":
                raise RuntimeError(f"server {port} did not enter required Local-TTT mode: {info.get('local_memory')}")
            return info
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            last_error = error
            stop.wait(min(0.2, max(0.0, deadline - time.monotonic())))
    raise RuntimeError(f"action server {port} not ready before timeout; last_error={last_error!r}")


def atomic_write_json(path: Path, value: Any) -> None:
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, prefix="." + path.name, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            json.dump(value, handle, indent=2, ensure_ascii=False, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


class ExecutionCancelled(RuntimeError):
    """Infrastructure cancellation, never a behavioral episode failure."""


class TaskDeadlineExceeded(TimeoutError):
    """The simulator process exceeded its total wall-time budget."""


class ProcessCleanupError(RuntimeError):
    """An owned process group could not be completely reaped within its budget."""


@contextmanager
def child_subreaper():
    """Reap orphaned grandchildren from our process groups on Linux, including containers.

    No unrelated PID is waited for or signalled. Restore the caller's subreaper
    setting afterwards; the coordinator is the only owner of this context.
    """
    if not sys.platform.startswith("linux"):
        raise RuntimeError("E1 owned-descendant cleanup requires Linux PR_SET_CHILD_SUBREAPER")
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    if libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0 or libc.prctl(36, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "cannot enable owned-descendant reaping")
    try:
        yield
    finally:
        if libc.prctl(36, previous.value, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "cannot restore child subreaper setting")


class OwnedProcess:
    """An exclusively owned POSIX session; cleanup never targets a borrowed server.

    Descendants must stay in this session's process group. Real simulator/server
    entrypoints do not daemonize or escape it with setsid/setpgid.
    """

    def __init__(self, command: list[str], *, cwd: Path, env: dict, log) -> None:
        self.process = subprocess.Popen(
            command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
        )
        self.pgid = self.process.pid
        self._lock = threading.Lock()
        self._closed = False

    def _signal(self, sig: int) -> None:
        try:
            os.killpg(self.pgid, sig)
        except ProcessLookupError:
            pass

    def _group_exists(self) -> bool:
        try:
            os.killpg(self.pgid, 0)
        except ProcessLookupError:
            return False
        return True

    def _reap_until(self, deadline: float) -> bool:
        while True:
            # Reap the Popen child with Popen, then only adopted children from
            # this exact group. Never steal another worker's wait status.
            if self.process.poll() is not None:
                while True:
                    try:
                        pid, _ = os.waitpid(-self.pgid, os.WNOHANG)
                    except ChildProcessError:
                        break
                    if pid == 0:
                        break
            if not self._group_exists():
                self.process.wait(timeout=max(0.001, deadline - time.monotonic()))
                return True
            if time.monotonic() >= deadline:
                return False
            time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))

    def close(self, timeout: float) -> None:
        with self._lock:
            if self._closed:
                return
            self._signal(signal.SIGTERM)
            if not self._reap_until(time.monotonic() + timeout):
                self._signal(signal.SIGKILL)
                if not self._reap_until(time.monotonic() + timeout):
                    raise ProcessCleanupError(f"owned process group {self.pgid} survived TERM/KILL/reap")
            self._closed = True

    def wait_task(self, *, timeout: float, stop: threading.Event) -> int:
        deadline = time.monotonic() + timeout
        while True:
            code = self.process.poll()
            if code is not None:
                return code
            if stop.is_set():
                raise ExecutionCancelled("simulator cancelled by coordinator/worker failure")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TaskDeadlineExceeded(f"simulator exceeded task wall deadline ({timeout:g}s)")
            stop.wait(min(0.05, remaining))


def positive_finite_seconds(value: str) -> float:
    seconds = float(value)
    if not math.isfinite(seconds) or seconds <= 0:
        raise argparse.ArgumentTypeError("timeout must be finite and positive")
    return seconds


def task_result(
    dataset_dir: Path,
    output_dir: Path,
    worker: int,
    gpu: str,
    elapsed_s: float,
    *,
    run_digest: str,
    expected_trials: int,
) -> dict[str, Any]:
    result_file = output_dir / "results.json"
    if not result_file.is_file():
        raise FileNotFoundError(f"task eval did not write {result_file}")
    rows = json.loads(result_file.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"task eval wrote invalid results: {result_file}")
    validate_task_results(rows, digest=run_digest, expected_trials=expected_trials)
    successes = sum(bool(row.get("policy")) for row in rows)
    return {
        "dataset_dir": str(dataset_dir),
        "worker": worker,
        "gpu": gpu,
        "trials": len(rows),
        "successes": successes,
        "sr": successes / len(rows),
        "elapsed_s": round(elapsed_s, 3),
        "results_file": str(result_file),
        "rollout_mp4s": sorted(str(path) for path in output_dir.glob("rollout*.mp4")),
        "rollouts": rows,
        "error": "; ".join(row["error"] for row in rows if row.get("error")) or None,
        "evaluation_run_digest": run_digest,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--config-file", type=Path)
    parser.add_argument("--server-python", type=Path, default=CHILD / ".venv/bin/python")
    parser.add_argument("--sim-python", type=Path, required=True)
    parser.add_argument("--gpus", default="0,1,2,3,4,5,6,7")
    parser.add_argument("--base-port", type=int, default=8912)
    parser.add_argument("--expected-tasks", type=int, default=18)
    parser.add_argument("--num-test-episodes", type=int, default=1)
    parser.add_argument("--action-horizon", type=int, default=16)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-steps", type=int, default=30)
    parser.add_argument("--guidance", type=float, default=1.0)
    parser.add_argument("--timeout", type=positive_finite_seconds, default=600.0, help="HTTP/server startup seconds")
    parser.add_argument(
        "--task-timeout",
        type=positive_finite_seconds,
        default=3600.0,
        help="total simulator process seconds per task, across all episodes (default: 3600)",
    )
    parser.add_argument(
        "--shutdown-timeout",
        type=positive_finite_seconds,
        default=5.0,
        help="seconds for each owned-group TERM and KILL/reap phase (default: 5)",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    checkpoint = args.checkpoint_path.resolve()
    if not (checkpoint / "model").is_dir():
        raise SystemExit(f"checkpoint DCP model/ missing: {checkpoint}")
    config_file = (
        args.config_file.resolve()
        if args.config_file is not None
        else (checkpoint.parent.parent / "config.yaml").resolve()
    )
    if not config_file.is_file():
        raise SystemExit(f"config file missing: {config_file}")
    if not args.server_python.is_file() or not os.access(args.server_python, os.X_OK):
        raise SystemExit(f"server python not executable: {args.server_python}")
    if not args.sim_python.is_file() or not os.access(args.sim_python, os.X_OK):
        raise SystemExit(f"sim python not executable: {args.sim_python}")
    if not 1 <= args.action_horizon <= 16:
        raise SystemExit("required Local-TTT screening requires 1 <= action_horizon <= 16")
    if args.num_test_episodes <= 0:
        raise SystemExit("--num-test-episodes must be positive")

    gpus = [item.strip() for item in args.gpus.split(",") if item.strip()]
    if not gpus or len(set(gpus)) != len(gpus):
        raise SystemExit("--gpus must contain unique GPU ids")
    tasks = discover_task_datasets(args.dataset_root.resolve(), args.expected_tasks)
    join_budget = (
        args.timeout + len(tasks) * (args.task_timeout + 2 * args.shutdown_timeout) + 2 * args.shutdown_timeout + 10
    )
    if not math.isfinite(join_budget):
        raise SystemExit("combined worker deadline must be finite")

    output_root = args.output_dir.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_evaluation_identity(
        root=ROOT,
        checkpoint=checkpoint,
        config_file=config_file,
        tasks=tasks,
        protocol={
            "seed": args.seed,
            "R": args.action_horizon,
            "H_pred": 16,
            "num_steps": args.num_steps,
            "guidance": args.guidance,
            "trials": args.num_test_episodes,
            "fps": 20,
            "camera_set": "left_wrist",
            "use_state": True,
            "base_encoding": "raw",
            "local_memory_mode": "required",
            "image_size": 256,
            "cam_size": 256,
            "success_latch": 1,
            "execution_contract": "v3_screening_e1_owned_process_groups",
            "task_timeout_s": args.task_timeout,
            "shutdown_timeout_s": args.shutdown_timeout,
        },
    )
    run_digest = claim_evaluation_run(output_root, manifest, resume=args.resume)
    execution_id = uuid.uuid4().hex
    summary_path = output_root / "screening_summary.json"
    work: queue.Queue[tuple[str, Path]] = queue.Queue()
    results: dict[str, dict[str, Any]] = {}
    result_lock = threading.RLock()
    worker_errors: list[dict[str, Any]] = []
    processes: list[tuple[OwnedProcess, int, str, str, Path, Path | None]] = []
    execution_finished = False

    for task, dataset_dir in tasks:
        task_out = output_root / task
        existing = task_out / "results.json"
        if args.resume and existing.is_file():
            results[task] = task_result(
                dataset_dir, task_out, -1, "resume", 0.0, run_digest=run_digest, expected_trials=args.num_test_episodes
            )
            continue
        elif existing.exists():
            raise SystemExit(f"refusing to overwrite existing task result without --resume: {existing}")
        work.put((task, dataset_dir))

    stop = threading.Event()

    def publish() -> None:
        with result_lock:
            ordered = {task: results[task] for task, _ in tasks if task in results}
            trials = sum(int(row.get("trials", 0)) for row in ordered.values())
            successes = sum(int(row.get("successes", 0)) for row in ordered.values())
            payload = {
                "checkpoint": str(checkpoint),
                "config_file": str(config_file),
                "action_horizon": args.action_horizon,
                "seed": args.seed,
                "expected_tasks": args.expected_tasks,
                "completed_tasks": len(ordered),
                "task_failures": sum(row.get("error") is not None for row in ordered.values()),
                "total_trials": trials,
                "total_successes": successes,
                "sr": successes / trials if trials else None,
                "tasks": ordered,
            }
            payload.update(
                screening_metrics(results, tasks=[task for task, _ in tasks], expected_trials=args.num_test_episodes)
            )
            payload["task_statistics_status"] = payload["status"]
            payload["worker_errors"] = list(worker_errors)
            payload["execution_status"] = (
                "FAILED"
                if worker_errors or payload["task_failures"]
                else payload["status"]
                if execution_finished
                else "RUNNING"
            )
            payload["status"] = payload["execution_status"]
            payload["sr_valid"] = payload["status"] == "COMPLETE" and payload["task_failures"] == 0
            payload["diagnostic_sr"] = payload["sr"]
            if not payload["sr_valid"]:
                payload["sr"] = None
            payload["execution_contract"] = {
                "version": "v3_screening_e1_owned_process_groups",
                "task_timeout_s": args.task_timeout,
                "shutdown_timeout_s": args.shutdown_timeout,
                "http_timeout_s": args.timeout,
            }
            payload["evaluation_run_digest"] = run_digest
            payload["execution_id"] = execution_id
            payload["worker_error_history"] = str(output_root / "worker_errors.jsonl")
            if execution_finished:
                atomic_write_json(output_root / f"execution_{execution_id}.json", payload)
            atomic_write_json(summary_path, payload)

    def record_error(exc, worker_id, gpu, phase, server_log, task_log=None, task=None, returncode=None) -> None:
        error = {
            "worker_id": worker_id,
            "gpu": gpu,
            "phase": phase,
            "task": task,
            "exception_type": type(exc).__name__,
            "message": str(exc),
            "traceback": "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)),
            "server_log": str(server_log) if server_log is not None else None,
            "task_log": str(task_log) if task_log is not None else None,
            "returncode": returncode,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_id": execution_id,
        }
        stop.set()
        with result_lock:
            worker_errors.append(error)
            # Append-only error ledger survives later summary publication/resume.
            with (output_root / "worker_errors.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(error, ensure_ascii=False, allow_nan=False) + "\n")
                handle.flush()
                os.fsync(handle.fileno())

    def start_process(command, *, cwd, env, log, worker_id, gpu, phase, server_log, task_log=None):
        owned = OwnedProcess(command, cwd=cwd, env=env, log=log)
        with result_lock:
            processes.append((owned, worker_id, gpu, phase, server_log, task_log))
        return owned

    def close_process(owned, worker_id, gpu, phase, server_log, task_log=None, task=None):
        try:
            owned.close(args.shutdown_timeout)
        except Exception as exc:
            record_error(exc, worker_id, gpu, phase, server_log, task_log, task, owned.process.poll())

    publish()

    def worker(worker_id: int, gpu: str) -> None:
        port = args.base_port + worker_id
        worker_dir = output_root / f"_worker{worker_id:02d}_gpu{gpu}"
        server_log_path = worker_dir / "action_server.log"
        server_env = os.environ.copy()
        server_env["CUDA_VISIBLE_DEVICES"] = gpu
        server_env["PYTHONPATH"] = str(CHILD) + (
            os.pathsep + server_env["PYTHONPATH"] if server_env.get("PYTHONPATH") else ""
        )
        server_command = [
            str(args.server_python),
            "-m",
            "cosmos_framework.scripts.action_policy_server_robocasa",
            "--checkpoint-path",
            str(checkpoint),
            "--config-file",
            str(config_file),
            "--port",
            str(port),
            "--raw-action-dim",
            "15",
            "--local-memory-mode",
            "required",
            "--local-memory-max-sessions",
            "1",
            "--num-steps",
            str(args.num_steps),
            "--guidance",
            str(args.guidance),
            "--fps",
            "20",
            "--http-400-on-error",
        ]
        server = None
        phase = "server_start"
        task = None
        task_log_path = None
        try:
            worker_dir.mkdir(parents=True, exist_ok=True)
            with server_log_path.open("ab", buffering=0) as server_log:
                server = start_process(
                    server_command,
                    cwd=CHILD,
                    env=server_env,
                    log=server_log,
                    worker_id=worker_id,
                    gpu=gpu,
                    phase="server",
                    server_log=server_log_path,
                )
                phase = "server_ready"
                info = wait_server(server.process, port, args.timeout, stop)
                atomic_write_json(worker_dir / f"server_info_{execution_id}.json", info)
                while not stop.is_set():
                    phase = "task_schedule"
                    try:
                        task, dataset_dir = work.get_nowait()
                    except queue.Empty:
                        break
                    task_out = output_root / task
                    task_log_path = task_out / "eval.log"
                    sim_env = os.environ.copy()
                    sim_env["CUDA_VISIBLE_DEVICES"] = gpu
                    sim_env["MUJOCO_GL"] = sim_env.get("MUJOCO_GL", "egl")
                    sim_env["PYTHONPATH"] = str(CHILD) + (
                        os.pathsep + sim_env["PYTHONPATH"] if sim_env.get("PYTHONPATH") else ""
                    )
                    command = [
                        str(args.sim_python),
                        str(CHILD / "cosmos_framework/simulation/robocasa/closed_loop_eval.py"),
                        "--server-url",
                        f"http://127.0.0.1:{port}",
                        "--dataset-dir",
                        str(dataset_dir),
                        "--evaluation-run-digest",
                        run_digest,
                        "--num-test-episodes",
                        str(args.num_test_episodes),
                        "--action-horizon",
                        str(args.action_horizon),
                        "--image-size",
                        "256",
                        "--cam-size",
                        "256",
                        "--camera-set",
                        "left_wrist",
                        "--use-state",
                        "--use-base-action",
                        "--base-encoding",
                        "raw",
                        "--local-memory-mode",
                        "required",
                        "--success-latch",
                        "1",
                        "--seed",
                        str(args.seed),
                        "--timeout",
                        str(args.timeout),
                        "--output-dir",
                        str(task_out),
                    ]
                    started = time.monotonic()
                    error: str | None = None
                    returncode = -1
                    row = None
                    simulator = None
                    task_exception = None
                    try:
                        phase = "task_start"
                        task_out.mkdir(parents=True, exist_ok=True)
                        with task_log_path.open("ab", buffering=0) as task_log:
                            simulator = start_process(
                                command,
                                cwd=CHILD,
                                env=sim_env,
                                log=task_log,
                                worker_id=worker_id,
                                gpu=gpu,
                                phase="simulator",
                                server_log=server_log_path,
                                task_log=task_log_path,
                            )
                            phase = "task_wait"
                            returncode = simulator.wait_task(timeout=args.task_timeout, stop=stop)
                        phase = "task_results"
                        row = task_result(
                            dataset_dir,
                            task_out,
                            worker_id,
                            gpu,
                            time.monotonic() - started,
                            run_digest=run_digest,
                            expected_trials=args.num_test_episodes,
                        )
                        if returncode != 0:
                            raise RuntimeError(f"closed_loop_eval exited with code {returncode}")
                    except BaseException as exc:  # noqa: BLE001
                        error = f"{type(exc).__name__}: {exc}"
                        task_exception = exc
                        stop.set()
                    finally:
                        if simulator is not None:
                            close_process(
                                simulator, worker_id, gpu, "task_cleanup", server_log_path, task_log_path, task
                            )
                            returncode = simulator.process.poll()
                    if task_exception is not None:
                        record_error(
                            task_exception,
                            worker_id,
                            gpu,
                            phase,
                            server_log_path,
                            task_log_path,
                            task,
                            returncode if simulator is not None else None,
                        )
                    if error is not None and row is None:
                        row = {
                            "dataset_dir": str(dataset_dir),
                            "worker": worker_id,
                            "gpu": gpu,
                            "trials": 0,
                            "successes": 0,
                            "sr": None,
                            "elapsed_s": round(time.monotonic() - started, 3),
                            "results_file": str(task_out / "results.json"),
                            "rollout_mp4s": sorted(str(path) for path in task_out.glob("rollout*.mp4")),
                            "rollouts": [],
                            "returncode": returncode,
                            "error": error,
                            "infrastructure_failure": True,
                        }
                    if error is not None:
                        row["error"] = error
                        row["returncode"] = returncode
                    with result_lock:
                        results[task] = row
                    publish()
                    work.task_done()
                phase = "server_exit"
                if server.process.poll() is not None:
                    raise RuntimeError(f"action server exited unexpectedly with code {server.process.returncode}")
        except BaseException as exc:  # noqa: BLE001
            record_error(
                exc,
                worker_id,
                gpu,
                phase,
                server_log_path,
                task_log_path,
                task,
                server.process.poll() if server is not None else None,
            )
            if task is not None:
                with result_lock:
                    # Keep existing task outcome/counts; annotate infrastructure health separately.
                    if task not in results:
                        results[task] = {
                            "trials": 0,
                            "successes": 0,
                            "error": str(exc),
                            "infrastructure_failure": True,
                            "task_log": str(task_log_path),
                        }
        finally:
            if server is not None:
                close_process(server, worker_id, gpu, "server_cleanup", server_log_path, task_log_path, task)
            publish()

    threads = [
        threading.Thread(target=worker, args=(index, gpu), name=f"robocasa-gpu-{gpu}", daemon=True)
        for index, gpu in enumerate(gpus)
    ]
    old_handlers = {}
    received_signal = []
    reaper = child_subreaper()
    reaper_active = False

    def cancel(signum, _frame):
        received_signal.append(signum)
        stop.set()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            old_handlers[sig] = signal.signal(sig, cancel)
        reaper.__enter__()
        reaper_active = True
        for thread in threads:
            thread.start()
        # Even a worker implementation bug cannot cause an unlimited join.
        deadline = time.monotonic() + join_budget
        while any(thread.is_alive() for thread in threads):
            if received_signal:
                raise ExecutionCancelled(f"coordinator received signal {received_signal[0]}")
            if time.monotonic() >= deadline:
                raise TaskDeadlineExceeded("coordinator worker-join deadline exceeded")
            for thread in threads:
                thread.join(timeout=0.05)
        if received_signal:
            raise ExecutionCancelled(f"coordinator received signal {received_signal[0]}")
    except BaseException as exc:  # noqa: BLE001
        record_error(exc, None, None, "coordinator", None)
    finally:
        stop.set()
        with result_lock:
            owned_processes = list(processes)
        for owned, worker_id, gpu, phase, server_log, task_log in owned_processes:
            close_process(owned, worker_id, gpu, phase + "_final_cleanup", server_log, task_log)
        deadline = time.monotonic() + 2 * args.shutdown_timeout + 1
        for thread in threads:
            if thread.ident is not None:
                thread.join(timeout=max(0.0, deadline - time.monotonic()))
        if any(thread.is_alive() for thread in threads):
            record_error(
                ProcessCleanupError("worker did not finish bounded cancellation"), None, None, "worker_join", None
            )
        if reaper_active:
            try:
                reaper.__exit__(None, None, None)
            except Exception as exc:
                record_error(exc, None, None, "subreaper_restore", None)
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)

    if received_signal and not worker_errors:
        record_error(
            ExecutionCancelled(f"coordinator received signal {received_signal[0]}"), None, None, "coordinator", None
        )
    execution_finished = True
    publish()
    with result_lock:
        task_rows = [results.get(task) for task, _ in tasks]
        missing = [task for (task, _), row in zip(tasks, task_rows, strict=True) if row is None]
        failed = [task for (task, _), row in zip(tasks, task_rows, strict=True) if row is not None and row.get("error")]
    if missing or failed or worker_errors:
        print(f"screening incomplete: missing={missing} failed={failed}; summary={summary_path}")
        return 1
    print(f"screening complete: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
