"""Deterministic symbolic lifecycle witnesses; no model, HTTP, tensors or GPU."""

from dataclasses import dataclass, replace

import pytest

from tools.v3.eval_v2_batch_design.ticket_registry import Ticket, TicketRegistry


@dataclass(frozen=True)
class Lease:
    epoch: str
    slot: str
    generation: int
    session: str
    episode: str


@dataclass(frozen=True)
class Request:
    lease: Lease
    frontier: int = 0
    noise_seed: int = 123
    compatibility: str = "raw15-state15-h16"

    @property
    def key(self):
        return repr((self.lease, self.frontier))


def request(index=0, **kwargs):
    return Request(
        Lease("server-1", f"slot{index}", 1, f"session{index}", f"ep{index}"), **kwargs
    )


def advance_to(registry, batch_id, state):
    for following in registry.STAGES[1:]:
        registry.advance(batch_id, following)
        if following == state:
            return
    raise AssertionError(f"unreachable test stage {state}")


@pytest.mark.parametrize(
    "state", ["SEALED", "PREPARED", "GENERATING", "GENERATED", "VALIDATED", "COMMITTED"]
)
def test_duplicate_joins_and_new_frontier_rejected_after_pop_at_every_stage(state):
    registry = TicketRegistry(slots=2, batch=2)
    a, b = request(0), request(1)
    first = registry.submit(a, 0, 1, size=2)
    registry.submit(b, 0, 1, size=3)
    assert registry.pop(0) == (a, b)
    batch_id = first.batch_id
    if state != "SEALED":
        advance_to(registry, batch_id, state)
    assert first.state == state and registry.bytes_used == 5
    assert registry.rows == [] and not first.quiescent
    assert registry.submit(a, 0.1, 999, size=1) is first
    assert first.arrived == 0 and first.deadline == 1 and first.size == 2
    assert registry.bytes_used == 5 and len(registry.tickets) == 2
    with pytest.raises(ValueError, match="one pending"):
        registry.submit(replace(a, frontier=1), 0.1, 1)
    with pytest.raises(ValueError, match="payload mismatch"):
        registry.submit(replace(a, noise_seed=999), 0.1, 1)
    with pytest.raises(ValueError, match="quiescence"):
        registry.release(first, "delivered")


def test_inflight_bytes_and_slot_capacity_are_not_reissued_on_pop():
    registry = TicketRegistry(slots=3, batch=1, byte_cap=5)
    first = registry.submit(request(0), 0, 1, size=3)
    assert registry.pop(0) == (first.request,)
    assert registry.bytes_used == 3 and registry.rows == []
    with pytest.raises(OverflowError):
        registry.submit(request(1), 0.1, 1, size=3)
    second = registry.submit(request(1), 0.1, 1, size=2)
    assert registry.bytes_used == 5
    with pytest.raises(OverflowError):
        registry.submit(request(2), 0.1, 1)
    registry.finish(first.batch_id, "ABORTED")
    assert registry.bytes_used == 5  # Finishing alone is not transport release.
    assert registry.release(first, "aborted") is True
    assert registry.bytes_used == 2 and registry.ticket(second.request) is second
    assert registry.submit(request(2), 0.1, 1, size=3).size == 3


def test_committed_result_retains_credit_until_delivered_or_discarded():
    registry = TicketRegistry(slots=1, batch=1)
    first = registry.submit(request(), 0, 1, size=4)
    registry.pop(0)
    advance_to(registry, first.batch_id, "COMMITTED")
    assert not first.quiescent and registry.bytes_used == 4
    registry.finish(first.batch_id, "COMMITTED")
    assert first.quiescent and registry.bytes_used == 4
    assert registry.submit(first.request, 0.2, 2) is first
    with pytest.raises(ValueError, match="one pending"):
        registry.submit(replace(first.request, frontier=1), 0.2, 2)
    with pytest.raises(ValueError):
        registry.finish(first.batch_id, "ABORTED")
    assert registry.release(first, "delivered") is True
    assert registry.bytes_used == 0 and not registry.tickets and not registry._batches
    next_ticket = registry.submit(replace(first.request, frontier=1), 0.2, 2)
    assert registry.release(first, "delivered") is False
    assert (
        registry.ticket(next_ticket.request) is next_ticket and registry.bytes_used == 1
    )


@pytest.mark.parametrize("state", ["QUEUED", "SEALED", "GENERATING", "COMMITTED"])
def test_timeout_only_requests_cancel_and_retains_credits_until_executor_drain(state):
    registry = TicketRegistry(slots=1, batch=1)
    first = registry.submit(request(), 0, 1, size=4)
    if state != "QUEUED":
        registry.pop(0)
        if state != "SEALED":
            advance_to(registry, first.batch_id, state)
    with pytest.raises(TimeoutError, match="not quiescence"):
        registry.pop(1)
    assert first.cancel_requested and not first.quiescent and registry.bytes_used == 4
    assert registry.outstanding(first.request.lease) == (first,)
    with pytest.raises(ValueError):
        registry.release(first, "aborted")
    if state == "QUEUED":
        registry.seal((first.request,))
    outcome = "COMMITTED" if state == "COMMITTED" else "ABORTED"
    registry.finish(first.batch_id, outcome)
    reason = "discarded" if outcome == "COMMITTED" else "aborted"
    assert registry.release(first, reason) is True
    assert registry.bytes_used == 0 and not registry._batches


def test_cancel_targets_exact_session_and_does_not_complete_or_release_batch():
    registry = TicketRegistry(slots=2, batch=2)
    a, b = request(0), request(1)
    ta = registry.submit(a, 0, 1, size=2)
    tb = registry.submit(b, 0, 1, size=3)
    registry.pop(0)
    advance_to(registry, ta.batch_id, "GENERATING")
    assert registry.cancel(a.lease) == (ta,)
    assert registry.cancelled(ta.batch_id)
    assert ta.cancel_requested and not tb.cancel_requested
    assert not ta.quiescent and not tb.quiescent and registry.bytes_used == 5
    wrong = replace(a.lease, session="foreign")
    assert registry.cancel(wrong) == ()
    registry.finish(ta.batch_id, "ABORTED")
    assert registry.release(ta, "aborted") and registry.bytes_used == 3
    assert registry._batches[tb.batch_id] == (tb,)
    assert registry.outstanding(b.lease) == (tb,)
    assert registry.release(tb, "aborted") and registry.bytes_used == 0


def test_cancelled_precommit_batch_cannot_cross_commit_boundary():
    registry = TicketRegistry(slots=1, batch=1)
    first = registry.submit(request(), 0, 1)
    registry.pop(0)
    advance_to(registry, first.batch_id, "VALIDATED")
    registry.cancel(first.request.lease)
    with pytest.raises(ValueError, match="cancelled"):
        registry.advance(first.batch_id, "COMMITTED")
    assert first.state == "VALIDATED" and not first.quiescent
    registry.finish(first.batch_id, "ABORTED")
    assert registry.release(first, "aborted")


def test_postcommit_cancel_only_allows_discard_and_preserves_other_members_credit():
    registry = TicketRegistry(slots=2, batch=2)
    a, b = request(0), request(1)
    ta = registry.submit(a, 0, 1, size=2)
    tb = registry.submit(b, 0, 1, size=3)
    registry.pop(0)
    advance_to(registry, ta.batch_id, "COMMITTED")
    registry.cancel(a.lease)
    with pytest.raises(ValueError):
        registry.finish(ta.batch_id, "ABORTED")
    registry.finish(ta.batch_id, "COMMITTED")
    assert registry.release(ta, "discarded")
    assert registry.ticket(b) is tb and registry.bytes_used == 3
    assert not tb.cancel_requested and tb.state == "COMMITTED"
    assert registry.release(tb, "delivered")


def test_seal_adopts_only_exact_complete_ordered_pop_membership():
    registry = TicketRegistry(slots=3, batch=2)
    requests = (request(0), request(1), request(2))
    for req in requests:
        registry.submit(req, 0, 1)
    popped = registry.pop(0)
    batch_id = registry.ticket(requests[0]).batch_id
    assert registry.seal(popped) == batch_id
    for invalid in (
        popped[:1],
        popped[::-1],
        (requests[0], requests[2]),
        (requests[0], requests[0]),
    ):
        with pytest.raises(ValueError):
            registry.seal(invalid)
    assert registry.bytes_used == 3


def test_foreign_or_stale_capability_cannot_release_an_owned_ticket():
    registry = TicketRegistry(slots=1, batch=1)
    first = registry.submit(request(), 0, 1)
    registry.pop(0)
    registry.finish(first.batch_id, "ABORTED")
    foreign = TicketRegistry(slots=1, batch=1)
    with pytest.raises(ValueError, match="foreign"):
        foreign.release(first, "aborted")
    forged = Ticket(
        first.request, 0, 1, 1, state="ABORTED", quiescent=True, owner=registry
    )
    with pytest.raises(ValueError, match="capability"):
        registry.release(forged, "aborted")
    assert registry.bytes_used == 1
    assert registry.release(first, "aborted")
    again = registry.submit(first.request, 0.1, 1)
    assert again is not first
    assert registry.release(first, "aborted") is False
    assert registry.ticket(first.request) is again and registry.bytes_used == 1


def test_new_server_epoch_rejects_old_submit_lookup_cancel_and_seal():
    registry = TicketRegistry(epoch="server-2")
    old = request()
    for operation in (
        lambda: registry.submit(old, 0, 1),
        lambda: registry.ticket(old),
        lambda: registry.cancel(old.lease),
        lambda: registry.seal((old,)),
    ):
        with pytest.raises(ValueError, match="epoch"):
            operation()
    fresh = replace(old, lease=replace(old.lease, epoch="server-2"))
    assert registry.submit(fresh, 0, 1).request == fresh
    assert registry.bytes_used == 1


@pytest.mark.parametrize("batch", [1, 2, 3, 8])
def test_partial_flush_preserves_credit_even_when_max_batch_exceeds_slots(batch):
    registry = TicketRegistry(slots=3, batch=batch)
    first = registry.submit(request(), 0, 1, size=4)
    if batch > 1:
        assert registry.pop(0.019) == ()
    assert registry.pop(0.021) == (first.request,)
    assert first.state == "SEALED" and registry.bytes_used == 4
    assert registry.submit(first.request, 0.03, 2) is first


def test_full_compatible_batch_preserves_oldest_incompatible_ticket_and_total_bytes():
    registry = TicketRegistry(slots=3, batch=2)
    a, b, c = request(0), request(1, compatibility="other"), request(2)
    for req in (a, b, c):
        registry.submit(req, 0, 1, size=2)
    assert registry.pop(0) == (a, c)
    assert registry.rows == [(b, 0, 1, 2)] and registry.bytes_used == 6
    assert registry.pop(0.021) == (b,)
    assert registry.bytes_used == 6 and registry.rows == []


def test_invalid_transitions_and_finish_do_not_create_quiescence():
    registry = TicketRegistry(slots=1, batch=1)
    first = registry.submit(request(), 0, 1)
    batch_id = registry.seal((first.request,))
    with pytest.raises(ValueError):
        registry.advance(batch_id, "COMMITTED")
    with pytest.raises(ValueError):
        registry.finish(batch_id, "COMMITTED")
    assert first.state == "SEALED" and not first.quiescent
    registry.finish(batch_id, "ABORTED")
    with pytest.raises(ValueError):
        registry.finish(batch_id, "ABORTED")
    with pytest.raises(ValueError):
        registry.release(first, "delivered")
    assert registry.release(first, "aborted")
