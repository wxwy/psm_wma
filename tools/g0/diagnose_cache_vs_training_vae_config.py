#!/usr/bin/env python3
"""Compare cache builder latent vs VAE encode with training's exact tokenizer config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.data.generator.action.utils.transforms import VideoResize
from cosmos_framework.model.generator.omni_mot_model import OmniMoTModel
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
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

    # Apply the same VideoResize as the training dataloader/cache builder.
    video_resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    resized = video_resize({"video": raw_uint8}, resolution=None)
    raw_uint8 = resized["video"]

    # Load cached latent.
    cache_item = torch.load(
        args.cache_root / "episodes" / f"episode_{args.episode_index:06d}.pt",
        map_location="cpu",
        weights_only=True,
    )
    cached_latent = cache_item["windows"][str(args.start_frame)]["latent"].float()  # [T_latent,C_latent,H,W]

    # Encode with training's exact VAE config, matching the model path:
    # uint8 [B,C,T,H,W] -> normalize to [-1,1] fp32 -> VAE encode -> fp32.
    class _Adapter:
        def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
            self.tokenizer_vision_gen = tokenizer
            self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}
        def encode(self, state: torch.Tensor) -> torch.Tensor:
            return self.tokenizer_vision_gen.encode(state)
        _normalize_uint8_vision_item = OmniMoTModel._normalize_uint8_vision_item

    train_tok = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=[17, 61, 73],
        encode_chunk_frames={"256": 68, "480": 24, "720": 8, "768": 8},
    )
    train_tok.model.model.to(device)
    encoder = _Adapter(train_tok, device)
    with torch.inference_mode():
        normalized = encoder._normalize_uint8_vision_item(raw_uint8.unsqueeze(0).to(device))
        train_latent = OmniMoTModel._encode_vision_item(
            encoder, normalized, num_views=1, frames_per_view=None
        ).float().cpu().squeeze(0)  # [C,T,H,W]
        train_latent = train_latent.permute(1, 0, 2, 3).contiguous()  # [T,C,H,W] to match cache layout

    shape_match = tuple(cached_latent.shape) == tuple(train_latent.shape)
    result = {
        "episode_index": args.episode_index,
        "start_frame": args.start_frame,
        "cache_shape": list(cached_latent.shape),
        "train_shape": list(train_latent.shape),
        "shape_match": shape_match,
        "max_abs_diff": float((cached_latent - train_latent).abs().max()) if shape_match else None,
        "mean_abs_diff": float((cached_latent - train_latent).abs().mean()) if shape_match else None,
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
