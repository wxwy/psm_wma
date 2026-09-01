#!/usr/bin/env python3
"""Fail-closed verifier for non-executable R09-B2 P4 launch D005 pairs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from tools.g0.write_r09_b2_p4_d005 import SCHEMA, TOML_RELATIVE, derive_job_path, sha256_json


TTT_KEYS = ("local_history_runtime.encoder", "local_memory2llm", "local_memory_modality_embed")
RANK_ENV = {"RANK", "WORLD_SIZE", "LOCAL_RANK", "MASTER_ADDR", "MASTER_PORT"}


def _check(record: dict[str, object], root: Path, backend: str) -> dict[str, bool]:
    command = record.get("command", {})
    env = record.get("environment", {})
    outputs = record.get("outputs", {})
    argv = command.get("argv", [])
    framework = (root / "cosmos-framework").resolve()
    expected_prefix = [str(command.get("interpreter", {}).get("realpath", "")), "-m", "torch.distributed.run", "--standalone", "--nnodes=1", "--nproc-per-node=1", "-m", "cosmos_framework.scripts.train"]
    expected_run = derive_job_path(env.get("set", {}).get("IMAGINAIRE_OUTPUT_ROOT", ""), outputs.get("job_identity", {}))
    has_toml = f"--sft-toml={TOML_RELATIVE}" in argv
    has_max = "trainer.max_iter=100" in argv
    has_zero = "trainer.save_zero_checkpoint=true" in argv
    ttt = "1" if backend == "ttt_fast_weight" else "0"
    check_dir = Path(expected_run) / "checkpoints"
    return {
        "schema": record.get("schema_version") == SCHEMA and record.get("status") == "FROZEN_NOT_EXECUTED",
        "non_executable": command.get("executable") is False,
        "cwd": command.get("cwd") == str(framework) and Path(command.get("cwd", ".")).resolve() == framework,
        "interpreter_launcher": argv[: len(expected_prefix)] == expected_prefix and command.get("launcher", {}).get("kind") in {"python_module", "torch.distributed.run"},
        "toml": has_toml,
        "budget": record.get("budget", {}).get("world_size") == 1 and record.get("budget", {}).get("optimizer_updates") == 100 and has_max and has_zero,
        "env": env.get("set", {}).get("PSM_R09_B1_TTT_ENABLED") == ttt and env.get("set", {}).get("LIBERO_NUM_WORKERS") == "0" and env.get("set", {}).get("CUDA_VISIBLE_DEVICES") == "0" and not (RANK_ENV & set(env.get("set", {}))),
        "output_derivation": outputs.get("run_root") == expected_run and outputs.get("checkpoint_step0") == f"{expected_run}/checkpoints/iter_000000000" and outputs.get("checkpoint_step100") == f"{expected_run}/checkpoints/iter_000000100",
        "fresh": not Path(expected_run).exists() and not check_dir.exists(),
        "digest": record.get("d005_sha256") == sha256_json({key: value for key, value in record.items() if key != "d005_sha256"}),
    }


def verify_pair(recurrent: dict[str, object], ttt: dict[str, object], root: Path) -> dict[str, object]:
    checks = {"recurrent": _check(recurrent, root, "recurrent"), "ttt_fast_weight": _check(ttt, root, "ttt_fast_weight")}
    shared = {"source", "budget", "inputs"}
    checks["matched"] = {key: recurrent.get(key) == ttt.get(key) for key in shared}
    checks["distinct_outputs"] = recurrent.get("outputs", {}).get("run_root") != ttt.get("outputs", {}).get("run_root")
    ok = all(all(values.values()) for values in checks.values() if isinstance(values, dict)) and checks["distinct_outputs"]
    return {"schema_version": "r09_b2_p4_d005_verifier_v1", "status": "PASS" if ok else "FAIL", "checks": checks}


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--recurrent", type=Path, required=True)
    parser.add_argument("--ttt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = verify_pair(json.loads(args.recurrent.read_text()), json.loads(args.ttt.read_text()), args.root.resolve())
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(result["status"])


if __name__ == "__main__":
    main()
