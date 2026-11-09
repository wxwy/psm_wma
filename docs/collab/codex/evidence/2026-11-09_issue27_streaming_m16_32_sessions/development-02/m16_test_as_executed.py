"""Actual frozen streaming M16:32 native Sessions, Worker FD/IPC and Owner HTTP.

Wan/current Policy boundaries, generation and env.step are explicit CPU doubles.
Store/Runtime slots, leases, native batching, owner controls, signatures, Worker
processes/transport and cleanup are real. No GPU, real Sim or Episode/SR claim.
"""

import json
import struct
import threading
import time
from types import SimpleNamespace

import pytest

from cosmos_framework.evaluation.robocasa_v2.contract import STREAMING_SCHEDULE
from cosmos_framework.evaluation.robocasa_v2.store import read
from cosmos_framework.inference import robocasa_session_transactions_test as s
from cosmos_framework.inference.robocasa_feature_evidence import PolicyBoundary
from cosmos_framework.inference.robocasa_vae_client import LocalVAEClient, VAEIPCError
from cosmos_framework.inference.robocasa_vae_protocol import (
    Frame,
    RGB_BYTES,
    source_digest,
    verify_feature,
)
from cosmos_framework.simulation.robocasa.eval_utils import canonicalize_raw15_for_env
from cosmos_framework.simulation.robocasa.sim_shared_vae_client import (
    ScopedActorCompletionChannel,
)
from tools.v3.eval_v2_batch_tests.shared_vae_routing_test import info, rig_for
from tools.v3.eval_v2_batch_tests.shared_vae_test import IDENTITY

clock_kernel = s.clock_kernel


@pytest.mark.parametrize(
    "same_render", [False, True], ids=["two-render-workers", "one-shared-render-worker"]
)
def test_streaming_m16_32_frozen_sessions_worker_ipc_ack_end_and_fail_closed(
    tmp_path, same_render
):
    with rig_for(tmp_path, 2, 16, same_render, streaming=True) as rig:
        rt, sup = rig.runtime, rig.supervisor
        frozen = read(rt.store.root / "manifest.json")
        assert frozen == rt.store.manifest
        assert frozen["protocol"]["schedule"] == STREAMING_SCHEDULE
        assert frozen["execution"]["sims_per_gpu"] == 16
        assert len(frozen["tasks"]) == 18 and len(rt.workers) == 32 > len(
            frozen["tasks"]
        )
        assert rt.streaming and rt.capacity_profile == "streaming32"
        assert all(
            a.capacity_profile == "streaming32" and len(a.slot_ids) == 16
            for a in rig.actors.values()
        )
        clocks = {a.clock_domain for a in rig.actors.values()}
        assert len(clocks) == 1
        clock = clocks.pop()
        sessions = []
        episode_deadline = time.monotonic() + 60
        for i, worker in enumerate(rt.workers):
            gpu = rt.worker_gpus[worker]
            handle = sup.ensure(worker, info(clock))
            registration = s.registration(
                rt.slot_ids[worker],
                run_lease=rt.store.lease_id,
                manifest_digest=frozen["digest"],
                task=frozen["task_order"][i % 18],
                episode_index=i // 18,
            )
            lease = (
                rig.actors[gpu]
                .register(registration, rt.server_owners[f"GPU{gpu}"])
                .json()["lease"]
            )
            actor = SimpleNamespace(
                nonce=f"actor-{worker}",
                owned=SimpleNamespace(proc=SimpleNamespace(poll=lambda: None)),
            )
            rt.actors[worker] = actor
            rt.slot_generations[worker] = 1
            peer = sup.register_assignment(
                worker, actor, dict(lease=lease), episode_deadline
            )
            public = {k: v for k, v in lease.items() if k != "capability"}
            channel = ScopedActorCompletionChannel(
                peer["relay_socket"], peer["actor_capability"], public
            )
            client = LocalVAEClient(
                peer["worker_socket"],
                lease["session_id"],
                peer["worker_session_capability"],
            )
            sessions.append(
                SimpleNamespace(
                    index=i,
                    worker=worker,
                    gpu=gpu,
                    lease=lease,
                    public=public,
                    handle=handle,
                    peer=peer,
                    channel=channel,
                    client=client,
                    episode_ns=int(episode_deadline * 1e9),
                )
            )
        assert len({v.lease["session_id"] for v in sessions}) == 32
        assert len({v.lease["slot_id"] for v in sessions}) == 32
        assert len({v.lease["server_epoch"] for v in sessions}) == 2
        expected_workers = 1 if same_render else 2
        assert (
            len(sup.handles)
            == len(rt.commands)
            == len(rt.owned_processes)
            == expected_workers
        )
        assert len(sup.policies) == 2 and not rt.startup_budget.pending
        assert rt.cpu_measurements[-1]["rss_bytes"] > 0
        for gpu, owner in rig.owners.items():
            approved = {v.lease["session_id"] for v in sessions if v.gpu == gpu}
            assert set(owner._sessions) == approved and len(approved) == 16
        for handle in sup.handles.values():
            assert handle.proof["limits"] == dict(
                max_sessions=32 if same_render else 16,
                max_policy_epochs=2 if same_render else 1,
            )
            assert handle.proof["bmax"] == 1 and handle.proof["wait_ms"] == 0

        # All admitted preparations are released together. Both original native
        # Policy executors generate actual B8+B8, with Session-specific actions.
        release = threading.Event()
        blockers = [
            a._executor.submit(lambda: release.wait(5)) for a in rig.actors.values()
        ]
        try:
            for v in sessions:
                request = s.payload(v.lease)
                request["state"][0] = v.index / 64
                v.reply = s.submit(rig.actors[v.gpu], v.lease, request)
        finally:
            release.set()
        for blocked in blockers:
            assert blocked.result(5)
        for v in sessions:
            actor = rig.actors[v.gpu]
            result = s.wait_result(actor, v.lease, v.reply)
            v.body = result.json()
            assert v.body["action"][0][0] == v.index / 64
            assert v.body["native_batch"]["size"] == 8
            v.deadline = int(actor._tickets[v.body["request_key"]].deadline * 1e9)
            v.image0 = bytes([v.index]) * RGB_BYTES
            boundary = PolicyBoundary.create(
                lease=v.public,
                request_key=v.body["request_key"],
                chunk_id=v.body["request_key"],
                source_step=0,
                source_rgb_sha256=source_digest(v.image0),
                identity=IDENTITY,
                deadline_ns=v.deadline,
                clock_domain=clock,
                visual96=struct.pack("<96f", *([v.index / 64] * 96)),
            )
            rig.boundaries[v.gpu][(v.lease["session_id"], 0)] = boundary
            assert s.ack(actor, v.lease, result).json()["acknowledged"]
            assert (
                actor._result(
                    actor._lease(v.lease),
                    v.body["request_key"],
                    v.body["payload_sha256"],
                ).status
                == 200
            )
        assert all(sizes == [8, 8] for sizes in rig.batches.values())
        assert all(a.info()["batch_histogram"] == {8: 2} for a in rig.actors.values())
        assert all(a.info()["tickets"] == 0 for a in rig.actors.values())

        # Real scoped relay->Owner HTTP completions authorize the Worker; the
        # synthetic current boundary skips step0 and one real IPC frame tests1.
        for v in sessions:
            key = v.body["request_key"]
            args = (key, key, v.body["payload_sha256"], 0, 16, v.deadline)
            assert all(scope.active() for scope in sup.core.scopes.values())
            try:
                first = v.channel.chunk(*args)
            except VAEIPCError as error:
                raise AssertionError(
                    {"http_errors": rig.http_errors, "remote_type": error.remote_type}
                ) from error
            assert v.channel.chunk(*args) == first
            v.raw = struct.pack(
                "<15f", *canonicalize_raw15_for_env(v.body["action"][0], False)[1]
            )
            for step, image in [(0, v.image0), (1, bytes([v.index + 40]) * RGB_BYTES)]:
                completed = time.monotonic_ns()
                fields = (
                    key,
                    key,
                    step,
                    source_digest(image),
                    v.raw,
                    completed,
                    v.deadline,
                )
                receipt = v.channel.post_step(*fields)
                assert (
                    receipt["source_step"] == step
                    and v.channel.post_step(*fields) == receipt
                )
            v.frame = Frame.create(
                v.public,
                key,
                key,
                1,
                image,
                v.raw,
                IDENTITY,
                v.episode_ns,
                v.deadline,
                clock,
                replan_deadline_ns=v.deadline,
            )
            v.job = v.client.submit(v.frame, v.deadline)
            assert v.client.submit(v.frame, v.deadline) == v.job
        for v in sessions:
            while True:
                result = v.client.poll(v.job, v.deadline)
                if result["status"] != "pending":
                    break
                assert time.monotonic_ns() < v.deadline
                time.sleep(0.001)
            assert result["status"] == "ready"
            feature = verify_feature(
                result["feature"],
                v.handle.signing_key,
                expected_lease=v.public,
                expected_identity=IDENTITY,
                expected_worker_id=v.handle.public["worker_id"],
                expected_worker_epoch=v.handle.public["worker_epoch"],
                expected_key_id=v.handle.public["key_id"],
                expected_clock_domain=clock,
                now_ns=time.monotonic_ns(),
            )
            assert feature["header"]["source_step"] == 1
            assert feature["header"]["source_rgb_sha256"] == source_digest(v.frame.rgb)
            assert v.client.ack(v.job, v.deadline)["acknowledged"]
            assert v.client.ack(v.job, v.deadline)["acknowledged"]
        for handle in sup.handles.values():
            client = next(v.client for v in sessions if v.handle is handle)
            stats = client.info(time.monotonic_ns() + 3_000_000_000)
            assert stats["batch_histogram"] == {"1": 32 if same_render else 16}
            assert stats["items"] == 0

        # Wrong data capability, stale assignment and wrong Policy Server fail
        # before advancing any approved Session. No response is treated as success.
        a, b = sessions[0], sessions[-1]
        wrong = LocalVAEClient(
            a.peer["worker_socket"],
            a.lease["session_id"],
            b.peer["worker_session_capability"],
        )
        with pytest.raises(VAEIPCError):
            wrong.poll(a.job, a.deadline)
        stale = ScopedActorCompletionChannel(
            a.peer["relay_socket"],
            a.peer["actor_capability"],
            dict(a.public, generation=2),
        )
        with pytest.raises(VAEIPCError):
            stale.end(a.deadline)
        with pytest.raises(ValueError):
            rig.actors[b.gpu].end(a.lease)
        assert len(sup.core.scopes) == 32 and all(
            not scope.closed and scope.completed == 2
            for scope in sup.core.scopes.values()
        )
        assert all(len(owner._sessions) == 16 for owner in rig.owners.values())

        for i, v in enumerate(sessions):
            ended = v.channel.end(v.deadline)
            assert ended["acknowledged"] and ended["quiescent"]
            assert v.channel.end(v.deadline) == ended
            assert rig.actors[v.gpu].end(v.lease).json()["acknowledged"]
            if i == 0:
                assert sum(len(o._sessions) for o in rig.owners.values()) == 31
                assert all(h.owned.proc.poll() is None for h in sup.handles.values())
        assert all(not owner._sessions for owner in rig.owners.values())
        assert all(
            a.info()["tickets"] == a.info()["encoded_bytes"] == 0
            for a in rig.actors.values()
        )
        assert all(scope.closed for scope in sup.core.scopes.values())
        handles = list(sup.handles.values())
        assert not rt.startup_budget.pending and rig.external.poll() is None
        sup.close()
        sup.close()
        assert all(
            h.owned.proc.returncode == 0 and not h.socket_root.exists() for h in handles
        )
        assert not sup.relay_root.exists() and rig.external.poll() is None
        # Public proof only: no bootstrap, assignment capability or signing key.
        (tmp_path / "streaming_m16_evidence.json").write_text(
            json.dumps(
                dict(
                    schedule=frozen["protocol"]["schedule"],
                    manifest_digest=frozen["digest"],
                    execution=frozen["execution"],
                    servers=2,
                    sims_per_server=16,
                    total_sim_sessions=32,
                    capacity_profile=rt.capacity_profile,
                    render_gpu_count=expected_workers,
                    worker_count=len(handles),
                    session_ids=[v.lease["session_id"] for v in sessions],
                    policy_epochs=sorted({v.lease["server_epoch"] for v in sessions}),
                    native_batch_sizes=rig.batches,
                    worker_bvae=1,
                    worker_frame_count=32,
                    policy_response_acks=32,
                    worker_result_acks=32,
                    scoped_ends=32,
                    native_ends=32,
                    duplicate_replay_unchanged=True,
                    permission_fail_closed=True,
                    first_end_isolated=True,
                    worker_pids=[h.owned.proc.pid for h in handles],
                    worker_returncodes=[h.owned.proc.returncode for h in handles],
                    ipc_removed=True,
                    external_process_survived=True,
                    startup_reservations_released=True,
                    measured_owned_rss_bytes=max(
                        x["rss_bytes"] for x in rt.cpu_measurements
                    ),
                    clock_domain=clock,
                    kernel_clock_and_physical_gpu="explicit_cpu_doubles",
                    policy_current_boundary="synthetic_injected",
                    wan="synthetic_cpu",
                    real_sim=False,
                ),
                indent=2,
            )
        )
