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


class ProtocolModel:
    """A single publication point for symbolic fast/visual state AND response cache."""

    def __init__(self, capacity=3, epoch="server-1"):
        if capacity < 1:
            raise ValueError("positive capacity required")
        self.capacity, self.epoch = capacity, epoch
        self.w0 = (1, 2, 3, 4)
        self.active: dict[str, Lease] = {}
        self.generations: dict[str, int] = {}
        self.closed: dict[str, Lease] = {}
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

    def reset(self, lease):
        """Exact ACK only for an active owned lease; old generations stay fenced."""
        if lease.slot not in self.active and self.closed.get(lease.slot) == lease:
            return True  # Lost end ACK can be fetched without reopening the lease.
        self._owned(Request(lease, 0))
        del self.active[lease.slot]
        self.closed[lease.slot] = lease
        states = dict(self.bundle.states)
        states.pop(lease.session)
        responses = {
            key: value
            for key, value in self.bundle.responses.items()
            if value[0].lease.session != lease.session
        }
        self.bundle = Bundle.of(states, responses)
        return True

    def cached(self, request):
        self._owned(request)
        existing = self.bundle.responses.get(request.key)
        if existing is None:
            return None
        if existing[0] != request:
            raise ValueError("request key reused with different payload")
        return existing[1]

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
        self, requests, generate, before_publish: Callable[[], None] = lambda: None
    ):
        """Only NEW tickets form a sealed batch; cached tickets bypass the queue."""
        if (
            not requests
            or len(requests) > self.capacity
            or len({r.lease.session for r in requests}) != len(requests)
            or len({r.key for r in requests}) != len(requests)
            or len({r.compatibility for r in requests}) != 1
        ):
            raise ValueError("invalid sealed batch")
        cached = [self.cached(r) for r in requests]
        if all(reply is not None for reply in cached):
            return tuple(cached)
        if any(reply is not None for reply in cached):
            raise ValueError("route cached tickets before sealing a new batch")
        original = self.bundle
        prepared = tuple(self._prepare(r) for r in requests)
        replies = tuple(generate(prepared))  # EXACTLY ONE vector call, no item loop.
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
        replacement = Bundle.of(states, responses)  # All allocations before commit.
        before_publish()  # Deterministic failure/cancel injection, not production API.
        for request in requests:
            self._owned(request)
        if self.bundle is not original:
            raise ValueError("ownership/state changed before publication")
        self.bundle = replacement  # ONLY publication of all candidates and replies.
        return replies


class BatchQueue:
    """Fake-clock bounded FIFO compatibility queue; not a threaded HTTP service."""

    def __init__(self, slots=3, batch=2, wait=0.02, byte_cap=64, item_cap=32):
        if min(slots, batch, wait, byte_cap, item_cap) <= 0:
            raise ValueError("positive queue bounds required")
        self.slots, self.batch, self.wait = slots, batch, wait
        self.byte_cap, self.item_cap = byte_cap, item_cap
        self.rows = []

    def add(self, request, now, deadline, size=1):
        if size < 1 or size > self.item_cap or deadline <= now:
            raise ValueError("invalid size or deadline")
        for existing, _, _, _ in self.rows:
            if existing.key == request.key:
                if existing != request:
                    raise ValueError("pending key payload mismatch")
                return False  # Duplicate HTTP submission attaches to same ticket.
            if existing.lease.slot == request.lease.slot:
                raise ValueError("one pending request per physical slot")
        if (
            len(self.rows) >= self.slots
            or sum(row[3] for row in self.rows) + size > self.byte_cap
        ):
            raise OverflowError("bounded queue full")
        self.rows.append((request, now, deadline, size))
        return True

    def pop(self, now):
        if not self.rows:
            return ()
        if any(deadline <= now for _, _, deadline, _ in self.rows):
            raise TimeoutError("expired queued request; coordinator must safe-stop")
        head, arrived, deadline, _ = self.rows[0]
        compatible = [
            row for row in self.rows if row[0].compatibility == head.compatibility
        ]
        if len(compatible) < min(self.batch, self.slots) and now < min(
            arrived + self.wait, deadline
        ):
            return ()
        chosen = compatible[: self.batch]
        self.rows = [row for row in self.rows if row not in chosen]
        return tuple(row[0] for row in chosen)
