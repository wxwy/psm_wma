#!/usr/bin/env python3
"""Merge per-GPU RoboCasa365 latent-cache shard manifests after a parallel build."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


_COMMON_KEYS = (
    "schema_version",
    "source_format",
    "suite",
    "source_dataset",
    "chunk_length",
    "camera_set",
    "camera_mode",
    "camera_keys",
    "sample_stride",
    "fps",
    "latent_shape",
    "action_shape_source",
    "state_shape",
    "source_view_size",
    "composed_output_size",
    "vae_canvas_size",
    "vae_canvas_size_policy",
    "vae_encode_contract",
    "cudnn_benchmark",
    "episode_limit_per_task_class",
    "episode_selection_seed",
    "episode_selection_policy",
    "full_task_class_count",
)


def _load(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(f"Missing shard manifest: {path}")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Shard manifest must be an object: {path}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--num-task-shards", type=int, required=True)
    args = parser.parse_args()

    if args.num_task_shards <= 0:
        raise ValueError("--num-task-shards must be positive")

    paths = [
        args.output_root / f"dataset_manifest_shard_{index:04d}_of_{args.num_task_shards:04d}.json"
        for index in range(args.num_task_shards)
    ]
    shards = [_load(path) for path in paths]
    base = shards[0]

    for index, shard in enumerate(shards):
        if shard.get("task_shard") != index:
            raise ValueError(
                f"Shard identity mismatch for {paths[index]}: "
                f"task_shard={shard.get('task_shard')!r}, expected={index}"
            )
        if shard.get("num_task_shards") != args.num_task_shards:
            raise ValueError(
                f"Shard-count mismatch for {paths[index]}: "
                f"num_task_shards={shard.get('num_task_shards')!r}, "
                f"expected={args.num_task_shards}"
            )
        for key in _COMMON_KEYS:
            if shard.get(key) != base.get(key):
                raise ValueError(
                    f"Shard contract mismatch for {key}: "
                    f"shard0={base.get(key)!r}, shard{index}={shard.get(key)!r}"
                )

    tasks: list[dict[str, object]] = []
    seen_task_classes: set[str] = set()
    for index, shard in enumerate(shards):
        shard_tasks = shard.get("tasks")
        if not isinstance(shard_tasks, list):
            raise ValueError(f"Shard {index} has invalid tasks payload")
        for task in shard_tasks:
            if not isinstance(task, dict):
                raise ValueError(f"Shard {index} contains non-object task entry")
            task_class = str(task.get("task_class", ""))
            if not task_class:
                raise ValueError(f"Shard {index} contains task without task_class")
            if task_class in seen_task_classes:
                raise ValueError(f"Duplicate task_class across shards: {task_class}")
            seen_task_classes.add(task_class)
            tasks.append(task)

    expected_task_count = int(base["full_task_class_count"])
    if len(tasks) != expected_task_count:
        raise ValueError(
            f"Merged task-class count mismatch: got {len(tasks)}, expected {expected_task_count}"
        )

    tasks.sort(key=lambda item: str(item["task_class"]))
    episode_count = sum(len(task.get("episodes", [])) for task in tasks)
    window_count = sum(
        int(row["window_count"])
        for task in tasks
        for row in task.get("episodes", [])
    )

    merged = dict(base)
    merged["task_class_count"] = expected_task_count
    merged["full_task_class_count"] = expected_task_count
    merged["task_shard"] = None
    merged["num_task_shards"] = None
    merged["episode_count"] = episode_count
    merged["window_count"] = window_count
    merged["tasks"] = tasks
    merged["parallel_build"] = {
        "num_processes": args.num_task_shards,
        "shard_manifests": [path.name for path in paths],
    }

    output_path = args.output_root / "dataset_manifest.json"
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(output_path)

    print(
        json.dumps(
            {
                "output_root": str(args.output_root),
                "manifest": str(output_path),
                "num_processes": args.num_task_shards,
                "task_class_count": expected_task_count,
                "episode_count": episode_count,
                "window_count": window_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
