"""Real Root supervisor/FD daemon/Unix IPC/Owner HTTP; synthetic CPU encoders.

No real Sim, GPU, checkpoint or throughput claim. Native leases and Feature Owner
state are real; only model generation and environment processes are boundaries.
"""

import copy
import json
import os
import subprocess
import sys
import threading
import time
import traceback
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.evaluation.robocasa_v2.store import Store
from cosmos_framework.inference import robocasa_session_transactions_test as s
from cosmos_framework.inference.robocasa_batch_transactions import (
    BatchedSessionTransactions,
    BatchOutput,
)
from cosmos_framework.inference.robocasa_feature_evidence import FeatureEvidenceOwner
from cosmos_framework.inference.robocasa_shared_policy_batch_test import FeatureAdapter
from cosmos_framework.scripts.robocasa_feature_http_test import server as wire
from robocasa_eval_v2 import shared_vae as module
from robocasa_eval_v2.config import execution
from robocasa_eval_v2.resources import owned_group_pids
from robocasa_eval_v2.runtime import Runtime
from tools.v3.eval_v2_batch_tests.shared_vae_test import IDENTITY
from tools.v3.eval_v2_batch_tests.shared_vae_topology_test import topology
from tools.v3.eval_v2_production_tests.contract_test import manifest

clock_kernel = s.clock_kernel


@contextmanager
def frozen_runtime(tmp_path, cfg):
    """Real frozen Store/Runtime layout; only CPU encoder/device probes injected."""
    run = tmp_path / "run"
    old = manifest(tasks=[f"Task{i}" for i in range(18)], episodes=2)
    frozen = build_manifest(
        tasks=old["tasks"],
        episodes=old["episodes_per_task"],
        seed=old["seed"],
        horizons=old["horizons"],
        experiment=old["experiment"],
        execution=execution(cfg),
    )
    store = Store(run, frozen)
    store.create()
    child = Path(__file__).resolve().parents[3] / "cosmos-framework"
    fixture = Path(__file__).with_name("shared_vae_daemon_fixture.py")
    measurements = []

    def cpu_probe(config, processes):
        pids = sorted(owned_group_pids(processes))
        rss = 0
        for pid in pids:
            for line in (Path("/proc") / str(pid) / "status").read_text().splitlines():
                if line.startswith("VmRSS:"):
                    rss += int(line.split()[1]) * 1024
        value = dict(
            rss_bytes=rss,
            owned_pids=pids,
            owned_gpu_bytes={
                g: 0 for g in set(config["gpu_ids"] + config["render_gpu_ids"])
            },
        )
        measurements.append(copy.deepcopy(value))
        return value

    def supervisor_for(runtime):
        return module.SharedVAESupervisor(
            runtime,
            command_factory=lambda public, private, ready: [
                sys.executable,
                "-B",
                str(fixture),
                str(private),
                str(ready),
                public["clock_domain"],
            ],
        )

    with store.locked():
        with patch.object(Runtime, "_make_shared_vae_supervisor", supervisor_for):
            runtime = Runtime(
                store,
                cfg,
                {},
                dict(os.environ, PYTHONPATH=str(child)),
                resource_probe=cpu_probe,
            )
        runtime.commands, runtime.proofs, runtime.cpu_measurements = (
            [],
            [],
            measurements,
        )
        runtime._shared_gpu_identity = lambda gpu: dict(
            gpu_id=gpu, uuid=f"GPU-synthetic-{gpu}", pci_bus_id=f"0000:{gpu:02x}:00.0"
        )
        original_spawn, original_proof = runtime._spawn, runtime._proof

        def spawn(command, **options):
            runtime.commands.append(list(command))
            return original_spawn(command, **options)

        def proof(kind, record):
            runtime.proofs.append((kind, copy.deepcopy(record)))
            return original_proof(kind, record)

        runtime._spawn, runtime._proof = spawn, proof
        try:
            yield runtime
        finally:
            try:
                runtime.shared_vae.close()
            finally:
                runtime.registry.recover()
                for log in runtime.logs:
                    log.close()


@contextmanager
def rig_for(tmp_path, servers, sims, same_render, *, streaming=False):
    cfg = topology(
        tmp_path, servers, sims, 8, same_render=same_render, streaming=streaming
    )
    cfg.update(server_python=sys.executable, server_start_s=10, terminate_grace_s=5)
    with frozen_runtime(tmp_path, cfg) as runtime:
        with owners_for(runtime) as rig:
            yield rig


@contextmanager
def owners_for(runtime):
    cfg, slots = runtime.cfg, runtime.worker_gpus
    actors, owners, http, threads = {}, {}, [], []
    batches, boundaries, http_errors = {}, {}, []

    def handler_for(service):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                record = json.loads(
                    self.rfile.read(int(self.headers["Content-Length"]))
                )
                try:
                    reply = wire.transaction_dispatch(
                        service, "POST", self.path, record, self.headers
                    )
                    status, body = reply.status, reply.body
                except Exception as error:
                    http_errors.append(
                        dict(
                            path=self.path,
                            error_type=type(error).__name__,
                            error=str(error),
                            traceback=traceback.format_exc(),
                        )
                    )
                    status, body = (
                        400,
                        json.dumps(dict(error=type(error).__name__)).encode(),
                    )
                self.send_response(status)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        return Handler

    supervisor = runtime.shared_vae
    external = subprocess.Popen([sys.executable, "-c", "import signal; signal.pause()"])
    try:
        for gpu in cfg["gpu_ids"]:
            names = tuple(runtime.slot_ids[w] for w, g in slots.items() if g == gpu)
            base, _ = s.make_adapter(len(names))
            batches[gpu] = []

            def generate(reqs, updates, gpu=gpu):
                batches[gpu].append(len(reqs))
                actions = []
                for req in reqs:
                    row = [req["state"][0]] * 15
                    row[4] = -1.0
                    row[8:14] = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
                    actions.append([list(row) for _ in range(16)])
                return BatchOutput(actions)

            actor = BatchedSessionTransactions(
                FeatureAdapter(base),
                generate,
                lambda: None,
                owner_token=f"cpu-policy-owner-{gpu}",
                run_lease=runtime.store.lease_id,
                manifest_digest=runtime.store.manifest["digest"],
                slot_ids=names,
                capacity_profile=runtime.capacity_profile,
                timeout_s=30,
                max_batch_size=8,
                batch_wait_ms=0,
            )
            owner = FeatureEvidenceOwner(
                f"cpu-policy-owner-{gpu}",
                policy_identity=IDENTITY,
                max_sessions=len(names),
            )
            boundaries[gpu] = {}
            owner.bind_boundary_lookup(
                lambda sid, step, gpu=gpu: boundaries[gpu].get((sid, step))
            )
            service = SimpleNamespace(transactions=actor, feature_evidence_owner=owner)
            server = ThreadingHTTPServer(("127.0.0.1", 0), handler_for(service))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            actors[gpu], owners[gpu] = actor, owner
            http.append(server)
            threads.append(thread)
            runtime.servers[f"GPU{gpu}"] = (None, None, server.server_port)
            runtime.server_owners[f"GPU{gpu}"] = f"cpu-policy-owner-{gpu}"
        yield SimpleNamespace(
            runtime=runtime,
            supervisor=supervisor,
            actors=actors,
            owners=owners,
            external=external,
            boundaries=boundaries,
            batches=batches,
            http_errors=http_errors,
        )
    finally:
        try:
            if supervisor is not None:
                supervisor.close()
        finally:
            for actor in actors.values():
                assert actor.close(timeout_s=5)
                actor._executor.shutdown(wait=True)
            for server in http:
                server.shutdown()
                server.server_close()
            for thread in threads:
                thread.join(3)
                assert not thread.is_alive()
            external.terminate()
            external.wait(3)


def info(clock_domain="cpu-clock"):
    return dict(
        local_feature=dict(
            identity=copy.deepcopy(IDENTITY),
            history_source="sim_shared_vae",
            clock_domain=clock_domain,
            worker_constructor_config={},
        )
    )


@pytest.mark.parametrize(
    "servers,sims,same_render",
    [(1, 1, False), (1, 8, False), (2, 8, False), (2, 8, True), (3, 2, True)],
)
def test_config_drives_workers_owner_enrollment_sessions_end_and_owned_cleanup(
    tmp_path, servers, sims, same_render
):
    with rig_for(tmp_path, servers, sims, same_render) as rig:
        rt, sup = rig.runtime, rig.supervisor
        handles, channels = [], []
        for worker, gpu in rt.worker_gpus.items():
            handle = sup.ensure(worker, info())
            handles.append(handle)
            lease = (
                rig.actors[gpu]
                .register(
                    s.registration(
                        rt.slot_ids[worker],
                        run_lease=rt.store.lease_id,
                        manifest_digest=rt.store.manifest["digest"],
                    ),
                    rt.server_owners[f"GPU{gpu}"],
                )
                .json()["lease"]
            )
            actor = SimpleNamespace(
                nonce=f"actor-{worker}",
                owned=SimpleNamespace(proc=SimpleNamespace(poll=lambda: None)),
            )
            rt.actors[worker] = actor
            rt.slot_generations[worker] = 1
            channel = sup.register_assignment(
                worker, actor, dict(lease=lease), time.monotonic() + 20
            )
            channels.append((lease, channel, gpu))
        expected_workers = len(set(rt.worker_render_gpus.values()))
        assert len(sup.handles) == len(rt.commands) == expected_workers
        assert len(sup.policies) == servers
        assert len({h.owned.proc.pid for h in handles}) == expected_workers
        for render, handle in sup.handles.items():
            count = sum(g == render for g in rt.worker_render_gpus.values())
            policies = {
                rt.worker_gpus[w]
                for w, g in rt.worker_render_gpus.items()
                if g == render
            }
            assert handle.proof["limits"] == dict(
                max_sessions=count, max_policy_epochs=len(policies)
            )
            assert handle.proof["bmax"] == 1 and handle.proof["wait_ms"] == 0
        for gpu, owner in rig.owners.items():
            expected = {
                lease["session_id"]
                for lease, channel, assigned in channels
                if assigned == gpu
            }
            assert set(owner._sessions) == expected and len(expected) == sims
            assert len({s.lease["server_epoch"] for s in owner._sessions.values()}) == 1
        first = channels[0][0]
        scope = next(
            v
            for v in sup.core.scopes.values()
            if v.lease["session_id"] == first["session_id"]
        )
        assert sup.core._end_scope(scope, time.monotonic_ns() + 3_000_000_000)[
            "acknowledged"
        ]
        assert len(rig.owners[channels[0][2]]._sessions) == sims - 1
        assert all(h.owned.proc.poll() is None for h in handles)
        assert rig.external.poll() is None
        assert all(
            h.signing_key.hex() not in json.dumps(rt.commands + rt.proofs)
            for h in handles
        )
        sup.close()
        sup.close()
        assert all(
            h.owned.proc.returncode == 0 and not h.socket_root.exists() for h in handles
        )
        assert rig.external.poll() is None and not sup.relay_root.exists()
        (tmp_path / "os_behavior.json").write_text(
            json.dumps(
                dict(
                    servers=servers,
                    total_sim_slots=servers * sims,
                    workers=expected_workers,
                    worker_pids=sorted({h.owned.proc.pid for h in handles}),
                    worker_returncodes=[
                        h.owned.proc.returncode for h in sup.handles.values()
                    ],
                    all_sessions_registered=True,
                    first_end_isolated=True,
                    external_alive=True,
                    actual_policy_models=False,
                    actual_simulators=False,
                    encoder="synthetic_cpu",
                ),
                indent=2,
            )
        )


@pytest.mark.parametrize(
    "field", ["vae_weights_sha256", "clock_domain", "worker_constructor_config"]
)
def test_reused_worker_rejects_other_policy_identity_or_constructor_changes(
    tmp_path, field
):
    with rig_for(tmp_path, 2, 1, True) as rig:
        workers = list(rig.runtime.worker_gpus)
        handle = rig.supervisor.ensure(workers[0], info())
        changed = info()
        if field == "vae_weights_sha256":
            changed["local_feature"]["identity"][field] = "f" * 64
        else:
            changed["local_feature"][field] = (
                "other" if field == "clock_domain" else {"foreign": True}
            )
        with pytest.raises(ValueError):
            rig.supervisor.ensure(workers[1], changed)
        assert len(rig.supervisor.policies) == 1 and handle.owned.proc.poll() is None
