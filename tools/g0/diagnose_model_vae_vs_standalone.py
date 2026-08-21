#!/usr/bin/env python3
"""Compare training-model VAE encode vs fresh standalone VAE encode for the same uint8 window."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.configs.toml_config.sft_config import SFTConfig
from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset


def load_model_vae(toml_path: Path, vae_path: Path):
    """Load OmniMoTModel from checkpoint and return its tokenizer encode fn."""
    cfg = SFTConfig.from_toml(str(toml_path))
    # Patch env-dependent fields
    cfg.model.tokenizer.vae_path = str(vae_path)
    model = OmniMoTModel(cfg.model)
    # set_precision builds tensor_kwargs; setup tokenizers already done in __init__
    model.set_precision()
    return model


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--toml-path", type=Path, required=True)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--episode-index", type=int, default=0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    device = torch.device("cuda")

    # Load raw uint8 window exactly as cache builder does.
    dataset = LIBEROLeRobotDataset(
        root=str(args.dataset_root),
        split="full",
        fps=20,
        chunk_length=16,
        camera_mode="concat_view",
        image_size=256,
        action_normalization=None,
    )
    episode = dataset._episodes[args.episode_index]
    row_indices = np.flatnonzero(dataset._row_episode == args.episode_index)
    timestamps = [float(dataset._row_timestamp[i]) for i in row_indices[args.start_frame : args.start_frame + 17]]
    video = dataset._load_video(episode, timestamps)
    raw_uint8 = (video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()

    # Fresh standalone VAE encode (cache builder style).
    fresh_tok = Wan2pt2VAEInterface(vae_path=str(args.vae_path))
    fresh_tok.model.model.to(device)
    with torch.inference_mode():
        fresh_latent = fresh_tok.encode(raw_uint8.unsqueeze(0).to(device)).float().cpu()

    # Model VAE encode.
    model = load_model_vae(args.toml_path, args.vae_path)
    model = model.to(device)
    with torch.inference_mode():
        model_latent = model.encode(raw_uint8.unsqueeze(0).to(device)).float().cpu()

    shape_match = tuple(fresh_latent.shape) == tuple(model_latent.shape)
    result = {
        "episode_index": args.episode_index,
        "start_frame": args.start_frame,
        "raw_shape": list(raw_uint8.shape),
        "fresh_latent_shape": list(fresh_latent.shape),
        "model_latent_shape": list(model_latent.shape),
        "fresh_dtype": str(fresh_latent.dtype),
        "model_dtype": str(model_latent.dtype),
        "shape_match": shape_match,
        "max_abs_diff": float((fresh_latent - model_latent).abs().max()) if shape_match else None,
        "mean_abs_diff": float((fresh_latent - model_latent).abs().mean()) if shape_match else None,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
