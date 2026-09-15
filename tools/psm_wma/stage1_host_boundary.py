"""CPU-only fake-host conformance model for the V27 host boundary.

This module intentionally has no process, IPC, filesystem, or project I/O.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import re
import secrets
from threading import RLock


V27_GATE = "G0-R09-B-TTT-V035-HOST-OWNED-CONTINUATION-CPU-STATIC"
_IDENTITY = re.compile(r"^[a-z][a-z0-9_-]*:[^\s]+$")
_SCHEMA = (
    ("consumer_provenance", ("provider", "module", "path", "source_blob", "callable", "abi", "transport")),
    ("guard_provenance", ("provider", "module", "path", "source_blob", "callable", "abi", "transport")),
    ("verifier_provenance", ("provider", "module", "path", "source_blob", "callable", "abi", "transport")),
    ("contract_c01_c15", tuple(f"c{index:02d}" for index in range(1, 16))),
    ("freshness_domain", ("git", "config", "local_v2", "output_absence_0", "output_absence_1", "designated_absence_0", "designated_absence_1", "designated_absence_2", "designated_absence_3")),
    ("query_identities", ("stdout", "stderr", "predicate")),
    ("absence_identities", ("authority_local", "authority_remote", "designated_0", "designated_1", "designated_2", "designated_3")),
    ("replay_binding", ("base", "owner_pair", "parser_rows", "source_rows", "parser_argv")),
    ("frozen_targets", ("json", "markdown", "patch_text", "patch_raw")),
    ("descriptor_rows", tuple(f"descriptor_{index}" for index in range(8))),
    ("source_rows", tuple(f"source_{index}" for index in range(8))),
    ("argv_items", tuple(f"argv_{index}" for index in range(8))),
)


class State(str, Enum):
    PENDING_REVIEW = "PENDING_REVIEW"
    APPROVED = "APPROVED"
    CONSUMING = "CONSUMING"
    TERMINAL = "TERMINAL"


Rows = tuple[tuple[str, tuple[tuple[str, str], ...]], ...]


def _default_rows(identity: str) -> Rows:
    if not identity or not _IDENTITY.fullmatch(f"review:{identity}"):
        raise ValueError("review identity must be a non-empty single token")
    return tuple(
        (category, tuple((field, f"identity:{identity}-{category}-{field}") for field in fields))
        for category, fields in _SCHEMA
    )


def _validate_rows(rows: Rows) -> None:
    if len(rows) != len(_SCHEMA):
        raise ValueError("review record category count is fixed")
    for actual, expected in zip(rows, _SCHEMA, strict=True):
        category, fields = actual
        expected_category, expected_fields = expected
        if category != expected_category or tuple(name for name, _ in fields) != expected_fields:
            raise ValueError("review record category field grammar is fixed")
        if any(not _IDENTITY.fullmatch(value) for _, value in fields):
            raise ValueError("review record identity format is invalid")


def _digest_rows(rows: Rows) -> str:
    _validate_rows(rows)
    return hashlib.sha256(
        "\n".join(f"{category}:{name}={value}" for category, fields in rows for name, value in fields).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class ReviewRecordV27:
    authority_rows: Rows
    digest: str
    host_generation_id: str
    host_session_id: str
    live_plan_id: str
    live_plan_digest: str
    host_lease_id: str
    binding_digest: str


@dataclass(frozen=True)
class _HostSnapshotV27:
    authority_rows: Rows
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


def _record_from(snapshot: _HostSnapshotV27) -> ReviewRecordV27:
    return ReviewRecordV27(
        tuple((category, tuple(fields)) for category, fields in snapshot.authority_rows),
        snapshot.digest, snapshot.host_generation_id, snapshot.host_session_id,
        snapshot.live_plan_id, snapshot.live_plan_digest, snapshot.host_lease_id,
        snapshot.binding_digest,
    )


class FakeStage1OrchestratorV27:
    """Test-only privileged attestation harness, not a client-facing host API."""

    def __init__(self, host: "FakeStage1HostV27") -> None:
        self._host = host

    def attest(self, record: ReviewRecordV27) -> ReviewApprovalV27:
        return self._host._mint_privileged_attestation(record)


class FakeStage1HostV27:
    """Host-owned authority: returned review records are detached audit copies."""

    def __init__(self, generation_id: str | None = None, *, root: str = "root", child: str = "child") -> None:
        if not root or not child:
            raise ValueError("formal root and child must be non-empty")
        self._generation = generation_id or secrets.token_hex(16)
        self._root = root
        self._child = child
        self._sessions: dict[str, dict[str, object]] = {}
        self._lock = RLock()

    def create(self, review_identity: str | Rows) -> ReviewRecordV27:
        rows = _default_rows(review_identity) if isinstance(review_identity, str) else review_identity
        _validate_rows(rows)
        with self._lock:
            session, lease, plan = (secrets.token_hex(16) for _ in range(3))
            row_digest = _digest_rows(rows)
            plan_digest = hashlib.sha256(f"plan:{row_digest}".encode()).hexdigest()
            binding = hashlib.sha256(f"{self._generation}:{session}:{plan}:{plan_digest}:{lease}".encode()).hexdigest()
            digest = hashlib.sha256(f"{V27_GATE}:{self._root}:{self._child}:{row_digest}:{binding}".encode()).hexdigest()
            snapshot = _HostSnapshotV27(rows, digest, self._generation, session, plan, plan_digest, lease, binding)
            self._sessions[session] = {"snapshot": snapshot, "state": State.PENDING_REVIEW, "nonce": secrets.token_hex(16), "applies": 0}
            return _record_from(snapshot)

    def _matches_snapshot(self, record: ReviewRecordV27, snapshot: _HostSnapshotV27) -> bool:
        try:
            row_digest = _digest_rows(record.authority_rows)
        except ValueError:
            return False
        expected_digest = hashlib.sha256(f"{V27_GATE}:{self._root}:{self._child}:{row_digest}:{record.binding_digest}".encode()).hexdigest()
        return record == _record_from(snapshot) and row_digest == _digest_rows(snapshot.authority_rows) and expected_digest == snapshot.digest

    def _mint_privileged_attestation(self, record: ReviewRecordV27) -> ReviewApprovalV27:
        with self._lock:
            entry = self._sessions.get(record.host_session_id)
            if entry is None or entry["state"] is not State.PENDING_REVIEW:
                raise ValueError("no pending host-owned session")
            snapshot = entry["snapshot"]
            assert isinstance(snapshot, _HostSnapshotV27)
            if not self._matches_snapshot(record, snapshot):
                raise ValueError("audit record does not match host-private snapshot")
            nonce = entry["nonce"]
            assert isinstance(nonce, str)
            return ReviewApprovalV27(V27_GATE, self._root, self._child, snapshot.digest, snapshot.host_generation_id, snapshot.host_session_id, snapshot.live_plan_id, snapshot.live_plan_digest, snapshot.host_lease_id, snapshot.binding_digest, nonce)

    def approve(self, approval: ReviewApprovalV27) -> bool:
        with self._lock:
            entry = self._sessions.get(approval.host_session_id)
            if entry is None or entry["state"] is not State.PENDING_REVIEW:
                return False
            snapshot = entry["snapshot"]
            assert isinstance(snapshot, _HostSnapshotV27)
            fields = (approval.gate, approval.root, approval.child, approval.record_digest, approval.host_generation_id, approval.host_session_id, approval.live_plan_id, approval.live_plan_digest, approval.host_lease_id, approval.binding_digest)
            expected = (V27_GATE, self._root, self._child, snapshot.digest, snapshot.host_generation_id, snapshot.host_session_id, snapshot.live_plan_id, snapshot.live_plan_digest, snapshot.host_lease_id, snapshot.binding_digest)
            if approval.counter != 1 or approval.nonce != entry["nonce"] or fields != expected:
                entry["state"] = State.TERMINAL
                return False
            entry["nonce"] = None
            entry["state"] = State.APPROVED
            return True

    def resume_once(self, session_id: str, lease_id: str, *, fresh: bool = True, apply_ok: bool = True, verify_ok: bool = True) -> bool:
        with self._lock:
            entry = self._sessions.get(session_id)
            if entry is None or entry["state"] is not State.APPROVED:
                return False
            snapshot = entry["snapshot"]
            assert isinstance(snapshot, _HostSnapshotV27)
            if lease_id != snapshot.host_lease_id or snapshot.host_generation_id != self._generation:
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
