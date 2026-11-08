"""Stage3A Root authority/lifecycle CPU contracts; model/GPU boundaries doubled."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest
from cosmos_framework.inference.robocasa_feature_evidence import (
    FeatureEvidenceOwner,
    PolicyBoundary,
)
from cosmos_framework.inference.robocasa_vae_client import (
    LocalVAEClient,
    OwnerVAEClient,
    UnixVAEServer,
    VAEIPCError,
)
from cosmos_framework.inference.robocasa_vae_protocol import (
    Frame,
    RGB_BYTES,
    source_digest,
    verify_feature,
)
from cosmos_framework.inference.robocasa_vae_worker import SharedVAEWorker, WorkerConfig
from cosmos_framework.simulation.robocasa.sim_shared_vae_client import (
    ScopedActorCompletionChannel,
)
from robocasa_eval_v2 import shared_vae as module
from robocasa_eval_v2.config import DEFAULTS, execution
from robocasa_eval_v2.startup import StartupBudget
from robocasa_eval_v2_processes import Registry


IDENTITY = {
    "vae_weights_sha256": "a" * 64,
    "vae_config_sha256": "b" * 64,
    "preprocess_profile_sha256": "c" * 64,
    "visual96_contract_sha256": "d" * 64,
    "encoder_backend": "eager",
    "encoder_dtype": "bfloat16",
}
RAW = struct.pack("<15f", *([0.01] * 15))
VISUAL = struct.pack("<96f", *([0.125] * 96))
POLICY_CONTROL = "policy-owner-only-test-capability"
SESSION_CAP = "session-data-only-test-capability"


def lease(generation=1):
    return {
        "server_epoch": "policy-epoch",
        "run_lease": "run",
        "manifest_digest": "e" * 64,
        "slot_id": "physical-slot",
        "generation": generation,
        "task": "CloseFridge",
        "episode_index": generation - 1,
        "attempt_id": f"attempt-{generation}",
        "session_id": f"session-{generation}",
        "episode_id": f"episode-{generation}",
        "capability": "native-session-only-test-capability",
    }


def public(value):
    return {key: entry for key, entry in value.items() if key != "capability"}


def deadline():
    return time.monotonic_ns() + 20_000_000_000


def profile_config(tmp_path, arm="C"):
    cfg = copy.deepcopy(DEFAULTS)
    cfg.update(
        execution_profile="phase_b",
        gpu_ids=[6],
        render_gpu_ids=[4],
        render_backend="egl",
        single_latency_arm=arm,
        local_memory_mode="off" if arm == "A" else "required",
    )
    if arm == "C":
        files = {
            "vae_weights": b"synthetic-file-not-real-weights",
            "vae_config": b"{}",
            "egl_vendor_json": b'{"ICD":{"library_path":"libEGL_nvidia.so.0"}}',
        }
        shared = {}
        for name, raw in files.items():
            path = tmp_path / name
            path.write_bytes(raw)
            shared[name] = str(path)
            shared[
                {
                    "vae_weights": "vae_weights_sha256",
                    "vae_config": "vae_config_sha256",
                    "egl_vendor_json": "egl_vendor_sha256",
                }[name]
            ] = hashlib.sha256(raw).hexdigest()
        shared.update(
            bmax=1,
            wait_ms=0,
            trust_model="registry_same_trust_domain",
            resources={
                "max_owned_gpu_bytes": 1000,
                "sim_startup_rss_bytes": 30,
                "sim_startup_gpu_bytes": 20,
                "server_startup_rss_bytes": 100,
                "server_startup_gpu_bytes": 100,
                "vae_startup_rss_bytes": 50,
                "vae_startup_gpu_bytes": 50,
                "initialization_concurrency": 1,
            },
        )
        cfg.update(
            local_evidence_profile="sim_shared_vae",
            sim_shared_vae=shared,
            batch_wait_ms=0,
        )
    return cfg


@pytest.mark.parametrize("arm", ["A", "B", "C"])
def test_explicit_single_profile_is_frozen_and_default_has_no_worker(tmp_path, arm):
    cfg = profile_config(tmp_path, arm)
    module.validate_profile(cfg)
    frozen = execution(cfg)
    assert frozen["single_latency"]["arm"] == arm
    assert module.enabled(cfg) is (arm == "C")
    assert (frozen["single_latency"]["worker"] is not None) is (arm == "C")
    manifest = build_manifest(
        tasks=["CloseFridge"],
        episodes=2,
        seed=0,
        horizons={"CloseFridge": 30},
        experiment={
            "model_digest": "1" * 64,
            "config_sha256": "2" * 64,
            "runtime_digest": "3" * 64,
            "root_sha": "4" * 40,
            "child_sha": "5" * 40,
            "task_metadata": {"CloseFridge": "6" * 64},
        },
        execution=frozen,
        local_memory=cfg["local_memory_mode"],
    )
    assert manifest["execution"] == frozen
    old = copy.deepcopy(DEFAULTS)
    old.update(execution_profile="phase_b")
    assert "single_latency" not in execution(old) and not module.enabled(old)


@pytest.mark.parametrize(
    "change", ["B8", "wait", "trust", "mode", "slots", "secret", "file"]
)
def test_c_profile_rejects_unsupported_or_changed_identity(tmp_path, change):
    cfg = profile_config(tmp_path)
    if change == "B8":
        cfg["sim_shared_vae"]["bmax"] = 8
    elif change == "wait":
        cfg["sim_shared_vae"]["wait_ms"] = 2
    elif change == "trust":
        cfg["sim_shared_vae"]["trust_model"] = "untrusted"
    elif change == "mode":
        cfg["local_memory_mode"] = "off"
    elif change == "slots":
        cfg["sims_per_gpu"] = 2
    elif change == "secret":
        cfg["sim_shared_vae"]["signing_key"] = "must-never-enter-manifest"
    else:
        Path(cfg["sim_shared_vae"]["vae_weights"]).write_bytes(b"changed")
    with pytest.raises(ValueError):
        module.validate_profile(cfg)


def test_c_startup_budget_charges_worker_with_other_pending_roles(tmp_path):
    cfg = profile_config(tmp_path)
    cfg["max_rss_bytes"] = 200
    measured = {"rss_bytes": 10, "owned_gpu_bytes": {4: 10, 6: 10}}
    budget = StartupBudget(cfg, lambda: copy.deepcopy(measured))
    with budget.reserve("server", "server", 6):
        with budget.reserve("vae", "vae", 4):
            assert set(budget.pending) == {"server", "vae"}
            with pytest.raises(RuntimeError, match="RSS"):
                with budget.reserve("second-vae", "vae", 4):
                    pytest.fail("combined RSS reservations were ignored")
        assert set(budget.pending) == {"server"}
    assert budget.pending == {}


@pytest.fixture
def relay_harness():
    root = Path(tempfile.mkdtemp(prefix="psm24-cpu-"))
    encoded, boundaries, native = [], {}, {}
    signing, control = b"S" * 32, b"W" * 32
    worker = SharedVAEWorker(
        lambda frames: [
            encoded.append(frame.header["source_step"]) or VISUAL for frame in frames
        ],
        IDENTITY,
        signing,
        "key",
        "worker",
        worker_epoch="worker-epoch",
        clock_domain="cpu-clock",
        config=WorkerConfig(),
    )
    server = UnixVAEServer(worker, root / "worker" / "v", control).start()
    owner = FeatureEvidenceOwner(
        POLICY_CONTROL, max_sessions=1, policy_identity=IDENTITY
    )
    owner.bind_boundary_lookup(lambda sid, step: boundaries[(sid, step)])
    owner.enroll_worker(
        POLICY_CONTROL,
        worker_id="worker",
        worker_epoch="worker-epoch",
        key_id="key",
        key=signing,
        identity=IDENTITY,
        clock_domain="cpu-clock",
    )

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                if self.headers.get("X-Cosmos-Owner") != POLICY_CONTROL:
                    raise PermissionError("wrong Root owner")
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                op = self.path.rsplit("/", 1)[-1]
                full = body["lease"]
                actual = public(full)
                if op == "register":
                    result = owner.register_session(
                        POLICY_CONTROL,
                        actual,
                        worker_id=body["worker_id"],
                        actor_id=body["actor_id"],
                        actor_epoch=body["actor_epoch"],
                        episode_deadline_ns=int(body["episode_deadline_ns"]),
                    )
                elif op == "issue":
                    item = native[body["request_key"]]
                    assert (
                        item["lease"] == actual
                        and item["payload_sha256"] == body["payload_sha256"]
                    )
                    result = owner.commit_action_chunk(
                        POLICY_CONTROL,
                        actual,
                        chunk_id=body["request_key"],
                        request_key=body["request_key"],
                        source_start=item["start"],
                        actions_f32le=RAW * 16,
                        deadline_ns=item["deadline"],
                    )
                elif op == "boundary":
                    result = owner.boundary_record(
                        POLICY_CONTROL, actual, body["source_step"]
                    )
                elif op == "complete":
                    fields = {
                        key: value
                        for key, value in body.items()
                        if key not in ("lease", "raw15_f32le_b64")
                    }
                    fields["raw15"] = base64.b64decode(body["raw15_f32le_b64"])
                    fields["step_completed_ns"] = int(fields["step_completed_ns"])
                    result = owner.complete_post_step(POLICY_CONTROL, actual, **fields)
                elif op == "end":
                    result = owner.end_session(POLICY_CONTROL, actual)
                else:
                    raise ValueError("unknown test endpoint")
                raw = json.dumps({"ok": True, "result": result}).encode()
                self.send_response(200)
            except Exception as error:
                raw = json.dumps({"error_type": type(error).__name__}).encode()
                self.send_response(400)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    policy = module.PolicyOwnerHTTP(
        f"http://127.0.0.1:{http.server_port}", POLICY_CONTROL
    )
    core = module._RelayCore()
    relay = module.ScopedActorRelay(core, root / "relay" / "a", b"R" * 32).start()
    handle = module.WorkerHandle(
        SimpleNamespace(),
        {},
        {},
        {"socket_path": str(server.path), "clock_domain": "cpu-clock"},
        OwnerVAEClient(server.path, control),
        signing,
        -1,
        server.path.parent,
        (0, 0),
    )

    def register(generation=1):
        full, end = lease(generation), deadline()
        actual = public(full)
        handle.owner.register(actual, SESSION_CAP, end, end)
        policy(
            "register",
            {
                "lease": full,
                "worker_id": "worker",
                "actor_id": "actor",
                "actor_epoch": "actor-epoch",
                "episode_deadline_ns": str(end),
            },
            end,
        )
        cap = "actor-scoped-test-capability-" + str(generation)
        scope = module._Scope(
            full,
            handle,
            policy,
            "actor",
            "actor-epoch",
            cap,
            SESSION_CAP,
            end,
            lambda: True,
        )
        core.add(scope)
        channel = ScopedActorCompletionChannel(str(relay.path) + ".ctl", cap, actual)
        return SimpleNamespace(
            full=full,
            lease=actual,
            deadline=end,
            scope=scope,
            channel=channel,
            worker=LocalVAEClient(server.path, actual["session_id"], SESSION_CAP),
        )

    def committed(session, start=0):
        request = "request-" + str(session.lease["generation"]) + "-" + str(start)
        image = bytes([start % 256]) * RGB_BYTES
        boundary = PolicyBoundary.create(
            lease=session.lease,
            request_key=request,
            chunk_id=request,
            source_step=start,
            source_rgb_sha256=source_digest(image),
            identity=IDENTITY,
            deadline_ns=session.deadline,
            clock_domain="cpu-clock",
            visual96=VISUAL,
        )
        boundaries[(session.lease["session_id"], start)] = boundary
        native[request] = {
            "lease": session.lease,
            "payload_sha256": "f" * 64,
            "start": start,
            "deadline": session.deadline,
        }
        return request, image

    yield SimpleNamespace(
        core=core,
        register=register,
        committed=committed,
        encoded=encoded,
        owner=owner,
        worker=worker,
    )
    try:
        relay.close(deadline())
    finally:
        server.close(deadline())
        http.shutdown()
        http.server_close()
        thread.join(2)
        for parent in (root / "worker", root / "relay"):
            if parent.exists():
                parent.rmdir()
        root.rmdir()


def test_real_owner_http_scoped_relay_sparse_steps_and_two_episode_slot_reuse(
    relay_harness,
):
    h = relay_harness
    for generation in (1, 2):
        session = h.register(generation)
        request, image0 = h.committed(session)
        session.channel.chunk(request, request, "f" * 64, 0, 16, session.deadline)
        session.channel.chunk(request, request, "f" * 64, 0, 16, session.deadline)
        keys = []
        for step in range(16):
            image = image0 if step == 0 else bytes([step]) * RGB_BYTES
            completed = time.monotonic_ns()
            receipt = session.channel.post_step(
                request,
                request,
                step,
                source_digest(image),
                RAW,
                completed,
                session.deadline,
            )
            assert receipt["source_step"] == step
            assert (
                session.channel.post_step(
                    request,
                    request,
                    step,
                    source_digest(image),
                    RAW,
                    completed,
                    session.deadline,
                )
                == receipt
            )
            if step:
                frame = Frame.create(
                    session.lease,
                    request,
                    request,
                    step,
                    image,
                    RAW,
                    IDENTITY,
                    session.deadline,
                    session.deadline,
                    "cpu-clock",
                )
                keys.append(session.worker.submit(frame, session.deadline))
        for key in keys:
            while True:
                result = session.worker.poll(key, session.deadline)
                if result["status"] != "pending":
                    break
                assert time.monotonic_ns() < session.deadline
                time.sleep(0.001)
            assert result["status"] == "ready"
            assert verify_feature(result["feature"], b"S" * 32)["header"][
                "source_step"
            ] in range(1, 16)
            session.worker.ack(key, session.deadline)
        assert session.channel.end(session.deadline)["quiescent"] is True
        assert session.channel.end(session.deadline)["acknowledged"] is True
        assert h.owner._sessions == {} and h.worker.info()["items"] == 0
    assert h.encoded == list(range(1, 16)) * 2


@pytest.mark.parametrize(
    "bad", ["capability", "lease", "unissued", "future_step", "boundary_rgb", "raw15"]
)
def test_scoped_owner_rejects_forged_or_uncompleted_callbacks(relay_harness, bad):
    h, s = relay_harness, relay_harness.register()
    request, image = h.committed(s)
    s.channel.chunk(request, request, "f" * 64, 0, 16, s.deadline)
    channel = s.channel
    if bad == "capability":
        channel = ScopedActorCompletionChannel(
            channel.path.as_posix() + ".ctl", "wrong-actor-capability", s.lease
        )
    if bad == "lease":
        channel = ScopedActorCompletionChannel(
            channel.path.as_posix() + ".ctl",
            channel._actor_capability,
            {**s.lease, "generation": 2},
        )
    with pytest.raises((VAEIPCError, ValueError)):
        channel.post_step(
            "unissued" if bad == "unissued" else request,
            request,
            1 if bad == "future_step" else 0,
            source_digest(bytes([7]) * RGB_BYTES)
            if bad == "boundary_rgb"
            else source_digest(image),
            struct.pack("<15f", *([0.2] * 15)) if bad == "raw15" else RAW,
            time.monotonic_ns(),
            s.deadline,
        )
    assert h.encoded == [] and s.scope.completed == 0


def test_buffered_close_event_is_read_after_normal_process_exit():
    read, write = os.pipe()
    os.write(write, b'{"kind":"CLOSED","receipt":{"ipc_quiescent":true}}\n')
    os.close(write)
    try:
        owned = SimpleNamespace(proc=SimpleNamespace(poll=lambda: 0))
        value = module._read_event(
            read, owned, deadline(), threading.Event(), allow_exit=True
        )
        assert value["kind"] == "CLOSED"
        with pytest.raises(RuntimeError):
            module._read_event(read, owned, deadline(), threading.Event())
    finally:
        os.close(read)


def test_registry_worker_is_peer_survives_sim_end_and_closes_with_private_fd_proof(
    tmp_path,
):
    cfg = profile_config(tmp_path)
    cfg.update(server_python=sys.executable, server_start_s=10, terminate_grace_s=3)
    run = tmp_path / "run"
    (run / "logs").mkdir(parents=True)

    class RootRuntime:
        def __init__(self):
            self.cfg, self.child_root = (
                cfg,
                Path(__file__).resolve().parents[3] / "cosmos-framework",
            )
            self.registry = Registry(run, 0.2)
            self.store = SimpleNamespace(root=run)
            self.stop, self.state_lock, self.starting = (
                threading.Event(),
                threading.RLock(),
                threading.Condition(),
            )
            self._closing = False
            self.logs, self.proofs, self.commands = [], [], []
            self.worker_render_gpus, self.worker_gpus = {"slot": 4}, {"slot": 6}
            self.servers, self.server_owners = (
                {"GPU6": (None, None, 1)},
                {"GPU6": POLICY_CONTROL},
            )
            self.environment = dict(os.environ, PYTHONPATH=str(self.child_root))
            self.startup_budget = StartupBudget(
                cfg, lambda: {"rss_bytes": 0, "owned_gpu_bytes": {4: 0, 6: 0}}
            )

        def _shared_gpu_identity(self, gpu):
            return {
                "gpu_id": gpu,
                "uuid": "GPU-synthetic-cpu-test",
                "pci_bus_id": "0000:00:00.0",
            }

        def _spawn(self, command, **kwargs):
            self.commands.append(list(command))
            return self.registry.start(command, **kwargs)

        def _proof(self, kind, value):
            self.proofs.append((kind, copy.deepcopy(value)))

    runtime = RootRuntime()
    fixture = Path(__file__).with_name("shared_vae_daemon_fixture.py")
    supervisor = module.SharedVAESupervisor(
        runtime,
        policy_type=lambda url, token: lambda operation, body, end: {"enrolled": True},
        command_factory=lambda config, private_fd, ready_fd: [
            sys.executable,
            "-B",
            str(fixture),
            str(private_fd),
            str(ready_fd),
        ],
    )
    external = subprocess.Popen([sys.executable, "-c", "import signal; signal.pause()"])
    sim, sim_record = runtime.registry.start(
        [sys.executable, "-c", "import signal; signal.pause()"], kind="simulator-slot"
    )
    handle = None
    try:
        handle = supervisor.ensure(
            "slot",
            {
                "local_feature": {
                    "identity": IDENTITY,
                    "history_source": "sim_shared_vae",
                    "clock_domain": "cpu-clock",
                    "worker_constructor_config": {},
                }
            },
        )
        parent = int(
            Path(f"/proc/{handle.owned.proc.pid}/stat")
            .read_text()
            .rsplit(")", 1)[1]
            .split()[1]
        )
        assert parent == os.getpid() and parent != sim.proc.pid
        assert handle.record["kind"].startswith("shared_vae_worker:")
        assert handle.proof["attestation"]["backend"] == "synthetic_cpu_test"
        assert "signing_key" not in json.dumps(runtime.commands)
        assert handle.signing_key.hex() not in json.dumps(
            runtime.commands + runtime.proofs
        )
        runtime.registry.close(sim, sim_record)
        assert handle.owned.proc.poll() is None and external.poll() is None
        supervisor.close()
        supervisor.close()
        assert handle.owned.proc.returncode == 0 and external.poll() is None
        assert not handle.socket_root.exists() and not supervisor.relay_root.exists()
        (tmp_path / "lifecycle.json").write_text(
            json.dumps(
                {
                    "worker_pid": handle.owned.proc.pid,
                    "worker_parent_pid": parent,
                    "worker_pgid": handle.record["identity"]["pgid"],
                    "sim_pid": sim.proc.pid,
                    "worker_survived_sim_end": True,
                    "worker_returncode": handle.owned.proc.returncode,
                    "external_pid": external.pid,
                    "external_alive": external.poll() is None,
                    "backend": "synthetic_cpu_test",
                    "zero_gpu_execution": True,
                    "credential_delivery": "inherited_fds_only",
                    "ready": handle.proof,
                },
                sort_keys=True,
            )
        )
    finally:
        try:
            if handle is not None and handle.owned.proc.poll() is None:
                supervisor.close()
        finally:
            runtime.registry.recover()
            for log in runtime.logs:
                log.close()
            external.terminate()
            external.wait(timeout=3)


def test_actual_loaded_tensor_identity_ignores_claimed_hash_and_detects_weight_changes():
    import torch
    from cosmos_framework.inference.robocasa_vae_daemon import loaded_vae_identity

    class Tokenizer:
        chunk_duration = 93
        encode_chunk_frames = {"256": 68, "480": 24, "720": 8}
        encode_exact_durations = [1, 17]
        spatial_compression_factor, temporal_compression_factor = 16, 4
        is_causal, use_streaming_encode, _keep_encoder_cache = True, False, False

        def __init__(self):
            model = (
                torch.nn.Linear(2, 2)
                .to(dtype=torch.bfloat16)
                .eval()
                .requires_grad_(False)
            )
            self.model = SimpleNamespace(
                model=model,
                dtype=torch.bfloat16,
                scale=(
                    torch.ones(48, dtype=torch.bfloat16),
                    torch.ones(48, dtype=torch.bfloat16),
                ),
            )

    tokenizer = Tokenizer()
    first = loaded_vae_identity(tokenizer)
    assert first == loaded_vae_identity(
        tokenizer, {"vae_path": "a-different-location-is-not-weight-evidence"}
    )
    with torch.no_grad():
        tokenizer.model.model.weight[0, 0].add_(1)
    second = loaded_vae_identity(tokenizer)
    assert first["vae_weights_sha256"] != second["vae_weights_sha256"]
    assert first["vae_config_sha256"] == second["vae_config_sha256"]
    tokenizer.model.model._aot_chunk_fns = {(1, 1, 1, 0): object()}
    with pytest.raises(ValueError):
        loaded_vae_identity(tokenizer)


def test_actual_device_guard_rejects_loaded_parameter_uuid_mismatch_without_querying_other_devices(
    monkeypatch,
):
    import torch
    from cosmos_framework.inference import robocasa_vae_daemon as daemon

    device = torch.device("cuda", 0)  # A descriptor, no CUDA initialization.
    encoder = SimpleNamespace(
        tokenizer=SimpleNamespace(
            model=SimpleNamespace(
                model=SimpleNamespace(
                    parameters=lambda: iter([SimpleNamespace(device=device)])
                )
            )
        )
    )
    monkeypatch.setattr(torch.cuda, "device_count", lambda: 1)
    monkeypatch.setattr(
        torch.cuda,
        "get_device_properties",
        lambda target: SimpleNamespace(uuid="GPU-wrong"),
    )
    monkeypatch.setattr(
        daemon.subprocess,
        "check_output",
        lambda *args, **kwargs: pytest.fail(
            "UUID mismatch must fail before any device query"
        ),
    )
    with pytest.raises(ValueError, match="UUID"):
        daemon._physical_device(
            {"gpu_id": 4, "uuid": "GPU-expected", "pci_bus_id": "0000:00:00.0"}, encoder
        )
