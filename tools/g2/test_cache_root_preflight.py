"""G2-I19-F1 direct-writer root guard; all inputs are synthetic CPU fixtures."""

from pathlib import Path

import numpy as np
import pytest

from tools.g2.rgbd_pose import LEGACY_SCHEMA, SCHEMA, cache
from tools.g2.rgbd_pose import source as src
from tools.g2.test_rgbd_pose_export import FakeReplay, bound, write_json


def tree_fingerprint(root):
    """Include directories/mtimes, so even an empty new lock directory fails."""
    return {
        path.relative_to(root).as_posix(): (
            path.is_dir(),
            path.stat().st_mtime_ns,
            src.sha256(path) if path.is_file() else None,
        )
        for path in [root, *sorted(root.rglob("*"))]
    }


@pytest.mark.parametrize(
    "artifact",
    [
        "legacy_episode",
        "unversioned_v2_episode",
        "unknown_episode",
        "staging",
        "failed",
    ],
)
def test_direct_writer_rejects_unversioned_root_before_any_write(tmp_path, artifact):
    _, _, source = bound(tmp_path / "sources")
    root = tmp_path / "existing"
    if artifact.endswith("episode"):
        episode = root / "tasks/OldLegacy/episodes/episode_987654"
        if artifact == "unknown_episode":
            episode.mkdir(parents=True)
            (episode / "unknown.bin").write_bytes(b"retain unverified episode evidence")
        else:
            schema = LEGACY_SCHEMA if artifact == "legacy_episode" else SCHEMA
            write_json(episode / "manifest.json", {"schema": schema})
            write_json(episode / "COMPLETE.json", {"schema": schema})
            # Synthetic legacy-style arrays must remain byte-identical too.
            np.savez_compressed(
                episode / "old.npz",
                depth=np.ones((2, 2), np.uint16),
                valid=np.ones((2, 2), bool),
            )
    else:
        write_json(
            root / ("." + artifact) / "owned-evidence/progress.json", {"preserve": True}
        )
    assert not (root / "cache_manifest.json").exists()
    before = tree_fingerprint(root)
    calls = []

    def factory(bound_source):
        calls.append(bound_source)
        return FakeReplay(bound_source)

    with pytest.raises(ValueError, match="unversioned cache contents"):
        cache.export_episode(
            root,
            source,
            [0],
            storage="uint16_mm",
            chunk_frames=32,
            recipe={},
            replay_factory=factory,
        )
    assert not calls
    assert tree_fingerprint(root) == before
    assert not (root / "cache_manifest.json").exists()
    assert not (root / ".manifest.lock").exists()
    assert not (root / ".locks").exists()


@pytest.mark.parametrize("preexisting_empty", [False, True])
def test_fresh_direct_writer_versions_root_and_preserves_verified_skip(
    tmp_path, preexisting_empty
):
    _, _, source = bound(tmp_path / "sources")
    root = tmp_path / "new"
    if preexisting_empty:
        root.mkdir()
    calls = []

    def factory(bound_source):
        calls.append(bound_source)
        return FakeReplay(bound_source)

    args = dict(storage="uint16_mm", chunk_frames=32, recipe={}, replay_factory=factory)
    result = cache.export_episode(root, source, [0], **args)
    assert result["status"] == "EXPORTED"
    assert src.read_json(root / "cache_manifest.json") == {"schema": SCHEMA}
    cache.verify_episode(Path(result["directory"]))
    before = tree_fingerprint(root)
    assert (
        cache.export_episode(root, source, [0], **args)["status"] == "SKIPPED_VERIFIED"
    )
    assert len(calls) == 1
    assert tree_fingerprint(root) == before
