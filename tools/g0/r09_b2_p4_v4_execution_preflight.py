"""P4-v4 execution-preflight entry foundation; no execution is authorized here."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path


REQUEST_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "run", "candidates",
    "backends", "authorities", "execution_contract",
}
ENTRY_KEYS = {"tool_path", "root_revision", "git_blob_sha256", "current_sha256", "identity_sha256"}
ENTRY_TOOL_PATH = "tools/g0/r09_b2_p4_v4_execution_preflight.py"
_GIT_REVISION = re.compile(r"[0-9a-f]{40}\Z")
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_EXECUTION_CONTRACT_ITEMS = (
    ("network", False),
    ("gpu", False),
    ("torch", False),
    ("model_data_checkpoint_io", False),
    ("one_shot", True),
    ("cleanup_retry_repair", False),
)


def read_execution_request(path: Path) -> bytes:
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValueError("execution request requires O_NOFOLLOW")
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("execution request must be a regular file")
        with os.fdopen(descriptor, "rb") as request_file:
            descriptor = -1
            return request_file.read()
    finally:
        if descriptor != -1:
            os.close(descriptor)


def load_execution_request(
    raw: bytes,
    _execution_contract_items: tuple[tuple[str, bool], ...] = _EXECUTION_CONTRACT_ITEMS,
) -> dict[str, object]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("execution request is not JSON") from exc
    canonical = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if not isinstance(value, dict) or raw != canonical:
        raise ValueError("execution request is not canonical JSON")
    if set(value) != REQUEST_KEYS or value.get("schema_version") != "r09_b2_p4_v4_execution_request_v1":
        raise ValueError("execution request schema differs")
    if not all(isinstance(value[key], dict) for key in REQUEST_KEYS - {"schema_version"}):
        raise ValueError("execution request section differs")
    if value["execution_contract"] != dict(_execution_contract_items):
        raise ValueError("execution request contract differs")
    validate_entry(value["entry"])
    return value


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
    ).hexdigest()


def validate_entry(value: object) -> None:
    if not isinstance(value, dict) or set(value) != ENTRY_KEYS or not all(
        isinstance(item, str) for item in value.values()
    ):
        raise ValueError("execution request entry schema differs")
    if value["tool_path"] != ENTRY_TOOL_PATH:
        raise ValueError("execution request entry path differs")
    if _GIT_REVISION.fullmatch(value["root_revision"]) is None or any(
        _SHA256.fullmatch(value[key]) is None
        for key in ("git_blob_sha256", "current_sha256", "identity_sha256")
    ):
        raise ValueError("execution request entry digest differs")
    identity = {key: item for key, item in value.items() if key != "identity_sha256"}
    if value["identity_sha256"] != canonical_sha256(identity):
        raise ValueError("execution request entry identity differs")


def request_sha256(raw: bytes) -> str:
    if not isinstance(raw, bytes):
        raise ValueError("execution request must be a regular file")
    return hashlib.sha256(raw).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args(argv)
    raw = read_execution_request(args.request)
    if request_sha256(raw) != args.request_sha256:
        raise ValueError("execution request SHA256 differs")
    load_execution_request(raw)
    raise RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")


if __name__ == "__main__":
    main()
