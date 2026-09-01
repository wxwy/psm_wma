#!/usr/bin/env python3
"""Build a non-executable R09-B2 P4 launch D005; never launches its argv."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


SCHEMA = "r09_b2_p4_launch_d005_v1"
TOML_RELATIVE = "examples/toml/sft_config/action_policy_libero_edge_all.toml"


def canonical_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sha256_json(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def membership_sha256(p3: dict[str, object], backend: str) -> str:
    rows = p3[backend]["inventory"]["model_parameters"]
    names = sorted(row["name"] for row in rows if row["selected_by_optimizer"])
    return sha256_json(names)


def derive_job_path(output_root: str, identity: dict[str, str]) -> str:
    return str(Path(output_root) / identity["project"] / identity["group"] / identity["name"])


def finalize(record: dict[str, object]) -> dict[str, object]:
    result = dict(record)
    result.pop("d005_sha256", None)
    result["d005_sha256"] = sha256_json(result)
    return result


def write_record(record: dict[str, object], output: Path) -> None:
    """Write only a verified non-executable record; no runtime imports or execution."""
    if record.get("status") != "FROZEN_NOT_EXECUTED" or record.get("command", {}).get("executable") is not False:
        raise ValueError("P4 D005 must be FROZEN_NOT_EXECUTED and non-executable")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(finalize(record)))


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True, help="prebuilt non-executable JSON input")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_record(json.loads(args.record.read_text()), args.output)


if __name__ == "__main__":
    main()
