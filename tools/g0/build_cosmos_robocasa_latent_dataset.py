#!/usr/bin/env python3
"""构建 RoboCasa LeRobot 三视角 exact-window latent cache。"""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

import numpy as np
import torch

from exact_window_cache import VisionEncoderAdapter, encode_window, to_training_uint8, window_indices, write_atomic
from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import RoboCasaLeRobotDataset
from cosmos_framework.data.generator.action.utils.transforms import VideoResize
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
from cosmos_framework.model.generator.vision_vae import (
    LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
)


def _revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _task_roots(source_root: Path, category: str) -> list[Path]:
    roots = sorted(source_root.glob(f"{category}/*/*/lerobot"))
    if not roots:
        raise FileNotFoundError(f"No RoboCasa LeRobot task roots under {source_root / category}")
    return roots


def _build_task(
    dataset: RoboCasaLeRobotDataset,
    output_root: Path,
    encoder: VisionEncoderAdapter,
    device: torch.device,
    video_resize: VideoResize,
    *,
    episode_limit: int | None,
    vae_path: Path,
    revision: str,
) -> dict[str, object]:
    episodes_dir = output_root / "tasks" / dataset.task_slug / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    episode_ids = [int(value) for value in dataset._ep_vals]
    if episode_limit is not None:
        episode_ids = episode_ids[:episode_limit]
    for episode_index in episode_ids:
        output_path = episodes_dir / f"episode_{episode_index:06d}.pt"
        if output_path.is_file():
            cached = torch.load(output_path, map_location="cpu", weights_only=True)
            if cached.get("format") == "exact_window_v1" and cached.get("task_id") == dataset.task_id:
                rows.append(cached["metadata"]["manifest_row"])
                continue
        row_indices = np.flatnonzero(dataset._row_episode == episode_index)
        timestamps = [float(value) for value in dataset._row_timestamp[row_indices]]
        video = dataset._load_video(dataset._episodes[episode_index], timestamps)
        if len(row_indices) != len(timestamps) or int(video.shape[0]) != len(row_indices):
            raise ValueError(
                "RoboCasa episode frame alignment mismatch: "
                f"task={dataset.task_id} episode={episode_index} "
                f"parquet_rows={len(row_indices)} timestamps={len(timestamps)} decoded_frames={video.shape[0]}"
            )
        video_uint8 = video_resize({"video": to_training_uint8(video)}, resolution=None)["video"]
        if video_uint8.shape[1] < 17:
            print(
                f"[skip] task={dataset.task_id} episode={episode_index:06d} "
                f"has only {video_uint8.shape[1]} frames (<17)",
                flush=True,
            )
            continue
        windows: dict[str, dict[str, object]] = {}
        latent_shape: list[int] | None = None
        for start in range(int(video_uint8.shape[1]) - 16):
            latent = encode_window(video_uint8[:, start : start + 17], encoder, device=device)
            frame_indices, anchor_indices = window_indices(start)
            latent_shape = list(latent.shape) if latent_shape is None else latent_shape
            windows[str(start)] = {
                "latent": latent,
                "window_frame_indices": frame_indices,
                "latent_source_frame_indices": anchor_indices,
                "global_row_indices": torch.from_numpy(np.asarray(row_indices[start : start + 17], dtype=np.int64)),
            }
        manifest_row = {
            "task_id": dataset.task_id,
            "task_slug": dataset.task_slug,
            "episode_index": episode_index,
            "episode_path": str(output_path),
            "window_count": len(windows),
            "source_video_frames": int(video_uint8.shape[1]),
            "latent_shape": latent_shape or [5, 48, 24, 16],
        }
        metadata = {
            "format": "exact_window_v1",
            "task_id": dataset.task_id,
            "task_slug": dataset.task_slug,
            "episode_index": episode_index,
            "camera_layout": "wrist_top_agentview_lr_bottom",
            "camera_keys": ["robot0_eye_in_hand", "robot0_agentview_left", "robot0_agentview_right"],
            "source_view_size": [256, 256],
            "agentview_resize": [128, 128],
            "composed_output_size": [384, 256],
            "vae_canvas_size": [int(video_uint8.shape[2]), int(video_uint8.shape[3])],
            "window_frames": 17,
            "vae_path": str(vae_path),
            "script_revision": revision,
            "manifest_row": manifest_row,
        }
        write_atomic({"format": "exact_window_v1", "task_id": dataset.task_id, "episode_index": episode_index, "windows": windows, "metadata": metadata}, output_path)
        rows.append(manifest_row)
        print(f"[write] task={dataset.task_id} episode={episode_index:06d} windows={len(windows)}", flush=True)
    return {"task_id": dataset.task_id, "task_slug": dataset.task_slug, "source_dataset": str(dataset._root), "episodes": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="RoboCasa target root containing atomic/ and composite/")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--suite", choices=("robocasa365_atomic", "robocasa365_composite"), required=True)
    parser.add_argument("--episode-limit", type=int, default=None)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for RoboCasa latent encoding")
    category = args.suite.removeprefix("robocasa365_")
    device = torch.device(args.device)
    torch.backends.cudnn.benchmark = False
    tokenizer = Wan2pt2VAEInterface(vae_path=str(args.vae_path), encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS, encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES)
    tokenizer.model.model.to(device).eval()
    encoder = VisionEncoderAdapter(tokenizer, device)
    resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    revision = _revision()
    task_rows = [_build_task(RoboCasaLeRobotDataset(str(root)), args.output_root, encoder, device, resize, episode_limit=args.episode_limit, vae_path=args.vae_path, revision=revision) for root in _task_roots(args.source_root, category)]
    episode_rows = [row for task in task_rows for row in task["episodes"]]
    latent_shapes = {tuple(row["latent_shape"]) for row in episode_rows}
    if len(latent_shapes) > 1:
        raise ValueError(f"RoboCasa cache requires one latent shape per suite, got {sorted(latent_shapes)}")
    manifest_latent_shape = list(next(iter(latent_shapes), (5, 48, 20, 12)))
    manifest = {
        "schema_version": "exact_window_v1", "suite": args.suite, "source_dataset": str(args.source_root),
        "source_format": "lerobot_v2.1", "chunk_length": 16, "camera_mode": "wrist_top_agentview_lr_bottom",
        "camera_keys": ["robot0_eye_in_hand", "robot0_agentview_left", "robot0_agentview_right"], "sample_stride": 1,
        "fps": 20.0, "latent_shape": manifest_latent_shape, "action_shape": [12], "state_shape": [16],
        "composed_output_size": [384, 256], "vae_canvas_size_policy": "VideoResize resolution=None tier-256",
        "vae_encode_contract": {"compute_dtype": str(tokenizer.dtype), "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS, "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES},
        "cudnn_benchmark": False, "script_revision": revision, "task_count": len(task_rows), "episode_count": len(episode_rows),
        "window_count": sum(int(row["window_count"]) for row in episode_rows), "tasks": task_rows,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"suite": args.suite, "task_count": len(task_rows), "episode_count": len(episode_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
