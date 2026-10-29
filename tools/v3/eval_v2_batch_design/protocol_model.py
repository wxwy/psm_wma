"""Executable protocol specification, NOT a model server or Local-TTT implementation.

Scalar tuples stand for immutable candidate state. Fake generators establish
transaction/correlation properties only, never tensor or native batch parity.
All methods run on a conceptual single executor; hooks model event interleavings.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable
from dataclasses import dataclass
from types import MappingProxyType

from tools.v3.eval_v2_batch_design.ticket_registry import TicketRegistry


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
    frontier: int
    evidence: tuple[int, ...] = ()
    noise_seed: int = 123
    compatibility: str = "raw15-state15-h16"

    @property
    def key(self):
        # Canonical identity, not a freely reusable HTTP log/request number.
        identity = (self.lease, self.frontier)
        return hashlib.sha256(repr(identity).encode()).hexdigest()


@dataclass(frozen=True)
class State:
    frontier: int = 0
    fast: tuple[int, ...] | None = None
    visual: tuple[int, ...] = ()
    committed: bool = False


@dataclass(frozen=True)
class Prepared:
    request: Request
    state: State


@dataclass(frozen=True)
class Response:
    key: str
    action: tuple[float, ...]


@dataclass(frozen=True)
class Bundle:
    states: object
    responses: object

    @classmethod
    def of(cls, states, responses):
        return cls(MappingProxyType(dict(states)), MappingProxyType(dict(responses)))


@dataclass(frozen=True)
class EndReply:
    acknowledged: bool
    lease: Lease

    def __bool__(self):
        return self.acknowledged


class ProtocolModel:
    """One state publication point and SAME queue/executor/End lifecycle owner."""

    def __init__(self, capacity=3, epoch="server-1", registry=None):
        if capacity < 1:
            raise ValueError("positive capacity required")
        self.capacity, self.epoch = capacity, epoch
        self.w0 = (1, 2, 3, 4)
        self.active: dict[str, Lease] = {}
        self.generations: dict[str, int] = {}
        self.closed: dict[str, Lease] = {}
        self.closing: set[Lease] = set()
        self.cancelled_sessions: set[Lease] = set()
        self.registry = (
            registry
            if registry is not None
            else TicketRegistry(slots=capacity, batch=capacity, epoch=epoch)
        )
        if self.registry.epoch != epoch or self.registry.slots != capacity:
            raise ValueError("Session and queue require the SAME lifecycle authority")
        self.executor_busy = False
        self.bundle = Bundle.of({}, {})

    def open(self, lease):
        if (
            lease.epoch != self.epoch
            or lease.slot in self.active
            or lease.generation <= self.generations.get(lease.slot, 0)
            or lease.session in self.bundle.states
            or len(self.active) >= self.capacity
        ):
            raise ValueError("invalid, stale or over-capacity lease")
        self.generations[lease.slot] = lease.generation
        self.active[lease.slot] = lease
        self.bundle = Bundle.of(
            {**self.bundle.states, lease.session: State()}, self.bundle.responses
        )

    def _owned(self, request):
        lease = request.lease
        if lease.epoch != self.epoch or self.active.get(lease.slot) != lease:
            raise ValueError("closed or stale assignment")

    def _available(self, request):
        self._owned(request)
        if request.lease in self.closing or request.lease in self.cancelled_sessions:
            raise ValueError("Session closing or cancelled")

    def submit(self, request, now=0, deadline=1, size=1):
        self._owned(request)
        if request.key not in self.registry.tickets:
            self._available(request)
        return self.registry.submit(request, now, deadline, size)

    def request_cancel(self, lease):
        """Intent ONLY: never finishes work, frees credit or ACKs Session End."""
        self._owned(Request(lease, 0))
        self.cancelled_sessions.add(lease)
        self.registry.cancel(lease)

    def request_end(self, lease):
        """Nonblocking request; a draining response is explicitly NOT an ACK."""
        if lease.slot not in self.active and self.closed.get(lease.slot) == lease:
            return EndReply(True, lease)
        self._owned(Request(lease, 0))
        self.closing.add(lease)
        self.request_cancel(lease)
        return self.poll_end(lease)

    def poll_end(self, lease):
        if lease.slot not in self.active and self.closed.get(lease.slot) == lease:
            return EndReply(True, lease)
        self._owned(Request(lease, 0))
        if lease not in self.closing:
            raise ValueError("end was not requested")
        owned = self.registry.outstanding(lease)
        if self.executor_busy or any(not ticket.quiescent for ticket in owned):
            return EndReply(False, lease)
        # Only the executor can establish quiescence. End may then discard its
        # undelivered response, without rolling back any committed co-member.
        for ticket in owned:
            reason = "discarded" if ticket.state == "COMMITTED" else "aborted"
            self.registry.release(ticket, reason)
        del self.active[lease.slot]
        self.closed[lease.slot] = lease
        self.closing.remove(lease)
        self.cancelled_sessions.discard(lease)
        states = dict(self.bundle.states)
        states.pop(lease.session)
        responses = {
            key: value
            for key, value in self.bundle.responses.items()
            if value[0].lease.session != lease.session
        }
        self.bundle = Bundle.of(states, responses)
        return EndReply(True, lease)

    def reset(self, lease):
        """Compatibility spelling; True means proven end, False means deferred."""
        return self.request_end(lease).acknowledged

    def drain_queued_cancellations(self):
        """Executor event for work that never entered generation; no fake drain."""
        for ticket in tuple(self.registry.tickets.values()):
            if ticket.state == "QUEUED" and ticket.cancel_requested:
                batch_id = self.registry.seal((ticket.request,))
                self.registry.finish(batch_id, "ABORTED")
                self.registry.release(ticket, "aborted")

    def cached(self, request):
        self._available(request)
        existing = self.bundle.responses.get(request.key)
        if existing is None:
            return None
        if existing[0] != request:
            raise ValueError("request key reused with different payload")
        ticket = self.registry.tickets.get(request.key)
        if ticket is not None and ticket.cancel_requested:
            raise ValueError("ticket cancelled; response cannot be delivered")
        if ticket is not None and not ticket.quiescent:
            raise ValueError("committed response not yet quiescent")
        return existing[1]

    def deliver(self, request):
        reply = self.cached(request)
        if reply is None:
            raise ValueError("no committed response")
        return reply

    def acknowledge(self, request):
        """Client confirms the frozen response; release credit exactly once."""
        self.deliver(request)
        if request.key in self.registry.tickets:
            self.registry.release(self.registry.ticket(request), "delivered")
        return True

    def _prepare(self, request):
        self._owned(request)
        if not request.key or not 0 <= len(request.evidence) <= 16:
            raise ValueError("invalid request bounds")
        old = self.bundle.states[request.lease.session]
        if not old.committed:
            if request.frontier != 0 or request.evidence:
                raise ValueError("fresh episode must begin at frontier zero")
            return Prepared(request, State(committed=True))
        if not request.evidence or request.frontier != old.frontier + len(
            request.evidence
        ):
            raise ValueError("noncontiguous, duplicate or missing evidence")
        base = self.w0 if old.fast is None else old.fast
        # SYMBOLIC transition only. Production MUST call the model-owned scan.
        fast = tuple(value + sum(request.evidence) for value in base)
        return Prepared(request, State(request.frontier, fast, request.evidence, True))

    def execute(
        self,
        requests,
        generate,
        before_publish: Callable[[], None] = lambda: None,
        *,
        on_stage: Callable[[str], None] = lambda stage: None,
    ):
        """Commit responses, but retain ticket credit until delivery ACK/discard."""
        if (
            not requests
            or len(requests) > self.capacity
            or len({r.lease.session for r in requests}) != len(requests)
            or len({r.key for r in requests}) != len(requests)
            or len({r.compatibility for r in requests}) != 1
        ):
            raise ValueError("invalid sealed batch")
        if self.executor_busy:
            raise ValueError("single model executor already owns a batch")
        # Cancelled popped work must still reach an executor-owned abort/drain.
        cached = [
            self.cached(r)
            if r.lease not in self.closing and r.lease not in self.cancelled_sessions
            else None
            for r in requests
        ]
        if all(reply is not None for reply in cached):
            return tuple(cached)
        if any(reply is not None for reply in cached):
            raise ValueError("route cached tickets before sealing a new batch")
        created = []
        try:
            for request in requests:
                if request.key in self.registry.tickets:
                    self.registry.ticket(request)
                else:
                    created.append(self.submit(request))
            batch_id = self.registry.seal(requests)
        except Exception:
            for ticket in created:
                batch_id = self.registry.seal((ticket.request,))
                self.registry.finish(batch_id, "ABORTED")
                self.registry.release(ticket, "aborted")
            raise
        tickets = tuple(self.registry.ticket(request) for request in requests)
        original, committed = self.bundle, False
        self.executor_busy = True

        def fence():
            if self.registry.cancelled(batch_id):
                raise ValueError("batch cancellation requested; no action dispatched")
            for request in requests:
                self._owned(request)

        try:
            on_stage("SEALED")
            fence()
            prepared = []
            for index, request in enumerate(requests):
                prepared.append(self._prepare(request))
                on_stage(f"PREPARED_ITEM_{index}")
                fence()
            prepared = tuple(prepared)
            self.registry.advance(batch_id, "PREPARED")
            on_stage("PREPARED")
            fence()
            self.registry.advance(batch_id, "GENERATING")
            on_stage("GENERATING")
            fence()
            replies = tuple(generate(prepared))  # ONE vector call, no item loop.
            self.registry.advance(batch_id, "GENERATED")
            on_stage("GENERATED")
            fence()
            if len(replies) != len(requests):
                raise ValueError("output cardinality mismatch")
            for request, reply in zip(requests, replies, strict=True):
                if (
                    reply.key != request.key
                    or not reply.action
                    or not all(math.isfinite(x) for x in reply.action)
                ):
                    raise ValueError("invalid or mis-correlated output")
            states, responses = dict(original.states), dict(original.responses)
            sessions = {r.lease.session for r in requests}
            responses = {
                k: v for k, v in responses.items() if v[0].lease.session not in sessions
            }
            for candidate, reply in zip(prepared, replies, strict=True):
                states[candidate.request.lease.session] = candidate.state
                responses[reply.key] = (candidate.request, reply)
            replacement = Bundle.of(states, responses)
            self.registry.advance(batch_id, "VALIDATED")
            on_stage("VALIDATED")
            before_publish()
            fence()
            if self.bundle is not original:
                raise ValueError("ownership/state changed before publication")
            # Model-owner critical section: no observer callback in between.
            self.registry.advance(batch_id, "COMMITTED")
            self.bundle, committed = replacement, True
            on_stage("COMMITTED")
            return replies
        finally:
            # An EXECUTOR event, only after generate returns/raises/unwinds.
            # Session End/HTTP timeout never supplies this quiescence proof.
            self.registry.finish(batch_id, "COMMITTED" if committed else "ABORTED")
            if not committed:
                for ticket in tickets:
                    self.registry.release(ticket, "aborted")
            self.executor_busy = False


class BatchQueue(TicketRegistry):
    """Compatibility name for the SAME queued+inflight lifecycle authority."""
