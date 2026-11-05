"""Bounded per-camera chunks and immutable episode directory commits."""

from __future__ import annotations

import errno
import fcntl
import json
import os
import shutil
import uuid
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

import numpy as np

from tools.g0.robocasa_work_queue import atomic_write_json

from . import LEGACY_SCHEMA, SCHEMA
from .geometry import (
    CONVENTIONS,
    ENCODING_COUNTS,
    check_calibration,
    decode_depth,
    depth_statistics,
    encode_depth,
    encoding_statistics,
    validate_encoding_statistics,
)
from .source import (
    Episode,
    canonical,
    digest,
    integer,
    read_json,
    sha256,
    verify_witnesses,
)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_json(path, value):
    # Reuse the existing g0 JSON publisher; validate finite JSON and add durability.
    canonical(value)
    atomic_write_json(Path(path), value)
    with Path(path).open("rb") as stream:
        os.fsync(stream.fileno())
    sync_directory(Path(path).parent)


def _check_root_schema(root):
    existing = root / "cache_manifest.json"
    if existing.exists() and read_json(existing).get("schema") != SCHEMA:
        raise ValueError(
            "legacy/unknown root cache schema; explicit verified transition required"
        )


def ensure_cache_manifest(root, contract):
    root = Path(root)
    if contract.get("schema") != SCHEMA:
        raise ValueError("requested root cache schema must be v2")
    _check_root_schema(root)
    if not (root / "cache_manifest.json").exists() and any(
        (root / name).exists() for name in ("tasks", ".staging", ".failed")
    ):
        raise ValueError(
            "unversioned cache contents; explicit verified transition required"
        )
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".manifest.lock").open("ab") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        path = root / "cache_manifest.json"
        if path.exists():
            if read_json(path) != contract:
                raise ValueError(
                    "cache configuration drift; choose a new output namespace"
                )
        else:
            durable_json(path, contract)


def episode_directory(root, episode):
    return (
        Path(root)
        / "tasks"
        / episode.task_class
        / "episodes"
        / f"episode_{episode.global_episode_index:06d}"
    )


@contextmanager
def episode_lock(root, episode):
    directory = Path(root) / ".locks"
    directory.mkdir(parents=True, exist_ok=True)
    with (
        directory / f"{episode.task_class}_{episode.global_episode_index:06d}.lock"
    ).open("ab") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def identity(source, frames, storage, chunk_frames, recipe):
    return {
        "schema": SCHEMA,
        "episode": asdict(source.episode),
        "frames": list(frames),
        "cameras": list(source.camera_shapes),
        "camera_shapes": {k: list(v) for k, v in source.camera_shapes.items()},
        "depth_storage": storage,
        "chunk_frames": chunk_frames,
        "source_files": source.witnesses,
        "alignment": source.alignment,
        "conventions": CONVENTIONS,
        "recipe": recipe,
    }


def _safe_file(directory, relative):
    relative = Path(relative)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("cache artifact path escapes episode")
    path = directory / relative
    if (
        path.is_symlink()
        or not path.resolve().is_relative_to(directory.resolve())
        or not path.is_file()
    ):
        raise ValueError("cache artifact missing/unsafe")
    return path


def read_frames(path):
    rows = []
    with Path(path).open("rb") as stream:
        for line in stream:
            if len(line) > 128 * 1024 or not line.endswith(b"\n"):
                raise ValueError("truncated/oversized frame index record")
            rows.append(json.loads(line.decode("utf-8")))
    return rows


def verify_episode(directory, *, expected_digest=None):
    directory = Path(directory)
    marker = read_json(directory / "COMPLETE.json")
    manifest = read_json(directory / "manifest.json")
    if marker.get("schema") == LEGACY_SCHEMA or manifest.get("schema") == LEGACY_SCHEMA:
        raise ValueError(
            "legacy v1 cache requires explicit verified transition; no automatic migration"
        )
    if (
        marker.get("schema") != SCHEMA
        or manifest.get("schema") != SCHEMA
        or manifest.get("status") != "COMPLETE"
        or sha256(directory / "manifest.json") != marker.get("manifest_sha256")
        or digest(manifest["identity"]) != marker.get("export_digest")
        or marker["export_digest"] != manifest.get("export_digest")
    ):
        raise ValueError("incomplete/corrupt episode commit")
    if expected_digest is not None and manifest["export_digest"] != expected_digest:
        raise ValueError("episode export identity differs; use a new output namespace")
    spec = manifest["identity"]
    episode = Episode(**spec["episode"])
    frames = spec["frames"]
    if not frames or frames != sorted(set(frames)):
        raise ValueError("invalid committed frame selection")
    if (
        spec.get("schema") != SCHEMA
        or spec["conventions"] != CONVENTIONS
        or spec["alignment"]["state_index_policy"] != "explicit_frame_index"
    ):
        raise ValueError("cache coordinate/state mapping convention mismatch")
    files = manifest["files"]
    expected_paths = set(files) | {"manifest.json", "COMPLETE.json"}
    actual_paths = {
        p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()
    }
    if actual_paths != expected_paths or "frames.jsonl" not in files:
        raise ValueError(
            "cache artifact set is incomplete or contains unexpected files"
        )
    for relative, record in files.items():
        path = _safe_file(directory, relative)
        if path.stat().st_size != record["size"] or sha256(path) != record["sha256"]:
            raise ValueError(f"cache artifact checksum mismatch: {relative}")
    rows = read_frames(directory / "frames.jsonl")
    if len(rows) != len(frames) or manifest["frame_count"] != len(frames):
        raise ValueError("frame index count mismatch")
    seen_chunks = {}
    for ordinal, (frame, row) in enumerate(zip(frames, rows, strict=True)):
        if any(row.get(k) != v for k, v in episode.frame(frame).items()):
            raise ValueError("frame/global/local/state mapping drift")
        if set(row["cameras"]) != set(spec["cameras"]):
            raise ValueError("frame camera membership drift")
        for camera, reference in row["cameras"].items():
            chunk_index, offset = divmod(
                ordinal, integer(spec["chunk_frames"], "chunk_frames", minimum=1)
            )
            path = f"cameras/{camera}/chunk_{chunk_index:06d}.npz"
            if reference["chunk"] != path or reference["offset"] != offset:
                raise ValueError("chunk/offset frame mapping drift")
            if reference["rgb"] != {
                "video": manifest["rgb_references"][camera]["video"],
                "frame_index": frame,
            }:
                raise ValueError("RGB reference/index mismatch")
            seen_chunks.setdefault((camera, path), []).append(frame)
    if set(files) != {"frames.jsonl"} | {path for _, path in seen_chunks}:
        raise ValueError("missing/unreferenced camera chunks")
    total_raw_bytes = 0
    by_frame = {row["frame_index"]: row for row in rows}
    encoding_totals = {
        c: {**dict.fromkeys(ENCODING_COUNTS, 0), "warning_frames": 0}
        for c in spec["cameras"]
    }
    for (camera, relative), expected_frames in seen_chunks.items():
        with np.load(_safe_file(directory, relative), allow_pickle=False) as archive:
            if set(archive.files) != {
                "depth",
                "K",
                "T_world_camera_gl",
                "T_world_camera_cv",
                "frame_indices",
            }:
                raise ValueError("unexpected depth chunk arrays")
            # NpzFile indexing decompresses each time. Keep just this bounded
            # chunk in memory instead of re-decoding its matrices for every row.
            chunk = {key: archive[key] for key in archive.files}
            n = len(expected_frames)
            height, width = spec["camera_shapes"][camera]
            if chunk["depth"].shape != (n, height, width):
                raise ValueError("depth chunk frame/shape mismatch")
            decode_depth(chunk["depth"], spec["depth_storage"])
            for index, frame in enumerate(expected_frames):
                stats = by_frame[frame]["cameras"][camera]["encoding"]
                validate_encoding_statistics(
                    stats, chunk["depth"][index], spec["depth_storage"]
                )
                for key in ENCODING_COUNTS:
                    encoding_totals[camera][key] += stats[key]
                encoding_totals[camera]["warning_frames"] += int(
                    stats["warning"] is not None
                )
            if chunk["frame_indices"].dtype != np.int64 or not np.array_equal(
                chunk["frame_indices"], expected_frames
            ):
                raise ValueError("depth chunk frame indices disagree")
            for key, shape in [
                ("K", (n, 3, 3)),
                ("T_world_camera_gl", (n, 4, 4)),
                ("T_world_camera_cv", (n, 4, 4)),
            ]:
                if chunk[key].dtype != np.float32 or chunk[key].shape != shape:
                    raise ValueError("camera calibration must be per-frame float32")
            for index in range(n):
                check_calibration(
                    chunk["K"][index],
                    chunk["T_world_camera_gl"][index],
                    chunk["T_world_camera_cv"][index],
                )
            total_raw_bytes += sum(value.nbytes for value in chunk.values())
    if manifest.get("depth_encoding") != encoding_totals:
        raise ValueError("episode depth encoding totals mismatch")
    if manifest["raw_array_bytes"] != total_raw_bytes:
        raise ValueError("cache capacity accounting mismatch")
    return manifest, rows


def cached_sample(directory, manifest, row, camera):
    reference = row["cameras"][camera]
    with np.load(Path(directory) / reference["chunk"], allow_pickle=False) as chunk:
        i = reference["offset"]
        depth = decode_depth(chunk["depth"][i], manifest["identity"]["depth_storage"])
        return {
            "depth_m": depth,
            "valid": depth > 0,
            **{
                key: chunk[key][i].copy()
                for key in ("K", "T_world_camera_gl", "T_world_camera_cv")
            },
        }


def require_disk_space(root, payload_bytes, min_free_bytes):
    integer(min_free_bytes, "min_free_bytes")
    required = int(payload_bytes * 1.002) + 16384 + min_free_bytes
    if shutil.disk_usage(root).free < required:
        raise OSError(
            errno.ENOSPC,
            "insufficient disk space for next chunk plus configured reserve",
        )


def export_episode(
    root,
    source,
    frames,
    *,
    storage,
    chunk_frames,
    recipe,
    replay_factory,
    min_free_bytes=0,
):
    frames = list(frames)
    if not frames or frames != sorted(set(frames)):
        raise ValueError("requested frames must be unique, sorted and nonempty")
    for frame in frames:
        source.episode.frame(frame)
    integer(chunk_frames, "chunk_frames", minimum=1)
    if chunk_frames > 256:
        raise ValueError("chunk_frames cannot exceed the bounded 256-frame buffer")
    root = Path(root).resolve()
    _check_root_schema(root)
    for input_file in source.witnesses:
        source_path = Path(input_file["path"]).resolve()
        if source_path.is_relative_to(root) or root.is_relative_to(source_path.parent):
            raise ValueError("cache output overlaps source inputs")
    spec = identity(source, frames, storage, chunk_frames, recipe)
    export_digest = digest(spec)
    destination = episode_directory(root, source.episode)
    with episode_lock(root, source.episode):
        verify_witnesses(source.witnesses)
        if destination.exists():
            manifest, _ = verify_episode(destination, expected_digest=export_digest)
            return {
                "status": "SKIPPED_VERIFIED",
                "directory": str(destination),
                "frame_count": manifest["frame_count"],
            }
        staging = root / ".staging" / uuid.uuid4().hex
        staging.mkdir(parents=True)
        encoding_totals = {
            c: {**dict.fromkeys(ENCODING_COUNTS, 0), "warning_frames": 0}
            for c in source.camera_shapes
        }
        files, buffers, raw_bytes, max_error = (
            {},
            {c: [] for c in source.camera_shapes},
            0,
            0.0,
        )

        def record_file(path):
            files[path.relative_to(staging).as_posix()] = {
                "sha256": sha256(path),
                "size": path.stat().st_size,
            }

        def flush(camera, number):
            nonlocal raw_bytes
            batch = buffers[camera]
            if not batch:
                return
            arrays = {key: np.stack([row[key] for row in batch]) for key in batch[0]}
            arrays["frame_indices"] = arrays["frame_indices"].astype(np.int64)
            chunk_bytes = sum(a.nbytes for a in arrays.values())
            require_disk_space(root, chunk_bytes, min_free_bytes)
            raw_bytes += chunk_bytes
            path = staging / f"cameras/{camera}/chunk_{number:06d}.npz"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as stream:
                np.savez_compressed(stream, **arrays)
                stream.flush()
                os.fsync(stream.fileno())
            record_file(path)
            buffers[camera] = []

        try:
            largest = max(
                min(chunk_frames, len(frames))
                * (h * w * (2 if storage == "uint16_mm" else 4) + 41 * 4 + 8)
                for h, w in source.camera_shapes.values()
            )
            require_disk_space(root, largest, min_free_bytes)
            backend = replay_factory(source)
            try:
                with (staging / "frames.jsonl").open("wb") as stream:
                    for ordinal, frame in enumerate(frames):
                        row = source.episode.frame(frame)
                        row.update(backend.restore(frame))
                        row["flat_timestamp"] = float(source.flat_timestamps[frame])
                        row["cameras"] = {}
                        number, offset = divmod(ordinal, chunk_frames)
                        for camera in source.camera_shapes:
                            sample = backend.render(camera)
                            check_calibration(
                                sample["K"],
                                sample["T_world_camera_gl"],
                                sample["T_world_camera_cv"],
                            )
                            encoded, valid, error = encode_depth(
                                sample["depth_m"], sample["valid"], storage
                            )
                            if valid.shape != tuple(source.camera_shapes[camera]):
                                raise ValueError(
                                    "rendered camera dimensions differ from source binding"
                                )
                            stats = encoding_statistics(
                                sample["depth_m"], sample["valid"], storage
                            )
                            for key in ENCODING_COUNTS:
                                encoding_totals[camera][key] += stats[key]
                            encoding_totals[camera]["warning_frames"] += int(
                                stats["warning"] is not None
                            )
                            max_error = max(max_error, error)
                            buffers[camera].append(
                                {
                                    "depth": encoded,
                                    "frame_indices": np.array(frame, dtype=np.int64),
                                    **{
                                        key: np.asarray(sample[key], dtype=np.float32)
                                        for key in (
                                            "K",
                                            "T_world_camera_gl",
                                            "T_world_camera_cv",
                                        )
                                    },
                                }
                            )
                            row["cameras"][camera] = {
                                "chunk": f"cameras/{camera}/chunk_{number:06d}.npz",
                                "offset": offset,
                                "rgb": {
                                    "video": source.rgb[camera]["video"],
                                    "frame_index": frame,
                                },
                                "depth": depth_statistics(sample["depth_m"], valid),
                                "quantization_max_abs_m": error,
                                "encoding": stats,
                            }
                            if len(buffers[camera]) == chunk_frames:
                                flush(camera, number)
                        stream.write(canonical(row) + b"\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                for camera in source.camera_shapes:
                    flush(camera, (len(frames) - 1) // chunk_frames)
                runtime = backend.identity
            finally:
                backend.close()
            verify_witnesses(source.witnesses)
            record_file(staging / "frames.jsonl")
            payload_bytes = sum(
                row["size"] for name, row in files.items() if name.endswith(".npz")
            )
            manifest = {
                "schema": SCHEMA,
                "status": "COMPLETE",
                "export_digest": export_digest,
                "identity": spec,
                "frame_count": len(frames),
                "full_episode": frames == list(range(source.episode.length)),
                "runtime": runtime,
                "rgb_references": source.rgb,
                "files": files,
                "depth_encoding": encoding_totals,
                "raw_array_bytes": raw_bytes,
                "compressed_payload_bytes": payload_bytes,
                "compression_ratio_raw_over_stored": raw_bytes / payload_bytes,
                "quantization_max_abs_m": max_error,
                "physical_geometry_gate": "PENDING_DS_GATE_B_C",
            }
            durable_json(staging / "manifest.json", manifest)
            durable_json(
                staging / "COMPLETE.json",
                {
                    "schema": SCHEMA,
                    "export_digest": export_digest,
                    "manifest_sha256": sha256(staging / "manifest.json"),
                },
            )
            verify_episode(staging, expected_digest=export_digest)
            for path in sorted(
                (p for p in staging.rglob("*") if p.is_dir()), reverse=True
            ):
                sync_directory(path)
            sync_directory(staging)
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise FileExistsError("episode appeared outside its exclusive lock")
            os.rename(staging, destination)
            parent = destination.parent
            while parent.is_relative_to(root):
                sync_directory(parent)
                if parent == root:
                    break
                parent = parent.parent
            return {
                "status": "EXPORTED",
                "directory": str(destination),
                "frame_count": len(frames),
                "compressed_payload_bytes": payload_bytes,
                "depth_encoding": encoding_totals,
                "quantization_max_abs_m": max_error,
            }
        except BaseException as exc:
            failed = root / ".failed" / staging.name
            failed.parent.mkdir(parents=True, exist_ok=True)
            if staging.exists():
                os.rename(staging, failed)
            try:
                durable_json(
                    failed / "failure.json",
                    {
                        "schema": SCHEMA,
                        "status": "FAILED",
                        "episode": asdict(source.episode),
                        "export_digest": export_digest,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
            except OSError as record_error:
                exc.add_note(
                    f"failure record could not be persisted: {record_error}; owned staging retained"
                )
            raise
