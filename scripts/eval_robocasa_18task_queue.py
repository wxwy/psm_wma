#!/usr/bin/env python3
"""Run RoboCasa with one isolated Server/Simulator pair per task and GPU worker."""

from __future__ import annotations

import fcntl
import json
import os
import queue
import re
import signal
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from typing import Any

from robocasa_eval_config import resolve
from robocasa_eval_results import fail_attempt, find_completed_attempt, finish_attempt, start_attempt
from robocasa_processes import (
    EpisodeProgress,
    EvaluationInterrupted,
    OwnedProcess,
    supervise_simulator,
)
from robocasa_vendor import build_verified_evaluation_identity
from v3_evaluation_identity import (
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


def discover_task_datasets(dataset_root: Path, expected_tasks: int | None = None) -> list[tuple[str, Path]]:
    """Discover one eval LeRobot dir per underlying RoboCasa task via dataset_meta env_name."""
    mapping: dict[str, Path] = {}
    for meta in sorted(dataset_root.glob("**/extras/dataset_meta.json")):
        try:
            payload = json.loads(meta.read_text(encoding="utf-8"))
            env_name = payload["env_args"]["env_name"]
            if not isinstance(env_name, str) or not env_name.isidentifier() or env_name == "all":
                raise ValueError("invalid underlying task class")
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
    if not mapping or (expected_tasks is not None and len(mapping) != expected_tasks):
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


def task_video_files(output_dir: Path) -> dict[str, list[str]]:
    """Classify actual artifacts, including partial videos without complete results."""
    files = [path for path in output_dir.glob("rollout*.mp4") if path.is_file()]
    return {
        "rollout_mp4s": sorted(str(path) for path in files if re.fullmatch(r"rollout\d+\.mp4", path.name)),
        "generated_mp4s": sorted(
            str(path) for path in files if re.fullmatch(r"rollout\d+_generated(?:_replan\d+)?\.mp4", path.name)
        ),
    }


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
        **task_video_files(output_dir),
        "rollouts": rows,
        "error": "; ".join(row["error"] for row in rows if row.get("error")) or None,
        "evaluation_run_digest": run_digest,
    }


def launch_environment(cache: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(CHILD) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["MUJOCO_GL"] = env.get("MUJOCO_GL", "egl")
    # Native JIT/controller imports must never write caches into locked vendors.
    env["NUMBA_CACHE_DIR"] = str(cache / "numba")
    env["MPLCONFIGDIR"] = str(cache / "matplotlib")
    env["XDG_CACHE_HOME"] = str(cache / "xdg")
    env["HF_HOME"] = env.get("HF_HOME") or str(cache / "huggingface")
    return env


def check_destination(output: Path, manifest: dict, *, resume: bool) -> None:
    """Read-only preview and run share namespace checks; never follow output symlinks."""
    if any(path.is_symlink() for path in (output, *output.parents)):
        raise ValueError("evaluation output path must not contain symlinks")
    if not output.exists():
        return
    if not output.is_dir():
        raise ValueError("evaluation output is not a directory")
    identity = output / "evaluation_manifest.json"
    if identity.is_symlink():
        raise ValueError("evaluation manifest must not be a symlink")
    if identity.exists():
        if not resume:
            raise FileExistsError("evaluation already exists; explicit same-identity resume required")
        if json.loads(identity.read_text()) != manifest:
            raise ValueError("evaluation identity changed: checkpoint/source/config/protocol/task/seed/R")
    elif any(output.iterdir()):
        raise ValueError("nonempty evaluation namespace has no identity")


def server_argv(args, checkpoint: Path, config_file: Path, port: int) -> list[str]:
    return [
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


def simulator_argv(
    args, dataset_dir: Path, task_out: Path, port: int, run_digest: str, runtime_digest: str, task_names: list[str]
) -> list[str]:
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
        "--evaluation-attempt-id",
        f"{task_out.parent.name}/{task_out.name}",
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
        "--save-generated-video",
        args.save_generated_video,
        "--runtime-probe-script",
        str(ROOT / "scripts/robocasa_vendor.py"),
        "--runtime-lock-file",
        str(args.vendor_lock),
        "--expected-runtime-digest",
        runtime_digest,
        "--runtime-tasks",
        ",".join(task_names),
    ]
    if args.asset_manifest is not None:
        command += ["--runtime-asset-manifest", str(args.asset_manifest)]
    if not args.save_rollout_mp4:
        command.append("--no-save-rollout-mp4")
    if not args.save_init_png:
        command.append("--no-save-init-png")
    return command


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="psm-robocasa-eval-cache-") as cache:
        return prepare(Path(cache))


def prepare(cache: Path) -> int:
    args = resolve(root=ROOT)
    discovered = discover_task_datasets(args.dataset_root.resolve(), None)
    mapping = dict(discovered)
    if args.list_tasks:
        print(json.dumps({"tasks": sorted(mapping)}, ensure_ascii=False, indent=2))
        return 0
    if args.tasks == "all":
        tasks = discover_task_datasets(args.dataset_root.resolve(), args.expected_tasks)
    else:
        missing = sorted(set(args.tasks) - mapping.keys())
        if missing:
            raise ValueError(f"unknown underlying RoboCasa tasks: {missing}")
        tasks = [(name, mapping[name]) for name in sorted(args.tasks)]
    checkpoint = args.checkpoint_path.resolve()
    if not (checkpoint / "model").is_dir():
        raise ValueError(f"checkpoint DCP model/ missing: {checkpoint}")
    config_file = (
        args.config_file.resolve()
        if args.config_file is not None
        else (checkpoint.parent.parent / "config.yaml").resolve()
    )
    if not config_file.is_file():
        raise ValueError(f"config file missing: {config_file}")
    gpus = args.gpus.split(",")
    output_root = args.output_dir.absolute()
    simulation_env = launch_environment(cache)
    bundle = build_verified_evaluation_identity(
        sim_python=args.sim_python,
        lock_path=args.vendor_lock,
        asset_manifest=args.asset_manifest,
        simulation_env=simulation_env,
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
            "manual_schema": "psm_wma_robocasa_eval_v1",
            "gpu_ids": gpus,
            "slots_per_gpu": 1,
            "base_port": args.base_port,
            "server_python": str(args.server_python),
            "save_rollout_mp4": args.save_rollout_mp4,
            "save_generated_video": args.save_generated_video,
            "save_init_png": args.save_init_png,
            "save_action_jsonl": True,
            "save_prediction_jsonl": True,
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
    manifest = bundle["manifest"]
    check_destination(output_root, manifest, resume=args.resume)
    if args.dry_run:
        preview = {
            "mode": "CPU_READ_ONLY_PREVIEW",
            "resolved_config": args.resolved_config,
            "output_dir": str(output_root),
            "manifest": manifest,
            "gpu_slots": [{"gpu": gpu, "slot": 0, "port": args.base_port + i} for i, gpu in enumerate(gpus)],
            "commands": [
                {
                    "gpu": gpu,
                    "slot": 0,
                    "env": {
                        "CUDA_VISIBLE_DEVICES": gpu,
                        "PYTHONPATH": simulation_env["PYTHONPATH"],
                        "MUJOCO_GL": simulation_env["MUJOCO_GL"],
                    },
                    "server": server_argv(args, checkpoint, config_file, args.base_port + index),
                    "tasks": [
                        {
                            "task": name,
                            "simulator": simulator_argv(
                                args,
                                directory,
                                output_root / name / "attempt_<next>",
                                args.base_port + index,
                                manifest["digest"],
                                manifest["identity"]["evaluation_runtime"]["digest"],
                                [n for n, _ in tasks],
                            ),
                        }
                        for name, directory in tasks
                    ],
                }
                for index, gpu in enumerate(gpus)
            ],
        }
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return 0
    require_free_ports([args.base_port + index for index in range(len(gpus))])
    run_digest = claim_evaluation_run(output_root, manifest, resume=args.resume)
    # A persistent lock file is harmless evidence; flock releases even on process death.
    fd = os.open(output_root / ".run.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "a") as lease:
        if not stat.S_ISREG(os.fstat(lease.fileno()).st_mode):
            raise ValueError("evaluation lease must be a regular file")
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("another process owns this evaluation namespace") from error
        return execute(args, checkpoint, config_file, tasks, gpus, output_root, simulation_env, bundle, run_digest)


def execute(args, checkpoint, config_file, tasks, gpus, output_root, simulation_env, bundle, run_digest) -> int:
    manifest = bundle["manifest"]
    runtime_digest = manifest["identity"]["evaluation_runtime"]["digest"]
    # Every invocation keeps its own raw probe and resolved parameters; previous attempts survive.
    invocations = output_root / "_invocations"
    invocations.mkdir(exist_ok=True)
    invocation = invocations / f"{time.time_ns()}_{os.getpid()}"
    invocation.mkdir()
    prior_summary = output_root / "screening_summary.json"
    if prior_summary.is_file():
        (invocation / "previous_screening_summary.json").write_bytes(prior_summary.read_bytes())
    atomic_write_json(invocation / "runtime_probe.json", bundle["runtime_probe_evidence"])
    atomic_write_json(invocation / "resolved-config.json", args.resolved_config)
    validation = dict(
        digest=run_digest,
        runtime_digest=runtime_digest,
        expected_trials=args.num_test_episodes,
        video_mode=args.save_generated_video,
        rollout_enabled=args.save_rollout_mp4,
        init_png_enabled=args.save_init_png,
        sim_python=args.sim_python,
    )
    summary_path = output_root / "screening_summary.json"
    work: queue.Queue[tuple[str, Path]] = queue.Queue()
    results: dict[str, dict[str, Any]] = {}
    result_lock = threading.Lock()

    for task, dataset_dir in tasks:
        task_out = output_root / task
        completed = find_completed_attempt(task_out, **validation) if args.resume else None
        if completed is not None:
            results[task] = task_result(
                dataset_dir, completed, -1, "resume", 0.0, run_digest=run_digest, expected_trials=args.num_test_episodes
            )
        else:
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
                "expected_tasks": len(tasks),
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
            for kind in ("rollout_mp4s", "generated_mp4s"):
                payload[kind] = sorted(path for row in ordered.values() for path in row.get(kind, []))
            payload["evaluation_run_digest"] = run_digest
            payload["invocation_dir"] = str(invocation)
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
        server_env = simulation_env.copy()
        server_env["CUDA_VISIBLE_DEVICES"] = gpu
        server_command = server_argv(args, checkpoint, config_file, port)
        # Open the worker log before claiming a task, so even initialization
        # errors are preserved by the outer worker boundary.
        with server_log_path.open("ab", buffering=0) as server_log:
            while not stop.is_set():
                try:
                    task, dataset_dir = work.get_nowait()
                except queue.Empty:
                    break
                task_root = output_root / task
                task_out = task_root
                started = time.monotonic()
                task_deadline = started + args.task_wall_timeout_s
                server_owned = sim_owned = None
                row, error, returncode = None, None, -1
                cleanup = {}
                stage = "server_start"
                try:
                    task_out = start_attempt(task_root, digest=run_digest, resume=args.resume)
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
                    command = simulator_argv(
                        args, dataset_dir, task_out, port, run_digest, runtime_digest, [name for name, _ in tasks]
                    )
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
                            attempt_id=f"{task_out.parent.name}/{task_out.name}",
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
                    if task_out != task_root:
                        try:
                            # Publish all process evidence before committing COMPLETE.
                            atomic_write_json(task_out / "process_cleanup.json", cleanup)
                            if error:
                                fail_attempt(task_out, error)
                            else:
                                stage = "evidence_validation"
                                finish_attempt(task_out, deadline=task_deadline, stop=stop, **validation)
                        except BaseException as exc:  # noqa: BLE001
                            error = error or f"evidence validation: {type(exc).__name__}: {exc}"
                            fail_attempt(task_out, error)
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
                            **task_video_files(task_out),
                            "rollouts": [],
                        }
                    row.update(
                        error=error,
                        returncode=returncode,
                        cleanup=cleanup,
                        elapsed_s=round(time.monotonic() - started, 3),
                    )
                    # Cleanup failure is an independent error, never replacement of
                    # the primary failure. Evidence survives even after cancellation.
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
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as error:
        # Failed interpreter/import probes retain their real diagnostic output.
        print(f"preflight failed: {error}", file=sys.stderr)
        for stream in (error.stdout, error.stderr):
            if stream:
                print(stream, file=sys.stderr)
        raise SystemExit(1) from error
