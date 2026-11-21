"""Strict standalone V2 configuration; does not reuse the legacy Run catalog."""

from __future__ import annotations

import argparse
import math
import os
import re
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.contract import (
    ACTION_CHUNK_SIZE,
    G2_R1_FORMAL_BATCH_WAIT_MS,
    ROUND_SCHEDULE,
    STREAMING_SCHEDULE,
    validate_streaming_resources,
)
from cosmos_framework.inference.g2_cache_budget import CACHE_OPTIONS, CacheBudget

DEFAULTS = {
    "schema": "psm_robocasa_eval_v2",
    "execution_profile": "phase_a",
    "local_memory_mode": "required",
    "g2_profile": "legacy",
    "g2_checkpoint_metadata_sha256": None,
    "g2_actor_options": None,
    "local_ttt_history_k": None,
    "single_latency_arm": None,
    "local_evidence_profile": "server_vae",
    "sim_shared_vae": None,
    "scheduling_protocol": ROUND_SCHEDULE,
    "streaming_resources": None,
    "batch_wait_ms": 20,
    "tasks": "all",
    "episodes_per_task": 50,
    # Runtime-only dispatch ceiling. Scientific manifest always freezes all episodes.
    "stage_episode_limit_per_task": None,
    "gpu_ids": [4, 5, 6],
    "render_gpu_ids": None,
    "render_backend": None,
    "server_reserve_bytes": 20 * 1024**3,
    "render_reserve_bytes_per_sim": 1024**3,
    "base_port": 8912,
    "seed": 0,
    "prediction_steps": 30,
    "guidance": 1.0,
    "save_rollout_mp4": True,
    "rollout_mp4_first_n_per_task": None,
    "save_generated_video": "first",
    "server_start_s": 900.0,
    "episode_wall_s": 1800.0,
    "request_timeout_s": 600.0,
    "terminate_grace_s": 10.0,
    "encoder_grace_s": 2.0,
    "media_spool_max_jobs": 4,
    "media_spool_max_bytes": 512 * 1024**2,
    "media_drain_timeout_s": 300.0,
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
    "g2_run_recipe",
    "g2_view_vae_recipe",
    "g2_view_vae_weights",
}
OPTIONAL_PATHS = {
    "asset_manifest",
    "g2_run_recipe",
    "g2_view_vae_recipe",
    "g2_view_vae_weights",
}

G2_ACTOR_PATHS = {"nav_checkout", "ros_setup", "scratch_root"}
G2_ACTOR_REQUIRED = G2_ACTOR_PATHS | {"nav_revision"}


def formal_r1(cfg):
    return (
        cfg["g2_profile"] == "g2_r1"
        and cfg["episodes_per_task"] == 50
        and (cfg["tasks"] == "all" or len(cfg["tasks"]) == 18)
    )


def validate_g2_profile(cfg):
    profile = cfg["g2_profile"]
    recipe = cfg.get("g2_run_recipe")
    metadata = cfg["g2_checkpoint_metadata_sha256"]
    options = cfg["g2_actor_options"]
    view_recipe = cfg.get("g2_view_vae_recipe")
    view_weights = cfg.get("g2_view_vae_weights")
    if profile != "g2_r2" and (view_recipe is not None or view_weights is not None):
        raise ValueError("G2 View VAE settings require the R2 profile")
    if profile == "legacy":
        if any(value is not None for value in (recipe, metadata, options)) or any(
            key in cfg for key in CACHE_OPTIONS.values()
        ):
            raise ValueError("G2 settings require an explicit G2 profile")
        return
    if (
        profile not in ("g2_r1", "g2_r2")
        or cfg["execution_profile"] != "phase_b"
        or cfg["local_memory_mode"] != "required"
        or cfg["local_evidence_profile"] != "server_vae"
        or cfg["single_latency_arm"] is not None
        or cfg["local_ttt_history_k"] != ACTION_CHUNK_SIZE
        or cfg["guidance"] != 1.0
    ):
        raise ValueError(
            "G2 requires Phase B, assigned Local-TTT, server VAE and guidance 1"
        )
    if formal_r1(cfg) and cfg["batch_wait_ms"] != G2_R1_FORMAL_BATCH_WAIT_MS:
        raise ValueError("formal G2 R1 evaluation requires batch_wait_ms=120")
    budget = CacheBudget.from_options(cfg)
    budget.validate_placement(
        slots=cfg["sims_per_gpu"],
        servers=len(cfg["gpu_ids"]),
        rss_limit=cfg["max_rss_bytes"],
        gpu_limit=(cfg["streaming_resources"] or {}).get("max_owned_gpu_bytes"),
    )
    cfg.update({key: getattr(budget, name) for name, key in CACHE_OPTIONS.items()})
    if (
        not recipe
        or not Path(recipe).is_file()
        or not isinstance(metadata, str)
        or re.fullmatch(r"[0-9a-f]{64}", metadata) is None
        or not isinstance(options, dict)
        or G2_ACTOR_REQUIRED - set(options)
        or set(options) - G2_ACTOR_REQUIRED - {"render_f27"}
        or not isinstance(options["nav_revision"], str)
        or re.fullmatch(r"[0-9a-f]{40}", options["nav_revision"]) is None
        or type(options.get("render_f27", False)) is not bool
    ):
        raise ValueError(
            "G2 requires an existing run recipe, checkpoint metadata SHA, and isolated native settings"
        )
    if options.get("render_f27") and cfg["render_backend"] != "egl":
        raise ValueError("G2 F27 requires the attested EGL Actor backend")
    if profile == "g2_r2":
        if (
            options.get("render_f27") is not True
            or not view_recipe
            or not view_weights
            or not Path(view_weights).is_file()
        ):
            raise ValueError(
                "G2 R2 requires live F27 and the pinned View VAE recipe and weights"
            )
        from g2.io import read_json, sha
        from g2.online.view_encoder import read_view_recipe

        run = read_json(recipe, limit=1 << 20)
        if (
            run.get("training", {}).get("profile") != "R2"
            or run.get("global_memory", {}).get("enabled") is not True
        ):
            raise ValueError("G2 R2 requires a materialized R2 Global training recipe")
        view_id = sha(run.get("view_recipe_id"), "training View VAE recipe")
        cfg["g2_view_recipe_id"] = read_view_recipe(view_recipe, view_id)["recipe_id"]
    for key in G2_ACTOR_PATHS:
        if not isinstance(options[key], str) or not options[key].strip():
            raise ValueError(f"missing G2 actor path {key}")
    cfg["g2_actor_options"] = {
        "render_f27": False,
        **options,
        **{
            key: str(Path(os.path.expandvars(options[key])).resolve())
            for key in G2_ACTOR_PATHS
        },
    }


def resolve(argv=None):
    p = argparse.ArgumentParser(
        description="Independent RoboCasa Evaluation V2 (requires approved runtime Gate)"
    )
    p.add_argument("mode", choices=("fresh", "resume", "dry-run", "authorize"))
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--owner-decision", type=Path)
    approvals = p.add_mutually_exclusive_group()
    approvals.add_argument("--f27-resume-approval", type=Path)
    approvals.add_argument("--end-fairness-resume-approval", type=Path)
    p.add_argument("--gpus")
    p.add_argument("--render-gpus")
    p.add_argument("--render-backend", choices=("egl", "osmesa"))
    p.add_argument("--execution-profile", choices=("phase_a", "phase_b"))
    p.add_argument("--local-memory-mode", choices=("off", "required"))
    p.add_argument("--local-ttt-history-k", type=int)
    p.add_argument("--single-latency-arm", choices=("A", "B", "C"))
    p.add_argument("--local-evidence-profile", choices=("server_vae", "sim_shared_vae"))
    p.add_argument(
        "--scheduling-protocol", choices=(ROUND_SCHEDULE, STREAMING_SCHEDULE)
    )
    p.add_argument("--batch-wait-ms", type=int)
    p.add_argument("--sims-per-gpu", type=int)
    p.add_argument("--max-infer-batch-size", type=int)
    p.add_argument("--media-spool-max-jobs", type=int)
    p.add_argument("--media-spool-max-bytes", type=int)
    p.add_argument("--media-drain-timeout-s", type=float)
    p.add_argument("--tasks")
    p.add_argument("--episodes", type=int)
    p.add_argument("--output-dir", type=Path)
    a = p.parse_args(argv)
    if a.f27_resume_approval is not None and a.mode not in ("resume", "dry-run"):
        p.error("--f27-resume-approval requires resume or dry-run of an existing Run")
    if a.end_fairness_resume_approval is not None and a.mode not in (
        "resume",
        "dry-run",
    ):
        p.error(
            "--end-fairness-resume-approval requires resume or dry-run of an existing Run"
        )
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
    if not isinstance(data, dict) or set(data) - set(DEFAULTS) - PATHS - set(
        CACHE_OPTIONS.values()
    ):
        raise ValueError("unknown V2 config fields")
    cfg = {**DEFAULTS, **data}
    if cfg["schema"] != DEFAULTS["schema"]:
        raise ValueError("new V2 config schema required")
    for field in (
        "execution_profile",
        "batch_wait_ms",
        "local_memory_mode",
        "local_ttt_history_k",
        "single_latency_arm",
        "local_evidence_profile",
        "scheduling_protocol",
        "media_spool_max_jobs",
        "media_spool_max_bytes",
        "media_drain_timeout_s",
    ):
        if getattr(a, field) is not None:
            cfg[field] = getattr(a, field)
    if a.sims_per_gpu is not None:
        cfg["sims_per_gpu"] = a.sims_per_gpu
    if a.max_infer_batch_size is not None:
        cfg["max_infer_batch_size"] = a.max_infer_batch_size
    if a.gpus is not None:
        cfg["gpu_ids"] = [int(x) for x in a.gpus.split(",")]
    if a.render_gpus is not None:
        cfg["render_gpu_ids"] = [int(x) for x in a.render_gpus.split(",")]
    if a.render_backend is not None:
        cfg["render_backend"] = a.render_backend
    if a.tasks is not None:
        cfg["tasks"] = "all" if a.tasks == "all" else a.tasks.split(",")
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
    render = rendering(cfg)
    cfg.update(render_backend=render["backend"], render_gpu_ids=render["gpu_ids"])
    for key in ("server_reserve_bytes", "render_reserve_bytes_per_sim"):
        if type(cfg[key]) is not int or cfg[key] < 0:
            raise ValueError(f"invalid {key}")
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
    if formal_r1(cfg) and "batch_wait_ms" not in data and a.batch_wait_ms is None:
        cfg["batch_wait_ms"] = G2_R1_FORMAL_BATCH_WAIT_MS
    stage_cap = cfg["stage_episode_limit_per_task"]
    if stage_cap is not None and (
        type(stage_cap) is not int
        or not 1 <= stage_cap < cfg["episodes_per_task"]
        or cfg["execution_profile"] != "phase_b"
        or cfg["scheduling_protocol"] != STREAMING_SCHEDULE
    ):
        raise ValueError(
            "stage_episode_limit_per_task requires streaming Phase B and a strict positive prefix"
        )
    if cfg["execution_profile"] not in ("phase_a", "phase_b"):
        raise ValueError("explicit execution profile required")
    if cfg["scheduling_protocol"] not in (ROUND_SCHEDULE, STREAMING_SCHEDULE):
        raise ValueError("explicit versioned scheduling protocol required")
    is_streaming = cfg["scheduling_protocol"] == STREAMING_SCHEDULE
    if is_streaming:
        if cfg["execution_profile"] != "phase_b":
            raise ValueError("streaming scheduling requires Phase B")
        validate_streaming_resources(cfg["streaming_resources"])
        if (
            max(
                cfg["streaming_resources"][k]
                for k in ("sim_startup_rss_bytes", "server_startup_rss_bytes")
            )
            > cfg["max_rss_bytes"]
        ):
            raise ValueError("startup RSS reservation exceeds owned RSS budget")
    elif cfg["streaming_resources"] is not None:
        raise ValueError("streaming resources require a new streaming Run")
    if cfg["local_memory_mode"] not in ("off", "required"):
        raise ValueError("explicit off|required Local-TTT mode required")
    if cfg["local_memory_mode"] == "off" and cfg["execution_profile"] != "phase_b":
        raise ValueError(
            "No-TTT requires the shared transactional phase_b profile (B1 or B2+)"
        )
    if (
        cfg["sims_per_gpu"] > (32 if is_streaming else 8)
        or cfg["max_infer_batch_size"] > (32 if is_streaming else 8)
        or type(cfg["batch_wait_ms"]) is not int
        or not (
            0
            if cfg.get("single_latency_arm") == "C"
            or cfg.get("local_evidence_profile") == "sim_shared_vae"
            else 1
        )
        <= cfg["batch_wait_ms"]
        <= 1000
    ):
        raise ValueError("bounded M/B/wait required")
    if cfg["execution_profile"] == "phase_a" and (
        cfg["sims_per_gpu"] != 1 or cfg["max_infer_batch_size"] != 1
    ):
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
    if cfg["execution_profile"] == "phase_b" and cfg["request_timeout_s"] > 6000:
        raise ValueError("transaction Server timeout cap exceeded")
    if (
        type(cfg["media_spool_max_jobs"]) is not int
        or not 1 <= cfg["media_spool_max_jobs"] <= 64
        or type(cfg["media_spool_max_bytes"]) is not int
        or not 1 <= cfg["media_spool_max_bytes"] <= 2**31
        or type(cfg["media_drain_timeout_s"]) not in (int, float)
        or not 0 < cfg["media_drain_timeout_s"] <= 3600
    ):
        raise ValueError("bounded positive media spool/drain settings required")
    if (
        not 0 < cfg["max_gpu_fraction"] < 1
        or cfg["save_generated_video"] not in ("none", "first", "all")
        or type(cfg["save_rollout_mp4"]) is not bool
    ):
        raise ValueError("invalid resource/media policy")
    from robocasa_eval_v2.shared_vae import validate_profile

    validate_profile(cfg)
    from cosmos_framework.inference.robocasa_vae_protocol import validate_history_k

    cfg["local_ttt_history_k"] = validate_history_k(
        cfg.get("local_ttt_history_k"), ACTION_CHUNK_SIZE
    )
    limit = cfg["rollout_mp4_first_n_per_task"]
    if limit is not None and (
        type(limit) is not int
        or not 0 <= limit <= cfg["episodes_per_task"]
        or not cfg["save_rollout_mp4"]
    ):
        raise ValueError("invalid rollout_mp4_first_n_per_task")
    for key in PATHS - OPTIONAL_PATHS:
        if not cfg.get(key):
            raise ValueError(f"missing {key}")
    for key in PATHS:
        if cfg.get(key):
            cfg[key] = str(Path(os.path.expandvars(cfg[key])).absolute())
    validate_g2_profile(cfg)
    output = Path(cfg["output_dir"])
    for key in (
        "checkpoint",
        "config_file",
        "dataset_root",
        "vendor_lock",
        "g2_run_recipe",
        "g2_view_vae_recipe",
        "g2_view_vae_weights",
    ):
        if not cfg.get(key):
            continue
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


def execution(cfg):
    if cfg.get("execution_profile", "phase_a") == "phase_a":
        return None
    result = {
        "profile": "phase_b_native_batch_v1",
        "gpu_ids": list(cfg["gpu_ids"]),
        "sims_per_gpu": cfg["sims_per_gpu"],
        "max_infer_batch_size": cfg["max_infer_batch_size"],
        "batch_wait_ms": cfg["batch_wait_ms"],
        "noise": "literal_cfg_seed_per_sample_v1",
    }
    if cfg.get("scheduling_protocol", ROUND_SCHEDULE) == STREAMING_SCHEDULE:
        result.update(
            scheduling=STREAMING_SCHEDULE,
            resources=cfg["streaming_resources"],
            max_rss_bytes=cfg["max_rss_bytes"],
        )
    if cfg.get("single_latency_arm") is not None:
        from robocasa_eval_v2.shared_vae import public_profile

        result["single_latency"] = public_profile(cfg)
    elif cfg.get("local_evidence_profile") == "sim_shared_vae":
        from robocasa_eval_v2.shared_vae import public_shared_profile

        result["shared_vae"] = public_shared_profile(cfg)
    from cosmos_framework.inference.robocasa_vae_protocol import validate_history_k

    history_k = validate_history_k(cfg.get("local_ttt_history_k"), ACTION_CHUNK_SIZE)
    if history_k != ACTION_CHUNK_SIZE:
        result["local_ttt_history_k"] = history_k
    return result


def rendering(cfg):
    """One ordered render device per Server; duplicates allow deliberate sharing."""
    backend = cfg.get("render_backend")
    if backend is None:
        backend = os.environ.get("MUJOCO_GL", "egl")
    if backend not in ("egl", "osmesa"):
        raise ValueError("render_backend must be egl or osmesa")
    devices = cfg.get("render_gpu_ids")
    if backend == "osmesa":
        if devices is not None and devices != []:
            raise ValueError("OSMesa cannot allocate render GPUs")
        return {"backend": backend, "gpu_ids": []}
    if devices is None:
        devices = cfg["gpu_ids"]
    if (
        not isinstance(devices, list)
        or len(devices) != len(cfg["gpu_ids"])
        or any(type(g) is not int or g < 0 for g in devices)
    ):
        raise ValueError("render_gpu_ids must map each Server to a physical GPU")
    return {"backend": backend, "gpu_ids": list(devices)}
