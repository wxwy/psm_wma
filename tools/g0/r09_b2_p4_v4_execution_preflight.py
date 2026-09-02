"""P4-v4 execution-preflight entry foundation; no execution is authorized here."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def request_sha256(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise ValueError("execution request must be a regular file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args(argv)
    if request_sha256(args.request) != args.request_sha256:
        raise ValueError("execution request SHA256 differs")
    raise RuntimeError("P4-v4 execution requires a separately reviewed frozen execution request")


if __name__ == "__main__":
    main()
