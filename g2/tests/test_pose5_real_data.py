"""Optional real RoboCasa gate. Skips when private assets are not mounted."""

import json
import math
import os
from pathlib import Path

import pytest
import torch

from g2.data.pose5 import (
    Pose5Recipe,
    build_pose5,
    build_state15_from_current,
    build_state15_from_window,
    source_base_rotation,
)

EPISODES = (9, 75, 104)
DECISION_FRAMES = (16, 32, 48)


def test_three_real_episodes_all_source_frames_and_nine_windows():
    root = os.environ.get("PSM_G2_POSE5_REAL_DATA_ROOT")
    view_root = os.environ.get("PSM_G2_POSE5_REAL_VIEW_ROOT")
    if not root or not view_root:
        pytest.skip(
            "set PSM_G2_POSE5_REAL_DATA_ROOT and _VIEW_ROOT to enable real gate"
        )
    pa = pytest.importorskip("pyarrow.parquet")
    torch.set_num_threads(2)
    source = Path(root)
    views = Path(view_root)
    meta = pa.read_table(
        source / "meta/episodes/chunk-000/file-000.parquet",
        columns=[
            "episode_index",
            "data/chunk_index",
            "data/file_index",
            "dataset_from_index",
            "dataset_to_index",
            "length",
        ],
    )
    target = {
        row["episode_index"]: row
        for row in meta.to_pylist()
        if row["episode_index"] in EPISODES
    }
    assert set(target) == set(EPISODES)
    data_path = source / "data/chunk-000/file-000.parquet"
    parquet = pa.read_table(
        data_path,
        columns=["observation.state", "frame_index", "episode_index", "timestamp"],
    )
    recipe = Pose5Recipe()
    summary = []
    all_frame_count = 0
    total_spatial_states = 0
    for episode in EPISODES:
        m = target[episode]
        assert m["data/chunk_index"] == 0 and m["data/file_index"] == 0
        rows = parquet.slice(m["dataset_from_index"], m["length"]).to_pylist()
        assert (
            len(rows) == m["length"] == m["dataset_to_index"] - m["dataset_from_index"]
        )
        episode_root = (
            views / "tasks/CloseBlenderLid/episodes" / f"episode_{episode:06d}"
        )
        manifest = json.loads((episode_root / "episode_manifest.json").read_text())
        assert manifest["episode_id"] == episode
        raw = []
        for i, row in enumerate(rows):
            assert row["episode_index"] == episode and row["frame_index"] == i
            assert math.isclose(row["timestamp"], i / 20, abs_tol=5e-5)
            s = row["observation.state"]
            assert len(s) == 16
            raw.append(s)
            pose = build_pose5(s, recipe=recipe)
            torch.testing.assert_close(
                pose[:3], torch.tensor(s[:3], dtype=torch.float32), atol=0, rtol=0
            )
            assert torch.isfinite(pose).all()
            assert abs(float(pose[3] ** 2 + pose[4] ** 2) - 1) < 2e-6
            entire = build_state15_from_current(s, recipe=recipe)
            assert entire.shape == (15,) and entire.dtype == torch.float32
            assert torch.equal(entire[:5], pose)
            assert torch.isfinite(entire).all()
        all_frame_count += len(raw)
        offsets = []
        forward_errors = []
        for state in manifest["states"]:
            frame = state["frame"]
            r = source_base_rotation(raw[frame], recipe=recipe)
            body = state["raw_robot_pose"]
            assert body["coordinate_frame"] == "world"
            source_pos = torch.tensor(raw[frame][:3], dtype=torch.float64)
            wheel_pos = torch.tensor(body["position_world"], dtype=torch.float64)
            delta_local = r.T @ (source_pos - wheel_pos)
            offsets.append(delta_local)
            actual_forward = r[:, 0]
            marker_forward = torch.tensor(body["forward_world"], dtype=torch.float64)
            forward_errors.append(
                float(torch.linalg.vector_norm(actual_forward - marker_forward))
            )
        offset = torch.stack(offsets)
        assert torch.max(torch.abs(offset[:, 0] - 0.2)) < 1e-4
        assert torch.max(torch.abs(offset[:, 1])) < 1e-4
        assert max(forward_errors) < 1e-4
        total_spatial_states += len(offsets)
        for t in DECISION_FRAMES:
            window = torch.tensor(raw[t : t + 17], dtype=torch.float32)
            assert tuple(window.shape) == (17, 16)
            train_state = build_state15_from_window(window, recipe=recipe)
            serve_state = build_state15_from_current(window[0], recipe=recipe)
            torch.testing.assert_close(train_state, serve_state, atol=0, rtol=0)
        summary.append(
            (
                episode,
                len(raw),
                len(offsets),
                float(offset[:, 2].min()),
                float(offset[:, 2].max()),
                max(forward_errors),
            )
        )
    assert all_frame_count == 1272
    assert total_spatial_states == 132
    # Source anchor and wheeled body are NOT interchangeable across real motion.
    ranges = [hi - lo for _, _, _, lo, hi, _ in summary]
    assert max(ranges) > 1e-3
    print(
        "REAL_POSE5_ALL_SOURCE_FRAMES",
        all_frame_count,
        "SPATIAL_STATES",
        total_spatial_states,
        "SOURCE_ANCHOR_WHEEL_Z_RANGE",
        ranges,
        "RECIPE",
        recipe.recipe_id,
    )
