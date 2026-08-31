#!/usr/bin/env python3
"""Verify that R09-B2 P0 records its unresolved execution blockers honestly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.input.read_text())
    checks = {
        "schema_exact": evidence.get("schema_version") == "r09_b2_matched_training_preflight_p0_v1",
        "source_complete": set(evidence.get("source", {})) == {"root_revision", "submodule_revision", "gitlink_revision"},
        "resolved_backend_pair_exact": evidence.get("recurrent", {}).get("local_history_backend") == "recurrent" and evidence.get("ttt_fast_weight", {}).get("local_history_backend") == "ttt_fast_weight",
        "selected_differences_allowed_only": evidence.get("resolved_config_contract", {}).get("selected_field_diff_allowed_only") is True,
        "complete_resolved_config_explicitly_blocked": evidence.get("resolved_config_contract", {}).get("complete_resolved_config_diff_present") is False,
        "same_step_budget": evidence.get("checks", {}).get("same_step_budget") is True,
        "same_microbatch_and_accumulation": evidence.get("checks", {}).get("same_microbatch_and_accumulation") is True,
        "stream_manifest_explicitly_blocked": evidence.get("stream_contract", {}).get("enforceable_by_current_dataset") is False,
        "capture_explicitly_blocked": evidence.get("capture_contract", {}).get("non_mutating_implementation_present") is False,
        "optimizer_membership_explicitly_blocked": evidence.get("optimizer_contract", {}).get("actual_parameter_membership_present") is False,
        "launch_budget_explicitly_blocked": evidence.get("launch_contract", {}).get("exact_argv_present") is False
        and evidence.get("launch_contract", {}).get("sanitized_environment_present") is False,
        "status_honestly_blocked": evidence.get("status") == "BLOCKED",
    }
    result = {
        "schema_version": "r09_b2_preflight_verifier_v1",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "input": str(args.input),
        "blockers": evidence.get("blockers", []),
        "next_gate": "需要单独实现可强制 window-ID manifest 与 non-mutating capture，之后重做 P0 审核。",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "checks": checks}, sort_keys=True))


if __name__ == "__main__":
    main()
