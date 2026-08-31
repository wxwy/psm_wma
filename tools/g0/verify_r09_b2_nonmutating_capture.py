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
    required = {"normal_clone", "zero_clone", "shuffle_clone", "rng_exception_restored", "snapshot_mutation_detected", "canonical_model_untouched"}
    checks = {
        "schema": artifact.get("schema_version") == "r09_b2_nonmutating_capture_cpu_v1",
        "required_cases": required <= set(artifact.get("checks", {})),
        "all_cases": all(artifact.get("checks", {}).get(key) is True for key in required),
    }
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
