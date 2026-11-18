"""DATA_B writer/receipt and DATA_C static-text contract, no private files."""

import json

import pytest
import torch

from g2.data import episode_state
from g2.data.episode_state import DataBError, episode_path, write_episode_state
from g2.data.joint_index import DataCError, _one_text
from g2.data.pose5 import Pose5Recipe


@pytest.fixture
def source(tmp_path):
    raw_file = tmp_path / "original.parquet"
    raw_file.write_bytes(b"immutable-source-for-test")
    return {
        "task_class": "TaskOne",
        "episode_index": 3,
        "rows": [{"observation.state": [float(i)] + [0.0] * 15} for i in range(19)],
        "instruction": "Original atomic instruction",
        "raw_source_path": str(raw_file),
        "raw_source_file_stat": {
            "size": raw_file.stat().st_size,
            "mtime_ns": raw_file.stat().st_mtime_ns,
        },
        "source_binding_digest": "1" * 64,
        "source_range": [0, 19],
        "source_frame_count": 19,
        "cache_manifest_sha256": "2" * 64,
        "exact_window_count": 3,
    }


@pytest.fixture
def fake_state(monkeypatch):
    def fake(s16, *, recipe):
        value = torch.zeros(15, dtype=torch.float32)
        value[0] = s16[0]
        value[2] = 0.7
        value[4] = 1.0
        return value

    monkeypatch.setattr(episode_state, "build_state15_from_current", fake)


def test_writer_one_episode_one_tensor_file_and_strict_resume(
    source, fake_state, tmp_path
):
    root = tmp_path / "data_b"
    recipe = Pose5Recipe()
    first = write_episode_state(root, source, recipe=recipe)
    second = write_episode_state(root, source, recipe=recipe, resume=True)
    assert first == second
    dest = episode_path(root, "TaskOne", 3)
    assert sorted(p.name for p in dest.iterdir()) == ["COMPLETE.json", "state15.pt"]
    loaded = torch.load(
        dest / "state15.pt", map_location="cpu", mmap=True, weights_only=True
    )
    assert loaded["state15"].shape == (19, 15)
    assert loaded["state15"].dtype == torch.float32
    assert loaded["state15"][:, 0].tolist() == list(range(19))
    assert loaded["metadata"]["recipe_id"] == recipe.recipe_id
    assert json.loads((dest / "COMPLETE.json").read_text())["training_ready"] is False
    with pytest.raises(FileExistsError):
        write_episode_state(root, source, recipe=recipe, resume=False)


def test_writer_bad_binding_and_corrupted_tensor_rejected(source, fake_state, tmp_path):
    root = tmp_path / "data_b"
    write_episode_state(root, source, recipe=Pose5Recipe())
    changed = dict(source, source_binding_digest="different")
    with pytest.raises(DataBError, match="source"):
        write_episode_state(root, changed, recipe=Pose5Recipe())
    target = episode_path(root, "TaskOne", 3) / "state15.pt"
    with target.open("ab") as f:
        f.write(b"corrupt")
    with pytest.raises(DataBError, match="SHA"):
        write_episode_state(root, source, recipe=Pose5Recipe())


def test_writer_refuses_partial_output(source, fake_state, tmp_path):
    root = tmp_path / "data_b"
    dest = episode_path(root, "TaskOne", 3)
    dest.mkdir(parents=True)
    (dest / "state15.pt").write_bytes(b"partial")
    with pytest.raises(DataBError, match="partial"):
        write_episode_state(root, source, recipe=Pose5Recipe())


def test_one_static_text_required_and_no_switch_in_atomic_episode():
    name = "Do task"
    text_id = "abc"
    entry = {
        "schema": "g2_episode_text_bank_v1",
        "texts": {
            text_id: {
                "original_preserved": True,
                "original_text": name,
                "enhanced_text": name + " Initial spatial context",
            }
        },
        "states": [
            {
                "text_id": text_id,
                "caption_source": {"original_text": name, "episode_index": 3},
            },
            {
                "text_id": text_id,
                "caption_source": {"original_text": name, "episode_index": 3},
            },
        ],
    }
    assert _one_text(entry, expected_text=name, ep=3)[0] == text_id
    entry["states"][1]["text_id"] = "future-new-text"
    with pytest.raises(DataCError, match="language text changed"):
        _one_text(entry, expected_text=name, ep=3)
