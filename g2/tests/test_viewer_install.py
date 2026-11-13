"""Static G2 replay UI installer and live-data contract checks."""
import json
from pathlib import Path

import pytest

from g2.viewer import install as viewer


def _info(raw):
    meta = raw / "CloseBlenderLid/20250822/lerobot/meta"
    meta.mkdir(parents=True)
    meta.joinpath("info.json").write_text(json.dumps({
        "fps": 20, "chunks_size": 1000,
        "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
    }))
    return meta


def test_catalog_preserves_local_global_indices_and_task_instruction(monkeypatch, tmp_path):
    pd = pytest.importorskip("pandas")
    _info(tmp_path / "raw")
    # A synthetic 9,126-episode mapping validates global/local identity without
    # any private RoboCasa dataset dependency.
    mapping = pd.DataFrame({
        "task_class": ["CloseBlenderLid"] * 9126,
        "local_episode_index": range(9126),
        "global_episode_index": range(9126),
        "tasks_phrasing": [["Close blender lid."]] * 9126,
        "length": [320] * 9126,
    })
    monkeypatch.setattr(pd, "read_parquet", lambda path: mapping)
    result = viewer.build_catalog(tmp_path / "fake.parquet", tmp_path / "raw")
    assert result["schema"] == "g2_replay_viewer_catalog_v1"
    assert result["total_episodes"] == 9126
    assert result["source_fps"] == 20 and result["spatial_fps"] == 2
    assert len(result["tasks"]) == 1
    task = result["tasks"][0]
    assert task["source_dir"] == "CloseBlenderLid/20250822/lerobot"
    assert task["episodes"][0] == {
        "global_id": 0, "local_id": 0, "frames": 320,
        "instruction": "Close blender lid.",
    }
    assert task["episodes"][-1]["global_id"] == 9125


def test_installer_writes_static_assets_and_links_original_video(monkeypatch, tmp_path):
    raw = tmp_path / "raw"
    _info(raw)
    mapping = tmp_path / "mapping.parquet"
    mapping.write_bytes(b"dummy")
    output = tmp_path / "compact"
    ep = output / "tasks/CloseBlenderLid/episodes/episode_000000"
    ep.mkdir(parents=True)
    marker = ep / "COMPLETE.json"
    marker.write_text('{"complete":true}')
    original = marker.read_bytes()
    monkeypatch.setattr(viewer, "build_catalog", lambda *_: {
        "schema": "g2_replay_viewer_catalog_v1", "source_fps": 20,
        "spatial_fps": 2, "total_episodes": 9126, "tasks": [],
    })
    path = viewer.install(mapping, raw, output)
    assert path == output / "view"
    assert (path / "index.html").is_file()
    assert (path / "viewer.js").is_file()
    assert (path / "viewer.css").is_file()
    assert (path / "catalog.json").is_file()
    assert (path / "source_videos").is_symlink()
    assert (path / "source_videos").resolve() == raw.resolve()
    assert marker.read_bytes() == original
    # Safe repeat installations never overwrite or delete source data.
    viewer.install(mapping, raw, output)
    assert marker.read_bytes() == original


def test_viewer_contains_required_controls_and_dynamic_complete_discovery():
    folder = Path(viewer.__file__).parent
    html = (folder / "index.html").read_text()
    js = (folder / "viewer.js").read_text()
    css = (folder / "viewer.css").read_text()
    for control in (
        'id="task-select"', 'id="episode-select"', 'id="refresh-episodes"',
        'id="instruction-text"', 'id="scrub"', 'id="prev-frame"',
        'id="next-frame"', 'id="play"', 'id="speed"', 'id="add-row"',
        'id="display-rows"',
    ):
        assert control in html
    for marker in (
        '"floor_top"', '"upper_up"', '"plus_X"', '"minus_X"',
        '"plus_Y"', '"minus_Y"', '"left"', '"right"', '"wrist"',
        "COMPLETE.json", "episode_manifest.json", "dragstart", "dragover",
        "drop", "localStorage", "spatialAt", "requestAnimationFrame",
    ):
        assert marker in js
    assert 'data-count="4"' in css and 'data-count="5"' in css
    assert "minmax(0,1fr)" in css
    assert "[hidden] { display: none !important; }" in css
