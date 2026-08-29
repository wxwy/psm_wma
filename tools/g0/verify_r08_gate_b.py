#!/usr/bin/env python3
"""Strict provenance and sensitivity verifier for R08 Gate B."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

from compare_r07_sensitivity import INVARIANT_KEYS, difference, load_json, load_tensors

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main() -> None:
    p = argparse.ArgumentParser()
    for mode in ("normal", "zero", "shuffle"):
        for kind in ("json", "pt", "provenance", "log", "config"):
            p.add_argument(f"--{mode}-{kind}", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args(); modes = ("normal", "zero", "shuffle")
    summaries = {m: load_json(getattr(a, f"{m}_json")) for m in modes}
    tensors = {m: load_tensors(getattr(a, f"{m}_pt")) for m in modes}
    prov = {m: load_json(getattr(a, f"{m}_provenance")) for m in modes}
    expected = all(prov[m].get("history_mode") == m and prov[m].get("capture_only") for m in modes)
    same_runtime = len({(x.get("root_revision"), x.get("submodule_revision"), x.get("gitlink_revision"), x.get("checkpoint_path")) for x in prov.values()}) == 1
    valid_git = all(x["gitlink_revision"] == x["submodule_revision"] and x["root_clean_tracked"] and x["submodule_clean_tracked"] for x in prov.values())
    loaded = all(re.search(re.escape(prov[m]["checkpoint_path"]) + r" .* in iteration 0", getattr(a, f"{m}_log").read_text()) for m in modes)
    invariant = {k: summaries["normal"].get(k) == summaries["zero"].get(k) == summaries["shuffle"].get(k) for k in INVARIANT_KEYS}
    metrics = {f"normal_vs_{m}": {k: difference(tensors["normal"][k], tensors[m][k]) for k in ("local_memory", "preds_vision", "preds_action")} for m in ("zero", "shuffle")}
    response = all(metrics[p][k]["l2_diff"] > 0 for p in metrics for k in ("local_memory", "preds_vision", "preds_action"))
    status = "PASS" if expected and same_runtime and valid_git and loaded and all(invariant.values()) and response else "FAIL"
    files = {m: {k: {"path": str(getattr(a, f"{m}_{k}")), "sha256": sha(getattr(a, f"{m}_{k}"))} for k in ("json", "pt", "provenance", "log", "config")} for m in modes}
    result = {"schema_version":"r08_gate_b_history_sensitivity_v1","status":status,"expected_modes":expected,"same_runtime":same_runtime,"valid_git":valid_git,"actual_checkpoint_loaded":loaded,"invariant_exact":invariant,"response":response,"metrics":metrics,"files":files,"verifier_sha256":sha(Path(__file__))}
    a.output.parent.mkdir(parents=True, exist_ok=True); a.output.write_text(json.dumps(result, indent=2)+"\n"); print(f"R08 Gate B: {status}")
    if status != "PASS": raise SystemExit(1)
if __name__ == "__main__": main()
