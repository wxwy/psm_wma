"""CPU-only fake-host conformance model for the V27 host boundary.

This module intentionally has no process, IPC, filesystem, or project I/O.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import secrets


class State(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    CONSUMING = "CONSUMING"
    TERMINAL = "TERMINAL"


@dataclass(frozen=True)
class ReviewRecordV27:
    digest: str
    host_generation_id: str
    host_session_id: str
    live_plan_id: str
    live_plan_digest: str
    host_lease_id: str
    binding_digest: str


@dataclass(frozen=True)
class ReviewApprovalV27:
    gate: str
    root: str
    child: str
    record_digest: str
    host_generation_id: str
    host_session_id: str
    live_plan_id: str
    live_plan_digest: str
    host_lease_id: str
    binding_digest: str
    nonce: str
    counter: int = 1


class FakeStage1HostV27:
    """Host-owned authority: clients get opaque ids, never mutable state."""

    def __init__(self, generation_id: str | None = None) -> None:
        self._generation = generation_id or secrets.token_hex(16)
        self._sessions: dict[str, dict[str, object]] = {}

    def create(self, review_identity: str) -> ReviewRecordV27:
        session = secrets.token_hex(16)
        lease = secrets.token_hex(16)
        plan = secrets.token_hex(16)
        plan_digest = hashlib.sha256(review_identity.encode()).hexdigest()
        binding = hashlib.sha256(
            f"{self._generation}:{session}:{plan}:{plan_digest}:{lease}".encode()
        ).hexdigest()
        record = ReviewRecordV27(
            digest=hashlib.sha256(f"{review_identity}:{binding}".encode()).hexdigest(),
            host_generation_id=self._generation,
            host_session_id=session,
            live_plan_id=plan,
            live_plan_digest=plan_digest,
            host_lease_id=lease,
            binding_digest=binding,
        )
        self._sessions[session] = {"record": record, "state": State.PENDING_REVIEW, "nonce": secrets.token_hex(16), "applies": 0}
        return record

    def approval_for_test(self, record: ReviewRecordV27, root: str, child: str) -> ReviewApprovalV27:
        entry = self._sessions[record.host_session_id]
        return ReviewApprovalV27("V27", root, child, record.digest, record.host_generation_id, record.host_session_id, record.live_plan_id, record.live_plan_digest, record.host_lease_id, record.binding_digest, str(entry["nonce"]))

    def approve(self, approval: ReviewApprovalV27) -> bool:
        entry = self._sessions.get(approval.host_session_id)
        if entry is None or entry["state"] is not State.PENDING_REVIEW:
            return False
        record = entry["record"]
        assert isinstance(record, ReviewRecordV27)
        fields = (approval.record_digest, approval.host_generation_id, approval.host_session_id, approval.live_plan_id, approval.live_plan_digest, approval.host_lease_id, approval.binding_digest)
        expected = (record.digest, record.host_generation_id, record.host_session_id, record.live_plan_id, record.live_plan_digest, record.host_lease_id, record.binding_digest)
        if approval.gate != "V27" or approval.counter != 1 or approval.nonce != entry["nonce"] or fields != expected:
            entry["state"] = State.TERMINAL
            return False
        entry["nonce"] = None
        entry["state"] = State.APPROVED
        return True

    def resume_once(self, session_id: str, lease_id: str, fresh: bool = True, apply_ok: bool = True, verify_ok: bool = True) -> bool:
        entry = self._sessions.get(session_id)
        if entry is None or entry["state"] is not State.APPROVED:
            return False
        record = entry["record"]
        assert isinstance(record, ReviewRecordV27)
        if lease_id != record.host_lease_id:
            entry["state"] = State.TERMINAL
            return False
        entry["state"] = State.CONSUMING
        if not fresh:
            entry["state"] = State.TERMINAL
            return False
        entry["applies"] = int(entry["applies"]) + 1
        entry["state"] = State.TERMINAL
        return apply_ok and verify_ok

    def apply_count(self, session_id: str) -> int:
        entry = self._sessions.get(session_id)
        return 0 if entry is None else int(entry["applies"])
