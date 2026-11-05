"""Gate A: synthetic inputs only, plus native CPU mj_ray on a tiny analytic scene.

No real RoboCasa, GL context, source recording, CUDA driver or GPU is loaded.
"""

import gzip
import hashlib
import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from scipy.spatial.transform import Rotation

from tools.g2 import export_robocasa_rgbd_pose as cli
from tools.g2 import verify_robocasa_rgbd_pose as checker
from tools.g2.rgbd_pose import cache
from tools.g2.rgbd_pose import geometry as g
from tools.g2.rgbd_pose import source as src
from tools.g2.rgbd_pose.replay import Replay


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def fixture_tree(tmp_path, count=1):
    raw, flat = tmp_path / "raw", tmp_path / "flat"
    mapping, flattened = [], []
    for n in range(count):
        task = ["CloseFridge", "OpenCabinet", "CloseBlenderLid"][n]
        dataset = raw / task / "recorded-date/lerobot"
        extra = dataset / "extras/episode_000000"
        extra.mkdir(parents=True)
        states = np.c_[0.5 + np.arange(4) * 0.05, np.arange(4), np.zeros((4, 2))]
        np.savez_compressed(extra / "states.npz", states=states)
        with gzip.open(extra / "model.xml.gz", "wt") as stream:
            stream.write('<mujoco model="synthetic_not_recorded"/>')
        write_json(extra / "ep_meta.json", {"lang": "synthetic instruction"})
        write_json(
            dataset / "extras/dataset_meta.json",
            {"env_args": {"env_name": task, "env_kwargs": {"robots": "synthetic"}}},
        )
        features = {
            "observation.images." + c: {"shape": [8, 8, 3]} for c in src.CAMERAS
        }
        write_json(
            dataset / "meta/info.json",
            {
                "features": features,
                "chunks_size": 1000,
                "video_path": "videos/chunk-{episode_chunk:03d}/{video_key}/episode_{episode_index:06d}.mp4",
            },
        )
        for camera in src.CAMERAS:
            path = (
                dataset
                / f"videos/chunk-000/observation.images.{camera}/episode_000000.mp4"
            )
            path.parent.mkdir(parents=True)
            path.write_bytes(b"synthetic-reference-only-not-an-actual-video")
        rows = [
            {
                "index": i,
                "episode_index": 0,
                "frame_index": i,
                "timestamp": i * 0.05,
                "observation.state": [float(i), float(n), 0.1],
            }
            for i in range(4)
        ]
        data = dataset / "data/chunk-000"
        data.mkdir(parents=True)
        pq.write_table(pa.Table.from_pylist(rows), data / "episode_000000.parquet")
        flattened.extend(
            {**r, "episode_index": n, "index": n * 4 + r["index"]} for r in rows
        )
        mapping.append(
            {
                "task_class": task,
                "task_slot": n,
                "local_episode_index": 0,
                "global_episode_index": n,
                "local_row_from": 0,
                "local_row_to": 4,
                "global_row_from": n * 4,
                "global_row_to": (n + 1) * 4,
                "length": 4,
                "resolved_task_class": task,
                "local_annotation": 0,
                "global_annotation": n,
                "tasks_phrasing": ["synthetic"],
            }
        )
    (flat / "data/chunk-000").mkdir(parents=True)
    write_json(flat / "meta/info.json", {"codebase_version": "v3.0", "fps": 20})
    pq.write_table(
        pa.Table.from_pylist(flattened), flat / "data/chunk-000/file-000.parquet"
    )
    pq.write_table(pa.Table.from_pylist(mapping), flat / "flat_v3_mapping.parquet")
    return raw, flat


def bound(tmp_path, *, count=1):
    raw, flat = fixture_tree(tmp_path, count=count)
    episodes = src.mapping_episodes(flat / "flat_v3_mapping.parquet")
    result = src.load_episode(
        raw,
        flat,
        episodes[0],
        src.CAMERAS[:1] + src.CAMERAS[2:],
        state_index_policy="frame_index",
    )
    return raw, flat, result


class FakeReplay:
    identity = {
        "kind": "explicit_cpu_test_double",
        "name": "deterministic_calibration_fixture",
    }
    created, closed = [], []

    def __init__(self, source):
        self.source, self.frame = source, None
        self.created.append(source.episode.global_episode_index)

    def restore(self, frame):
        self.frame = frame
        return {
            "state_max_abs_error": 0.0,
            "sim_time": float(self.source.states[frame, 0]),
        }

    def render(self, camera):
        height, width = self.source.camera_shapes[camera]
        T = np.eye(4)
        T[:3, 3] = [self.frame * 0.1 if camera == src.CAMERAS[2] else 0, 0, 1]
        valid = np.ones((height, width), dtype=bool)
        valid[0, 0] = False
        return {
            "K": np.array([[4, 0, width / 2], [0, 4, height / 2], [0, 0, 1.0]]),
            "T_world_camera_gl": T,
            "T_world_camera_cv": T @ g.GL_FROM_CV,
            "depth_m": np.full((height, width), 1.2347 + self.frame * 0.01),
            "valid": valid,
            "rgb": np.full((height, width, 3), 7 + self.frame, dtype=np.uint8),
        }

    def ray_check(self, camera, sample, **kwargs):
        return {"status": "PASS", "matching_geom_samples": 32, "test_double": True}

    def close(self):
        self.closed.append(self.source.episode.global_episode_index)


@pytest.fixture(autouse=True)
def reset_fake():
    FakeReplay.created, FakeReplay.closed = [], []


def exported(tmp_path, *, frames=(0, 1, 3), storage="uint16_mm"):
    raw, flat, source = bound(tmp_path)
    result = cache.export_episode(
        tmp_path / "cache",
        source,
        frames,
        storage=storage,
        chunk_frames=2,
        recipe={"synthetic": True},
        replay_factory=FakeReplay,
    )
    return raw, flat, source, Path(result["directory"])


def test_pixel_center_y_sign_and_camera_to_world_direction():
    K = np.array([[2, 0, 2], [0, 2, 2], [0, 0, 1.0]])
    T_gl = np.eye(4)
    T_gl[:3, 3] = [10, 20, 30]
    points = g.backproject_world(K, T_gl @ g.GL_FROM_CV, [[2.5, 3.5]], [4.0])
    np.testing.assert_allclose(
        points, [[11, 17, 26]]
    )  # Downward image y is negative GL y.
    np.testing.assert_allclose(
        g.project_world(K, T_gl @ g.GL_FROM_CV, points), [[2.5, 3.5]]
    )


def test_float32_rotated_pose_roundtrip_uses_stored_matrix_inverse():
    from scipy.spatial.transform import Rotation

    T = np.eye(4)
    T[:3, :3] = Rotation.from_euler("xyz", [0.3, 0.7, -0.8]).as_matrix()
    T[:3, 3] = [1.4, -2.7, 0.9]
    T = T.astype(np.float32)
    K = np.array([[132, 0, 128], [0, 132, 128], [0, 0, 1]], dtype=np.float32)
    pixels = np.array([[0.5, 0.5], [255.5, 255.5], [128.5, 90.5]])
    world = g.backproject_world(K, T, pixels, [1.3, 2.7, 0.3])
    np.testing.assert_allclose(g.project_world(K, T, world), pixels, atol=1e-10, rtol=0)


@pytest.mark.parametrize("violation", ["double_flip", "inverse", "reflection", "bad_K"])
def test_calibration_rejects_wrong_conventions(violation):
    K, T_gl = np.eye(3), np.eye(4)
    T_gl[0, 3] = 2
    T_cv = T_gl @ g.GL_FROM_CV
    if violation == "double_flip":
        T_cv = T_gl.copy()
    if violation == "inverse":
        T_cv = np.linalg.inv(T_cv)
    if violation == "reflection":
        T_gl[0, 0] = -1
    if violation == "bad_K":
        K[0, 0] = -1
    with pytest.raises(ValueError):
        g.check_calibration(K, T_gl, T_cv)


def test_optical_buffer_background_and_known_clip_distances():
    depth, valid = g.depth_buffer_to_z([[0, 0.5, 1, np.nan]], 0.1, 10)
    np.testing.assert_allclose(depth, [[0.1, 0.1 / 0.505, 0, 0]])
    np.testing.assert_array_equal(valid, [[True, True, False, False]])


@pytest.mark.parametrize(
    "near,far,buffer",
    [(0, 10, [[0]]), (1, 1, [[0]]), (0.1, 10, [[1.1]]), (0.1, 10, [[-0.01]])],
)
def test_invalid_depth_buffer_or_planes_rejected(near, far, buffer):
    with pytest.raises(ValueError):
        g.depth_buffer_to_z(buffer, near, far)


@pytest.mark.parametrize("storage", g.DEPTH_FORMATS)
def test_depth_codec_round_trip_mask_and_quantization(storage):
    random = np.random.default_rng(23)
    depth = random.uniform(0.001, 65.535, (13, 17))
    valid = random.random(depth.shape) > 0.2
    depth[~valid] = np.nan
    encoded, mask, error = g.encode_depth(depth, valid, storage)
    decoded = g.decode_depth(encoded, mask, storage)
    assert np.all(encoded[~valid] == 0) and np.array_equal(mask, valid)
    assert error <= (0.0005001 if storage == "uint16_mm" else 4e-6)
    np.testing.assert_allclose(decoded[valid], depth[valid], atol=0.0005001, rtol=0)


@pytest.mark.parametrize("distance", [0.0004, 0.00099, 65.5351, 100.0])
def test_uint16_overflow_never_saturates(distance):
    encoded, valid, error = g.encode_depth(
        [[distance]], np.array([[True]]), "uint16_mm"
    )
    assert encoded.tolist() == [[0]] and valid.tolist() == [[False]] and error == 0


def test_float_storage_is_explicit_fallback_and_invalid_not_a_valid_range():
    encoded, valid, error = g.encode_depth(
        [[100.0, np.inf]], np.array([[True, False]]), "float32_m"
    )
    assert encoded.tolist() == [[100.0, 0.0]] and error == 0
    assert g.decode_depth(encoded, valid, "float32_m").tolist() == [[100.0, 0.0]]


@pytest.mark.parametrize(
    "bad", ["invalid_nonzero", "zero_valid", "wrong_dtype", "mask_not_bool"]
)
def test_corrupt_depth_payload_rejected(bad):
    value, mask = np.array([[1000, 0]], dtype=np.uint16), np.array([[True, False]])
    if bad == "invalid_nonzero":
        value[0, 1] = 1
    if bad == "zero_valid":
        value[0, 0] = 0
    if bad == "wrong_dtype":
        value = value.astype(np.int32)
    if bad == "mask_not_bool":
        mask = mask.astype(np.uint8)
    with pytest.raises(ValueError):
        g.decode_depth(value, mask, "uint16_mm")


def test_existing_g0_accepted_membership_no_new_sampling(tmp_path):
    path = tmp_path / "training_manifest.json"
    selected = [0, 1]
    value = {
        "schema_version": "exact_window_v1",
        "source_format": "lerobot_v3",
        "episode_count": 1,
        "tasks": [
            {
                "task_class": "CloseFridge",
                "selected_episode_ids": selected,
                "selected_episode_digest": hashlib.sha256(b"0,1").hexdigest(),
                "episodes": [{"episode_index": 1, "task_class": "CloseFridge"}],
            }
        ],
    }
    write_json(path, value)
    assert src.selected_episodes(path)[0] == {("CloseFridge", 1)}
    value["tasks"][0]["selected_episode_digest"] = "0" * 64
    write_json(path, value)
    with pytest.raises(ValueError, match="digest"):
        src.selected_episodes(path)


@pytest.mark.parametrize(
    "bad", ["duplicate", "local_namespace", "implicit_seed", "cross_task_global"]
)
def test_selection_refuses_ambiguous_or_unproven_membership(tmp_path, bad):
    path = tmp_path / "select.json"
    value = {
        "schema": "psm_wma_rgbd_episode_selection_v1",
        "episode_namespace": "global_episode_index",
        "episodes": [{"task_class": "CloseFridge", "global_episode_index": 0}],
    }
    if bad == "duplicate":
        value["episodes"] *= 2
    if bad == "local_namespace":
        value["episode_namespace"] = "local_episode_index"
    if bad == "implicit_seed":
        value = {"episode_limit": 100, "episode_seed": 42}
    if bad == "cross_task_global":
        value["episodes"].append(
            {"task_class": "OpenCabinet", "global_episode_index": 0}
        )
    write_json(path, value)
    with pytest.raises(ValueError):
        src.selected_episodes(path)


@pytest.mark.parametrize(
    "bad", ["length", "duplicate", "overlap", "resolved", "missing", "negative"]
)
def test_mapping_intervals_identity_and_schema_fail_closed(tmp_path, bad):
    _, flat = fixture_tree(tmp_path, count=2)
    path = flat / "flat_v3_mapping.parquet"
    rows = pq.read_table(path).to_pylist()
    if bad == "length":
        rows[0]["local_row_to"] -= 1
    if bad == "duplicate":
        rows.append(rows[0])
    if bad == "overlap":
        rows[1].update(global_row_from=3, global_row_to=7)
    if bad == "resolved":
        rows[0]["resolved_task_class"] = "WrongTask"
    if bad == "missing":
        [r.pop("length") for r in rows]
    if bad == "negative":
        rows[0]["local_episode_index"] = -1
    pq.write_table(pa.Table.from_pylist(rows), path)
    with pytest.raises(ValueError):
        src.mapping_episodes(path)


def test_mapping_expands_exact_rows_and_shards_without_sampling(tmp_path):
    _, flat = fixture_tree(tmp_path, count=3)
    episodes = src.mapping_episodes(flat / "flat_v3_mapping.parquet")
    selection = tmp_path / "selection.json"
    write_json(
        selection,
        {
            "schema": "psm_wma_rgbd_episode_selection_v1",
            "episode_namespace": "global_episode_index",
            "episodes": [
                {
                    "task_class": e.task_class,
                    "global_episode_index": e.global_episode_index,
                }
                for e in episodes
            ],
        },
    )
    left = src.select(episodes, manifest=selection, task_shard=0, num_task_shards=2)[0]
    right = src.select(episodes, manifest=selection, task_shard=1, num_task_shards=2)[0]
    assert set(left).isdisjoint(right) and set(left + right) == set(episodes)
    row = next(e for e in episodes if e.global_episode_index == 2).frame(3)
    assert (
        row["global_row_index"] == 11
        and row["local_row_index"] == row["source_state_index"] == 3
    )
    with pytest.raises(ValueError):
        src.select(episodes, local_episode=0)
    with pytest.raises(ValueError):
        src.select(episodes)
    with pytest.raises(ValueError):
        src.select(episodes, global_episode=0, task_shard=0)


def test_source_checks_all_nonvisual_rows_and_never_corrects_half_second_offset(
    tmp_path,
):
    raw, flat, source = bound(tmp_path)
    assert source.states[0, 0] == 0.5 and source.flat_timestamps[0] == 0
    assert source.alignment["timestamp_shift_applied"] is False
    assert source.episode.frame(0)["source_state_index"] == 0
    with pytest.raises(ValueError, match="explicitly"):
        src.load_episode(raw, flat, source.episode, [src.CAMERAS[0]])


@pytest.mark.parametrize(
    "bad",
    [
        "flat_state",
        "flat_index",
        "flat_version",
        "states_length",
        "source_ambiguous",
        "wrong_task",
        "rgb_missing",
        "resize",
    ],
)
def test_source_inconsistency_is_not_hidden_by_replay(tmp_path, bad):
    raw, flat, source = bound(tmp_path)
    if bad in {"flat_state", "flat_index"}:
        path = flat / "data/chunk-000/file-000.parquet"
        rows = pq.read_table(path).to_pylist()
        if bad == "flat_state":
            rows[2]["observation.state"][0] += 0.1
        else:
            rows[2]["index"] += 1
        pq.write_table(pa.Table.from_pylist(rows), path)
    if bad == "flat_version":
        write_json(flat / "meta/info.json", {"codebase_version": "v2.1"})
    if bad == "states_length":
        np.savez_compressed(
            source.dataset_dir / "extras/episode_000000/states.npz",
            states=source.states[:-1],
        )
    if bad == "source_ambiguous":
        shutil.copytree(
            source.dataset_dir, source.dataset_dir.parent.parent / "second/lerobot"
        )
    if bad == "wrong_task":
        write_json(
            source.dataset_dir / "extras/dataset_meta.json",
            {"env_args": {"env_name": "Wrong", "env_kwargs": {}}},
        )
    if bad == "rgb_missing":
        Path(source.rgb[src.CAMERAS[0]]["video"]).unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        src.load_episode(
            raw,
            flat,
            source.episode,
            list(source.rgb),
            state_index_policy="frame_index",
            image_size=16 if bad == "resize" else None,
        )


@pytest.mark.parametrize("storage", g.DEPTH_FORMATS)
def test_chunk_roundtrip_partial_terminal_frame_camera_pose_and_actual_capacity(
    tmp_path, storage
):
    _, _, source, directory = exported(tmp_path, storage=storage)
    manifest, rows = cache.verify_episode(directory)
    assert [r["frame_index"] for r in rows] == [0, 1, 3]
    assert not manifest["full_episode"] and manifest["frame_count"] == 3
    assert len(list(directory.glob("cameras/*/*.npz"))) == 4
    assert FakeReplay.created == FakeReplay.closed == [0]
    left = cache.cached_sample(directory, manifest, rows[-1], src.CAMERAS[0])
    wrist = cache.cached_sample(directory, manifest, rows[-1], src.CAMERAS[2])
    assert left["T_world_camera_cv"][0, 3] == 0
    assert wrist["T_world_camera_cv"][0, 3] == pytest.approx(0.3)
    expected = 3 * 2 * (8 * 8 * (2 if storage == "uint16_mm" else 4) + 41 * 4 + 8)
    assert manifest["raw_array_bytes"] == expected
    assert manifest["compression_ratio_raw_over_stored"] == pytest.approx(
        expected / manifest["compressed_payload_bytes"]
    )
    assert rows[-1]["cameras"][src.CAMERAS[0]]["rgb"]["frame_index"] == 3


def test_resume_verifies_before_skip_and_never_opens_another_environment(tmp_path):
    _, _, source, directory = exported(tmp_path)
    before = {
        p.relative_to(directory): src.sha256(p)
        for p in directory.rglob("*")
        if p.is_file()
    }
    result = cache.export_episode(
        tmp_path / "cache",
        source,
        [0, 1, 3],
        storage="uint16_mm",
        chunk_frames=2,
        recipe={"synthetic": True},
        replay_factory=FakeReplay,
    )
    assert result["status"] == "SKIPPED_VERIFIED" and FakeReplay.created == [0]
    assert before == {
        p.relative_to(directory): src.sha256(p)
        for p in directory.rglob("*")
        if p.is_file()
    }
    with pytest.raises(ValueError, match="identity"):
        cache.export_episode(
            tmp_path / "cache",
            source,
            [0, 1, 3],
            storage="float32_m",
            chunk_frames=2,
            recipe={"synthetic": True},
            replay_factory=FakeReplay,
        )


@pytest.mark.parametrize("bad", ["marker", "chunk", "checksum", "extra"])
def test_missing_corrupt_and_extra_committed_files_are_not_reused(tmp_path, bad):
    _, _, _, directory = exported(tmp_path)
    if bad == "marker":
        (directory / "COMPLETE.json").unlink()
    if bad == "chunk":
        next(directory.glob("cameras/*/*.npz")).unlink()
    if bad == "checksum":
        next(directory.glob("cameras/*/*.npz")).write_bytes(b"corrupt")
    if bad == "extra":
        (directory / "uncommitted.tmp").write_text("unexpected")
    with pytest.raises((ValueError, FileNotFoundError)):
        cache.verify_episode(directory)


def reseal_frame_index(directory, payload):
    path = directory / "frames.jsonl"
    path.write_bytes(payload)
    manifest = src.read_json(directory / "manifest.json")
    manifest["files"]["frames.jsonl"] = {
        "sha256": src.sha256(path),
        "size": path.stat().st_size,
    }
    write_json(directory / "manifest.json", manifest)
    marker = src.read_json(directory / "COMPLETE.json")
    marker["manifest_sha256"] = src.sha256(directory / "manifest.json")
    write_json(directory / "COMPLETE.json", marker)


@pytest.mark.parametrize(
    "bad", ["utf8", "truncated", "duplicate", "state_index", "rgb_index", "offset"]
)
def test_semantic_frame_corruption_even_with_updated_file_checksums(tmp_path, bad):
    _, _, _, directory = exported(tmp_path)
    rows = cache.read_frames(directory / "frames.jsonl")
    if bad == "utf8":
        payload = b"\xff\n"
    elif bad == "truncated":
        payload = src.canonical(rows[0])
    else:
        if bad == "duplicate":
            rows[1] = rows[0]
        if bad == "state_index":
            rows[0]["source_state_index"] = 3
        if bad == "rgb_index":
            rows[0]["cameras"][src.CAMERAS[0]]["rgb"]["frame_index"] = 3
        if bad == "offset":
            rows[0]["cameras"][src.CAMERAS[0]]["offset"] = 1
        payload = b"".join(src.canonical(row) + b"\n" for row in rows)
    reseal_frame_index(directory, payload)
    with pytest.raises((ValueError, UnicodeError)):
        cache.verify_episode(directory)


@pytest.mark.parametrize("failure", ["frame", "close", "source_change"])
def test_failure_before_commit_is_isolated_and_successful_retry_is_single_copy(
    tmp_path, failure
):
    _, _, source = bound(tmp_path)

    class Broken(FakeReplay):
        def render(self, camera):
            if self.frame == 1:
                if failure == "frame":
                    raise RuntimeError("injected frame failure")
                if failure == "source_change":
                    # Change a pinned synthetic source metadata file instead.
                    path = source.dataset_dir / "extras/episode_000000/ep_meta.json"
                    path.write_text('{"changed":true}')
            return super().render(camera)

        def close(self):
            super().close()
            if failure == "close":
                raise RuntimeError("injected cleanup failure")

    with pytest.raises((ValueError, RuntimeError)):
        cache.export_episode(
            tmp_path / "cache",
            source,
            [0, 1, 3],
            storage="uint16_mm",
            chunk_frames=2,
            recipe={},
            replay_factory=Broken,
        )
    assert not cache.episode_directory(tmp_path / "cache", source.episode).exists()
    assert len(list((tmp_path / "cache/.failed").glob("*/failure.json"))) == 1
    if failure != "source_change":
        cache.export_episode(
            tmp_path / "cache",
            source,
            [0, 1, 3],
            storage="uint16_mm",
            chunk_frames=2,
            recipe={},
            replay_factory=FakeReplay,
        )
        assert len(list((tmp_path / "cache/tasks").glob("*/episodes/episode_*"))) == 1


def test_exclusive_episode_lock_is_bounded_and_released(tmp_path):
    _, _, source = bound(tmp_path)
    with cache.episode_lock(tmp_path / "cache", source.episode):
        with pytest.raises(BlockingIOError):
            with cache.episode_lock(tmp_path / "cache", source.episode):
                pytest.fail("duplicate owner")
    with cache.episode_lock(tmp_path / "cache", source.episode):
        pass


@pytest.mark.parametrize("failure", ["marker_publish", "directory_rename"])
def test_crash_at_commit_boundaries_never_publishes_partial_episode(
    tmp_path, monkeypatch, failure
):
    _, _, source = bound(tmp_path)
    destination = cache.episode_directory(tmp_path / "cache", source.episode)
    original_json, original_rename = cache.durable_json, cache.os.rename

    def publish(path, value):
        if Path(path).name == "COMPLETE.json":
            raise OSError("injected marker write failure")
        return original_json(path, value)

    def rename(old, new):
        if Path(new) == destination:
            raise OSError("injected commit rename failure")
        return original_rename(old, new)

    if failure == "marker_publish":
        monkeypatch.setattr(cache, "durable_json", publish)
    else:
        monkeypatch.setattr(cache.os, "rename", rename)
    with pytest.raises(OSError, match="injected"):
        cache.export_episode(
            tmp_path / "cache",
            source,
            [0, 3],
            storage="uint16_mm",
            chunk_frames=2,
            recipe={},
            replay_factory=FakeReplay,
        )
    assert not destination.exists() and list(
        (tmp_path / "cache/.failed").glob("*/failure.json")
    )


def test_existing_incomplete_target_is_preserved_not_silently_overwritten(tmp_path):
    _, _, source = bound(tmp_path)
    destination = cache.episode_directory(tmp_path / "cache", source.episode)
    destination.mkdir(parents=True)
    (destination / "unknown_evidence.txt").write_text("preserve")
    with pytest.raises(FileNotFoundError):
        cache.export_episode(
            tmp_path / "cache",
            source,
            [0],
            storage="uint16_mm",
            chunk_frames=2,
            recipe={},
            replay_factory=FakeReplay,
        )
    assert (
        destination / "unknown_evidence.txt"
    ).read_text() == "preserve" and not FakeReplay.created


def native_boundary(source):
    calls, constructions = [], []
    model = SimpleNamespace(
        camera_name2id=lambda name: list(source.camera_shapes).index(name),
        vis=SimpleNamespace(map=SimpleNamespace(znear=0.1, zfar=10)),
        stat=SimpleNamespace(extent=1),
    )
    data = SimpleNamespace(
        time=0.0,
        cam_xmat=np.array([np.eye(3).flatten()] * 2),
        cam_xpos=np.array([[0.0, 0.0, 1.0], [0.2, 0.0, 1.0]]),
    )
    sim = SimpleNamespace(model=model, data=data, saved=None)
    sim.get_state = lambda: np.array(sim.saved)

    def render(**kw):
        h, w = kw["height"], kw["width"]
        rgb = np.broadcast_to(
            np.arange(h, dtype=np.uint8)[:, None, None], (h, w, 3)
        ).copy()
        depth = np.broadcast_to(np.linspace(0.1, 0.6, h)[:, None], (h, w)).copy()
        return rgb, depth

    sim.render = render
    env = SimpleNamespace(sim=sim, closed=False)
    env.close = lambda: setattr(env, "closed", True)

    def make(**kwargs):
        constructions.append(kwargs)
        return env

    def reset_to(instance, value):
        assert instance is env
        calls.append(value)
        sim.saved = value["states"].copy()
        data.time = sim.saved[0]

    def extrinsic(sim, camera):
        T = np.eye(4)
        T[:3, 3] = sim.data.cam_xpos[sim.model.camera_name2id(camera)]
        return T @ np.diag([1.0, -1.0, -1.0, 1.0])

    helpers = SimpleNamespace(
        get_real_depth_map=lambda sim, b: 0.1 / (1 - b * 0.99),
        get_camera_intrinsic_matrix=lambda sim, camera, h, w: np.array(
            [[4, 0, w / 2], [0, 4, h / 2], [0, 0, 1.0]]
        ),
        get_camera_extrinsic_matrix=extrinsic,
    )
    return env, calls, constructions, make, reset_to, helpers


def test_production_replay_adapter_full_model_then_state_only_and_one_flip(tmp_path):
    _, _, source = bound(tmp_path)
    original_meta = json.dumps(source.env_metadata, sort_keys=True)
    env, calls, constructions, make, reset, helpers = native_boundary(source)
    replay = Replay(source, make=make, reset_to=reset, camera_utils=helpers)
    try:
        assert set(calls[0]) == {"model", "ep_meta", "states"}
        assert calls[0]["model"] == source.model_xml
        assert json.loads(calls[0]["ep_meta"]) == source.ep_meta
        replay.restore(3)
        assert set(calls[-1]) == {"states"} and calls[-1]["states"][0] == pytest.approx(
            0.65
        )
        sample = replay.render(src.CAMERAS[0])
        assert sample["rgb"][0, 0, 0] == 7  # Exactly one bottom-left -> top-left flip.
        assert sample["depth_m"][0, 0] == pytest.approx(0.1 / (1 - 0.6 * 0.99))
        np.testing.assert_allclose(
            sample["T_world_camera_cv"], sample["T_world_camera_gl"] @ g.GL_FROM_CV
        )
        assert (
            constructions[0]["has_renderer"] is False
            and constructions[0]["use_camera_obs"] is False
        )
        assert constructions[0]["camera_depths"] is True
        assert json.dumps(source.env_metadata, sort_keys=True) == original_meta
    finally:
        replay.close()
    assert env.closed


def test_replay_initialization_error_closes_owned_environment(tmp_path):
    _, _, source = bound(tmp_path)
    env, _, _, make, _, helpers = native_boundary(source)

    def broken(*args):
        raise RuntimeError("injected official reset failure")

    with pytest.raises(RuntimeError):
        Replay(source, make=make, reset_to=broken, camera_utils=helpers)
    assert env.closed


def test_replay_does_not_accept_failed_state_restoration(tmp_path):
    _, _, source = bound(tmp_path)
    env, _, _, make, reset, helpers = native_boundary(source)
    replay = Replay(source, make=make, reset_to=reset, camera_utils=helpers)
    env.sim.get_state = lambda: env.sim.saved + 1
    try:
        with pytest.raises(ValueError, match="differs"):
            replay.restore(0)
    finally:
        replay.close()


def test_dry_run_real_mapping_path_has_no_renderer_or_output_side_effect(
    tmp_path, capsys
):
    raw, flat = fixture_tree(tmp_path)

    def forbidden(*args):
        pytest.fail("dry-run cannot construct a simulator")

    command = [
        "--raw-root",
        str(raw),
        "--flat-root",
        str(flat),
        "--output-root",
        str(tmp_path / "out"),
        "--local-episode",
        "0",
        "--task-class",
        "CloseFridge",
        "--frames",
        "0,1,3",
        "--state-index-policy",
        "frame_index",
        "--dry-run",
    ]
    assert cli.main(command, replay_factory=forbidden) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["selected_frame_count"] == 3 and not (tmp_path / "out").exists()
    assert result["uncompressed_array_bytes_estimate"] == 3 * 2 * (
        8 * 8 * 2 + 41 * 4 + 8
    )


def test_cache_contract_no_implicit_configuration_drift(tmp_path):
    root = tmp_path / "cache"
    cache.ensure_cache_manifest(root, {"schema": cache.SCHEMA, "cameras": ["left"]})
    cache.ensure_cache_manifest(root, {"schema": cache.SCHEMA, "cameras": ["left"]})
    with pytest.raises(ValueError, match="drift"):
        cache.ensure_cache_manifest(
            root, {"schema": cache.SCHEMA, "cameras": ["wrist"]}
        )


def test_disk_budget_stops_before_environment_creation(tmp_path, monkeypatch):
    _, _, source = bound(tmp_path)
    monkeypatch.setattr(
        cache.shutil, "disk_usage", lambda path: SimpleNamespace(free=32)
    )
    with pytest.raises(OSError, match="disk space"):
        cache.export_episode(
            tmp_path / "cache",
            source,
            [0, 1],
            storage="uint16_mm",
            chunk_frames=2,
            recipe={},
            replay_factory=FakeReplay,
            min_free_bytes=1024,
        )
    assert not FakeReplay.created
    assert not cache.episode_directory(tmp_path / "cache", source.episode).exists()


def test_full_export_cli_resume_and_input_overlap_refusal(tmp_path, capsys):
    raw, flat = fixture_tree(tmp_path)
    output = tmp_path / "out"
    command = [
        "--raw-root",
        str(raw),
        "--flat-root",
        str(flat),
        "--output-root",
        str(output),
        "--global-episode",
        "0",
        "--state-index-policy",
        "frame_index",
        "--chunk-frames",
        "2",
        "--min-free-bytes",
        "0",
    ]
    assert cli.main(command, replay_factory=FakeReplay) == 0
    first = list(output.glob("_runs/*.json"))[0]
    report = src.read_json(first)
    assert report["selected_frame_count"] == report["completed_frame_count"] == 4
    assert FakeReplay.created == [0]
    assert cli.main(command, replay_factory=FakeReplay) == 0
    assert FakeReplay.created == [0] and len(list(output.glob("_runs/*.json"))) == 2
    bad = command.copy()
    bad[bad.index("--output-root") + 1] = str(raw / "forbidden")
    with pytest.raises(ValueError, match="separate"):
        cli.main(bad, replay_factory=FakeReplay)
    assert not (raw / "forbidden").exists()
    capsys.readouterr()


def test_cli_failure_isolated_other_episode_commits_and_nonzero_final_report(
    tmp_path, capsys
):
    raw, flat = fixture_tree(tmp_path, count=2)
    selection = tmp_path / "selection.json"
    write_json(
        selection,
        {
            "schema": "psm_wma_rgbd_episode_selection_v1",
            "episode_namespace": "global_episode_index",
            "flat_mapping_sha256": src.sha256(flat / "flat_v3_mapping.parquet"),
            "episodes": [
                {"task_class": "CloseFridge", "global_episode_index": 0},
                {"task_class": "OpenCabinet", "global_episode_index": 1},
            ],
        },
    )

    class FailOne(FakeReplay):
        def render(self, camera):
            if self.source.episode.global_episode_index == 0:
                raise RuntimeError("owned episode only")
            return super().render(camera)

    output = tmp_path / "out"
    assert (
        cli.main(
            [
                "--raw-root",
                str(raw),
                "--flat-root",
                str(flat),
                "--output-root",
                str(output),
                "--selection-manifest",
                str(selection),
                "--state-index-policy",
                "frame_index",
                "--min-free-bytes",
                "0",
            ],
            replay_factory=FailOne,
        )
        == 1
    )
    report = src.read_json(next(output.glob("_runs/*.json")))
    assert report["failed_episode_count"] == 1 and report["selected_frame_count"] == 8
    assert report["completed_frame_count"] == 4
    assert list(output.glob("tasks/OpenCabinet/episodes/episode_000001/COMPLETE.json"))
    assert not list(output.glob("tasks/CloseFridge/episodes/*/COMPLETE.json"))
    capsys.readouterr()


@pytest.mark.parametrize(
    "kind", ["g0_wrong_source", "external_wrong_mapping", "correct"]
)
def test_selection_identity_cannot_mix_datasets_with_same_numeric_ids(tmp_path, kind):
    raw, flat = fixture_tree(tmp_path)
    path = tmp_path / "membership.json"
    value = {
        "schema": "psm_wma_rgbd_episode_selection_v1",
        "episode_namespace": "global_episode_index",
        "flat_mapping_sha256": src.sha256(flat / "flat_v3_mapping.parquet"),
        "episodes": [{"task_class": "CloseFridge", "global_episode_index": 0}],
    }
    if kind == "g0_wrong_source":
        value = {"schema_version": "exact_window_v1", "source_dataset": str(raw)}
    if kind == "external_wrong_mapping":
        value["flat_mapping_sha256"] = "0" * 64
    write_json(path, value)
    if kind == "correct":
        src.verify_selection_source(
            path, flat, src.sha256(flat / "flat_v3_mapping.parquet")
        )
    else:
        with pytest.raises(ValueError):
            src.verify_selection_source(
                path, flat, src.sha256(flat / "flat_v3_mapping.parquet")
            )


def test_verifier_failure_always_writes_new_non_success_report(tmp_path, capsys):
    directory, report = tmp_path / "incomplete", tmp_path / "report.json"
    directory.mkdir()
    assert checker.main(["--episode-dir", str(directory), "--report", str(report)]) == 1
    assert src.read_json(report)["status"] == "VERIFICATION_FAILED"
    with pytest.raises(ValueError, match="new"):
        checker.main(["--episode-dir", str(directory), "--report", str(report)])


def test_verifier_text_statistics_mask_pose_and_half_second_offset(tmp_path):
    raw, flat, _, directory = exported(tmp_path)

    def reader(ref, frame):
        return np.full((8, 8, 3), 7 + frame, dtype=np.uint8)

    report = checker.verify(
        directory,
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=FakeReplay,
        rgb_reader=reader,
    )
    assert report["geometry_gate"] == "PASS"
    assert report["status"] == "SYNTHETIC_SPATIAL_REPLAY_CHECKS_PASS"
    assert report["timestamp_diagnostic"]["min_offset_s"] == pytest.approx(0.5)
    assert report["camera_pose_motion"][src.CAMERAS[2]]["changed"] is True
    assert report["camera_pose_motion"][src.CAMERAS[0]]["changed"] is False
    assert all(
        c["rgb"]["mae"] == 0 and c["rgb"]["ssim"] == pytest.approx(1)
        for r in report["frames"]
        for c in r["cameras"].values()
    )


@pytest.mark.parametrize("status", ["FAIL", "INCONCLUSIVE"])
def test_unproven_ray_geometry_cannot_pass_physical_gate(tmp_path, status):
    raw, flat, _, directory = exported(tmp_path)

    class Unproven(FakeReplay):
        def ray_check(self, *args, **kwargs):
            return {"status": status}

    report = checker.verify(
        directory,
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=Unproven,
        rgb_reader=lambda ref, i: np.full((8, 8, 3), 7 + i, dtype=np.uint8),
    )
    assert report["geometry_gate"] == "FAIL_OR_INCONCLUSIVE"


@pytest.mark.parametrize(
    "violation", ["none", "vertical_flip", "ray_distance", "unknown_filters"]
)
def test_real_cpu_mj_ray_tilted_plane_independent_of_project_unproject(
    violation, monkeypatch, tmp_path
):
    monkeypatch.setenv("MUJOCO_GL", "disable")
    import mujoco

    angle = 0.3
    model = mujoco.MjModel.from_xml_string(f'''<mujoco><worldbody>
      <geom name="surface" type="plane" size="3 3 .1" euler="{np.degrees(angle)} 0 0" group="1"/>
      <geom name="hidden_occluder" type="sphere" size=".2" pos="0 0 .6" group="5"/>
    </worldbody></mujoco>''')
    data = mujoco.MjData(model)
    mujoco.mj_forward(model, data)
    height = width = 8
    K = np.array([[8, 0, 4], [0, 8, 4], [0, 0, 1.0]])
    T_gl = np.eye(4)
    T_gl[2, 3] = 1
    y = (np.arange(height)[:, None] + 0.5 - 4) / 8
    z = np.broadcast_to(
        np.cos(angle) / (np.cos(angle) - np.sin(angle) * y), (height, width)
    ).copy()
    fresh_z = z.copy()
    if violation == "vertical_flip":
        z = z[::-1].copy()
    if violation == "ray_distance":
        x = (np.arange(width)[None, :] + 0.5 - 4) / 8
        z *= np.sqrt(1 + x * x + y * y)
    segmentation = np.empty((height, width, 2), dtype=np.int32)
    segmentation[..., 0] = int(mujoco.mjtObj.mjOBJ_GEOM)
    segmentation[..., 1] = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_GEOM, "surface")
    near = model.vis.map.znear * model.stat.extent
    far = model.vis.map.zfar * model.stat.extent
    raw_buffer = ((1 - near / fresh_z) / (1 - near / far))[::-1]

    def render(**kwargs):
        if kwargs.get("segmentation"):
            return segmentation[::-1]
        rgb = np.zeros((height, width, 3), dtype=np.uint8)
        return (rgb, raw_buffer) if kwargs.get("depth") else rgb

    options = mujoco.MjvOption()
    options.geomgroup[:] = [1, 1, 1, 0, 0, 0]
    sim = SimpleNamespace(
        model=model,
        data=data,
        render=render,
        _render_context_offscreen=SimpleNamespace(
            vopt=options,
            con=SimpleNamespace(offSamples=0),
            scn=SimpleNamespace(
                flags=mujoco.MjvScene().flags.copy(),
                ngeom=1,
                geoms=[
                    SimpleNamespace(
                        objtype=int(mujoco.mjtObj.mjOBJ_GEOM),
                        objid=0,
                        transparent=False,
                        rgba=np.ones(4),
                    )
                ],
            ),
        ),
    )
    if violation == "unknown_filters":
        sim._render_context_offscreen = None
    replay = object.__new__(Replay)
    replay.env = SimpleNamespace(sim=sim)
    sample = {
        "depth_m": z,
        "valid": np.ones_like(z, dtype=bool),
        "K": K,
        "T_world_camera_cv": T_gl @ g.GL_FROM_CV,
    }
    result = replay.ray_check("synthetic", sample, atol_m=1e-7, min_samples=32)
    write_json(
        tmp_path / "native_cpu_ray.json",
        {
            "synthetic_scene": True,
            "real_renderer_executed": False,
            "mujoco_version": mujoco.__version__,
            "violation": violation,
            **result,
        },
    )
    assert result["status"] == (
        {"none": "PASS", "unknown_filters": "INCONCLUSIVE"}.get(violation, "FAIL")
    )
    if violation == "none":
        assert result["matching_geom_samples"] == 64
        assert result["max_abs_z_error_m"] < 1e-10
        assert result["static_geoms_included"] is True and result["geomgroup"][5] == 0


def test_static_float32_camera_rotation_is_not_reported_as_motion(tmp_path):
    raw, flat, source = bound(tmp_path)
    rotation = (
        Rotation.from_euler(
            "xyz", [-2.6178494833854566, 1.7480055403415324, 2.8816979303657675]
        )
        .as_matrix()
        .astype(np.float32)
    )

    class Rotated(FakeReplay):
        def render(self, camera):
            sample = super().render(camera)
            sample["T_world_camera_gl"][:3, :3] = rotation
            sample["T_world_camera_cv"] = sample["T_world_camera_gl"] @ np.diag(
                [1.0, -1.0, -1.0, 1.0]
            )
            return sample

    result = cache.export_episode(
        tmp_path / "out",
        source,
        [0, 1, 3],
        storage="uint16_mm",
        chunk_frames=2,
        recipe={"regression": "static_f32_pose"},
        replay_factory=Rotated,
    )
    report = checker.verify(
        result["directory"],
        replay=True,
        raw_root=raw,
        flat_root=flat,
        state_index_policy="frame_index",
        replay_factory=Rotated,
        rgb_reader=lambda ref, i: np.full((8, 8, 3), 7 + i, dtype=np.uint8),
    )
    motion = report["camera_pose_motion"][src.CAMERAS[0]]
    assert motion["changed"] is False
    assert motion["max_rotation_rad"] < 1e-7
