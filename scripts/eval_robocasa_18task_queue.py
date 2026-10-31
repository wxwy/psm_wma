#!/usr/bin/env python3
"""Run RoboCasa with one isolated Server/Simulator pair per task and GPU worker."""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from robocasa_eval_config import resolve
from robocasa_eval_progress import EvaluationProgress as EvaluationProgress
from robocasa_eval_video_view import export_videos as export_videos
from robocasa_processes import (
    EvaluationInterrupted,
)
from robocasa_processes import OwnedProcess as OwnedProcess
from robocasa_vendor import build_verified_evaluation_identity as build_verified_evaluation_identity
from v3_evaluation_identity import (
    sha256_file as sha256_file,
)
from v3_evaluation_identity import (
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


def validate_server_info(
    info: Any,
    *,
    checkpoint: Path,
    config_file: Path,
    num_steps: int,
    guidance: float,
    local_memory_mode="required",
) -> None:
    """Validate the effective server configuration, not just HTTP readiness."""
    if not isinstance(info, dict):
        raise ValueError("action server /info must be an object")
    # CLI/manifest retain the requested root; the Child reports its selected model DCP.
    for name, expected in (
        ("checkpoint", (checkpoint / "model").resolve()),
        ("config_file", config_file),
    ):
        value = info.get(name)
        if (
            not isinstance(value, str)
            or not Path(value).is_absolute()
            or Path(value).resolve() != expected
        ):
            raise ValueError(
                f"action server {name} mismatch: expected {expected}, got {value!r}"
            )
    for name, expected in (
        ("raw_action_dim", 15),
        ("action_chunk_size", 16),
        ("max_action_dim", 64),
        ("num_steps", num_steps),
        ("fps", 20),
        (
            "seed",
            0,
        ),  # Policy sampler default; --seed on this queue is the environment seed.
    ):
        if type(info.get(name)) is not int or info[name] != expected:
            raise ValueError(
                f"action server {name} mismatch: expected {expected}, got {info.get(name)!r}"
            )
    if type(info.get("guidance")) not in (int, float) or info["guidance"] != guidance:
        raise ValueError("action server guidance mismatch")
    local = info.get("local_memory")
    if (
        info.get("requires_state") is not True
        or not isinstance(local, dict)
        or local_memory_mode not in ("off", "required")
        or local.get("enabled") is not (local_memory_mode == "required")
        or local.get("mode") != local_memory_mode
        or (
            local_memory_mode == "required"
            and (type(local.get("action_dim")) is not int or local["action_dim"] != 15)
        )
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
    local_memory_mode="required",
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
            local_memory_mode=local_memory_mode,
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
        "--live-progress-file",
        str(task_out / "live_progress.jsonl"),
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
    # A single production admission path; no fallback to strict whole-Task Resume.
    from robocasa_resume_cli import prepare_resume

    return prepare_resume(resolve(root=ROOT), cache, queue_api=SimpleNamespace(**globals()))


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
