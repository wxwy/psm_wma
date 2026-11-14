"""Static G2 replay UI installer and live-data contract checks."""
import json
import shutil
import subprocess
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
    assert not (path / "directory_picker.js").exists()
    assert (path / "viewer.css").is_file()
    assert (path / "catalog.json").is_file()
    (path / "directory_picker.js").write_text("stale picker", encoding="utf-8")
    viewer.install(mapping, raw, output)
    assert not (path / "directory_picker.js").exists()
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
    # Previously the visible <img>.src was replaced before the new PNG had
    # finished downloading/decoding. That produced a visible blank flash,
    # especially for the larger 2Hz floor_top frames.
    assert 'function decodedImage(path)' in js
    assert 'image.decode()' in js
    assert 'context.drawImage(image, 0, 0)' in js
    assert 'tile.displayedPath = path' in js
    assert 'tile.generation !== generation' in js
    assert 'tile.disposed = true' in js
    assert 'preloadNext(index)' in js
    assert 'tile.img.src =' not in js
    assert 'tile.img.hidden' not in js
    assert '.tile-visual canvas' in css
    assert 'showDirectoryPicker' not in js
    assert 'scanRemoteRoot' not in js
    assert 'directory_picker.js' not in html
    assert 'local-folder-fallback' not in html
    assert 'directory-layout' not in html
    assert 'fixed-source-grid' in html
    assert 'robocasa365-target-atomic-6views' in html
    assert 'robocasa365_official/v1.0/target/atomic' in html
    assert 'font-size:18px' in css
    assert 'const entries = await listDirectory(url);' in js
    assert 'data-count="4"' in css and 'data-count="5"' in css
    assert "minmax(0,1fr)" in css
    assert "[hidden] { display: none !important; }" in css



def test_delayed_png_decode_never_blanks_visible_floor_map():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable in this Python test environment")
    script = Path(viewer.__file__).parents[1] / "tests/viewer_no_flicker_smoke.js"
    result = subprocess.run(
        [node, str(script)], check=False, capture_output=True,
        text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "VIEWER_NO_BLANK_FRAME_REGRESSION_PASS" in result.stdout


def test_island_four_directions_with_multiple_ids_and_no_island_episode():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable in this Python test environment")
    script = Path(viewer.__file__).parents[1] / "tests/viewer_island_sources_smoke.js"
    result = subprocess.run([node, str(script)], check=False,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "VIEWER_ISLAND_FOUR_VIEW_CONTRACT_PASS" in result.stdout


def test_compact_row_spacing_without_row_number_labels():
    folder = Path(viewer.__file__).parent
    js = (folder / "viewer.js").read_text()
    css = (folder / "viewer.css").read_text()
    html = (folder / "index.html").read_text()
    assert "ROW " not in js
    assert "row-identity" not in js
    assert ".display-rows { display:flex; flex-direction:column; gap:10px }" in css
    assert "margin:0 0 2.5px" in css
    assert "justify-content:flex-end" in css
    assert "actions.append(add, remove); head.append(actions);" in js
    assert "viewer.js?v=20261114-default-3rows" in html
    assert "viewer.css?v=20261113-fixed-dirs" in html


def test_fixed_directory_mode_has_no_recursive_catalog_discovery():
    folder = Path(viewer.__file__).parent
    js = (folder / "viewer.js").read_text()
    html = (folder / "index.html").read_text()
    assert "function taskDirectory()" in js
    assert 'return state.dataRoot + "tasks/"' in js
    assert 'const entries = await listDirectory(url);' in js
    assert "function scanRemoteRoot()" not in js
    assert "showDirectoryPicker" not in js
    assert "G2DirectorySource" not in js
    assert 'source_videos' in (folder / "install.py").read_text()
    assert 'source_videos' not in html


def test_published_result_task_counts_and_short_alias():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable in this Python test environment")
    script = Path(viewer.__file__).parents[1] / "tests/viewer_published_catalog_smoke.js"
    result = subprocess.run([node, str(script)], check=False,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "G2_VIEWER_PUBLISHED_TASK_COUNTS_AND_ALIASES_PASS" in result.stdout


def test_only_existing_episode_views_are_dropdown_choices():
    folder = Path(viewer.__file__).parent
    js = (folder / "viewer.js").read_text()
    html = (folder / "index.html").read_text()
    assert 'function availableSources(manifest, cameras = new Set())' in js
    assert 'function ownerState(manifest, index, relative)' in js
    assert 'function detectAvailableCameras()' in js
    assert 'method: "HEAD"' in js
    assert 'const groups = availableSources(state.manifest, state.availableCameras)' in js
    assert 'options.includes(selected) ? selected : options[0]' in js
    assert 'state.completedByTask' in js
    assert 'discoverCompletedTasks(true)' in js
    assert 'viewer.js?v=20261114-default-3rows' in html


def test_dynamic_three_row_default_layout_and_v1_layout_migration():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js unavailable in this Python test environment")
    script = Path(viewer.__file__).parents[1] / "tests/viewer_default_layout_smoke.js"
    result = subprocess.run([node, str(script)], check=False,
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "G2_DEFAULT_THREE_ROWS_DYNAMIC_ISLAND_AND_LAYOUT_MIGRATION_PASS" in result.stdout


def test_automatic_layout_is_regenerated_per_episode_but_custom_layout_persists():
    script = (Path(viewer.__file__).parent / "viewer.js").read_text()
    html = (Path(viewer.__file__).parent / "index.html").read_text()
    assert "psm-g2-viewer-layout-v2" in script
    assert "psm-g2-viewer-layout-v1" in script
    assert "state.autoLayout = false;" in script
    assert "state.autoLayout = true;" in script
    assert "if (state.autoLayout)" in script
    assert "state.rows = startingLayout(manifest, cameras);" in script
    assert 'localStorage.setItem(STORAGE, "auto")' in script
    assert "resetDefaultLayout();" in script
    assert "默认三行布局" in script
    assert "默认三行布局" in html
