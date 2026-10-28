"""Strict standalone V2 configuration; does not reuse the legacy Run catalog."""

from __future__ import annotations

import argparse
import math
import os
from pathlib import Path

DEFAULTS = {
    "schema": "psm_robocasa_eval_v2",
    "tasks": "all",
    "episodes_per_task": 50,
    "gpu_ids": [4, 5, 6],
    "base_port": 8912,
    "seed": 0,
    "prediction_steps": 30,
    "guidance": 1.0,
    "save_rollout_mp4": True,
    "save_generated_video": "first",
    "server_start_s": 900.0,
    "episode_wall_s": 1800.0,
    "request_timeout_s": 600.0,
    "terminate_grace_s": 10.0,
    "encoder_grace_s": 2.0,
    "sims_per_gpu": 1,
    "max_infer_batch_size": 1,
    "max_gpu_fraction": 0.85,
    "max_rss_bytes": 128 * 1024**3,
}
PATHS = {
    "checkpoint",
    "config_file",
    "dataset_root",
    "output_dir",
    "server_python",
    "sim_python",
    "vendor_lock",
    "asset_manifest",
}


def resolve(argv=None):
    p = argparse.ArgumentParser(
        description="Independent RoboCasa Evaluation V2 (requires approved runtime Gate)"
    )
    p.add_argument("mode", choices=("fresh", "resume", "dry-run", "authorize"))
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--owner-decision", type=Path)
    p.add_argument("--gpus")
    p.add_argument("--sims-per-gpu", type=int)
    p.add_argument("--max-infer-batch-size", type=int)
    p.add_argument("--tasks")
    p.add_argument("--episodes", type=int)
    p.add_argument("--output-dir", type=Path)
    a = p.parse_args(argv)
    import yaml

    class Unique(yaml.SafeLoader):
        pass

    def mapping(loader, node, deep=False):
        value = {}
        for key, entry in node.value:
            name = loader.construct_object(key, deep=deep)
            if not isinstance(name, str) or name in value:
                raise ValueError("duplicate/nonstring config key")
            value[name] = loader.construct_object(entry, deep=deep)
        return value

    Unique.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)
    data = yaml.load(a.config.read_text(), Loader=Unique)
    if not isinstance(data, dict) or set(data) - set(DEFAULTS) - PATHS:
        raise ValueError("unknown V2 config fields")
    cfg = {**DEFAULTS, **data}
    if cfg["schema"] != DEFAULTS["schema"]:
        raise ValueError("new V2 config schema required")
    if a.sims_per_gpu is not None:
        cfg["sims_per_gpu"] = a.sims_per_gpu
    if a.max_infer_batch_size is not None:
        cfg["max_infer_batch_size"] = a.max_infer_batch_size
    if a.gpus is not None:
        cfg["gpu_ids"] = [int(x) for x in a.gpus.split(",")]
    if a.tasks is not None:
        cfg["tasks"] = a.tasks.split(",")
    if a.episodes is not None:
        cfg["episodes_per_task"] = a.episodes
    if a.output_dir is not None:
        cfg["output_dir"] = str(a.output_dir)
    if (
        not isinstance(cfg["gpu_ids"], list)
        or not cfg["gpu_ids"]
        or len(set(cfg["gpu_ids"])) != len(cfg["gpu_ids"])
        or any(type(g) is not int or g < 0 for g in cfg["gpu_ids"])
    ):
        raise ValueError("unique nonnegative GPU IDs required")
    if cfg["tasks"] != "all" and (
        not isinstance(cfg["tasks"], list)
        or not cfg["tasks"]
        or len(set(cfg["tasks"])) != len(cfg["tasks"])
    ):
        raise ValueError("ordered distinct Task list required")
    for key in [
        "episodes_per_task",
        "base_port",
        "prediction_steps",
        "sims_per_gpu",
        "max_infer_batch_size",
        "max_rss_bytes",
    ]:
        if type(cfg[key]) is not int or cfg[key] <= 0:
            raise ValueError(f"invalid {key}")
    if (
        cfg["episodes_per_task"] > 50
        or cfg["base_port"] + len(cfg["gpu_ids"]) - 1 > 65535
    ):
        raise ValueError("plan/port range")
    if cfg["sims_per_gpu"] != 1 or cfg["max_infer_batch_size"] != 1:
        raise ValueError(
            "Phase A supports only sims_per_gpu=1 and max_infer_batch_size=1"
        )
    if type(cfg["seed"]) is not int or not 0 <= cfg["seed"] < 2**32:
        raise ValueError("invalid seed")
    for key in [
        "server_start_s",
        "episode_wall_s",
        "request_timeout_s",
        "terminate_grace_s",
        "encoder_grace_s",
        "guidance",
        "max_gpu_fraction",
    ]:
        if (
            type(cfg[key]) not in (int, float)
            or not math.isfinite(cfg[key])
            or (key != "guidance" and cfg[key] <= 0)
        ):
            raise ValueError(f"invalid {key}")
    if (
        not 0 < cfg["max_gpu_fraction"] < 1
        or cfg["save_generated_video"] not in ("none", "first", "all")
        or type(cfg["save_rollout_mp4"]) is not bool
    ):
        raise ValueError("invalid resource/media policy")
    for key in PATHS - {"asset_manifest"}:
        if not cfg.get(key):
            raise ValueError(f"missing {key}")
    for key in PATHS:
        if cfg.get(key):
            cfg[key] = str(Path(os.path.expandvars(cfg[key])).absolute())
    output = Path(cfg["output_dir"])
    for key in ("checkpoint", "config_file", "dataset_root", "vendor_lock"):
        source = Path(cfg[key]).resolve()
        if key == "config_file":
            source = source.parent
        if (
            source == output
            or source.is_relative_to(output)
            or output.is_relative_to(source)
        ):
            raise ValueError("output overlaps protected input")
    if a.mode == "fresh" and output.exists():
        raise FileExistsError("fresh namespace already exists")
    if a.mode != "authorize" and a.owner_decision is not None:
        raise ValueError(
            "Owner permit is a separate authorize command, never automatic Resume"
        )
    return a, cfg
