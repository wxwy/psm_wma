"""CPU-only queue integration: real local HTTP/PIDs/Git, synthetic simulator/results.

No Torch/CUDA/model/simulator imports. Child process fixtures are stdlib-only.
Run directly with Python, or pytest --noconftest and an external empty config.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import importlib.util
import json
import os
import re
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import uuid
from contextlib import ExitStack
from enum import Enum
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
spec = importlib.util.spec_from_file_location("screening_queue", ROOT / "scripts/eval_robocasa_18task_queue.py")
queue_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_module)
TASKS = {"CloseFridge", "TurnOnSinkFaucet", "PickPlaceSinkToCounter", "NavigateKitchen"}
COMPLETION_WAIT_S = 120.0
LATE_SCENARIO_WATCHDOG_S = COMPLETION_WAIT_S + 60.0
SCENARIO_CLEANUP_RESERVE_S = 30.0
SLOW_HEALTHY_DELAY_S = 13.0
LATE_COMPLETION_CASES = {
    "mkdir_failure",
    "log_open_failure",
    "late_launch_failure",
    "slow_mkdir_failure",
}


class FixtureCompletionTimeout(AssertionError):
    """The prerequisite did not complete; the intended fault was NOT injected."""


def _scenario_watchdog(case):
    if case == "completion_never_finished":
        return 30.0
    return LATE_SCENARIO_WATCHDOG_S if case in LATE_COMPLETION_CASES else 90.0


def _raise_after_completed(
    summary_path,
    trials,
    message,
    *,
    waits,
    injected,
    init_faults,
    operation=None,
    timeout_s=COMPLETION_WAIT_S,
    deadline=None,
    started_event=None,
):
    """Wait for real healthy task results; record a caught OSError only AFTER completion."""
    started = time.monotonic()
    until = min(started + timeout_s, deadline) if deadline is not None else started + timeout_s
    witness = {
        "target_trials": trials,
        "started_at": started,
        "deadline": until,
        "status": "WAITING",
    }
    waits.append(witness)
    if started_event is not None:
        started_event.set()
    while time.monotonic() < until:
        try:
            summary = json.loads(summary_path.read_text())
            tasks = summary.get("tasks", {})
            healthy = (
                summary.get("total_trials") == trials
                and len(tasks) == trials // 5
                and all(row.get("trials") == 5 and row.get("error") is None for row in tasks.values())
                and not summary.get("worker_errors")
                and summary.get("status") == ("COMPLETE" if trials == 20 else "INCOMPLETE")
            )
        except (OSError, ValueError):
            healthy = False
        observed_at = time.monotonic()
        if healthy and observed_at < until:
            witness.update(
                status="COMPLETED",
                completed_at=observed_at,
                observed_trials=summary["total_trials"],
                observed_tasks=sorted(tasks),
                observed_status=summary["status"],
            )
            try:
                raise OSError(message)
            except OSError as error:
                injected.append(
                    {
                        "wait_index": len(waits) - 1,
                        "type": type(error).__name__,
                        "message": str(error),
                        "injected_at": time.monotonic(),
                    }
                )
                if operation is not None:
                    init_faults.append(operation)
                raise
        time.sleep(min(0.01, max(0, until - time.monotonic())))
    witness.update(status="TIMED_OUT", finished_at=time.monotonic())
    raise FixtureCompletionTimeout(f"fixture prerequisite timed out before {trials} healthy trials; fault not injected")


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def _episode_fixture(directory, *, episode, digest, video, generated_mode="none", rollout=True):
    """Write real audit schemas/media; only model and simulator are synthetic."""
    stem = f"rollout{episode:02d}"
    attempt_id = f"{directory.parent.name}/{directory.name}"
    action = {
        "episode": episode,
        "evaluation_run_digest": digest,
        "evaluation_attempt_id": attempt_id,
        "source_step": 0,
        "evidence_completed": True,
        "predicted_raw15": [0.0] * 15,
        "canonical_executed_raw15": [0.0] * 15,
        "submitted_env12": [0.0] * 12,
    }
    prediction = {
        "episode": episode,
        "evaluation_run_digest": digest,
        "evaluation_attempt_id": attempt_id,
        "latency_ms": 1.0,
        "step_before_query": 0,
        "action_chunk": [[0.0] * 15] * 16,
        "local_memory": {"prefix_present": True},
    }
    generated_videos = (
        []
        if generated_mode == "none"
        else [f"{stem}_generated.mp4"]
        if generated_mode == "first"
        else [f"{stem}_generated_replan0000.mp4"]
    )
    row = {
        "ep": episode,
        "policy": episode % 2 == 0,
        "outcome": "success" if episode % 2 == 0 else "behavioral_failure",
        "error": None,
        "steps": 1,
        "replans": 1,
        "completed_action_records": 1,
        "actions_file": f"{stem}_actions.jsonl",
        "predictions_file": f"{stem}_predictions.jsonl",
        "evaluation_run_digest": digest,
        "evaluation_attempt_id": attempt_id,
        "generated_videos": generated_videos,
    }
    for suffix, record in (("actions", action), ("predictions", prediction)):
        (directory / f"{stem}_{suffix}.jsonl").write_text(json.dumps(record) + "\n")
    (directory / f"{stem}_episode.json").write_text(json.dumps(row))
    if rollout:
        (directory / f"{stem}.mp4").write_bytes(video)
    (directory / f"{stem}_cleanup.json").write_text(
        json.dumps(
            {
                "session_id": f"{uuid.uuid4().hex}:0:{uuid.uuid4().hex}",
                "reset_ok": True,
                "cleanup_error": None,
                "rollout_error": None,
                "media_error": None,
            }
        )
    )
    if generated_videos:
        for name in generated_videos:
            (directory / name).write_bytes(video)
        (directory / f"{stem}_generated_manifest.json").write_text(
            json.dumps(
                {
                    "schema": "psm_generated_video_v1",
                    "status": "COMPLETE",
                    "mode": generated_mode,
                    "evaluation_run_digest": digest,
                    "evaluation_attempt_id": attempt_id,
                    "videos": [{"replan": 0, "source_step": 0, "file": generated_videos[0], "frames": 2}],
                }
            )
        )
    from PIL import Image

    Image.new("RGB", (16, 16), (15, 30, 45)).save(directory / f"{stem}_init.png")
    return row


def _child_checkpoint_builder():
    """Run pinned Child method/type-detector bodies without importing GPU/Pydantic.

    Only enum base and unused registry/config annotation dependencies are isolated;
    the local-path normalization and DCP-file detection execute unchanged source.
    """
    source = ROOT / "cosmos-framework/cosmos_framework/inference/common/args.py"
    tree = ast.parse(source.read_text())
    classes = {node.name: node for node in tree.body if isinstance(node, ast.ClassDef)}
    method = next(
        node
        for node in classes["CheckpointOverrides"].body
        if isinstance(node, ast.FunctionDef) and node.name == "_build_checkpoint"
    )

    class StringEnum(str, Enum):
        pass

    namespace = {"Path": Path, "StrEnum": StringEnum, "Self": object, "CheckpointConfig": object, "re": re}
    namespace["DEFAULT_CONFIG_FILE"] = "unused_registry_default.py"
    module = ast.Module(body=[classes["ConfigFileType"], classes["CheckpointType"], method], type_ignores=[])
    exec(compile(module, str(source), "exec"), namespace)
    return namespace["_build_checkpoint"]


CHILD_CHECKPOINT_BUILDER = _child_checkpoint_builder()


def _child_chunk_resolver():
    """Execute the unchanged Child parser and CLI/config/fallback branch only."""
    source = ROOT / "cosmos-framework/cosmos_framework/scripts/action_policy_server_robocasa.py"
    tree = ast.parse(source.read_text())
    parser = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_extract_chunk_length_from_config"
    )
    default = next(
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "_DEFAULT_ACTION_CHUNK_SIZE" for target in node.targets)
    )
    service = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "ActionModelService")
    init = next(node for node in service.body if isinstance(node, ast.FunctionDef) and node.name == "__init__")
    resolution = next(
        node
        for node in init.body
        if isinstance(node, ast.If) and ast.unparse(node.test) == "args.action_chunk_size is not None"
    )
    namespace = {"Any": object, "DictConfig": dict}
    exec(compile(ast.Module(body=[default, parser], type_ignores=[]), str(source), "exec"), namespace)
    branch = compile(ast.Module(body=[resolution], type_ignores=[]), str(source), "exec")

    def resolve(cli_value, config):
        local = {
            "args": SimpleNamespace(action_chunk_size=cli_value),
            "self": SimpleNamespace(experiment_config=config),
            "log": SimpleNamespace(info=lambda message: None),
        }
        exec(branch, namespace, local)
        return local["resolved_chunk_size"]

    return resolve


CHILD_CHUNK_RESOLVER = _child_chunk_resolver()


def _child_model_path(checkpoint: Path, config: Path) -> str:
    setup = SimpleNamespace(checkpoint_path=str(checkpoint), config_file=str(config), experiment_overrides=[])
    CHILD_CHECKPOINT_BUILDER(setup, checkpoints={})
    return setup.checkpoint_path


def _info(checkpoint: Path, config: Path) -> dict:
    # Effective fields exposed by the unchanged Child get_info()/Local adapter.
    return {
        "checkpoint": str(checkpoint / "model"),
        "config_file": str(config),
        "raw_action_dim": 15,
        "max_action_dim": 64,
        "action_chunk_size": 16,
        "requires_state": True,
        "num_steps": 30,
        "guidance": 1.0,
        "fps": 20,
        "seed": 0,
        "local_memory": {"enabled": True, "mode": "required", "action_dim": 15},
    }


def _serve(port: int, info: dict) -> None:
    class Handler(BaseHTTPRequestHandler):
        occupied = False

        def do_GET(self):
            if self.path == "/error":
                self.send_error(400, "injected HTTP failure")
                return
            if self.path == "/stall":
                time.sleep(5)
            if self.path == "/claim":
                if Handler.occupied:
                    self.send_error(400, "session limit reached")
                    return
                Handler.occupied = True
            body = json.dumps(info).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def _start_http(port: int, info: dict, **kwargs):
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--serve", str(port), json.dumps(info)], **kwargs
    )


def _ready(proc, port):
    until = time.monotonic() + 5
    while time.monotonic() < until:
        if proc.poll() is not None:
            raise RuntimeError("fixture HTTP server exited")
        try:
            return queue_module._read_json(f"http://127.0.0.1:{port}/info", timeout=0.2)
        except OSError:
            time.sleep(0.01)
    raise RuntimeError("fixture HTTP startup timeout")


def _stop(proc):
    if proc.poll() is None:
        proc.terminate()
    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=3)


def _free_base(count):
    for _ in range(100):
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]
        try:
            queue_module.require_free_ports(list(range(port, port + count)))
            return port
        except (OSError, RuntimeError, ValueError):
            continue
    raise RuntimeError("no fixture port range")


def _git(root, *args):
    return subprocess.check_output(
        ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-C", str(root), *args],
        stderr=subprocess.STDOUT,
        text=True,
    ).strip()


def _repo(root):
    root.mkdir()
    _git(root, "init", "-q")
    (root / "fixture.txt").write_text("synthetic source\n")
    _git(root, "add", "fixture.txt")
    _git(root, "-c", "user.name=CPU Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")


def _scenario(case, parent, count):
    """Invoke the actual queue main/identity with only server/simulator boundaries replaced."""
    scenario_started = time.monotonic()
    completion_deadline = scenario_started + _scenario_watchdog(case) - SCENARIO_CLEANUP_RESERVE_S
    if case == "completion_never_finished":
        waits, injected, init_faults = [], [], []
        try:
            _raise_after_completed(
                parent / "never_created_summary.json",
                20,
                "must never inject this OSError",
                waits=waits,
                injected=injected,
                init_faults=init_faults,
                operation="mkdir",
                timeout_s=0.15,
            )
        except FixtureCompletionTimeout as error:
            report = {
                "case": case,
                "error": f"{type(error).__name__}: {error}",
                "completion_waits": waits,
                "injected_exceptions": injected,
                "init_faults": init_faults,
                "thread_names": [
                    thread.name for thread in threading.enumerate() if thread.name.startswith("robocasa-gpu-")
                ],
                "server_exits": [],
                "summary_exists": (parent / "never_created_summary.json").exists(),
            }
            (parent / "report.json").write_text(json.dumps(report))
            return
        raise AssertionError("never-completed fixture unexpectedly injected a fault or returned")
    root = parent / "source"
    _repo(root)
    child = root / "cosmos-framework"
    _repo(child)
    _git(
        root,
        "update-index",
        "--add",
        "--cacheinfo",
        f"160000,{_git(child, 'rev-parse', 'HEAD')},cosmos-framework",
    )
    _git(
        root,
        "-c",
        "user.name=CPU Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "gitlink",
    )
    queue_module.ROOT, queue_module.CHILD = root, child
    checkpoint = parent / "job/checkpoints/iter_000004000"
    (checkpoint / "model").mkdir(parents=True)
    (checkpoint / "model/.metadata").write_bytes(b"tiny synthetic metadata, not a real DCP")
    (checkpoint / "model/__0_0.distcp").write_bytes(b"synthetic")
    config = checkpoint.parent.parent / "config.yaml"
    config.write_text(
        json.dumps({"dataloader_train": {"dataloader": {"datasets": {"robocasa": {"dataset": {"chunk_length": 32}}}}}})
    )
    original_config_bytes = config.read_bytes()
    dataset = parent / "datasets"
    for task in TASKS:
        meta = dataset / task / "lerobot/extras/dataset_meta.json"
        meta.parent.mkdir(parents=True)
        meta.write_text(json.dumps({"env_args": {"env_name": task}}))
    observed_tasks = queue_module.discover_task_datasets(dataset, 4)
    assert {name for name, _ in observed_tasks} == TASKS
    output = parent / "evaluation"
    base = _free_base(count)
    calls, servers, foreign = [], [], []
    sim_calls = []
    runtime_calls = []
    runtime_witness = {}
    from v3_evaluation_identity import build_evaluation_identity

    def verified_identity(*, sim_python, lock_path, asset_manifest=None, simulation_env=None, **kwargs):
        runtime_calls.append(
            {
                "python": str(sim_python),
                "tasks": [name for name, _ in kwargs["tasks"]],
                "pythonpath": (simulation_env or {}).get("PYTHONPATH"),
            }
        )
        if case == "runtime_failure":
            raise ValueError("injected dirty vendor runtime rejection")
        manifest = build_evaluation_identity(**kwargs)
        runtime = {"schema": "cpu_fixture_runtime_v1", "tasks": sorted(name for name, _ in kwargs["tasks"])}
        runtime["digest"] = hashlib.sha256(_canonical(runtime)).hexdigest()
        runtime_witness.clear()
        runtime_witness.update(runtime)
        manifest["identity"]["evaluation_runtime"] = runtime
        manifest["digest"] = hashlib.sha256(_canonical(manifest["identity"])).hexdigest()
        return {
            "manifest": manifest,
            "runtime_probe_evidence": {"argv": [str(sim_python), "CPU_FIXTURE_PROBE"], "returncode": 0},
        }

    import imageio.v2 as imageio
    import numpy as np

    tiny_video = parent / "fixture.mp4"
    imageio.mimwrite(tiny_video, [np.zeros((16, 16, 3), dtype=np.uint8)] * 2, fps=20, macro_block_size=None)
    video_bytes = tiny_video.read_bytes()
    completion_wait_started = threading.Event()
    completion_waits, injected_exceptions = [], []
    healthy_delay = {}
    init_faults, unhandled_thread_errors = [], []
    original_mkdir, original_open = Path.mkdir, Path.open

    def fail_initialization(operation):
        _raise_after_completed(
            output / "screening_summary.json",
            20,
            f"injected worker1 {operation} failure after all tasks",
            waits=completion_waits,
            injected=injected_exceptions,
            init_faults=init_faults,
            operation=operation,
            deadline=completion_deadline,
            started_event=completion_wait_started,
        )

    def mkdir(path, *args, **kwargs):
        if case in ("mkdir_failure", "slow_mkdir_failure") and path.name == "_worker01_gpu1":
            fail_initialization("mkdir")
        return original_mkdir(path, *args, **kwargs)

    def open_file(path, *args, **kwargs):
        if case == "log_open_failure" and path.name == "action_server.log" and path.parent.name == "_worker01_gpu1":
            fail_initialization("log_open")
        return original_open(path, *args, **kwargs)

    def popen(command, **kwargs):
        if command[1:3] == ["-B", "-c"]:
            # The real CPU media verifier owns its decoder/FFmpeg process group.
            # Keep that boundary real, rather than misclassifying it as a model server.
            return subprocess.Popen(command, **kwargs)
        if len(command) > 1 and str(command[1]).endswith("closed_loop_eval.py"):
            return sim_popen(command, **kwargs)
        calls.append(command)
        gpu = kwargs["env"]["CUDA_VISIBLE_DEVICES"]
        assert command[1:3] == [
            "-m",
            "cosmos_framework.scripts.action_policy_server_robocasa",
        ]
        assert command[command.index("--local-memory-max-sessions") + 1] == "1"
        if case == "late_launch_failure" and gpu == "1":
            _raise_after_completed(
                output / "screening_summary.json",
                15,
                "injected second worker launch failure after all tasks",
                waits=completion_waits,
                injected=injected_exceptions,
                init_faults=init_faults,
                deadline=completion_deadline,
            )
        port = int(command[command.index("--port") + 1])
        info = _info(checkpoint, config)
        info["checkpoint"] = _child_model_path(checkpoint, config)
        cli_chunk = int(command[command.index("--action-chunk-size") + 1]) if "--action-chunk-size" in command else None
        info["action_chunk_size"] = CHILD_CHUNK_RESOLVER(cli_chunk, json.loads(config.read_text()))
        if case == "wrong_chunk":
            info["action_chunk_size"] = 32
        if case == "wrong_checkpoint":
            info["checkpoint"] = str(checkpoint.with_name("iter_000003900") / "model")
        if case == "wrong_job_same_iteration":
            info["checkpoint"] = str(parent / "other_job/checkpoints/iter_000004000/model")
        if case == "parent_checkpoint":
            info["checkpoint"] = str(checkpoint)
        if case == "wrong_config":
            info["config_file"] = str(parent / "another.yaml")
        if case == "wrong_mode":
            info["local_memory"]["mode"] = "off"
        if case == "changed_config":
            config.write_text("synthetic: changed after identity\n")
        if case == "foreign_race":
            old = _start_http(port, info, stdout=kwargs["stdout"], stderr=subprocess.STDOUT)
            foreign.append(old)
            _ready(old, port)
            proc = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(30)"], **kwargs)
        else:
            proc = _start_http(port, info, **kwargs)
        servers.append(proc)
        return proc

    def sim_popen(command, **kwargs):
        assert command[1].endswith("closed_loop_eval.py")
        sim_calls.append(command)
        if case == "slow_mkdir_failure" and len(sim_calls) == 1:
            assert completion_wait_started.wait(COMPLETION_WAIT_S), "fault worker never entered completion wait"
            # Deliberately slow the healthy producer, not the completion check:
            # its real Summary still controls when the OSError may be injected.
            healthy_delay["started_at"] = time.monotonic()
            time.sleep(SLOW_HEALTHY_DELAY_S)
            healthy_delay["finished_at"] = time.monotonic()
        assert kwargs["env"].get("PYTHONPATH") == runtime_calls[-1]["pythonpath"]
        directory = Path(command[command.index("--output-dir") + 1])
        digest = command[command.index("--evaluation-run-digest") + 1]
        assert command[command.index("--evaluation-attempt-id") + 1] == f"{directory.parent.name}/{directory.name}"
        (directory / "runtime_attestation.json").write_text(json.dumps(runtime_witness))
        assert command[command.index("--expected-runtime-digest") + 1]
        assert set(command[command.index("--runtime-tasks") + 1].split(",")) == (
            {"CloseFridge", "TurnOnSinkFaucet"} if case == "task_subset" else TASKS
        )
        video_mode = command[command.index("--save-generated-video") + 1]
        rollout_enabled = "--no-save-rollout-mp4" not in command
        expected_mode = (
            ("all" if case == "generated_all" else "first")
            if case.startswith(("generated_", "partial_video_"))
            else "none"
        )
        assert video_mode == expected_mode
        if case == "partial_video_first":
            _episode_fixture(
                directory,
                episode=0,
                digest=digest,
                video=video_bytes,
                generated_mode=video_mode,
                rollout=rollout_enabled,
            )
            return subprocess.Popen([sys.executable, "-c", "raise SystemExit(7)"], **kwargs)
        if case == "partial_resume" and len(sim_calls) == 1:
            row = _episode_fixture(directory, episode=0, digest=digest, video=video_bytes)
            (directory / "results.json").write_text(json.dumps([row]))
            return subprocess.Popen([sys.executable, "-c", "raise SystemExit(7)"], **kwargs)
        if case in ("sim_failure", "primary_and_cleanup") and len(sim_calls) == 1:
            return subprocess.Popen([sys.executable, "-c", "raise SystemExit(7)"], **kwargs)
        if case == "session_leak":
            queue_module._read_json(command[command.index("--server-url") + 1] + "/claim")
        fault = (
            case
            in (
                "task_timeout",
                "episode_timeout",
                "sigkill",
                "sigterm",
                "request_timeout",
                "reset_failure",
                "video_failure",
                "missing_results",
                "http400",
                "cancel",
                "cleanup_failure",
                "primary_and_cleanup",
            )
            and len(sim_calls) == 1
        )
        if fault and case != "cleanup_failure":
            if case == "cancel":
                threading.Timer(0.1, lambda: os.kill(os.getpid(), signal.SIGTERM)).start()
                return subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"], **kwargs)
            elif case in ("http400", "request_timeout"):
                url = command[command.index("--server-url") + 1] + ("/error" if case == "http400" else "/stall")
                return subprocess.Popen(
                    [sys.executable, "-c", f"import urllib.request;urllib.request.urlopen({url!r},timeout=0.05)"],
                    **kwargs,
                )
            if case == "episode_timeout":
                Path(command[command.index("--progress-file") + 1]).write_text(
                    json.dumps(
                        {
                            "schema": "psm_episode_progress_v1",
                            "event": "start",
                            "episode": 0,
                            "evaluation_run_digest": digest,
                            "evaluation_attempt_id": f"{directory.parent.name}/{directory.name}",
                        }
                    )
                    + "\n"
                )
            if case in ("task_timeout", "episode_timeout"):
                # A descendant ignores SIGTERM; both processes must be reclaimed.
                script = "import subprocess,sys,time,signal; signal.signal(signal.SIGTERM,signal.SIG_IGN); subprocess.Popen([sys.executable,'-c','import signal,time;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(60)']);time.sleep(60)"
            elif case in ("sigterm", "sigkill"):
                sig = "SIGTERM" if case == "sigterm" else "SIGKILL"
                script = f"import os,signal;os.kill(os.getpid(),signal.{sig})"
            else:
                script = f"raise RuntimeError({case!r})"
            return subprocess.Popen([sys.executable, "-c", script], **kwargs)
        rows = [
            _episode_fixture(
                directory,
                episode=index,
                digest=digest,
                video=video_bytes,
                generated_mode=video_mode,
                rollout=rollout_enabled,
            )
            for index in range(5)
        ]
        (directory / "results.json").write_text(json.dumps(rows))
        progress = Path(command[command.index("--progress-file") + 1])
        progress.write_text(
            "".join(
                json.dumps(
                    {
                        "schema": "psm_episode_progress_v1",
                        "episode": index,
                        "event": event,
                        "evaluation_run_digest": digest,
                        "evaluation_attempt_id": f"{directory.parent.name}/{directory.name}",
                    }
                )
                + "\n"
                for index in range(5)
                for event in ("start", "end")
            )
        )
        if case == "live_progress":
            live_path = Path(command[command.index("--live-progress-file") + 1])
            live_path.write_text(
                "".join(
                    json.dumps(
                        {
                            "schema": "psm_eval_live_progress_v1",
                            "evaluation_run_digest": digest,
                            "evaluation_attempt_id": f"{directory.parent.name}/{directory.name}",
                            "task": directory.parent.name,
                            "event": event,
                            "stage": "executing",
                            "episode": index,
                            "episodes": 5,
                            "steps": 1,
                            "max_steps": 900,
                            "predictions": 1,
                            "last_prediction_ms": 1.0,
                            "outcome": rows[index]["outcome"] if event == "episode_end" else None,
                            "error": None,
                            "instruction": "close the fridge",
                        }
                    )
                    + "\n"
                    for index in range(5)
                    for event in ("episode_start", "episode_end")
                )
            )
        if case == "wrong_attempt_progress":
            events = [json.loads(line) for line in progress.read_text().splitlines()]
            events[0]["evaluation_attempt_id"] = "CloseFridge/attempt_9999"
            progress.write_text("".join(json.dumps(event) + "\n" for event in events))
        if len(sim_calls) == 4 and case == "server_dies_after_tasks":
            _stop(servers[-1])
        return subprocess.Popen([sys.executable, "-c", "pass"], **kwargs)

    # Proxy only the queue module's external process boundaries. Real immutable
    # identity still invokes real Git; the rest of the host subprocess module is intact.
    queue_module.subprocess = SimpleNamespace(
        Popen=popen, STDOUT=subprocess.STDOUT, TimeoutExpired=subprocess.TimeoutExpired
    )
    queue_module.OwnedProcess.__init__.__globals__["subprocess"] = queue_module.subprocess
    argv = [
        "queue",
        "--checkpoint-path",
        str(checkpoint),
        "--config-file",
        str(config),
        "--dataset-root",
        str(dataset),
        "--output-dir",
        str(output),
        "--server-python",
        sys.executable,
        "--sim-python",
        sys.executable,
        "--gpus",
        ",".join(str(index) for index in range(count)),
        "--base-port",
        str(base),
        "--expected-tasks",
        "4",
        "--tasks",
        ",".join(sorted(TASKS)),
        "--num-test-episodes",
        "5",
        "--num-steps",
        "30",
        "--guidance",
        "1.0",
        "--timeout",
        "5",
    ]
    argv += ["--terminate-grace-s", "0.15"]
    argv += ["--save-generated-video", "none"]
    if case in ("generated_first", "generated_all", "partial_video_first"):
        argv += ["--no-save-rollout-mp4", "--save-generated-video", "all" if case == "generated_all" else "first"]
    if case == "task_subset":
        argv += ["--tasks", "CloseFridge,TurnOnSinkFaucet"]
    if case == "task_unknown":
        argv += ["--tasks", "DoesNotExist"]
    if case == "dry_run":
        argv += ["--dry-run"]
    if case == "list_tasks":
        argv += ["--list-tasks"]
    if case == "progress_disabled":
        argv += ["--no-progress"]
    if case in (
        "task_timeout",
        "episode_timeout",
        "sigkill",
        "sigterm",
        "request_timeout",
        "reset_failure",
        "video_failure",
        "missing_results",
        "http400",
        "cancel",
        "cleanup_failure",
        "primary_and_cleanup",
        "partial_resume",
    ):
        argv += ["--on-infrastructure-error", "continue_with_new_server"]
    if case == "task_timeout":
        # The task budget also includes decoding all required audit media.
        # Healthy tasks have room for this real CPU work; the injected hung
        # simulator still exceeds this bound and requires SIGKILL.
        argv += ["--task-wall-timeout-s", "5"]
    if case == "episode_timeout":
        argv += ["--episode-wall-timeout-s", "0.2"]
    real_close = queue_module.OwnedProcess.close
    injected_cleanup = []

    def close_with_fault(owned):
        witness = real_close(owned)
        if (
            case in ("cleanup_failure", "primary_and_cleanup")
            and owned.proc.pid not in {p.pid for p in servers}
            and not injected_cleanup
        ):
            injected_cleanup.append(owned.proc.pid)
            owned.cleanup["error"] = "injected cleanup error after real group reap"
            raise OSError(owned.cleanup["error"])
        return witness

    error = None
    with ExitStack() as stack:
        if case == "export_notification_failure":
            original_print = print

            def closed_notification(*args, **kwargs):
                if args and str(args[0]).startswith("video browsing"):
                    raise ValueError("closed progress terminal")
                return original_print(*args, **kwargs)

            stack.enter_context(patch("builtins.print", side_effect=closed_notification))
        if case == "observer_failure":
            for name in ("start", "update", "close"):
                stack.enter_context(patch.object(queue_module.EvaluationProgress, name, side_effect=OSError(name)))
        if case == "export_failure":
            stack.enter_context(patch.object(queue_module, "export_videos", side_effect=OSError("export unavailable")))
        if case == "occupied_port":
            occupied = stack.enter_context(socket.socket())
            occupied.bind(("0.0.0.0", base + count - 1))
            occupied.listen()
        try:
            with (
                patch.object(sys, "argv", argv),
                patch.object(Path, "mkdir", mkdir),
                patch.object(Path, "open", open_file),
                patch.object(queue_module.OwnedProcess, "close", close_with_fault),
                patch.object(queue_module, "build_verified_evaluation_identity", side_effect=verified_identity),
                patch.object(
                    threading,
                    "excepthook",
                    lambda event: unhandled_thread_errors.append(str(event.exc_value)),
                ),
            ):
                rc = queue_module.main()
                first_rc = rc
                first_summary = (
                    json.loads((output / "screening_summary.json").read_text())
                    if (output / "screening_summary.json").is_file()
                    else None
                )
                if case in (
                    "partial_resume",
                    "resume_complete",
                    "resume_wrong_video",
                    "resume_wrong_timeout",
                    "resume_missing_progress",
                    "resume_wrong_attempt",
                    "resume_failed_cleanup",
                    "progress_resume",
                ):
                    if case in ("resume_missing_progress", "resume_wrong_attempt", "resume_failed_cleanup"):
                        victim = output / "CloseFridge/attempt_0001"
                        corrupt_path = victim / (
                            "rollout00_cleanup.json" if case == "resume_failed_cleanup" else "episode_progress.jsonl"
                        )
                        if case == "resume_missing_progress":
                            corrupt_path.unlink()
                        elif case == "resume_wrong_attempt":
                            events = [json.loads(line) for line in corrupt_path.read_text().splitlines()]
                            events[0]["evaluation_attempt_id"] = "CloseFridge/attempt_9999"
                            corrupt_path.write_text("".join(json.dumps(event) + "\n" for event in events))
                        else:
                            cleanup = json.loads(corrupt_path.read_text())
                            cleanup["reset_ok"] = False
                            corrupt_path.write_text(json.dumps(cleanup))
                        corrupt_bytes = corrupt_path.read_bytes() if corrupt_path.exists() else None
                    argv += ["--resume"]
                    if case == "progress_resume":
                        argv += ["--no-progress", "--progress-interval-s", "10"]
                    if case == "resume_wrong_video":
                        argv += ["--save-generated-video", "first"]
                    if case == "resume_wrong_timeout":
                        argv += ["--task-wall-timeout-s", "10801"]
                    rc = queue_module.main()
        except (RuntimeError, ValueError, SystemExit) as exc:
            rc, error = 1, f"{type(exc).__name__}: {exc}"
        finally:
            foreign_alive = all(proc.poll() is None for proc in foreign)
            server_exits = [proc.poll() for proc in servers]
            for proc in [*servers, *foreign]:
                _stop(proc)
    report = {
        "case": case,
        "rc": rc,
        "error": error,
        "server_commands": len(calls),
        "server_command_argv": calls,
        "frozen_config_unchanged": config.read_bytes() == original_config_bytes,
        "sim_calls": len(sim_calls),
        "sim_command_argv": sim_calls,
        "runtime_calls": runtime_calls,
        "server_exits": server_exits,
        "foreign_alive_before_fixture_cleanup": foreign_alive,
        "thread_names": [thread.name for thread in threading.enumerate() if thread.name.startswith("robocasa-gpu-")],
        "output_exists": output.exists(),
        "init_faults": init_faults,
        "completion_waits": completion_waits,
        "injected_exceptions": injected_exceptions,
        "healthy_delay": healthy_delay,
        "unhandled_thread_errors": unhandled_thread_errors,
    }
    if "first_rc" in locals() and case in (
        "partial_resume",
        "resume_complete",
        "resume_wrong_video",
        "resume_wrong_timeout",
        "resume_missing_progress",
        "resume_wrong_attempt",
        "resume_failed_cleanup",
        "progress_resume",
    ):
        report.update(first_rc=first_rc, first_summary=first_summary)
    if "corrupt_path" in locals():
        report["corrupt_artifact_preserved"] = corrupt_bytes == (
            corrupt_path.read_bytes() if corrupt_path.exists() else None
        )
    report["attempts"] = {
        task: [
            {
                "path": str(path),
                "marker": json.loads((path / "attempt.json").read_text()),
                "episode_indices": [row["ep"] for row in json.loads((path / "results.json").read_text())]
                if (path / "results.json").is_file()
                else [],
            }
            for path in sorted((output / task).glob("attempt_*"))
            if (path / "attempt.json").is_file()
        ]
        for task in TASKS
    }
    if (output / "screening_summary.json").exists():
        report["summary"] = json.loads((output / "screening_summary.json").read_text())
    if (output / "evaluation_manifest.json").exists():
        report["protocol"] = json.loads((output / "evaluation_manifest.json").read_text())["identity"]["protocol"]
    (parent / "report.json").write_text(json.dumps(report))


class MediaClassificationTests(unittest.TestCase):
    def test_prediction_video_cannot_be_reported_as_environment_video(self):
        for mode in ("first", "all"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "CloseFridge/attempt_0001"
                output.mkdir(parents=True)
                row = _episode_fixture(
                    output,
                    episode=0,
                    digest="fixture",
                    video=b"classification fixture",
                    generated_mode=mode,
                    rollout=False,
                )
                (output / "results.json").write_text(json.dumps([row]))
                result = queue_module.task_result(
                    Path("/fixture"), output, 0, "0", 0, run_digest="fixture", expected_trials=1
                )
                self.assertEqual(result["rollout_mp4s"], [])
                self.assertEqual(result["generated_mp4s"], [str(output / row["generated_videos"][0])])

    def test_environment_video_and_none_mode_have_separate_lists(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "CloseFridge/attempt_0001"
            output.mkdir(parents=True)
            row = _episode_fixture(output, episode=0, digest="fixture", video=b"classification fixture")
            (output / "results.json").write_text(json.dumps([row]))
            (output / "rollout00_not_video.mp4").write_bytes(b"unrelated artifact")
            result = queue_module.task_result(
                Path("/fixture"), output, 0, "0", 0, run_digest="fixture", expected_trials=1
            )
            self.assertEqual(result["rollout_mp4s"], [str(output / "rollout00.mp4")])
            self.assertEqual(result["generated_mp4s"], [])


class ServerIdentityTests(unittest.TestCase):
    def test_real_child_explicit_chunk16_overrides_config32_and_missing_flag_fails_strict_info(self):
        checkpoint, config_path = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        config = {"dataloader_train": {"dataloader": {"datasets": {"robocasa": {"dataset": {"chunk_length": 32}}}}}}
        before = copy.deepcopy(config)
        info = _info(checkpoint, config_path)
        info["action_chunk_size"] = CHILD_CHUNK_RESOLVER(16, config)
        self.assertEqual(info["action_chunk_size"], 16)
        queue_module.validate_server_info(
            info, checkpoint=checkpoint, config_file=config_path, num_steps=30, guidance=1.0
        )
        for inherited in (config, {}):
            with self.subTest(source="config32" if inherited else "fallback"):
                info["action_chunk_size"] = CHILD_CHUNK_RESOLVER(None, inherited)
                self.assertEqual(info["action_chunk_size"], 32)
                with self.assertRaisesRegex(ValueError, "action_chunk_size mismatch"):
                    queue_module.validate_server_info(
                        info, checkpoint=checkpoint, config_file=config_path, num_steps=30, guidance=1.0
                    )
        self.assertEqual(config, before)

    def test_real_child_checkpoint_builder_model_path_passes_exact_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "iter_000004000"
            model = checkpoint / "model"
            model.mkdir(parents=True)
            (model / ".metadata").write_bytes(b"synthetic")
            (model / "__0_0.distcp").write_bytes(b"synthetic")
            config = Path(directory) / "config.yaml"
            self.assertEqual(_child_model_path(checkpoint, config), str(model))
            self.assertEqual(_child_model_path(model, config), str(model))
            info = _info(checkpoint, config)
            info["checkpoint"] = _child_model_path(checkpoint, config)
            queue_module.validate_server_info(
                info, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
            )

    def test_effective_info_exact_fields_and_malformed_values_fail_closed(self):
        checkpoint, config = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        good = _info(checkpoint, config)
        queue_module.validate_server_info(good, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0)
        changes = {
            "checkpoint": [
                None,
                "/synthetic/iter_000003900/model",
                "iter_000004000/model",
                str(checkpoint),
                "/other_job/iter_000004000/model",
                str(checkpoint / "model_other"),
                str(checkpoint / "model/another_model"),
            ],
            "config_file": [None, "/other/config.yaml"],
            "raw_action_dim": [None, 12, "15", True],
            "max_action_dim": [None, 32],
            "action_chunk_size": [None, 32, 0],
            "requires_state": [None, False, 1],
            "num_steps": [None, 29, "30"],
            "guidance": [None, 2.0, float("nan"), True],
            "fps": [None, 30],
            "seed": [None, 1],
            "local_memory": [None, {"enabled": True, "mode": "off"}, {"enabled": True, "mode": "required"}],
        }
        for field, values in changes.items():
            for value in values:
                with self.subTest(field=field, value=value):
                    bad = copy.deepcopy(good)
                    bad[field] = value
                    with self.assertRaises(ValueError):
                        queue_module.validate_server_info(
                            bad, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
                        )
        with self.assertRaises(ValueError):
            queue_module.validate_server_info([], checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0)

    def test_process_exit_during_ready_check_is_rejected(self):
        checkpoint, config = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        process = SimpleNamespace(poll=unittest.mock.Mock(side_effect=[None, 7]), returncode=7)
        with (
            patch.object(queue_module, "_read_json", return_value=_info(checkpoint, config)),
            patch.object(queue_module, "require_owned_listener"),
            self.assertRaisesRegex(RuntimeError, "exited during identity"),
        ):
            queue_module.wait_server(
                process, 1234, 1, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
            )

    def test_invalid_port_range_is_rejected(self):
        for port in (0, 65536, -1, True):
            with self.subTest(port=port), self.assertRaises(ValueError):
                queue_module.require_free_ports([port])

    def test_unverifiable_listener_ownership_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "cannot verify"):
            queue_module.require_owned_listener(SimpleNamespace(pid=999999999), 1234)

    def test_ready_connection_timeout_and_already_dead_server(self):
        checkpoint, config = Path("/synthetic/iter_000004000"), Path("/synthetic/config.yaml")
        process = SimpleNamespace(poll=lambda: None)
        with patch.object(queue_module, "_read_json", side_effect=OSError("synthetic connection refused")):
            with self.assertRaisesRegex(RuntimeError, "not ready before timeout"):
                queue_module.wait_server(
                    process, 1234, 0.01, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
                )
        process = SimpleNamespace(poll=lambda: 9, returncode=9)
        with self.assertRaisesRegex(RuntimeError, "exited early"):
            queue_module.wait_server(
                process, 1234, 1, checkpoint=checkpoint, config_file=config, num_steps=30, guidance=1.0
            )


class QueueIntegrationTests(unittest.TestCase):
    def scenario(self, case, count=2):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            with (parent / "console.log").open("w") as log:
                process = subprocess.Popen(
                    [
                        sys.executable,
                        str(Path(__file__).resolve()),
                        "--scenario",
                        case,
                        directory,
                        str(count),
                    ],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                try:
                    rc = process.wait(timeout=_scenario_watchdog(case))
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                    self.fail("CPU queue fixture hung; owned process group killed")
            self.assertEqual(rc, 0, (parent / "console.log").read_text())
            report = json.loads((parent / "report.json").read_text())
            report["console"] = (parent / "console.log").read_text()
            self.assertEqual(report["thread_names"], [], report)
            self.assertTrue(all(code is not None for code in report["server_exits"]), report)
            print("QUEUE_WITNESS " + json.dumps(report, sort_keys=True))
            return report

    def test_live_progress_reports_episode_boundaries_without_changing_results(self):
        report = self.scenario("live_progress", 2)
        self.assertEqual(report["rc"], 0)
        self.assertEqual(report["summary"]["status"], "COMPLETE")
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertEqual(report["summary"]["total_successes"], 12)
        self.assertIn("episode_end", report["console"])
        for command in report["sim_command_argv"]:
            self.assertEqual(command.count("--live-progress-file"), 1)
        self.assertNotIn("progress", report["protocol"])
        self.assertNotIn("progress_interval_s", report["protocol"])

    def test_terminal_progress_can_be_disabled_without_changing_results(self):
        report = self.scenario("progress_disabled", 1)
        self.assertEqual(report["rc"], 0)
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertNotIn("episode_end", report["console"])

    def test_progress_options_can_change_on_same_identity_task_resume(self):
        report = self.scenario("progress_resume", 1)
        self.assertEqual((report["first_rc"], report["rc"]), (0, 0))
        self.assertEqual(report["server_commands"], 4)
        self.assertEqual(report["sim_calls"], 4)
        self.assertTrue(all(len(attempts) == 1 for attempts in report["attempts"].values()))

    def test_observer_failure_cannot_change_queue_completion_or_cleanup(self):
        report = self.scenario("observer_failure", 2)
        self.assertEqual(report["rc"], 0)
        self.assertEqual(report["summary"]["status"], "COMPLETE")
        self.assertEqual(report["summary"]["worker_errors"], {})

    def test_browsing_export_failure_cannot_change_queue_completion(self):
        report = self.scenario("export_failure", 1)
        self.assertEqual(report["rc"], 0)
        self.assertEqual(report["summary"]["status"], "COMPLETE")
        self.assertIn("export unavailable", report["console"])

    def test_browsing_notification_failure_cannot_replace_completed_exit_code(self):
        report = self.scenario("export_notification_failure", 1)
        self.assertEqual(report["rc"], 0)
        self.assertEqual(report["summary"]["status"], "COMPLETE")
        self.assertIsNone(report["error"])

    def test_four_tasks_five_episodes_complete_on_one_two_or_four_workers(self):
        for count in (1, 2, 8):
            with self.subTest(workers=count):
                report = self.scenario("normal", count)
                self.assertEqual(report["rc"], 0)
                self.assertEqual(report["server_commands"], 4)
                for command in report["server_command_argv"]:
                    self.assertEqual(command.count("--no-guardrails"), 1)
                    self.assertEqual(command.count("--action-chunk-size"), 1)
                    self.assertEqual(command[command.index("--action-chunk-size") + 1], "16")
                self.assertTrue(report["frozen_config_unchanged"])
                self.assertEqual(report["protocol"]["server_action_chunk_size"], 16)
                self.assertEqual(report["protocol"]["H_pred"], 16)
                self.assertEqual(report["protocol"]["R"], 16)
                summary = report["summary"]
                self.assertEqual(set(summary["tasks"]), TASKS)
                self.assertEqual(summary["status"], "COMPLETE")
                self.assertEqual(summary["total_trials"], 20)
                self.assertEqual(summary["total_successes"], 12)
                self.assertEqual(summary["sr"], 0.6)
                self.assertEqual(summary["worker_errors"], {})
                for row in summary["tasks"].values():
                    self.assertEqual(row["trials"], 5)
                    self.assertEqual(len(row["rollout_mp4s"]), 5)

    def test_generated_video_summary_keeps_environment_videos_disabled(self):
        for case in ("generated_first", "generated_all"):
            with self.subTest(mode=case):
                report = self.scenario(case, 1)
                self.assertEqual(report["rc"], 0, report)
                summary = report["summary"]
                self.assertEqual(summary["status"], "COMPLETE")
                self.assertEqual(summary["rollout_mp4s"], [])
                self.assertEqual(len(summary["generated_mp4s"]), 20)
                for row in summary["tasks"].values():
                    self.assertEqual(row["rollout_mp4s"], [])
                    self.assertEqual(len(row["generated_mp4s"]), 5)
                    self.assertEqual(
                        sorted(row["generated_mp4s"]),
                        sorted(
                            str(Path(row["results_file"]).parent / name)
                            for episode in row["rollouts"]
                            for name in episode["generated_videos"]
                        ),
                    )

    def test_failed_partial_attempt_preserves_prediction_video_without_environment_video(self):
        report = self.scenario("partial_video_first", 1)
        self.assertEqual(report["rc"], 1)
        summary = report["summary"]
        self.assertEqual(summary["status"], "INCOMPLETE")
        self.assertEqual(summary["rollout_mp4s"], [])
        self.assertEqual(len(summary["generated_mp4s"]), 1)
        row = next(iter(summary["tasks"].values()))
        self.assertEqual(row["rollout_mp4s"], [])
        self.assertEqual(row["generated_mp4s"], summary["generated_mp4s"])
        self.assertEqual(row["rollouts"], [])
        self.assertIn("generated", row["generated_mp4s"][0])
        self.assertEqual(report["attempts"][next(iter(summary["tasks"]))][0]["marker"]["status"], "FAILED")

    def test_occupied_nonfirst_port_refuses_all_workers_before_output_claim(self):
        report = self.scenario("occupied_port")
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["server_commands"], 0)
        self.assertEqual(report["sim_calls"], 0)
        self.assertFalse(report["output_exists"])
        self.assertIn("unavailable", report["error"])

    def test_wrong_checkpoint_config_and_mode_stop_before_simulator(self):
        for case in ("wrong_checkpoint", "wrong_config", "wrong_mode", "wrong_chunk"):
            with self.subTest(case=case):
                report = self.scenario(case)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["sim_calls"], 0)
                self.assertTrue(report["summary"]["worker_errors"])
                self.assertIsNone(report["summary"]["sr"])

    def test_same_iteration_other_job_and_unnormalized_parent_are_rejected(self):
        for case in ("wrong_job_same_iteration", "parent_checkpoint"):
            with self.subTest(case=case):
                report = self.scenario(case)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["sim_calls"], 0)
                self.assertTrue(report["summary"]["worker_errors"])
                self.assertIsNone(report["summary"]["sr"])

    def test_foreign_listener_race_with_identical_info_is_not_our_process(self):
        report = self.scenario("foreign_race", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["sim_calls"], 0)
        self.assertTrue(report["foreign_alive_before_fixture_cleanup"])
        self.assertIn("does not own port", str(report["summary"]["worker_errors"]))

    def test_config_content_change_during_startup_is_rejected(self):
        report = self.scenario("changed_config", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["sim_calls"], 0)
        self.assertIn("changed since evaluation identity", str(report["summary"]["worker_errors"]))

    def test_server_launch_error_after_other_tasks_does_not_disappear(self):
        report = self.scenario("late_launch_failure")
        self.assertEqual(report["rc"], 1)
        # Per-task creation claims the failing task before Popen; only the
        # other three tasks can complete. Initialization failures below still
        # prove a late worker error cannot hide behind all twenty results.
        self.assertEqual(report["summary"]["total_trials"], 15)
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")
        self.assertIsNone(report["summary"]["sr"])
        self.assertIn("injected second worker", str(report["summary"]["worker_errors"]))
        self.check_completion_before_fault(report, 15, "injected second worker launch failure after all tasks")

    def check_completion_before_fault(self, report, trials, message):
        self.assertEqual(len(report["completion_waits"]), 1)
        self.assertEqual(len(report["injected_exceptions"]), 1)
        wait, error = report["completion_waits"][0], report["injected_exceptions"][0]
        self.assertEqual(wait["status"], "COMPLETED")
        self.assertEqual(wait["target_trials"], trials)
        self.assertEqual(wait["observed_trials"], trials)
        self.assertEqual(len(wait["observed_tasks"]), trials // 5)
        self.assertEqual(error["wait_index"], 0)
        self.assertEqual(error["type"], "OSError")
        self.assertEqual(error["message"], message)
        self.assertLessEqual(wait["started_at"], wait["completed_at"])
        self.assertLess(wait["completed_at"], wait["deadline"])
        self.assertLessEqual(wait["completed_at"], error["injected_at"])

    def check_initialization_failure(self, case, operation):
        report = self.scenario(case)
        self.assertEqual(report["init_faults"], [operation])
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertEqual(set(report["summary"]["tasks"]), TASKS)
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")
        self.assertIsNone(report["summary"]["sr"])
        self.assertIn(
            f"worker1 {operation} failure",
            report["summary"]["worker_errors"]["_worker_1"]["error"],
        )
        self.assertEqual(report["server_commands"], 4)
        self.assertEqual(report["sim_calls"], 4)
        self.assertEqual(report["unhandled_thread_errors"], [])
        self.check_completion_before_fault(report, 20, f"injected worker1 {operation} failure after all tasks")
        self.assertTrue(
            report["summary"]["worker_errors"]["_worker_1"]["error"].startswith("OSError: injected worker1")
        )
        return report

    def test_worker_mkdir_failure_after_healthy_worker_completes_all_tasks_is_preserved(
        self,
    ):
        self.check_initialization_failure("mkdir_failure", "mkdir")

    def test_worker_log_open_failure_after_healthy_worker_completes_all_tasks_is_preserved(
        self,
    ):
        self.check_initialization_failure("log_open_failure", "log_open")

    def test_slow_healthy_worker_exceeds_old_wait_before_real_initialization_fault(
        self,
    ):
        report = self.check_initialization_failure("slow_mkdir_failure", "mkdir")
        wait = report["completion_waits"][0]
        delay = report["healthy_delay"]
        self.assertGreaterEqual(delay["finished_at"] - delay["started_at"], SLOW_HEALTHY_DELAY_S)
        self.assertGreater(wait["completed_at"] - wait["started_at"], 12)
        self.assertLessEqual(delay["finished_at"], wait["completed_at"])

    def test_completion_wait_timeout_cannot_inject_or_fake_completion(self):
        report = self.scenario("completion_never_finished")
        self.assertIn("FixtureCompletionTimeout:", report["error"])
        self.assertIn("fault not injected", report["error"])
        self.assertEqual(report["init_faults"], [])
        self.assertEqual(report["injected_exceptions"], [])
        self.assertFalse(report["summary_exists"])
        self.assertEqual(len(report["completion_waits"]), 1)
        wait = report["completion_waits"][0]
        self.assertEqual(wait["status"], "TIMED_OUT")
        self.assertGreaterEqual(wait["finished_at"], wait["deadline"])
        self.assertNotIn("completed_at", wait)
        self.assertLess(COMPLETION_WAIT_S + SCENARIO_CLEANUP_RESERVE_S, LATE_SCENARIO_WATCHDOG_S)

    def test_server_exit_after_completed_tasks_is_not_screening_success(self):
        report = self.scenario("server_dies_after_tasks", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertIn("exited during screening", str(report["summary"]["worker_errors"]))
        self.assertIsNone(report["summary"]["sr"])

    def test_persistent_abandoned_session_cannot_contaminate_next_task(self):
        report = self.scenario("session_leak", 1)
        self.assertEqual(report["rc"], 0)
        self.assertEqual(report["server_commands"], 4)
        self.assertEqual(report["summary"]["status"], "COMPLETE")

    def test_kill_timeout_reset_media_and_missing_results_use_fresh_server(self):
        for case in (
            "task_timeout",
            "episode_timeout",
            "sigkill",
            "sigterm",
            "request_timeout",
            "reset_failure",
            "video_failure",
            "missing_results",
            "http400",
        ):
            with self.subTest(fault=case):
                report = self.scenario(case, 1)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["server_commands"], 4)
                self.assertEqual(report["sim_calls"], 4)
                self.assertEqual(report["summary"]["status"], "INCOMPLETE")
                self.assertIsNone(report["summary"]["sr"])
                self.assertEqual(report["summary"]["task_failures"], 1)
                self.assertEqual(report["summary"]["total_trials"], 15)
                cleanup = next(row["cleanup"] for row in report["summary"]["tasks"].values() if row["error"])
                self.assertFalse(cleanup["server"]["live_group"])
                self.assertFalse(cleanup["simulator"]["live_group"])
                if "timeout" in case and case != "request_timeout":
                    self.assertIn("SIGKILL", cleanup["simulator"]["signals"])

    def test_owner_cancel_stops_queue_and_reaps_both_groups(self):
        report = self.scenario("cancel", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["server_commands"], 1)
        self.assertIn("Owner signal", str(report["summary"]["worker_errors"]))
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")

    def test_cleanup_error_always_stops_and_retains_primary_error(self):
        for case in ("cleanup_failure", "primary_and_cleanup"):
            with self.subTest(fault=case):
                report = self.scenario(case, 1)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["server_commands"], 1)
                row = next(iter(report["summary"]["tasks"].values()))
                self.assertIn("injected cleanup", row["cleanup"]["simulator"]["error"])
                self.assertIsNone(report["summary"]["sr"])
                if case == "primary_and_cleanup":
                    self.assertIn("exited with code 7", row["error"])
                    self.assertNotIn("injected cleanup", row["error"])

    def test_simulator_failure_keeps_error_and_nonzero_exit(self):
        report = self.scenario("sim_failure", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["summary"]["task_failures"], 1)
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")
        self.assertIsNone(report["summary"]["sr"])

    def test_selected_tasks_share_exact_runtime_identity_and_only_run_requested_subset(self):
        report = self.scenario("task_subset", 2)
        self.assertEqual(report["rc"], 0, report)
        self.assertEqual(report["server_commands"], 2)
        self.assertEqual(report["sim_calls"], 2)
        self.assertEqual(set(report["summary"]["tasks"]), {"CloseFridge", "TurnOnSinkFaucet"})
        self.assertEqual(report["summary"]["planned_trials"], 10)
        self.assertEqual(report["summary"]["total_trials"], 10)
        self.assertEqual(len(report["runtime_calls"]), 1)
        self.assertEqual(set(report["runtime_calls"][0]["tasks"]), {"CloseFridge", "TurnOnSinkFaucet"})
        for command in report["sim_command_argv"]:
            self.assertEqual(command[command.index("--save-generated-video") + 1], "none")
            self.assertIn("--runtime-probe-script", command)
            self.assertIn("--runtime-lock-file", command)
            self.assertIn("--expected-runtime-digest", command)

    def test_unknown_task_rejected_before_runtime_probe_or_namespace_claim(self):
        report = self.scenario("task_unknown", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["runtime_calls"], [])
        self.assertEqual(report["server_commands"], 0)
        self.assertFalse(report["output_exists"])

    def test_dirty_vendor_rejected_before_server_or_namespace_claim(self):
        report = self.scenario("runtime_failure", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(len(report["runtime_calls"]), 1)
        self.assertEqual(report["server_commands"], 0)
        self.assertEqual(report["sim_calls"], 0)
        self.assertFalse(report["output_exists"])
        self.assertIn("dirty vendor runtime", report["error"])

    def test_list_tasks_and_dry_run_are_read_only_and_never_launch_workers(self):
        for case in ("list_tasks", "dry_run"):
            with self.subTest(mode=case):
                report = self.scenario(case, 2)
                self.assertEqual(report["rc"], 0, report)
                self.assertEqual(report["server_commands"], 0)
                self.assertEqual(report["sim_calls"], 0)
                self.assertFalse(report["output_exists"])
                self.assertEqual(len(report["runtime_calls"]), int(case == "dry_run"))

    def test_same_identity_resume_skips_only_whole_valid_tasks(self):
        report = self.scenario("resume_complete", 1)
        self.assertEqual(report["first_rc"], 0)
        self.assertEqual(report["rc"], 0, report)
        self.assertEqual(report["server_commands"], 4)
        self.assertEqual(report["sim_calls"], 4)
        self.assertEqual(report["summary"]["total_trials"], 20)
        self.assertTrue(all(len(attempts) == 1 for attempts in report["attempts"].values()))
        self.assertTrue(all(attempts[0]["marker"]["status"] == "COMPLETE" for attempts in report["attempts"].values()))

    def test_queue_online_progress_rejects_foreign_attempt_before_completion(self):
        report = self.scenario("wrong_attempt_progress", 1)
        self.assertEqual(report["rc"], 1)
        self.assertEqual(report["server_commands"], 1)
        self.assertEqual(report["sim_calls"], 1)
        self.assertEqual(report["summary"]["status"], "INCOMPLETE")
        self.assertIn("progress identity/order mismatch", str(report["summary"]["worker_errors"]))
        self.assertTrue(
            all(
                attempt["marker"]["status"] == "FAILED"
                for attempts in report["attempts"].values()
                for attempt in attempts
            )
        )

    def test_resume_cannot_skip_complete_marker_with_missing_or_foreign_episode_evidence(self):
        for case in ("resume_missing_progress", "resume_wrong_attempt", "resume_failed_cleanup"):
            with self.subTest(corruption=case):
                report = self.scenario(case, 1)
                self.assertEqual(report["first_rc"], 0)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["server_commands"], 4)
                self.assertEqual(report["sim_calls"], 4)
                self.assertIn("ValueError:", report["error"])
                self.assertTrue(report["corrupt_artifact_preserved"])
                self.assertTrue(all(len(attempts) == 1 for attempts in report["attempts"].values()))
                self.assertTrue(
                    all(attempts[0]["marker"]["status"] == "COMPLETE" for attempts in report["attempts"].values())
                )

    def test_partial_task_resume_keeps_old_evidence_and_restarts_entire_task_from_zero(self):
        report = self.scenario("partial_resume", 1)
        self.assertEqual(report["first_rc"], 1)
        self.assertEqual(report["first_summary"]["total_trials"], 15)
        self.assertEqual(report["rc"], 0, report)
        self.assertEqual(report["server_commands"], 5)
        self.assertEqual(report["sim_calls"], 5)
        self.assertEqual(report["summary"]["total_trials"], 20)
        restarted = [attempts for attempts in report["attempts"].values() if len(attempts) == 2]
        self.assertEqual(len(restarted), 1)
        self.assertEqual(restarted[0][0]["marker"]["status"], "FAILED")
        self.assertEqual(restarted[0][1]["marker"]["status"], "COMPLETE")
        self.assertTrue(restarted[0][0]["path"].endswith("attempt_0001"))
        self.assertTrue(restarted[0][1]["path"].endswith("attempt_0002"))
        self.assertEqual(restarted[0][0]["episode_indices"], [0])
        self.assertEqual(restarted[0][1]["episode_indices"], [0, 1, 2, 3, 4])

    def test_resume_refuses_video_or_timeout_protocol_change_without_launching_more_servers(self):
        for case in ("resume_wrong_video", "resume_wrong_timeout"):
            with self.subTest(change=case):
                report = self.scenario(case, 1)
                self.assertEqual(report["first_rc"], 0)
                self.assertEqual(report["rc"], 1)
                self.assertEqual(report["server_commands"], 4)
                self.assertEqual(report["sim_calls"], 4)
                self.assertIn("identity changed", report["error"])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        _serve(int(sys.argv[2]), json.loads(sys.argv[3]))
    elif len(sys.argv) > 1 and sys.argv[1] == "--scenario":
        _scenario(sys.argv[2], Path(sys.argv[3]), int(sys.argv[4]))
    else:
        unittest.main()
