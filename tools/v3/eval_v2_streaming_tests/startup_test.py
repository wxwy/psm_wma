"""Actual OS ownership/READY/SimSlot/HTTP/native/Store with slow startup doubles."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from cosmos_framework.evaluation.robocasa_v2.store import records
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)  # noqa: F401
from robocasa_eval_v2.runtime import Runtime
from robocasa_eval_v2_processes import process_identity
from tools.v3.eval_v2_batch_tests import runtime_test as old
from tools.v3.eval_v2_streaming_tests.capacity_test import streaming_config


def cpu_run(tmp_path, monkeypatch, *, mode="off", fail=False):
    original_execution = old.execution

    def resolved(cfg):
        cfg.update(
            streaming_config(
                gpu_ids=[0],
                sims_per_gpu=2 if fail else 4,
                max_infer_batch_size=1 if fail else 2,
            ),
            render_backend="osmesa",
            render_gpu_ids=[],
        )
        return original_execution(cfg)

    class OwnedRuntime(Runtime):
        def __init__(self, *args, **kwargs):
            kwargs["resource_probe"] = lambda *a, **k: {
                "rss_bytes": 0,
                "owned_gpu_bytes": {0: 0},
            }
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(old, "execution", resolved)
    monkeypatch.setattr(old, "FIXTURE", Path(__file__).with_name("os_fixture.py"))
    monkeypatch.setattr(old, "Runtime", OwnedRuntime)
    return old.cpu_run(
        tmp_path,
        monkeypatch,
        g=1,
        n=1 if fail else 2,
        episodes=2 if fail else 4,
        fail_server=fail,
        local_memory_mode=mode,
    )


@pytest.mark.parametrize("mode", ["off", "required"])
def test_real_os_parallel_ready_make_env_exactly_one_server_and_cleanup(
    tmp_path, monkeypatch, mode
):
    value, cfg, runtime, report, error = cpu_run(tmp_path, monkeypatch, mode=mode)
    if error:
        pytest.fail(
            repr(error)
            + "\n"
            + "\n".join(
                p.read_text()[-10000:] for p in (value.root / "logs").glob("*.log")
            )
        )
    assert report["valid"] == 8 and report["results_qualified"]
    processes = records(value.root / "_internal/processes")
    assert sum(p["kind"] == "server" for p in processes) == 1
    assert sum(p["kind"].startswith("simulator_slot:") for p in processes) == 4
    assert len(runtime.actors) == len(runtime.slot_ids) == 4
    for stage in ("READY", "make_env"):
        stamps = [
            json.loads(p.read_bytes())
            for p in (value.root / "_internal/cpu_streaming_startup" / stage).iterdir()
        ]
        assert len(stamps) == 4
        assert max(s["start"] for s in stamps) < min(s["end"] for s in stamps)
    for process in processes:
        assert (
            value.root / "_internal/process_closed" / f"{process['id']}.json"
        ).is_file()
        assert process_identity(process["identity"]["pid"]) is None
    assert runtime._active_jobs == 0 and runtime._closing
    with pytest.raises(RuntimeError, match="cancelled before process"):
        runtime._spawn([sys.executable, "-c", "raise SystemExit(99)"], kind="late")


def test_streaming_server_exit_23_two_inflight_and_unrelated_process_survives(
    tmp_path, monkeypatch
):
    outsider = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(180)"])
    try:
        value, cfg, runtime, report, error = cpu_run(tmp_path, monkeypatch, fail=True)
        assert error is not None and report["valid"] == 0
        assert outsider.poll() is None
        faults = [
            json.loads(line.removeprefix("CPU_SERVER_FAULT "))
            for p in (value.root / "logs").glob("*_server.log")
            for line in p.read_text().splitlines()
            if line.startswith("CPU_SERVER_FAULT ")
        ]
        assert len(faults) == 1 and len(faults[0]["tickets"]) == 2
        assert next(iter(runtime.servers.values()))[0].proc.returncode == 23
        processes = records(value.root / "_internal/processes")
        for process in processes:
            assert process_identity(process["identity"]["pid"]) is None
            assert (
                value.root / "_internal/process_closed" / f"{process['id']}.json"
            ).exists()
        errors = value.errors("CloseFridge")
        assert len({e["attempt"]["episode"] for e in errors if e["attempt"]}) == 2
    finally:
        outsider.terminate()
        outsider.wait(5)
