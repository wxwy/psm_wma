#!/usr/bin/env python3
"""Fail-closed pair verifier for future R09-B2 P5 static config envelopes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.g0.export_r09_b2_p5_resolved_config import SCHEMA
from tools.g0.verify_r09_b2_p4_d005 import P3_VERIFIER_SHA256, _load_frozen_inputs, _p3_contract, sha256_json

P4_DIR = Path("artifacts/g0/r09/b2/p4_launch_d005")


def _pointer(token: str) -> str:
    return token.replace("~", "~0").replace("/", "~1")


def diff_paths(left: Any, right: Any, path: str = "") -> dict[str, tuple[Any, Any]]:
    if type(left) is not type(right):
        return {path or "/": (left, right)}
    if isinstance(left, dict):
        result: dict[str, tuple[Any, Any]] = {}
        for key in sorted(set(left) | set(right)):
            child = f"{path}/{_pointer(key)}"
            if key not in left or key not in right:
                result[child] = (left.get(key), right.get(key))
            else:
                result.update(diff_paths(left[key], right[key], child))
        return result
    if isinstance(left, list):
        if len(left) != len(right):
            return {path or "/": (left, right)}
        result: dict[str, tuple[Any, Any]] = {}
        for index, (a, b) in enumerate(zip(left, right, strict=True)):
            result.update(diff_paths(a, b, f"{path}/{index}"))
        return result
    return {} if left == right else {path or "/": (left, right)}


def _contract(envelope: Mapping[str, Any]) -> Mapping[str, Any]:
    return envelope["effective_launch"]["p1_p3_d005_bindings"]["p3_inventory"]["backend_contract"]


def _p3_checks(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], contracts: Mapping[str, Any]) -> bool:
    try:
        common = ("p3_inventory_path", "p3_inventory_sha256", "p3_verifier_sha256")
        rp, tp = recurrent["provenance"]["inputs"], ttt["provenance"]["inputs"]
        if any(rp[key] != tp[key] for key in common): return False
        return (_contract(recurrent) == contracts["recurrent"] and _contract(ttt) == contracts["ttt_fast_weight"])
    except (KeyError, TypeError):
        return False


def _allowed(path: str, left: Any, right: Any, contracts: Mapping[str, Any]) -> bool:
    fixed = {
        "/provenance/inputs/p4_record_sha256",
        "/effective_launch/environment/set/IMAGINAIRE_OUTPUT_ROOT",
        "/effective_launch/environment/effective/IMAGINAIRE_OUTPUT_ROOT",
        "/effective_launch/derived_job_path_local",
    }
    p3 = "/effective_launch/p1_p3_d005_bindings/p3_inventory/backend_contract/"
    if path == "/backend":
        return left == "recurrent" and right == "ttt_fast_weight"
    if path in {"/effective_launch/environment/set/PSM_R09_B1_TTT_ENABLED", "/effective_launch/environment/effective/PSM_R09_B1_TTT_ENABLED"}:
        return left == "0" and right == "1"
    if path == "/resolved_config/model/config/local_history_backend":
        return left == "recurrent" and right == "ttt_fast_weight"
    if path in fixed or path == p3 + "optimizer_membership_sha256":
        return True
    if path == p3 + "selector_keys":
        return left == contracts["recurrent"]["selector_keys"] and right == contracts["ttt_fast_weight"]["selector_keys"]
    if path.startswith(p3 + "selector_keys/"):
        return left in contracts["recurrent"]["selector_keys"] or right in contracts["ttt_fast_weight"]["selector_keys"]
    selector_path = "/resolved_config/optimizer/keys_to_select"
    if path == selector_path:
        return left == contracts["recurrent"]["selector_keys"] and right == contracts["ttt_fast_weight"]["selector_keys"]
    if path.startswith(selector_path + "/"):
        values = set(contracts["recurrent"]["selector_keys"]) | set(contracts["ttt_fast_weight"]["selector_keys"])
        return left in values or right in values
    return False


def _expected(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    p1, p3 = _load_frozen_inputs(root)
    records = {backend: json.loads((root / P4_DIR / f"{backend}.json").read_text()) for backend in ("recurrent", "ttt_fast_weight")}
    contracts = {backend: _p3_contract(p3, backend) for backend in records}
    return records, contracts


def _bound(envelope: Mapping[str, Any], record: Mapping[str, Any], contract: Mapping[str, Any]) -> bool:
    try:
        required = {"schema_version", "backend", "provenance", "effective_launch", "resolved_config"}
        if set(envelope) != required or envelope["provenance"]["production_source"] != record["source"]:
            return False
        launch = envelope["effective_launch"]
        inputs = envelope["provenance"]["inputs"]
        command = launch["command"]
        environment = launch["environment"]
        expected_digest = sha256_json({key: value for key, value in record.items() if key != "d005_sha256"})
        return (set(command) == {"argv", "cwd", "interpreter", "toml", "trailing_overrides"}
                and command["argv"] == record["command"]["argv"] and command["cwd"] == record["command"]["cwd"]
                and command["interpreter"] == record["command"]["interpreter"]
                and command["toml"] == "examples/toml/sft_config/action_policy_libero_edge_all.toml"
                and command["trailing_overrides"] == ["trainer.max_iter=100", "trainer.save_zero_checkpoint=true"]
                and environment["set"] == record["environment"]["set"] and environment["unset"] == record["environment"]["unset"]
                and environment["inherit_allowlist"] == record["environment"]["inherit_allowlist"] and environment["effective"] == record["environment"]["set"]
                and launch["world_size"] == record["budget"]["world_size"] and launch["budget"] == record["budget"]
                and launch["p1_p3_d005_bindings"]["p1_manifest"] == record["inputs"]["p1_manifest"]
                and launch["p1_p3_d005_bindings"]["p3_inventory"] == record["inputs"]["p3_inventory"]
                and launch["derived_job_path_local"] == record["outputs"]["run_root"]
                and inputs["p4_record_sha256"] == expected_digest and inputs["p3_inventory_path"] == record["inputs"]["p3_inventory"]["path"]
                and inputs["p3_inventory_sha256"] == record["inputs"]["p3_inventory"]["sha256"] and inputs["p3_verifier_sha256"] == P3_VERIFIER_SHA256
                and envelope["resolved_config"]["model"]["config"]["local_history_backend"] == ("ttt_fast_weight" if record["backend"] == "ttt_fast_weight" else "recurrent")
                and envelope["resolved_config"]["optimizer"]["keys_to_select"] == contract["selector_keys"])
    except (KeyError, TypeError):
        return False


def verify_pair(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], root: Path) -> dict[str, Any]:
    try:
        records, contracts = _expected(root.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return {"schema_version": SCHEMA + "_verifier", "status": "FAIL", "error": str(exc), "checks": {}}
    checks = {
        "schema": all(item.get("schema_version") == SCHEMA for item in (recurrent, ttt)),
        "backend": recurrent.get("backend") == "recurrent" and ttt.get("backend") == "ttt_fast_weight",
        "recurrent_bound": _bound(recurrent, records["recurrent"], contracts["recurrent"]),
        "ttt_bound": _bound(ttt, records["ttt_fast_weight"], contracts["ttt_fast_weight"]),
        "p3_common_and_contract": _p3_checks(recurrent, ttt, contracts),
    }
    differences = diff_paths(recurrent, ttt)
    checks["allowlist"] = all(_allowed(path, left, right, contracts) for path, (left, right) in differences.items())
    return {"schema_version": SCHEMA + "_verifier", "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "differences": differences}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--recurrent", type=Path, required=True); parser.add_argument("--ttt", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_pair(json.loads(args.recurrent.read_text()), json.loads(args.ttt.read_text()), args.root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
