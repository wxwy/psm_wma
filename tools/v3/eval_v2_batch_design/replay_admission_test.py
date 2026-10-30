"""B-D3: actual public submit -> execute/replay -> ACK admission boundaries."""

from dataclasses import replace

import pytest

from tools.v3.eval_v2_batch_design.protocol_model import (
    Lease,
    ProtocolModel,
    Request,
    Response,
)


class Vector:
    def __init__(self):
        self.calls = 0

    def __call__(self, prepared):
        self.calls += 1
        return tuple(
            Response(p.request.key, (float(p.request.frontier),)) for p in prepared
        )


def setup():
    model, vector = ProtocolModel(2), Vector()
    leases = tuple(
        Lease(model.epoch, f"slot{i}", 1, f"session{i}", f"episode{i}")
        for i in range(2)
    )
    for lease in leases:
        model.open(lease)
    r0, other = (Request(lease, 0) for lease in leases)
    model.submit(r0, size=3)
    model.submit(other, deadline=10, size=5)
    replies = model.execute((r0, other), vector)
    model.acknowledge(r0)
    return model, vector, r0, other, replies


def assert_other_unchanged(model, other, ticket, state, response):
    assert model.registry.ticket(other) is ticket
    assert ticket.size == 5 and ticket.state == "COMMITTED" and ticket.quiescent
    assert model.bundle.states[other.lease.session] is state
    assert model.bundle.responses[other.key] is response


def test_ack_then_late_submit_replay_ack_then_next_frontier_has_no_ghost_ticket():
    model, vector, r0, other, replies = setup()
    original = model.bundle
    other_ticket = model.registry.ticket(other)
    assert model.registry.bytes_used == 5 and r0.key not in model.registry.tickets
    # A retransmitted POST arrives after the original Ticket was fully released.
    assert model.submit(r0, now=100, deadline=101, size=20) is replies[0]
    assert model.registry.tickets == {other.key: other_ticket}
    assert model.registry.bytes_used == 5 and model.bundle is original
    assert model.execute((r0,), vector) == (replies[0],)
    assert model.acknowledge(r0) is True
    assert vector.calls == 1 and model.registry.bytes_used == 5
    r1 = replace(r0, frontier=1, evidence=(7,))
    ticket = model.submit(r1, size=4)
    assert ticket.request == r1 and ticket.state == "QUEUED"
    assert model.registry.bytes_used == 9
    # Neither late R0 POST nor a second R0 ACK may release/change R1.
    assert model.submit(r0) is replies[0]
    assert model.acknowledge(r0) is True
    assert model.registry.ticket(r1) is ticket and model.registry.bytes_used == 9
    assert model.execute((r1,), vector)[0].key == r1.key
    model.acknowledge(r1)
    assert vector.calls == 2 and model.registry.bytes_used == 5
    assert_other_unchanged(
        model,
        other,
        other_ticket,
        original.states[other.lease.session],
        original.responses[other.key],
    )


@pytest.mark.parametrize("mutation", ["noise", "evidence", "compatibility"])
@pytest.mark.parametrize("next_queued", [False, True])
def test_changed_payload_after_ack_rejected_before_any_allocation(
    mutation, next_queued, monkeypatch
):
    model, vector, r0, other, _ = setup()
    if next_queued:
        model.submit(replace(r0, frontier=1, evidence=(7,)), size=4)
    changed = {
        "noise": replace(r0, noise_seed=99),
        "evidence": replace(r0, evidence=(1,)),
        "compatibility": replace(r0, compatibility="other-profile"),
    }[mutation]
    original = model.bundle
    tickets = dict(model.registry.tickets)
    allocations = []
    allocate = model.registry.submit

    def spy(*args, **kwargs):
        allocations.append(args[0])
        return allocate(*args, **kwargs)

    monkeypatch.setattr(model.registry, "submit", spy)
    with pytest.raises(ValueError, match="different payload"):
        model.submit(changed)
    assert not allocations and model.registry.tickets == tickets
    assert model.registry.bytes_used == (9 if next_queued else 5)
    assert model.bundle is original and vector.calls == 1
    assert other.key in model.registry.tickets


@pytest.mark.parametrize("mutated", [False, True])
@pytest.mark.parametrize("current_acked", [False, True])
def test_evicted_frontier_cannot_allocate_or_block_current_frontier(
    mutated, current_acked, monkeypatch
):
    model, vector, r0, other, _ = setup()
    r1 = replace(r0, frontier=1, evidence=(7,))
    model.submit(r1, size=4)
    model.execute((r1,), vector)  # Evicts R0, while R1 still owns delivery credit.
    if current_acked:
        model.acknowledge(r1)
    assert r0.key not in model.bundle.responses
    old = replace(r0, noise_seed=99) if mutated else r0
    original = model.bundle
    tickets = dict(model.registry.tickets)
    allocations = []
    allocate = model.registry.submit

    def spy(*args, **kwargs):
        allocations.append(args[0])
        return allocate(*args, **kwargs)

    monkeypatch.setattr(model.registry, "submit", spy)
    with pytest.raises(ValueError, match="stale|evicted"):
        model.submit(old)
    assert not allocations and model.registry.tickets == tickets
    assert model.registry.bytes_used == (5 if current_acked else 9)
    assert model.bundle is original
    # A stale ACK outside the bounded replay window also cannot free R1.
    with pytest.raises(ValueError, match="no committed response"):
        model.acknowledge(old)
    assert model.registry.tickets == tickets
    model.acknowledge(r1)
    r2 = replace(r1, frontier=2, evidence=(8,))
    fresh = model.submit(r2, size=4)
    assert fresh.request == r2 and model.registry.bytes_used == 9
    assert vector.calls == 2 and other.key in model.registry.tickets


@pytest.mark.parametrize("phase", ["QUEUED", "SEALED", "GENERATING", "COMMITTED"])
def test_unresolved_duplicate_still_joins_original_ticket_without_renewal(phase):
    model, vector = ProtocolModel(1), Vector()
    lease = Lease(model.epoch, "slot", 1, "session", "episode")
    model.open(lease)
    request = Request(lease, 0)
    ticket = model.submit(request, deadline=5, size=7)
    observed = []

    def check():
        assert model.submit(request, now=1, deadline=100, size=30) is ticket
        assert (ticket.arrived, ticket.deadline, ticket.size) == (0, 5, 7)
        assert model.registry.bytes_used == 7 and len(model.registry.tickets) == 1
        observed.append(phase)

    if phase == "QUEUED":
        check()
    else:

        def stage(name):
            if name == phase:
                check()

        model.execute((request,), vector, on_stage=stage)
    assert observed == [phase]


def test_released_replay_cannot_bypass_closed_or_restarted_lease():
    model, vector, r0, _, _ = setup()
    model.request_end(r0.lease)
    with pytest.raises(ValueError, match="stale"):
        model.submit(r0)
    restarted = ProtocolModel(2, epoch="server-2")
    with pytest.raises(ValueError, match="stale"):
        restarted.submit(r0)
    assert vector.calls == 1 and restarted.registry.bytes_used == 0
