"""Static-only P4-v4 candidate publication contract; never materializes a run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from tools.g0.export_r09_b2_p5_resolved_config import P4_V4_BACKENDS, canonical_bytes


PAYLOAD_FILES = ("request.json", "result.json", "verification.json")
LINK_KEYS = {"schema_version", "backend", "attempt_id", "run_token", "payload_sha256"}
FAILURE_KEYS = {"schema_version", "backend", "attempt_id", "run_token", "status", "stage", "error_type", "error"}


def _canonical(path: Path) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"candidate entry must be a regular file: {path.name}")
    raw = path.read_bytes()
    value = json.loads(raw)
    if not isinstance(value, dict) or canonical_bytes(value) != raw:
        raise ValueError(f"candidate entry is not canonical JSON: {path.name}")
    return value, raw


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_pass_candidate(candidate: Path, backend: str) -> dict[str, bytes]:
    if backend not in P4_V4_BACKENDS or candidate.name != backend:
        raise ValueError("candidate backend directory differs")
    if {entry.name for entry in candidate.iterdir()} != {*PAYLOAD_FILES, "candidate_link.json"}:
        raise ValueError("PASS candidate file set differs")
    payload = {name: _canonical(candidate / name)[1] for name in PAYLOAD_FILES}
    link, _ = _canonical(candidate / "candidate_link.json")
    if (set(link) != LINK_KEYS or link["schema_version"] != "r09_b2_p4_v4_candidate_link_v1"
            or link["backend"] != backend or link["attempt_id"] != candidate.parent.name
            or not isinstance(link["run_token"], str) or len(link["run_token"]) != 64
            or link["payload_sha256"] != {name: _sha(payload[name]) for name in PAYLOAD_FILES}):
        raise ValueError("PASS candidate link differs")
    request = json.loads(payload["request.json"])
    token = request.get("p4_run", {}).get("run_token") if isinstance(request.get("p4_run"), dict) else None
    if (request.get("backend") != backend or token != link["run_token"]
            or {"attempt_id", "run_token"} & set(request)):
        raise ValueError("PASS candidate payload binding differs")
    return payload


def verify_fail_candidate(candidate: Path, backend: str) -> None:
    if {entry.name for entry in candidate.iterdir()} != {"request.json", "failure.json"}:
        raise ValueError("FAIL candidate file set differs")
    failure, _ = _canonical(candidate / "failure.json")
    if (set(failure) != FAILURE_KEYS or failure["backend"] != backend or failure["attempt_id"] != candidate.parent.name
            or failure["status"] != "FAIL" or failure["stage"] not in {"admission", "materialize", "final_verify"}):
        raise ValueError("FAIL candidate schema differs")


def stage_atomic_publication(candidates: Path) -> dict[str, dict[str, bytes]]:
    if {entry.name for entry in candidates.iterdir()} != set(P4_V4_BACKENDS):
        raise ValueError("candidate backend set differs")
    return {backend: load_pass_candidate(candidates / backend, backend) for backend in P4_V4_BACKENDS}
