"""CPU CLI/lease/store/worker/Child Local evidence gate with fake model and Kitchen.

The queue, protected admission, persistent store, process supervisor, original
Child main/run_policy/LocalMemoryClient, evidence validators and report stay real.
Only runtime attestation, model HTTP inference, Kitchen construction and the
proprioception fixture are replaced. Tiny pickle/ZIP files are not a real DCP.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import pickle
import random
import socket
import subprocess
import sys
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CHILD = ROOT / "cosmos-framework"
sys.path.insert(0, str(ROOT / "scripts"))

from robocasa_resume_store import ResumeStoreError, RunStore  # noqa: E402


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_bytes(canonical(value) + b"\n")


def snapshot(directory):
    return {str(path.relative_to(directory)): path.read_bytes() for path in directory.rglob("*") if path.is_file()}


def event(path, **row):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(row, allow_nan=False) + "\n")


def events(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()] if Path(path).exists() else []


def git(directory, *args):
    return subprocess.check_output(
        ["git", "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-C", str(directory), *args],
        text=True,
        stderr=subprocess.STDOUT,
    ).strip()


def repository(directory):
    directory.mkdir()
    git(directory, "init", "-q")
    (directory / "fixture.txt").write_text("CPU source identity only\n")
    git(directory, "add", "fixture.txt")
    git(
        directory, "-c", "user.name=CPU Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture"
    )


def model_files(checkpoint):
    model = checkpoint / "model"
    model.mkdir(parents=True, exist_ok=True)
    (model / ".metadata").write_bytes(pickle.dumps({"cpu_fixture": True}, protocol=4))
    with zipfile.ZipFile(model / "__0_0.distcp", "w") as archive:
        archive.writestr("archive/data.pkl", b"not tensors; never model-loaded")


def free_port():
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _serve(port, info, trace, fault):
    class Handler(BaseHTTPRequestHandler):
        active = None

        def send_json(self, value, status=200):
            body = canonical(value)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            self.send_json(info)

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            if payload.get("_local_memory_command") == "reset":
                session = payload["session_id"]
                event(trace, kind="local_reset", session=session, active=Handler.active)
                if fault == "reset_failure":
                    self.send_json({"error": "injected reset failure"}, 500)
                    return
                if session != Handler.active:
                    self.send_json({"error": "foreign reset"}, 409)
                    return
                Handler.active = None
                self.send_json({"local_memory": {"status": "reset", "session_id": session}})
                return
            local = payload["local_memory"]
            session = local["session_id"]
            if Handler.active not in {None, session}:
                self.send_json({"error": "previous episode session leaked"}, 409)
                return
            Handler.active = session
            event(
                trace,
                kind="prediction",
                session=session,
                episode_id=local["episode_id"],
                consumer_step=local["consumer_step"],
                evidence_steps=[row["source_step"] for row in local["evidence"]],
                reset=local["reset"],
                state_width=len(payload["state"]),
                prompt=payload["prompt"],
            )
            # Finite, valid raw15, including identity rot6d and arm control mode.
            action = [0, 0, 0, 0, -1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0]
            self.send_json(
                {
                    "action": [action] * 16,
                    "video": [payload["image"]],
                    "local_memory": {
                        "session_id": session,
                        "episode_id": local["episode_id"],
                        "consumer_step": local["consumer_step"],
                        "prefix_present": local["consumer_step"] > 0,
                    },
                }
            )

        def log_message(self, *_):
            pass

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


def _simulate(original, runtime_path, trace, fault):
    """Exercise unchanged Child CLI, Local ledger and HTTP cleanup on a fake env."""
    sys.path.insert(0, str(CHILD))
    import numpy as np
    from cosmos_framework.simulation.robocasa import closed_loop_eval as child

    task = read(Path(original[original.index("--dataset-dir") + 1]) / "extras/dataset_meta.json")["env_args"][
        "env_name"
    ]

    class Environment:
        def __init__(self, seed):
            self.seed, self.rng, self.episode, self.steps = seed, random.Random(seed), -1, 0
            event(trace, kind="env_construct", task=task, seed=seed, pid=os.getpid())

        def obs(self):
            frame = np.zeros((256, 256, 3), dtype=np.uint8)
            return {f"{camera}_image": frame for camera in child.CAMS}

        def reset(self):
            self.episode += 1
            self.steps = 0
            event(
                trace,
                kind="env_reset",
                task=task,
                seed=self.seed,
                physical_episode=self.episode,
                scene=self.rng.getrandbits(64),
            )
            if fault == "third_episode_error" and self.episode == 2:
                raise RuntimeError("injected third Episode reset failure")
            return self.obs()

        def get_ep_meta(self):
            return {"lang": f"actual instruction {task} episode {self.episode}"}

        def step(self, action):
            assert len(action) == 12 and np.isfinite(action).all()
            self.rng.random()
            self.steps += 1
            return self.obs(), 0.0, False, {}

        def _check_success(self):
            return self.episode % 2 == 0

        def close(self):
            event(trace, kind="env_close", task=task, seed=self.seed, episodes=self.episode + 1)

    child.make_env = lambda *_args, seed=None, **_kwargs: Environment(seed)
    child.build_state_token = lambda _obs: [0.0] * 15
    child.verify_runtime = lambda _args, _task: read(runtime_path)
    sys.argv = original[1:]
    child.main()


class Harness:
    """Only external runtime/model/Kitchen boundaries are fixtures."""

    def __init__(self, tmp_path, monkeypatch):
        self.directory = tmp_path
        self.probes, self.servers, self.simulators = [], [], []
        self.fault = ""
        self.trace = tmp_path / "fake_boundary_events.jsonl"
        spec = importlib.util.spec_from_file_location(
            "episode_resume_gate_queue", ROOT / "scripts/eval_robocasa_18task_queue.py"
        )
        self.queue = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.queue)
        self.source = tmp_path / "source"
        repository(self.source)
        repository(self.source / "cosmos-framework")
        git(
            self.source,
            "update-index",
            "--add",
            "--cacheinfo",
            f"160000,{git(self.source / 'cosmos-framework', 'rev-parse', 'HEAD')},cosmos-framework",
        )
        git(
            self.source,
            "-c",
            "user.name=CPU Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "commit",
            "-qm",
            "gitlink",
        )
        monkeypatch.setattr(self.queue, "ROOT", self.source)
        monkeypatch.setattr(self.queue, "CHILD", self.source / "cosmos-framework")
        self.checkpoint = tmp_path / "job/checkpoints/iter_000004000"
        model_files(self.checkpoint)
        self.config = self.checkpoint.parent.parent / "config.yaml"
        self.config.write_text("cpu_fixture: true\n")
        self.dataset = tmp_path / "dataset"
        self.output = tmp_path / "evaluation"
        self.add_task("CloseFridge")
        self.port = free_port()
        monkeypatch.setattr(self.queue, "build_verified_evaluation_identity", self.runtime_bundle)
        real_server, real_simulator = self.queue.server_argv, self.queue.simulator_argv

        def server(args, checkpoint, config, port):
            original = real_server(args, checkpoint, config, port)
            assert original[original.index("--action-chunk-size") + 1] == "16"
            info = {
                "checkpoint": str(checkpoint / "model"),
                "config_file": str(config),
                "raw_action_dim": 15,
                "max_action_dim": 64,
                "action_chunk_size": 16,
                "requires_state": True,
                "num_steps": args.num_steps,
                "guidance": args.guidance,
                "fps": 20,
                "seed": 0,
                "local_memory": {"enabled": True, "mode": "required", "action_dim": 15},
            }
            self.servers.append(original)
            return [
                sys.executable,
                "-B",
                str(Path(__file__).resolve()),
                "--fixture-server",
                str(port),
                json.dumps(info),
                str(self.trace),
                self.fault,
            ]

        def simulator(*args, **kwargs):
            original = real_simulator(*args, **kwargs)
            self.simulators.append(original)
            return [
                sys.executable,
                "-B",
                str(Path(__file__).resolve()),
                "--fixture-sim",
                json.dumps(original),
                str(self.runtime_path),
                str(self.trace),
                self.fault,
            ]

        monkeypatch.setattr(self.queue, "server_argv", server)
        monkeypatch.setattr(self.queue, "simulator_argv", simulator)

    def add_task(self, task):
        path = self.dataset / task / "lerobot/extras/dataset_meta.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        write(path, {"env_args": {"env_name": task}})

    def runtime_bundle(self, **kwargs):
        from v3_evaluation_identity import build_evaluation_identity

        self.probes.append([name for name, _ in kwargs["tasks"]])
        for field in ("sim_python", "lock_path", "asset_manifest", "simulation_env"):
            kwargs.pop(field, None)
        base = build_evaluation_identity(**kwargs)
        runtime = {
            "schema": "psm_robocasa_runtime_v1",
            "fixture_scope": "CPU fake environment; no physics or model acceptance",
            "protocol": {"official_horizons": {name: 17 for name, _ in kwargs["tasks"]}},
        }
        runtime["digest"] = hashlib.sha256(canonical(runtime)).hexdigest()
        self.runtime_path = self.directory / f"runtime_{len(self.probes)}.json"
        write(self.runtime_path, runtime)
        base["identity"].update(schema="psm_v3_eval_identity_vendor_v1", evaluation_runtime=runtime)
        base["digest"] = hashlib.sha256(canonical(base["identity"])).hexdigest()
        return {"manifest": base, "runtime_probe_evidence": {"returncode": 0, "scope": "fake CPU runtime boundary"}}

    def invoke(self, monkeypatch, *, tasks="CloseFridge", episodes=5, seed=0, resume=False, media="none", extra=()):
        command = [
            "eval_robocasa_18task_queue.py",
            "--checkpoint",
            str(self.checkpoint),
            "--config-file",
            str(self.config),
            "--dataset-root",
            str(self.dataset),
            "--output-dir",
            str(self.output),
            "--tasks",
            tasks,
            "--episodes",
            str(episodes),
            "--seed",
            str(seed),
            "--gpus",
            "0",
            "--base-port",
            str(self.port),
            "--server-python",
            sys.executable,
            "--sim-python",
            sys.executable,
            "--save-generated-video",
            media,
            "--no-save-rollout-mp4",
            "--no-save-init-png",
            "--no-progress",
            "--server-start-timeout-s",
            "15",
            "--predict-request-timeout-s",
            "5",
            "--episode-wall-timeout-s",
            "30",
            "--task-wall-timeout-s",
            "180",
            "--terminate-grace-s",
            "0.2",
        ]
        if resume:
            command.append("--resume")
        monkeypatch.setattr(sys, "argv", command + list(extra))
        return self.queue.main()

    def report(self):
        pointer = read(self.output / "latest_invocation.json")
        path = Path(pointer["report_path"])
        assert path.is_relative_to(self.output), "current report escaped the evaluation namespace"
        assert path.is_file(), "protected CLI did not produce an invocation report"
        return read(path)


@pytest.fixture
def harness(tmp_path, monkeypatch):
    return Harness(tmp_path, monkeypatch)


def legacy(harness, *, completed=2, trials=5, status="FAILED"):
    """Construct immutable old-schema evidence before invoking the real admission."""
    from tools.v3.episode_resume_prototype.episode_evidence_test import build_legacy_run

    directory = harness.directory / "old_fixture"
    directory.mkdir()
    run = build_legacy_run(directory, completed=completed, trials=trials, status=status)
    manifest = read(run / "evaluation_manifest.json")
    checkpoint = Path(manifest["identity"]["checkpoint"])
    model_files(checkpoint)
    shard = checkpoint / "model/__0_0.distcp"
    info = shard.stat()
    manifest["identity"].update(
        model_metadata_sha256=hashlib.sha256((checkpoint / "model/.metadata").read_bytes()).hexdigest(),
        model_shard_stat_witnesses=[[shard.name, info.st_size, info.st_mtime_ns, info.st_ctime_ns]],
    )
    old_digest = manifest["digest"]
    manifest["digest"] = hashlib.sha256(canonical(manifest["identity"])).hexdigest()
    for path in run.rglob("*"):
        if path.is_file() and path.name != "evaluation_manifest.json" and path.suffix in {".json", ".jsonl"}:
            path.write_text(path.read_text().replace(old_digest, manifest["digest"]))
    write(run / "evaluation_manifest.json", manifest)
    # The real legacy launcher reserves this lease before Worker execution.
    (run / ".run.lock").touch()
    harness.output = run
    harness.checkpoint = checkpoint
    harness.config = checkpoint.parent.parent / "config.yaml"
    harness.dataset = directory / "dataset"
    return snapshot(run)


def test_actual_fresh_cli_preserves_literal_seed_and_uses_real_child_local_cleanup(harness, monkeypatch):
    assert harness.invoke(monkeypatch, episodes=5, seed=9) == 0
    report = harness.report()
    assert report["status"] == "COMPLETE" and report["completed"] == 5
    assert report["sr"] == 3 / 5
    trace = events(harness.trace)
    assert len([row for row in trace if row["kind"] == "env_construct"]) == 1
    resets = [row for row in trace if row["kind"] == "env_reset"]
    assert [row["seed"] for row in resets] == [9] * 5
    assert [row["physical_episode"] for row in resets] == list(range(5))
    cleanup = [row for row in trace if row["kind"] == "local_reset"]
    assert len(cleanup) == 5 and len({row["session"] for row in cleanup}) == 5
    assert all(row["active"] == row["session"] for row in cleanup)
    predictions = [row for row in trace if row["kind"] == "prediction"]
    assert all(row["state_width"] == 15 for row in predictions)
    assert any(row["consumer_step"] == 16 and row["evidence_steps"] == list(range(16)) for row in predictions)


def test_legacy_two_completed_plus_three_new_runs_complete_protected_pipeline(harness, monkeypatch):
    original = legacy(harness)
    assert harness.invoke(monkeypatch, episodes=5, seed=1, resume=True) == 0
    report = harness.report()
    assert (report["status"], report["reused"], report["executed"], report["completed"]) == ("COMPLETE", 2, 3, 5)
    assert "MIXED_SEED" in report["actual_conditions"]["flags"]
    assert "MIXED_SAMPLING_PROTOCOL" in report["actual_conditions"]["flags"]
    assert len(harness.simulators) == 3
    assert all(command[command.index("--num-test-episodes") + 1] == "1" for command in harness.simulators)
    assert len({command[command.index("--seed") + 1] for command in harness.simulators}) == 3
    current = snapshot(harness.output)
    assert all(current[path] == content for path, content in original.items())
    assert len([row for row in events(harness.trace) if row["kind"] == "local_reset"]) == 3


def test_added_task_keeps_fresh_batch_while_legacy_task_only_runs_gap(harness, monkeypatch):
    legacy(harness)
    harness.add_task("NavigateKitchen")
    assert harness.invoke(monkeypatch, tasks="NavigateKitchen,CloseFridge", episodes=5, resume=True) == 0
    report = harness.report()
    assert report["completed"] == 10 and report["reused"] == 2 and report["executed"] == 8
    grouped = {name: [] for name in ("CloseFridge", "NavigateKitchen")}
    for command in harness.simulators:
        name = read(Path(command[command.index("--dataset-dir") + 1]) / "extras/dataset_meta.json")["env_args"][
            "env_name"
        ]
        grouped[name].append(command)
    assert len(grouped["CloseFridge"]) == 3 and len(grouped["NavigateKitchen"]) == 1
    fresh = grouped["NavigateKitchen"][0]
    assert fresh[fresh.index("--num-test-episodes") + 1] == "5"
    assert fresh[fresh.index("--seed") + 1] == "0"


@pytest.mark.parametrize("changed", ["checkpoint", "num_steps", "action_horizon", "guidance"])
def test_four_model_mismatches_stop_before_probe_lease_writes_or_worker(harness, monkeypatch, changed):
    original = legacy(harness, completed=5, status="COMPLETE")
    if changed == "checkpoint":
        alternate = harness.directory / "another/checkpoints/iter_000004000"
        model_files(alternate)
        harness.checkpoint = alternate
        extra = ()
    else:
        extra = {
            "num_steps": ("--prediction-steps", "20"),
            "action_horizon": ("--action-horizon", "8"),
            "guidance": ("--guidance", "2"),
        }[changed]
    with pytest.raises(
        (ValueError, RuntimeError), match="(?i)checkpoint|num_steps|action_horizon|guidance|model.*mismatch"
    ):
        harness.invoke(monkeypatch, resume=True, extra=extra)
    assert snapshot(harness.output) == original
    assert not harness.probes and not harness.servers and not harness.simulators


@pytest.mark.parametrize("location", ["checkpoint_model", "dataset"])
def test_output_inside_read_only_input_is_rejected_before_any_write_or_launch(harness, monkeypatch, location):
    harness.output = (
        harness.checkpoint / "model/eval_results"
        if location == "checkpoint_model"
        else harness.dataset / "eval_results"
    )
    checkpoint_before, dataset_before = snapshot(harness.checkpoint), snapshot(harness.dataset)
    config_before = harness.config.read_bytes()
    with pytest.raises(ValueError, match="overlaps a read-only input"):
        harness.invoke(monkeypatch)
    assert snapshot(harness.checkpoint) == checkpoint_before
    assert snapshot(harness.dataset) == dataset_before
    assert harness.config.read_bytes() == config_before
    assert not harness.output.exists()
    assert not harness.probes and not harness.servers and not harness.simulators


def test_complete_reuse_skips_runtime_ports_models_and_new_requested_seed(harness, monkeypatch):
    original = legacy(harness, completed=5, status="COMPLETE")
    with socket.socket() as occupied:
        occupied.bind(("127.0.0.1", harness.port))
        occupied.listen()
        assert harness.invoke(monkeypatch, episodes=3, seed=7, resume=True, media="all") == 0
    report = harness.report()
    assert report["completed"] == report["reused"] == 3 and report["executed"] == 0
    assert report["excluded"] == 2 and report["missing_requested_media"] > 0
    assert any(row.get("code") == "NO_NEW_EPISODES_AT_REQUESTED_SEED" for row in report["warnings"])
    assert not harness.probes and not harness.servers and not harness.simulators
    current = snapshot(harness.output)
    assert all(current[path] == content for path, content in original.items())


def test_existing_namespace_requires_explicit_resume_without_any_writes(harness, monkeypatch):
    original = legacy(harness)
    with pytest.raises((ValueError, FileExistsError), match="(?i)resume|exists"):
        harness.invoke(monkeypatch)
    assert snapshot(harness.output) == original
    assert not harness.probes and not harness.servers


def test_busy_real_namespace_lease_prevents_migration_probe_and_worker(harness, monkeypatch):
    legacy(harness)
    (harness.output / ".run.lock").touch()
    original = snapshot(harness.output)
    with (harness.output / ".run.lock").open("a") as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        with pytest.raises(ResumeStoreError, match="RUN_LOCKED"):
            harness.invoke(monkeypatch, resume=True)
    assert snapshot(harness.output) == original
    assert not harness.probes and not harness.servers


def test_runtime_error_episode_is_not_counted_and_new_invocation_can_finish_prefix(harness, monkeypatch):
    harness.fault = "third_episode_error"
    assert harness.invoke(monkeypatch, episodes=5) != 0
    partial = harness.report()
    assert partial["status"] == "PARTIAL" and partial["sr"] is None
    assert partial["completed"] == 2 and partial["remaining"] == 3
    assert partial["executed"] == 3 and partial["failed"] == 1
    first_invocations = sorted(path for path in harness.output.glob("_invocations/*") if path.is_dir())
    first_evidence = snapshot(first_invocations[0])
    harness.fault = ""
    assert harness.invoke(monkeypatch, episodes=5, seed=1, resume=True) == 0
    complete = harness.report()
    assert complete["status"] == "COMPLETE" and complete["reused"] == 2 and complete["executed"] == 3
    assert snapshot(first_invocations[0]) == first_evidence


def test_media_upgrade_only_records_new_episode_and_keeps_legacy_evidence(harness, monkeypatch):
    original = legacy(harness)
    assert (
        harness.invoke(
            monkeypatch, episodes=3, resume=True, media="all", extra=("--save-rollout-mp4", "--save-init-png")
        )
        == 0
    )
    report = harness.report()
    assert report["status"] == "COMPLETE" and report["reused"] == 2 and report["executed"] == 1
    assert report["missing_requested_media"] > 0
    assert len(harness.simulators) == 1
    sources = report["tasks"]["CloseFridge"]["episode_sources"]
    assert sources[-1]["media_coverage"]["available_generated"] >= 1
    assert sources[-1]["media_coverage"]["available_rollout"] is True
    assert sources[-1]["media_coverage"]["available_init_png"] is True
    assert all(isinstance(path, str) for path in report["rollout_mp4s"])
    current = snapshot(harness.output)
    assert all(current[path] == content for path, content in original.items())


def test_real_child_local_reset_failure_cannot_complete_and_next_run_uses_new_server(harness, monkeypatch):
    harness.fault = "reset_failure"
    assert harness.invoke(monkeypatch, episodes=2) != 0
    broken = harness.report()
    assert broken["status"] == "PARTIAL" and broken["sr"] is None
    assert (broken["completed"], broken["executed"], broken["failed"]) == (0, 1, 1)
    assert len(harness.servers) == 1
    harness.fault = ""
    assert harness.invoke(monkeypatch, episodes=2, seed=1, resume=True) == 0
    recovered = harness.report()
    assert recovered["status"] == "COMPLETE" and recovered["reused"] == 0 and recovered["executed"] == 2
    assert len(harness.servers) == 2
    assert recovered["actual_conditions"]["effective_seeds"] == [1]


def test_final_source_rescan_failure_publishes_partial_and_preserves_executor_errors(harness, monkeypatch):
    original_discover = RunStore.discover_history
    calls = []

    def fail_final_scan(store, *args, **kwargs):
        calls.append(store.root)
        if len(calls) == 2:
            raise ValueError("SOURCE_EVIDENCE_CHANGED: injected final rescan fault")
        return original_discover(store, *args, **kwargs)

    monkeypatch.setattr(RunStore, "discover_history", fail_final_scan)
    harness.fault = "third_episode_error"
    assert harness.invoke(monkeypatch, episodes=5) != 0
    assert len(calls) == 2
    report = harness.report()
    summary = read(read(harness.output / "latest_invocation.json")["summary_path"])
    assert report["status"] == summary["status"] == "PARTIAL"
    assert report["exit_code"] == 1 and report["sr"] is None and report["partial_sr"] is None
    assert report["completed"] == 0 and report["remaining"] == 5
    assert all(not row["episode_sources"] for row in report["tasks"].values())
    errors = report["invocation_errors"]
    assert any(
        row.get("stage") == "final_source_revalidation" and "SOURCE_EVIDENCE_CHANGED" in row.get("error", "")
        for row in errors
    )
    assert any("closed_loop_eval exited with code" in row.get("error", "") for row in errors)
    job = report["job_results"][0]
    assert job["error"] and job["returncode"] != 0
    assert set(job["cleanup"]) == {"server", "simulator"}
    assert all(witness["live_group"] is False for witness in job["cleanup"].values())
    # Evidence remains available for investigation even though final verification
    # failed and no Episode can safely contribute to this invocation's SR.
    assert list(harness.output.glob("_invocations/*/sources/**/rollout00_episode.json"))


@pytest.mark.parametrize(
    "fault",
    ["utf8", "truncated", "file_limit", "line_limit", "duplicate", "identity", "order", "nonfinite", "valid_start"],
)
def test_final_progress_fault_is_durable_partial_without_invented_starts(harness, monkeypatch, fault):
    original_discover = RunStore.discover_history
    calls, injected = [], []

    def inject_final_progress(store, *args, **kwargs):
        calls.append(store.root)
        if len(calls) == 2:
            path = next(store.root.glob("_invocations/*/sources/**/episode_progress.jsonl"))
            first = path.read_bytes().splitlines(keepends=True)[0]
            row = json.loads(first)
            payload = first
            if fault == "utf8":
                payload = b"\xff\n"
            elif fault == "truncated":
                payload = first.rstrip(b"\n")
            elif fault == "line_limit":
                payload = b" " * 4096 + b"\n"
            elif fault == "duplicate":
                payload = first.rstrip()[:-1] + b',"episode":0}\n'
            elif fault == "identity":
                row["evaluation_attempt_id"] = "wrong/attempt_0001"
                payload = canonical(row) + b"\n"
            elif fault == "order":
                payload = first + first
            elif fault == "nonfinite":
                payload = first.rstrip()[:-1] + b',"extra":NaN}\n'
            path.write_bytes(payload)
            if fault == "file_limit":
                with path.open("r+b") as stream:
                    stream.truncate(64 * 1024 * 1024 + 1)
            injected.append((path, path.stat().st_size, hashlib.sha256(path.read_bytes()).hexdigest()))
        return original_discover(store, *args, **kwargs)

    monkeypatch.setattr(RunStore, "discover_history", inject_final_progress)
    harness.fault = "third_episode_error"
    assert harness.invoke(monkeypatch, episodes=5) != 0
    report = harness.report()
    summary = read(read(harness.output / "latest_invocation.json")["summary_path"])
    assert report["status"] == summary["status"] == "PARTIAL"
    assert report["exit_code"] == 1 and report["sr"] is None
    assert report["completed"] == 0 and report["remaining"] == 5
    progress_errors = [row for row in report["invocation_errors"] if row.get("stage") == "final_progress_read"]
    if fault == "valid_start":
        assert not progress_errors
        assert (report["executed"], report["failed"]) == (1, 1)
    else:
        assert len(progress_errors) == 1
        assert progress_errors[0]["task"] == "CloseFridge"
        assert progress_errors[0]["path"] == str(injected[0][0])
        assert progress_errors[0]["error"]
        assert (report["executed"], report["failed"]) == (0, 0)
    assert any("closed_loop_eval exited" in row.get("error", "") for row in report["invocation_errors"])
    job = report["job_results"][0]
    assert job["error"] and all(not witness["live_group"] for witness in job["cleanup"].values())
    path, size, digest = injected[0]
    assert path.stat().st_size == size and hashlib.sha256(path.read_bytes()).hexdigest() == digest


def test_terminal_progress_file_limit_rejects_before_open(tmp_path, monkeypatch):
    from robocasa_resume_cli import _progress_starts

    path = tmp_path / "episode_progress.jsonl"
    with path.open("wb") as stream:
        stream.truncate(64 * 1024 * 1024 + 1)

    def forbidden_open(*args, **kwargs):
        pytest.fail("oversized progress must be rejected by stat before any read")

    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError, match="oversized file"):
        _progress_starts({"attempt_dir": tmp_path})


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--fixture-server":
        _serve(int(sys.argv[2]), json.loads(sys.argv[3]), sys.argv[4], sys.argv[5])
    elif len(sys.argv) > 1 and sys.argv[1] == "--fixture-sim":
        _simulate(json.loads(sys.argv[2]), sys.argv[3], sys.argv[4], sys.argv[5])
