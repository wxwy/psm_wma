#!/usr/bin/env python3
"""Compare cache builder full-episode path vs per-window training path."""

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


class _Adapter:
    def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
        self.tokenizer_vision_gen = tokenizer
        self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

    def encode(self, state: torch.Tensor) -> torch.Tensor:
        return self.tokenizer_vision_gen.encode(state)

    _normalize_uint8_vision_item = OmniMoTModel._normalize_uint8_vision_item


def vae_encode(uint8_window: torch.Tensor, adapter: _Adapter) -> torch.Tensor:
    """uint8 [C,T,H,W] -> latent [T_latent,C_latent,H,W] fp32."""
    normalized = adapter._normalize_uint8_vision_item(uint8_window.unsqueeze(0))
    latent = OmniMoTModel._encode_vision_item(adapter, normalized, num_views=1, frames_per_view=None)
    return latent.squeeze(0).permute(1, 0, 2, 3).cpu().float()


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
    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=[17, 61, 73],
        encode_chunk_frames={"256": 68, "480": 24, "720": 8, "768": 8},
    )
    tokenizer.model.model.to(device)
    adapter = _Adapter(tokenizer, device)
    video_resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)

    episode = dataset._episodes[args.episode_index]
    row_indices = np.flatnonzero(dataset._row_episode == args.episode_index)

    # Full-episode path (cache builder style).
    full_timestamps = [float(dataset._row_timestamp[i]) for i in row_indices]
    full_video = dataset._load_video(episode, full_timestamps)  # [T,C,H,W]
    full_uint8 = (full_video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
    full_resized = video_resize({"video": full_uint8}, resolution=None)
    full_window_uint8 = full_resized["video"][:, args.start_frame : args.start_frame + 17].contiguous()

    # Per-window path (training style).
    win_timestamps = [float(dataset._row_timestamp[i]) for i in row_indices[args.start_frame : args.start_frame + 17]]
    win_video = dataset._load_video(episode, win_timestamps)  # [17,C,H,W]
    win_uint8 = (win_video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
    win_resized = video_resize({"video": win_uint8}, resolution=None)
    win_window_uint8 = win_resized["video"].contiguous()

    pixel_diff = (full_window_uint8.float() - win_window_uint8.float()).abs()

    with torch.inference_mode():
        full_latent = vae_encode(full_window_uint8.to(device), adapter)
        win_latent = vae_encode(win_window_uint8.to(device), adapter)

    latent_diff = (full_latent - win_latent).abs()

    result = {
        "episode_index": args.episode_index,
        "start_frame": args.start_frame,
        "shape": list(full_window_uint8.shape),
        "pixel_max_abs_diff": float(pixel_diff.max()),
        "pixel_mean_abs_diff": float(pixel_diff.mean()),
        "latent_max_abs_diff": float(latent_diff.max()),
        "latent_mean_abs_diff": float(latent_diff.mean()),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
