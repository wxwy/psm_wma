from __future__ import annotations

import json
import sys
from pathlib import Path

from tools.g0.merge_robocasa_latent_task_manifests import main


def _manifest(task_class: str, episode_index: int) -> dict[str, object]:
    return {
        "schema_version": "exact_window_v1",
        "source_format": "lerobot_v3",
        "suite": "robocasa365_target_atomic",
        "source_dataset": "/source",
        "chunk_length": 16,
        "camera_set": "left_wrist",
        "camera_mode": "left_wrist",
        "camera_keys": ["left", "wrist"],
        "sample_stride": 1,
        "fps": 20.0,
        "latent_shape": [5, 48, 12, 20],
        "action_shape_source": [12],
        "state_shape": [16],
        "source_view_size": [256, 256],
        "composed_output_size": [256, 512],
        "vae_canvas_size": [192, 320],
        "vae_canvas_size_policy": "VideoResize resolution=None auto-tier",
        "vae_encode_contract": {
            "compute_dtype": "torch.bfloat16",
            "encode_exact_durations": [17, 61, 73],
            "encode_chunk_frames": {"256": 68, "480": 24, "720": 8, "768": 8},
        },
        "cudnn_benchmark": False,
        "episode_limit_per_task_class": None,
        "episode_selection_seed": 42,
        "episode_selection_policy": "ALL",
        "full_task_class_count": 2,
        "script_revision": "test",
        "task_class_count": 1,
        "task_shard": None,
        "num_task_shards": None,
        "episode_count": 1,
        "window_count": 3,
        "tasks": [
            {
                "task_class": task_class,
                "task_slug": task_class,
                "episodes": [
                    {
                        "episode_index": episode_index,
                        "window_count": 3,
                    }
                ],
            }
        ],
    }


def test_merge_task_manifests(tmp_path: Path, monkeypatch) -> None:
    task_dir = tmp_path / ".work_queue" / "task_manifests"
    task_dir.mkdir(parents=True)
    (task_dir / "A.json").write_text(json.dumps(_manifest("A", 0)), encoding="utf-8")
    (task_dir / "B.json").write_text(json.dumps(_manifest("B", 1)), encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["merge", "--output-root", str(tmp_path)])
    main()

    merged = json.loads((tmp_path / "dataset_manifest.json").read_text(encoding="utf-8"))
    assert merged["task_class_count"] == 2
    assert merged["episode_count"] == 2
    assert merged["window_count"] == 6
    assert [task["task_class"] for task in merged["tasks"]] == ["A", "B"]
    assert merged["parallel_build"]["mode"] == "work_queue"
