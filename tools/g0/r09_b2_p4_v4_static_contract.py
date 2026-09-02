"""Static-only P4-v4 candidate publication contract; never materializes a run."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from tools.g0.export_r09_b2_p5_resolved_config import (
    P4_V4_BACKENDS, P4_V4_PREFLIGHT_RELATIVE, _path_identity, _validate_source,
    canonical_bytes, load_p4_v4_preflight,
)


PAYLOAD_FILES = ("request.json", "result.json", "verification.json")
LINK_KEYS = {"schema_version", "backend", "attempt_id", "run_token", "payload_sha256"}
FAILURE_KEYS = {"schema_version", "backend", "attempt_id", "run_token", "status", "stage", "error_type", "error"}
REQUEST_KEYS = {"schema_version", "backend", "production_source", "p4_run", "p4_staging", "request_defaults", "interpreter", "loader_argv", "effective_environment", "native_loader_environment", "payload_manifest", "producer"}


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


def _token(value: object) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError("candidate run token must be 64 lowercase hexadecimal characters")
    return value


def _candidate_directory(candidate: Path, backend: str) -> None:
    if (backend not in P4_V4_BACKENDS or candidate.name != backend or candidate.is_symlink()
            or candidate.parent.is_symlink() or candidate.parent.parent.is_symlink()
            or not candidate.is_dir() or not candidate.parent.is_dir()):
        raise ValueError("candidate backend directory differs or is not canonical")


def _fail_request(candidate: Path, backend: str) -> tuple[str, str]:
    request, _ = _canonical(candidate / "request.json")
    run = request.get("p4_run")
    if set(request) != REQUEST_KEYS or request.get("backend") != backend or not isinstance(run, dict):
        raise ValueError("FAIL candidate request schema differs")
    if set(run) != {"identity", "run_token", "roster_sha256"}:
        raise ValueError("FAIL candidate request run binding differs")
    token = _token(run["run_token"])
    run_root = _path_identity(run["identity"], kind="run_root")
    _validate_source(request["production_source"])
    return token, str(run_root)


def load_pass_candidate(candidate: Path, backend: str) -> dict[str, bytes]:
    _candidate_directory(candidate, backend)
    if {entry.name for entry in candidate.iterdir()} != {*PAYLOAD_FILES, "candidate_link.json"}:
        raise ValueError("PASS candidate file set differs")
    payload = {name: _canonical(candidate / name)[1] for name in PAYLOAD_FILES}
    link, _ = _canonical(candidate / "candidate_link.json")
    if (set(link) != LINK_KEYS or link["schema_version"] != "r09_b2_p4_v4_candidate_link_v1"
            or link["backend"] != backend or link["attempt_id"] != candidate.parent.name
            or not isinstance(link["run_token"], str)
            or link["payload_sha256"] != {name: _sha(payload[name]) for name in PAYLOAD_FILES}):
        raise ValueError("PASS candidate link differs")
    _token(link["run_token"])
    request = json.loads(payload["request.json"])
    token = request.get("p4_run", {}).get("run_token") if isinstance(request.get("p4_run"), dict) else None
    if (request.get("backend") != backend or token != link["run_token"]
            or {"attempt_id", "run_token"} & set(request)):
        raise ValueError("PASS candidate payload binding differs")
    return payload


def verify_fail_candidate(candidate: Path, backend: str) -> tuple[str, str]:
    _candidate_directory(candidate, backend)
    if {entry.name for entry in candidate.iterdir()} != {"request.json", "failure.json"}:
        raise ValueError("FAIL candidate file set differs")
    token, run_root = _fail_request(candidate, backend)
    failure, _ = _canonical(candidate / "failure.json")
    if (set(failure) != FAILURE_KEYS or failure["schema_version"] != "r09_b2_p4_v4_candidate_failure_v1"
            or failure["backend"] != backend or failure["attempt_id"] != candidate.parent.name
            or failure["run_token"] != token or failure["status"] != "FAIL"
            or failure["stage"] not in {"admission", "materialize", "final_verify"}
            or not all(isinstance(failure[key], str) and failure[key] for key in ("error_type", "error"))):
        raise ValueError("FAIL candidate schema differs")
    return token, run_root


def _reject_failed_identity_reuse(candidates: Path, payloads: dict[str, dict[str, bytes]]) -> None:
    candidate_root = candidates.parent
    if candidate_root.is_symlink() or not candidate_root.is_dir():
        raise ValueError("candidate root is not canonical")
    admitted = {
        (backend, _token(json.loads(payload["request.json"])["p4_run"]["run_token"]), str(_path_identity(
            json.loads(payload["request.json"])["p4_run"]["identity"], kind="run_root",
        )))
        for backend, payload in payloads.items()
    }
    for attempt in candidate_root.iterdir():
        if attempt.is_symlink() or not attempt.is_dir():
            raise ValueError("candidate history attempt is not a canonical directory")
        for backend in P4_V4_BACKENDS:
            candidate = attempt / backend
            if candidate.exists() and (candidate / "failure.json").exists():
                token, run_root = verify_fail_candidate(candidate, backend)
                if any(item[0] == backend and (item[1] == token or item[2] == run_root) for item in admitted):
                    raise ValueError("failed candidate token/run-root identity is permanently poisoned")


def _validate_final_pair(payloads: dict[str, dict[str, bytes]]) -> None:
    """Reuse the verifier-owned final P4-v4 grammar on byte-preserved temporary paths."""
    with tempfile.TemporaryDirectory() as temporary:
        evidence_root = Path(temporary)
        for backend in P4_V4_BACKENDS:
            directory = evidence_root / P4_V4_PREFLIGHT_RELATIVE / backend
            directory.mkdir(parents=True)
            for filename in PAYLOAD_FILES:
                (directory / filename).write_bytes(payloads[backend][filename])
        loaded = load_p4_v4_preflight(evidence_root)
        for backend in P4_V4_BACKENDS:
            for filename, key in zip(PAYLOAD_FILES, ("request", "result", "verification"), strict=True):
                if canonical_bytes(loaded[backend][key]) != payloads[backend][filename]:
                    raise ValueError("final P4-v4 verifier changed candidate payload bytes")
        recurrent, ttt = loaded["recurrent"]["request"], loaded["ttt_fast_weight"]["request"]
        if (recurrent["production_source"] != ttt["production_source"]
                or recurrent["request_defaults"] != ttt["request_defaults"]
                or recurrent["interpreter"] != ttt["interpreter"]):
            raise ValueError("P4-v4 pair shared source/default/interpreter differs")
        for key in ("cwd", "toml", "overrides", "interpreter", "loader_argv", "runtime_sys_path"):
            if recurrent.get("effective_launch", {}).get(key) != ttt.get("effective_launch", {}).get(key):
                raise ValueError("P4-v4 pair effective launch differs")


def stage_atomic_publication(candidates: Path) -> dict[str, dict[str, bytes]]:
    if candidates.is_symlink() or not candidates.is_dir() or {entry.name for entry in candidates.iterdir()} != set(P4_V4_BACKENDS):
        raise ValueError("candidate backend set differs")
    payloads = {backend: load_pass_candidate(candidates / backend, backend) for backend in P4_V4_BACKENDS}
    _reject_failed_identity_reuse(candidates, payloads)
    _validate_final_pair(payloads)
    return payloads
