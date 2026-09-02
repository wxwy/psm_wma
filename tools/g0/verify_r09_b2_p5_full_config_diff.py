#!/usr/bin/env python3
"""Fail-closed verifier for future R09-B2 P5 v4 config envelopes."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from tools.g0.export_r09_b2_p5_resolved_config import (
    P4_V4_BACKENDS,
    build_v4_pair_requests,
    load_p4_v4_preflight,
)
from tools.g0.verify_r09_b2_p4_d005 import (P3_ARTIFACT_SHA256, P3_VERIFIER_SHA256,
                                             _load_frozen_inputs, _p3_contract)


SCHEMA = "r09_b2_p5_full_config_diff_v4"


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


def _git_full_clean(root: Path) -> bool:
    result = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "--untracked-files=all"],
        check=False, text=True, capture_output=True,
    )
    return root.is_dir() and result.returncode == 0 and not result.stdout


def _file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _exporter_source(exporter_root: Path) -> dict[str, Any]:
    files = (
        "tools/g0/export_r09_b2_p5_resolved_config.py",
        "tools/g0/verify_r09_b2_p5_full_config_diff.py",
    )
    framework = exporter_root / "cosmos-framework"
    if not _git_full_clean(exporter_root) or not _git_full_clean(framework):
        raise ValueError("exporter_root and its cosmos-framework submodule must be full-clean")
    return {
        "root_revision": subprocess.check_output(["git", "-C", str(exporter_root), "rev-parse", "HEAD"], text=True).strip(),
        "tool_sha256": {name: _file_sha(exporter_root / name) for name in files},
    }


def _p3_contracts(evidence_root: Path) -> dict[str, Mapping[str, Any]]:
    _, inventory = _load_frozen_inputs(evidence_root)
    return {backend: _p3_contract(inventory, backend) for backend in P4_V4_BACKENDS}


def _p3_provenance(contract: Mapping[str, Any]) -> dict[str, Any]:
    return {"artifact_sha256": P3_ARTIFACT_SHA256, "verifier_sha256": P3_VERIFIER_SHA256,
            "backend_contract": {"selector_keys": contract["selector_keys"],
                                 "optimizer_membership_sha256": contract["optimizer_membership_sha256"]}}


def _bound(envelope: Mapping[str, Any], request: Mapping[str, Any], record: Mapping[str, Any], exporter_source: Mapping[str, Any], p3_contract: Mapping[str, Any]) -> bool:
    try:
        required = {"schema_version", "backend", "provenance", "effective_launch", "resolved_config"}
        provenance = envelope["provenance"]
        launch = envelope["effective_launch"]
        request_sha = hashlib.sha256(
            (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode()
        ).hexdigest()
        return (
            set(envelope) == required
            and envelope["schema_version"] == SCHEMA
            and envelope["backend"] == request["backend"]
            and provenance == {
                "p4_v4_request_sha256": request_sha,
                "p4_v4_result_sha256": request["p4_result_sha256"],
                "p4_v4_verification_sha256": request["p4_verification_sha256"],
                "exporter_source": exporter_source, "p3_contract": _p3_provenance(p3_contract),
            }
            and launch == {
                "cwd": request["cwd"],
                "toml": request["toml"],
                "overrides": request["overrides"],
                "interpreter": request["interpreter"],
                "loader_argv": request["loader_argv"],
                "environment": request["environment"],
                "runtime_sys_path": request["runtime_sys_path"],
            }
            and isinstance(envelope["resolved_config"], Mapping)
            and envelope["resolved_config"].get("optimizer", {}).get("keys_to_select") == p3_contract["selector_keys"]
        )
    except (KeyError, TypeError):
        return False


def _allowed(path: str, left: Any, right: Any, contracts: Mapping[str, Mapping[str, Any]]) -> bool:
    if path == "/backend":
        return left == "recurrent" and right == "ttt_fast_weight"
    if path in {
        "/provenance/p4_v4_request_sha256",
        "/provenance/p4_v4_result_sha256",
        "/provenance/p4_v4_verification_sha256",
    }:
        return isinstance(left, str) and isinstance(right, str) and left != right
    if path == "/provenance/p3_contract/backend_contract/optimizer_membership_sha256":
        return left == contracts["recurrent"]["optimizer_membership_sha256"] and right == contracts["ttt_fast_weight"]["optimizer_membership_sha256"]
    if path == "/provenance/p3_contract/backend_contract/selector_keys":
        return left == contracts["recurrent"]["selector_keys"] and right == contracts["ttt_fast_weight"]["selector_keys"]
    if path.startswith("/provenance/p3_contract/backend_contract/selector_keys/"):
        return left in contracts["recurrent"]["selector_keys"] or right in contracts["ttt_fast_weight"]["selector_keys"]
    if path == "/effective_launch/environment/PSM_R09_B1_TTT_ENABLED":
        return left == "0" and right == "1"
    if path == "/resolved_config/model/config/local_history_backend":
        return left == "recurrent" and right == "ttt_fast_weight"
    selector = "/resolved_config/optimizer/keys_to_select"
    if path == selector:
        return left == contracts["recurrent"]["selector_keys"] and right == contracts["ttt_fast_weight"]["selector_keys"]
    if path.startswith(selector + "/"):
        return left in contracts["recurrent"]["selector_keys"] or right in contracts["ttt_fast_weight"]["selector_keys"]
    return False


def verify_pair(recurrent: Mapping[str, Any], ttt: Mapping[str, Any], evidence_root: Path, exporter_root: Path) -> dict[str, Any]:
    try:
        root = evidence_root.resolve()
        exporter_root = exporter_root.resolve()
        if root == exporter_root or root.is_relative_to(exporter_root) or exporter_root.is_relative_to(root):
            raise ValueError("evidence_root and exporter_root must be distinct non-overlapping canonical directories")
        preflight = load_p4_v4_preflight(root)
        requests = build_v4_pair_requests(root)
        contracts = _p3_contracts(root)
        exporter_source = _exporter_source(exporter_root)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        return {"schema_version": SCHEMA + "_verifier", "status": "FAIL", "error": str(exc), "checks": {}}
    checks = {
        "schema": all(item.get("schema_version") == SCHEMA for item in (recurrent, ttt)),
        "backend": recurrent.get("backend") == P4_V4_BACKENDS[0] and ttt.get("backend") == P4_V4_BACKENDS[1],
        "recurrent_bound": _bound(recurrent, requests["recurrent"], preflight["recurrent"]["request"], exporter_source, contracts["recurrent"]),
        "ttt_bound": _bound(ttt, requests["ttt_fast_weight"], preflight["ttt_fast_weight"]["request"], exporter_source, contracts["ttt_fast_weight"]),
    }
    differences = diff_paths(recurrent, ttt)
    checks["allowlist"] = all(_allowed(path, left, right, contracts) for path, (left, right) in differences.items())
    return {"schema_version": SCHEMA + "_verifier", "status": "PASS" if all(checks.values()) else "FAIL", "checks": checks, "differences": differences}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--exporter-root", type=Path, required=True)
    parser.add_argument("--recurrent", type=Path, required=True)
    parser.add_argument("--ttt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_pair(json.loads(args.recurrent.read_text()), json.loads(args.ttt.read_text()), args.evidence_root, args.exporter_root)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
