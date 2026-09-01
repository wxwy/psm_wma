#!/usr/bin/env python3
"""Fail-closed, non-executing verifier for the R09-B2 P4 D005 pair."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

from tools.g0.write_r09_b2_p4_d005 import SCHEMA, TOML_RELATIVE, derive_job_path, membership_sha256, sha256_json


RANK_ENV = {"RANK", "WORLD_SIZE", "LOCAL_RANK", "MASTER_ADDR", "MASTER_PORT"}
REQUIRED_ENV = {
    "PSM_R08_LOCAL_HISTORY_ENABLED": "1", "PSM_R09_B2_STREAM_MANIFEST_ROOT": None,
    "LIBERO_LATENT_CACHE_ROOT": None, "LIBERO_LATENT_CACHE_VERIFY_RATIO": "0",
    "LIBERO_NUM_WORKERS": "0", "LIBERO_ROOT": None, "BASE_CHECKPOINT_PATH": None,
    "EDGE_POLICY_CHECKPOINT": None, "WAN_VAE_PATH": None, "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1", "PYTHONPATH": None, "IMAGINAIRE_OUTPUT_ROOT": None,
    "CUDA_VISIBLE_DEVICES": "0",
}
FROZEN_OVERRIDES = ("trainer.max_iter=100", "trainer.save_zero_checkpoint=true")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_tree(path: Path) -> str:
    if path.is_file():
        return _sha256_file(path)
    return sha256_json([(str(child.relative_to(path)), _sha256_file(child)) for child in sorted(path.rglob("*")) if child.is_file()])


def _git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def _git_clean(root: Path) -> bool:
    return subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"], check=False).returncode == 0


def _asset_ok(asset: object, root: Path) -> bool:
    if not isinstance(asset, dict) or set(asset) != {"path", "realpath", "sha256"}:
        return False
    path = Path(str(asset["path"])).expanduser()
    realpath = path.resolve()
    allowed = (root.resolve(), Path("/localdisk-tmp/models").resolve(), Path("/disk/rl/data").resolve())
    return path.exists() and str(realpath) == asset["realpath"] and any(realpath.is_relative_to(base) for base in allowed) and _sha256_tree(realpath) == asset["sha256"]


def _source_ok(source: object, root: Path) -> bool:
    if not isinstance(source, dict):
        return False
    framework = root / "cosmos-framework"
    try:
        return source == {
            "root_revision": _git(root, "rev-parse", "HEAD"), "root_clean": _git_clean(root),
            "submodule_revision": _git(framework, "rev-parse", "HEAD"), "submodule_clean": _git_clean(framework),
            "gitlink_revision": _git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2],
        }
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        return False


def _p3_contract(p3: dict[str, object], backend: str) -> dict[str, object]:
    inventory = p3[backend]["inventory"]
    return {"selector_keys": inventory["selector"]["keys_to_select"], "optimizer_membership_sha256": membership_sha256(p3, backend)}


def _argv_ok(record: dict[str, object], framework: Path) -> bool:
    command = record.get("command", {})
    interpreter = (framework / ".venv/bin/python").resolve()
    argv = command.get("argv")
    if not interpreter.is_file() or not isinstance(argv, list):
        return False
    expected = [str(interpreter), "-m", "torch.distributed.run", "--standalone", "--nnodes=1", "--nproc-per-node=1", "-m", "cosmos_framework.scripts.train", f"--sft-toml={TOML_RELATIVE}", *FROZEN_OVERRIDES]
    return argv == expected and command.get("interpreter") == {"realpath": str(interpreter), "sha256": _sha256_file(interpreter)} and command.get("launcher") == {"kind": "python_module", "module": "torch.distributed.run"}


def _env_ok(record: dict[str, object], backend: str) -> bool:
    env = record.get("environment", {})
    values = env.get("set") if isinstance(env, dict) else None
    if not isinstance(values, dict) or set(values) != set(REQUIRED_ENV) | {"PSM_R09_B1_TTT_ENABLED"}:
        return False
    if values.get("PSM_R09_B1_TTT_ENABLED") != ("1" if backend == "ttt_fast_weight" else "0") or RANK_ENV & set(values):
        return False
    for key, value in REQUIRED_ENV.items():
        if (value is not None and values.get(key) != value) or (value is None and not isinstance(values.get(key), str)):
            return False
    bare = {"set": values, "unset": sorted(RANK_ENV), "inherit_allowlist": []}
    output_root = Path(values["IMAGINAIRE_OUTPUT_ROOT"])
    return env.get("unset") == bare["unset"] and env.get("inherit_allowlist") == [] and env.get("sha256") == sha256_json(bare) and output_root.is_absolute() and str(output_root.resolve()) == values["IMAGINAIRE_OUTPUT_ROOT"]


def _inputs_ok(record: dict[str, object], root: Path, p1: dict[str, object], p3: dict[str, object], backend: str) -> bool:
    inputs = record.get("inputs", {})
    if not isinstance(inputs, dict) or set(inputs) != {"p1_manifest", "p3_inventory", "external_assets"}:
        return False
    p1_binding, p3_binding, assets = inputs["p1_manifest"], inputs["p3_inventory"], inputs["external_assets"]
    if not isinstance(p1_binding, dict) or not isinstance(p3_binding, dict) or not isinstance(assets, dict):
        return False
    required_assets = {"base_checkpoint", "edge_processor", "wan_vae", "libero_root", "stream_manifest", "latent_cache", "interpreter"}
    p1_ok = isinstance(p1.get("schema_version"), str) and p1.get("status", "").startswith("PASS") and isinstance(p1.get("tiny_cpu_build", {}).get("record_count"), int)
    return p1_ok and p1_binding == {"sha256": sha256_json(p1), "record_count": p1["tiny_cpu_build"]["record_count"]} and p3_binding == {"sha256": sha256_json(p3), "backend_contract": _p3_contract(p3, backend)} and set(assets) == required_assets and all(_asset_ok(asset, root) for asset in assets.values())


def _env_assets_bound(record: dict[str, object]) -> bool:
    env, assets = record["environment"]["set"], record["inputs"]["external_assets"]
    mapping = {"BASE_CHECKPOINT_PATH": "base_checkpoint", "EDGE_POLICY_CHECKPOINT": "edge_processor", "WAN_VAE_PATH": "wan_vae", "LIBERO_ROOT": "libero_root", "PSM_R09_B2_STREAM_MANIFEST_ROOT": "stream_manifest", "LIBERO_LATENT_CACHE_ROOT": "latent_cache"}
    try:
        return all(env[key] == assets[name]["realpath"] for key, name in mapping.items()) and env["PYTHONPATH"] == str(Path(assets["interpreter"]["realpath"]).parents[2])
    except (KeyError, TypeError):
        return False


def _output_ok(record: dict[str, object], root: Path) -> bool:
    outputs, env = record.get("outputs", {}), record.get("environment", {})
    if not isinstance(outputs, dict) or not isinstance(env, dict):
        return False
    expected = Path(derive_job_path(env["set"]["IMAGINAIRE_OUTPUT_ROOT"], outputs.get("job_identity", {}))).resolve()
    required = {"job_identity", "run_root", "checkpoint_step0", "checkpoint_step100", "stdout_log", "capture_dir", "fresh"}
    expected_children = {"checkpoint_step0": expected / "checkpoints/iter_000000000", "checkpoint_step100": expected / "checkpoints/iter_000000100", "stdout_log": expected / "stdout.log", "capture_dir": expected / "capture"}
    if not expected.is_relative_to(root.resolve()) or set(outputs) != required or outputs.get("run_root") != str(expected) or outputs.get("fresh") is not True or any(outputs[key] != str(value) for key, value in expected_children.items()):
        return False
    try:
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(expected.relative_to(root.resolve()))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except ValueError:
        return False
    return not expected.exists() and not tracked


def _budget_ok(record: dict[str, object]) -> bool:
    budget = record.get("budget", {})
    required = {"world_size", "micro_batch_size", "grad_accum_steps", "global_batch_size", "samples_per_update", "optimizer_updates"}
    return isinstance(budget, dict) and set(budget) == required and budget["world_size"] == 1 and budget["optimizer_updates"] == 100 and budget["global_batch_size"] == budget["micro_batch_size"] * budget["grad_accum_steps"] * budget["world_size"] and budget["samples_per_update"] == budget["global_batch_size"]


def _check(record: dict[str, object], root: Path, p1: dict[str, object], p3: dict[str, object], backend: str) -> dict[str, bool]:
    command = record.get("command", {})
    framework = (root / "cosmos-framework").resolve()
    return {
        "schema": record.get("schema_version") == SCHEMA and record.get("status") == "FROZEN_NOT_EXECUTED", "non_executable": command.get("executable") is False,
        "source": _source_ok(record.get("source"), root), "cwd": command.get("cwd") == str(framework), "argv": _argv_ok(record, framework),
        "environment": _env_ok(record, backend), "inputs": _inputs_ok(record, root, p1, p3, backend), "env_assets_bound": _env_assets_bound(record) if isinstance(record.get("inputs"), dict) and isinstance(record.get("environment"), dict) else False, "outputs": _output_ok(record, root), "budget": _budget_ok(record),
        "command_digest": command.get("sha256") == sha256_json({key: value for key, value in command.items() if key != "sha256"}),
        "record_digest": record.get("d005_sha256") == sha256_json({key: value for key, value in record.items() if key != "d005_sha256"}),
    }


def verify_pair(recurrent: dict[str, object], ttt: dict[str, object], root: Path, p1: dict[str, object], p3: dict[str, object]) -> dict[str, object]:
    checks = {"recurrent": _check(recurrent, root, p1, p3, "recurrent"), "ttt_fast_weight": _check(ttt, root, p1, p3, "ttt_fast_weight")}
    checks["matched"] = {
        "source": recurrent.get("source") == ttt.get("source"),
        "budget": recurrent.get("budget") == ttt.get("budget"),
        "p1_manifest": recurrent.get("inputs", {}).get("p1_manifest") == ttt.get("inputs", {}).get("p1_manifest"),
        "p3_sha256": recurrent.get("inputs", {}).get("p3_inventory", {}).get("sha256") == ttt.get("inputs", {}).get("p3_inventory", {}).get("sha256"),
        "external_assets": recurrent.get("inputs", {}).get("external_assets") == ttt.get("inputs", {}).get("external_assets"),
    }
    checks["distinct_outputs"] = recurrent.get("outputs", {}).get("run_root") != ttt.get("outputs", {}).get("run_root")
    ok = all(all(values.values()) for values in checks.values() if isinstance(values, dict)) and checks["distinct_outputs"]
    return {"schema_version": "r09_b2_p4_d005_verifier_v2", "status": "PASS" if ok else "FAIL", "checks": checks}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--p1", type=Path, required=True); parser.add_argument("--p3", type=Path, required=True); parser.add_argument("--recurrent", type=Path, required=True); parser.add_argument("--ttt", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_pair(json.loads(args.recurrent.read_text()), json.loads(args.ttt.read_text()), args.root.resolve(), json.loads(args.p1.read_text()), json.loads(args.p3.read_text()))
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print(result["status"])


if __name__ == "__main__":
    main()
