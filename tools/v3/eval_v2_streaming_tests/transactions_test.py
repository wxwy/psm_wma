"""32 Sessions through the public client/dispatcher and native H16 B32 carriers."""

import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
import torch
from torch import nn
from cosmos_framework.inference.robocasa_batch_transactions import (
    BatchedSessionTransactions,
)
from cosmos_framework.inference.robocasa_dual_mode_test import forbidden, no_ttt_payload
from cosmos_framework.inference.robocasa_local_memory_policy import (
    RoboCasaLocalMemoryPolicyAdapter,
)
from cosmos_framework.inference.robocasa_session_transactions_test import (
    make_adapter,
    payload,
    registration,
    clock_kernel as clock_kernel,  # noqa: F401
)
from cosmos_framework.inference.robocasa_transaction_client import (
    TransactionPolicyClient,
)
from cosmos_framework.scripts.robocasa_transactions_b1_test import (
    DirectTransport,
    service,
    server,
)


@pytest.mark.parametrize("mode", ["off", "required"])
@pytest.mark.parametrize("cap", [8, 16, 32])
def test_32_sessions_native_shapes_routing_replay_and_real_fast_state(
    monkeypatch, mode, cap
):
    obj = service(monkeypatch)
    if mode == "required":
        obj.local_memory_adapter, obj.model = make_adapter(32)
    else:
        obj.model = nn.Module()
        obj.model.net = nn.Module()
        obj.local_memory_adapter = RoboCasaLocalMemoryPolicyAdapter(
            obj, mode="off", decode_image=forbidden, max_sessions=32
        )
        for name in (
            "prepare",
            "commit",
            "commit_many",
            "abort",
            "reset",
            "status",
            "prefixes",
        ):
            monkeypatch.setattr(obj.local_memory_adapter, name, forbidden)
    calls = []

    def generate(batch, **kwargs):
        n = len(batch["prompt"])
        prefixes = kwargs.get("_local_memory_prefixes")
        assert len(batch["action"]) == len(batch["sequence_plan"]) == n
        assert all(a[0].shape == (17, 64) for a in batch["action"])
        assert (prefixes is not None) == (mode == "required")
        calls.append(
            {
                "size": n,
                "hot": [] if prefixes is None else [p is not None for p in prefixes],
            }
        )
        return {
            "action": [
                torch.full((1, 17, 64), float(batch["action"][i][0][0, 0]))
                for i in range(n)
            ],
            "vision": [torch.zeros(1, 3, 1, 8, 8) for _ in range(n)],
        }

    obj.model.generate_samples_from_batch = generate
    actor = BatchedSessionTransactions(
        obj.local_memory_adapter,
        obj._transaction_batch,
        lambda: None,
        owner_token="cpu-owner",
        run_lease="run",
        manifest_digest="a" * 64,
        slot_ids=tuple(f"slot{i}" for i in range(32)),
        capacity_profile="streaming32",
        max_batch_size=cap,
        batch_wait_ms=1000,
        timeout_s=30,
        model_lock=obj._lock,
    )
    obj.transactions = actor
    clients = [
        TransactionPolicyClient(
            "http://cpu",
            timeout_s=30,
            transport=DirectTransport(obj),
            batch_profile=True,
            max_batch_size=cap,
            local_memory_mode=mode,
            capacity_profile="streaming32",
        )
        for _ in range(32)
    ]
    try:
        leases = [
            client.register(registration(f"slot{i}"), "cpu-owner")
            for i, client in enumerate(clients)
        ]
        assert len({a["session_id"] for a in leases}) == 32
        for wave in range(2):
            barrier = threading.Barrier(32)
            requests = [
                no_ttt_payload(a, wave)
                if mode == "off"
                else payload(a, wave * 2, 0, i + 1)
                for i, a in enumerate(leases)
            ]
            for i, request in enumerate(requests):
                request["state"][0] = i * 0.001

            def predict(i):
                barrier.wait(10)
                return clients[i].predict(requests[i])

            with ThreadPoolExecutor(32) as pool:
                results = list(pool.map(predict, range(32)))
            for i, result in enumerate(results):
                assert result["assignment"]["session_id"] == leases[i]["session_id"]
                assert result["native_batch"]["size"] <= cap
                assert len(result["action"]) == 16 and len(result["action"][0]) == 15
                assert result["action"][0][0] == pytest.approx((i * 0.001 + 1) / 2)
            if wave == 0:
                before = len(calls)
                assert clients[0].predict(requests[0]) == results[0]
                assert (
                    len(calls) == before
                )  # Post-ACK replay never runs native generation twice.
        assert all(1 <= c["size"] <= cap for c in calls)
        if cap == 32:
            assert any(c["size"] == 32 for c in calls)
        if mode == "required":
            fast = obj.local_memory_adapter.snapshot.fast
            assert len(fast) == 32 and len({id(v.state) for v in fast.values()}) == 32
            assert any(any(c["hot"]) for c in calls)
            others = {
                sid: state
                for sid, state in fast.items()
                if sid != leases[0]["session_id"]
            }
            clients[0].end()
            assert all(
                obj.local_memory_adapter.snapshot.fast[sid] is state
                for sid, state in others.items()
            )
        else:
            assert obj.local_memory_adapter.memory is None
        for client in clients:
            if client.lease is not None:
                client.end()
        info = actor.info()
        assert info["sessions"] == info["tickets"] == info["encoded_bytes"] == 0
        assert info["requests_finished"] == 64
        assert info["queue_wait_p95_ms"] >= info["queue_wait_p50_ms"] >= 0
        assert info["batch_generate_ms"]["count"] == len(calls)
        with pytest.raises((ValueError, RuntimeError)):
            actor.register(registration("slot0", generation=1), "cpu-owner")
    finally:
        assert actor.close(timeout_s=5)
        actor._executor.shutdown(wait=True)


def test_server_preflight_explicit_32_capacity_and_client_rejects_bad_batch_or_ack(
    tmp_path,
):
    path = tmp_path / "owner"
    path.write_text("cpu-private-owner")
    path.chmod(0o600)
    args = SimpleNamespace(
        transaction_profile="batch",
        transaction_capacity_profile="streaming32",
        transaction_slot_ids=",".join(f"s{i}" for i in range(32)),
        transaction_slot_id=None,
        transaction_max_batch_size=32,
        transaction_batch_wait_ms=20,
        local_memory_mode="off",
        local_memory_max_sessions=32,
        action_chunk_size=16,
        transaction_owner_token_file=path,
        transaction_run_lease="run",
        transaction_manifest_digest="a" * 64,
    )
    actual = server._transaction_options(args)
    assert (
        actual["capacity_profile"] == "streaming32"
        and len(actual["slot_ids"]) == actual["max_batch_size"] == 32
    )
    args.transaction_capacity_profile = "legacy8"
    with pytest.raises(ValueError):
        server._transaction_options(args)
    client = TransactionPolicyClient(
        "http://cpu",
        batch_profile=True,
        max_batch_size=32,
        capacity_profile="streaming32",
    )
    assert client._batch_valid({"id": "a" * 32, "size": 32, "index": 31})
    assert not client._batch_valid({"id": "a" * 32, "size": 33, "index": 0})
    with pytest.raises(ValueError, match="capacity profile"):
        client.bind_assignment(
            {
                "prediction_clock_domain": client.clock_domain,
                "capacity_profile": "legacy8",
            }
        )


def test_coordinator_cancellation_stops_registration_retry_immediately():
    import requests

    cancelled = threading.Event()
    calls = []

    class Lost:
        def request(self, *args, **kwargs):
            calls.append(kwargs["timeout"])
            cancelled.set()
            raise requests.ConnectionError("owned Server stopped during registration")

    client = TransactionPolicyClient(
        "http://cpu", transport=Lost(), cancelled=cancelled.is_set
    )
    with pytest.raises(RuntimeError, match="coordinator cancelled"):
        client.register(registration(), "cpu-owner")
    assert len(calls) == 1 and client.lease is None
