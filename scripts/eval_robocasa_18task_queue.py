#!/usr/bin/env python3
"""Run the V3 RoboCasa target-atomic screening with persistent per-GPU workers.

Each worker owns one GPU, one action-policy server and one simulator subprocess at a time.
Workers pull tasks from a shared deterministic queue; the model is loaded once per GPU, not
once per task.  The child evaluator owns rollout semantics and Local-TTT telemetry.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import socket
import subprocess
import threading
import time
import urllib.error
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from typing import Any

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
            try:
                listener.bind(("0.0.0.0", port))
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
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/info"
    last_error: BaseException | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            raise RuntimeError(f"action server exited early with code {proc.returncode}")
        try:
            info = _read_json(url, timeout=min(5.0, max(0.001, deadline - time.monotonic())))
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
            last_error = error
            time.sleep(min(2.0, max(0.0, deadline - time.monotonic())))
            continue
        validate_server_info(
            info, checkpoint=checkpoint, config_file=config_file, num_steps=num_steps, guidance=guidance
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
            payload["evaluation_run_digest"] = run_digest
            worker_errors = {key: row for key, row in results.items() if key.startswith("_worker_")}
            payload["worker_errors"] = worker_errors
            if worker_errors:
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
            "--http-400-on-error",
        ]
        with server_log_path.open("ab", buffering=0) as server_log:
            server = None
            try:
                require_free_ports([port])
                server = subprocess.Popen(
                    server_command,
                    cwd=CHILD,
                    env=server_env,
                    stdout=server_log,
                    stderr=subprocess.STDOUT,
                )
                info = wait_server(
                    server,
                    port,
                    args.timeout,
                    checkpoint=checkpoint,
                    config_file=config_file,
                    num_steps=args.num_steps,
                    guidance=args.guidance,
                )
                if sha256_file(config_file) != manifest["identity"]["config_sha256"]:
                    raise ValueError("action server config file changed since evaluation identity was frozen")
                atomic_write_json(worker_dir / "server_info.json", info)
                atomic_write_json(worker_dir / "server_process.json", {"pid": server.pid, "port": port})
                while not stop.is_set():
                    if server.poll() is not None:
                        raise RuntimeError(f"action server exited during screening with code {server.returncode}")
                    try:
                        task, dataset_dir = work.get_nowait()
                    except queue.Empty:
                        break
                    task_out = output_root / task
                    task_out.mkdir(parents=True, exist_ok=True)
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
                    try:
                        with task_log_path.open("ab", buffering=0) as task_log:
                            completed = subprocess.run(
                                command,
                                cwd=CHILD,
                                env=sim_env,
                                stdout=task_log,
                                stderr=subprocess.STDOUT,
                                check=False,
                            )
                        returncode = completed.returncode
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
                            error = f"closed_loop_eval exited with code {returncode}"
                    except BaseException as exc:  # noqa: BLE001
                        error = f"{type(exc).__name__}: {exc}"
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
                        }
                    if error is not None:
                        row["error"] = error
                        row["returncode"] = returncode
                    with result_lock:
                        results[task] = row
                    publish()
                    work.task_done()
            except BaseException as exc:  # noqa: BLE001
                stop.set()
                with result_lock:
                    results[f"_worker_{worker_id}"] = {
                        "worker": worker_id,
                        "gpu": gpu,
                        "error": f"{type(exc).__name__}: {exc}",
                        "server_log": str(server_log_path),
                    }
                publish()
            finally:
                if server is not None:
                    server.terminate()
                    try:
                        server.wait(timeout=20)
                    except subprocess.TimeoutExpired:
                        server.kill()
                        server.wait()

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
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

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
