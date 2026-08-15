#!/usr/bin/env python3
"""构建与 Cosmos 视觉编码契约一致的 LIBERO episode latent store。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import numpy as np
import torch

from cosmos_framework.data.generator.action.datasets.libero_lerobot_dataset import LIBEROLeRobotDataset
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface


def _encode_episode(
    video_uint8: torch.Tensor,
    tokenizer: Wan2pt2VAEInterface,
    *,
    device: torch.device,
) -> torch.Tensor:
    if video_uint8.ndim != 4 or video_uint8.dtype != torch.uint8:
        raise ValueError(f"Expected uint8 [C,T,H,W], got {tuple(video_uint8.shape)} {video_uint8.dtype}")
    normalized = video_uint8.to(device=device, dtype=torch.float32).div(127.5).sub(1.0)
    padded_frames = 1 + ((normalized.shape[1] - 1 + 3) // 4) * 4
    if padded_frames != normalized.shape[1]:
        normalized = torch.cat(
            [normalized, normalized[:, -1:, :, :].expand(-1, padded_frames - normalized.shape[1], -1, -1)],
            dim=1,
        )
    with torch.inference_mode():
        latent = tokenizer.encode(normalized.unsqueeze(0)).squeeze(0).float()
    if not torch.isfinite(latent).all():
        raise FloatingPointError("Cosmos latent contains NaN/Inf")
    return latent.cpu()


def _episode_instructions(dataset: LIBEROLeRobotDataset, episode_index: int) -> list[str]:
    episode = dataset._episodes[episode_index]
    tasks = episode.get("tasks")
    if isinstance(tasks, list) and tasks and isinstance(tasks[0], str):
        return [str(task).strip() for task in tasks if str(task).strip()]
    else:
        task_index = int(tasks[0]) if isinstance(tasks, list) else int(episode.get("task_index", 0))
        task = dataset._tasks[task_index]
        return [part.strip() for part in str(task).split(" | ") if part.strip()]


def _code_revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _write_atomic(payload: dict[str, object], output_path: Path) -> None:
    temporary_path = output_path.with_suffix(output_path.suffix + ".tmp")
    torch.save(payload, temporary_path)
    os.replace(temporary_path, output_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument("--episode-limit", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    if not torch.cuda.is_available() and args.device.startswith("cuda"):
        raise RuntimeError("CUDA is required for Cosmos LIBERO latent encoding")
    device = torch.device(args.device)
    dataset = LIBEROLeRobotDataset(
        root=str(args.dataset_root),
        split="full",
        fps=20,
        chunk_length=16,
        camera_mode="concat_view",
        image_size=args.image_size,
        action_normalization=None,
    )
    tokenizer = Wan2pt2VAEInterface(vae_path=str(args.vae_path))
    tokenizer.model.model.to(device)
    episode_ids = [int(v) for v in dataset._ep_vals]
    if args.episode_limit is not None:
        episode_ids = episode_ids[: args.episode_limit]
    episodes_dir = args.output_root / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_root / "dataset_manifest.json"
    manifest_rows_by_episode: dict[int, dict[str, object]] = {}
    if manifest_path.is_file():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for row in existing_manifest.get("episodes", []):
            manifest_rows_by_episode[int(row["episode_index"])] = row
    code_revision = _code_revision()
    started = time.monotonic()
    for ordinal, episode_index in enumerate(episode_ids, start=1):
        output_path = episodes_dir / f"episode_{episode_index:06d}.pt"
        if output_path.exists():
            try:
                cached = torch.load(output_path, map_location="cpu", weights_only=True)
                metadata = cached.get("metadata", {})
                latent = cached["latents"]["cosmos_concat_view"]
                if metadata.get("image_size") == args.image_size and torch.isfinite(latent).all():
                    manifest_rows_by_episode.setdefault(
                        episode_index,
                        {
                            "episode_index": episode_index,
                            "episode_path": str(output_path),
                            "video_frames": int(metadata["source_video_frames"]),
                            "latent_frames": int(latent.shape[0]),
                            "latent_shape": list(latent.shape),
                            "instructions": cached["language"].get("instructions", []),
                            "image_size": args.image_size,
                        },
                    )
                    print(f"[skip] episode={episode_index}", flush=True)
                    continue
            except (OSError, KeyError, RuntimeError, ValueError):
                pass
        row_indices = np.flatnonzero(dataset._row_episode == episode_index)
        timestamps = [float(dataset._row_timestamp[i]) for i in row_indices]
        video = dataset._load_video(dataset._episodes[episode_index], timestamps)
        video_uint8 = torch.round(video * 255.0).clamp(0, 255).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
        latent = _encode_episode(video_uint8, tokenizer, device=device)
        source_indices = np.minimum(np.arange(latent.shape[1], dtype=np.int64) * 4, video_uint8.shape[1] - 1)
        instructions = _episode_instructions(dataset, episode_index)
        metadata = {
            "episode_id": f"episode_{episode_index:06d}",
            "episode_index": episode_index,
            "encoder": "cosmos_omnimot._encode_vision_item",
            "normalization": "uint8 / 127.5 - 1.0",
            "input_layout": "[C,T,H,W]",
            "camera_layout": "concat_view spatial-left-right",
            "latent_layout": "[T_latent,C_latent,H_latent,W_latent]",
            "temporal_compression_factor": tokenizer.temporal_compression_factor,
            "spatial_compression_factor": tokenizer.spatial_compression_factor,
            "source_frame_to_latent_policy": "causal_endpoint",
            "source_video_frames": int(video_uint8.shape[1]),
            "image_size": args.image_size,
            "vae_path": str(args.vae_path),
            "script_revision": code_revision,
            "split": "full",
            "fps": 20,
        }
        payload = {
                "latents": {"cosmos_concat_view": latent.permute(1, 0, 2, 3).to(torch.float16)},
                "indices": {
                    "source_frame_indices": torch.from_numpy(source_indices),
                    "global_row_indices": torch.from_numpy(np.asarray(row_indices, dtype=np.int64)),
                },
                "language": {"instruction": instructions[0], "instructions": instructions},
                "metadata": metadata,
            }
        _write_atomic(payload, output_path)
        manifest_rows_by_episode[episode_index] = {
                "episode_index": episode_index,
                "episode_path": str(output_path),
                "video_frames": int(video_uint8.shape[1]),
                "latent_frames": int(latent.shape[1]),
                "latent_shape": list(latent.permute(1, 0, 2, 3).shape),
                "instructions": instructions,
                "image_size": args.image_size,
            }
        print(f"[{ordinal}/{len(episode_ids)}] episode={episode_index} video={tuple(video_uint8.shape)} latent={tuple(latent.shape)} elapsed={time.monotonic()-started:.1f}s", flush=True)
    manifest_path.write_text(
        json.dumps(
            {
                "source_dataset": str(args.dataset_root),
                "encoder": "cosmos_omnimot._encode_vision_item",
                "normalization": "uint8 / 127.5 - 1.0",
                "camera_layout": "concat_view spatial-left-right",
                "image_size": args.image_size,
                "vae_path": str(args.vae_path),
                "script_revision": code_revision,
                "split": "full",
                "fps": 20,
                "episode_count": len(manifest_rows_by_episode),
                "episodes": [manifest_rows_by_episode[i] for i in sorted(manifest_rows_by_episode)],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"output_root": str(args.output_root), "episodes_written": len(manifest_rows_by_episode)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
