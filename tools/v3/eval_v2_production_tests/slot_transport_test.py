"""Default Root pool and real Worker socket protocol, only OS/model/physics doubles."""

import hashlib
import os
from pathlib import Path
import socket
import threading
from types import SimpleNamespace
from urllib.parse import urlparse

from cosmos_framework.evaluation.robocasa_v2.store import read, Store
from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.simulation.robocasa import eval_v2_worker
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.native_test import server
from tools.v3.eval_v2_production_tests.runtime_test import cfg
from tools.v3.eval_v2_production_tests.slot_test import (
    TrackedEnv,
    prepare_monkey,
    slot_config,
)
from tools.v3.eval_v2_production_tests.store_test import fresh


class BridgeRegistry:
    def __init__(self, events):
        self.events, self.started, self.errors, self.threads = events, [], [], []
        self.grace = 0.5

    def start(self, command, *, kind, pass_fds, **kwargs):
        path = command[command.index("--config") + 1]
        expected = command[command.index("--config-sha256") + 1]
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected
        config = read(path)
        channel = socket.socket(fileno=os.dup(pass_fds[0]))
        process = SimpleNamespace(pid=os.getpid(), returncode=None)
        process.poll = lambda: process.returncode
        owned = SimpleNamespace(proc=process, pgid=os.getpid())
        record = {"kind": kind, "cpu_process_boundary_double": True}

        def run():
            try:
                eval_v2_worker.serve(
                    channel,
                    config,
                    factory=lambda t, s, g: TrackedEnv(
                        t, g["seed"], self.events, success_at=1
                    ),
                )
                process.returncode = 0
            except BaseException as error:
                self.errors.append(error)
                process.returncode = 1

        thread = threading.Thread(target=run)
        owned.thread = thread
        self.threads.append(thread)
        self.started.append(kind)
        thread.start()
        return owned, record

    def close(self, owned, record):
        if hasattr(owned, "thread"):
            owned.thread.join(2)
            assert not owned.thread.is_alive()
        return {"cleanup": {"cpu_owned_process_double": True}}

    def recover(self):
        return []


def test_default_root_pool_and_worker_transport_reuse_only_G_actors(
    tmp_path, monkeypatch
):
    prepare_monkey(monkeypatch)
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.group_members", lambda pgid: {os.getpid(): "S"}
    )
    value = fresh(tmp_path, tasks=tuple(f"Task{i}" for i in range(7)), episodes=2)
    events = []
    with server() as (url, calls):
        with value.locked():
            template = slot_config(value, "1" * 32, url)
        m = value.manifest
        real_metadata = {t: s["metadata_sha256"] for t, s in template["tasks"].items()}
        m = build_manifest(
            tasks=m["tasks"],
            episodes=2,
            seed=m["seed"],
            horizons=m["horizons"],
            experiment=dict(m["experiment"], task_metadata=real_metadata),
        )
        value = Store(tmp_path / "bridge", m)
        value.create()
        inputs = {
            "tasks": {t: s["dataset_dir"] for t, s in template["tasks"].items()},
            "runtime": {"digest": "CPU_TEST_FACTORY"},
            "simulation_libraries": {},
        }
        config = dict(
            cfg(3),
            episode_wall_s=5,
            request_timeout_s=2,
            save_rollout_mp4=False,
            save_generated_video="none",
            encoder_grace_s=0.1,
            sim_python="CPU_PYTHON",
            vendor_lock="CPU_vendor_lock",
        )

        class Bridge(Runtime):
            def _server(self, worker):
                if worker not in self.servers:
                    proc = SimpleNamespace(pid=os.getpid(), poll=lambda: None)
                    self.servers[worker] = (
                        SimpleNamespace(proc=proc, pgid=os.getpid()),
                        {"kind": "CPU_model"},
                        urlparse(url).port,
                    )
                return self.servers[worker]

        runtime = Bridge(
            value, config, inputs, {}, resource_probe=lambda *a, **kw: None
        )
        registry = BridgeRegistry(events)
        runtime.registry = registry
        with value.locked():
            report, error = runtime.run()
        assert error is None and report["valid"] == 14 and report["results_qualified"]
        assert len(registry.started) == len(runtime.actors) == len(runtime.servers) == 3
        assert not registry.errors and all(not t.is_alive() for t in registry.threads)
        assert set(runtime.actors) == set(runtime.workers)
        assert (
            len({x["local_memory"]["session_id"] for x in calls if "local_memory" in x})
            == 14
        )
