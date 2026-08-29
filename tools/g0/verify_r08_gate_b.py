#!/usr/bin/env python3
"""Strict provenance and sensitivity verifier for R08 Gate B."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from compare_r07_sensitivity import INVARIANT_KEYS, difference, load_json, load_tensors

CAPTURE_SCHEMA = "r07_no_memory_parity_v1"
TENSOR_SCHEMA = "r07_sensitivity_tensors_v1"
PROVENANCE_SCHEMA = "r08_gate_b_capture_provenance_v1"
MANIFEST_SCHEMA = "r08_gate_a_checkpoint_manifest_v1"


def sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def checkpoint_identity(manifest_path: Path) -> tuple[dict, bool]:
    manifest = load_json(manifest_path)
    valid = isinstance(manifest, dict) and manifest.get("schema_version") == MANIFEST_SCHEMA
    checkpoint_path = Path(manifest.get("checkpoint_path", "")) if valid else Path()
    files = manifest.get("files", {}) if valid else {}
    required = {"model/.metadata", "model/__0_0.distcp"}
    valid = valid and checkpoint_path.is_dir() and isinstance(files, dict) and required <= set(files)
    for relative, expected in files.items() if isinstance(files, dict) else ():
        candidate = checkpoint_path / relative
        valid = valid and isinstance(expected, dict) and candidate.is_file()
        valid = valid and candidate.stat().st_size == expected.get("size_bytes") and sha(candidate) == expected.get("sha256")
    return {"manifest_path": str(manifest_path), "manifest_sha256": sha(manifest_path), "checkpoint_path": str(checkpoint_path), "file_count": len(files) if isinstance(files, dict) else 0, "checkpoint_identity_valid": bool(valid)}, bool(valid)


def finite_response(metric: dict) -> bool:
    if not isinstance(metric, dict) or not math.isfinite(metric.get("l2_diff", math.nan)) or metric["l2_diff"] <= 0:
        return False
    if not math.isfinite(metric.get("max_abs_diff", math.nan)):
        return False
    return "relative_l2_diff" not in metric or math.isfinite(metric["relative_l2_diff"])


def verified_result(a: argparse.Namespace) -> dict:
    modes = ("normal", "zero", "shuffle")
    summaries = {m: load_json(getattr(a, f"{m}_json")) for m in modes}
    tensors = {m: load_tensors(getattr(a, f"{m}_pt")) for m in modes}
    prov = {m: load_json(getattr(a, f"{m}_provenance")) for m in modes}
    identity, checkpoint_identity_valid = checkpoint_identity(a.checkpoint_manifest)
    checkpoint_path = identity["checkpoint_path"]
    capture_schema_valid = all(x.get("schema_version") == CAPTURE_SCHEMA for x in summaries.values())
    tensor_schema_valid = all(x.get("schema_version") == TENSOR_SCHEMA for x in tensors.values())
    provenance_schema_valid = all(x.get("schema_version") == PROVENANCE_SCHEMA for x in prov.values())
    expected_modes = all(prov[m].get("history_mode") == m and prov[m].get("capture_only") is True for m in modes)
    same_runtime = len({(x.get("root_revision"), x.get("submodule_revision"), x.get("gitlink_revision"), x.get("checkpoint_path")) for x in prov.values()}) == 1
    valid_git = all(x.get("gitlink_revision") == x.get("submodule_revision") and x.get("root_clean_tracked") is True and x.get("submodule_clean_tracked") is True for x in prov.values())
    manifest_checkpoint_path = all(x.get("checkpoint_path") == checkpoint_path for x in prov.values())
    loaded = all(re.search(re.escape(f"Loaded checkpoint from {checkpoint_path}") + r"(?: \([^)]*\))? in iteration " + str(a.expected_iteration) + r"(?:\n|$)", getattr(a, f"{m}_log").read_text()) for m in modes)
    resumed = all(re.search(re.escape(f"Resuming ckpt {checkpoint_path}") + r"(?: \([^)]*\))? with keys:", getattr(a, f"{m}_log").read_text()) for m in modes)
    model_only = all(re.search(r"(?m)^\s*load_training_state:\s*false\s*$", getattr(a, f"{m}_config").read_text()) and re.search(r"(?m)^\s*load_path:\s*" + re.escape(checkpoint_path) + r"\s*$", getattr(a, f"{m}_config").read_text()) for m in modes)
    invariant = {k: all(k in summaries[m] for m in modes) and summaries["normal"][k] == summaries["zero"][k] == summaries["shuffle"][k] for k in INVARIANT_KEYS}
    metrics = {f"normal_vs_{m}": {k: difference(tensors["normal"][k], tensors[m][k]) for k in ("local_memory", "preds_vision", "preds_action")} for m in ("zero", "shuffle")}
    response = all(finite_response(metrics[pair][field]) for pair in metrics for field in ("local_memory", "preds_vision", "preds_action"))
    status = "PASS" if all((capture_schema_valid, tensor_schema_valid, provenance_schema_valid, expected_modes, same_runtime, valid_git, manifest_checkpoint_path, checkpoint_identity_valid, loaded, resumed, model_only, all(invariant.values()), response)) else "FAIL"
    files = {m: {k: {"path": str(getattr(a, f"{m}_{k}")), "sha256": sha(getattr(a, f"{m}_{k}"))} for k in ("json", "pt", "provenance", "log", "config")} for m in modes}
    return {"schema_version": "r08_gate_b_history_sensitivity_v1", "status": status, "capture_schema_valid": capture_schema_valid, "tensor_schema_valid": tensor_schema_valid, "provenance_schema_valid": provenance_schema_valid, "expected_modes": expected_modes, "same_runtime": same_runtime, "valid_git": valid_git, "manifest_checkpoint_path": manifest_checkpoint_path, "actual_checkpoint_loaded": loaded, "actual_checkpoint_resumed": resumed, "model_only_warm_start": model_only, "expected_iteration": a.expected_iteration, "checkpoint_identity": identity, "invariant_exact": invariant, "response": response, "metrics": metrics, "files": files, "verifier_sha256": sha(Path(__file__))}


def main() -> None:
    p = argparse.ArgumentParser()
    for mode in ("normal", "zero", "shuffle"):
        for kind in ("json", "pt", "provenance", "log", "config"):
            p.add_argument(f"--{mode}-{kind}", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--checkpoint-manifest", type=Path, required=True)
    p.add_argument("--expected-iteration", type=int, default=0)
    a = p.parse_args()
    result = verified_result(a)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"R08 Gate B: {result['status']}")
    if result["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
