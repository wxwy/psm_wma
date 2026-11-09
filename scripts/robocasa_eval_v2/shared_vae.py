"""Opt-in Stage3A Worker peer and scoped trusted-Actor completion relay.

Global Policy/Worker owner credentials stay in this Root process. Sims receive
only their own Worker submission capability and one revocable Actor capability
through the existing private Actor control socket. This is an explicitly
controlled same-trust-domain seam, not proof against hostile same-UID processes.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import os
import secrets
import select
import stat
import tempfile
import threading
import time
import urllib.request
import uuid
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.contract import (
    STREAMING_RESOURCE_FIELDS,
    validate_shared_vae,
    validate_single_latency,
)
from cosmos_framework.inference.robocasa_vae_client import (
    LocalVAEClient,
    OwnerVAEClient,
    UnixVAEServer,
)
from cosmos_framework.inference.robocasa_vae_daemon import file_sha256
from cosmos_framework.inference.robocasa_vae_protocol import (
    canonical_json,
    strict_json,
    validate_lease,
    validate_raw15,
    validate_history_k,
    selected_history_step,
)


def enabled(cfg):
    return cfg.get("local_evidence_profile", "server_vae") == "sim_shared_vae"


def public_profile(cfg):
    arm = cfg.get("single_latency_arm")
    if arm is None:
        return None
    worker = (
        dict(cfg["sim_shared_vae"], max_rss_bytes=cfg["max_rss_bytes"])
        if arm == "C"
        else None
    )
    return {
        "version": "stage3a_single_v1",
        "arm": arm,
        "history_source": cfg.get("local_evidence_profile", "server_vae"),
        "worker": worker,
    }


def public_shared_profile(cfg):
    return {
        "version": "sim_shared_vae_b1_v1",
        "history_source": "sim_shared_vae",
        "worker": dict(cfg["sim_shared_vae"], max_rss_bytes=cfg["max_rss_bytes"]),
    }


def _worker_drain_timeout_s(value):
    if (
        type(value) not in (int, float)
        or not math.isfinite(value)
        or value <= 0
        or value != int(value)
    ):
        raise ValueError("C Worker terminate_grace_s requires positive whole seconds")
    # Normalize the private wire only; leave resolved config/Resume identity intact.
    return int(value)


def validate_profile(cfg):
    history_k = validate_history_k(cfg.get("local_ttt_history_k", 16))
    if history_k != 16 and (
        not enabled(cfg) or cfg.get("local_memory_mode") != "required"
    ):
        raise ValueError("sparse history K requires shared VAE Local-TTT")
    if cfg.get("local_evidence_profile", "server_vae") not in (
        "server_vae",
        "sim_shared_vae",
    ):
        raise ValueError(
            "explicit server_vae or sim_shared_vae evidence profile required"
        )
    arm = cfg.get("single_latency_arm")
    shared_mode = enabled(cfg)
    if arm is not None and (arm == "C") != shared_mode:
        raise ValueError("single measurement arm differs from selected history source")
    if arm is None and not shared_mode:
        if cfg.get("sim_shared_vae") is not None:
            raise ValueError("Worker configuration requires sim_shared_vae history")
        return
    if arm is not None and (
        cfg.get("execution_profile") != "phase_b"
        or len(cfg["gpu_ids"]) != 1
        or cfg["sims_per_gpu"] != 1
        or cfg["max_infer_batch_size"] != 1
    ):
        raise ValueError(
            "single A/B/C requires exactly one transactional Server and Sim"
        )
    if not shared_mode:
        if cfg.get("sim_shared_vae") is not None:
            raise ValueError("A/B create zero historical VAE Workers")
    else:
        if (
            cfg.get("execution_profile") != "phase_b"
            or cfg.get("local_memory_mode") != "required"
            or type(cfg["max_infer_batch_size"]) is not int
            or not 1 <= cfg["max_infer_batch_size"] <= 8
        ):
            raise ValueError(
                "shared VAE requires transactional Local-TTT and Policy batch1..8"
            )
        _worker_drain_timeout_s(cfg["terminate_grace_s"])
        shared = cfg.get("sim_shared_vae")
        if type(shared) is not dict:
            raise ValueError(
                "explicit C Worker files and resource reservations required"
            )
        # No credentials may enter configuration, resolved snapshots or Manifest.
        expected = {
            "vae_weights",
            "vae_weights_sha256",
            "vae_config",
            "vae_config_sha256",
            "egl_vendor_json",
            "egl_vendor_sha256",
            "bmax",
            "wait_ms",
            "trust_model",
            "resources",
        }
        if set(shared) != expected:
            raise ValueError("exact public Worker configuration required")
        for name, digest_name in (
            ("vae_weights", "vae_weights_sha256"),
            ("vae_config", "vae_config_sha256"),
            ("egl_vendor_json", "egl_vendor_sha256"),
        ):
            path = Path(os.path.expandvars(shared[name])).absolute()
            if not path.is_file() or file_sha256(path) != shared[digest_name]:
                raise ValueError("frozen Worker input hash mismatch")
            shared[name] = str(path)
        vendor = json.loads(Path(shared["egl_vendor_json"]).read_text())
        library = vendor.get("ICD", {}).get("library_path", "")
        if "nvidia" not in str(library).lower():
            raise ValueError("C Sim requires an explicit NVIDIA-only EGL vendor file")
        if cfg.get("render_backend") != "egl" or (
            arm == "C" and cfg["batch_wait_ms"] != 0
        ):
            raise ValueError(
                "shared VAE requires verified EGL; single C retains zero Policy peer wait"
            )
        if cfg.get("streaming_resources") is not None and any(
            cfg["streaming_resources"][key] != shared["resources"][key]
            for key in STREAMING_RESOURCE_FIELDS
        ):
            raise ValueError(
                "C may not override existing streaming resource reservations"
            )
    if arm is not None:
        validate_single_latency(
            public_profile(cfg), local_memory=cfg["local_memory_mode"]
        )
    else:
        validate_shared_vae(
            public_shared_profile(cfg), local_memory=cfg["local_memory_mode"]
        )


def input_files(cfg):
    if not enabled(cfg):
        return []
    value = cfg["sim_shared_vae"]
    return [
        (Path(value[name]), value[sha])
        for name, sha in (
            ("vae_weights", "vae_weights_sha256"),
            ("vae_config", "vae_config_sha256"),
            ("egl_vendor_json", "egl_vendor_sha256"),
        )
    ]


def resource_settings(cfg):
    if enabled(cfg):
        return cfg["sim_shared_vae"]["resources"]
    return cfg["streaming_resources"]


def _remaining(deadline_ns):
    if type(deadline_ns) is not int or deadline_ns <= time.monotonic_ns():
        raise TimeoutError("original Owner operation deadline exhausted")
    return max(0.000001, (deadline_ns - time.monotonic_ns()) / 1e9)


def _directory_identity(path):
    value = path.lstat()
    if not stat.S_ISDIR(value.st_mode) or stat.S_IMODE(value.st_mode) != 0o700:
        raise ValueError("private owned IPC directory required")
    return value.st_dev, value.st_ino


def _remove_directory(path, identity):
    try:
        if _directory_identity(path) != identity:
            raise RuntimeError("owned IPC directory identity changed")
        path.rmdir()  # Never recursively delete unknown files or replacement paths.
    except FileNotFoundError:
        pass


class PolicyOwnerHTTP:
    def __init__(self, url, token):
        self.url, self._token = url.rstrip("/"), token
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def __call__(self, operation, body, deadline_ns):
        request = urllib.request.Request(
            self.url + "/v2/feature/" + operation,
            data=canonical_json(body),
            headers={"Content-Type": "application/json", "X-Cosmos-Owner": self._token},
            method="POST",
        )
        with self._opener.open(
            request, timeout=min(30, _remaining(deadline_ns))
        ) as response:
            raw = response.read(1_048_577)
        if len(raw) > 1_048_576:
            raise ValueError("bounded Policy Owner response required")
        result = json.loads(raw)
        if (
            isinstance(result, dict)
            and set(result) == {"ok", "result"}
            and result["ok"] is True
        ):
            return result["result"]
        return result


@dataclass
class WorkerHandle:
    owned: object
    record: dict
    proof: dict
    public: dict
    owner: object = field(repr=False)
    signing_key: bytes = field(repr=False)
    ready_fd: int = field(repr=False)
    socket_root: Path
    socket_root_identity: tuple

    def end(self, session_id, capability, deadline_ns):
        return LocalVAEClient(self.public["socket_path"], session_id, capability).end(
            deadline_ns
        )


@dataclass
class _Scope:
    lease: dict
    handle: WorkerHandle
    policy: object = field(repr=False)
    actor_id: str
    actor_epoch: str
    capability: str = field(repr=False)
    worker_capability: str = field(repr=False)
    deadline: int
    active: object = field(repr=False)
    lock: object = field(default_factory=threading.RLock, repr=False)
    chunk: dict | None = None
    completed: int = 0
    steps: OrderedDict = field(default_factory=OrderedDict)
    closed: bool = False
    end_receipt: dict | None = None


class _RelayCore:
    def __init__(self):
        self.lock = threading.RLock()
        self.scopes = {}
        self.stopping = False

    def add(self, scope):
        with self.lock:
            if self.stopping:
                raise RuntimeError("Actor relay is closing")
            # Keep at most one current and one ended scope per physical Slot.
            for key, old in list(self.scopes.items()):
                if old.lease["slot_id"] == scope.lease["slot_id"]:
                    if not old.closed:
                        raise RuntimeError(
                            "previous Worker Session has not received End"
                        )
                    del self.scopes[key]
            self.scopes[hashlib.sha256(scope.capability.encode()).digest()] = scope

    def dispatch(self, request, deadline):
        common = {"op", "deadline_ns", "actor_capability", "lease"}
        extra = {
            "chunk": {
                "chunk_id",
                "request_key",
                "payload_sha256",
                "source_start",
                "count",
            },
            "post_step": {
                "chunk_id",
                "request_key",
                "source_step",
                "source_rgb_sha256",
                "raw15_f32le_b64",
                "step_completed_ns",
            },
            "end": set(),
        }
        op = request.get("op")
        if (
            op not in extra
            or set(request) != common | extra[op]
            or type(request["actor_capability"]) is not str
        ):
            raise ValueError("exact scoped Actor request required")
        with self.lock:
            scope = self.scopes.get(
                hashlib.sha256(request["actor_capability"].encode()).digest()
            )
        if scope is None or not secrets.compare_digest(
            scope.capability, request["actor_capability"]
        ):
            raise PermissionError("unissued Actor capability")
        lease = validate_lease(request["lease"])
        if lease != validate_lease(
            {key: value for key, value in scope.lease.items() if key != "capability"}
        ):
            raise PermissionError("foreign Actor assignment")
        with scope.lock:
            if op == "end":
                return self._end_scope(scope, deadline)
            if scope.closed or self.stopping or not scope.active():
                raise RuntimeError("Actor assignment is no longer active")
            deadline = min(deadline, scope.deadline)
            _remaining(deadline)
            if op == "chunk":
                if (
                    request["chunk_id"] != request["request_key"]
                    or type(request["source_start"]) is not int
                    or request["source_start"] != scope.completed
                    or request["count"] != 16
                ):
                    raise ValueError("committed H16 chunk identity mismatch")
                scope.policy(
                    "issue",
                    {
                        "lease": scope.lease,
                        "request_key": request["request_key"],
                        "payload_sha256": request["payload_sha256"],
                    },
                    deadline,
                )
                boundary = scope.policy(
                    "boundary",
                    {"lease": scope.lease, "source_step": scope.completed},
                    deadline,
                )
                header = boundary["header"]
                if (
                    header["issued_chunk_id"] != request["chunk_id"]
                    or header["policy_request_key"] != request["request_key"]
                    or header["lease"] != lease
                ):
                    raise ValueError(
                        "Policy committed boundary differs from Actor chunk"
                    )
                scope.chunk = {key: request[key] for key in extra["chunk"]}
                return boundary
            from cosmos_framework.inference.robocasa_feature_evidence import (
                validate_boundary_record,
                validate_post_step_receipt,
            )

            step = request["source_step"]
            if type(step) is not int or step < 0 or scope.chunk is None:
                raise ValueError("post-step requires a committed issued chunk")
            fingerprint = hashlib.sha256(
                canonical_json({key: request[key] for key in extra["post_step"]})
            ).hexdigest()
            if step in scope.steps:
                old, receipt = scope.steps[step]
                if old != fingerprint:
                    raise ValueError("completed Actor step changed bytes")
                return receipt
            if (
                step != scope.completed
                or request["chunk_id"] != scope.chunk["chunk_id"]
                or request["request_key"] != scope.chunk["request_key"]
                or not scope.chunk["source_start"]
                <= step
                < scope.chunk["source_start"] + 16
            ):
                raise ValueError(
                    "Actor cannot skip, rename or preauthorize a source step"
                )
            raw15 = validate_raw15(
                base64.b64decode(request["raw15_f32le_b64"], validate=True)
            )
            boundary = None
            if step % 16 == 0:
                boundary = validate_boundary_record(
                    scope.policy(
                        "boundary",
                        {"lease": scope.lease, "source_step": step},
                        deadline,
                    )
                )
                if (
                    boundary["header"]["source_rgb_sha256"]
                    != request["source_rgb_sha256"]
                ):
                    raise ValueError(
                        "successful step RGB differs from Policy current boundary"
                    )
            receipt = validate_post_step_receipt(
                scope.policy(
                    "complete",
                    {
                        "lease": scope.lease,
                        "chunk_id": request["chunk_id"],
                        "request_key": request["request_key"],
                        "source_step": step,
                        "source_rgb_sha256": request["source_rgb_sha256"],
                        "raw15_f32le_b64": base64.b64encode(raw15).decode("ascii"),
                        "step_completed_ns": request["step_completed_ns"],
                        "actor_id": scope.actor_id,
                        "actor_epoch": scope.actor_epoch,
                    },
                    deadline,
                )
            )
            expected_receipt = {
                "lease": lease,
                "issued_chunk_id": request["chunk_id"],
                "policy_request_key": request["request_key"],
                "source_step": step,
                "source_rgb_sha256": request["source_rgb_sha256"],
                "raw15_sha256": hashlib.sha256(raw15).hexdigest(),
                "actor_id": scope.actor_id,
                "actor_epoch": scope.actor_epoch,
                "clock_domain": scope.handle.public["clock_domain"],
                "episode_deadline_ns": str(scope.deadline),
                "step_completed_ns": request["step_completed_ns"],
            }
            history_k = scope.handle.public.get("local_ttt_history_k", 16)
            selected = selected_history_step(
                step, scope.chunk["source_start"], history_k
            )
            if history_k != 16:
                expected_receipt.update(history_k=history_k, selected=selected)
            if any(receipt[name] != value for name, value in expected_receipt.items()):
                raise ValueError(
                    "Policy post-step receipt differs from actual scoped Actor completion"
                )
            if boundary is not None:
                scope.handle.owner.boundary_skip(
                    lease,
                    request["chunk_id"],
                    request["request_key"],
                    step,
                    request["source_rgb_sha256"],
                    hashlib.sha256(raw15).hexdigest(),
                    boundary["policy_boundary_sha256"],
                    receipt,
                    deadline,
                )
                scope.handle.owner.issue(
                    lease["session_id"],
                    request["chunk_id"],
                    request["request_key"],
                    step + 1,
                    15,
                    deadline,
                )
            else:
                scope.handle.owner.complete(
                    lease["session_id"],
                    request["chunk_id"],
                    step + 1,
                    deadline,
                    **({"skipped_receipt": receipt} if not selected else {}),
                )
            scope.steps[step] = (fingerprint, receipt)
            while len(scope.steps) > 32:
                scope.steps.popitem(last=False)
            scope.completed += 1
            return receipt

    def _end_scope(self, scope, deadline):
        if scope.closed:
            return copy.deepcopy(scope.end_receipt)
        first = None
        try:
            ended = scope.policy("end", {"lease": scope.lease}, deadline)
            if type(ended) is not dict or ended.get("ended") is not True:
                raise RuntimeError("Policy feature authority did not acknowledge End")
        except BaseException as error:
            first = error
        try:
            receipt = scope.handle.end(
                scope.lease["session_id"], scope.worker_capability, deadline
            )
        except BaseException as error:
            if first is None:
                first = error
            elif callable(getattr(first, "add_note", None)):
                first.add_note("Worker End also failed: " + type(error).__name__)
        if first is not None:
            raise first
        if receipt.get("acknowledged") is True and receipt.get("quiescent") is True:
            scope.closed, scope.end_receipt = True, copy.deepcopy(receipt)
        return receipt

    def close(self, deadline_ns):
        with self.lock:
            self.stopping = True
            scopes = list(self.scopes.values())
        safe, first = True, None
        for scope in scopes:
            try:
                with scope.lock:
                    if not scope.closed:
                        self._end_scope(scope, deadline_ns)
                    safe = safe and scope.closed
            except BaseException as error:
                safe = False
                if first is None:
                    first = error
                elif callable(getattr(first, "add_note", None)):
                    first.add_note(
                        "Another feature Session cleanup failed: "
                        + type(error).__name__
                    )
        if first is not None:
            raise first
        return {"closed": safe, "quiescent": safe}


class ScopedActorRelay(UnixVAEServer):
    def _dispatch(self, lane, request, accepted_deadline):
        if lane != "control":
            raise PermissionError(
                "Actor completion requires its scoped control channel"
            )
        return self.worker.dispatch(request, accepted_deadline), False


def _read_event(fd, owned, deadline, stop, *, allow_exit=False):
    raw = bytearray()
    while True:
        if stop.is_set():
            raise RuntimeError("Worker startup was cancelled")
        remaining = _remaining(deadline)
        readable = select.select([fd], [], [], min(0.1, remaining))[0]
        if not readable:
            if owned.proc.poll() is not None:
                raise RuntimeError("Worker exited before an owned lifecycle receipt")
            continue
        if not allow_exit and owned.proc.poll() is not None:
            raise RuntimeError("Worker exited before READY admission")
        byte = os.read(fd, 1)
        if not byte or len(raw) >= 65536:
            raise RuntimeError("Worker READY channel closed or exceeded bound")
        if byte == b"\n":
            return strict_json(bytes(raw), max_bytes=65536)
        raw.extend(byte)


class SharedVAESupervisor:
    def __init__(self, runtime, *, policy_type=PolicyOwnerHTTP, command_factory=None):
        self.runtime, self.policy_type, self.command_factory = (
            runtime,
            policy_type,
            command_factory,
        )
        self.handles, self.policies = {}, {}
        self.lock = threading.RLock()
        self.closing = False
        self.closed = False
        self.core = _RelayCore()
        self.relay_root = Path(tempfile.mkdtemp(prefix="psm24-relay-"))
        self.relay_root_identity = _directory_identity(self.relay_root)
        self.relay = ScopedActorRelay(
            self.core,
            self.relay_root / "a",
            secrets.token_bytes(32),
            connection_timeout_s=30,
        ).start()

    def _enroll_policy(self, handle, worker):
        runtime = self.runtime
        gpu = runtime.worker_render_gpus[worker]
        policy_gpu = runtime.worker_gpus[worker]
        route = (gpu, policy_gpu)
        if route in self.policies:
            return self.policies[route]
        key = "GPU" + str(policy_gpu)
        policy = self.policy_type(
            "http://127.0.0.1:" + str(runtime.servers[key][2]),
            runtime.server_owners[key],
        )
        public = handle.public
        policy(
            "enroll",
            {
                "worker_id": public["worker_id"],
                "worker_epoch": public["worker_epoch"],
                "key_id": public["key_id"],
                "key_hex": handle.signing_key.hex(),
                "identity": public["identity"],
                "clock_domain": public["clock_domain"],
                "bmax": 1,
                "wait_ms": 0,
            },
            time.monotonic_ns() + 30_000_000_000,
        )
        self.policies[route] = policy
        return policy

    def ensure(self, worker, policy_info):
        runtime, cfg = self.runtime, self.runtime.cfg
        gpu = runtime.worker_render_gpus[worker]
        with self.lock:
            if self.closing:
                raise RuntimeError("shared Worker supervisor is closing")
            if runtime.stop.is_set():
                raise RuntimeError("cancelled before shared Worker startup")
            settings = cfg["sim_shared_vae"]
            feature = policy_info["local_feature"]
            history_k = validate_history_k(cfg.get("local_ttt_history_k", 16))
            if validate_history_k(feature.get("local_ttt_history_k", 16)) != history_k:
                raise ValueError(
                    "Policy history K differs from frozen Run configuration"
                )
            if (
                feature.get("history_source") != "sim_shared_vae"
                or feature["identity"]["encoder_backend"] != "eager"
            ):
                raise ValueError("C Policy did not attest the actual eager VAE")
            constructor = strict_json(
                Path(settings["vae_config"]).read_bytes(), max_bytes=65536
            )
            if constructor != feature["worker_constructor_config"]:
                raise ValueError(
                    "frozen Worker configuration differs from actual Policy constructor"
                )
            if gpu in self.handles:
                handle = self.handles[gpu]
                if handle.owned.proc.poll() is not None:
                    raise RuntimeError(
                        "shared Worker exited; restart requires a fresh Session/epoch"
                    )
                if (
                    handle.public["identity"] != feature["identity"]
                    or handle.public["clock_domain"] != feature["clock_domain"]
                    or handle.public["constructor_config"] != constructor
                    or handle.public.get("local_ttt_history_k", 16) != history_k
                ):
                    raise ValueError(
                        "Policy differs from the already loaded shared Worker"
                    )
                try:
                    self._enroll_policy(handle, worker)
                except BaseException:
                    runtime.stop.set()
                    raise
                return handle
            members = [
                slot
                for slot, assigned in runtime.worker_render_gpus.items()
                if assigned == gpu
            ]
            policy_count = len({runtime.worker_gpus[slot] for slot in members})
            socket_root = Path(tempfile.mkdtemp(prefix="psm24-vae-"))
            socket_root_identity = _directory_identity(socket_root)
            worker_id, epoch, key_id = (
                "GPU" + str(gpu),
                uuid.uuid4().hex,
                uuid.uuid4().hex,
            )
            signing, control = secrets.token_bytes(32), secrets.token_bytes(32)
            public = {
                "worker_id": worker_id,
                "worker_epoch": epoch,
                "key_id": key_id,
                "clock_domain": feature["clock_domain"],
                "identity": feature["identity"],
                "vae_weights": settings["vae_weights"],
                "vae_file_sha256": settings["vae_weights_sha256"],
                "constructor_config": constructor,
                "socket_path": str(socket_root / "v"),
                "bmax": 1,
                "wait_ms": 0,
                "physical_device": runtime._shared_gpu_identity(gpu),
                "drain_timeout_s": _worker_drain_timeout_s(cfg["terminate_grace_s"]),
                "max_sessions": len(members),
                "max_policy_epochs": policy_count,
                **({"local_ttt_history_k": history_k} if history_k != 16 else {}),
            }
            secret_read, secret_write = os.pipe()
            ready_read, ready_write = os.pipe()
            owned = None
            log = (runtime.store.root / "logs" / f"vae_{worker_id}_{epoch}.log").open(
                "ab"
            )
            with runtime.state_lock:
                runtime.logs.append(log)
            command = [
                cfg["server_python"],
                "-B",
                "-m",
                "cosmos_framework.inference.robocasa_vae_daemon",
                "--bootstrap-fd",
                str(secret_read),
                "--ready-fd",
                str(ready_write),
            ]
            if self.command_factory is not None:
                command = self.command_factory(public, secret_read, ready_write)
            try:
                with runtime.startup_budget.reserve("vae:" + str(gpu), "vae", gpu):
                    owned, record = runtime._spawn(
                        command,
                        kind="shared_vae_worker:" + worker_id,
                        env=dict(runtime.environment, CUDA_VISIBLE_DEVICES=str(gpu)),
                        cwd=runtime.child_root,
                        pass_fds=(secret_read, ready_write),
                        stdout=log,
                        stderr=log,
                    )
                    os.close(secret_read)
                    secret_read = None
                    os.close(ready_write)
                    ready_write = None
                    private = canonical_json(
                        {
                            "public": public,
                            "signing_key_hex": signing.hex(),
                            "control_capability_hex": control.hex(),
                        }
                    )
                    if len(private) > 65536:
                        raise ValueError("bounded private Worker bootstrap required")
                    deadline = time.monotonic_ns() + int(cfg["server_start_s"] * 1e9)
                    os.set_blocking(secret_write, False)
                    while private:
                        if not select.select(
                            [], [secret_write], [], min(0.1, _remaining(deadline))
                        )[1]:
                            continue
                        count = os.write(secret_write, private)
                        private = private[count:]
                    os.close(secret_write)
                    secret_write = None
                    proof = _read_event(ready_read, owned, deadline, runtime.stop)
                    expected = {
                        "kind": "READY",
                        "pid": owned.proc.pid,
                        "worker_id": worker_id,
                        "worker_epoch": epoch,
                        "key_id": key_id,
                        "clock_domain": public["clock_domain"],
                        "bmax": 1,
                        "wait_ms": 0,
                    }
                    if (
                        any(proof.get(key) != value for key, value in expected.items())
                        or proof["attestation"]["identity"] != public["identity"]
                        or proof["physical_device"] != public["physical_device"]
                        or proof.get("limits")
                        != {
                            "max_sessions": len(members),
                            "max_policy_epochs": policy_count,
                        }
                    ):
                        raise ValueError("shared Worker actual READY identity mismatch")
                    if (
                        validate_history_k(proof.get("local_ttt_history_k", 16))
                        != history_k
                    ):
                        raise ValueError("shared Worker READY history K mismatch")
                    attestation = proof["attestation"]
                    if (
                        attestation.get("vae_file_sha256")
                        != settings["vae_weights_sha256"]
                        or attestation.get("constructor_config_sha256")
                        != hashlib.sha256(canonical_json(constructor)).hexdigest()
                    ):
                        raise ValueError(
                            "actual loaded Worker source-file/config proof mismatch"
                        )
                    if self.command_factory is None and (
                        attestation.get("backend") != "actual_loaded_wan"
                        or attestation.get("device_type") != "cuda"
                    ):
                        raise ValueError(
                            "synthetic encoder may not enter the production C profile"
                        )
                    if set(proof["sockets"]) != {
                        public["socket_path"],
                        public["socket_path"] + ".ctl",
                    }:
                        raise ValueError(
                            "complete Worker data/control socket proof required"
                        )
                    for path, expected_socket in proof["sockets"].items():
                        actual = Path(path).lstat()
                        if not stat.S_ISSOCK(actual.st_mode) or (
                            actual.st_dev,
                            actual.st_ino,
                            stat.S_IMODE(actual.st_mode),
                        ) != (
                            expected_socket["device"],
                            expected_socket["inode"],
                            0o600,
                        ):
                            raise ValueError(
                                "shared Worker owned socket proof mismatch"
                            )
                owner = OwnerVAEClient(public["socket_path"], control)
                handle = WorkerHandle(
                    owned,
                    record,
                    proof,
                    public,
                    owner,
                    signing,
                    ready_read,
                    socket_root,
                    socket_root_identity,
                )
                self._enroll_policy(handle, worker)
                with runtime.starting:
                    if runtime._closing or runtime.stop.is_set():
                        raise RuntimeError("Worker READY completed after cancellation")
                    self.handles[gpu] = handle
                runtime._proof(
                    "shared_vae_worker_ready", {"process": record, "proof": proof}
                )
                return handle
            except BaseException as primary:
                runtime.stop.set()
                if owned is not None:
                    try:
                        runtime.registry.close(owned, record)
                    except BaseException as cleanup:
                        if callable(getattr(primary, "add_note", None)):
                            primary.add_note(
                                "Worker startup cleanup also failed: "
                                + type(cleanup).__name__
                            )
                os.close(ready_read)
                raise
            finally:
                for descriptor in (secret_read, secret_write, ready_write):
                    if descriptor is not None:
                        os.close(descriptor)

    def register_assignment(self, worker, actor, assignment, deadline):
        runtime = self.runtime
        handle = self.handles[runtime.worker_render_gpus[worker]]
        policy = self.policies[
            (runtime.worker_render_gpus[worker], runtime.worker_gpus[worker])
        ]
        lease = assignment["lease"]
        actor_id, actor_epoch = runtime.slot_ids[worker], actor.nonce
        capability, worker_capability = (
            secrets.token_urlsafe(32),
            secrets.token_urlsafe(32),
        )
        deadline_ns = int(deadline * 1e9)
        public_lease = {
            key: value for key, value in lease.items() if key != "capability"
        }
        try:
            handle.owner.register(
                public_lease, worker_capability, deadline_ns, deadline_ns
            )
            policy(
                "register",
                {
                    "lease": lease,
                    "worker_id": handle.public["worker_id"],
                    "actor_id": actor_id,
                    "actor_epoch": actor_epoch,
                    "episode_deadline_ns": str(deadline_ns),
                },
                deadline_ns,
            )
            scope = _Scope(
                lease,
                handle,
                policy,
                actor_id,
                actor_epoch,
                capability,
                worker_capability,
                deadline_ns,
                lambda: not runtime.stop.is_set()
                and runtime.actors.get(worker) is actor
                and actor.owned.proc.poll() is None
                and runtime.slot_generations[worker] == lease["generation"],
            )
            self.core.add(scope)
        except BaseException as primary:
            runtime.stop.set()  # Do not reuse an assignment with half-open authorities.
            cleanup_deadline = time.monotonic_ns() + int(
                runtime.cfg["terminate_grace_s"] * 1e9
            )
            for cleanup in (
                lambda: policy("end", {"lease": lease}, cleanup_deadline),
                lambda: handle.end(
                    lease["session_id"], worker_capability, cleanup_deadline
                ),
            ):
                try:
                    cleanup()
                except BaseException as error:
                    if callable(getattr(primary, "add_note", None)):
                        primary.add_note(
                            "Partial registration cleanup failed: "
                            + type(error).__name__
                        )
            raise
        return {
            "relay_socket": str(self.relay.path) + ".ctl",
            "actor_capability": capability,
            "worker_socket": handle.public["socket_path"],
            "worker_session_capability": worker_capability,
            "worker_id": handle.public["worker_id"],
            "worker_epoch": handle.public["worker_epoch"],
            "key_id": handle.public["key_id"],
            "identity": handle.public["identity"],
            "clock_domain": handle.public["clock_domain"],
            "trust_model": "registry_same_trust_domain",
            **(
                {"local_ttt_history_k": handle.public["local_ttt_history_k"]}
                if "local_ttt_history_k" in handle.public
                else {}
            ),
            "actor_id": actor_id,
            "actor_epoch": actor_epoch,
        }

    def close(self):
        with self.lock:
            if self.closed:
                return
            self.closing = True
            return self._close()

    def _close(self):
        deadline = time.monotonic_ns() + int(
            self.runtime.cfg["terminate_grace_s"] * 1e9
        )
        relay = self.relay.close(deadline)
        if not relay.get("quiescent") or not relay.get("ipc_quiescent"):
            raise RuntimeError("Actor relay did not quiesce")
        _remove_directory(self.relay_root, self.relay_root_identity)
        for handle in self.handles.values():
            receipt = handle.owner.shutdown(deadline)
            if not receipt.get("closed") or not receipt.get("quiescent"):
                raise RuntimeError("shared Worker did not drain")
            closed = _read_event(
                handle.ready_fd,
                handle.owned,
                deadline,
                threading.Event(),
                allow_exit=True,
            )
            if closed.get("kind") != "CLOSED" or not closed["receipt"].get(
                "ipc_quiescent"
            ):
                raise RuntimeError("shared Worker IPC close proof missing")
            handle.owned.proc.wait(timeout=_remaining(deadline))
            self.runtime.registry.close(handle.owned, handle.record)
            if handle.owned.proc.returncode not in (None, 0):
                raise RuntimeError(
                    "shared Worker exited abnormally after its close receipt"
                )
            os.close(handle.ready_fd)
            _remove_directory(handle.socket_root, handle.socket_root_identity)
            self.runtime._proof(
                "shared_vae_worker_closed",
                {"process": handle.record, "receipt": closed},
            )
        self.closed = True
