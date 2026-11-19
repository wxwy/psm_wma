"""RoboCasa G2 DATA_B: owned episode-level 20Hz state15 cache, never per-frame files.

Source-of-truth is the original LeRobot flat Parquet and a fixed G1 verified
exact-window receipt. Writer and reader are independent of simulator and VAE.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
import tempfile
from io import BytesIO
from pathlib import Path

import torch

from g2.data.pose5 import Pose5Recipe, build_state15_from_current
from g2.io import parse_json


class DataBError(ValueError):
    pass


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def canonical(data: dict) -> str:
    return hashlib.sha256(
        json.dumps(
            data,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def json_load(path: Path):
    return json.loads(path.read_text())


def atomic_write_json(path: Path, obj: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", dir=path.parent, prefix=".g2-state-", delete=False
    ) as file:
        tmp = Path(file.name)
        json.dump(
            obj, file, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False
        )
        file.flush()
        os.fsync(file.fileno())
    try:
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def require_regular(path: Path):
    if path.is_symlink() or not path.is_file():
        raise DataBError(f"not an owned regular file: {path}")


def _stat_identity(info):
    if not stat.S_ISREG(info.st_mode):
        raise DataBError("expected an immutable regular file")
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def file_identity(path):
    path = Path(path).absolute()
    if path.resolve(strict=True) != path:
        raise DataBError(
            "artifact path traverses a symlink or a noncanonical component"
        )
    return _stat_identity(path.lstat())


def read_bound_bytes(path, *, limit, expected_sha256=None):
    """Hash the same bytes the consumer parses, and detect a racing replacement."""
    path = Path(path)
    token = file_identity(path)
    with os.fdopen(
        os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb"
    ) as file:
        if _stat_identity(os.fstat(file.fileno())) != token or token[2] > limit:
            raise DataBError("artifact changed or exceeds its byte limit")
        raw = file.read(token[2] + 1)
        if len(raw) != token[2] or _stat_identity(os.fstat(file.fileno())) != token:
            raise DataBError("artifact changed while reading")
    if file_identity(path) != token:
        raise DataBError("artifact replaced while reading")
    sha = hashlib.sha256(raw).hexdigest()
    if expected_sha256 is not None and sha != expected_sha256:
        raise DataBError(f"artifact SHA256 differs: {path.name}")
    return raw, sha, token


def read_bound_json(path, *, expected_sha256=None, limit=16 * 1024 * 1024):
    raw, sha, token = read_bound_bytes(
        path, limit=limit, expected_sha256=expected_sha256
    )
    value = parse_json(raw)
    if not isinstance(value, dict):
        raise DataBError("expected a JSON object")
    return value, sha, token


class VerifiedRawEpisodes:
    """One metadata map and bounded parquet cache, preserving native G1 identities."""

    def __init__(self, source_root, g1_index_root, g1_cache_root):
        self.source_root = Path(source_root)
        self.g1_cache_root = Path(g1_cache_root)
        self.index_root = Path(g1_index_root)
        self.receipt = json_load(self.index_root / "receipt.json")
        self.source_binding = self.receipt["source_binding_digest"]
        if self.receipt.get("schema") != "psm_v3_robocasa_verified_index_v1":
            raise DataBError("wrong exact-window source receipt")
        require_regular(self.g1_cache_root / "dataset_manifest.json")
        if (
            digest(self.g1_cache_root / "dataset_manifest.json")
            != self.receipt["cache_manifest_sha256"]
        ):
            raise DataBError("G1 exact-window cache manifest changed")
        self.by_episode = {}
        for item in self.receipt["bindings"]:
            ep = int(item["episode_index"])
            if ep in self.by_episode:
                raise DataBError("G1 source episode index duplicated")
            self.by_episode[ep] = item
        import pyarrow.parquet as pq

        meta = pq.read_table(
            self.source_root / "meta/episodes/chunk-000/file-000.parquet",
            columns=[
                "episode_index",
                "data/chunk_index",
                "data/file_index",
                "dataset_from_index",
                "dataset_to_index",
                "length",
                "tasks",
            ],
        )
        self.source_meta = {int(x["episode_index"]): x for x in meta.to_pylist()}
        task_table = pq.read_table(self.source_root / "meta/tasks.parquet").to_pylist()
        self.task_texts = {
            int(x["task_index"]): x["__index_level_0__"] for x in task_table
        }
        self.file_bases = {}
        for item in self.source_meta.values():
            name = (int(item["data/chunk_index"]), int(item["data/file_index"]))
            self.file_bases[name] = min(
                self.file_bases.get(name, item["dataset_from_index"]),
                item["dataset_from_index"],
            )
        self.file_stat = {r["path"]: r for r in self.receipt["files"]["source_data"]}
        self._loaded = {}

    def read(self, task_class: str, episode_index: int) -> dict:
        """Read a whole source episode, exactly ordered by original 20Hz frame_index."""
        item = self.by_episode[episode_index]
        if item["task_class"] != task_class:
            raise DataBError("task class differs from verified G1 binding")
        meta = self.source_meta[episode_index]
        for field in ("dataset_from_index", "dataset_to_index", "length"):
            if int(meta[field]) != int(item[field]):
                raise DataBError(f"original LeRobot {field} differs from G1 receipt")
        from_pos, to_pos = (
            int(item["dataset_from_index"]),
            int(item["dataset_to_index"]),
        )
        name = (int(meta["data/chunk_index"]), int(meta["data/file_index"]))
        relative = f"data/chunk-{name[0]:03d}/file-{name[1]:03d}.parquet"
        if item["data_file"] != relative:
            raise DataBError("original parquet path differs from G1 receipt")
        source = self.source_root / relative
        require_regular(source)
        stat = source.stat()
        witness = self.file_stat[relative]
        if stat.st_size != witness["size"] or stat.st_mtime_ns != witness["mtime_ns"]:
            raise DataBError("source parquet differs from the G1 verified witness")
        if name not in self._loaded:
            import pyarrow.parquet as pq

            self._loaded = {
                name: pq.read_table(
                    source,
                    columns=[
                        "episode_index",
                        "frame_index",
                        "timestamp",
                        "task_index",
                        "observation.state",
                        "action",
                    ],
                )
            }
        table = self._loaded[name]
        relative_start = from_pos - int(self.file_bases[name])
        rows = table.slice(relative_start, to_pos - from_pos).to_pylist()
        if len(rows) != item["length"]:
            raise DataBError("episode slice length mismatch")
        task_indices = set()
        for frame, row in enumerate(rows):
            if row["episode_index"] != episode_index or row["frame_index"] != frame:
                raise DataBError("original source frame/episode identity mismatch")
            if not math.isclose(float(row["timestamp"]), frame / 20, abs_tol=5e-5):
                raise DataBError("original episode not 20Hz")
            state = row["observation.state"]
            action = row["action"]
            if (
                len(state) != 16
                or len(action) != 12
                or not all(math.isfinite(float(n)) for n in (*state, *action))
            ):
                raise DataBError("original source state16/action12 is malformed")
            task_indices.add(row["task_index"])
        if len(task_indices) != 1:
            raise DataBError("atomic episode task identity switched")
        task_id = next(iter(task_indices))
        text = self.task_texts[task_id]
        if not isinstance(text, str) or not text:
            raise DataBError("missing original task text")
        return {
            "task_class": task_class,
            "episode_index": episode_index,
            "rows": rows,
            "instruction": text,
            "raw_source_path": str(source),
            "raw_source_file_stat": {k: witness[k] for k in ("size", "mtime_ns")},
            "source_binding_digest": self.source_binding,
            "source_range": [from_pos, to_pos],
            "source_frame_count": len(rows),
            "cache_manifest_sha256": self.receipt["cache_manifest_sha256"],
            "exact_window_count": item["window_count"],
        }


def episode_path(root, task_class: str, episode_index: int):
    if (
        not isinstance(task_class, str)
        or not task_class.isalnum()
        or type(episode_index) is not int
        or not 0 <= episode_index < 10_000_000
    ):
        raise DataBError("unsafe DATA_B task/episode path")
    return (
        Path(root) / "tasks" / task_class / "episodes" / f"episode_{episode_index:06d}"
    )


def build_episode_state(source: dict, recipe: Pose5Recipe) -> torch.Tensor:
    """A finite CPU FP32 [all original frames,15] cache, not only decision windows."""
    if type(recipe) is not Pose5Recipe:
        raise DataBError("explicit source-world recipe required")
    values = [
        build_state15_from_current(r["observation.state"], recipe=recipe)
        for r in source["rows"]
    ]
    out = torch.stack(values).contiguous()
    if out.dtype != torch.float32 or out.shape != (len(source["rows"]), 15):
        raise DataBError("state15 shape invalid")
    if not bool(torch.isfinite(out).all()):
        raise DataBError("state15 cache contains nonfinite values")
    return out


def write_episode_state(
    root, source: dict, *, recipe: Pose5Recipe, resume=True
) -> dict:
    dest = episode_path(root, source["task_class"], source["episode_index"])
    complete_path = dest / "COMPLETE.json"
    if complete_path.exists():
        if not resume:
            raise FileExistsError(complete_path)
        return verify_episode_state(root, source, expected_recipe=recipe.recipe_id)
    if dest.exists() and any(dest.iterdir()):
        raise DataBError("partial DATA_B output: refuse unsafe overwrite")
    dest.mkdir(parents=True, exist_ok=True)
    data = build_episode_state(source, recipe)
    metadata = {
        "schema": "g2_data_b_state15_episode_v1",
        "task_class": source["task_class"],
        "episode_index": source["episode_index"],
        "frame_count": len(data),
        "fps": 20,
        "start_frame": 0,
        "source_binding_digest": source["source_binding_digest"],
        "raw_source_path": source["raw_source_path"],
        "raw_source_file_stat": source["raw_source_file_stat"],
        "source_range": source["source_range"],
        "original_instruction": source["instruction"],
        "recipe_id": recipe.recipe_id,
        "recipe": recipe.__dict__,
        "state15_space": "data_b_model_input",
        "source_frame_reference": "source_base_world_not_wheeled_base",
        "training_ready": False,
    }
    target = dest / "state15.pt"
    with tempfile.NamedTemporaryFile(
        dir=dest, prefix=".g2-state-", suffix=".tmp", delete=False
    ) as file:
        tmp = Path(file.name)
        torch.save({"metadata": metadata, "state15": data}, file)
        file.flush()
        os.fsync(file.fileno())
    try:
        if target.exists():
            raise DataBError("refuse to overwrite existing state15.pt")
        os.replace(tmp, target)
    finally:
        tmp.unlink(missing_ok=True)
    marker = {
        "schema": "g2_data_b_complete_v1",
        "complete": True,
        "state15_sha256": digest(target),
        "episode_index": source["episode_index"],
        "task_class": source["task_class"],
        "recipe_id": recipe.recipe_id,
        "source_binding_digest": source["source_binding_digest"],
        "frame_count": len(data),
        "training_ready": False,
    }
    atomic_write_json(complete_path, marker)
    return verify_episode_state(root, source, expected_recipe=recipe.recipe_id)


def read_episode_state(
    dest,
    *,
    task,
    episode,
    frame_count,
    source_binding_digest,
    recipe_id,
    expected_sha256=None,
):
    """Read a sealed DATA_B tensor with its embedded source metadata."""
    expected = dict(
        task_class=task,
        episode_index=episode,
        frame_count=frame_count,
        source_binding_digest=source_binding_digest,
        recipe_id=recipe_id,
        training_ready=False,
    )
    marker, _, _ = read_bound_json(dest / "COMPLETE.json")
    if (
        marker.get("schema") != "g2_data_b_complete_v1"
        or marker.get("complete") is not True
        or any(marker.get(k) != v for k, v in expected.items())
        or not isinstance(marker.get("state15_sha256"), str)
        or (expected_sha256 is not None and marker["state15_sha256"] != expected_sha256)
    ):
        raise DataBError("DATA_B completion/source/recipe or SHA mismatch")
    raw, sha, _ = read_bound_bytes(
        dest / "state15.pt",
        limit=64 * 1024**2,
        expected_sha256=marker["state15_sha256"],
    )
    obj = torch.load(BytesIO(raw), map_location="cpu", weights_only=True)
    if not isinstance(obj, dict) or set(obj) != {"metadata", "state15"}:
        raise DataBError("DATA_B file envelope invalid")
    meta, states = obj["metadata"], obj["state15"]
    if (
        any(meta.get(k) != v for k, v in expected.items())
        or meta.get("schema") != "g2_data_b_state15_episode_v1"
        or meta.get("fps") != 20
        or meta.get("start_frame") != 0
        or meta.get("state15_space") != "data_b_model_input"
        or meta.get("source_frame_reference") != "source_base_world_not_wheeled_base"
    ):
        raise DataBError("DATA_B embedded provenance differs")
    if (
        not isinstance(states, torch.Tensor)
        or states.shape != (frame_count, 15)
        or states.dtype != torch.float32
        or not bool(torch.isfinite(states).all())
    ):
        raise DataBError("DATA_B tensor failed shape/dtype/finite checks")
    return states, meta, sha


def verify_episode_state(root, source: dict, *, expected_recipe: str) -> dict:
    """Strict source-bound offline check."""
    dest = episode_path(root, source["task_class"], source["episode_index"])
    _, meta, sha = read_episode_state(
        dest,
        task=source["task_class"],
        episode=source["episode_index"],
        frame_count=source["source_frame_count"],
        source_binding_digest=source["source_binding_digest"],
        recipe_id=expected_recipe,
    )
    if (
        meta["source_range"] != source["source_range"]
        or meta["original_instruction"] != source["instruction"]
        or meta["raw_source_file_stat"] != source["raw_source_file_stat"]
    ):
        raise DataBError("DATA_B embedded provenance differs")
    return {
        "episode_root": str(dest),
        "state15_path": str(dest / "state15.pt"),
        "state15_sha256": sha,
        "recipe_id": meta["recipe_id"],
        "source_binding_digest": meta["source_binding_digest"],
        "frame_count": meta["frame_count"],
    }
