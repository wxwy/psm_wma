#!/usr/bin/env python3
"""Merge per-task RoboCasa365 latent-cache manifests from dynamic work-queue builds."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from merge_robocasa_latent_shards import _COMMON_KEYS, _load
from robocasa_work_queue import atomic_write_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    manifest_dir = args.output_root / ".work_queue" / "task_manifests"
    paths = sorted(manifest_dir.glob("*.json"))
    if not paths:
        raise FileNotFoundError(f"No task manifests found under {manifest_dir}")

    manifests = [_load(path) for path in paths]
    base = manifests[0]

    tasks: list[dict[str, object]] = []
    seen_task_classes: set[str] = set()
    for path, manifest in zip(paths, manifests, strict=True):
        for key in _COMMON_KEYS:
            if manifest.get(key) != base.get(key):
                raise ValueError(
                    f"Task-manifest contract mismatch for {key}: "
                    f"base={base.get(key)!r}, {path.name}={manifest.get(key)!r}"
                )

        task_rows = manifest.get("tasks")
        if not isinstance(task_rows, list) or len(task_rows) != 1:
            raise ValueError(f"{path} must contain exactly one task entry")
        task = task_rows[0]
        if not isinstance(task, dict):
            raise ValueError(f"{path} task entry must be an object")
        task_class = str(task.get("task_class", ""))
        if not task_class:
            raise ValueError(f"{path} task entry is missing task_class")
        if task_class in seen_task_classes:
            raise ValueError(f"Duplicate task_class across task manifests: {task_class}")
        seen_task_classes.add(task_class)
        tasks.append(task)

    expected_task_count = int(base["full_task_class_count"])
    if len(tasks) != expected_task_count:
        raise ValueError(
            f"Work-queue task-class count mismatch: got {len(tasks)}, "
            f"expected {expected_task_count}"
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
        "mode": "work_queue",
        "task_manifests": [str(path.relative_to(args.output_root)) for path in paths],
    }

    output_path = args.output_root / "dataset_manifest.json"
    atomic_write_json(output_path, merged)

    print(
        json.dumps(
            {
                "output_root": str(args.output_root),
                "manifest": str(output_path),
                "mode": "work_queue",
                "task_class_count": expected_task_count,
                "episode_count": episode_count,
                "window_count": window_count,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
