"""Real Runtime, owned OS Sim/HTTP processes and native loop; CPU boundaries only."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import sys
from pathlib import Path

import pytest
from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.evaluation.robocasa_v2.scheduler import logical_plan
from cosmos_framework.evaluation.robocasa_v2.store import Store, records
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)
from robocasa_eval_v2 import runtime as module
from robocasa_eval_v2.config import execution
from robocasa_eval_v2_processes import Registry, process_identity
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.contract_test import manifest

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tools/v3/eval_v2_batch_tests/os_fixture.py"


def free_ports(count):
    for _ in range(30):
        sockets = []
        try:
            first = socket.socket()
            first.bind(("127.0.0.1", 0))
            sockets.append(first)
            port = first.getsockname()[1]
            for i in range(1, count):
                s = socket.socket()
                s.bind(("127.0.0.1", port + i))
                sockets.append(s)
            return port
        except OSError:
            pass
        finally:
            for s in sockets:
                s.close()
    raise RuntimeError("no CPU fixture loopback ports")


class CpuRegistry(Registry):
    def start(self, command, *, kind, **kwargs):
        if kind.startswith("simulator_slot:"):
            assert command[2:4] == [
                "-m",
                "cosmos_framework.simulation.robocasa.eval_v2_worker",
            ]
            command = [sys.executable, "-B", str(FIXTURE), "sim", *command[4:]]
        return super().start(command, kind=kind, **kwargs)


def cpu_run(tmp_path, monkeypatch, *, g=1, n=2, episodes=2, fail_server=False):
    tasks = ("CloseFridge", "OpenCabinet", "OpenDrawer")[:n]
    cfg = dict(
        execution_profile="phase_b",
        gpu_ids=list(range(g)),
        sims_per_gpu=2,
        max_infer_batch_size=2,
        batch_wait_ms=100,
        episodes_per_task=episodes,
        base_port=free_ports(g),
        server_start_s=90,
        episode_wall_s=180,
        request_timeout_s=30,
        terminate_grace_s=1,
        encoder_grace_s=0.3,
        prediction_steps=2,
        guidance=1.0,
        server_python=sys.executable,
        sim_python=sys.executable,
        checkpoint=str(tmp_path / "inputs/checkpoint"),
        config_file=str(tmp_path / "inputs/config.yaml"),
        vendor_lock=str(ROOT / "third_party/robosuite_patches/vendor.lock.json"),
        save_rollout_mp4=False,
        save_generated_video="none",
    )
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    Path(cfg["config_file"]).write_text("cpu_fixture_not_training_config: true\n")
    m = manifest(tasks, episodes)
    specs = {}
    digests = {}
    for task in tasks:
        d = inputs / task
        (d / "extras").mkdir(parents=True)
        p = d / "extras/dataset_meta.json"
        p.write_text(json.dumps({"env_args": {"env_name": task}}))
        specs[task] = str(d)
        digests[task] = hashlib.sha256(p.read_bytes()).hexdigest()
    experiment = {**m["experiment"], "task_metadata": digests}
    m = build_manifest(
        tasks=tasks,
        episodes=episodes,
        seed=7,
        horizons={t: 32 for t in tasks},
        experiment=experiment,
        execution=execution(cfg),
    )
    value = Store(tmp_path / "run", m)
    value.create()
    monkeypatch.setattr(module.identity, "guard", lambda *a, **k: None)
    original = module.server_argv

    def cpu_command(args, checkpoint, config_file, port):
        base = original(args, checkpoint, config_file, port)
        return [
            sys.executable,
            "-B",
            str(FIXTURE),
            "server",
            *base[3:],
            *(["--cpu-exit-on-batch2"] if fail_server else []),
        ]

    monkeypatch.setattr(module, "server_argv", cpu_command)
    env = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        CUDA_VISIBLE_DEVICES="",
        OMP_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        PYTHONPATH=os.pathsep.join(
            map(str, (ROOT, ROOT / "cosmos-framework", ROOT / "scripts"))
        ),
    )
    evidence = {
        "tasks": specs,
        "simulation_libraries": {},
        "runtime": {"digest": "CPU_TEST_FACTORY"},
        "actual_root": "a" * 40,
    }
    runtime = Runtime(value, cfg, evidence, env, resource_probe=lambda *a, **k: None)
    runtime.registry = CpuRegistry(value.root, cfg["terminate_grace_s"])
    with value.locked():
        report, error = runtime.run()
    return value, cfg, runtime, report, error


@pytest.mark.parametrize("g,n,episodes", [(1, 2, 2), (2, 3, 1), (1, 3, 1)])
def test_real_OS_multisim_native_B2_delivery_D5_task_reuse_and_resume(
    tmp_path, monkeypatch, g, n, episodes
):
    value, cfg, runtime, report, error = cpu_run(
        tmp_path, monkeypatch, g=g, n=n, episodes=episodes
    )
    if error:
        logs = {
            p.name: p.read_text()[-12000:] for p in (value.root / "logs").glob("*.log")
        }
        pytest.fail(str(error) + "\n" + json.dumps(logs, ensure_ascii=False))
    assert report["valid"] == n * episodes and report["results_qualified"]
    processes = records(value.root / "_internal/processes")
    assert sum(p["kind"] == "server" for p in processes) == min(g, n)
    assert sum(p["kind"].startswith("simulator_slot:") for p in processes) == min(
        g * 2, n
    )
    for p in processes:
        assert (value.root / "_internal/process_closed" / (p["id"] + ".json")).exists()
        assert process_identity(p["identity"]["pid"]) is None
    calls = []
    for p in (value.root / "logs").glob("*_server.log"):
        calls.extend(
            json.loads(s[len("CPU_NATIVE_BATCH ") :])
            for s in p.read_text().splitlines()
            if s.startswith("CPU_NATIVE_BATCH ")
        )
    assert calls and any(c["size"] == 2 for c in calls)
    assert len({c["pid"] for c in calls}) == min(g, n)
    assert sum(c["size"] for c in calls) == 2 * n * episodes
    assert any(any(c["prefix_present"]) for c in calls)
    predictions = []
    for p in value.root.glob("tasks/*/episodes/*/predictions.jsonl"):
        predictions.extend(json.loads(s) for s in p.read_text().splitlines())
    assert len(predictions) == 2 * n * episodes
    assert all(
        p["transaction"]["assignment"]["session_id"] == p["local_memory"]["session_id"]
        for p in predictions
    )
    first = [p for p in predictions if p["source_step"] == 0]
    assert len({p["local_memory"]["session_id"] for p in first}) == n * episodes
    assert all(p["local_memory"]["prefix_present"] is False for p in first)
    rows = records(next((value.root / "_internal/scheduler").iterdir()))
    assert [
        (x["data"]["task"], x["data"]["episode"])
        for x in rows
        if x["kind"] == "DISPATCH"
    ] == logical_plan(value.manifest)
    assert sum(x["kind"] == "ROUND_BARRIER" for x in rows) == episodes
    events = [
        json.loads(s)
        for p in (value.root / "_internal/cpu_fixture_events").glob("*.jsonl")
        for s in p.read_text().splitlines()
    ]
    intervals = {}
    overlaps = False
    for pid in {e["pid"] for e in events}:
        own = sorted((e for e in events if e["pid"] == pid), key=lambda e: e["time"])
        pairs = []
        start = None
        for e in own:
            if e["kind"] == "execute_begin":
                start = e["time"]
            elif e["kind"] == "execute_end" and start is not None:
                pairs.append((start, e["time"]))
                start = None
        intervals[pid] = pairs
    for a, ia in intervals.items():
        for b, ib in intervals.items():
            if a != b and any(
                max(x[0], y[0]) < min(x[1], y[1]) for x in ia for y in ib
            ):
                overlaps = True
    assert overlaps, intervals
    frozen = {
        str(p): p.read_bytes()
        for p in value.root.glob("tasks/*/episodes/*/result.json")
    }
    # Same frozen plan: no Server/Sim/GPU preflight for completed Resume.
    with Store(value.root, value.manifest).locked() as resumed:
        check = Runtime(
            resumed,
            cfg,
            {},
            {},
            resource_probe=lambda *a, **k: pytest.fail(
                "completed Resume touched resource probe"
            ),
        )
        done, err = check.run()
        assert err is None and done["valid"] == n * episodes
    assert frozen == {
        str(p): p.read_bytes()
        for p in value.root.glob("tasks/*/episodes/*/result.json")
    }
    print(
        "B2_CPU_OS_WITNESS "
        + json.dumps(
            {
                "G": g,
                "N": n,
                "M": 2,
                "B": 2,
                "models": min(g, n),
                "sim_processes": len(intervals),
                "physics_overlap": overlaps,
                "native_batch_histogram": {
                    str(s): sum(c["size"] == s for c in calls) for s in (1, 2)
                },
                "valid": report["valid"],
                "synthetic_only": True,
            }
        ),
        flush=True,
    )


def test_owned_Server_death_faults_all_live_Slots_and_reaps_only_owned_groups(
    tmp_path, monkeypatch
):
    import subprocess

    foreign = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True
    )
    try:
        value, cfg, runtime, report, error = cpu_run(
            tmp_path, monkeypatch, fail_server=True
        )
        assert error is not None and report["results_qualified"] is False
        assert report["valid"] < 4
        for task in value.manifest["tasks"]:
            assert any(e["resolution"] is None for e in value.errors(task))
        for p in records(value.root / "_internal/processes"):
            assert (
                value.root / "_internal/process_closed" / (p["id"] + ".json")
            ).exists()
            assert process_identity(p["identity"]["pid"]) is None
        assert foreign.poll() is None
    finally:
        foreign.terminate()
        foreign.wait(timeout=5)
