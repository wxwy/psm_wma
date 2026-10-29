"""Design witnesses only: symbolic state, fake clock, fake vector generator."""

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
        self.calls = []

    def __call__(self, prepared):
        self.calls.append(prepared)
        return tuple(
            Response(
                p.request.key, (float(p.request.frontier), float(p.request.noise_seed))
            )
            for p in prepared
        )


def setup(n=3):
    model, generator = ProtocolModel(n), Vector()
    leases = tuple(
        Lease(model.epoch, f"gpu0/slot{i}", 1, f"session{i}", f"ep{i}")
        for i in range(n)
    )
    for lease in leases:
        model.open(lease)
    requests = tuple(Request(lease, 0) for lease in leases)
    return model, generator, leases, requests


@pytest.mark.parametrize("n", [1, 2, 3])
def test_single_vector_call_and_cold_prefixes(n):
    model, generator, _, requests = setup(n)
    replies = model.execute(requests, generator)
    assert len(generator.calls) == 1
    assert tuple(p.state.fast for p in generator.calls[0]) == (None,) * n
    assert tuple(reply.key for reply in replies) == tuple(r.key for r in requests)


def test_independent_evidence_w0_and_reset_ack():
    model, generator, leases, requests = setup(2)
    model.execute(requests, generator)
    updates = tuple(
        replace(r, frontier=2, evidence=(i + 1, i + 2)) for i, r in enumerate(requests)
    )
    model.execute(updates, generator)
    a, b = (model.bundle.states[lease.session] for lease in leases)
    assert a.fast != b.fast and a.fast is not b.fast
    assert a.visual != b.visual and model.w0 == (1, 2, 3, 4)
    model.reset(leases[0])
    assert model.bundle.states[leases[1].session] is b
    fresh = replace(leases[0], generation=2, session="new", episode="new-episode")
    model.open(fresh)
    assert model.bundle.states["new"].fast is None
    with pytest.raises(ValueError, match="stale"):
        model.open(leases[0])
    with pytest.raises(ValueError, match="stale"):
        model.execute((requests[0],), generator)


def test_mixed_cold_hot_prefixes_preserve_sample_positions():
    model, generator, _, requests = setup(3)
    model.execute(requests[:2], generator)
    hot = tuple(
        replace(r, frontier=1, evidence=(i + 1,)) for i, r in enumerate(requests[:2])
    )
    model.execute((hot[1], requests[2], hot[0]), generator)
    states = tuple(p.state.fast for p in generator.calls[-1])
    assert states[0] is not None and states[1] is None and states[2] is not None
    assert states[0] != states[2]


@pytest.mark.parametrize("fault", ["raise", "nan", "reverse", "missing", "allocation"])
def test_sealed_batch_failure_never_publishes_any_session(fault):
    model, generator, _, requests = setup(2)
    original = model.bundle

    def broken(prepared):
        replies = generator(prepared)
        if fault == "raise":
            raise RuntimeError("generation failure")
        if fault == "nan":
            return (replies[0], replace(replies[1], action=(float("nan"),)))
        if fault == "reverse":
            return replies[::-1]
        if fault == "missing":
            return replies[:1]
        return replies

    def allocation():
        if fault == "allocation":
            raise MemoryError("response serialization/allocation failure")

    with pytest.raises((RuntimeError, ValueError, MemoryError)):
        model.execute(requests, broken, allocation)
    assert model.bundle is original and not model.bundle.responses


def test_cancel_between_generation_and_publication_fences_whole_batch():
    model, generator, leases, requests = setup(2)
    b = model.bundle.states[leases[1].session]
    with pytest.raises(ValueError, match="stale"):
        model.execute(requests, generator, lambda: model.reset(leases[0]))
    assert model.bundle.states[leases[1].session] is b
    assert not model.bundle.responses


def test_lost_response_retry_is_identical_and_never_regenerates():
    model, generator, _, requests = setup(2)
    replies = model.execute(requests, generator)
    original = model.bundle
    assert model.cached(requests[1]) is replies[1]  # HTTP completion order reversed.
    assert model.cached(requests[0]) is replies[0]
    assert model.execute(requests, generator) == replies
    assert len(generator.calls) == 1 and model.bundle is original
    with pytest.raises(ValueError, match="different payload"):
        model.cached(replace(requests[0], noise_seed=99))


def test_evicted_reply_cannot_restart_old_frontier():
    model, generator, _, requests = setup(1)
    model.execute(requests, generator)
    hot = replace(requests[0], frontier=1, evidence=(7,))
    model.execute((hot,), generator)
    assert len(model.bundle.responses) == 1
    assert model.cached(requests[0]) is None
    with pytest.raises(ValueError, match="evidence"):
        model.execute(requests, generator)
    assert len(generator.calls) == 2


def test_reset_of_foreign_lease_preserves_every_session():
    model, _, leases, _ = setup(2)
    original = model.bundle
    with pytest.raises(ValueError, match="stale"):
        model.reset(replace(leases[0], session=leases[1].session))
    assert model.bundle is original


def test_restarted_server_rejects_old_epoch():
    _, generator, leases, requests = setup(1)
    restarted = ProtocolModel(epoch="server-2")
    with pytest.raises(ValueError, match="stale"):
        restarted.open(leases[0])
    with pytest.raises(ValueError, match="stale"):
        restarted.execute(requests, generator)
    assert not generator.calls


@pytest.mark.parametrize(
    "mutation", ["duplicate-session", "incompatible", "fresh-evidence"]
)
def test_invalid_membership_rejected_before_generation(mutation):
    model, generator, _, requests = setup(2)
    a, b = requests
    if mutation == "duplicate-session":
        b = replace(a, frontier=1, evidence=(1,))
    elif mutation == "incompatible":
        b = replace(b, compatibility="other-checkpoint")
    else:
        b = replace(b, frontier=1, evidence=(1,))
    original = model.bundle
    with pytest.raises(ValueError):
        model.execute((a, b), generator)
    assert not generator.calls and model.bundle is original


@pytest.mark.parametrize("batch", [1, 2, 3, 8])
def test_partial_batch_flush_is_bounded_even_when_b_exceeds_m(batch):
    _, _, _, requests = setup(3)
    queue = BatchQueue(slots=3, batch=batch)
    queue.add(requests[0], now=0, deadline=1)
    if batch > 1:
        assert queue.pop(0.019) == ()
    assert queue.pop(0.021) == requests[:1]


def test_full_batch_and_incompatible_oldest_are_not_starved():
    _, _, _, requests = setup(3)
    queue = BatchQueue(slots=3, batch=2)
    a, b, c = requests
    queue.add(a, 0, 1)
    queue.add(replace(b, compatibility="second"), 0.001, 1)
    queue.add(c, 0.002, 1)
    assert queue.pop(0.003) == (a, c)
    assert queue.pop(0.022) == (replace(b, compatibility="second"),)


def test_duplicate_pending_request_does_not_consume_queue_capacity():
    _, _, _, requests = setup(2)
    queue = BatchQueue(slots=2, batch=2)
    assert queue.add(requests[0], 0, 1)
    assert not queue.add(requests[0], 0.001, 1)
    with pytest.raises(ValueError, match="payload mismatch"):
        queue.add(replace(requests[0], noise_seed=99), 0.001, 1)
    with pytest.raises(ValueError, match="one pending"):
        queue.add(replace(requests[0], frontier=1, evidence=(1,)), 0.001, 1)
    assert len(queue.rows) == 1


@pytest.mark.parametrize("fault", ["item-size", "total-bytes", "deadline"])
def test_queue_limits_fail_without_delivering_actions(fault):
    _, _, _, requests = setup(2)
    queue = BatchQueue(slots=2, batch=2, byte_cap=3, item_cap=2)
    queue.add(requests[0], 0, 1, size=2)
    if fault == "item-size":
        with pytest.raises(ValueError):
            queue.add(requests[1], 0.01, 1, size=3)
    elif fault == "total-bytes":
        with pytest.raises(OverflowError):
            queue.add(requests[1], 0.01, 1, size=2)
    else:
        with pytest.raises(TimeoutError):
            queue.pop(1)
    assert len(queue.rows) == 1


def test_end_ack_can_be_retried_but_cannot_close_a_new_assignment():
    model, _, leases, _ = setup(2)
    assert model.reset(leases[0]) is True
    original = model.bundle
    assert model.reset(leases[0]) is True
    assert model.bundle is original
    new = replace(leases[0], generation=2, session="new", episode="new")
    model.open(new)
    original = model.bundle
    with pytest.raises(ValueError, match="stale"):
        model.reset(leases[0])
    assert model.bundle is original


def test_literal_noise_seed_is_not_changed_by_batch_position():
    batched, vector, _, requests = setup(3)
    requests = tuple(replace(r, noise_seed=10 + i) for i, r in enumerate(requests))
    replies = batched.execute(requests[::-1], vector)
    serial, reference, _, _ = setup(3)
    expected = {r.key: serial.execute((r,), reference)[0] for r in requests}
    assert all(expected[reply.key] == reply for reply in replies)
    assert len(vector.calls) == 1 and len(reference.calls) == 3
