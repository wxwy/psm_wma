#!/usr/bin/env python3
"""构建 RoboCasa LeRobot 可配置多视角 exact-window latent cache。"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import torch

from exact_window_cache import VisionEncoderAdapter, encode_window, to_training_uint8, window_indices, write_atomic
from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (
    RoboCasaLeRobotDataset,
    normalize_robocasa_camera_set,
)
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
    """Accept the RoboCasa root, target root, category root, or a single lerobot root."""
    candidates: list[Path] = []
    if source_root.name == "lerobot":
        candidates = [source_root]
    elif source_root.name == category:
        candidates = sorted(source_root.glob("*/*/lerobot"))
    else:
        candidates = sorted(source_root.glob(f"{category}/*/*/lerobot"))
        if not candidates:
            candidates = sorted(source_root.glob(f"target/{category}/*/*/lerobot"))
    if not candidates:
        raise FileNotFoundError(
            f"No RoboCasa LeRobot task roots for category={category!r} under {source_root}; "
            "accepted roots include .../robocasa365, .../robocasa365/target, or the category directory"
        )
    return candidates


def _episode_selection_score(*, seed: int, task_id: str, episode_index: int) -> bytes:
    payload = f"{seed}:{task_id}:{episode_index}".encode("utf-8")
    return hashlib.sha256(payload).digest()


def _select_episode_ids(
    episode_ids: list[int],
    *,
    task_id: str,
    episode_limit: int | None,
    episode_seed: int,
) -> list[int]:
    """Choose a deterministic, nested per-task episode subset.

    Ranking every episode by a stable SHA256 score makes N=10 a strict subset
    of N=20 for the same seed/task, independent of filesystem/parquet ordering.
    Returned IDs are sorted only for deterministic processing/storage order.
    """
    unique_ids = sorted(set(int(value) for value in episode_ids))
    if episode_limit is None:
        return unique_ids
    if episode_limit <= 0:
        raise ValueError(f"episode_limit must be positive, got {episode_limit}")
    ranked = sorted(
        unique_ids,
        key=lambda episode_index: (
            _episode_selection_score(seed=episode_seed, task_id=task_id, episode_index=episode_index),
            episode_index,
        ),
    )
    return sorted(ranked[:episode_limit])


def _episode_selection_digest(episode_ids: list[int]) -> str:
    payload = ",".join(str(value) for value in episode_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _build_task(
    dataset: RoboCasaLeRobotDataset,
    output_root: Path,
    encoder: VisionEncoderAdapter,
    device: torch.device,
    video_resize: VideoResize,
    *,
    episode_limit: int | None,
    episode_seed: int,
    vae_path: Path,
    revision: str,
) -> dict[str, object]:
    episodes_dir = output_root / "tasks" / dataset.task_slug / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    all_episode_ids = [int(value) for value in dataset._ep_vals]
    episode_ids = _select_episode_ids(
        all_episode_ids,
        task_id=dataset.task_id,
        episode_limit=episode_limit,
        episode_seed=episode_seed,
    )
    selection_digest = _episode_selection_digest(episode_ids)
    for episode_index in episode_ids:
        output_path = episodes_dir / f"episode_{episode_index:06d}.pt"
        if output_path.is_file():
            cached = torch.load(output_path, map_location="cpu", weights_only=True)
            metadata = cached.get("metadata", {})
            cached_camera_set = metadata.get("camera_set", metadata.get("camera_layout"))
            camera_matches = False
            if isinstance(cached_camera_set, str):
                try:
                    camera_matches = normalize_robocasa_camera_set(cached_camera_set) == dataset.camera_set
                except ValueError:
                    camera_matches = False
            if (
                cached.get("format") == "exact_window_v1"
                and cached.get("task_id") == dataset.task_id
                and camera_matches
            ):
                rows.append(metadata["manifest_row"])
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
        if latent_shape is None:
            raise RuntimeError(
                f"RoboCasa episode unexpectedly produced no exact windows after length check: "
                f"task={dataset.task_id} episode={episode_index}"
            )
        composed_h, composed_w = dataset.composed_output_size
        vae_canvas_size = [int(video_uint8.shape[2]), int(video_uint8.shape[3])]
        manifest_row = {
            "task_id": dataset.task_id,
            "task_slug": dataset.task_slug,
            "episode_index": episode_index,
            "episode_path": str(output_path),
            "window_count": len(windows),
            "source_video_frames": int(video_uint8.shape[1]),
            "camera_set": dataset.camera_set,
            "composed_output_size": [composed_h, composed_w],
            "vae_canvas_size": vae_canvas_size,
            "latent_shape": latent_shape,
        }
        metadata = {
            "format": "exact_window_v1",
            "task_id": dataset.task_id,
            "task_slug": dataset.task_slug,
            "episode_index": episode_index,
            "camera_set": dataset.camera_set,
            "camera_layout": dataset.camera_set,
            "camera_keys": list(dataset.camera_keys),
            "source_view_size": [dataset._image_size, dataset._image_size],
            "composed_output_size": [composed_h, composed_w],
            "vae_canvas_size": vae_canvas_size,
            "window_frames": 17,
            "vae_path": str(vae_path),
            "script_revision": revision,
            "manifest_row": manifest_row,
        }
        write_atomic({"format": "exact_window_v1", "task_id": dataset.task_id, "episode_index": episode_index, "windows": windows, "metadata": metadata}, output_path)
        rows.append(manifest_row)
        print(f"[write] task={dataset.task_id} episode={episode_index:06d} windows={len(windows)}", flush=True)
    composed_h, composed_w = dataset.composed_output_size
    return {
        "task_id": dataset.task_id,
        "task_slug": dataset.task_slug,
        "source_dataset": str(dataset._root),
        "camera_set": dataset.camera_set,
        "camera_keys": list(dataset.camera_keys),
        "composed_output_size": [composed_h, composed_w],
        "episode_selection_seed": episode_seed,
        "selected_episode_ids": episode_ids,
        "selected_episode_digest": selection_digest,
        "source_episode_count": len(all_episode_ids),
        "episodes": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="RoboCasa target root containing atomic/ and composite/")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument("--suite", choices=("robocasa365_atomic", "robocasa365_composite"), required=True)
    parser.add_argument(
        "--camera-set",
        choices=("left_wrist", "wrist_lr", "left_wrist_right"),
        default="left_wrist",
        help=(
            "Camera composition before Cosmos resizing: left_wrist=256x512 LIBERO-style; "
            "wrist_lr=384x256 with large wrist over two 128x128 agent views; "
            "left_wrist_right=256x768 three full-resolution horizontal views."
        ),
    )
    parser.add_argument("--episode-limit", type=int, default=None)
    parser.add_argument(
        "--episode-seed",
        type=int,
        default=42,
        help="Stable per-task subset seed. The same seed gives nested N=10 -> N=20 subsets.",
    )
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for RoboCasa latent encoding")
    category = args.suite.removeprefix("robocasa365_")
    existing_manifest_path = args.output_root / "dataset_manifest.json"
    if existing_manifest_path.is_file():
        existing_manifest = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        existing_camera_set = existing_manifest.get("camera_set", existing_manifest.get("camera_mode"))
        if existing_manifest.get("suite") != args.suite:
            raise ValueError(
                f"Output root already contains suite={existing_manifest.get('suite')!r}; requested {args.suite!r}"
            )
        if isinstance(existing_camera_set, str):
            existing_camera_set = normalize_robocasa_camera_set(existing_camera_set)
            if existing_camera_set != args.camera_set:
                raise ValueError(
                    f"Output root already contains camera_set={existing_camera_set!r}; "
                    f"requested {args.camera_set!r}. Use a separate output root per camera layout."
                )

    device = torch.device(args.device)
    torch.backends.cudnn.benchmark = False
    tokenizer = Wan2pt2VAEInterface(vae_path=str(args.vae_path), encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS, encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES)
    tokenizer.model.model.to(device).eval()
    encoder = VisionEncoderAdapter(tokenizer, device)
    resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    revision = _revision()
    task_rows = [
        _build_task(
            RoboCasaLeRobotDataset(str(root), camera_set=args.camera_set),
            args.output_root,
            encoder,
            device,
            resize,
            episode_limit=args.episode_limit,
            episode_seed=args.episode_seed,
            vae_path=args.vae_path,
            revision=revision,
        )
        for root in _task_roots(args.source_root, category)
    ]
    episode_rows = [row for task in task_rows for row in task["episodes"]]
    if not episode_rows:
        raise RuntimeError("RoboCasa cache build produced zero encoded episodes")

    latent_shapes = {tuple(row["latent_shape"]) for row in episode_rows}
    composed_sizes = {tuple(row["composed_output_size"]) for row in episode_rows}
    vae_canvas_sizes = {tuple(row["vae_canvas_size"]) for row in episode_rows}
    camera_sets = {str(row["camera_set"]) for row in episode_rows}
    if len(latent_shapes) != 1:
        raise ValueError(f"RoboCasa cache requires one latent shape per suite, got {sorted(latent_shapes)}")
    if len(composed_sizes) != 1 or len(vae_canvas_sizes) != 1 or camera_sets != {args.camera_set}:
        raise ValueError(
            "RoboCasa cache camera geometry drift: "
            f"camera_sets={sorted(camera_sets)} composed={sorted(composed_sizes)} "
            f"vae_canvas={sorted(vae_canvas_sizes)}"
        )

    manifest_latent_shape = list(next(iter(latent_shapes)))
    manifest_composed_size = list(next(iter(composed_sizes)))
    manifest_vae_canvas_size = list(next(iter(vae_canvas_sizes)))
    camera_keys = list(task_rows[0]["camera_keys"])
    manifest = {
        "schema_version": "exact_window_v1",
        "suite": args.suite,
        "source_dataset": str(args.source_root),
        "source_format": "lerobot_v2.1",
        "chunk_length": 16,
        "camera_mode": args.camera_set,
        "camera_set": args.camera_set,
        "camera_keys": camera_keys,
        "sample_stride": 1,
        "fps": 20.0,
        "latent_shape": manifest_latent_shape,
        "action_shape": [12],
        "state_shape": [16],
        "source_view_size": [256, 256],
        "composed_output_size": manifest_composed_size,
        "vae_canvas_size": manifest_vae_canvas_size,
        "vae_canvas_size_policy": "VideoResize resolution=None auto-tier",
        "vae_encode_contract": {
            "compute_dtype": str(tokenizer.dtype),
            "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
            "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
        },
        "cudnn_benchmark": False,
        "script_revision": revision,
        "episode_limit_per_task": args.episode_limit,
        "episode_selection_seed": args.episode_seed,
        "episode_selection_policy": "sha256(seed:task_id:episode_index) rank, prefix-N, execution sorted",
        "task_count": len(task_rows),
        "episode_count": len(episode_rows),
        "window_count": sum(int(row["window_count"]) for row in episode_rows),
        "tasks": task_rows,
    }
    args.output_root.mkdir(parents=True, exist_ok=True)
    (args.output_root / "dataset_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "suite": args.suite,
                "camera_set": args.camera_set,
                "task_count": len(task_rows),
                "episode_count": len(episode_rows),
                "episode_limit_per_task": args.episode_limit,
                "episode_selection_seed": args.episode_seed,
                "window_count": manifest["window_count"],
                "composed_output_size": manifest_composed_size,
                "vae_canvas_size": manifest_vae_canvas_size,
                "latent_shape": manifest_latent_shape,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
