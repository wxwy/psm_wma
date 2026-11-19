#!/usr/bin/env python3
"""Generate immutable run JSON from versioned code-repository recipes and external model/data paths."""
import argparse
import hashlib
import json
import os
from pathlib import Path

BINDINGS = dict(
    data_c_root="G2_DATA_C_ROOT", g1_verified_index_root="G2_INDEX_ROOT",
    initial_language_root="G2_LANGUAGE_ROOT", snapshot_root="G2_SNAPSHOT_ROOT",
    state15_root="G2_STATE15_ROOT", view_root="G2_SIXVIEWS_ROOT",
)
CONFIG_SHA = "f87e2e49c6931ce7dc32b467aa3f8026269f5ad255216e1cdd8fafb1d7e7374e"
MODEL_SHA = "8e2a59fc3db785c9aa095af4f6c1253532a64d2624ab056b1ee486af4cfd11da"
SCHEDULE = {"warmup_steps": 0, "decay": "constant", "min_factor": 1.0, "horizon_steps": 30000}

def hash_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def materialize(profile, root, dest, environ):
    cfg = json.loads((root / "configs/g2" / (profile + "_formal_30000.template.json")).read_text())
    plan = cfg["training"]
    if (
        plan["profile"] != profile.upper() or
        (plan["stage_a_steps"], plan["stage_b_steps"]) != (1000, 29000) or
        plan["target_effective_consumers"] != 59489136 or cfg["save_iter"] != 100 or
        plan["gen_schedule"] != SCHEDULE or plan["action_schedule"] != SCHEDULE or
        (plan["global_schedule"] == SCHEDULE) != (profile == "r2") or
        cfg["provider_factory"] != "g2.data.verified_provider:open_verified_provider" or
        cfg["g1_config_sha256"] != CONFIG_SHA or
        plan["init_checkpoint_identity"] != MODEL_SHA
    ):
        raise ValueError("formal R1/R2 plan drift")
    job = Path(environ["G2_G1_JOB_ROOT"]).resolve(strict=True)
    config = job / "config.yaml"
    model = job / "checkpoints/iter_000027700/model/.metadata"
    if hash_file(config) != CONFIG_SHA or hash_file(model) != MODEL_SHA:
        raise ValueError("G1 Iter27700 model/config identity drift")
    if cfg["g1_config_path"] != "__G2_G1_CONFIG_PATH__":
        raise ValueError("unresolved G1 config template")
    cfg["g1_config_path"] = str(config)
    for field, envkey in BINDINGS.items():
        if cfg["provider_kwargs"][field] != "__" + envkey + "__":
            raise ValueError("unresolved DATA_C template " + field)
        cfg["provider_kwargs"][field] = str(Path(environ[envkey]).resolve(strict=True))
    for envkey in ("G2_RAW_ROOT", "G2_CACHE_ROOT", "G2_INDEX_ROOT", "G2_EDGE_MODEL"):
        if not Path(environ[envkey]).is_dir():
            raise FileNotFoundError(envkey)
    if not Path(environ["G2_WAN_VAE"]).is_file():
        raise FileNotFoundError("G2_WAN_VAE")
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink() or dest.parent.is_symlink():
        raise ValueError("recipe symlink refused")
    content = json.dumps(cfg, sort_keys=True, indent=2) + "\n"
    if dest.exists():
        if dest.read_text() != content:
            raise ValueError("frozen runtime recipe already exists with different bytes")
    else:
        with dest.open("x") as f:
            f.write(content)
    print(json.dumps({"profile": profile, "sha256": hash_file(dest), "recipe": str(dest),
                      "steps": 30000, "save_iter": 100, "consumers": 59489136}), flush=True)
    return cfg

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("r1", "r2"), required=True)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    materialize(args.profile, args.root.resolve(), args.output.absolute(), os.environ)
