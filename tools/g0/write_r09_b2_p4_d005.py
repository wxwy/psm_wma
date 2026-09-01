#!/usr/bin/env python3
"""Build a non-executable R09-B2 P4 launch D005; never launches its argv."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path


SCHEMA = "r09_b2_p4_launch_d005_v2"
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


def write_record(record: dict[str, object], output: Path, *, root: Path, peer: dict[str, object]) -> None:
    """Write only a pair-verified non-executable record; no runtime imports or execution."""
    if record.get("status") != "FROZEN_NOT_EXECUTED" or record.get("command", {}).get("executable") is not False:
        raise ValueError("P4 D005 must be FROZEN_NOT_EXECUTED and non-executable")
    from tools.g0.verify_r09_b2_p4_d005 import verify_pair

    backend = record.get("backend")
    if backend not in {"recurrent", "ttt_fast_weight"}:
        raise ValueError(f"unknown P4 backend: {backend}")
    result = verify_pair(record if backend == "recurrent" else peer, record if backend == "ttt_fast_weight" else peer, root.resolve())
    if result["status"] != "PASS":
        raise ValueError("refusing to write a D005 record that fails the complete static pair contract")
    output = output.resolve()
    if output.exists():
        raise ValueError(f"refusing to overwrite existing D005 output: {output}")
    try:
        relative = output.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"D005 output must be rooted in repository: {output}") from exc
    if subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(relative)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        raise ValueError(f"refusing to write Git-tracked D005 output: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical_bytes(finalize(record)))


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", type=Path, required=True, help="prebuilt non-executable JSON input")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--peer", type=Path, required=True)
    args = parser.parse_args()
    write_record(json.loads(args.record.read_text()), args.output, root=args.root, peer=json.loads(args.peer.read_text()))


if __name__ == "__main__":
    main()
