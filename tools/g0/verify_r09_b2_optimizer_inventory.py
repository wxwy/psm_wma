#!/usr/bin/env python3
"""Verify P3 inventory structure without converting BLOCKED into PASS."""

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
    source = artifact.get("source", {})
    execution = artifact.get("execution", {})
    checks = {"schema": artifact.get("schema_version") == "r09_b2_optimizer_inventory_v1", "provenance": all(source.get(key) for key in ("root_revision", "submodule_revision", "gitlink_revision", "recipe_sha256", "collector_sha256", "verifier_sha256", "optimizer_source_sha256")), "no_execution": execution.get("device") == "meta" and all(not execution.get(key) for key in ("weights_loaded", "checkpoint_loaded", "forward_executed", "backward_executed", "optimizer_step_executed", "scheduler_step_executed")), "backend_records": all(artifact.get(key, {}).get("status") in {"PASS", "BLOCKED"} for key in ("recurrent", "ttt_fast_weight"))}
    result = {"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "inventory_status": artifact.get("status")}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
