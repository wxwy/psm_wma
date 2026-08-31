#!/usr/bin/env python3
"""Verify P3 inventory structure without converting BLOCKED into PASS."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def inventory_checks(record: dict[str, object]) -> dict[str, bool]:
    """Validate every membership claim required before a backend may be PASS."""
    inventory = record.get("inventory", {})
    rows = inventory.get("model_parameters", [])
    names = [row.get("name") for row in rows]
    selected = {row.get("name") for row in rows if row.get("selected_by_optimizer")}
    groups = inventory.get("optimizer_param_groups", [])
    grouped = [name for group in groups for name in group.get("parameter_names", [])]
    ttt_names = {"W", "pending_evidence", "last_evidence", "initialized", "segment_progress"}
    dcp = inventory.get("dcp_state", {})
    return {
        "unique_model_names": len(names) == len(set(names)),
        "groups_reverse_map": all(name in set(names) for name in grouped),
        "groups_unique": len(grouped) == len(set(grouped)),
        "selected_equals_groups": selected == set(grouped),
        "group_metadata": all("lr" in group and "weight_decay" in group for group in groups),
        "ttt_dynamic_excluded": not any(name.split(".")[-1] in ttt_names for name in names + [row.get("name", "") for row in inventory.get("named_buffers", [])]),
        "dcp_inspected": dcp.get("inspected") is True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    artifact = json.loads(args.artifact.read_text())
    source = artifact.get("source", {})
    execution = artifact.get("execution", {})
    backends = {name: artifact.get(name, {}) for name in ("recurrent", "ttt_fast_weight")}
    checks = {"schema": artifact.get("schema_version") == "r09_b2_optimizer_inventory_v1", "provenance": all(source.get(key) for key in ("root_revision", "submodule_revision", "gitlink_revision", "recipe_sha256", "collector_sha256", "verifier_sha256", "optimizer_source_sha256", "sft_config_source_sha256", "model_source_sha256")), "no_execution": execution.get("device") == "meta" and all(not execution.get(key) for key in ("weights_loaded", "checkpoint_loaded", "forward_executed", "backward_executed", "optimizer_step_executed", "scheduler_step_executed")), "backend_records": all(record.get("status") in {"PASS", "BLOCKED"} for record in backends.values())}
    backend_checks = {name: inventory_checks(record) for name, record in backends.items()}
    pass_ready = all(all(item.values()) for item in backend_checks.values())
    record_valid = all(checks.values()) and (artifact.get("status") != "PASS" or pass_ready)
    status = "PASS" if artifact.get("status") == "PASS" and record_valid else artifact.get("status", "FAIL")
    result = {"status": status, "record_valid": record_valid, "checks": checks, "backend_checks": backend_checks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    if not result["record_valid"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
