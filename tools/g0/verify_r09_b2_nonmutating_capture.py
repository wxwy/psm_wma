#!/usr/bin/env python3
"""Verify the CPU-only R09-B2 P2 isolation-contract artifact."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text())
    required = {"parameters", "buffers", "optimizer", "scheduler", "batch_metadata", "recurrent_state", "ttt_state"}
    mutations = artifact.get("mutation_checks", {})
    source = artifact.get("source", {})
    checks = {
        "schema": artifact.get("schema_version") == "r09_b2_nonmutating_capture_cpu_v3",
        "required_cases": required == set(mutations),
        "actual_callback_entrypoint": all(mutations.get(key, {}).get("callback_entrypoint") for key in required),
        "all_cases_rejected": all(mutations.get(key, {}).get("rejected") for key in required),
        "provenance": all(isinstance(source.get(key), str) and source[key] for key in ("root_revision", "submodule_revision", "gitlink_revision", "collector_sha256", "verifier_sha256", "capture_source_sha256")),
    }
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
