"""CPU-only fake-host conformance model for the V27 host boundary.

This module intentionally has no process, IPC, filesystem, or project I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import secrets
from threading import RLock


V27_GATE = "G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC"
_RECORD_CATEGORIES = (
    "consumer_provenance", "guard_provenance", "verifier_provenance",
    "contract_c01_c15", "freshness_domain", "query_identities",
    "absence_identities", "replay_binding", "frozen_targets",
    "descriptor_rows", "source_rows", "argv_items",
)


class State(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    CONSUMING = "CONSUMING"
    TERMINAL = "TERMINAL"


def _digest_rows(rows: tuple[tuple[str, tuple[str, ...]], ...]) -> str:
    return hashlib.sha256(
        "\n".join(f"{name}:{'|'.join(values)}" for name, values in rows).encode("utf-8")
    ).hexdigest()


def _default_rows(identity: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    if not identity:
        raise ValueError("review identity must be non-empty")
    return tuple((name, (f"{identity}:{index}",)) for index, name in enumerate(_RECORD_CATEGORIES))


def _validate_rows(rows: tuple[tuple[str, tuple[str, ...]], ...]) -> None:
    if tuple(name for name, _ in rows) != _RECORD_CATEGORIES:
        raise ValueError("review record categories must be exact and ordered")
    for _, values in rows:
        if not values or any(not isinstance(value, str) or not value for value in values):
            raise ValueError("review record fields must be non-empty strings")


@dataclass(frozen=True)
class ReviewRecordV27:
    authority_rows: tuple[tuple[str, tuple[str, ...]], ...]
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


class FakeStage1OrchestratorV27:
    """Test-only privileged attestation harness, not a client-facing host API."""

    def __init__(self, host: "FakeStage1HostV27") -> None:
        self._host = host

    def attest(self, record: ReviewRecordV27) -> ReviewApprovalV27:
        return self._host._mint_privileged_attestation(record)


class FakeStage1HostV27:
    """Host-owned authority: clients get opaque ids, never approval material."""

    def __init__(self, generation_id: str | None = None, *, root: str = "root", child: str = "child") -> None:
        if not root or not child:
            raise ValueError("formal root and child must be non-empty")
        self._generation = generation_id or secrets.token_hex(16)
        self._root = root
        self._child = child
        self._sessions: dict[str, dict[str, object]] = {}
        self._lock = RLock()

    def create(self, review_identity: str | tuple[tuple[str, tuple[str, ...]], ...]) -> ReviewRecordV27:
        rows = _default_rows(review_identity) if isinstance(review_identity, str) else review_identity
        _validate_rows(rows)
        with self._lock:
            session, lease, plan = (secrets.token_hex(16) for _ in range(3))
            row_digest = _digest_rows(rows)
            plan_digest = hashlib.sha256(f"plan:{row_digest}".encode()).hexdigest()
            binding = hashlib.sha256(
                f"{self._generation}:{session}:{plan}:{plan_digest}:{lease}".encode()
            ).hexdigest()
            digest = hashlib.sha256(
                f"{V27_GATE}:{self._root}:{self._child}:{row_digest}:{binding}".encode()
            ).hexdigest()
            record = ReviewRecordV27(rows, digest, self._generation, session, plan, plan_digest, lease, binding)
            self._sessions[session] = {
                "record": record, "state": State.PENDING_REVIEW,
                "nonce": secrets.token_hex(16), "applies": 0,
            }
            return record

    def _mint_privileged_attestation(self, record: ReviewRecordV27) -> ReviewApprovalV27:
        with self._lock:
            entry = self._sessions.get(record.host_session_id)
            if entry is None or entry["record"] != record or entry["state"] is not State.PENDING_REVIEW:
                raise ValueError("no pending host-owned session")
            nonce = entry["nonce"]
            assert isinstance(nonce, str)
            return ReviewApprovalV27(
                V27_GATE, self._root, self._child, record.digest,
                record.host_generation_id, record.host_session_id, record.live_plan_id,
                record.live_plan_digest, record.host_lease_id, record.binding_digest, nonce,
            )

    def approve(self, approval: ReviewApprovalV27) -> bool:
        with self._lock:
            entry = self._sessions.get(approval.host_session_id)
            if entry is None or entry["state"] is not State.PENDING_REVIEW:
                return False
            record = entry["record"]
            assert isinstance(record, ReviewRecordV27)
            fields = (
                approval.gate, approval.root, approval.child, approval.record_digest,
                approval.host_generation_id, approval.host_session_id, approval.live_plan_id,
                approval.live_plan_digest, approval.host_lease_id, approval.binding_digest,
            )
            expected = (
                V27_GATE, self._root, self._child, record.digest,
                record.host_generation_id, record.host_session_id, record.live_plan_id,
                record.live_plan_digest, record.host_lease_id, record.binding_digest,
            )
            if approval.counter != 1 or approval.nonce != entry["nonce"] or fields != expected:
                entry["state"] = State.TERMINAL
                return False
            entry["nonce"] = None
            entry["state"] = State.APPROVED
            return True

    def resume_once(
        self, session_id: str, lease_id: str, *, fresh: bool = True,
        apply_ok: bool = True, verify_ok: bool = True,
    ) -> bool:
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None or entry["state"] is not State.APPROVED:
                return False
            record = entry["record"]
            assert isinstance(record, ReviewRecordV27)
            if lease_id != record.host_lease_id:
                entry["state"] = State.TERMINAL
                return False
            entry["state"] = State.CONSUMING
        if not fresh or not apply_ok:
            with self._lock:
                entry["state"] = State.TERMINAL
            return False
        with self._lock:
            entry["applies"] = int(entry["applies"]) + 1
            entry["state"] = State.TERMINAL
        return verify_ok

    def apply_count(self, session_id: str) -> int:
        with self._lock:
            entry = self._sessions.get(session_id)
            return 0 if entry is None else int(entry["applies"])

    def state(self, session_id: str) -> State | None:
        with self._lock:
            entry = self._sessions.get(session_id)
            return None if entry is None else entry["state"]  # type: ignore[return-value]


def mutate(approval: ReviewApprovalV27, **changes: object) -> ReviewApprovalV27:
    """Test helper for untrusted-payload drift witnesses."""
    return replace(approval, **changes)
