#!/usr/bin/env python3
"""构建与 Cosmos 视觉编码契约一致的 LIBERO episode latent store。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
import warnings
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


class _VisionEncoderAdapter:
    """Minimal adapter so the builder calls the exact OmniMoTModel helpers."""

    def __init__(self, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
        self.tokenizer_vision_gen = tokenizer
        self.tensor_kwargs_fp32 = {"device": device, "dtype": torch.float32}

    def encode(self, state: torch.Tensor) -> torch.Tensor:
        return self.tokenizer_vision_gen.encode(state)

def _encode_window(video_uint8: torch.Tensor, encoder: _VisionEncoderAdapter, *, device: torch.device) -> torch.Tensor:
    """Encode one independent 17-frame window via the shared uint8 VAE entry."""
    if video_uint8.ndim != 4 or video_uint8.shape[1] != 17 or video_uint8.dtype != torch.uint8:
        raise ValueError(f"Expected uint8 [C,17,H,W], got {tuple(video_uint8.shape)} {video_uint8.dtype}")
    latent = encode_uint8_vision_item(encoder, video_uint8.unsqueeze(0).to(device))
    return latent.squeeze(0).permute(1, 0, 2, 3).cpu()


def _build_windowed(args: argparse.Namespace, dataset: LIBEROLeRobotDataset, tokenizer: Wan2pt2VAEInterface, device: torch.device) -> None:
    """Build a new, window-keyed store; supports resuming from an interrupted run."""
    episodes_dir = args.output_root / "episodes"
    manifest_path = args.output_root / "dataset_manifest.json"
    is_sharded = args.episode_shard is not None
    if is_sharded:
        shard_manifest_path = args.output_root / f"dataset_manifest_shard_{args.episode_shard:04d}.json"

    # Resume: keep existing valid episode files and manifest rows.
    existing_rows: dict[int, dict[str, object]] = {}
    if manifest_path.is_file():
        existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if existing_manifest.get("schema_version") != "exact_window_v1":
            raise ValueError(f"Cannot resume: existing manifest schema={existing_manifest.get('schema_version')!r}")
        expected_contract = {
            "compute_dtype": "torch.bfloat16",
            "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
            "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
        }
        if existing_manifest.get("vae_encode_contract") != expected_contract:
            raise ValueError(
                "Cannot resume latent cache with a different or missing VAE encoding contract; "
                "build into a new output_root."
            )
        for row in existing_manifest.get("episodes", []):
            existing_rows[int(row["episode_index"])] = row
        print(f"[resume] found {len(existing_rows)} episodes in existing manifest", flush=True)

    args.output_root.mkdir(parents=True, exist_ok=True)
    episodes_dir.mkdir(exist_ok=True)
    revision = _code_revision()
    encoder = _VisionEncoderAdapter(tokenizer, device)
    video_resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    rows_by_episode: dict[int, dict[str, object]] = dict(existing_rows)
    episode_ids = [int(v) for v in dataset._ep_vals]
    if args.task_index is not None:
        episode_ids = [episode for episode in episode_ids if int(dataset._row_task[np.flatnonzero(dataset._row_episode == episode)[0]]) == args.task_index]
    if args.episode_limit is not None:
        episode_ids = episode_ids[: args.episode_limit]
    if is_sharded:
        episode_ids = episode_ids[args.episode_shard::args.num_shards]
        print(f"[shard] processing {len(episode_ids)} episodes (shard {args.episode_shard}/{args.num_shards})", flush=True)

    def _is_complete(episode_index: int) -> bool:
        path = episodes_dir / f"episode_{episode_index:06d}.pt"
        if not path.is_file():
            return False
        if episode_index not in rows_by_episode:
            return False
        try:
            cached = torch.load(path, map_location="cpu", weights_only=True)
            return cached.get("format") == "exact_window_v1" and int(cached.get("episode_index", -1)) == episode_index
        except Exception:
            return False

    for episode_index in episode_ids:
        if _is_complete(episode_index):
            print(f"[skip] episode={episode_index:06d} already complete", flush=True)
            continue
        row_indices = np.flatnonzero(dataset._row_episode == episode_index)
        timestamps = [float(dataset._row_timestamp[i]) for i in row_indices]
        video = dataset._load_video(dataset._episodes[episode_index], timestamps)
        # Match the training path exactly: _build_result() first converts float [0,1]
        # [T,C,H,W] to uint8 and permutes to [C,T,H,W]; ActionTransformPipeline then
        # applies VideoResize on the uint8 tensor.  We must apply VideoResize after
        # uint8 conversion, otherwise bicubic resize operates on float [0,1] and the
        # result differs from the online path.
        video_uint8 = (video * 255.0).clamp(0.0, 255.0).to(torch.uint8).permute(1, 0, 2, 3).contiguous()
        resized = video_resize({"video": video_uint8}, resolution=None)
        video_uint8 = resized["video"]
        image_size = resized["image_size"]  # [target_h, target_w, orig_h_resized, orig_w_resized]
        instructions = _episode_instructions(dataset, episode_index)
        windows: dict[str, dict[str, object]] = {}
        latent_shape: list[int] | None = None
        for start in range(max(0, video_uint8.shape[1] - 16)):
            latent = _encode_window(video_uint8[:, start : start + 17], encoder, device=device)
            if latent_shape is None:
                latent_shape = list(latent.shape)
            windows[str(start)] = {
                "latent": latent.float(),
                "window_frame_indices": torch.arange(start, start + 17, dtype=torch.long),
                "latent_source_frame_indices": torch.arange(start, start + 17, 4, dtype=torch.long),
                "global_row_indices": torch.from_numpy(np.asarray(row_indices[start : start + 17], dtype=np.int64)),
            }
        metadata = {
            "episode_index": episode_index, "source_video_frames": int(video_uint8.shape[1]),
            "window_frames": 17, "image_size": args.image_size,
            "target_h": int(image_size[0].item()), "target_w": int(image_size[1].item()),
            "orig_h_resized": int(image_size[2].item()), "orig_w_resized": int(image_size[3].item()),
            "format": "exact_window_v1", "episode_index": episode_index,
            "encoder": "Wan2pt2VAEInterface.encode independent window",
            "normalization": "uint8 / 127.5 - 1.0", "input_layout": "[C,T,H,W]",
            "latent_layout": "[T_latent,C_latent,H_latent,W_latent]",
            "camera_layout": "concat_view spatial-left-right", "num_views": 1, "frames_per_view": 17,
            "temporal_compression_factor": 4,
            "vae_path": str(args.vae_path), "script_revision": revision, "task_index": args.task_index,
        }
        _write_atomic(
            {
                "format": "exact_window_v1",
                "episode_index": episode_index,
                "windows": windows,
                "language": {"instruction": instructions[0], "instructions": instructions},
                "metadata": metadata,
            },
            episodes_dir / f"episode_{episode_index:06d}.pt",
        )
        rows_by_episode[episode_index] = {
            "episode_index": episode_index,
            "episode_path": str(episodes_dir / f"episode_{episode_index:06d}.pt"),
            "window_count": len(windows),
            "image_size": args.image_size,
            "target_h": metadata["target_h"],
            "target_w": metadata["target_w"],
            "latent_shape": latent_shape if latent_shape is not None else [5, 48, 16, 32],
        }
        print(f"[write] episode={episode_index:06d} windows={len(windows)} latent_shape={rows_by_episode[episode_index]['latent_shape']}", flush=True)
    rows = [rows_by_episode[i] for i in sorted(rows_by_episode)]
    manifest_latent_shape = rows[0]["latent_shape"] if rows else [5, 48, 16, 32]
    manifest = {"schema_version": "exact_window_v1", "suite": args.suite, "source_dataset": str(args.dataset_root), "image_size": args.image_size, "chunk_length": dataset._chunk_length, "camera_mode": dataset._camera_mode, "sample_stride": dataset._sample_stride, "fps": dataset._fps, "latent_shape": manifest_latent_shape, "vae_path": str(args.vae_path), "vae_encode_contract": {"compute_dtype": str(tokenizer.dtype), "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS, "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES}, "script_revision": revision, "task_index": args.task_index, "episode_count": len(rows), "window_count": sum(int(row["window_count"]) for row in rows), "episodes": rows}
    if is_sharded:
        manifest["episode_shard"] = args.episode_shard
        manifest["num_shards"] = args.num_shards
        shard_manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_root": str(args.output_root), "shard_manifest": str(shard_manifest_path), "episodes_written": len(rows), "episodes_skipped": len(existing_rows)}, ensure_ascii=False))
    else:
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output_root": str(args.output_root), "episodes_written": len(rows), "episodes_skipped": len(existing_rows)}, ensure_ascii=False))


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
    parser.add_argument("--windowed", action="store_true", help="Build independent 17-frame windows in a new store")
    parser.add_argument("--task-index", type=int, default=None)
    parser.add_argument("--suite", default=None, help="Suite name; defaults to --dataset-root basename.")
    parser.add_argument("--episode-shard", type=int, default=None, help="Shard index for parallel episode builds.")
    parser.add_argument("--num-shards", type=int, default=None, help="Total number of parallel episode shards.")
    args = parser.parse_args()
    if args.suite is None:
        args.suite = args.dataset_root.name
    if (args.episode_shard is None) != (args.num_shards is None):
        raise ValueError("--episode-shard and --num-shards must be provided together")
    if args.num_shards is not None and args.num_shards <= 0:
        raise ValueError(f"--num-shards must be positive, got {args.num_shards}")
    if args.episode_shard is not None and not 0 <= args.episode_shard < args.num_shards:
        raise ValueError(f"--episode-shard must be in [0,{args.num_shards}), got {args.episode_shard}")

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
    # Use the exact VAE config as the online training path.  The LIBERO action
    # recipe overrides encode_exact_durations and encode_chunk_frames; any
    # deviation in chunking changes the causal-convolution accumulation order
    # and produces ~3e-2 max_abs_diff.
    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    )
    tokenizer.model.model.to(device)
    if args.windowed:
        _build_windowed(args, dataset, tokenizer, device)
        return
    warnings.warn(
        "The legacy non-windowed R12 cache does not satisfy exact_window_v1 and must not be used for cache training; "
        "pass --windowed instead.",
        FutureWarning,
        stacklevel=2,
    )
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
