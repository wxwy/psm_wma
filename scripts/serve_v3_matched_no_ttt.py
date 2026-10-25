"""Validate a matched baseline identity, then invoke the existing Cosmos server.

--dry-run only reads JSON/YAML/metadata paths and prints argv. No model imports.
This entry does not adapt the required-TTT Queue or reuse its historical results.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import yaml

GENERATION_KEYS = [
    "moe_gen",
    "time_embedder",
    "vae2llm",
    "llm2vae",
    "action2llm",
    "llm2action",
    "action_modality_embed",
]


def server_command(profile_path: Path, *, python: str = sys.executable) -> list[str]:
    profile = yaml.safe_load(profile_path.read_text())
    expected = {
        "schema": "psm_wma_matched_no_ttt_inference_v1",
        "local_memory_mode": "off",
        "raw_action_dim": 15,
        "max_action_dim": 64,
        "action_chunk_size": 16,
        "fps": 20,
    }
    if not isinstance(profile, dict) or set(profile) != {
        *expected,
        "checkpoint",
        "config_file",
        "num_steps",
        "guidance",
        "port",
    }:
        raise ValueError("No-TTT inference profile schema/fields mismatch")
    if any(type(profile[key]) is not type(value) or profile[key] != value for key, value in expected.items()):
        raise ValueError("No-TTT inference raw15/chunk16/off protocol mismatch")
    if (
        any(type(profile[key]) is not int or profile[key] <= 0 for key in ("num_steps", "port"))
        or profile["port"] > 65535
    ):
        raise ValueError("invalid num_steps/port")
    if type(profile["guidance"]) not in (float, int) or not math.isfinite(profile["guidance"]):
        raise ValueError("invalid guidance")
    config_file, checkpoint = (Path(profile[key]).expanduser().resolve() for key in ("config_file", "checkpoint"))
    job = config_file.parent
    identity = json.loads((job / "v3_job_identity.json").read_text())
    if (
        identity.get("schema") != "corrected_phase5_f0_v1"
        or identity.get("namespace") != str(job)
        or identity.get("semantic", {}).get("training_profile") != "matched_no_ttt_v1"
        or identity.get("diagnostic_only_do_not_resume") is not False
        or identity.get("canonical_config_sha256", {}).get("config.yaml")
        != hashlib.sha256(config_file.read_bytes()).hexdigest()
        or checkpoint.parent != job / "checkpoints"
        or not checkpoint.name.startswith("iter_")
        or not checkpoint.name[5:].isdigit()
        or int(checkpoint.name[5:]) < 1
    ):
        raise ValueError("No-TTT inference requires its own canonical job/checkpoint/config identity")
    semantic_digest = hashlib.sha256(
        json.dumps(identity["semantic"], sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()
    if identity.get("semantic_digest") != semantic_digest:
        raise ValueError("No-TTT semantic identity digest mismatch")
    config = yaml.safe_load(config_file.read_text())
    if (
        config["model"]["config"].get("local_memory_enabled") is not False
        or config["optimizer"]["keys_to_select"] != GENERATION_KEYS
    ):
        raise ValueError("No-TTT inference config instantiates Local or mismatches Generation optimizer")
    geometry = {
        "raw_action_dim": 15,
        "state_dim": 15,
        "h_pred": 16,
        "consumer_frames": 17,
        "t": 16,
        "b": 8,
        "ga": 2,
        "world_size": 8,
    }
    contract = identity["semantic"].get("contract", {})
    if any(type(contract.get(key)) is not int or contract[key] != value for key, value in geometry.items()):
        raise ValueError("No-TTT training identity raw15/state15/H16/Packed128 mismatch")
    datasets = config.get("dataloader_train", {}).get("dataloader", {}).get("datasets", {})
    dataset = datasets.get("robocasa", {}).get("dataset", {})
    if (
        any(
            dataset.get(key) != value or type(dataset.get(key)) is not type(value)
            for key, value in {
                "chunk_length": 16,
                "camera_set": "left_wrist",
                "use_state": True,
                "use_base_action": True,
                "base_encoding": "raw",
                "max_action_dim": 64,
                "mode": "wam",
                "action_normalization": None,
            }.items()
        )
        or dataset.get("fps") != 20
    ):
        raise ValueError("No-TTT saved dataset action/state/camera contract mismatch")
    if not (checkpoint / "model/.metadata").is_file() or not any((checkpoint / "model").glob("*.distcp")):
        raise FileNotFoundError("No-TTT inference requires model DCP metadata and shards")
    command = [
        python,
        "-m",
        "cosmos_framework.scripts.action_policy_server_robocasa",
        "--checkpoint-path",
        str(checkpoint),
        "--config-file",
        str(config_file),
    ]
    for key in (
        "raw_action_dim",
        "max_action_dim",
        "action_chunk_size",
        "fps",
        "num_steps",
        "guidance",
        "port",
        "local_memory_mode",
    ):
        command += ["--" + key.replace("_", "-"), str(profile[key])]
    return command + ["--no-guardrails", "--http-400-on-error"]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    command = server_command(args.config)
    if args.dry_run:
        print(json.dumps({"argv": command, "local_memory_mode": "off", "model_loaded": False}, indent=2))
        return
    child = Path(__file__).resolve().parents[1] / "cosmos-framework"
    os.environ["PYTHONPATH"] = str(child) + os.pathsep + os.environ.get("PYTHONPATH", "")
    os.environ["HF_HUB_OFFLINE"] = os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
