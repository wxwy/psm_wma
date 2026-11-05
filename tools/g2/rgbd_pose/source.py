"""Read the existing episode mapping and accepted training-manifest membership.

There is deliberately no episode sampler here. Row intervals are half-open;
timestamps are diagnostic data and never determine a simulator state index.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

CAMERAS = (
    "robot0_agentview_left",
    "robot0_agentview_right",
    "robot0_eye_in_hand",
)
CORE_COLUMNS = (
    "task_class",
    "local_episode_index",
    "global_episode_index",
    "local_row_from",
    "local_row_to",
    "global_row_from",
    "global_row_to",
    "length",
)


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha256(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(data)
    return result.hexdigest()


def read_json(path):
    path = Path(path)
    if path.stat().st_size > 32 * 1024**2:
        raise ValueError(f"JSON exceeds 32 MiB: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def integer(value, name, *, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def task_name(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value):
        raise ValueError("invalid underlying task class")
    return value


def witness(path, *, content=True):
    path = Path(path).resolve(strict=True)
    info = path.stat()
    if not path.is_file():
        raise ValueError(f"not a regular source file: {path}")
    result = {
        "path": str(path),
        "size": info.st_size,
        "mtime_ns": info.st_mtime_ns,
        "ctime_ns": info.st_ctime_ns,
        "device": info.st_dev,
        "inode": info.st_ino,
    }
    if content:
        result["sha256"] = sha256(path)
    return result


def verify_witnesses(records):
    for record in records:
        if witness(record["path"], content="sha256" in record) != record:
            raise ValueError(f"source changed during export: {record['path']}")


def selected_episodes(path):
    """Consume existing g0 accepted cache rows, or an explicit global-ID list."""
    value = read_json(path)
    accepted = []
    if value.get("schema") == "psm_wma_rgbd_episode_selection_v1":
        if value.get("episode_namespace") != "global_episode_index":
            raise ValueError("selection must explicitly use global_episode_index")
        for row in value["episodes"]:
            accepted.append(
                (
                    task_name(row["task_class"]),
                    integer(row["global_episode_index"], "global episode"),
                )
            )
    elif (
        value.get("schema_version") == "exact_window_v1"
        and value.get("source_format") == "lerobot_v3"
    ):
        # These are the actual accepted members produced by g0, not a newly
        # sampled prefix. selected_episode_ids can also contain skipped-short eps.
        for task in value["tasks"]:
            name = task_name(task["task_class"])
            rows = task.get("episodes")
            if not isinstance(rows, list) or not rows:
                raise ValueError("training manifest must declare accepted episode rows")
            ids = [
                integer(row["episode_index"], "accepted global episode") for row in rows
            ]
            if any(row.get("task_class", name) != name for row in rows):
                raise ValueError("accepted episode belongs to another task")
            if "selected_episode_ids" in task:
                selected = [
                    integer(i, "selected global episode")
                    for i in task["selected_episode_ids"]
                ]
                if selected != sorted(set(selected)) or not set(ids).issubset(selected):
                    raise ValueError("accepted/selected episode membership disagrees")
                checksum = hashlib.sha256(
                    ",".join(map(str, selected)).encode()
                ).hexdigest()
                if task.get("selected_episode_digest") != checksum:
                    raise ValueError("g0 selected_episode_digest mismatch")
            accepted.extend((name, i) for i in ids)
        if "episode_count" in value and value["episode_count"] != len(accepted):
            raise ValueError("training manifest accepted episode count mismatch")
    else:
        raise ValueError("unsupported selection manifest; no implicit N/seed sampling")
    if not accepted or len(set(accepted)) != len(accepted):
        raise ValueError("empty or duplicate selected episodes")
    if len({index for _, index in accepted}) != len(accepted):
        raise ValueError("one global episode cannot belong to two tasks")
    return set(accepted), witness(path)


def verify_selection_source(path, flat_root, mapping_sha256):
    value = read_json(path)
    if value.get("schema_version") == "exact_window_v1":
        recorded = value.get("source_dataset")
        if (
            not isinstance(recorded, str)
            or Path(recorded).resolve() != Path(flat_root).resolve()
        ):
            raise ValueError("training selection source_dataset differs from Flat root")
    elif value.get("schema") == "psm_wma_rgbd_episode_selection_v1":
        if value.get("flat_mapping_sha256") != mapping_sha256:
            raise ValueError(
                "external episode selection must bind the exact Flat mapping SHA256"
            )
    else:
        raise ValueError("unknown episode selection source identity")


@dataclass(frozen=True)
class Episode:
    task_class: str
    local_episode_index: int
    global_episode_index: int
    local_row_from: int
    local_row_to: int
    global_row_from: int
    global_row_to: int
    length: int

    def frame(self, index):
        integer(index, "frame index")
        if index >= self.length:
            raise ValueError("frame outside mapped episode")
        return {
            "task_class": self.task_class,
            "global_episode_index": self.global_episode_index,
            "local_episode_index": self.local_episode_index,
            "frame_index": index,
            "local_row_index": self.local_row_from + index,
            "global_row_index": self.global_row_from + index,
            "source_state_index": index,
            "source_rgb_frame_index": index,
        }


def mapping_episodes(path):
    import pyarrow.parquet as pq

    table = pq.read_table(path)
    if set(CORE_COLUMNS) - set(table.column_names):
        raise ValueError(
            f"episode mapping lacks columns: {sorted(set(CORE_COLUMNS) - set(table.column_names))}"
        )
    episodes, global_ids, local_ids = [], set(), set()
    for row in table.to_pylist():
        values = {k: row[k] for k in CORE_COLUMNS}
        values["task_class"] = task_name(values["task_class"])
        for key in CORE_COLUMNS[1:]:
            integer(values[key], key, minimum=1 if key == "length" else 0)
        episode = Episode(**values)
        if (
            episode.local_row_to - episode.local_row_from != episode.length
            or episode.global_row_to - episode.global_row_from != episode.length
        ):
            raise ValueError("mapping row intervals must be half-open and match length")
        if row.get("resolved_task_class", episode.task_class) != episode.task_class:
            raise ValueError(
                "task_class/resolved_task_class disagree; explicit source audit required"
            )
        local_id = (episode.task_class, episode.local_episode_index)
        if episode.global_episode_index in global_ids or local_id in local_ids:
            raise ValueError("mapping contains duplicate episode identities")
        global_ids.add(episode.global_episode_index)
        local_ids.add(local_id)
        episodes.append(episode)
    if not episodes:
        raise ValueError("empty episode mapping")
    intervals = [(e.global_row_from, e.global_row_to) for e in episodes]
    for name in sorted({e.task_class for e in episodes}):
        rows = sorted(
            (e.local_row_from, e.local_row_to) for e in episodes if e.task_class == name
        )
        if any(a[1] > b[0] for a, b in zip(rows, rows[1:])):
            raise ValueError("overlapping local row intervals")
    intervals.sort()
    if any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
        raise ValueError("overlapping global row intervals")
    return sorted(episodes, key=lambda e: (e.task_class, e.global_episode_index))


def select(
    episodes,
    *,
    manifest=None,
    task=None,
    global_episode=None,
    local_episode=None,
    task_shard=None,
    num_task_shards=None,
    episode_shard=None,
    num_episode_shards=None,
):
    for value in (global_episode, local_episode):
        if value is not None:
            integer(value, "explicit episode index")
    if (manifest is None) == (global_episode is None and local_episode is None):
        raise ValueError(
            "provide a selection manifest OR one explicit episode, never an implicit corpus"
        )
    if global_episode is not None and local_episode is not None:
        raise ValueError("global and local episode selectors are mutually exclusive")
    if local_episode is not None and task is None:
        raise ValueError("local episode requires its task class")
    records = {(e.task_class, e.global_episode_index): e for e in episodes}
    if manifest is not None:
        members, selection = selected_episodes(manifest)
        if members - records.keys():
            raise ValueError(
                "selection contains episodes absent from the authoritative mapping"
            )
        picked = [records[key] for key in sorted(members)]
    else:
        selection = None
        picked = [
            e
            for e in episodes
            if (global_episode is None or e.global_episode_index == global_episode)
            and (local_episode is None or e.local_episode_index == local_episode)
        ]
    if task is not None:
        task_name(task)
        picked = [e for e in picked if e.task_class == task]
    if not picked:
        raise ValueError("selection matched no mapped episode")
    if manifest is None and len(picked) != 1:
        raise ValueError("explicit episode selector must resolve uniquely")
    for shard, count, label in [
        (task_shard, num_task_shards, "task"),
        (episode_shard, num_episode_shards, "episode"),
    ]:
        if (shard is None) != (count is None):
            raise ValueError(f"both {label} shard/count are required")
        if count is not None:
            integer(count, "shard count", minimum=1)
            integer(shard, "shard")
            if shard >= count:
                raise ValueError("shard must be below its count")
    if task_shard is not None:
        names = sorted({e.task_class for e in picked})[task_shard::num_task_shards]
        picked = [e for e in picked if e.task_class in names]
    if episode_shard is not None:
        picked = picked[episode_shard::num_episode_shards]
    return picked, selection


def _rows(path, episode_index):
    import pyarrow.dataset as ds

    table = ds.dataset(path, format="parquet").to_table(
        columns=[
            "index",
            "episode_index",
            "frame_index",
            "observation.state",
            "timestamp",
            "__filename",
        ],
        filter=ds.field("episode_index") == episode_index,
    )
    if not len(table):
        raise ValueError("mapped episode has no source parquet rows")
    order = np.argsort(table["frame_index"].to_numpy(), kind="stable")
    values = {
        k: np.asarray(table[k].to_pylist())[order]
        for k in table.column_names
        if k != "observation.state"
    }
    values["observation.state"] = np.asarray(
        table["observation.state"].to_pylist(), dtype=np.float64
    )[order]
    return values


@dataclass
class SourceEpisode:
    episode: Episode
    dataset_dir: Path
    states: np.ndarray
    env_metadata: dict
    ep_meta: dict
    model_xml: str
    rgb: dict
    camera_shapes: dict
    witnesses: list
    alignment: dict
    flat_timestamps: np.ndarray


def load_episode(
    raw_root,
    flat_root,
    episode,
    cameras,
    *,
    state_index_policy=None,
    source_dataset=None,
    image_size=None,
):
    if state_index_policy != "frame_index":
        raise ValueError(
            "state/frame policy must be explicitly declared as frame_index and verified by DS"
        )
    raw_root, flat_root = Path(raw_root).resolve(), Path(flat_root).resolve()
    flat_info_path = flat_root / "meta/info.json"
    flat_info = read_json(flat_info_path)
    if not str(flat_info.get("codebase_version", "")).startswith("v3"):
        raise ValueError("Flat source must explicitly declare LeRobot v3")
    if not cameras or len(set(cameras)) != len(cameras) or set(cameras) - set(CAMERAS):
        raise ValueError("unsupported or duplicate source cameras")
    if source_dataset is not None:
        candidates = [Path(source_dataset).resolve()]
    elif (raw_root / "extras/dataset_meta.json").is_file():
        candidates = [raw_root]
    else:
        candidates = [
            p.parent.parent
            for p in (raw_root / episode.task_class).glob("**/extras/dataset_meta.json")
        ]
    candidates = [
        p
        for p in candidates
        if (
            p / f"extras/episode_{episode.local_episode_index:06d}/states.npz"
        ).is_file()
    ]
    if len(candidates) != 1:
        raise ValueError(
            "source dataset binding missing/ambiguous; provide --source-dataset explicitly"
        )
    dataset = candidates[0].resolve()
    if not dataset.is_relative_to(raw_root):
        raise ValueError("source dataset escapes raw-root")
    extra = dataset / f"extras/episode_{episode.local_episode_index:06d}"
    paths = [
        extra / "states.npz",
        extra / "model.xml.gz",
        extra / "ep_meta.json",
        dataset / "extras/dataset_meta.json",
        dataset / "meta/info.json",
    ]
    witnesses = [witness(p) for p in paths]
    witnesses.append(witness(flat_info_path))
    metadata, info = read_json(paths[3]), read_json(paths[4])
    env_metadata = metadata["env_args"]
    if env_metadata["env_name"] != episode.task_class:
        raise ValueError("source dataset env_name differs from mapped task")
    with np.load(paths[0], allow_pickle=False) as saved:
        states = np.asarray(saved["states"])
    if (
        states.ndim != 2
        or states.shape[0] != episode.length
        or not np.isfinite(states).all()
    ):
        raise ValueError(
            "states length/shape/finite check disagrees with episode mapping"
        )
    raw_rows = _rows(dataset / "data", episode.local_episode_index)
    flat_rows = _rows(flat_root / "data", episode.global_episode_index)
    for label, rows, start in [
        ("raw", raw_rows, episode.local_row_from),
        ("flat", flat_rows, episode.global_row_from),
    ]:
        if not np.issubdtype(
            rows["frame_index"].dtype, np.integer
        ) or not np.issubdtype(rows["index"].dtype, np.integer):
            raise ValueError(f"{label} frame/index columns must be integers")
        if not np.array_equal(
            rows["frame_index"], np.arange(episode.length)
        ) or not np.array_equal(rows["index"], start + np.arange(episode.length)):
            raise ValueError(f"{label} frame/index rows do not match episode intervals")
        if not np.isfinite(rows["timestamp"]).all():
            raise ValueError("non-finite source timestamp")
        for path in np.unique(rows["__filename"]):
            witnesses.append(witness(path, content=label == "raw"))
    if not np.array_equal(
        raw_rows["observation.state"], flat_rows["observation.state"]
    ):
        raise ValueError(
            "raw/Flat observation.state mismatch; refusing frame alignment"
        )
    with gzip.open(paths[1], "rt", encoding="utf-8") as stream:
        xml = stream.read(64 * 1024**2 + 1)
    if not xml or len(xml) > 64 * 1024**2:
        raise ValueError("model XML empty or exceeds 64 MiB")
    rgb, shapes = {}, {}
    for camera in cameras:
        key = "observation.images." + camera
        feature = info["features"][key]
        shape = feature["shape"]
        if len(shape) != 3 or shape[2] != 3:
            raise ValueError("source RGB feature must declare HxWx3")
        height, width = [integer(int(v), "camera size", minimum=1) for v in shape[:2]]
        if image_size is not None:
            size = integer(image_size, "image size", minimum=1)
            if (height, width) != (size, size):
                raise ValueError(
                    "requested image size differs from original RGB; implicit resampling is forbidden"
                )
        relative = info["video_path"].format(
            episode_chunk=episode.local_episode_index
            // integer(info["chunks_size"], "chunks_size", minimum=1),
            episode_index=episode.local_episode_index,
            video_key=key,
        )
        video = (dataset / relative).resolve()
        if not video.is_relative_to(dataset):
            raise ValueError("RGB video path escapes source dataset")
        proof = witness(video, content=False)
        witnesses.append(proof)
        rgb[camera] = {
            "video": str(video),
            "feature": key,
            "frame_index_policy": "mapped_local_frame_index_no_timestamp_shift",
            "witness": proof,
        }
        shapes[camera] = (height, width)
    verify_witnesses(witnesses)
    return SourceEpisode(
        episode,
        dataset,
        states,
        env_metadata,
        read_json(paths[2]),
        xml,
        rgb,
        shapes,
        witnesses,
        {
            "raw_flat_state_exact_equal": True,
            "frame_rows_verified": episode.length,
            "state_index_policy": "explicit_frame_index",
            "timestamp_shift_applied": False,
            "state_frame_physical_alignment": "PENDING_DS_GATE_B_C",
        },
        flat_rows["timestamp"].astype(np.float64),
    )
