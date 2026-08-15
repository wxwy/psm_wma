#!/usr/bin/env python3
"""按 Cosmos OmniMoT 的视觉编码契约生成 RGB latent 缓存。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface


def _normalize(state: torch.Tensor) -> torch.Tensor:
    if state.dtype != torch.uint8:
        raise TypeError(f"Cosmos RGB cache expects uint8 pixels, got {state.dtype}.")
    return state.to(dtype=torch.float32).div(127.5).sub(1.0)


@torch.inference_mode()
def encode_cosmos_rgb(
    rgb: torch.Tensor,
    tokenizer: Wan2pt2VAEInterface,
    *,
    num_views: int,
    frames_per_view: int,
) -> torch.Tensor:
    """复用 OmniMoTModel._encode_vision_item 的 camera-major 语义。"""
    if rgb.ndim not in (4, 5):
        raise ValueError(f"RGB must have [C,T,H,W] or [B,C,T,H,W], got {tuple(rgb.shape)}")
    temporal_dim = rgb.ndim - 3
    expected_frames = num_views * frames_per_view
    if int(rgb.shape[temporal_dim]) != expected_frames:
        raise ValueError(
            f"RGB temporal length must equal num_views*frames_per_view={expected_frames}, "
            f"got {int(rgb.shape[temporal_dim])}."
        )
    encoded_views: list[torch.Tensor] = []
    for view_idx in range(num_views):
        view = rgb.narrow(temporal_dim, view_idx * frames_per_view, frames_per_view)
        normalized = _normalize(view)
        had_batch = normalized.ndim == 5
        if not had_batch:
            normalized = normalized.unsqueeze(0)
        encoded = tokenizer.encode(normalized).contiguous().float()
        encoded_views.append(encoded if had_batch else encoded.squeeze(0))
    return torch.cat(encoded_views, dim=temporal_dim)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="torch.save 保存的 RGB tensor")
    parser.add_argument("--output", type=Path, required=True, help="输出 torch.save latent cache")
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--num-views", type=int, default=1)
    parser.add_argument("--frames-per-view", type=int, required=True)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    if args.num_views < 1 or args.frames_per_view < 1:
        raise ValueError("num_views 和 frames_per_view 必须为正整数")
    rgb = torch.load(args.input, map_location="cpu", weights_only=True)
    if not isinstance(rgb, torch.Tensor):
        raise TypeError(f"input must contain a tensor, got {type(rgb).__name__}")
    if not torch.cuda.is_available() and args.device.startswith("cuda"):
        raise RuntimeError("CUDA is required for the Cosmos Wan VAE cache builder.")
    device = torch.device(args.device)
    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=[args.frames_per_view],
    )
    tokenizer.model.model.to(device)
    latent = encode_cosmos_rgb(
        rgb.to(device),
        tokenizer,
        num_views=args.num_views,
        frames_per_view=args.frames_per_view,
    ).cpu()
    if not torch.isfinite(latent).all():
        raise FloatingPointError("Cosmos RGB latent contains NaN/Inf")
    metadata = {
        "encoder": "cosmos_omnimot._encode_vision_item",
        "normalization": "uint8 / 127.5 - 1.0",
        "layout": "camera-major concatenation on temporal axis",
        "num_views": args.num_views,
        "frames_per_view": args.frames_per_view,
        "input_shape": list(rgb.shape),
        "latent_shape": list(latent.shape),
        "temporal_compression_factor": tokenizer.temporal_compression_factor,
        "spatial_compression_factor": tokenizer.spatial_compression_factor,
        "vae_path": str(args.vae_path),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"latent": latent, "metadata": metadata}, args.output)
    print(json.dumps(metadata, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
