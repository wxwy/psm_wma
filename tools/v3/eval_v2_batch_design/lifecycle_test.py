"""Integrated symbolic Queue -> model executor -> End / response credit witnesses."""

from dataclasses import replace

import pytest

from tools.v3.eval_v2_batch_design.protocol_model import (
    BatchQueue,
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


def setup(n=2, *, registry=None):
    model = ProtocolModel(n, registry=registry)
    leases = tuple(
        Lease(model.epoch, f"slot{i}", 1, f"session{i}", f"episode{i}")
        for i in range(n)
    )
    for lease in leases:
        model.open(lease)
    return model, Vector(), leases, tuple(Request(lease, 0) for lease in leases)


def warm(model, vector, requests):
    model.execute(requests, vector)
    for request in requests:
        model.acknowledge(request)
    hot = tuple(
        replace(r, frontier=1, evidence=(i + 1,)) for i, r in enumerate(requests)
    )
    model.execute(hot, vector)
    for request in hot:
        model.acknowledge(request)
    return tuple(
        replace(r, frontier=2, evidence=(i + 3,)) for i, r in enumerate(requests)
    )


@pytest.mark.parametrize(
    "phase",
    [
        "SEALED",
        "PREPARED_ITEM_0",
        "PREPARED_ITEM_1",
        "PREPARED",
        "GENERATING",
        "inside_generation",
        "GENERATED",
        "VALIDATED",
        "before_publish",
    ],
)
def test_end_never_acks_owned_batch_before_abort_and_quiescence(phase):
    model, vector, leases, requests = setup()
    requests = warm(model, vector, requests)
    original = model.bundle
    events = []

    def end_during(stage):
        if stage != phase:
            return
        owned = model.registry.ticket(requests[0])
        reply = model.request_end(leases[0])
        events.append(
            (stage, reply.acknowledged, owned.quiescent, model.registry.bytes_used)
        )
        assert not reply and not model.poll_end(leases[0])
        assert owned.state not in ("ABORTED", "COMMITTED")
        assert model.registry.ticket(requests[1]).request == requests[1]
        assert model.bundle is original
        assert model.submit(requests[0]) is owned  # Duplicate attaches while draining.
        with pytest.raises(ValueError, match="over-capacity|stale"):
            model.open(replace(leases[0], generation=2, session="new", episode="new"))
        with pytest.raises(ValueError, match="closing"):
            model.submit(replace(requests[0], frontier=3))
        with pytest.raises(ValueError, match="quiescence"):
            model.registry.release(owned, "aborted")

    def generate(prepared):
        end_during("inside_generation")
        return vector(prepared)

    with pytest.raises(ValueError, match="cancellation"):
        model.execute(
            requests,
            generate,
            lambda: end_during("before_publish"),
            on_stage=end_during,
        )
    assert events == [(phase, False, False, 2)]
    assert model.bundle is original  # Fast, visual, frontier and response all intact.
    assert not model.registry.tickets and model.registry.bytes_used == 0
    assert model.active[leases[0].slot] == leases[0]  # Abort alone is not End ACK.
    assert model.poll_end(leases[0]).acknowledged is True
    assert model.bundle.states[leases[1].session] is original.states[leases[1].session]
    expected = {
        key: value
        for key, value in original.responses.items()
        if value[0].lease.session == leases[1].session
    }
    assert model.bundle.responses == expected


def test_end_of_queued_ticket_needs_real_owner_drain_without_generation():
    model, vector, leases, requests = setup()
    ticket = model.submit(requests[0], size=7)
    assert model.request_end(leases[0]).acknowledged is False
    assert ticket.state == "QUEUED" and ticket.cancel_requested
    assert model.registry.bytes_used == 7
    assert model.poll_end(leases[0]).acknowledged is False
    model.drain_queued_cancellations()
    assert ticket.state == "ABORTED" and ticket.released and ticket.quiescent
    assert model.registry.bytes_used == 0 and vector.calls == 0
    assert model.poll_end(leases[0]).acknowledged is True


def test_popped_ticket_end_before_prepare_uses_same_registry():
    queue = BatchQueue(slots=2, batch=2, byte_cap=8)
    model, vector, leases, requests = setup(registry=queue)
    tickets = tuple(model.submit(r, size=3) for r in requests)
    assert queue.pop(0) == requests
    assert not queue.rows and len(queue.tickets) == 2 and queue.bytes_used == 6
    assert model.request_end(leases[0]).acknowledged is False
    assert model.registry is queue
    assert queue.submit(requests[0], 0.1, 100, size=1) is tickets[0]
    with pytest.raises(ValueError, match="one pending"):
        queue.submit(replace(requests[0], frontier=1, evidence=(1,)), 0.1, 1)
    with pytest.raises(ValueError, match="cancellation"):
        model.execute(requests, vector)
    assert vector.calls == 0 and queue.bytes_used == 0
    assert model.poll_end(leases[0]).acknowledged is True


def test_cancel_only_is_never_cleanup_ack_or_state_deletion():
    model, vector, leases, requests = setup()
    original = model.bundle
    assert model.request_cancel(leases[0]) is None
    assert model.bundle is original and model.active[leases[0].slot] == leases[0]
    with pytest.raises(ValueError, match="end was not requested"):
        model.poll_end(leases[0])
    with pytest.raises(ValueError, match="cancelled"):
        model.execute(requests, vector)
    assert vector.calls == 0 and model.registry.bytes_used == 0
    assert model.request_end(leases[0]).acknowledged is True


def test_inflight_deadline_cannot_manufacture_quiescence_or_end_ack():
    model, _, leases, requests = setup()
    observations = []

    def blocked_generation(prepared):
        with pytest.raises(TimeoutError):
            model.registry.pop(1)
        assert model.request_end(leases[0]).acknowledged is False
        for _ in range(3):
            observations.append(model.poll_end(leases[0]).acknowledged)
            assert model.registry.bytes_used == 2
            assert not model.registry.ticket(requests[0]).quiescent
        with pytest.raises(ValueError, match="quiescence"):
            model.registry.release(model.registry.ticket(requests[0]), "aborted")
        raise RuntimeError("fake executor finally unwinds; timeout was not a drain")

    with pytest.raises(RuntimeError, match="finally unwinds"):
        model.execute(requests, blocked_generation)
    assert observations == [False, False, False]
    assert model.registry.bytes_used == 0
    assert model.poll_end(leases[0]).acknowledged is True


def test_end_after_commit_defers_then_discards_own_reply_without_touching_cobatch():
    model, vector, leases, requests = setup()
    observations = []

    def after_commit(stage):
        if stage == "COMMITTED":
            observations.append(model.request_end(leases[0]).acknowledged)
            assert model.registry.bytes_used == 2
            assert all(
                t.state == "COMMITTED" and not t.quiescent
                for t in model.registry.tickets.values()
            )
            with pytest.raises(ValueError, match="quiescent"):
                model.deliver(requests[1])

    replies = model.execute(requests, vector, on_stage=after_commit)
    assert observations == [False] and vector.calls == 1
    b = model.bundle.states[leases[1].session]
    b_reply = model.bundle.responses[requests[1].key]
    assert model.registry.bytes_used == 2  # Commit is NOT delivery ACK.
    assert model.poll_end(leases[0]).acknowledged is True
    assert model.registry.bytes_used == 1
    assert model.bundle.states[leases[1].session] is b
    assert model.bundle.responses[requests[1].key] is b_reply
    with pytest.raises(ValueError, match="stale"):
        model.deliver(requests[0])
    assert model.deliver(requests[1]) is replies[1]
    assert model.acknowledge(requests[1]) is True
    assert model.registry.bytes_used == 0


def test_committed_response_or_delivery_ack_loss_keeps_one_ticket_and_never_regenerates():
    model, vector, _, requests = setup()
    replies = model.execute(requests, vector)
    ticket = model.registry.ticket(requests[0])
    assert model.submit(requests[0], now=0.1, deadline=100, size=10) is ticket
    assert ticket.size == 1 and ticket.deadline == 1
    assert model.execute(requests, vector) == replies
    assert model.deliver(requests[0]) is replies[0]
    assert vector.calls == 1 and model.registry.bytes_used == 2
    with pytest.raises(ValueError, match="one pending"):
        model.submit(replace(requests[0], frontier=1, evidence=(1,)))
    assert model.acknowledge(requests[0]) is True
    assert model.acknowledge(requests[0]) is True
    assert model.registry.bytes_used == 1
    assert model.submit(replace(requests[0], frontier=1, evidence=(1,))) is not ticket
    assert model.registry.bytes_used == 2
    assert model.registry.release(ticket, "delivered") is False
    assert model.registry.bytes_used == 2


def test_end_ack_loss_replays_only_after_abort_then_cannot_close_new_assignment():
    model, vector, leases, requests = setup()
    with pytest.raises(ValueError, match="cancellation"):
        model.execute(requests, vector, lambda: model.request_end(leases[0]))
    first = model.poll_end(leases[0])
    assert first.acknowledged and model.request_end(leases[0]) == first
    assert model.poll_end(leases[0]) == first
    new = replace(leases[0], generation=2, session="new", episode="new")
    model.open(new)
    with pytest.raises(ValueError, match="stale"):
        model.request_end(leases[0])
    assert model.active[new.slot] == new


def test_wrong_lease_or_epoch_end_cannot_release_any_other_ticket():
    model, _, leases, requests = setup()
    tickets = tuple(model.submit(r, size=4) for r in requests)
    for bad in (
        replace(leases[0], session=leases[1].session),
        replace(leases[0], epoch="other"),
    ):
        with pytest.raises(ValueError, match="stale"):
            model.request_end(bad)
    assert model.registry.bytes_used == 8
    assert tuple(model.registry.tickets.values()) == tickets


def test_registry_timeout_after_commit_cannot_deliver_or_regenerate_cancelled_ticket():
    model, vector, leases, requests = setup()
    a = model.submit(requests[0], deadline=1, size=3)
    b = model.submit(requests[1], deadline=10, size=3)
    replies = model.execute(requests, vector)
    original = model.bundle
    with pytest.raises(TimeoutError):
        model.registry.pop(1)
    assert a.cancel_requested and not b.cancel_requested
    assert model.submit(requests[0], now=1, deadline=100) is a
    assert model.registry.bytes_used == 6
    with pytest.raises(ValueError, match="cancelled"):
        model.deliver(requests[0])
    with pytest.raises(ValueError, match="cancelled"):
        model.execute(requests, vector)
    assert vector.calls == 1 and model.bundle is original
    assert model.deliver(requests[1]) is replies[1]
    assert model.request_end(leases[0]).acknowledged is True
    assert model.registry.bytes_used == 3 and model.registry.ticket(requests[1]) is b


def test_unrelated_session_end_during_generation_waits_without_aborting_members():
    model, vector, leases, requests = setup(3)
    observed = []

    def generate(prepared):
        observed.append(model.request_end(leases[2]).acknowledged)
        return vector(prepared)

    replies = model.execute(requests[:2], generate)
    assert observed == [False] and len(replies) == 2
    assert model.poll_end(leases[2]).acknowledged is True
    assert model.deliver(requests[0]) is replies[0]
    assert model.deliver(requests[1]) is replies[1]


def test_seal_failure_releases_only_new_admissions_and_keeps_old_inflight():
    queue = BatchQueue(slots=2, batch=1)
    model, vector, _, requests = setup(registry=queue)
    old = model.submit(requests[0], size=7)
    assert queue.pop(0) == requests[:1]
    with pytest.raises(ValueError, match="membership"):
        model.execute(requests, vector)
    assert queue.tickets == {requests[0].key: old}
    assert old.state == "SEALED" and queue.bytes_used == 7 and vector.calls == 0


def test_restart_epoch_rejects_old_end_and_release_receipts():
    old, vector, leases, requests = setup()
    old.execute(requests, vector)
    ticket = old.registry.ticket(requests[0])
    new = ProtocolModel(2, epoch="server-2")
    with pytest.raises(ValueError, match="stale"):
        new.request_end(leases[0])
    with pytest.raises(ValueError, match="foreign"):
        new.registry.release(ticket, "delivered")
    assert old.registry.bytes_used == 2 and new.registry.bytes_used == 0
