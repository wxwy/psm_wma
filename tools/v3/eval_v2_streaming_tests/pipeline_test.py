"""64 real SimSlot FSMs -> public Client/dispatcher -> native CPU carriers -> 900 Core.

Only process/device, physics and diffusion boundaries are doubles. No remote
assets, CUDA or real RoboCasa result is represented by this CPU evidence.
"""

import json
import threading
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest
import torch
from torch import nn
from cosmos_framework.evaluation.robocasa_v2.store import Store, records
from cosmos_framework.inference.robocasa_batch_transactions import (
    BatchedSessionTransactions,
)
from cosmos_framework.inference.robocasa_local_memory_policy import (
    RoboCasaLocalMemoryPolicyAdapter,
)
from cosmos_framework.inference.robocasa_session_transactions_test import (
    clock_kernel as clock_kernel,
)  # noqa: F401
from cosmos_framework.scripts.robocasa_transactions_b1_test import (
    DirectTransport,
    service,
)
from cosmos_framework.simulation.robocasa.eval_v2_slot import SimSlot
from robocasa_eval_v2.config import DEFAULTS
from robocasa_eval_v2.identity import ATOMIC_TASKS
from robocasa_eval_v2.runtime import Runtime
from tools.v3.eval_v2_production_tests.native_test import RAW
from tools.v3.eval_v2_production_tests.slot_test import (
    CpuActor,
    TrackedEnv,
    prepare_monkey,
    slot_config,
)
from tools.v3.eval_v2_streaming_tests.capacity_test import (
    streaming_config,
    streaming_manifest,
)


class NativeCpuActor(CpuActor):
    def __init__(self, slot, pid, barrier):
        super().__init__(slot, pid)
        self.barrier = barrier

    def request(self, op, *, deadline=None, **kwargs):
        if op == "initialize" and self.barrier is not None:
            barrier, self.barrier = self.barrier, None
            barrier.wait(
                30
            )  # Controlled first wave: prove all 64 Slot objects are live.
        if op == "execute":
            return self.slot.execute(**kwargs)
        return super().request(op, deadline=deadline, **kwargs)


class Router:
    def __init__(self, runtime):
        self.runtime = runtime

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    def request(self, method, url, **kwargs):
        obj = self.runtime.services[urlsplit(url).port]
        return DirectTransport(obj).request(method, url, **kwargs)

    def get(self, url, **kwargs):
        obj = self.runtime.services[urlsplit(url).port]
        return SimpleNamespace(
            json=lambda: {"session_transactions": obj.transactions.info()}
        )


class Pipeline(Runtime):
    def __init__(self, store, cfg, monkeypatch, inputs=None, environment=None):
        def measured(*a, **kw):
            return {"rss_bytes": 0, "owned_gpu_bytes": {6: 0, 7: 0}}

        super().__init__(
            store, cfg, inputs or {}, environment or {}, resource_probe=measured
        )
        self.services, self.load_count, self.native_calls, self.events = {}, {}, [], []
        self.monkeypatch = monkeypatch
        self.barrier = threading.Barrier(len(self.workers))
        self.slot_template = slot_config(store, "0" * 32, "http://cpu")
        if inputs is not None:
            self.slot_template["tasks"] = {
                task: dict(
                    dataset_dir=directory,
                    metadata_sha256=store.manifest["experiment"]["task_metadata"][task],
                    horizon=store.manifest["horizons"][task],
                )
                for task, directory in inputs["tasks"].items()
            }
        self.all_slots, self.session_ids = [], set()
        self.registry.close = lambda *a: None  # CPU process boundary only.
        self.registry.recover = lambda: None

    def _create_server(self, worker):
        gpu = self.worker_gpus[worker]
        key, port = f"GPU{gpu}", self.cfg["base_port"] + self.cfg["gpu_ids"].index(gpu)
        obj = service(self.monkeypatch)
        obj.model = nn.Module()
        obj.model.net = nn.Module()
        obj.local_memory_adapter = RoboCasaLocalMemoryPolicyAdapter(
            obj, mode="off", decode_image=lambda _: None, max_sessions=32
        )

        def generate(batch, **kwargs):
            n = len(batch["prompt"])
            assert "_local_memory_prefixes" not in kwargs
            assert len(batch["action"]) == len(batch["sequence_plan"]) == n
            assert all(a[0].shape == (17, 64) for a in batch["action"])
            self.native_calls.append(
                dict(gpu=gpu, size=n, prompts=list(batch["prompt"]))
            )
            action = torch.zeros(1, 17, 64)
            action[:, 1:, :15] = torch.tensor(RAW) * 2 - 1
            return {
                "action": [action.clone() for _ in range(n)],
                "vision": [torch.zeros(1, 3, 1, 8, 8) for _ in range(n)],
            }

        obj.model.generate_samples_from_batch = generate
        obj.transactions = BatchedSessionTransactions(
            obj.local_memory_adapter,
            obj._transaction_batch,
            lambda: None,
            slot_ids=tuple(
                self.slot_ids[w] for w in self.workers if self.worker_gpus[w] == gpu
            ),
            max_batch_size=self.cfg["max_infer_batch_size"],
            batch_wait_ms=self.cfg["batch_wait_ms"],
            capacity_profile="streaming32",
            owner_token="cpu-owner",
            run_lease=self.store.lease_id,
            manifest_digest=self.store.manifest["digest"],
            model_lock=obj._lock,
            timeout_s=15,
        )
        self.services[port] = obj
        self.load_count[gpu] = self.load_count.get(gpu, 0) + 1
        proc = SimpleNamespace(pid=70000 + gpu, poll=lambda: None)
        owned = SimpleNamespace(proc=proc, pgid=proc.pid)
        with self.state_lock:
            self.server_owners[key] = "cpu-owner"
            self.servers[key] = (owned, {"cpu_policy_owner": gpu}, port)
        return self.servers[key]

    def _setup_actor(self, claim):
        worker = claim["physical_worker"]
        if worker not in self.actors:
            port = self.servers[f"GPU{self.worker_gpus[worker]}"][2]
            cfg = dict(self.slot_template, physical_slot_id=self.slot_ids[worker])
            cfg["settings"] = dict(
                cfg["settings"],
                server_url=f"http://cpu:{port}",
                execution_profile="phase_b",
                max_infer_batch_size=self.cfg["max_infer_batch_size"],
                capacity_profile="streaming32",
                local_memory_mode="off",
                sampling_protocol=self.store.manifest["protocol"]["sampling"],
                predict_timeout_s=15,
            )
            slot = SimSlot(
                cfg,
                factory=lambda t, s, g: TrackedEnv(
                    t, g["seed"], self.events, success_at=1
                ),
            )
            self.all_slots.append(slot)
            with self.state_lock:
                self.actors[worker] = NativeCpuActor(
                    slot, 80000 + self.workers.index(worker), self.barrier
                )
        self.phases[worker] = "environment_initialization"
        return self._start_assignment(
            claim, self.actors[worker], {"CPU_native_owner": self.worker_gpus[worker]}
        )

    def _register_assignment(self, claim, deadline):
        result = super()._register_assignment(claim, deadline)
        with self.state_lock:
            self.session_ids.add(result["lease"]["session_id"])
        return result

    def close(self):
        super().close()
        for obj in self.services.values():
            assert obj.transactions.close(timeout_s=5)
            obj.transactions._executor.shutdown(wait=True)


@pytest.mark.parametrize("cap", [8, 16])
def test_18_real_tasks_64_sim_sessions_900_unique_core_and_resume(
    tmp_path, monkeypatch, cap
):
    prepare_monkey(monkeypatch)
    cfg = dict(
        DEFAULTS,
        **streaming_config(max_infer_batch_size=cap),
        render_backend="osmesa",
        render_gpu_ids=[],
        base_port=19600,
        episodes_per_task=50,
        local_memory_mode="off",
        save_rollout_mp4=False,
        save_generated_video="none",
    )
    value = Store(tmp_path / "run", streaming_manifest(ATOMIC_TASKS, 50, cfg))
    assert value.manifest["scope"] == "formal900"
    value.create()
    with value.locked():
        runtime = Pipeline(value, cfg, monkeypatch)
        monkeypatch.setattr("requests.Session", lambda: Router(runtime))
        report, error = runtime.run()
        if error is not None:
            raise error
        assert (
            report["valid"] == report["success"] == 900 and report["results_qualified"]
        )
        assert runtime.load_count == {6: 1, 7: 1}
        assert len(runtime.all_slots) == len(runtime.slot_ids) == 64
        assert len(set(runtime.slot_ids.values())) == 64
        assert len(runtime.session_ids) == 900
        first_sessions = {next(iter(s.used_sessions)) for s in runtime.all_slots}
        assert len(first_sessions) == 64
        assert all(s.state == "CLEAN" and s.env is None for s in runtime.all_slots)
        assert sum(c["size"] for c in runtime.native_calls) == 900
        assert all(1 <= c["size"] <= cap for c in runtime.native_calls)
        assert any(c["size"] > 1 for c in runtime.native_calls)
        entries = records(
            value.root
            / "_internal/scheduler"
            / next((value.root / "_internal/scheduler").iterdir()).name
        )
        dispatched = [x["data"] for x in entries if x["kind"] == "DISPATCH"]
        assert len({(c["task"], c["episode"]) for c in dispatched}) == 900
        assert len({c["physical_worker"] for c in dispatched[:64]}) == 64
        assert not any(x["kind"] == "ROUND_BARRIER" for x in entries)
        rows = [
            json.loads(line)
            for line in (value.root / "episodes.jsonl").read_text().splitlines()
        ]
        assert {(r["task"], r["episode"]) for r in rows} == {
            (t, ep) for t in ATOMIC_TASKS for ep in range(50)
        }
        assert len({r["sampling"]["physical_slot_id"] for r in rows}) == 64
        assert not list(value.root.glob("tasks/**/media/*.mp4"))
        original = {
            p: p.read_bytes() for p in value.root.glob("tasks/*/episodes/*/result.json")
        }
        summary = {
            "cap": cap,
            "slots": 64,
            "sessions": len(runtime.session_ids),
            "valid": report["valid"],
            "native_batches": runtime.native_calls,
            "stats": [o.transactions.info() for o in runtime.services.values()],
        }
        (tmp_path / "cpu_pipeline.json").write_text(json.dumps(summary, indent=2))
    resumed = Store(value.root, value.manifest)
    with resumed.locked():
        again = Pipeline(resumed, cfg, monkeypatch)
        report, error = again.run()
        assert (
            error is None
            and report["valid"] == 900
            and not again.all_slots
            and not again.load_count
        )
        assert all(p.read_bytes() == raw for p, raw in original.items())
