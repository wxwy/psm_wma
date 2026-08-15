#!/usr/bin/env python3
"""Generate R06 cache/online parity evidence for four non-zero window offsets.

This is a probe, not a training run.  It encodes the same 17-frame windows with
the Wan VAE and compares them to the corresponding R12 episode slices.  The
reported ``loss_max_abs_diff`` is the latent MSE-to-zero proxy; a training-side
loss callback may replace it before enabling the cache.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface


def encode_window(video: torch.Tensor, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> torch.Tensor:
    pixels = video.to(device=device, dtype=torch.float32).div(127.5).sub(1.0)
    padded = 1 + ((pixels.shape[1] - 1 + 3) // 4) * 4
    if padded > pixels.shape[1]:
        pixels = torch.cat([pixels, pixels[:, -1:].expand(-1, padded - pixels.shape[1], -1, -1)], dim=1)
    with torch.inference_mode():
        return tokenizer.encode(pixels.unsqueeze(0)).squeeze(0).float().cpu()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--cache-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episode-index", type=int, default=0)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    device = torch.device(args.device)
    dataset = LIBEROLeRobotDataset(
        root=str(args.dataset_root), split="full", fps=20, chunk_length=16,
        camera_mode="concat_view", image_size=256, action_normalization=None,
    )
    tokenizer = Wan2pt2VAEInterface(vae_path=str(args.vae_path))
    tokenizer.model.model.to(device)
    episode = dataset._episodes[args.episode_index]
    row_indices = np.flatnonzero(dataset._row_episode == args.episode_index)
    cache_item = torch.load(
        args.cache_root / "episodes" / f"episode_{args.episode_index:06d}.pt",
        map_location="cpu", weights_only=True,
    )
    cached = cache_item["latents"]["cosmos_concat_view"].float()
    source_indices = cache_item["indices"]["source_frame_indices"].long()
    rows: list[dict[str, object]] = []
    for start in (1, 2, 3, 4, 5):
        timestamps = [float(dataset._row_timestamp[i]) for i in row_indices[start : start + 17]]
        video = dataset._load_video(episode, timestamps)
        online = encode_window(torch.round(video * 255).clamp(0, 255).to(torch.uint8).permute(1, 0, 2, 3), tokenizer, device)
        aligned = start - start % 4
        positions = torch.searchsorted(source_indices, torch.arange(aligned, aligned + 17, 4))
        cache_window = cached[positions]
        latent_diff = float((cache_window - online.permute(1, 0, 2, 3)).abs().max())
        cache_loss = float(cache_window.square().mean())
        online_loss = float(online.square().mean())
        rows.append({
            "start_frame": start, "start_mod_4": start % 4, "aligned_start_frame": aligned,
            "semantic_shift_frames": start - aligned, "latent_max_abs_diff": latent_diff,
            "loss_max_abs_diff": abs(cache_loss - online_loss),
        })
    result = {
        "status": "PASS" if all(r["latent_max_abs_diff"] <= 1e-5 and r["loss_max_abs_diff"] <= 1e-5 for r in rows) else "FAIL",
        "episode_index": args.episode_index, "windows": rows,
        "latent_max_abs_diff": max(float(r["latent_max_abs_diff"]) for r in rows),
        "loss_max_abs_diff": max(float(r["loss_max_abs_diff"]) for r in rows),
        "coverage_start_mod_4": sorted({int(r["start_mod_4"]) for r in rows}),
        "loss_definition": "mean(latent ** 2), proxy pending training-side loss callback",
        "cache_policy": "aligned_start=start-(start%4), semantic_shift recorded per window",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
