#!/usr/bin/env python3
"""从已缓存的 episode 窗口生成在线 VAE probe 格式输出。

不依赖训练流程，直接：
1. 读 cache 的 episode_000000.pt；
2. 按 window key 从 LIBERO 视频解码对应 17 帧 uint8；
3. 走训练同一条 _encode_vision_item 路径得到 online latent；
4. 保存 raw_uint8.pt / online_latent.pt / meta.json。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.data.generator.action.utils.transforms import VideoResize
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
from cosmos_framework.model.generator.vision_vae import (
    LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
    encode_uint8_vision_item,
)


class _VisionEncoderAdapter:
    def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
        self.tokenizer_vision_gen = tokenizer
        self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

    def encode(self, state: torch.Tensor) -> torch.Tensor:
        return self.tokenizer_vision_gen.encode(state)

def _online_encode(raw_uint8: torch.Tensor, encoder: _VisionEncoderAdapter, device: torch.device) -> torch.Tensor:
    """Exact training-time path: uint8 [C,T,H,W] -> shared VAE entry -> [1,C,T,H,W]."""
    if raw_uint8.dtype != torch.uint8 or raw_uint8.ndim != 4:
        raise ValueError(f"Expected uint8 [C,T,H,W], got {tuple(raw_uint8.shape)} {raw_uint8.dtype}")
    latent = encode_uint8_vision_item(encoder, raw_uint8.unsqueeze(0).to(device))
    return latent.float().cpu()  # [1, C, T_latent, H, W]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--episode-index", type=int, default=0)
    parser.add_argument("--max-windows", type=int, default=20)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    device = torch.device(args.device)
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
        encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    )
    tokenizer.model.model.to(device).eval()
    encoder = _VisionEncoderAdapter(tokenizer, device)
    video_resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)

    episode = dataset._episodes[args.episode_index]
    row_indices = np.flatnonzero(dataset._row_episode == args.episode_index)

    cache_item = torch.load(
        args.cache_root / "episodes" / f"episode_{args.episode_index:06d}.pt",
        map_location="cpu",
        weights_only=True,
    )
    cached_windows = cache_item["windows"]

    output_root = args.output_root / f"rank_{0:02d}"
    output_root.mkdir(parents=True, exist_ok=True)

    saved = 0
    for start_str in sorted(cached_windows.keys(), key=int):
        if saved >= args.max_windows:
            break
        start = int(start_str)
        timestamps = [float(dataset._row_timestamp[i]) for i in row_indices[start : start + 17]]
        video = dataset._load_video(episode, timestamps)
        raw_uint8 = (video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
        raw_uint8 = video_resize({"video": raw_uint8}, resolution=None)["video"]

        with torch.inference_mode():
            online_latent = _online_encode(raw_uint8, encoder, device)

        sample_dir = output_root / f"sample_{saved:06d}"
        sample_dir.mkdir(exist_ok=True)
        torch.save(raw_uint8, sample_dir / "raw_uint8.pt")
        torch.save(online_latent, sample_dir / "online_latent.pt")
        meta = {
            "iteration": 0,
            "episode_index": args.episode_index,
            "start_frame": start,
            "task_index": int(dataset._row_task[row_indices[start]]),
            "dataset_name": args.dataset_root.name,
            "num_views": 1,
            "frames_per_view": None,
            "raw_shape": list(raw_uint8.shape),
            "raw_dtype": str(raw_uint8.dtype),
            "latent_shape": list(online_latent.shape),
            "latent_dtype": str(online_latent.dtype),
            "vae_compute_dtype": str(tokenizer.dtype),
            "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
            "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
        }
        (sample_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"saved {sample_dir} episode={args.episode_index} start={start}")
        saved += 1

    print(f"Done: saved {saved} samples to {output_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
