#!/usr/bin/env python3
"""Compare cache builder output vs training path output pixel-by-pixel for one window."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.data.generator.action.utils.transforms import ActionTransformPipeline, VideoResize


def cache_builder_pixels(dataset_root: Path, episode_index: int, start_frame: int, image_size: int = 256):
    """Replicate cache builder path for one window."""
    dataset = LIBEROLeRobotDataset(
        root=str(dataset_root),
        split="full",
        fps=20,
        chunk_length=16,
        camera_mode="concat_view",
        image_size=image_size,
        action_normalization=None,
    )
    episode = dataset._episodes[episode_index]
    row_indices = np.flatnonzero(dataset._row_episode == episode_index)
    timestamps = [float(dataset._row_timestamp[i]) for i in row_indices[start_frame : start_frame + 17]]
    video = dataset._load_video(episode, timestamps)  # [T,C,H,W] float [0,1]
    video_uint8 = (video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
    video_resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    resized = video_resize({"video": video_uint8}, resolution=None)
    return resized["video"], resized["image_size"]


def training_path_pixels(dataset_root: Path, episode_index: int, start_frame: int, image_size: int = 256):
    """Replicate training path for one window."""
    dataset = LIBEROLeRobotDataset(
        root=str(dataset_root),
        split="train",
        fps=20,
        chunk_length=16,
        camera_mode="concat_view",
        image_size=image_size,
        action_normalization="quantile_rot",
        max_episodes=2,
    )
    transform = ActionTransformPipeline(
        tokenizer_config=None,
        cfg_dropout_rate=0.0,
        max_action_dim=64,
        append_viewpoint_info=False,
        append_duration_fps_timestamps=False,
        append_resolution_info=False,
        append_idle_frames=False,
        format_prompt_as_json=False,
    )
    # Find the flat index that maps to this episode/start.
    ep_vals = dataset._ep_vals.tolist() if isinstance(dataset._ep_vals, np.ndarray) else list(dataset._ep_vals)
    if episode_index not in ep_vals:
        raise ValueError(f"episode_index={episode_index} not in training _ep_vals={ep_vals}")
    ep = ep_vals.index(episode_index)
    prev = int(dataset._valid_cum[ep - 1]) if ep > 0 else 0
    local_start = start_frame
    idx = prev + local_start
    sample = dataset[idx]
    sample = transform(sample, resolution=None)
    return sample["video"], sample["image_size"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--episode-index", type=int, default=0)
    parser.add_argument("--start-frame", type=int, default=0)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    cache_pixels, cache_image_size = cache_builder_pixels(args.dataset_root, args.episode_index, args.start_frame)
    train_pixels, train_image_size = training_path_pixels(args.dataset_root, args.episode_index, args.start_frame)

    result = {
        "episode_index": args.episode_index,
        "start_frame": args.start_frame,
        "cache_shape": list(cache_pixels.shape),
        "train_shape": list(train_pixels.shape),
        "cache_image_size": cache_image_size.tolist(),
        "train_image_size": train_image_size.tolist(),
        "shape_match": list(cache_pixels.shape) == list(train_pixels.shape),
        "dtype_match": str(cache_pixels.dtype) == str(train_pixels.dtype),
        "pixel_max_abs_diff": float((cache_pixels.float() - train_pixels.float()).abs().max()),
        "pixel_mean_abs_diff": float((cache_pixels.float() - train_pixels.float()).abs().mean()),
    }
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
