"""Controlled READY failures/cancellation: unpublished processes still have owners."""

import sys
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_eval_v2 import runtime as module
from robocasa_eval_v2.config import DEFAULTS
from tools.v3.eval_v2_streaming_tests.capacity_test import (
    streaming_config,
    streaming_manifest,
)


class Registry:
    def __init__(self):
        self.created = []
        self.recovered = threading.Event()

    def start(self, command, **kwargs):
        process = SimpleNamespace(
            proc=SimpleNamespace(pid=71000, poll=lambda: None), pgid=71000
        )
        self.created.append(process)
        return process, {"id": uuid.uuid4().hex, "cpu_fake_process": True}

    def recover(self):
        self.recovered.set()


def fresh(tmp_path):
    cfg = dict(
        DEFAULTS,
        **streaming_config(gpu_ids=[6], sims_per_gpu=2, max_infer_batch_size=2),
        render_backend="osmesa",
        render_gpu_ids=[],
        local_memory_mode="off",
        server_python=sys.executable,
        checkpoint=str(tmp_path / "cpu_checkpoint"),
        config_file=str(tmp_path / "cpu_config"),
        prediction_steps=2,
        save_generated_video="none",
    )
    value = Store(tmp_path / "run", streaming_manifest(cfg=cfg))
    value.create()
    return value, cfg


def test_bad_ready_info_is_terminal_one_spawn_and_unpublished_server_is_measured(
    tmp_path, monkeypatch
):
    value, cfg = fresh(tmp_path)
    with value.locked():
        probes = []

        def measure(cfg, processes=(), **kwargs):
            probes.append(tuple(processes))
            return {"rss_bytes": 0, "owned_gpu_bytes": {6: 0}}

        runtime = module.Runtime(value, cfg, {}, {}, resource_probe=measure)
        runtime.registry = Registry()
        entered, release = threading.Event(), threading.Event()

        def wait_server(*args, **kwargs):
            entered.set()
            assert release.wait(4)
            return {"session_transactions": {"enabled": False}}

        monkeypatch.setattr(module, "wait_server", wait_server)
        with ThreadPoolExecutor(2) as pool:
            first = pool.submit(runtime._server, runtime.workers[0])
            assert entered.wait(3)
            second = pool.submit(runtime._server, runtime.workers[1])
            assert not runtime.servers and len(runtime._processes()) == 1
            runtime._measure()
            assert probes[-1] == tuple(runtime.registry.created)
            release.set()
            with pytest.raises(ValueError, match="Server identity"):
                first.result(4)
            with pytest.raises(RuntimeError, match="cancelled"):
                second.result(4)
        assert len(runtime.registry.created) == 1 and not runtime.servers
        assert runtime.stop.is_set() and not runtime.startup_budget.pending
        runtime.close()


def test_stop_during_ready_waits_for_startup_owner_before_final_cleanup(
    tmp_path, monkeypatch
):
    value, cfg = fresh(tmp_path)
    with value.locked():
        runtime = module.Runtime(
            value,
            cfg,
            {},
            {},
            resource_probe=lambda *a, **k: {"rss_bytes": 0, "owned_gpu_bytes": {6: 0}},
        )
        registry = runtime.registry = Registry()
        entered, release = threading.Event(), threading.Event()

        def wait_server(*args, **kwargs):
            entered.set()
            assert release.wait(4)
            return {
                "session_transactions": dict(
                    enabled=True,
                    local_memory_mode="off",
                    execution_profile="session_native_batch_v1",
                    run_lease=value.lease_id,
                    manifest_digest=value.manifest["digest"],
                    slot_ids=list(runtime.slot_ids.values()),
                    max_native_batch=2,
                    batch_wait_ms=20,
                    capacity_profile="streaming32",
                )
            }

        monkeypatch.setattr(module, "wait_server", wait_server)
        with ThreadPoolExecutor(2) as pool:
            actor = pool.submit(
                runtime._actor,
                {"physical_worker": runtime.workers[0], "task": "CloseFridge"},
            )
            assert entered.wait(3)
            closing = pool.submit(runtime.close)
            assert registry.recovered.wait(3)
            assert runtime._closing and runtime._active_jobs == 1 and not closing.done()
            release.set()
            with pytest.raises(RuntimeError, match="after cancellation"):
                actor.result(4)
            closing.result(4)
        assert (
            runtime.closed
            and runtime._active_jobs == 0
            and not runtime.servers
            and not runtime.actors
        )
        assert len(registry.created) == 1 and not runtime.startup_budget.pending
        with pytest.raises(RuntimeError, match="cancelled before process creation"):
            runtime._spawn([sys.executable], kind="late")
