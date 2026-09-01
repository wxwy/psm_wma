#!/usr/bin/env python3
"""Fail-closed, non-executing verifier for the R09-B2 P4 D005 pair."""

from __future__ import annotations

import hashlib
import json
import subprocess
import tomllib
from pathlib import Path

from tools.g0.write_r09_b2_p4_d005 import SCHEMA, TOML_RELATIVE, derive_job_path, sha256_json
from tools.g0.r09_b2_interpreter_provenance import lexical_interpreter, verify_native_load_contract
from tools.g0.verify_r09_b2_p3_gpu_inventory import (
    EXPECTED_RECURRENT_SELECTOR_KEYS,
    EXPECTED_TTT_SELECTOR_KEYS,
)


RANK_ENV = {"RANK", "WORLD_SIZE", "LOCAL_RANK", "MASTER_ADDR", "MASTER_PORT"}
P1_HEADER_RELATIVE = "artifacts/g0/r09/b2/p1_production_manifest_100x16x128/header.json"
P3_ARTIFACT_RELATIVE = "artifacts/g0/r09/b2/p3_gpu_inventory_attempt6/p3_gpu_inventory.json"
P3_VERIFIER_RELATIVE = "artifacts/g0/r09/b2/p3_gpu_inventory_attempt6/p3_gpu_inventory_verifier_selector_review.json"
P1_HEADER_SHA256 = "e49ade9dd63f537db89a3efc9174b0da55b2511ce58db195b002674df88ab5e1"
P3_ARTIFACT_SHA256 = "5dd5253cabaa5efa54f3ddc8891f632e3b05e515bf91c8055108e037f69b684d"
P3_VERIFIER_SHA256 = "e9700cd63e9626ce88969b2d21682c186af7dfe0c7489f88795de1301d5b64f8"
FROZEN_GITLINK = "21d064f2b7c7aeeb67cfee50ac8d6722a944eddb"
PRODUCTION_BUDGET = {"world_size": 1, "micro_batch_size": 128, "grad_accum_steps": 16, "global_batch_size": 2048, "samples_per_update": 2048, "optimizer_updates": 100}
PRODUCTION_P1 = {"record_count": 204800, "world_size": 1, "num_workers": 0, "optimizer_updates": 100, "grad_accum": 16, "max_samples_per_batch": 128}
SANITIZED_ENV = {
    "PSM_LOCAL_DUMMY_ENABLED", "PSM_LOCAL_DUMMY_MODE", "PSM_LOCAL_DUMMY_DIM", "PSM_R09_A1_ENABLED", "PSM_R09_A1_PROBE_OUTPUT",
    "PSM_R08_LOCAL_HISTORY_HORIZON", "PSM_R08_GATE_B_CAPTURE_ONLY", "LIBERO_MAX_EPISODES",
    "LIBERO_PREFETCH_FACTOR", "ONLINE_VAE_PROBE_OUTPUT", "ONLINE_VAE_PROBE_MAX_SAMPLES",
    "PSM_R07_RUNTIME_PROBE_OUTPUT", "PSM_R08_GATE_A_PROBE_OUTPUT", "PSM_R09_B1_PROBE_OUTPUT",
    "PSM_R08_GATE_A_DEVICE_MONITOR_EVERY_N", "PSM_R07_PARITY_OUTPUT", "PSM_R07_PARITY_TENSOR_OUTPUT",
    "PSM_R08_GATE_B_PROVENANCE_OUTPUT", "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy", "NO_PROXY", "no_proxy",
}
REQUIRED_ENV = {
    "PSM_R08_LOCAL_HISTORY_ENABLED": "1", "PSM_R09_B2_STREAM_MANIFEST_ROOT": None,
    "LIBERO_LATENT_CACHE_ROOT": None, "LIBERO_LATENT_CACHE_VERIFY_RATIO": "0",
    "LIBERO_NUM_WORKERS": "0", "LIBERO_ROOT": None, "BASE_CHECKPOINT_PATH": None,
    "EDGE_POLICY_CHECKPOINT": None, "WAN_VAE_PATH": None, "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1", "PYTHONPATH": None, "IMAGINAIRE_OUTPUT_ROOT": None,
    "CUDA_VISIBLE_DEVICES": "0",
}
FROZEN_OVERRIDES = ("trainer.max_iter=100", "trainer.save_zero_checkpoint=true")
TOP_LEVEL_KEYS = {"schema_version", "status", "backend", "source", "command", "environment", "budget", "inputs", "outputs", "native_load_contract", "d005_sha256"}


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
        gitlink = _git(root, "ls-tree", "HEAD", "cosmos-framework").split()[2]
        return (_git_clean(root) and _git_clean(framework) and gitlink == FROZEN_GITLINK
                and _git(framework, "rev-parse", "HEAD") == FROZEN_GITLINK
                and source == {"root_revision": _git(root, "rev-parse", "HEAD"),
                               "submodule_revision": FROZEN_GITLINK, "gitlink_revision": FROZEN_GITLINK})
    except (subprocess.CalledProcessError, FileNotFoundError, IndexError):
        return False


def _p3_contract(p3: dict[str, object], backend: str) -> dict[str, object]:
    inventory = p3.get(backend, {}).get("inventory")
    if not isinstance(inventory, dict) or not isinstance(inventory.get("model_parameters"), list):
        raise ValueError("frozen P3 inventory is malformed")
    expected = EXPECTED_TTT_SELECTOR_KEYS if backend == "ttt_fast_weight" else EXPECTED_RECURRENT_SELECTOR_KEYS
    rows = inventory["model_parameters"]
    if not all(isinstance(row, dict) and isinstance(row.get("name"), str) for row in rows):
        raise ValueError("frozen P3 parameter rows are malformed")
    expected_selected = sorted(row["name"] for row in rows if any(key in row["name"] for key in expected))
    actual_selected = sorted(row["name"] for row in rows if row.get("selected_by_optimizer") is True)
    actual_resolved = sorted(row["name"] for row in rows if row.get("selected_by_resolved_selector") is True)
    selector = inventory["selector"]
    if (selector != {"backend": backend, "keys_to_select": list(expected)}
            or actual_selected != expected_selected or actual_resolved != expected_selected):
        raise ValueError("P3 selector, resolved selector, or optimizer membership differs from verifier-owned contract")
    return {"selector_keys": list(expected), "optimizer_membership_sha256": sha256_json(expected_selected)}


def _load_frozen_inputs(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    p1_path = root / P1_HEADER_RELATIVE
    p3_path = root / P3_ARTIFACT_RELATIVE
    p3_verifier_path = root / P3_VERIFIER_RELATIVE
    if (not p1_path.is_file() or not p3_path.is_file() or not p3_verifier_path.is_file()
            or _sha256_file(p1_path) != P1_HEADER_SHA256
            or _sha256_file(p3_path) != P3_ARTIFACT_SHA256
            or _sha256_file(p3_verifier_path) != P3_VERIFIER_SHA256):
        raise ValueError("frozen P1/P3 evidence digest mismatch")
    p1, p3, p3_verifier = json.loads(p1_path.read_text()), json.loads(p3_path.read_text()), json.loads(p3_verifier_path.read_text())
    suites = p1.get("files", {}).get("suite_record_sha256", {})
    p1_dir = p1_path.parent
    p1_files_ok = (_sha256_file(p1_dir / "records.jsonl") == p1.get("records_sha256")
                   and isinstance(suites, dict)
                   and set(suites) == {"libero_spatial", "libero_object", "libero_goal", "libero_10"}
                   and all(_sha256_file(p1_dir / "suites" / f"{suite}.jsonl") == digest for suite, digest in suites.items()))
    if ({key: p1.get(key) for key in PRODUCTION_P1} != PRODUCTION_P1 or not p1_files_ok
            or p3_verifier.get("status") != "PASS" or not p3_verifier.get("record_valid")):
        raise ValueError("frozen P1/P3 evidence contract mismatch")
    return p1, p3


def _argv_ok(record: dict[str, object], framework: Path) -> bool:
    command = record.get("command", {})
    try:
        interpreter = lexical_interpreter(framework / ".venv/bin/python")
    except (OSError, ValueError):
        return False
    argv = command.get("argv")
    if not isinstance(argv, list):
        return False
    expected = [interpreter["path"], "-m", "torch.distributed.run", "--standalone", "--nnodes=1", "--nproc-per-node=1", "-m", "cosmos_framework.scripts.train", f"--sft-toml={TOML_RELATIVE}", *FROZEN_OVERRIDES]
    return argv == expected and command.get("interpreter") == interpreter and command.get("launcher") == {"kind": "python_module", "module": "torch.distributed.run"}


def _allowed_roots(root: Path) -> tuple[Path, ...]:
    return (root.resolve(), Path("/localdisk-tmp/models").resolve(), Path("/disk/rl/data").resolve())


def _interpreter_asset_ok(asset: object, root: Path) -> bool:
    try:
        expected = lexical_interpreter(root / "cosmos-framework/.venv/bin/python")
    except (OSError, ValueError):
        return False
    return isinstance(asset, dict) and asset == expected


def _env_ok(record: dict[str, object], backend: str, root: Path) -> bool:
    env = record.get("environment", {})
    values = env.get("set") if isinstance(env, dict) else None
    if not isinstance(values, dict) or set(values) != set(REQUIRED_ENV) | {"PSM_R09_B1_TTT_ENABLED"}:
        return False
    if values.get("PSM_R09_B1_TTT_ENABLED") != ("1" if backend == "ttt_fast_weight" else "0") or RANK_ENV & set(values):
        return False
    for key, value in REQUIRED_ENV.items():
        if (value is not None and values.get(key) != value) or (value is None and not isinstance(values.get(key), str)):
            return False
    bare = {"set": values, "unset": sorted(RANK_ENV | SANITIZED_ENV), "inherit_allowlist": []}
    output_root = Path(values["IMAGINAIRE_OUTPUT_ROOT"])
    return env.get("unset") == bare["unset"] and env.get("inherit_allowlist") == [] and env.get("sha256") == sha256_json(bare) and output_root.is_absolute() and str(output_root.resolve()) == values["IMAGINAIRE_OUTPUT_ROOT"] and any(output_root.is_relative_to(base) for base in _allowed_roots(root))


def _inputs_ok(record: dict[str, object], root: Path, p1: dict[str, object], p3: dict[str, object], backend: str) -> bool:
    inputs = record.get("inputs", {})
    if not isinstance(inputs, dict) or set(inputs) != {"p1_manifest", "p3_inventory", "external_assets"}:
        return False
    p1_binding, p3_binding, assets = inputs["p1_manifest"], inputs["p3_inventory"], inputs["external_assets"]
    if not isinstance(p1_binding, dict) or not isinstance(p3_binding, dict) or not isinstance(assets, dict):
        return False
    required_assets = {"base_checkpoint", "edge_processor", "wan_vae", "libero_root", "stream_manifest", "latent_cache", "interpreter"}
    p1_ok = {key: p1.get(key) for key in PRODUCTION_P1} == PRODUCTION_P1
    return (p1_ok
            and p1_binding == {"path": P1_HEADER_RELATIVE, "sha256": P1_HEADER_SHA256,
                               "records_sha256": p1["records_sha256"], "record_count": PRODUCTION_P1["record_count"]}
            and p3_binding == {"path": P3_ARTIFACT_RELATIVE, "sha256": P3_ARTIFACT_SHA256,
                               "backend_contract": _p3_contract(p3, backend)}
            and set(assets) == required_assets
            and all(_asset_ok(asset, root) for name, asset in assets.items() if name != "interpreter")
            and _interpreter_asset_ok(assets["interpreter"], root))


def _env_assets_bound(record: dict[str, object], root: Path) -> bool:
    env, assets = record["environment"]["set"], record["inputs"]["external_assets"]
    mapping = {"BASE_CHECKPOINT_PATH": "base_checkpoint", "EDGE_POLICY_CHECKPOINT": "edge_processor", "WAN_VAE_PATH": "wan_vae", "LIBERO_ROOT": "libero_root", "PSM_R09_B2_STREAM_MANIFEST_ROOT": "stream_manifest", "LIBERO_LATENT_CACHE_ROOT": "latent_cache"}
    try:
        return (all(env[key] == assets[name]["realpath"] for key, name in mapping.items())
                and env["PYTHONPATH"] == str((root / "cosmos-framework").resolve())
                and assets["interpreter"] == record["command"]["interpreter"]
                and env["PSM_R09_B2_STREAM_MANIFEST_ROOT"] == str((root / P1_HEADER_RELATIVE).parent.resolve()))
    except (KeyError, TypeError):
        return False


def _output_ok(record: dict[str, object], root: Path, job_identity: dict[str, str]) -> bool:
    outputs, env = record.get("outputs", {}), record.get("environment", {})
    if not isinstance(outputs, dict) or not isinstance(env, dict):
        return False
    expected = Path(derive_job_path(env["set"]["IMAGINAIRE_OUTPUT_ROOT"], job_identity)).resolve()
    required = {"job_identity", "run_root", "checkpoint_step0", "checkpoint_step100", "stdout_log", "capture_dir", "fresh"}
    expected_children = {"checkpoint_step0": expected / "checkpoints/iter_000000000", "checkpoint_step100": expected / "checkpoints/iter_000000100", "stdout_log": expected / "stdout.log", "capture_dir": expected / "capture"}
    if (not any(expected.is_relative_to(base) for base in _allowed_roots(root)) or set(outputs) != required
            or outputs.get("job_identity") != job_identity or outputs.get("run_root") != str(expected)
            or outputs.get("fresh") is not True
            or any(outputs[key] != str(value) for key, value in expected_children.items())):
        return False
    try:
        tracked = subprocess.run(["git", "-C", str(root), "ls-files", "--error-unmatch", str(expected.relative_to(root.resolve()))], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    except ValueError:
        tracked = False
    return not expected.exists() and not tracked


def _budget_ok(record: dict[str, object]) -> bool:
    budget = record.get("budget", {})
    required = {"world_size", "micro_batch_size", "grad_accum_steps", "global_batch_size", "samples_per_update", "optimizer_updates"}
    return isinstance(budget, dict) and set(budget) == required and budget == PRODUCTION_BUDGET


def _recipe_contract(root: Path) -> dict[str, str] | None:
    try:
        with (root / "cosmos-framework" / TOML_RELATIVE).open("rb") as handle:
            recipe = tomllib.load(handle)
        identity = {key: recipe["job"][key] for key in ("project", "group", "name")}
        if not all(isinstance(value, str) and value for value in identity.values()):
            return None
        return identity if recipe["trainer"]["grad_accum_iter"] == PRODUCTION_BUDGET["grad_accum_steps"] else None
    except (FileNotFoundError, KeyError, tomllib.TOMLDecodeError):
        return None


def _schema_structure_ok(record: dict[str, object]) -> bool:
    command = record.get("command")
    environment = record.get("environment")
    inputs = record.get("inputs")
    outputs = record.get("outputs")
    return (set(record) == TOP_LEVEL_KEYS and isinstance(record.get("source"), dict)
            and set(record["source"]) == {"root_revision", "submodule_revision", "gitlink_revision"}
            and isinstance(command, dict) and set(command) == {"cwd", "interpreter", "argv", "executable", "launcher", "sha256"}
            and isinstance(environment, dict) and set(environment) == {"set", "unset", "inherit_allowlist", "sha256"}
            and isinstance(inputs, dict) and set(inputs) == {"p1_manifest", "p3_inventory", "external_assets"}
            and isinstance(outputs, dict) and set(outputs) == {"job_identity", "run_root", "checkpoint_step0", "checkpoint_step100", "stdout_log", "capture_dir", "fresh"}
            and isinstance(record.get("native_load_contract"), dict))


def _check(record: dict[str, object], root: Path, p1: dict[str, object], p3: dict[str, object], backend: str) -> dict[str, bool]:
    command = record.get("command", {})
    framework = (root / "cosmos-framework").resolve()
    job_identity = _recipe_contract(root)
    return {
        "schema": _schema_structure_ok(record) and record.get("schema_version") == SCHEMA and record.get("status") == "FROZEN_NOT_EXECUTED" and record.get("backend") == backend, "non_executable": command.get("executable") is False,
        "source": _source_ok(record.get("source"), root), "cwd": command.get("cwd") == str(framework), "argv": _argv_ok(record, framework),
        "environment": _env_ok(record, backend, root), "inputs": _inputs_ok(record, root, p1, p3, backend), "env_assets_bound": _env_assets_bound(record, root) if isinstance(record.get("inputs"), dict) and isinstance(record.get("environment"), dict) else False, "native_load_contract": verify_native_load_contract(record.get("native_load_contract", {})), "outputs": job_identity is not None and _output_ok(record, root, job_identity), "budget": _budget_ok(record),
        "command_digest": command.get("sha256") == sha256_json({key: value for key, value in command.items() if key != "sha256"}),
        "record_digest": record.get("d005_sha256") == sha256_json({key: value for key, value in record.items() if key != "d005_sha256"}),
    }


def verify_pair(recurrent: dict[str, object], ttt: dict[str, object], root: Path) -> dict[str, object]:
    try:
        p1, p3 = _load_frozen_inputs(root)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {"schema_version": "r09_b2_p4_d005_verifier_v2", "status": "FAIL", "error": str(exc), "checks": {}}
    try:
        checks = {"recurrent": _check(recurrent, root, p1, p3, "recurrent"), "ttt_fast_weight": _check(ttt, root, p1, p3, "ttt_fast_weight")}
    except (KeyError, TypeError, ValueError) as exc:
        return {"schema_version": "r09_b2_p4_d005_verifier_v2", "status": "FAIL", "error": str(exc), "checks": {}}
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
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True); parser.add_argument("--recurrent", type=Path, required=True); parser.add_argument("--ttt", type=Path, required=True); parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_pair(json.loads(args.recurrent.read_text()), json.loads(args.ttt.read_text()), args.root.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n"); print(result["status"])


if __name__ == "__main__":
    main()
