#!/usr/bin/env python3
"""Build RoboCasa365 flat LeRobot v3 exact-window Wan2.2 latent caches."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import torch

from exact_window_cache import VisionEncoderAdapter, encode_window, to_training_uint8, window_indices, write_atomic
from cosmos_framework.data.generator.action.datasets.robocasa_lerobot_dataset import (
    compose_robocasa_video,
    normalize_robocasa_camera_set,
    robocasa_camera_keys,
    robocasa_composed_size,
    robocasa_task_class_from_index,
)
from cosmos_framework.data.generator.action.utils.transforms import VideoResize
from cosmos_framework.model.generator.tokenizers.wan2pt2_vae_4x16x16 import Wan2pt2VAEInterface
from cosmos_framework.model.generator.vision_vae import (
    LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
)
from lerobot.datasets.lerobot_dataset import LeRobotDatasetMetadata
from lerobot.datasets.video_utils import decode_video_frames


_TASK_CLASS_FEATURE = "annotation.human.task_name"
_TARGET_TASK_COUNTS = {
    "robocasa365_target_atomic": 18,
    "robocasa365_target_composite_seen": 16,
    "robocasa365_target_composite_unseen": 16,
}


def _revision() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def _task_slug(task_class: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", task_class).strip("_")
    if not slug:
        raise ValueError(f"Cannot derive task slug from {task_class!r}")
    return slug


def _episode_selection_score(*, seed: int, task_class: str, episode_index: int) -> bytes:
    return hashlib.sha256(f"{seed}:{task_class}:{episode_index}".encode("utf-8")).digest()


def _select_episode_ids(
    episode_ids: list[int],
    *,
    task_class: str,
    episode_limit: int | None,
    episode_seed: int,
) -> list[int]:
    unique_ids = sorted(set(int(value) for value in episode_ids))
    if episode_limit is None:
        return unique_ids
    if episode_limit <= 0:
        raise ValueError(f"episode_limit must be positive, got {episode_limit}")
    ranked = sorted(
        unique_ids,
        key=lambda episode_index: (
            _episode_selection_score(
                seed=episode_seed,
                task_class=task_class,
                episode_index=episode_index,
            ),
            episode_index,
        ),
    )
    return sorted(ranked[:episode_limit])


def _selection_digest(episode_ids: list[int]) -> str:
    payload = ",".join(str(value) for value in episode_ids).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _metadata_column(meta: LeRobotDatasetMetadata, key: str, episode_index: int):
    if meta.episodes is None:
        raise ValueError("LeRobot v3 metadata has no episode table")
    return meta.episodes[key][episode_index]


def _verify_v3_source(meta: LeRobotDatasetMetadata, source_root: Path) -> None:
    info_path = source_root / "meta" / "info.json"
    if not info_path.is_file():
        raise FileNotFoundError(f"Missing LeRobot v3 meta/info.json: {info_path}")
    info = json.loads(info_path.read_text(encoding="utf-8"))
    version = str(info.get("codebase_version", ""))
    if not version.startswith("v3"):
        raise ValueError(f"RoboCasa cache builder is v3-only, got codebase_version={version!r}")
    required = {
        _TASK_CLASS_FEATURE,
        "observation.state",
        "action",
        "observation.images.robot0_agentview_left",
        "observation.images.robot0_agentview_right",
        "observation.images.robot0_eye_in_hand",
    }
    features = set(info.get("features", {}))
    missing = sorted(required - features)
    if missing:
        raise ValueError(f"RoboCasa365 v3 source is missing required features: {missing}")
    if meta.tasks is None:
        raise ValueError("RoboCasa365 v3 source has no meta/tasks.parquet task table")


def _build_episode_task_catalog(
    meta: LeRobotDatasetMetadata,
    source_root: Path,
) -> tuple[dict[int, str], dict[str, list[int]]]:
    """Map every episode to the underlying RoboCasa task class.

    task_index is intentionally not used: it indexes natural-language phrasing.
    The v3 mirror stores annotation.human.task_name as a global task-table index.
    """
    episodes_by_file: dict[Path, list[int]] = defaultdict(list)
    for episode_index in range(meta.total_episodes):
        episodes_by_file[source_root / meta.get_data_file_path(episode_index)].append(episode_index)

    episode_to_class: dict[int, str] = {}
    class_to_episodes: dict[str, list[int]] = defaultdict(list)

    for data_path, expected_episodes in sorted(episodes_by_file.items(), key=lambda item: str(item[0])):
        table = pq.read_table(data_path, columns=["episode_index", _TASK_CLASS_FEATURE])
        episode_col = np.asarray(table["episode_index"].to_numpy(), dtype=np.int64)
        task_col = np.asarray(table[_TASK_CLASS_FEATURE].to_numpy(), dtype=np.int64)

        for episode_index in expected_episodes:
            values = np.unique(task_col[episode_col == episode_index])
            if len(values) != 1:
                raise ValueError(
                    f"Episode {episode_index} must have exactly one {_TASK_CLASS_FEATURE}; got {values.tolist()}"
                )
            task_class = robocasa_task_class_from_index(meta.tasks, int(values[0]))
            episode_to_class[episode_index] = task_class
            class_to_episodes[task_class].append(episode_index)

    if len(episode_to_class) != meta.total_episodes:
        missing = sorted(set(range(meta.total_episodes)) - set(episode_to_class))
        raise ValueError(f"Task-class catalog misses {len(missing)} episodes; first={missing[:10]}")

    return episode_to_class, {key: sorted(value) for key, value in class_to_episodes.items()}


def _load_episode_rows(
    meta: LeRobotDatasetMetadata,
    source_root: Path,
    episode_index: int,
) -> dict[str, np.ndarray]:
    data_path = source_root / meta.get_data_file_path(episode_index)
    table = pq.read_table(
        data_path,
        columns=["index", "timestamp", "episode_index", _TASK_CLASS_FEATURE],
        filters=[("episode_index", "=", int(episode_index))],
    )
    if table.num_rows == 0:
        raise ValueError(f"No rows found for episode={episode_index} in {data_path}")
    data = {
        "index": np.asarray(table["index"].to_numpy(), dtype=np.int64),
        "timestamp": np.asarray(table["timestamp"].to_numpy(), dtype=np.float64),
        "episode_index": np.asarray(table["episode_index"].to_numpy(), dtype=np.int64),
        _TASK_CLASS_FEATURE: np.asarray(table[_TASK_CLASS_FEATURE].to_numpy(), dtype=np.int64),
    }
    order = np.argsort(data["index"], kind="stable")
    return {key: value[order] for key, value in data.items()}


def _load_episode_video(
    meta: LeRobotDatasetMetadata,
    source_root: Path,
    episode_index: int,
    timestamps: list[float],
    *,
    camera_set: str,
    image_size: int,
    tolerance_s: float,
) -> torch.Tensor:
    frames: dict[str, torch.Tensor] = {}
    for key in robocasa_camera_keys(camera_set):
        from_key = f"videos/{key}/from_timestamp"
        if meta.episodes is None or from_key not in meta.episodes.column_names:
            raise ValueError(f"LeRobot v3 episode metadata is missing {from_key!r}")
        from_ts = float(_metadata_column(meta, from_key, episode_index))
        video_path = source_root / meta.get_video_file_path(episode_index, key)
        value = decode_video_frames(
            video_path,
            [from_ts + ts for ts in timestamps],
            tolerance_s,
        )
        frames[key] = value.float()
    return compose_robocasa_video(frames, camera_set=camera_set, image_size=image_size)


def _valid_cached_row(
    output_path: Path,
    *,
    suite: str,
    task_class: str,
    episode_index: int,
    camera_set: str,
) -> dict[str, object] | None:
    if not output_path.is_file():
        return None
    try:
        cached = torch.load(output_path, map_location="cpu", weights_only=True)
    except Exception as exc:
        print(f"[resume-invalid] {output_path}: {type(exc).__name__}: {exc}", flush=True)
        return None
    if not isinstance(cached, dict):
        return None
    if cached.get("format") != "exact_window_v1":
        return None
    if cached.get("source_format") != "lerobot_v3":
        return None
    if cached.get("suite") != suite or cached.get("task_class") != task_class:
        return None
    if int(cached.get("episode_index", -1)) != int(episode_index):
        return None
    metadata = cached.get("metadata")
    windows = cached.get("windows")
    if not isinstance(metadata, dict) or not isinstance(windows, dict) or not windows:
        return None
    if metadata.get("camera_set") != camera_set:
        return None
    row = metadata.get("manifest_row")
    if not isinstance(row, dict) or int(row.get("window_count", -1)) != len(windows):
        return None
    return row


def _build_task(
    *,
    meta: LeRobotDatasetMetadata,
    source_root: Path,
    output_root: Path,
    suite: str,
    task_class: str,
    source_episode_ids: list[int],
    encoder: VisionEncoderAdapter,
    device: torch.device,
    video_resize: VideoResize,
    camera_set: str,
    image_size: int,
    episode_limit: int | None,
    episode_seed: int,
    tolerance_s: float,
    vae_path: Path,
    revision: str,
) -> dict[str, object]:
    task_slug = _task_slug(task_class)
    selected = _select_episode_ids(
        source_episode_ids,
        task_class=task_class,
        episode_limit=episode_limit,
        episode_seed=episode_seed,
    )
    episodes_dir = output_root / "tasks" / task_slug / "episodes"
    episodes_dir.mkdir(parents=True, exist_ok=True)

    cached_rows: dict[int, dict[str, object]] = {}
    for episode_index in selected:
        path = episodes_dir / f"episode_{episode_index:06d}.pt"
        row = _valid_cached_row(
            path,
            suite=suite,
            task_class=task_class,
            episode_index=episode_index,
            camera_set=camera_set,
        )
        if row is not None:
            cached_rows[episode_index] = row

    if len(cached_rows) == len(selected):
        target = "ALL" if episode_limit is None else str(episode_limit)
        print(
            f"[resume-skip-task] task={task_class} target={target} complete={len(selected)}/{len(selected)}",
            flush=True,
        )

    rows: list[dict[str, object]] = []
    for episode_index in selected:
        if episode_index in cached_rows:
            rows.append(cached_rows[episode_index])
            continue

        data = _load_episode_rows(meta, source_root, episode_index)
        task_indices = np.unique(data[_TASK_CLASS_FEATURE])
        if len(task_indices) != 1:
            raise ValueError(f"Episode {episode_index} has inconsistent task-name annotations")
        resolved = robocasa_task_class_from_index(meta.tasks, int(task_indices[0]))
        if resolved != task_class:
            raise ValueError(
                f"Episode {episode_index} task-class mismatch: catalog={task_class!r}, rows={resolved!r}"
            )

        timestamps = [float(value) for value in data["timestamp"]]
        video = _load_episode_video(
            meta,
            source_root,
            episode_index,
            timestamps,
            camera_set=camera_set,
            image_size=image_size,
            tolerance_s=tolerance_s,
        )
        if int(video.shape[0]) != len(timestamps):
            raise ValueError(
                f"RoboCasa v3 frame alignment mismatch episode={episode_index}: "
                f"rows={len(timestamps)} decoded={video.shape[0]}"
            )

        video_uint8 = video_resize({"video": to_training_uint8(video)}, resolution=None)["video"]
        if video_uint8.shape[1] < 17:
            print(f"[skip-short] episode={episode_index} frames={video_uint8.shape[1]}", flush=True)
            continue

        windows: dict[str, dict[str, object]] = {}
        latent_shape: list[int] | None = None
        for start in range(int(video_uint8.shape[1]) - 16):
            latent = encode_window(video_uint8[:, start : start + 17], encoder, device=device)
            frame_indices, anchor_indices = window_indices(start)
            latent_shape = list(latent.shape)
            windows[str(start)] = {
                "latent": latent,
                "window_frame_indices": frame_indices,
                "latent_source_frame_indices": anchor_indices,
                "global_row_indices": torch.from_numpy(data["index"][start : start + 17].copy()),
            }

        if latent_shape is None:
            raise RuntimeError(f"Episode {episode_index} produced no exact windows")

        composed_h, composed_w = robocasa_composed_size(camera_set, image_size)
        canvas = [int(video_uint8.shape[2]), int(video_uint8.shape[3])]
        output_path = episodes_dir / f"episode_{episode_index:06d}.pt"
        manifest_row = {
            "task_class": task_class,
            "task_slug": task_slug,
            "episode_index": episode_index,
            "episode_path": str(output_path),
            "window_count": len(windows),
            "source_video_frames": int(video_uint8.shape[1]),
            "camera_set": camera_set,
            "composed_output_size": [composed_h, composed_w],
            "vae_canvas_size": canvas,
            "latent_shape": latent_shape,
        }
        metadata = {
            "format": "exact_window_v1",
            "source_format": "lerobot_v3",
            "suite": suite,
            "task_class": task_class,
            "task_slug": task_slug,
            "episode_index": episode_index,
            "camera_set": camera_set,
            "camera_keys": list(robocasa_camera_keys(camera_set)),
            "source_view_size": [image_size, image_size],
            "composed_output_size": [composed_h, composed_w],
            "vae_canvas_size": canvas,
            "window_frames": 17,
            "vae_path": str(vae_path),
            "script_revision": revision,
            "manifest_row": manifest_row,
        }
        write_atomic(
            {
                "format": "exact_window_v1",
                "source_format": "lerobot_v3",
                "suite": suite,
                "task_class": task_class,
                "episode_index": episode_index,
                "windows": windows,
                "metadata": metadata,
            },
            output_path,
        )
        rows.append(manifest_row)
        print(
            f"[write] task={task_class} episode={episode_index:06d} windows={len(windows)}",
            flush=True,
        )

    return {
        "task_class": task_class,
        "task_slug": task_slug,
        "source_episode_count": len(source_episode_ids),
        "selected_episode_ids": selected,
        "selected_episode_digest": _selection_digest(selected),
        "episode_selection_seed": episode_seed,
        "episodes": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True, help="Downloaded flat RoboCasa365 LeRobot v3 repo")
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--vae-path", type=Path, required=True)
    parser.add_argument(
        "--suite",
        choices=tuple(_TARGET_TASK_COUNTS),
        required=True,
    )
    parser.add_argument(
        "--camera-set",
        choices=("left_wrist", "wrist_lr", "left_wrist_right"),
        default="left_wrist",
    )
    parser.add_argument("--image-size", type=int, default=256)
    parser.add_argument(
        "--episode-limit",
        type=int,
        default=None,
        help="Optional deterministic per-task-class cap; omit for all episodes.",
    )
    parser.add_argument("--episode-seed", type=int, default=42)
    parser.add_argument("--tolerance-s", type=float, default=1e-4)
    parser.add_argument("--device", default="cuda")
    args = parser.parse_args()

    args.camera_set = normalize_robocasa_camera_set(args.camera_set)
    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for RoboCasa latent encoding")

    meta = LeRobotDatasetMetadata(repo_id="local", root=args.source_root, revision="local")
    _verify_v3_source(meta, args.source_root)
    _, class_to_episodes = _build_episode_task_catalog(meta, args.source_root)

    expected_task_count = _TARGET_TASK_COUNTS[args.suite]
    if len(class_to_episodes) != expected_task_count:
        raise ValueError(
            f"{args.suite} expected {expected_task_count} underlying task classes, "
            f"found {len(class_to_episodes)}: {sorted(class_to_episodes)}"
        )

    existing_manifest_path = args.output_root / "dataset_manifest.json"
    if existing_manifest_path.is_file():
        existing = json.loads(existing_manifest_path.read_text(encoding="utf-8"))
        for key, value in {
            "schema_version": "exact_window_v1",
            "source_format": "lerobot_v3",
            "suite": args.suite,
            "camera_set": args.camera_set,
        }.items():
            if existing.get(key) != value:
                raise ValueError(
                    f"Output root contract mismatch for {key}: existing={existing.get(key)!r}, requested={value!r}"
                )

    device = torch.device(args.device)
    torch.backends.cudnn.benchmark = False
    tokenizer = Wan2pt2VAEInterface(
        vae_path=str(args.vae_path),
        encode_exact_durations=LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
        encode_chunk_frames=LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
    )
    tokenizer.model.model.to(device).eval()
    encoder = VisionEncoderAdapter(tokenizer, device)
    resize = VideoResize(pad_keys=["video"], keep_aspect_ratio=True)
    revision = _revision()

    task_rows = [
        _build_task(
            meta=meta,
            source_root=args.source_root,
            output_root=args.output_root,
            suite=args.suite,
            task_class=task_class,
            source_episode_ids=class_to_episodes[task_class],
            encoder=encoder,
            device=device,
            video_resize=resize,
            camera_set=args.camera_set,
            image_size=args.image_size,
            episode_limit=args.episode_limit,
            episode_seed=args.episode_seed,
            tolerance_s=args.tolerance_s,
            vae_path=args.vae_path,
            revision=revision,
        )
        for task_class in sorted(class_to_episodes)
    ]

    episode_rows = [row for task in task_rows for row in task["episodes"]]
    if not episode_rows:
        raise RuntimeError("RoboCasa v3 cache build produced zero encoded/reused episodes")

    latent_shapes = {tuple(row["latent_shape"]) for row in episode_rows}
    composed_sizes = {tuple(row["composed_output_size"]) for row in episode_rows}
    canvas_sizes = {tuple(row["vae_canvas_size"]) for row in episode_rows}
    if len(latent_shapes) != 1 or len(composed_sizes) != 1 or len(canvas_sizes) != 1:
        raise ValueError(
            f"RoboCasa v3 cache geometry drift: latent={sorted(latent_shapes)} "
            f"composed={sorted(composed_sizes)} canvas={sorted(canvas_sizes)}"
        )

    manifest = {
        "schema_version": "exact_window_v1",
        "source_format": "lerobot_v3",
        "suite": args.suite,
        "source_dataset": str(args.source_root),
        "chunk_length": 16,
        "camera_set": args.camera_set,
        "camera_mode": args.camera_set,
        "camera_keys": list(robocasa_camera_keys(args.camera_set)),
        "sample_stride": 1,
        "fps": 20.0,
        "latent_shape": list(next(iter(latent_shapes))),
        "action_shape_source": [12],
        "state_shape": [16],
        "source_view_size": [args.image_size, args.image_size],
        "composed_output_size": list(next(iter(composed_sizes))),
        "vae_canvas_size": list(next(iter(canvas_sizes))),
        "vae_canvas_size_policy": "VideoResize resolution=None auto-tier",
        "vae_encode_contract": {
            "compute_dtype": str(tokenizer.dtype),
            "encode_exact_durations": LIBERO_EXACT_WINDOW_ENCODE_EXACT_DURATIONS,
            "encode_chunk_frames": LIBERO_EXACT_WINDOW_ENCODE_CHUNK_FRAMES,
        },
        "cudnn_benchmark": False,
        "script_revision": revision,
        "episode_limit_per_task_class": args.episode_limit,
        "episode_selection_seed": args.episode_seed,
        "episode_selection_policy": (
            "ALL episodes when limit is null; otherwise "
            "sha256(seed:task_class:episode_index) rank, prefix-N"
        ),
        "task_class_count": len(task_rows),
        "episode_count": len(episode_rows),
        "window_count": sum(int(row["window_count"]) for row in episode_rows),
        "tasks": task_rows,
    }

    args.output_root.mkdir(parents=True, exist_ok=True)
    existing_manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "suite": args.suite,
                "source_format": "lerobot_v3",
                "camera_set": args.camera_set,
                "task_class_count": manifest["task_class_count"],
                "episode_count": manifest["episode_count"],
                "window_count": manifest["window_count"],
                "latent_shape": manifest["latent_shape"],
                "episode_limit_per_task_class": args.episode_limit,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
