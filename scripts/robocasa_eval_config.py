#!/usr/bin/env python3
"""Versioned, strict Owner configuration for the RoboCasa manual evaluation queue."""

from __future__ import annotations

import argparse
import math
import os
import re
from pathlib import Path

SCHEMA = "psm_wma_robocasa_eval_v1"
ROOT = Path(__file__).resolve().parents[1]
DEFAULTS = {
    "schema": SCHEMA,
    "tasks": "all",
    "episodes_per_task": 1,
    "gpu_ids": [0],
    "slots_per_gpu": 1,
    "base_port": 8912,
    "expected_tasks": 18,
    "seed": 0,
    "prediction_steps": 30,
    "guidance": 1.0,
    "fps": 20,
    "action_horizon": 16,
    "local_memory_mode": "required",
    "server_lifecycle": "per_task",
    "on_infrastructure_error": "stop",
    "save_rollout_mp4": True,
    "save_generated_video": "first",
    "save_init_png": True,
    "save_action_jsonl": True,
    "save_prediction_jsonl": True,
    "resume": False,
    "progress": True,
    "progress_interval_s": 5.0,
}
TIMEOUT_DEFAULTS = {
    "server_start_s": 900.0,
    "predict_request_s": 600.0,
    "episode_wall_s": 1800.0,
    "task_wall_s": 10800.0,
    "terminate_grace_s": 20.0,
}
PATH_FIELDS = {
    "checkpoint",
    "config_file",
    "dataset_root",
    "server_python",
    "sim_python",
    "output_root",
    "output_dir",
    "vendor_lock",
    "asset_manifest",
}
KNOWN_FIELDS = set(DEFAULTS) | PATH_FIELDS | {"run_name", "timeouts"}


def _yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as error:
        raise ValueError("YAML configuration requires PyYAML in the launcher Python") from error

    class UniqueLoader(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        values = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in values:
                raise ValueError(f"duplicate/non-string YAML key: {key!r}")
            values[key] = loader.construct_object(value_node, deep=deep)
        return values

    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.load(handle, Loader=UniqueLoader)
    except yaml.YAMLError as error:
        raise ValueError(f"invalid evaluation YAML: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("evaluation YAML must be a mapping")
    unknown = set(data) - KNOWN_FIELDS
    if unknown:
        raise ValueError(f"unknown evaluation config fields: {sorted(unknown)}")
    if data.get("schema") != SCHEMA:
        raise ValueError(f"evaluation YAML requires schema: {SCHEMA}")
    return data


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__, argument_default=argparse.SUPPRESS)
    result.add_argument("--config", type=Path, help="evaluation YAML; --config-file is the model config")
    result.add_argument("--list-tasks", action="store_true")
    result.add_argument("--dry-run", action="store_true")
    result.add_argument("--checkpoint", "--checkpoint-path", dest="checkpoint")
    for field in (
        "dataset-root",
        "config-file",
        "server-python",
        "sim-python",
        "output-root",
        "output-dir",
        "run-name",
        "vendor-lock",
        "asset-manifest",
    ):
        result.add_argument("--" + field)
    result.add_argument("--tasks", help="comma-separated underlying task classes, or all")
    result.add_argument("--gpus", dest="gpu_ids", help="comma-separated CUDA GPU IDs; one task slot per GPU")
    for flag, name in (
        ("episodes", "episodes_per_task"),
        ("slots-per-gpu", "slots_per_gpu"),
        ("base-port", "base_port"),
        ("expected-tasks", "expected_tasks"),
        ("seed", "seed"),
        ("prediction-steps", "prediction_steps"),
        ("action-horizon", "action_horizon"),
        ("fps", "fps"),
    ):
        aliases = {"episodes": ["--num-test-episodes"], "prediction-steps": ["--num-steps"]}.get(flag, [])
        result.add_argument("--" + flag, *aliases, dest=name, type=int)
    result.add_argument("--guidance", type=float)
    result.add_argument("--progress-interval-s", type=float)
    result.add_argument("--timeout", type=float, help="legacy alias setting both server and prediction timeouts")
    for flag in (
        "server-start-timeout-s",
        "predict-request-timeout-s",
        "episode-wall-timeout-s",
        "task-wall-timeout-s",
        "terminate-grace-s",
    ):
        result.add_argument("--" + flag, type=float)
    for flag in ("local-memory-mode", "server-lifecycle", "on-infrastructure-error", "save-generated-video"):
        result.add_argument("--" + flag)
    for flag in (
        "resume",
        "save-rollout-mp4",
        "save-init-png",
        "save-action-jsonl",
        "save-prediction-jsonl",
        "progress",
    ):
        result.add_argument("--" + flag, action=argparse.BooleanOptionalAction)
    return result


def _names(value, *, field: str, all_allowed=False) -> list[str] | str:
    if all_allowed and value == "all":
        return "all"
    if isinstance(value, str):
        value = [item.strip() for item in value.split(",")]
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"{field} must be a nonempty list without empty entries")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} contains duplicates")
    if any(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", item) is None or item == "all" for item in value):
        raise ValueError(f"invalid {field} name")
    return list(value)


def resolve(argv=None, *, root: Path = ROOT) -> argparse.Namespace:
    """Resolve CLI > YAML > v1 defaults without writing files or importing simulators.

    YAML relative paths resolve against its directory. CLI paths resolve against cwd.
    Python executable paths retain symlinks so a venv does not turn into system Python.
    Actual task discovery, DCP checks and runtime attestation belong to the queue.
    """
    cli = vars(parser().parse_args(argv))
    config = cli.pop("config", None)
    data = _yaml(config) if config is not None else {}
    yaml_base = config.absolute().parent if config is not None else Path.cwd()
    for field in PATH_FIELDS & data.keys():
        if not isinstance(data[field], str) or not data[field]:
            raise ValueError(f"{field} must be a nonempty path string")
        path = Path(data[field]).expanduser()
        data[field] = str(path if path.is_absolute() else yaml_base / path)
    timeouts = data.pop("timeouts", {})
    if not isinstance(timeouts, dict) or set(timeouts) - set(TIMEOUT_DEFAULTS):
        raise ValueError("invalid/unknown timeouts fields")
    timeouts = TIMEOUT_DEFAULTS | timeouts
    for key in ("list_tasks", "dry_run"):
        cli.setdefault(key, False)
    resolved = (
        DEFAULTS
        | {
            "server_python": str(root / "cosmos-framework/.venv/bin/python"),
            "vendor_lock": str(root / "third_party/robosuite_patches/vendor.lock.json"),
        }
        | data
    )
    if "timeout" in cli:
        value = cli.pop("timeout")
        timeouts["server_start_s"] = value
        timeouts["predict_request_s"] = value
    timeout_aliases = {
        "server_start_timeout_s": "server_start_s",
        "predict_request_timeout_s": "predict_request_s",
        "episode_wall_timeout_s": "episode_wall_s",
        "task_wall_timeout_s": "task_wall_s",
        "terminate_grace_s": "terminate_grace_s",
    }
    for key, field in timeout_aliases.items():
        if key in cli:
            timeouts[field] = cli.pop(key)
    # An explicit CLI output-dir replaces YAML output_root/run_name, and vice versa.
    if "output_dir" in cli:
        if "output_root" in cli or "run_name" in cli:
            raise ValueError("--output-dir is exclusive with --output-root/--run-name")
        resolved.pop("output_root", None)
        resolved.pop("run_name", None)
    elif "output_root" in cli or "run_name" in cli:
        resolved.pop("output_dir", None)
    resolved.update(cli)
    for field in PATH_FIELDS & resolved.keys():
        value = resolved[field]
        if not isinstance(value, str) or not value:
            raise ValueError(f"{field} must be a nonempty path string")
        resolved[field] = str(Path(value).expanduser().absolute())
    resolved["tasks"] = _names(resolved["tasks"], field="tasks", all_allowed=True)
    gpu_ids = resolved["gpu_ids"]
    if isinstance(gpu_ids, str):
        gpu_ids = [item.strip() for item in gpu_ids.split(",")]
    if not isinstance(gpu_ids, list) or not gpu_ids:
        raise ValueError("gpu_ids must be a nonempty list")
    if any(type(item) is not int and (not isinstance(item, str) or not item.isdecimal()) for item in gpu_ids):
        raise ValueError("gpu_ids must contain nonnegative integer CUDA IDs")
    gpu_ids = [int(item) for item in gpu_ids]
    if any(item < 0 for item in gpu_ids) or len(gpu_ids) != len(set(gpu_ids)):
        raise ValueError("gpu_ids must be unique nonnegative CUDA IDs")
    resolved["gpu_ids"] = gpu_ids
    for field in (
        "episodes_per_task",
        "slots_per_gpu",
        "base_port",
        "expected_tasks",
        "prediction_steps",
        "fps",
        "action_horizon",
    ):
        if type(resolved[field]) is not int or resolved[field] <= 0:
            raise ValueError(f"{field} must be a positive integer")
    if type(resolved["seed"]) is not int or resolved["seed"] < 0:
        raise ValueError("seed must be a nonnegative integer")
    if resolved["base_port"] + len(gpu_ids) - 1 > 65535:
        raise ValueError("base_port plus GPU workers exceeds port range")
    if resolved["tasks"] == "all" and resolved["expected_tasks"] != 18:
        raise ValueError("tasks=all requires exactly 18 underlying task classes; select a subset explicitly")
    for field, expected in (
        ("slots_per_gpu", 1),
        ("fps", 20),
        ("local_memory_mode", "required"),
        ("server_lifecycle", "per_task"),
    ):
        if resolved[field] != expected:
            raise ValueError(f"frozen protocol requires {field}={expected}")
    if resolved["action_horizon"] > 16:
        raise ValueError("action_horizon must be in 1..16")
    if resolved["save_generated_video"] not in ("none", "first", "all"):
        raise ValueError("save_generated_video must be none, first or all")
    if resolved["on_infrastructure_error"] not in ("stop", "continue_with_new_server"):
        raise ValueError("invalid on_infrastructure_error")
    for field in (
        "resume",
        "save_rollout_mp4",
        "save_init_png",
        "save_action_jsonl",
        "save_prediction_jsonl",
        "progress",
    ):
        if type(resolved[field]) is not bool:
            raise ValueError(f"{field} must be a boolean")
    for field in ("save_action_jsonl", "save_prediction_jsonl"):
        if not resolved[field]:
            raise ValueError(f"audit evidence requires {field}=true")
    if type(resolved["guidance"]) not in (int, float) or not math.isfinite(resolved["guidance"]):
        raise ValueError("guidance must be finite")
    interval = resolved["progress_interval_s"]
    if type(interval) not in (int, float) or not math.isfinite(interval) or interval <= 0:
        raise ValueError("progress_interval_s must be finite and positive")
    for field, value in timeouts.items():
        if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"timeouts.{field} must be finite and positive")
    resolved["timeouts"] = timeouts
    if "dataset_root" not in resolved:
        raise ValueError("dataset_root is required")
    if not resolved["list_tasks"]:
        for field in ("checkpoint", "sim_python"):
            if field not in resolved:
                raise ValueError(f"{field} is required")
        if "output_dir" in resolved and ("output_root" in resolved or "run_name" in resolved):
            raise ValueError("output_dir is exclusive with output_root/run_name")
        if "output_dir" not in resolved:
            if "output_root" not in resolved or "run_name" not in resolved:
                raise ValueError("output_root + run_name (or output_dir) required")
            name = resolved["run_name"]
            if not isinstance(name, str) or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", name) is None:
                raise ValueError("run_name must be one safe namespace component")
            resolved["output_dir"] = str(Path(resolved["output_root"]) / name)
        if "config_file" not in resolved:
            resolved["config_file"] = str(Path(resolved["checkpoint"]).parent.parent / "config.yaml")
        for field in ("server_python", "sim_python"):
            path = Path(resolved[field])
            if not path.is_file() or not os.access(path, os.X_OK):
                raise ValueError(f"{field} is not executable: {path}")
    result = argparse.Namespace(**resolved)
    result.config = config
    result.resolved_config = {key: value for key, value in resolved.items() if key not in ("list_tasks", "dry_run")}
    for field in PATH_FIELDS:
        setattr(result, field, Path(resolved[field]) if field in resolved else None)
    result.checkpoint_path = result.checkpoint
    result.gpus = ",".join(map(str, gpu_ids))
    result.num_test_episodes = result.episodes_per_task
    result.num_steps = result.prediction_steps
    result.timeout = timeouts["predict_request_s"]
    for key, field in timeout_aliases.items():
        setattr(result, key, timeouts[field])
    return result
