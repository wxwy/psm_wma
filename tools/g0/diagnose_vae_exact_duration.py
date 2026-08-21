#!/usr/bin/env python3
"""Compare VAE encode output with/without encode_exact_durations=[17]."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface


class _Adapter:
    def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
        self.tokenizer_vision_gen = tokenizer
        self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

    def encode(self, state: torch.Tensor) -> torch.Tensor:
        return self.tokenizer_vision_gen.encode(state)

    _normalize_uint8_vision_item = OmniMoTModel._normalize_uint8_vision_item


def encode_window(raw_uint8: torch.Tensor, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> torch.Tensor:
    encoder = _Adapter(tokenizer, device)
    normalized = encoder._normalize_uint8_vision_item(raw_uint8.unsqueeze(0).to(device))
    latent = OmniMoTModel._encode_vision_item(encoder, normalized, num_views=1, frames_per_view=None)
    return latent.float().cpu()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--episode-index", type=int, default=0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    device = torch.device("cuda")
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

    tok_exact = Wan2pt2VAEInterface(vae_path=str(args.vae_path), encode_exact_durations=[17])
    tok_exact.model.model.to(device)
    latent_exact = encode_window(raw_uint8, tok_exact, device)

    tok_default = Wan2pt2VAEInterface(vae_path=str(args.vae_path))
    tok_default.model.model.to(device)
    latent_default = encode_window(raw_uint8, tok_default, device)

    shape_match = tuple(latent_exact.shape) == tuple(latent_default.shape)
    result = {
        "shape_match": shape_match,
        "exact_shape": list(latent_exact.shape),
        "default_shape": list(latent_default.shape),
        "max_abs_diff": float((latent_exact - latent_default).abs().max()) if shape_match else None,
        "mean_abs_diff": float((latent_exact - latent_default).abs().mean()) if shape_match else None,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
