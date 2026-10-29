"""Symbolic queued + in-flight ownership; not a threaded or native service.

Only the conceptual single executor calls advance/finish. Cancellation records
intent, never proof that an executing model transaction has stopped. The caller
must finish only after its executor has returned or unwound all owned work.
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field


@dataclass(eq=False)
class Ticket:
    request: object
    arrived: float
    deadline: float
    size: int
    state: str = "QUEUED"
    batch_id: str | None = None
    cancel_requested: bool = False
    quiescent: bool = False
    released: bool = False
    owner: object = field(default=None, repr=False)


class TicketRegistry:
    """One bounded authority shared by the symbolic queue and Session executor."""

    STAGES = (
        "SEALED",
        "PREPARED",
        "GENERATING",
        "GENERATED",
        "VALIDATED",
        "COMMITTED",
    )

    def __init__(
        self,
        slots=3,
        batch=2,
        wait=0.02,
        byte_cap=64,
        item_cap=32,
        epoch="server-1",
    ):
        if any(
            type(value) is not int or value < 1
            for value in (slots, batch, byte_cap, item_cap)
        ):
            raise ValueError("positive integer queue bounds required")
        if (
            not math.isfinite(wait)
            or wait <= 0
            or not isinstance(epoch, str)
            or not epoch
        ):
            raise ValueError("finite positive wait and nonempty epoch required")
        self.slots, self.batch, self.wait = slots, batch, wait
        self.byte_cap, self.item_cap, self.epoch = byte_cap, item_cap, epoch
        self.tickets: dict[str, Ticket] = {}
        self._batches: dict[str, tuple[Ticket, ...]] = {}

    @property
    def rows(self):
        return [
            (ticket.request, ticket.arrived, ticket.deadline, ticket.size)
            for ticket in self.tickets.values()
            if ticket.state == "QUEUED"
        ]

    @property
    def bytes_used(self):
        return sum(ticket.size for ticket in self.tickets.values())

    def _epoch(self, lease):
        if lease.epoch != self.epoch:
            raise ValueError("stale server epoch")

    def ticket(self, request):
        self._epoch(request.lease)
        ticket = self.tickets.get(request.key)
        if ticket is None:
            raise ValueError("no unresolved ticket for request")
        if ticket.owner is not self or ticket.request != request:
            raise ValueError("pending key payload mismatch")
        return ticket

    def submit(self, request, now, deadline, size=1):
        self._epoch(request.lease)
        if request.key in self.tickets:
            # HTTP retries attach to the original immutable admission budget.
            # They cannot renew deadline or alter its retained encoded size.
            return self.ticket(request)
        if (
            not math.isfinite(now)
            or not math.isfinite(deadline)
            or deadline <= now
            or type(size) is not int
            or not 1 <= size <= self.item_cap
        ):
            raise ValueError("invalid size or deadline")
        if any(
            ticket.request.lease.slot == request.lease.slot
            for ticket in self.tickets.values()
        ):
            raise ValueError(
                "one pending request per physical slot, including in-flight work"
            )
        if len(self.tickets) >= self.slots or self.bytes_used + size > self.byte_cap:
            raise OverflowError("bounded queued + in-flight capacity full")
        ticket = Ticket(request, now, deadline, size, owner=self)
        self.tickets[request.key] = ticket
        return ticket

    def add(self, request, now, deadline, size=1):
        fresh = request.key not in self.tickets
        self.submit(request, now, deadline, size)
        return fresh

    def _batch(self, batch_id):
        batch = self._batches.get(batch_id)
        if batch is None:
            raise ValueError("unknown or already released batch")
        return batch

    def seal(self, requests):
        requests = tuple(requests)
        if (
            not requests
            or len(requests) > min(self.slots, self.batch)
            or len({request.key for request in requests}) != len(requests)
            or len({request.lease.slot for request in requests}) != len(requests)
            or len({request.lease.session for request in requests}) != len(requests)
            or len({request.compatibility for request in requests}) != 1
        ):
            raise ValueError("invalid sealed batch membership")
        tickets = tuple(self.ticket(request) for request in requests)
        if all(ticket.state == "SEALED" for ticket in tickets):
            batch_id = tickets[0].batch_id
            if (
                any(ticket.batch_id != batch_id for ticket in tickets)
                or self._batch(batch_id) != tickets
            ):
                raise ValueError("must adopt the exact complete ordered sealed batch")
            return batch_id
        if not all(
            ticket.state == "QUEUED" and ticket.batch_id is None for ticket in tickets
        ):
            raise ValueError("cannot reseal running, terminal or mixed-state tickets")
        batch_id = uuid.uuid4().hex
        self._batches[batch_id] = tickets
        for ticket in tickets:
            ticket.state, ticket.batch_id = "SEALED", batch_id
        return batch_id

    def pop(self, now):
        if not math.isfinite(now):
            raise ValueError("finite monotonic time required")
        expired = [
            ticket
            for ticket in self.tickets.values()
            if ticket.state != "ABORTED" and ticket.deadline <= now
        ]
        if expired:
            for ticket in expired:
                ticket.cancel_requested = True
            raise TimeoutError(
                "expired queued or in-flight request; cancellation is not quiescence"
            )
        rows = self.rows
        if not rows:
            return ()
        head, arrived, deadline, _ = rows[0]
        compatible = [row for row in rows if row[0].compatibility == head.compatibility]
        if len(compatible) < min(self.batch, self.slots) and now < min(
            arrived + self.wait, deadline
        ):
            return ()
        chosen = tuple(row[0] for row in compatible[: self.batch])
        self.seal(chosen)
        return chosen

    def advance(self, batch_id, state):
        batch = self._batch(batch_id)
        current = batch[0].state
        if any(
            ticket.released or ticket.quiescent or ticket.state != current
            for ticket in batch
        ):
            raise ValueError("batch ownership/stage mismatch")
        if (
            current not in self.STAGES[:-1]
            or state != self.STAGES[self.STAGES.index(current) + 1]
        ):
            raise ValueError("invalid executor stage transition")
        if state == "COMMITTED" and any(ticket.cancel_requested for ticket in batch):
            raise ValueError("cancelled batch cannot enter commit")
        for ticket in batch:
            ticket.state = state

    def finish(self, batch_id, outcome):
        """Executor release event; never called by End, timeout or HTTP handlers."""
        batch = self._batch(batch_id)
        if any(ticket.quiescent or ticket.released for ticket in batch):
            raise ValueError("executor already finished or ownership released")
        allowed = ("COMMITTED",) if outcome == "COMMITTED" else self.STAGES[:-1]
        if outcome not in ("COMMITTED", "ABORTED") or any(
            ticket.state not in allowed for ticket in batch
        ):
            raise ValueError("invalid terminal outcome for current batch stage")
        for ticket in batch:
            ticket.state, ticket.quiescent = outcome, True

    def release(self, ticket, reason):
        if ticket.owner is not self:
            raise ValueError("foreign ticket owner")
        allowed = (
            ("delivered", "discarded") if ticket.state == "COMMITTED" else ("aborted",)
        )
        if (
            ticket.state not in ("COMMITTED", "ABORTED")
            or not ticket.quiescent
            or reason not in allowed
        ):
            raise ValueError(
                "ticket cannot release before terminal executor quiescence"
            )
        if ticket.released:
            return False
        if self.tickets.get(ticket.request.key) is not ticket:
            raise ValueError("stale or foreign active ticket capability")
        ticket.released = True
        del self.tickets[ticket.request.key]
        batch = self._batch(ticket.batch_id)
        remaining = tuple(member for member in batch if not member.released)
        if remaining:
            # Credit return must also drop this registry's payload reference;
            # an unrelated co-member's delivery delay must not retain it.
            self._batches[ticket.batch_id] = remaining
        else:
            del self._batches[ticket.batch_id]
        return True

    def cancel(self, lease):
        self._epoch(lease)
        tickets = self.outstanding(lease)
        for ticket in tickets:
            ticket.cancel_requested = True
        return tickets

    def outstanding(self, lease):
        self._epoch(lease)
        return tuple(
            ticket for ticket in self.tickets.values() if ticket.request.lease == lease
        )

    def cancelled(self, batch_id):
        return any(ticket.cancel_requested for ticket in self._batch(batch_id))
