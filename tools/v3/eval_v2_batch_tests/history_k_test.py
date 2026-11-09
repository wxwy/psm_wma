"""Issue28 frozen K and actual Root/daemon/Owner HTTP/Unix IPC CPU contracts.

Policy generation/current boundary/env/device/kernel are explicit synthetic
boundaries. Full CPU Local updates are exercised by the Child tests separately.
"""

import copy
import json
import struct
import threading
import time
from types import SimpleNamespace

import pytest
import yaml

from cosmos_framework.evaluation.robocasa_v2.contract import (
    build_manifest,
    validate_manifest,
)
from cosmos_framework.evaluation.robocasa_v2.store import Store
from cosmos_framework.inference import robocasa_session_transactions_test as s
from cosmos_framework.inference.robocasa_feature_evidence import PolicyBoundary
from cosmos_framework.inference.robocasa_vae_client import LocalVAEClient, VAEIPCError
from cosmos_framework.inference.robocasa_vae_protocol import (
    Frame,
    RGB_BYTES,
    source_digest,
)
from cosmos_framework.simulation.robocasa.eval_utils import canonicalize_raw15_for_env
from cosmos_framework.simulation.robocasa.sim_shared_vae_client import (
    ScopedActorCompletionChannel,
)
from robocasa_eval_v2 import shared_vae
from robocasa_eval_v2.cli import main
from robocasa_eval_v2.config import execution, resolve
from robocasa_eval_v2.runtime import Runtime
from tools.v3.eval_v2_batch_tests.shared_vae_routing_test import info, rig_for
from tools.v3.eval_v2_batch_tests.shared_vae_test import IDENTITY, profile_config
from tools.v3.eval_v2_batch_tests.shared_vae_topology_test import topology
from tools.v3.eval_v2_production_tests.contract_test import manifest
from tools.v3.eval_v2_production_tests.entry_test import config

clock_kernel = s.clock_kernel


def frozen(cfg):
    old = manifest(episodes=2)
    return build_manifest(
        tasks=old["tasks"],
        episodes=2,
        seed=old["seed"],
        horizons=old["horizons"],
        experiment=old["experiment"],
        execution=execution(cfg),
        local_memory="required",
    )


@pytest.mark.parametrize("k", [1, 2, 4, 8, 16])
def test_public_CLI_frozen_K_and_unchanged_M_B_resume_rejection(tmp_path, capsys, k):
    path, inputs = config(tmp_path)
    cfg = {**profile_config(tmp_path), **inputs, "local_ttt_history_k": k}
    path.write_text(yaml.safe_dump(cfg))
    _, resolved = resolve(
        ["fresh", "--config", str(path), "--local-ttt-history-k", str(k)]
    )
    assert resolved["local_ttt_history_k"] == k
    m = frozen(resolved)
    assert validate_manifest(m) == m
    if k == 16:
        assert "local_ttt_history_k" not in m["execution"]
        del resolved["local_ttt_history_k"]
        assert frozen(resolved) == m  # Default dense identity is byte-equivalent.
    else:
        assert m["execution"]["local_ttt_history_k"] == k
    store = Store(inputs["output_dir"], m)
    store.create()
    assert main(["dry-run", "--config", str(path)]) == 0
    capsys.readouterr()
    changed = copy.deepcopy(resolved)
    changed["local_ttt_history_k"] = 1 if k != 1 else 2
    with pytest.raises(ValueError, match="frozen manifest"):
        Runtime(store, changed, {}, {})
    path.write_text(yaml.safe_dump(changed))
    with pytest.raises(ValueError, match="frozen Run"):
        main(["dry-run", "--config", str(path)])
    for field in ("sims_per_gpu", "max_infer_batch_size"):
        changed = copy.deepcopy(resolved)
        changed[field] = 2
        with pytest.raises(ValueError, match="frozen manifest"):
            Runtime(store, changed, {}, {})


@pytest.mark.parametrize("k", [1, 2, 4, 8, 16])
@pytest.mark.parametrize("servers,sims", [(1, 1), (1, 8), (2, 16), (3, 5)])
def test_sparse_K_composes_with_generic_topology_not_a_config_whitelist(
    tmp_path, k, servers, sims
):
    cfg = topology(tmp_path, servers, sims, 8, streaming=sims > 8)
    cfg["local_ttt_history_k"] = k
    shared_vae.validate_profile(cfg)
    assert validate_manifest(frozen(cfg))["execution"] == execution(cfg)


@pytest.mark.parametrize("value", [0, 3, 17, True, 4.0, "4"])
def test_public_CLI_rejects_bad_K_before_fresh_namespace(tmp_path, value):
    path, inputs = config(tmp_path)
    cfg = {**profile_config(tmp_path), **inputs, "local_ttt_history_k": value}
    path.write_text(yaml.safe_dump(cfg))
    with pytest.raises(ValueError):
        resolve(["fresh", "--config", str(path)])
    assert not (tmp_path / "out").exists()


@pytest.mark.parametrize("arm", ["A", "B"])
def test_sparse_K_never_implicitly_enables_NoTTT_or_legacy_history(tmp_path, arm):
    cfg = profile_config(tmp_path, arm)
    assert "local_ttt_history_k" not in execution(cfg)
    cfg["local_ttt_history_k"] = 4
    with pytest.raises(ValueError, match="shared VAE Local"):
        shared_vae.validate_profile(cfg)


@pytest.mark.parametrize(
    "k,servers,sims", [(k, 1, 2) for k in (1, 2, 4, 8, 16)] + [(4, 2, 16)]
)
def test_sparse_sessions_real_FD_daemon_owner_HTTP_IPC_and_owned_cleanup(
    tmp_path, k, servers, sims
):
    with rig_for(tmp_path, servers, sims, True, streaming=sims > 8, history_k=k) as rig:
        rt, sup = rig.runtime, rig.supervisor
        sessions = []
        end_s = time.monotonic() + 90
        clock = next(iter(rig.actors.values())).clock_domain
        for i, worker in enumerate(rt.workers):
            gpu, actor = rt.worker_gpus[worker], rig.actors[rt.worker_gpus[worker]]
            handle = sup.ensure(worker, info(clock, k))
            lease = actor.register(
                s.registration(
                    rt.slot_ids[worker],
                    run_lease=rt.store.lease_id,
                    manifest_digest=rt.store.manifest["digest"],
                ),
                rt.server_owners[f"GPU{gpu}"],
            ).json()["lease"]
            sim = SimpleNamespace(
                nonce=f"sim-{i}",
                owned=SimpleNamespace(proc=SimpleNamespace(poll=lambda: None)),
            )
            rt.actors[worker], rt.slot_generations[worker] = sim, 1
            peer = sup.register_assignment(worker, sim, dict(lease=lease), end_s)
            public = {n: value for n, value in lease.items() if n != "capability"}
            sessions.append(
                SimpleNamespace(
                    index=i,
                    worker=worker,
                    gpu=gpu,
                    actor=actor,
                    lease=lease,
                    public=public,
                    handle=handle,
                    peer=peer,
                    channel=ScopedActorCompletionChannel(
                        peer["relay_socket"], peer["actor_capability"], public
                    ),
                    client=LocalVAEClient(
                        peer["worker_socket"],
                        lease["session_id"],
                        peer["worker_session_capability"],
                    ),
                )
            )
        assert len({v.lease["session_id"] for v in sessions}) == servers * sims
        assert (
            len(sup.handles) == 1
        )  # One actual CPU Worker process shared by every Session.
        handle = sessions[0].handle
        assert handle.proof.get("local_ttt_history_k", 16) == k
        assert handle.proof["bmax"] == 1 and handle.proof["wait_ms"] == 0
        if k != 16:
            with pytest.raises(ValueError, match="history K"):
                sup.ensure(sessions[0].worker, info(clock, 16))
        release = threading.Event()
        gates = [
            a._executor.submit(lambda: release.wait(10)) for a in rig.actors.values()
        ]
        try:
            for v in sessions:
                payload = s.payload(v.lease)
                payload["state"][0] = v.index / 64
                v.pending = s.submit(v.actor, v.lease, payload)
        finally:
            release.set()
        for gate in gates:
            assert gate.result(10)
        for v in sessions:
            response = s.wait_result(v.actor, v.lease, v.pending)
            v.result = response.json()
            v.deadline = int(v.actor._tickets[v.result["request_key"]].deadline * 1e9)
            key = v.result["request_key"]
            image = bytes([v.index]) * RGB_BYTES
            boundary = PolicyBoundary.create(
                lease=v.public,
                request_key=key,
                chunk_id=key,
                source_step=0,
                source_rgb_sha256=source_digest(image),
                identity=IDENTITY,
                deadline_ns=v.deadline,
                clock_domain=clock,
                visual96=struct.pack("<96f", *([v.index / 64] * 96)),
            )
            rig.boundaries[v.gpu][(v.lease["session_id"], 0)] = boundary
            s.ack(v.actor, v.lease, response)
            v.raw = struct.pack(
                "<15f", *canonicalize_raw15_for_env(v.result["action"][0], False)[1]
            )
            v.channel.chunk(key, key, v.result["payload_sha256"], 0, 16, v.deadline)
            v.rows, v.frames = [], []
            for step in range(16):
                selected = step % (16 // k) == 0
                rgb = bytes([v.index + step]) * RGB_BYTES if selected else None
                fields = (
                    key,
                    key,
                    step,
                    source_digest(rgb) if selected else None,
                    v.raw,
                    time.monotonic_ns(),
                    v.deadline,
                )
                receipt = v.channel.post_step(*fields)
                assert (
                    v.channel.post_step(*fields) == receipt
                )  # Scoped replay does not reauthorize work.
                v.rows.append(
                    dict(source_step=step, post_step_receipt=receipt, feature=None)
                )
                if selected and step:
                    v.frames.append(
                        Frame.create(
                            v.public,
                            key,
                            key,
                            step,
                            rgb,
                            v.raw,
                            IDENTITY,
                            int(end_s * 1e9),
                            v.deadline,
                            clock,
                            replan_deadline_ns=v.deadline,
                        )
                    )
            # All skip completions arrived before the first selected async Frame.
            for frame in v.frames:
                job = v.client.submit(frame, v.deadline)
                assert v.client.submit(frame, v.deadline) == job
                while True:
                    result = v.client.poll(job, v.deadline)
                    if result["status"] != "pending":
                        break
                    assert time.monotonic_ns() < v.deadline
                    time.sleep(0.001)
                assert result["status"] == "ready"
                v.rows[frame.header["source_step"]]["feature"] = result["feature"]
                assert v.client.ack(job, v.deadline)["acknowledged"]
            payload = dict(
                session_id=v.public["session_id"],
                episode_id=v.public["episode_id"],
                consumer_step=16,
                reset=False,
                evidence=v.rows,
            )
            if k != 16:
                from cosmos_framework.inference.robocasa_feature_evidence import (
                    SPARSE_EVIDENCE_FORMAT,
                    SPARSE_EVIDENCE_VERSION,
                )

                payload.update(
                    evidence_version=SPARSE_EVIDENCE_VERSION,
                    evidence_format=SPARSE_EVIDENCE_FORMAT,
                    local_ttt_history_k=k,
                )
            batch = rig.owners[v.gpu].admit(
                payload,
                lease=v.public,
                deadline_ns=v.deadline,
                clock_domain=clock,
                previous_step=0,
            )
            assert (
                batch.source_steps == tuple(range(0, 16, 16 // k))
                and len(batch.raw15) == k
            )
            assert (
                len(rig.owners[v.gpu]._sessions[v.lease["session_id"]].completed) == 16
            )
        stats = sessions[0].client.info(time.monotonic_ns() + 3_000_000_000)
        assert stats["batch_histogram"] == (
            {"1": servers * sims * (k - 1)} if k > 1 else {}
        )
        assert stats["items"] == stats["bytes"] == 0
        if servers == 2:
            assert rig.batches == {gpu: [8, 8] for gpu in rig.batches}
        a, b = sessions[:2]
        wrong = LocalVAEClient(
            a.peer["worker_socket"],
            a.lease["session_id"],
            b.peer["worker_session_capability"],
        )
        with pytest.raises(VAEIPCError):
            wrong.poll(
                "f" * 64, a.deadline
            )  # Session data capabilities cannot access another Session.
        for i, v in enumerate(sessions):
            assert v.channel.end(v.deadline)["quiescent"]
            assert v.actor.end(v.lease).json()["acknowledged"]
            if i == 0:
                assert (
                    sum(len(o._sessions) for o in rig.owners.values())
                    == servers * sims - 1
                )
                assert handle.owned.proc.poll() is None and rig.external.poll() is None
        assert not rig.http_errors and not rt.startup_budget.pending
        sup.close()
        assert (
            handle.owned.proc.returncode == 0
            and not handle.socket_root.exists()
            and not sup.relay_root.exists()
        )
        assert rig.external.poll() is None
        (tmp_path / "sparse_os_behavior.json").write_text(
            json.dumps(
                dict(
                    k=k,
                    servers=servers,
                    sims_per_server=sims,
                    sessions=servers * sims,
                    completed_steps=servers * sims * 16,
                    history_encode1=servers * sims * (k - 1),
                    worker_returncode=0,
                    external_survived=True,
                    policy_batch_histograms=rig.batches,
                    real_model=False,
                    real_env=False,
                ),
                indent=2,
            )
        )
