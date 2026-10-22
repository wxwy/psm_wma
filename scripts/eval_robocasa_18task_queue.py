#!/usr/bin/env python3
"""Run RoboCasa with one isolated Server/Simulator pair per task and GPU worker."""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import signal
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from robocasa_processes import (
    EpisodeProgress,
    EvaluationInterrupted,
    OwnedProcess,
    positive_seconds,
    supervise_simulator,
)
from v3_evaluation_identity import (
    build_evaluation_identity,
    claim_evaluation_run,
    screening_metrics,
    sha256_file,
    validate_task_results,
)

ROOT = Path(__file__).resolve().parents[1]
CHILD = ROOT / "cosmos-framework"


def _read_json(url: str, timeout: float = 5.0) -> dict[str, Any]:
    # /info must come from this loopback listener, never an environment HTTP proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(url, timeout=timeout) as response:  # noqa: S310 - localhost only
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


def require_free_ports(ports: list[int]) -> None:
    """Check every requested IPv4 bind before claiming output or launching a model."""
    with ExitStack() as stack:
        for port in ports:
            if type(port) is not int or not 1 <= port <= 65535:
                raise ValueError(f"invalid action server port: {port}")
            listener = stack.enter_context(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
            # Match ThreadingHTTPServer: a stopped owned server can leave
            # TIME_WAIT sockets. This never permits binding an active listener.
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                listener.bind(("0.0.0.0", port))
                listener.listen(1)
            except OSError as error:
                raise RuntimeError(f"action server port {port} unavailable: {error}") from error


def validate_server_info(info: Any, *, checkpoint: Path, config_file: Path, num_steps: int, guidance: float) -> None:
    """Validate the effective server configuration, not just HTTP readiness."""
    if not isinstance(info, dict):
        raise ValueError("action server /info must be an object")
    # CLI/manifest retain the requested root; the Child reports its selected model DCP.
    for name, expected in (("checkpoint", (checkpoint / "model").resolve()), ("config_file", config_file)):
        value = info.get(name)
        if not isinstance(value, str) or not Path(value).is_absolute() or Path(value).resolve() != expected:
            raise ValueError(f"action server {name} mismatch: expected {expected}, got {value!r}")
    for name, expected in (
        ("raw_action_dim", 15),
        ("action_chunk_size", 16),
        ("max_action_dim", 64),
        ("num_steps", num_steps),
        ("fps", 20),
        ("seed", 0),  # Policy sampler default; --seed on this queue is the environment seed.
    ):
        if type(info.get(name)) is not int or info[name] != expected:
            raise ValueError(f"action server {name} mismatch: expected {expected}, got {info.get(name)!r}")
    if type(info.get("guidance")) not in (int, float) or info["guidance"] != guidance:
        raise ValueError("action server guidance mismatch")
    local = info.get("local_memory")
    if (
        info.get("requires_state") is not True
        or not isinstance(local, dict)
        or local.get("enabled") is not True
        or local.get("mode") != "required"
        or type(local.get("action_dim")) is not int
        or local["action_dim"] != 15
    ):
        raise ValueError("action server state/required Local-TTT protocol mismatch")


def require_owned_listener(proc: subprocess.Popen, port: int) -> None:
    """Linux same-user /proc proof closes the check-free→bind stale-server race.

    The existing Child serves HTTP in the Popen process itself. Never accept a
    foreign listener even if its /info happens to have identical paths/parameters.
    """
    try:
        process = Path("/proc") / str(proc.pid)
        sockets = set()
        for descriptor in (process / "fd").iterdir():
            try:
                sockets.add(os.readlink(descriptor))
            except FileNotFoundError:  # A transient, unrelated descriptor may close.
                continue
        for line in (process / "net/tcp").read_text().splitlines()[1:]:
            fields = line.split()
            address, hex_port = fields[1].split(":")
            if (
                fields[3] == "0A"
                and address in {"00000000", "0100007F"}
                and int(hex_port, 16) == port
                and f"socket:[{fields[9]}]" in sockets
            ):
                return
    except (OSError, ValueError, IndexError) as error:
        raise RuntimeError(f"cannot verify action server pid {proc.pid} owns port {port}: {error}") from error
    raise RuntimeError(f"action server pid {proc.pid} does not own port {port}")


def wait_server(
    proc: subprocess.Popen,
    port: int,
    timeout: float,
    *,
    checkpoint: Path,
    config_file: Path,
    num_steps: int,
    guidance: float,
    stop: threading.Event | None = None,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/info"
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        if stop is not None and stop.is_set():
            raise EvaluationInterrupted("evaluation cancelled during server startup")
        if proc.poll() is not None:
            raise RuntimeError(f"action server exited early with code {proc.returncode}")
        try:
            info = _read_json(url, timeout=min(5.0, max(0.001, deadline - time.monotonic())))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(min(0.1, max(0.0, deadline - time.monotonic())))
            continue
        validate_server_info(
            info,
            checkpoint=checkpoint,
            config_file=config_file,
            num_steps=num_steps,
            guidance=guidance,
        )
        require_owned_listener(proc, port)
        if proc.poll() is not None:
            raise RuntimeError(f"action server exited during identity verification with code {proc.returncode}")
        return info
    raise RuntimeError(f"action server {port} not ready before timeout; last_error={last_error!r}")


def atomic_write_json(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(temporary, path)


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
    parser.add_argument("--timeout", type=float, default=600.0)
    parser.add_argument("--server-start-timeout-s", type=float, default=None)
    parser.add_argument("--predict-request-timeout-s", type=float, default=None)
    parser.add_argument("--episode-wall-timeout-s", type=float, default=1800)
    parser.add_argument("--task-wall-timeout-s", type=float, default=10800)
    parser.add_argument("--terminate-grace-s", type=float, default=20)
    parser.add_argument("--server-lifecycle", choices=("per_task",), default="per_task")
    parser.add_argument(
        "--on-infrastructure-error",
        choices=("stop", "continue_with_new_server"),
        default="stop",
    )
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    args.server_start_timeout_s = (
        args.server_start_timeout_s if args.server_start_timeout_s is not None else args.timeout
    )
    args.predict_request_timeout_s = (
        args.predict_request_timeout_s if args.predict_request_timeout_s is not None else args.timeout
    )
    for seconds in (
        args.server_start_timeout_s,
        args.predict_request_timeout_s,
        args.episode_wall_timeout_s,
        args.task_wall_timeout_s,
        args.terminate_grace_s,
    ):
        positive_seconds(seconds)
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
    if args.num_steps <= 0 or not math.isfinite(args.guidance) or not math.isfinite(args.timeout) or args.timeout <= 0:
        raise SystemExit("--num-steps/--timeout must be positive and --guidance/--timeout finite")

    gpus = [item.strip() for item in args.gpus.split(",") if item.strip()]
    if not gpus or len(set(gpus)) != len(gpus):
        raise SystemExit("--gpus must contain unique GPU ids")
    require_free_ports([args.base_port + index for index in range(len(gpus))])
    tasks = discover_task_datasets(args.dataset_root.resolve(), args.expected_tasks)

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
            "server_action_chunk_size": 16,
            "raw_action_dim": 15,
            "max_action_dim": 64,
            "policy_seed": 0,
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
            "server_lifecycle": args.server_lifecycle,
            "on_infrastructure_error": args.on_infrastructure_error,
            "timeouts": {
                "server_start_s": args.server_start_timeout_s,
                "predict_request_s": args.predict_request_timeout_s,
                "episode_wall_s": args.episode_wall_timeout_s,
                "task_wall_s": args.task_wall_timeout_s,
                "terminate_grace_s": args.terminate_grace_s,
            },
        },
    )
    run_digest = claim_evaluation_run(output_root, manifest, resume=args.resume)
    summary_path = output_root / "screening_summary.json"
    work: queue.Queue[tuple[str, Path]] = queue.Queue()
    results: dict[str, dict[str, Any]] = {}
    result_lock = threading.Lock()

    for task, dataset_dir in tasks:
        task_out = output_root / task
        existing = task_out / "results.json"
        if args.resume and existing.is_file():
            results[task] = task_result(
                dataset_dir,
                task_out,
                -1,
                "resume",
                0.0,
                run_digest=run_digest,
                expected_trials=args.num_test_episodes,
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
                screening_metrics(
                    results,
                    tasks=[task for task, _ in tasks],
                    expected_trials=args.num_test_episodes,
                )
            )
            payload["evaluation_run_digest"] = run_digest
            worker_errors = {key: row for key, row in results.items() if key.startswith("_worker_")}
            payload["worker_errors"] = worker_errors
            if worker_errors or any(row.get("error") for row in ordered.values()):
                payload["status"] = "INCOMPLETE"
                payload["sr"] = None
            atomic_write_json(summary_path, payload)

    publish()

    def run_worker(worker_id: int, gpu: str) -> None:
        port = args.base_port + worker_id
        worker_dir = output_root / f"_worker{worker_id:02d}_gpu{gpu}"
        worker_dir.mkdir(parents=True, exist_ok=True)
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
            "--action-chunk-size",
            "16",
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
            "--no-guardrails",
            "--http-400-on-error",
        ]
        # Open the worker log before claiming a task, so even initialization
        # errors are preserved by the outer worker boundary.
        with server_log_path.open("ab", buffering=0) as server_log:
            while not stop.is_set():
                try:
                    task, dataset_dir = work.get_nowait()
                except queue.Empty:
                    break
                task_out = output_root / task
                started = time.monotonic()
                task_deadline = started + args.task_wall_timeout_s
                server_owned = sim_owned = None
                row, error, returncode = None, None, -1
                cleanup = {}
                stage = "server_start"
                try:
                    task_out.mkdir(parents=True, exist_ok=True)
                    require_free_ports([port])
                    server_owned = OwnedProcess(
                        server_command,
                        grace_s=args.terminate_grace_s,
                        cwd=CHILD,
                        env=server_env,
                        stdout=server_log,
                        stderr=subprocess.STDOUT,
                    )
                    server = server_owned.proc
                    info = wait_server(
                        server,
                        port,
                        min(
                            args.server_start_timeout_s,
                            max(0.001, task_deadline - time.monotonic()),
                        ),
                        checkpoint=checkpoint,
                        config_file=config_file,
                        num_steps=args.num_steps,
                        guidance=args.guidance,
                        stop=stop,
                    )
                    if sha256_file(config_file) != manifest["identity"]["config_sha256"]:
                        raise ValueError("action server config file changed since evaluation identity was frozen")
                    atomic_write_json(task_out / "server_info.json", info)
                    atomic_write_json(
                        task_out / "server_process.json",
                        {"pid": server.pid, "pgid": server_owned.pgid, "port": port},
                    )
                    sim_env = server_env.copy()
                    sim_env["MUJOCO_GL"] = sim_env.get("MUJOCO_GL", "egl")
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
                        str(args.predict_request_timeout_s),
                        "--output-dir",
                        str(task_out),
                        "--progress-file",
                        str(task_out / "episode_progress.jsonl"),
                    ]
                    atomic_write_json(
                        task_out / "commands.json",
                        {"server": server_command, "simulator": command},
                    )
                    stage = "simulator"
                    with (task_out / "eval.log").open("ab", buffering=0) as task_log:
                        sim_owned = OwnedProcess(
                            command,
                            grace_s=args.terminate_grace_s,
                            cwd=CHILD,
                            env=sim_env,
                            stdout=task_log,
                            stderr=subprocess.STDOUT,
                        )
                        progress = EpisodeProgress(
                            task_out / "episode_progress.jsonl",
                            digest=run_digest,
                            episodes=args.num_test_episodes,
                        )
                        returncode = supervise_simulator(
                            sim_owned,
                            server=server,
                            task_deadline=task_deadline,
                            episode_wall_s=args.episode_wall_timeout_s,
                            progress=progress,
                            stop=stop,
                        )
                    if returncode != 0:
                        raise EvaluationInterrupted(f"closed_loop_eval exited with code {returncode}")
                    row = task_result(
                        dataset_dir,
                        task_out,
                        worker_id,
                        gpu,
                        time.monotonic() - started,
                        run_digest=run_digest,
                        expected_trials=args.num_test_episodes,
                    )
                    if row.get("error"):
                        raise EvaluationInterrupted(row["error"])
                except BaseException as exc:  # noqa: BLE001
                    error = f"{type(exc).__name__}: {exc}"
                    if row is None and (task_out / "results.json").is_file():
                        try:
                            row = task_result(
                                dataset_dir,
                                task_out,
                                worker_id,
                                gpu,
                                time.monotonic() - started,
                                run_digest=run_digest,
                                expected_trials=args.num_test_episodes,
                            )
                        except Exception:
                            pass  # Raw partial files remain; never treat them as complete trials.
                finally:
                    # Both groups, including descendants of an already-dead leader,
                    # are reclaimed before another task can acquire this worker.
                    for name, owned in (
                        ("simulator", sim_owned),
                        ("server", server_owned),
                    ):
                        if owned is not None:
                            try:
                                cleanup[name] = owned.close()
                            except BaseException as exc:  # noqa: BLE001
                                cleanup[name] = owned.cleanup
                                error = error or f"cleanup {name}: {type(exc).__name__}: {exc}"
                    if row is None:
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
                        }
                    row.update(error=error, returncode=returncode, cleanup=cleanup)
                    # Cleanup failure is an independent error, never replacement of
                    # the primary failure. Evidence survives even after cancellation.
                    if task_out.is_dir():
                        atomic_write_json(task_out / "process_cleanup.json", cleanup)
                    with result_lock:
                        results[task] = row
                        if error:
                            results[f"_worker_{worker_id}_{task}"] = {
                                "worker": worker_id,
                                "gpu": gpu,
                                "task": task,
                                "stage": stage,
                                "error": error,
                                "cleanup": cleanup,
                                "server_log": str(server_log_path),
                            }
                    if (error and args.on_infrastructure_error == "stop") or any(
                        item.get("error") for item in cleanup.values()
                    ):
                        stop.set()
                    publish()
                    work.task_done()

    def worker(worker_id: int, gpu: str) -> None:
        # The service loop has its own failure/cleanup path. This entry boundary
        # also covers directory/log initialization and resource-context exits.
        try:
            run_worker(worker_id, gpu)
        except BaseException as exc:  # noqa: BLE001
            stop.set()
            with result_lock:
                results[f"_worker_{worker_id}"] = {
                    "worker": worker_id,
                    "gpu": gpu,
                    "error": f"{type(exc).__name__}: {exc}",
                    "server_log": str(output_root / f"_worker{worker_id:02d}_gpu{gpu}" / "action_server.log"),
                }
            publish()

    threads = [
        threading.Thread(target=worker, args=(index, gpu), name=f"robocasa-gpu-{gpu}", daemon=False)
        for index, gpu in enumerate(gpus)
    ]

    def cancel(signum, _frame):
        with result_lock:
            results["_worker_cancel"] = {"error": f"Owner signal {signum}"}
        stop.set()

    previous_handlers = {}
    if threading.current_thread() is threading.main_thread():
        for sig in (signal.SIGTERM, signal.SIGINT):
            previous_handlers[sig] = signal.signal(sig, cancel)
    try:
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)

    publish()
    with result_lock:
        task_rows = [results.get(task) for task, _ in tasks]
        missing = [task for (task, _), row in zip(tasks, task_rows, strict=True) if row is None]
        failed = [task for (task, _), row in zip(tasks, task_rows, strict=True) if row is not None and row.get("error")]
        worker_errors = [key for key in results if key.startswith("_worker_")]
    if missing or failed or worker_errors:
        print(
            f"screening incomplete: missing={missing} failed={failed} workers={worker_errors}; summary={summary_path}"
        )
        return 1
    print(f"screening complete: {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
