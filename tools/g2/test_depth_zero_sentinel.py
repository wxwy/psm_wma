"""Issue19 production paths with synthetic data; no server recording or GPU.

The 736/73/74 fixtures reproduce reported counts/ranges, not real CloseFridge.
Native recorded-scene acceptance remains a separate server gate.
"""

from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from tools.g2 import verify_robocasa_rgbd_pose as checker
from tools.g2.rgbd_pose import LEGACY_SCHEMA, SCHEMA
from tools.g2.rgbd_pose import cache, geometry as g, source as src
from tools.g2.test_rgbd_pose_export import (
    FakeReplay,
    bound,
    cli,
    exported,
    fixture_tree,
    reseal_frame_index,
    write_json,
)


@pytest.mark.parametrize(
    "distance,expected",
    [
        (-1.0, 0),
        (0.0, 0),
        (0.0009999, 0),
        (0.001, 1),
        (0.00149, 1),
        (65.5349, 65535),
        (65.535, 65535),
        (65.5350001, 0),
        (591.547, 0),
        (614.359, 0),
    ],
)
def test_uint16_boundary_never_wraps_or_saturates(distance, expected):
    encoded, valid, error = g.encode_depth(
        [[distance]], np.array([[True]]), "uint16_mm"
    )
    assert encoded.dtype == np.uint16 and encoded.item() == expected
    assert valid.item() == (expected > 0)
    assert error <= 0.0005001
    decoded = g.decode_depth(encoded, "uint16_mm")
    assert decoded.item() == expected / 1000
    if not expected:
        assert error == 0 and not np.any(decoded > 0)


@pytest.mark.parametrize("distance", [np.nan, np.inf, -np.inf, -100, 600])
@pytest.mark.parametrize("storage", g.DEPTH_FORMATS)
def test_renderer_invalid_is_zero_without_persisted_mask(distance, storage):
    encoded, mask, error = g.encode_depth([[distance]], np.array([[False]]), storage)
    assert encoded.item() == 0 and not mask.item() and error == 0
    stats = g.encoding_statistics([[distance]], np.array([[False]]), storage)
    assert stats["renderer_invalid"] == 1 and stats["encoded_valid"] == 0
    assert stats["below_1mm"] == stats["above_65_535m"] == 0
    g.validate_encoding_statistics(stats, encoded, storage)


@pytest.mark.parametrize("distance", [np.nan, np.inf, -np.inf])
def test_nonfinite_claimed_renderer_valid_remains_malformed_input(distance):
    with pytest.raises(ValueError, match="finite"):
        g.encode_depth([[distance]], np.array([[True]]), "uint16_mm")


def test_source_range_counts_disjoint_and_large_fraction_explicit():
    depth = np.array([[np.nan, 0, 0.0001, 65.5351, 591.547, 0.001, 65.535]])
    renderer = np.array([[False, True, True, True, True, True, True]])
    encoded, _, _ = g.encode_depth(depth, renderer, "uint16_mm")
    stats = g.encoding_statistics(depth, renderer, "uint16_mm")
    assert {k: stats[k] for k in g.ENCODING_COUNTS} == {
        "total_pixels": 7,
        "renderer_invalid": 1,
        "below_1mm": 2,
        "above_65_535m": 2,
        "encoded_valid": 2,
    }
    assert stats["warning"] == "RANGE_EXCLUSION_GT_1_PERCENT"
    assert stats["range_excluded_fraction_of_renderer_valid"] == 4 / 6
    assert stats["finite_raw_max_m"] == 591.547
    g.validate_encoding_statistics(stats, encoded, "uint16_mm")


def test_float32_retains_far_and_submillimeter_values_without_uint16_filter():
    depth = np.array([[0.00001, 614.359, 1.0]])
    renderer = np.ones(depth.shape, bool)
    encoded, mask, _ = g.encode_depth(depth, renderer, "float32_m")
    assert mask.all() and encoded.dtype == np.float32
    np.testing.assert_allclose(g.decode_depth(encoded, "float32_m"), depth, rtol=1e-7)
    stats = g.encoding_statistics(depth, renderer, "float32_m")
    assert not stats["range_filter_applied"] and stats["encoded_valid"] == 3
    assert stats["below_1mm"] == stats["above_65_535m"] == 0
    g.validate_encoding_statistics(stats, encoded, "float32_m")


@pytest.mark.parametrize("bad", ["negative", "nan", "inf", "dtype", "empty"])
def test_depth_only_decoder_rejects_malformed_payload(bad):
    value = np.array([[1.0, 0.0]], np.float32)
    if bad == "negative":
        value[0, 0] = -1
    if bad == "nan":
        value[0, 0] = np.nan
    if bad == "inf":
        value[0, 0] = np.inf
    if bad == "dtype":
        value = value.astype(np.float64)
    if bad == "empty":
        value = np.empty((0, 2), np.float32)
    with pytest.raises(ValueError):
        g.decode_depth(value, "float32_m")


@pytest.mark.parametrize(
    "bad",
    ["negative", "bool", "count", "fraction", "extra", "extrema", "missing_extrema"],
)
def test_encoding_diagnostic_corruption_rejected(bad):
    encoded = np.array([[1000, 0]], np.uint16)
    stats = g.encoding_statistics([[1.0, 600]], np.ones((1, 2), bool), "uint16_mm")
    if bad == "negative":
        stats["above_65_535m"] = -1
    if bad == "bool":
        stats["above_65_535m"] = True
    if bad == "count":
        stats["encoded_valid"] = 2
    if bad == "fraction":
        stats["range_excluded_fraction_of_renderer_valid"] = 0
    if bad == "extra":
        stats["valid"] = [[True, False]]
    if bad == "extrema":
        stats["finite_raw_max_m"] = 1.0
    if bad == "missing_extrema":
        del stats["finite_raw_min_m"]
    with pytest.raises(ValueError):
        g.validate_encoding_statistics(stats, encoded, "uint16_mm")


def long_source(tmp_path):
    raw, flat = fixture_tree(tmp_path)
    dataset = raw / "CloseFridge/recorded-date/lerobot"
    info = src.read_json(dataset / "meta/info.json")
    for feature in info["features"].values():
        feature["shape"] = [256, 256, 3]
    write_json(dataset / "meta/info.json", info)
    count = 75
    states = np.c_[
        0.5 + np.arange(count) * 0.05, np.arange(count), np.zeros((count, 2))
    ]
    np.savez_compressed(dataset / "extras/episode_000000/states.npz", states=states)
    rows = [
        {
            "index": i,
            "episode_index": 0,
            "frame_index": i,
            "timestamp": i * 0.05,
            "observation.state": [float(i), 0.0, 0.1],
        }
        for i in range(count)
    ]
    pq.write_table(
        pa.Table.from_pylist(rows), dataset / "data/chunk-000/episode_000000.parquet"
    )
    pq.write_table(
        pa.Table.from_pylist([{**r, "episode_index": 736} for r in rows]),
        flat / "data/chunk-000/file-000.parquet",
    )
    mapping = pq.read_table(flat / "flat_v3_mapping.parquet").to_pylist()
    mapping[0].update(
        global_episode_index=736, length=count, local_row_to=count, global_row_to=count
    )
    pq.write_table(pa.Table.from_pylist(mapping), flat / "flat_v3_mapping.parquet")
    source = src.load_episode(
        raw,
        flat,
        src.mapping_episodes(flat / "flat_v3_mapping.parquet")[0],
        [src.CAMERAS[0], src.CAMERAS[2]],
        state_index_policy="frame_index",
    )
    return raw, flat, source


class ReportedFarFloor(FakeReplay):
    def render(self, camera):
        value = super().render(camera)
        if camera == src.CAMERAS[2] and self.frame in (73, 74):
            count, far = (25, 591.547) if self.frame == 73 else (230, 614.359)
            value["depth_m"].ravel()[1 : count + 1] = far
        return value

    def ray_check(self, camera, sample, **kwargs):
        # Production verifier must send only representable depths to geometry.
        assert sample["depth_m"][sample["valid"]].max() <= 65.535
        assert np.all(sample["depth_m"][~sample["valid"]] == 0)
        return super().ray_check(camera, sample, **kwargs)


def test_reported_736_frames_73_74_through_export_and_spatial_verifier(tmp_path):
    raw, flat, source = long_source(tmp_path)
    result = cache.export_episode(
        tmp_path / "v2",
        source,
        [73, 74],
        storage="uint16_mm",
        chunk_frames=32,
        recipe={},
        replay_factory=ReportedFarFloor,
    )
    directory = Path(result["directory"])
    manifest, rows = cache.verify_episode(directory)
    assert manifest["schema"] == SCHEMA and [r["frame_index"] for r in rows] == [73, 74]
    wrist = src.CAMERAS[2]
    assert [r["cameras"][wrist]["encoding"]["above_65_535m"] for r in rows] == [25, 230]
    for row, count in zip(rows, (25, 230), strict=True):
        saved = cache.cached_sample(directory, manifest, row, wrist)
        assert np.count_nonzero(~saved["valid"]) == count + 1
        assert np.count_nonzero(saved["depth_m"] == 65.535) == 0
    report = checker.verify(
        directory,
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=ReportedFarFloor,
        rgb_reader=lambda ref, frame: np.full((256, 256, 3), 7 + frame, np.uint8),
    )
    assert report["status"] == "SYNTHETIC_SPATIAL_REPLAY_CHECKS_PASS"
    assert report["depth_encoding"][wrist]["above_65_535m"] == 255
    for frame in report["frames"]:
        stats = frame["cameras"][wrist]
        assert (
            stats["valid_mask_matches_replay"] and stats["encoding_counts_match_replay"]
        )
        assert stats["renderer_valid_pixels"] > stats["depth"]["valid_pixels"]
        assert stats["independent_geometry"]["status"] == "PASS"


@pytest.mark.parametrize("storage", g.DEPTH_FORMATS)
def test_chunk32_terminal_full_coverage_no_stored_mask_and_immutable_skip(
    tmp_path, storage
):
    _, _, source = long_source(tmp_path)
    root = tmp_path / "cache"
    args = dict(
        storage=storage, chunk_frames=32, recipe={}, replay_factory=ReportedFarFloor
    )
    result = cache.export_episode(root, source, range(75), **args)
    directory = Path(result["directory"])
    manifest, rows = cache.verify_episode(directory)
    assert manifest["full_episode"] and len(rows) == 75
    for camera in source.camera_shapes:
        frames = []
        for path in sorted((directory / "cameras" / camera).glob("*.npz")):
            with np.load(path, allow_pickle=False) as chunk:
                assert set(chunk.files) == {
                    "depth",
                    "K",
                    "T_world_camera_gl",
                    "T_world_camera_cv",
                    "frame_indices",
                }
                assert len(chunk["depth"]) <= 32
                frames.extend(chunk["frame_indices"].tolist())
                for i, frame in enumerate(chunk["frame_indices"]):
                    fake = ReportedFarFloor(source)
                    fake.restore(int(frame))
                    original = fake.render(camera)
                    for key in ("K", "T_world_camera_gl", "T_world_camera_cv"):
                        np.testing.assert_array_equal(
                            chunk[key][i], original[key].astype(np.float32)
                        )
        assert frames == list(range(75))
    before = {p: src.sha256(p) for p in directory.rglob("*") if p.is_file()}
    assert (
        cache.export_episode(root, source, range(75), **args)["status"]
        == "SKIPPED_VERIFIED"
    )
    assert before == {p: src.sha256(p) for p in before}


def reseal_chunk(directory, path, arrays):
    np.savez_compressed(path, **arrays)
    manifest = src.read_json(directory / "manifest.json")
    manifest["files"][path.relative_to(directory).as_posix()] = {
        "size": path.stat().st_size,
        "sha256": src.sha256(path),
    }
    write_json(directory / "manifest.json", manifest)
    marker = src.read_json(directory / "COMPLETE.json")
    marker["manifest_sha256"] = src.sha256(directory / "manifest.json")
    write_json(directory / "COMPLETE.json", marker)


@pytest.mark.parametrize(
    "bad", ["legacy_valid", "missing_K", "depth_dtype", "frame_indices", "pose_dtype"]
)
def test_v2_rejects_mixed_or_malformed_chunks_even_with_updated_hashes(tmp_path, bad):
    _, _, _, directory = exported(tmp_path)
    path = next(directory.glob("cameras/*/*.npz"))
    with np.load(path, allow_pickle=False) as chunk:
        arrays = {k: chunk[k] for k in chunk.files}
    if bad == "legacy_valid":
        arrays["valid"] = arrays["depth"] > 0
    if bad == "missing_K":
        del arrays["K"]
    if bad == "depth_dtype":
        arrays["depth"] = arrays["depth"].astype(np.int32)
    if bad == "frame_indices":
        arrays["frame_indices"][0] += 1
    if bad == "pose_dtype":
        arrays["T_world_camera_cv"] = arrays["T_world_camera_cv"].astype(np.float64)
    reseal_chunk(directory, path, arrays)
    with pytest.raises(ValueError):
        cache.verify_episode(directory)


def test_legacy_episode_schema_is_explicitly_rejected(tmp_path):
    _, _, _, directory = exported(tmp_path)
    marker = src.read_json(directory / "COMPLETE.json")
    marker["schema"] = LEGACY_SCHEMA
    write_json(directory / "COMPLETE.json", marker)
    with pytest.raises(ValueError, match="legacy v1"):
        cache.verify_episode(directory)


def test_v1_root_with_seven_old_episodes_failure_and_staging_is_never_modified(
    tmp_path,
):
    raw, flat, _ = bound(tmp_path / "sources")
    root = tmp_path / "legacy"
    write_json(root / "cache_manifest.json", {"schema": LEGACY_SCHEMA})
    for i in range(7):
        write_json(
            root / f"tasks/CloseFridge/episodes/episode_{i:06d}/manifest.json",
            {"schema": LEGACY_SCHEMA, "untouched_fixture": i},
        )
    write_json(root / ".failed/retained/failure.json", {"old": True})
    write_json(root / ".staging/retained/progress.json", {"old": True})
    before = {
        p.relative_to(root): src.sha256(p) for p in root.rglob("*") if p.is_file()
    }
    with pytest.raises(ValueError, match="legacy/unknown root"):
        cli.main(
            [
                "--raw-root",
                str(raw),
                "--flat-root",
                str(flat),
                "--output-root",
                str(root),
                "--global-episode",
                "0",
                "--state-index-policy",
                "frame_index",
            ],
            replay_factory=FakeReplay,
        )
    assert before == {
        p.relative_to(root): src.sha256(p) for p in root.rglob("*") if p.is_file()
    }
    assert not (root / ".manifest.lock").exists()


def test_missing_source_encoding_diagnostics_not_accepted(tmp_path):
    _, _, _, directory = exported(tmp_path)
    rows = cache.read_frames(directory / "frames.jsonl")
    rows[0]["cameras"][src.CAMERAS[0]]["encoding"]["encoded_valid"] = 0
    reseal_frame_index(directory, b"".join(src.canonical(r) + b"\n" for r in rows))
    with pytest.raises(ValueError, match="counts disagree"):
        cache.verify_episode(directory)


def test_v1_contract_cannot_be_requested_even_in_new_namespace(tmp_path):
    with pytest.raises(ValueError, match="must be v2"):
        cache.ensure_cache_manifest(tmp_path / "cache", {"schema": LEGACY_SCHEMA})
    assert not (tmp_path / "cache").exists()


def test_direct_episode_writer_also_rejects_legacy_root_before_writes(tmp_path):
    _, _, source = bound(tmp_path / "sources")
    root = tmp_path / "old"
    write_json(root / "cache_manifest.json", {"schema": LEGACY_SCHEMA})
    before = src.sha256(root / "cache_manifest.json")
    with pytest.raises(ValueError, match="legacy/unknown root"):
        cache.export_episode(
            root,
            source,
            [0],
            storage="uint16_mm",
            chunk_frames=32,
            recipe={},
            replay_factory=FakeReplay,
        )
    assert list(root.iterdir()) == [root / "cache_manifest.json"]
    assert src.sha256(root / "cache_manifest.json") == before


def test_missing_root_manifest_cannot_relabel_existing_cache_contents(tmp_path):
    root = tmp_path / "old"
    write_json(root / "tasks/CloseFridge/manifest.json", {"schema": LEGACY_SCHEMA})
    before = {p: src.sha256(p) for p in root.rglob("*") if p.is_file()}
    with pytest.raises(ValueError, match="unversioned cache contents"):
        cache.ensure_cache_manifest(root, {"schema": SCHEMA})
    assert {p: src.sha256(p) for p in root.rglob("*") if p.is_file()} == before


def test_replay_rejects_wrong_zero_classification_even_when_storage_mask_matches(
    tmp_path,
):
    raw, flat, source, directory = exported(tmp_path)
    rows = cache.read_frames(directory / "frames.jsonl")
    camera = src.CAMERAS[0]
    fake = FakeReplay(source)
    fake.restore(0)
    sample = fake.render(camera)
    sample["depth_m"][0, 0] = 0.0004
    sample["valid"][0, 0] = True
    rows[0]["cameras"][camera]["encoding"] = g.encoding_statistics(
        sample["depth_m"], sample["valid"], "uint16_mm"
    )
    manifest = src.read_json(directory / "manifest.json")
    totals = manifest["depth_encoding"][camera]
    totals["renderer_invalid"] -= 1
    totals["below_1mm"] += 1
    totals["warning_frames"] += 1
    write_json(directory / "manifest.json", manifest)
    reseal_frame_index(directory, b"".join(src.canonical(r) + b"\n" for r in rows))
    cache.verify_episode(
        directory
    )  # Self-consistent offline claims need source replay.
    report = checker.verify(
        directory,
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=FakeReplay,
        rgb_reader=lambda ref, frame: np.full((8, 8, 3), 7 + frame, np.uint8),
    )
    checked = report["frames"][0]["cameras"][camera]
    assert (
        checked["valid_mask_matches_replay"]
        and not checked["encoding_counts_match_replay"]
    )
    assert report["status"] == "SPATIAL_REPLAY_CHECKS_NOT_ACCEPTED"


def test_all_range_excluded_frame_cannot_claim_spatial_pass(tmp_path):
    class AllFar(FakeReplay):
        def render(self, camera):
            sample = super().render(camera)
            sample["depth_m"][:] = 600.0
            return sample

    raw, flat, source = bound(tmp_path / "source")
    result = cache.export_episode(
        tmp_path / "cache",
        source,
        [0],
        storage="uint16_mm",
        chunk_frames=32,
        recipe={},
        replay_factory=AllFar,
    )
    report = checker.verify(
        result["directory"],
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=AllFar,
        rgb_reader=lambda ref, frame: np.full((8, 8, 3), 7, np.uint8),
    )
    assert report["status"] == "SPATIAL_REPLAY_CHECKS_NOT_ACCEPTED"
    for camera in source.camera_shapes:
        checked = report["frames"][0]["cameras"][camera]
        assert checked["depth"]["valid_pixels"] == 0
        assert checked["fresh_depth_max_abs_m"] is None
