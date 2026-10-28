"""Production RoundScheduler -> checked resident Servers -> native Task actors."""

from __future__ import annotations

import hashlib
import json
import re
import socket
import threading
import time
import uuid
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from types import SimpleNamespace

from cosmos_framework.evaluation.robocasa_v2.contract import result_record
from cosmos_framework.evaluation.robocasa_v2.scheduler import (
    RoundScheduler,
    slot_disposition,
)
from cosmos_framework.evaluation.robocasa_v2.store import records, save, write
from eval_robocasa_18task_queue import (
    CHILD,
    ROOT,
    require_free_ports,
    server_argv,
    wait_server,
)
from robocasa_eval_v2_processes import Actor, Registry, process_identity
from robocasa_processes import group_members

from robocasa_eval_v2 import identity, resources


class Runtime:
    def __init__(
        self, store, cfg, inputs, environment, *, resource_probe=resources.check
    ):
        self.store, self.cfg, self.inputs, self.environment = (
            store,
            cfg,
            inputs,
            environment,
        )
        self.stop = threading.Event()
        self.registry = Registry(store.root, cfg["terminate_grace_s"])
        self.servers = {}
        self.actors = {}  # physical worker -> single reusable Sim process
        self.actor_tasks = {}
        self.slot_claim_tasks = {}
        self.slot_environments = {}
        self.slot_ids = {f"GPU{g}": uuid.uuid4().hex for g in cfg["gpu_ids"]}
        self.logs = []
        self.resource_probe = resource_probe
        self.setup_lock = threading.Lock()
        self.certificates = {}
        self.latest_attempts = {}
        self.phases = {}
        self.closed = False
        self.workers = [
            f"GPU{g}" for g in cfg["gpu_ids"][: len(store.manifest["task_order"])]
        ]

    def _proof(self, kind, data):
        name = f"{kind}_{uuid.uuid4().hex}.json"
        path = self.store.root / "_internal/runtime" / name
        save(path, data)
        return (
            str(path.relative_to(self.store.root))
            + ":"
            + hashlib.sha256(path.read_bytes()).hexdigest()
        )

    def recover(self):
        self.registry.recover()
        # Full decommissioning of every old Server/Env group means no old Local
        # session can survive. Refuse to issue a receipt if any registry entry is
        # unclosed; no caller-provided true booleans are accepted from the CLI.
        entries = records(self.store.root / "_internal/processes")
        if any(
            not (
                self.store.root / "_internal/process_closed" / f"{e['id']}.json"
            ).exists()
            for e in entries
        ):
            raise RuntimeError("prior processes not demonstrably closed")
        proof = self._proof(
            "recovered_owned_groups",
            {"records": [e["id"] for e in entries], "owned_groups_gone": True},
        )
        for task in self.store.manifest["task_order"]:
            for stream in self.store._streams(task):
                if not self.store._cleaned(task, stream["stream_id"]):
                    self.store.recovery_error(
                        task,
                        stream["stream_id"],
                        "unclosed_prior_coordinator",
                        "Recovered previously unclosed owned runtime; explicit fresh health proof required",
                    )
                self.store.cleanup_stream(
                    task,
                    stream["stream_id"],
                    lambda _, p=proof: {
                        "probe_id": p,
                        "owned_processes_gone": True,
                        "local_sessions_closed": True,
                    },
                )

        # A crash may occur after Core commit but before resolving its old fault.
        # Reuse the original immutable certificate rather than rerunning a valid
        # Episode or inventing a new scene association for that Core.
        for task in self.store.manifest["task_order"]:
            for error in self.store.errors(task):
                if (
                    error["resolution"] is not None
                    or error["attempt"] is None
                    or error["core_committed_at_fault"]
                ):
                    continue
                row = self.store._result(task, error["attempt"]["episode"])
                if row is None or row["attempt_id"] == error["attempt"]["attempt_id"]:
                    continue
                for cert in records(self.store._internal(task) / "recovery"):
                    if (
                        cert["old"]["stream_id"] == error["stream_id"]
                        and cert["new"]["stream_id"] == row["stream_id"]
                    ):
                        self.store.resolve_error(
                            task, error["id"], cert, replacement=row
                        )
                        break

    def _server(self, worker):
        if worker in self.servers:
            return self.servers[worker]
        self.phases[worker] = "model_loading"
        index = self.workers.index(worker)
        gpu = self.cfg["gpu_ids"][index]
        port = self.cfg["base_port"] + index
        env = dict(self.environment, CUDA_VISIBLE_DEVICES=str(gpu))
        log = (self.store.root / "logs" / f"{worker}_server.log").open("ab")
        self.logs.append(log)
        args = SimpleNamespace(
            server_python=self.cfg["server_python"],
            num_steps=self.cfg["prediction_steps"],
            guidance=self.cfg["guidance"],
        )
        owned, rec = self.registry.start(
            server_argv(
                args, Path(self.cfg["checkpoint"]), Path(self.cfg["config_file"]), port
            ),
            kind="server",
            env=env,
            cwd=CHILD,
            stdout=log,
            stderr=log,
        )
        self.servers[worker] = (owned, rec, port)
        try:
            info = wait_server(
                owned.proc,
                port,
                self.cfg["server_start_s"],
                checkpoint=Path(self.cfg["checkpoint"]),
                config_file=Path(self.cfg["config_file"]),
                num_steps=self.cfg["prediction_steps"],
                guidance=self.cfg["guidance"],
                stop=self.stop,
            )
        except BaseException:
            self.stop.set()
            raise
        self._proof("server_identity", {"process": rec, "info": info})
        return self.servers[worker]

    def _actor(self, claim):
        task = claim["task"]
        worker = claim["physical_worker"]
        with self.setup_lock:
            if self.stop.is_set():
                raise RuntimeError("cancelled before runtime startup")
            server, server_rec, port = self._server(claim["physical_worker"])
            self.phases[claim["physical_worker"]] = "environment_initialization"
            if worker in self.actors:
                return self._start_assignment(claim, self.actors[worker], server_rec)
            nonce = uuid.uuid4().hex
            cfg = {
                "nonce": nonce,
                "manifest_digest": self.store.manifest["digest"],
                "coordinator_lease_id": self.store.lease_id,
                "episodes_per_task": self.store.manifest["episodes_per_task"],
                "physical_slot_id": self.slot_ids[worker],
                "physical_worker": worker,
                "gpu_id": self.cfg["gpu_ids"][self.workers.index(worker)],
                "task_root": str(self.store.root / "_internal/tasks"),
                "tasks": {
                    name: {
                        "dataset_dir": directory,
                        "metadata_sha256": self.store.manifest["experiment"][
                            "task_metadata"
                        ][name],
                        "horizon": self.store.manifest["horizons"][name],
                    }
                    for name, directory in self.inputs["tasks"].items()
                },
                "source_files": {
                    key: {
                        "path": str(CHILD / path),
                        "sha256": hashlib.sha256(
                            (CHILD / path).read_bytes()
                        ).hexdigest(),
                    }
                    for key, path in {
                        "worker": "cosmos_framework/simulation/robocasa/eval_v2_worker.py",
                        "native": "cosmos_framework/simulation/robocasa/closed_loop_eval.py",
                        "adapter": "cosmos_framework/simulation/robocasa/eval_v2_adapter.py",
                        "slot": "cosmos_framework/simulation/robocasa/eval_v2_slot.py",
                    }.items()
                },
                "settings": {
                    "server_url": f"http://127.0.0.1:{port}",
                    "horizon": self.store.manifest["horizons"][task],
                    "predict_timeout_s": self.cfg["request_timeout_s"],
                    "save_rollout_mp4": self.cfg["save_rollout_mp4"],
                    "save_generated_video": self.cfg["save_generated_video"],
                    "encoder_grace_s": self.cfg["encoder_grace_s"],
                },
                "simulation_libraries": self.inputs["simulation_libraries"],
                "runtime_args": {
                    "runtime_probe_script": str(ROOT / "scripts/robocasa_vendor.py"),
                    "runtime_lock_file": self.cfg["vendor_lock"],
                    "runtime_asset_manifest": self.cfg.get("asset_manifest"),
                    "expected_runtime_digest": self.inputs["runtime"]["digest"],
                    "runtime_tasks": ",".join(self.store.manifest["task_order"]),
                },
            }
            path = self.store.root / "_internal/actor_configs" / f"{nonce}.json"
            write(path, cfg)
            parent, child = socket.socketpair()
            gpu = self.cfg["gpu_ids"][self.workers.index(claim["physical_worker"])]
            env = dict(
                self.environment,
                CUDA_VISIBLE_DEVICES=str(gpu),
                MUJOCO_EGL_DEVICE_ID=str(gpu),
            )
            log = (self.store.root / "logs" / f"{worker}_simulator.log").open("ab")
            self.logs.append(log)
            command = [
                self.cfg["sim_python"],
                "-B",
                "-m",
                "cosmos_framework.simulation.robocasa.eval_v2_worker",
                "--config",
                str(path),
                "--config-sha256",
                hashlib.sha256(path.read_bytes()).hexdigest(),
                "--control-fd",
                str(child.fileno()),
            ]
            try:
                owned, rec = self.registry.start(
                    command,
                    kind=f"simulator_slot:{self.slot_ids[worker]}",
                    env=env,
                    cwd=CHILD,
                    pass_fds=(child.fileno(),),
                    stdout=log,
                    stderr=log,
                )
            except BaseException:
                parent.close()
                raise
            finally:
                child.close()
            actor = Actor(
                owned,
                rec,
                parent,
                self.registry,
                nonce,
                self.stop,
                server.proc,
                self.cfg["episode_wall_s"],
            )
            self.actors[worker] = actor
            ready = actor._receive()
            if (
                ready.get("kind") != "READY"
                or ready.get("pid") != owned.proc.pid
                or ready.get("physical_slot_id") != self.slot_ids[worker]
                or ready.get("state") != "IDLE"
                or ready.get("runtime_digest") != self.inputs["runtime"]["digest"]
            ):
                raise RuntimeError("native Worker handshake mismatch")
            self.resource_probe(
                self.cfg,
                [v[0] for v in self.servers.values()]
                + [x.owned for x in self.actors.values()],
            )
            return self._start_assignment(claim, actor, server_rec)

    def _start_assignment(self, claim, actor, server_record):
        worker, task, a = claim["physical_worker"], claim["task"], claim["attempt"]
        self.slot_claim_tasks[worker] = task
        grant = None
        if self.actor_tasks.get(worker) != task:
            grant = self.store.allocate_environment(task, self.slot_ids[worker])
        ready = actor.request(
            "start_episode", attempt=a, grant=grant, health_only="attempt_id" not in a
        )
        if (
            ready.get("task") != task
            or ready.get("physical_slot_id") != self.slot_ids[worker]
            or ready.get("attempt_id") != a.get("attempt_id")
            or ready.get("state") not in ("ENV_READY", "CLEAN")
        ):
            raise RuntimeError("Slot assignment acknowledgement mismatch")
        expected = grant if grant is not None else self.slot_environments[worker]
        if (
            ready.get("environment_id") != expected["environment_id"]
            or ready.get("actual_seed") != expected["seed"]
        ):
            raise ValueError("Slot environment seed grant acknowledgement mismatch")
        self.slot_environments[worker] = expected
        self.actor_tasks[worker] = task
        proof = self._proof(
            "native_slot_health",
            {
                "physical_worker": worker,
                "gpu_id": self.cfg["gpu_ids"][self.workers.index(worker)],
                "actor": actor.record,
                "ready": ready,
                "server": server_record,
            },
        )
        self.resource_probe(
            self.cfg,
            [v[0] for v in self.servers.values()]
            + [x.owned for x in self.actors.values()],
        )
        for error in self.store.errors(task):
            if error["resolution"] is None and error["stream_id"] != a["stream_id"]:
                self.certificates[error["id"]] = self.store.certify_recovery(
                    task,
                    error["stream_id"],
                    lambda _, p=proof: {"probe_id": p, "healthy": True},
                )
        return actor

    def run_slot(self, scheduler, claim):
        a = claim["attempt"]
        task = a["task"]
        self.latest_attempts[task] = a
        self.slot_claim_tasks[claim["physical_worker"]] = task
        try:
            identity.guard(self.cfg, self.store.manifest, self.inputs, source=False)
            actor = self._actor(claim)
            deadline = time.monotonic() + self.cfg.get("episode_wall_s", 1800)
            while True:
                if self.stop.is_set():
                    raise RuntimeError("evaluation cancelled")
                sample = self.store.begin_initialization(a)
                response = actor.request("initialize", deadline=deadline)
                if response.get("error") is None:
                    state = self.store.initialization_outcome(
                        a, initial_success=response["initial_success"]
                    )
                else:
                    proof = response.get("resource_proof", {})
                    safe = response.get("safe_to_retry") is True and all(
                        proof.get(k) is True
                        for k in (
                            "physics_finite",
                            "forward_ok",
                            "sampling_error_class",
                        )
                    )
                    name = response["error"].get("type", "RemoteInitializationError")
                    if (
                        not isinstance(name, str)
                        or not name.isidentifier()
                        or len(name) > 128
                    ):
                        raise ValueError("invalid remote error type")
                    remote = type(name, (Exception,), {})(response["error"]["message"])
                    state = self.store.initialization_outcome(
                        a, error=remote, stage=response["stage"], safe_to_retry=safe
                    )
                if state["status"] == "admitted":
                    admitted_sampling = response["sampling"]
                    expected = self.slot_environments[claim["physical_worker"]]
                    if (
                        admitted_sampling["environment_id"]
                        != expected["environment_id"]
                        or admitted_sampling["actual_seed"] != expected["seed"]
                        or admitted_sampling["physical_slot_id"]
                        != self.slot_ids[claim["physical_worker"]]
                    ):
                        raise ValueError(
                            "admitted scene has foreign environment provenance"
                        )
                    self.store.bind_sampling(a, admitted_sampling)
                    break
                if state["status"] in (
                    "skipped_init_error",
                    "scene_admission_exhausted",
                ):
                    released = actor.request(
                        "finish_without_session", deadline=deadline
                    )
                    if (
                        released.get("state") != "CLEAN"
                        or released.get("session_opened") is not False
                    ):
                        raise RuntimeError("unproven no-Session Slot release")
                    scheduler.finish(claim)
                    return {
                        "task": task,
                        "episode": a["episode"],
                        "outcome": state["status"],
                    }
                if state["status"] == "invalid":
                    raise RuntimeError("unsafe native initialization")
            directory = (
                self.store._ledger(task, a["episode"]) / "work" / a["attempt_id"]
            )
            self.phases[claim["physical_worker"]] = "executing"
            response = actor.request(
                "execute",
                attempt=a,
                reset_index=sample["reset_index"],
                directory=str(directory),
                deadline=deadline,
            )
            sampling = response["sampling"]
            if sampling != admitted_sampling:
                raise ValueError("foreign physical Slot evidence")
            row = result_record(
                self.store.manifest,
                task=task,
                episode=a["episode"],
                generation=a["generation"],
                stream_id=a["stream_id"],
                attempt_id=a["attempt_id"],
                worker_id=a["worker_id"],
                seed=a["seed"],
                reset_index=sample["reset_index"],
                observation=response["observation"],
                instruction=response["instruction"],
                replans=response["replans"],
                elapsed_seconds=response["elapsed_seconds"],
                sampling=sampling,
            )
            self.phases[claim["physical_worker"]] = "result_validation"
            scheduler.commit(claim, row, staging=directory)
            # Encoders are in this Task's owned group. Any late/stray child means
            # resource cleanup is uncertain, independent of the committed SR.
            helpers = set(response.get("media_helper_pids", []))
            if len(helpers) > 1 or any(
                type(pid) is not int or pid <= 0 for pid in helpers
            ):
                raise RuntimeError("invalid media helper ownership")
            for pid in helpers:
                ident = process_identity(pid)
                command = (
                    (Path("/proc") / str(pid) / "cmdline").read_bytes().split(b"\0")
                )
                if (
                    ident is None
                    or ident["pgid"] != actor.owned.pgid
                    or not any(
                        re.fullmatch(
                            rb"from multiprocessing\.resource_tracker import main;main\(\d+\)",
                            v,
                        )
                        for v in command
                    )
                ):
                    raise RuntimeError("unverified media helper process")
            if response.get("media_process_fault") or set(
                group_members(actor.owned.pgid)
            ) - helpers != {actor.owned.proc.pid}:
                raise RuntimeError(
                    "owned media/process descendants remain after Core commit"
                )
            for error in self.store.errors(task):
                cert = self.certificates.get(error["id"])
                if error["resolution"] is None and cert:
                    self.store.resolve_error(
                        task,
                        error["id"],
                        cert,
                        replacement=row
                        if error["attempt"] is not None
                        and not error["core_committed_at_fault"]
                        else None,
                    )
            scheduler.finish(claim)
            self.phases[claim["physical_worker"]] = "idle"
            return {"task": task, "episode": a["episode"], "outcome": row["outcome"]}
        except BaseException as error:
            if task in self.store.active_tasks:
                if self.store._result(task, a["episode"]) is None:
                    self.store.finish_invalid(a, f"{type(error).__name__}: {error}")
                else:
                    self.store.record_process_error(
                        task,
                        "native_episode",
                        f"{type(error).__name__}: {error}",
                        attempt=a,
                    )
            self.stop.set()
            raise

    def close(self):
        if self.closed:
            return
        errors = []
        for worker, actor in list(self.actors.items()):
            task = self.slot_claim_tasks.get(worker, self.actor_tasks.get(worker))
            try:
                was = actor.owned.proc.poll()
                proof = actor.close()
                if proof["close_error"] or was not in (None, 0):
                    raise RuntimeError(str(proof))
            except Exception as e:
                if task in self.store.active_tasks:
                    errors.append((task, repr(e)))
        for worker, (owned, record, port) in self.servers.items():
            try:
                was = owned.proc.poll()
                self.registry.close(owned, record)
                if was is not None:
                    raise RuntimeError(f"Action Server unexpectedly exited {was}")
            except Exception as e:
                task = self.slot_claim_tasks.get(worker, self.actor_tasks.get(worker))
                if task in self.store.active_tasks:
                    errors.append((task, repr(e)))
        for task, message in errors:
            self.store.record_process_error(
                task, "process_cleanup", message, attempt=self.latest_attempts.get(task)
            )
        self.registry.recover()  # Must succeed before any positive cleanup receipt.
        proof = self._proof(
            "final_owned_cleanup",
            {"errors": errors, "all_registry_groups_closed": True},
        )
        for task in list(self.store.active_tasks):
            stream = self.store.active_tasks[task]
            self.store.cleanup_stream(
                task,
                stream["stream_id"],
                lambda _, p=proof: {
                    "probe_id": p,
                    "owned_processes_gone": True,
                    "local_sessions_closed": True,
                },
            )
        for log in self.logs:
            log.close()
        self.closed = True

    def run(self):
        self.recover()
        pending = any(
            slot_disposition(self.store, t, i) == "execute"
            for t in self.store.manifest["task_order"]
            for i in range(self.store.manifest["episodes_per_task"])
        )
        faults = any(
            e["resolution"] is None
            for t in self.store.manifest["task_order"]
            for e in self.store.errors(t)
        )
        if not pending and not faults:
            return self.store.publish_views(), None
        self.resource_probe(self.cfg, before_models=True)
        require_free_ports(
            [self.cfg["base_port"] + i for i in range(len(self.workers))]
        )
        scheduler = RoundScheduler(self.store, self.workers)
        pool = ThreadPoolExecutor(max_workers=len(self.workers))
        futures = {}
        original = None
        last_round = -1
        last_print = 0
        try:
            for task in self.store.manifest["task_order"]:
                old_errors = [
                    e for e in self.store.errors(task) if e["resolution"] is None
                ]
                rows = self.store.rows(task)
                if len(rows) == self.cfg["episodes_per_task"] and old_errors:
                    stream = self.store.begin_task(task, recovery_only=True)
                    worker = self.workers[
                        self.store.manifest["task_order"].index(task)
                        % len(self.workers)
                    ]
                    self._actor(
                        {"task": task, "physical_worker": worker, "attempt": stream}
                    )
                    for e in old_errors:
                        cert = self.certificates[e["id"]]
                        self.store.resolve_error(task, e["id"], cert)
            while not scheduler.done:
                for worker in self.workers:
                    if worker not in scheduler.inflight:
                        claim = scheduler.dispatch(worker)
                        if claim:
                            futures[pool.submit(self.run_slot, scheduler, claim)] = (
                                claim
                            )
                if futures:
                    done, _ = wait(futures, timeout=1, return_when=FIRST_COMPLETED)
                    for f in done:
                        claim = futures.pop(f)
                        result = f.result()
                        print("[eval-v2] " + json.dumps(result), flush=True)
                if self.stop.is_set():
                    raise RuntimeError("native Worker requested safe stop")
                for task, actor in list(self.actors.items()):
                    if actor.owned.proc.poll() is not None:
                        raise RuntimeError(f"native Task Worker exited: {task}")
                if scheduler.round != last_round:
                    identity.guard(self.cfg, self.store.manifest, self.inputs)
                    self.resource_probe(
                        self.cfg,
                        [v[0] for v in self.servers.values()]
                        + [x.owned for x in self.actors.values()],
                    )
                    last_round = scheduler.round
                if time.monotonic() - last_print >= 5:
                    from cosmos_framework.evaluation.robocasa_v2.store import read

                    statuses = []
                    for worker, claim in scheduler.inflight.items():
                        directory = (
                            self.store._ledger(claim["task"], claim["episode"])
                            / "work"
                            / claim["attempt"]["attempt_id"]
                        )
                        try:
                            progress = read(directory / "progress.json")
                            if not isinstance(progress, dict):
                                progress = {}
                        except (ValueError, OSError):
                            progress = {}
                        statuses.append(
                            {
                                "gpu": worker,
                                "task": claim["task"],
                                "episode": claim["episode"],
                                "episodes": self.cfg["episodes_per_task"],
                                "stage": progress.get(
                                    "stage",
                                    self.phases.get(
                                        worker, "environment_initialization"
                                    ),
                                ),
                                "steps": progress.get("steps", 0),
                                "horizon": self.store.manifest["horizons"][
                                    claim["task"]
                                ],
                                "predictions": progress.get("predictions", 0),
                                "last_prediction_ms": progress.get(
                                    "last_prediction_ms"
                                ),
                            }
                        )
                    print(
                        "[eval-v2] "
                        + json.dumps(
                            {"round": scheduler.round + 1, "workers": statuses}
                        ),
                        flush=True,
                    )
                    last_print = time.monotonic()
        except BaseException as e:
            original = e
            self.stop.set()
            scheduler.cancel(repr(e))
            # Keep the approved commit/cancel serialization. A switched-out Task
            # has no in-flight producer merely because its logical stream is open.
            affected = {c["task"] for c in scheduler.inflight.values()}
            for task in affected:
                self.store.record_process_error(
                    task,
                    "coordinator_stop",
                    repr(e),
                    attempt=self.latest_attempts.get(task),
                )
        finally:
            if original is not None:
                for actor in self.actors.values():
                    try:
                        actor.channel.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
            # Threads have bounded Actor requests and observe stop before reset.
            # Keep spawning threads alive until their owned children are closed:
            # Linux parent-death signals are tied to the spawning thread.
            if futures:
                wait(futures, timeout=self.cfg["terminate_grace_s"])
            try:
                self.close()
            except BaseException as e:
                original = original or e
            finally:
                pool.shutdown(wait=True, cancel_futures=True)
            try:
                identity.guard(self.cfg, self.store.manifest, self.inputs)
                report = self.store.publish_views()
                if original is not None:
                    write(
                        self.store.root / "_internal/last_failure.json",
                        {"error": repr(original)[:8192]},
                        replace=True,
                    )
            except BaseException:
                raise
        return report, original
