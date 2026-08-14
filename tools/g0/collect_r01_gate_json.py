#!/usr/bin/env python3
"""Collect G0-R01 runtime evidence into one machine-readable Gate result."""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import platform
import subprocess
from pathlib import Path
from typing import Any


EXPECTED_COSMOS_COMMIT = "ad9158ea35b9c8a76c2c3c00c553141d65fbeea3"
EXPECTED_ACTION_SHAPE = [32, 8]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_commit(path: Path) -> str:
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def _environment() -> tuple[dict[str, Any], list[dict[str, str]]]:
    import torch

    env = {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "cudnn": torch.backends.cudnn.version(),
        "ld_library_path": os.environ.get("LD_LIBRARY_PATH", ""),
    }
    query = [
        "nvidia-smi",
        "--query-gpu=index,name,memory.total,driver_version",
        "--format=csv,noheader,nounits",
    ]
    try:
        rows = subprocess.check_output(query, text=True).splitlines()
    except (FileNotFoundError, subprocess.CalledProcessError):
        rows = []
    gpu = []
    for row in rows:
        fields = [value.strip() for value in row.split(",")]
        if len(fields) == 4:
            gpu.append(dict(zip(("index", "name", "memory_total_mb", "driver_version"), fields, strict=True)))
    if not gpu and torch.cuda.is_available():
        properties = torch.cuda.get_device_properties(0)
        gpu.append(
            {
                "index": "0",
                "name": properties.name,
                "memory_total_mb": f"{properties.total_memory / 1024**2:.0f}",
                "driver_version": "unavailable",
            }
        )
    return env, gpu


def _peak_vram_mb(path: Path) -> float | None:
    if not path.is_file():
        return None
    values: list[float] = []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.reader(stream):
            for cell in row:
                try:
                    values.append(float(cell.strip().split()[0]))
                    break
                except (ValueError, IndexError):
                    continue
    return max(values) if values else None


def _reasoner_metrics(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"finite": False, "warmup_latency_ms": [], "steady_latency_ms": []}
    payload = _read_json(path)
    all_timings = payload.get("all", {})
    warmup = [1000.0 * value for key, values in all_timings.items() if key.startswith("[warmup]") for value in values]
    steady = [1000.0 * value for key, values in all_timings.items() if not key.startswith("[warmup]") for value in values]
    return {
        "finite": bool(warmup)
        and bool(steady)
        and all(math.isfinite(value) and value >= 0 for value in warmup + steady),
        "warmup_latency_ms": warmup,
        "steady_latency_ms": steady,
    }


def _client_metrics(path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    empty_policy = {"shape": None, "finite": False, "latency_ms_requests": [], "num_timed_requests": 0}
    empty_world = {"shape": None, "finite": False}
    if not path.is_file():
        return empty_policy, empty_world
    payload = _read_json(path)
    requests = payload.get("requests", [])
    timed = [item for item in requests if not item.get("warmup", False)]
    if not timed:
        return empty_policy, empty_world
    action_shapes = [item.get("action", {}).get("shape") for item in timed]
    video_shapes = [item.get("video", {}).get("shape") for item in timed]
    policy = {
        "shape": action_shapes[0] if len({tuple(shape or []) for shape in action_shapes}) == 1 else None,
        "finite": all(item.get("action", {}).get("finite") is True for item in timed),
        "latency_ms_requests": [item.get("latency_ms") for item in timed],
        "num_timed_requests": len(timed),
    }
    world = {
        "shape": video_shapes[0] if len({tuple(shape or []) for shape in video_shapes}) == 1 else None,
        "finite": all(item.get("video", {}).get("finite") is True for item in timed),
    }
    latencies = policy["latency_ms_requests"]
    policy["finite"] = (
        policy["finite"]
        and all(isinstance(value, (int, float)) and math.isfinite(value) and value >= 0 for value in latencies)
    )
    world["finite"] = (
        world["finite"]
        and world["shape"] is not None
        and len(world["shape"]) == 4
        and all(isinstance(value, int) and value > 0 for value in world["shape"])
        and world["shape"][-1] == 3
    )
    return policy, world


def collect(
    root: Path,
    checkpoint: Path,
    evidence: Path,
    *,
    port: int = 8000,
    seed: int = 0,
    num_steps: int = 4,
) -> dict[str, Any]:
    cosmos = root / "cosmos-framework"
    reasoner = _reasoner_metrics(evidence / "reasoner" / "benchmark.json")
    policy, world = _client_metrics(evidence / "robolab_client_metrics.json")
    vram_mb = [value for value in (_peak_vram_mb(evidence / "reasoner_vram.csv"), _peak_vram_mb(evidence / "policy_vram.csv")) if value is not None]
    required = [
        evidence / "preflight.log",
        evidence / "reasoner" / "reasoner" / "sample_outputs.json",
        evidence / "reasoner" / "reasoner" / "reasoner_text.txt",
        evidence / "policy_server.log",
    ]
    missing = [str(path) for path in required if not path.is_file() or path.stat().st_size == 0]
    cosmos_commit = _git_commit(cosmos)
    env, gpu = _environment()
    failures: list[str] = []
    blockers: list[str] = []
    if cosmos_commit != EXPECTED_COSMOS_COMMIT:
        blockers.append("BLOCKED_VERSION_DRIFT")
    if missing:
        blockers.append("BLOCKED_MISSING_EVIDENCE")
    if not (evidence / "robolab_client_metrics.json").is_file():
        blockers.append("BLOCKED_CLIENT_ASSET")
    if not vram_mb:
        blockers.append("BLOCKED_MISSING_VRAM")
    if not gpu:
        blockers.append("BLOCKED_NO_GPU")
    reasoner_output = evidence / "reasoner" / "reasoner" / "sample_outputs.json"
    if reasoner_output.is_file() and _read_json(reasoner_output).get("status") != "success":
        failures.append("FAIL_REASONER_OUTPUT")
    if (evidence / "reasoner" / "benchmark.json").is_file() and not reasoner["finite"]:
        failures.append("FAIL_REASONER")
    if (evidence / "robolab_client_metrics.json").is_file() and policy["num_timed_requests"] < 2:
        failures.append("FAIL_INSUFFICIENT_REQUESTS")
    if policy["shape"] is not None and policy["shape"] != EXPECTED_ACTION_SHAPE:
        failures.append("FAIL_ACTION_SHAPE")
    if policy["shape"] is not None and not policy["finite"]:
        failures.append("FAIL_ACTION_NONFINITE")
    if world["shape"] is not None and not world["finite"]:
        failures.append("FAIL_WORLD_NONFINITE")
    status = "FAIL" if failures else "BLOCKED" if blockers else "PASS"
    return {
        "gate": "G0-R01",
        "repo_commit": _git_commit(root),
        "cosmos_commit": cosmos_commit,
        "checkpoint_path": str(checkpoint),
        "checkpoint_index_complete": (
            "MISSING_OR_EMPTY"
            not in (evidence / "preflight.log").read_text(encoding="utf-8", errors="replace")
            if (evidence / "preflight.log").is_file()
            else False
        ),
        "gpu": gpu,
        "dtype": "bfloat16",
        "env": env,
        "run_config": {
            "seed": seed,
            "port": port,
            "domain_name": "droid_lerobot",
            "action_chunk_size": 32,
            "action_dim": 8,
            "conditioning_fps": 15.0,
            "num_steps": num_steps,
        },
        "reasoner": reasoner,
        "policy": policy,
        "world": world,
        "peak_vram_gb": max(vram_mb) / 1024.0 if vram_mb else None,
        "status": status,
        "blocker": blockers or None,
        "exception": failures or None,
        "missing_evidence": missing,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--num-steps", type=int, default=4)
    args = parser.parse_args()
    result = collect(
        args.root.resolve(),
        args.checkpoint.resolve(),
        args.evidence_dir.resolve(),
        port=args.port,
        seed=args.seed,
        num_steps=args.num_steps,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "status": result["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
