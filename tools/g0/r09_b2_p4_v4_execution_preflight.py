"""P4-v4 execution-preflight entry foundation; no execution is authorized here."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


REQUEST_KEYS = {
    "schema_version", "entry", "source", "interpreter", "environment", "run", "candidates",
    "backends", "authorities", "execution_contract",
}
EXECUTION_CONTRACT = {
    "network": False,
    "gpu": False,
    "torch": False,
    "model_data_checkpoint_io": False,
    "one_shot": True,
    "cleanup_retry_repair": False,
}

def request_sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("execution request must be a regular file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_execution_request(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
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
    if value["execution_contract"] != EXECUTION_CONTRACT:
        raise ValueError("execution request contract differs")
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args(argv)
    if request_sha256(args.request) != args.request_sha256:
        raise ValueError("execution request SHA256 differs")
    load_execution_request(args.request)
    raise RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")


if __name__ == "__main__":
    main()
