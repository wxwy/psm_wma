#!/usr/bin/env python3
"""Cache-only dataloader->model forward smoke; assert no MP4 decode and no VAE encode."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import torch

# Resolve repo root and ensure project imports.
_REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO_ROOT / "cosmos-framework"))

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--steps", type=int, default=3)
    parser.add_argument("--max-episodes", type=int, default=2)
    args = parser.parse_args()
    args.output_json = args.output_json.resolve()

    if not os.environ.get("LIBERO_LATENT_CACHE_ROOT"):
        raise RuntimeError("LIBERO_LATENT_CACHE_ROOT is required")
    if not os.environ.get("LIBERO_ROOT"):
        raise RuntimeError("LIBERO_ROOT is required")

    # Force cache-only verification off; the runtime guard should not encode VAE.
    os.environ["LIBERO_LATENT_CACHE_VERIFY_RATIO"] = "0.0"
    os.environ["LIBERO_MAX_EPISODES"] = str(args.max_episodes)
    # 必须在父进程取样，才能让 MP4 decode hook 覆盖所有可能的调用。
    os.environ["LIBERO_NUM_WORKERS"] = "0"

    from cosmos_framework.data.generator.action.datasets import libero_lerobot_dataset as _dataset_mod
    from cosmos_framework.model.generator.tokenizers import wan2pt2_vae_4x16x16 as _vae_mod
    from lerobot.datasets import video_utils as _video_utils

    decode_calls = 0
    torchcodec_decode_calls = 0
    vae_interface_encode_calls = 0
    vae_encode_calls = 0

    original_load_video = _dataset_mod.LIBEROLeRobotDataset._load_video
    original_decode_video_frames = _video_utils.decode_video_frames
    original_interface_encode = _vae_mod.Wan2pt2VAEInterface.encode
    original_encode = _vae_mod.WanVAE.encode

    def _counting_load_video(self, episode, timestamps):
        nonlocal decode_calls
        decode_calls += 1
        return original_load_video(self, episode, timestamps)

    def _counting_encode(self, videos, scale):
        nonlocal vae_encode_calls
        vae_encode_calls += 1
        return original_encode(self, videos, scale)

    def _counting_decode_video_frames(*args, **kwargs):
        nonlocal torchcodec_decode_calls
        torchcodec_decode_calls += 1
        return original_decode_video_frames(*args, **kwargs)

    def _counting_interface_encode(self, state):
        nonlocal vae_interface_encode_calls
        vae_interface_encode_calls += 1
        return original_interface_encode(self, state)

    with (
        patch.object(_dataset_mod.LIBEROLeRobotDataset, "_load_video", _counting_load_video),
        patch.object(_video_utils, "decode_video_frames", _counting_decode_video_frames),
        patch.object(_vae_mod.Wan2pt2VAEInterface, "encode", _counting_interface_encode),
        patch.object(_vae_mod.WanVAE, "encode", _counting_encode),
    ):
        from cosmos_framework.configs.toml_config.sft_config import load_experiment_from_toml
        from cosmos_framework.utils.lazy_config import instantiate

        # The composed model config contains project-relative JSON paths.
        os.chdir(_REPO_ROOT / "cosmos-framework")
        # The bare experiment dict is not a runnable config (missing framework-composed
        # keys such as model_parallel); compose through the structured-TOML loader.
        config = load_experiment_from_toml(
            str(_REPO_ROOT / "cosmos-framework/examples/toml/sft_config/action_policy_libero_edge_all.toml")
        )
        # Mirrors cosmos_framework/scripts/train.py: model/dataloader are instantiated
        # from the composed config; ImaginaireTrainer does not own them.
        model = instantiate(config.model)
        dataloader = instantiate(config.dataloader_train)

        start_time = time.time()
        data_iter = iter(dataloader)
        for step in range(args.steps):
            batch = next(data_iter)
            # Forward only; no optimizer step needed for smoke.
            with torch.no_grad():
                _ = model.get_data_and_condition(batch)
        elapsed = time.time() - start_time

    result = {
        "schema_version": "cache_only_forward_smoke_v1",
        "steps": args.steps,
        "max_episodes": args.max_episodes,
        "dataset_load_video_calls": decode_calls,
        "torchcodec_decode_calls": torchcodec_decode_calls,
        "vae_interface_encode_calls": vae_interface_encode_calls,
        "wan_vae_encode_calls": vae_encode_calls,
        "elapsed_s": round(elapsed, 3),
        "status": "PASS"
        if decode_calls == 0 and torchcodec_decode_calls == 0 and vae_interface_encode_calls == 0 and vae_encode_calls == 0
        else "FAIL",
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
