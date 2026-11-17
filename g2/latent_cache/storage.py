"""Atomic per-View tensors and an explicitly bounded, CPU-only lazy reader.

Importing this module and opening an episode index do not import torch. Numeric
files are mapped only for requested Views. Full-file/whole-history checks belong
to the offline inspector; ordinary reads verify only the selected tensor row.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import tempfile
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from g2.io import digest, read_json

from .contract import (
    COMPLETE_SCHEMA,
    INDEX_SCHEMA,
    PAYLOAD_SCHEMA,
    CacheError,
    contained,
    fingerprint,
    safe_relative,
    validate_recipe,
)

_DTYPES = {"float32", "float16", "bfloat16"}
_JSON_LIMIT = 16 * 1024 * 1024


def _hex(value):
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(x not in "0123456789abcdef" for x in value)
    ):
        raise CacheError("invalid cache SHA256")
    return value


def _integer(value, name, *, positive=False):
    if type(value) is not int or value < int(positive):
        raise CacheError("invalid " + name)
    return value


def _absolute(path):
    path = Path(path).absolute()
    for item in [*reversed(path.parents), path]:
        if item.is_symlink():
            raise CacheError("symlink is forbidden in cache path: " + str(item))
    return path


def _view_id(value):
    path = Path(safe_relative(value))
    if (
        path.parts[0] not in ("sixview", "islands")
        or path.suffix
        or len(path.parts) < (3 if path.parts[0] == "islands" else 2)
    ):
        raise CacheError("invalid logical View ID")
    return path.as_posix()


def _fsync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


@contextmanager
def build_lock(cache_root):
    """Reject another writer without replacing or unlinking its lock inode."""
    root = _absolute(cache_root)
    root.mkdir(parents=True, exist_ok=True)
    if not root.is_dir():
        raise CacheError("cache root must be a directory")
    try:
        fd = os.open(
            root / ".build.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
        )
    except OSError as exc:
        raise CacheError("cannot safely open cache build lock") from exc
    locked = False
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            locked = True
        except BlockingIOError as exc:
            raise CacheError("another builder holds this cache target") from exc
        yield root
    finally:
        if locked:
            fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def atomic_json(path, value, *, replace=False):
    """Publish a cache-owned JSON file; never follow a symlink or clobber by default."""
    path = _absolute(path)
    data = (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".json-", suffix=".tmp", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        _absolute(path)
        if replace:
            if path.exists() and not path.is_file():
                raise CacheError("refuse non-file cache JSON target")
            os.replace(temp, path)
        else:
            try:
                os.link(temp, path)
            except FileExistsError as exc:
                raise CacheError("cache JSON target already exists") from exc
        _fsync_directory(path.parent)
    finally:
        temp.unlink(missing_ok=True)


def tensor_sha256(tensor):
    """Hash only the supplied CPU tensor, including BF16 without a dtype cast."""
    import torch

    if type(tensor) is not torch.Tensor or tensor.device.type != "cpu":
        raise CacheError("latent record must be a plain CPU tensor")
    data = tensor.detach().contiguous().view(torch.uint8).numpy().tobytes()
    return hashlib.sha256(data).hexdigest()


def _metadata(metadata, count):
    if not isinstance(metadata, dict) or metadata.get("schema") != PAYLOAD_SCHEMA:
        raise CacheError("wrong per-View payload schema")
    if not isinstance(metadata.get("episode_key"), str) or not metadata["episode_key"]:
        raise CacheError("missing episode identity")
    _hex(metadata.get("recipe_id"))
    source = metadata.get("source")
    if not isinstance(source, dict):
        raise CacheError("missing source identity")
    _hex(source.get("manifest_sha256"))
    _hex(source.get("complete_sha256"))
    view = _view_id(metadata.get("view_id"))
    plan = metadata.get("view_plan")
    if not isinstance(plan, dict) or plan.get("path") != view + ".pt":
        raise CacheError("payload View path does not match its identity")
    records = plan.get("records")
    preprocessing = metadata.get("preprocessing")
    if (
        not isinstance(records, list)
        or len(records) != count
        or not isinstance(preprocessing, list)
        or len(preprocessing) != count
        or any(not isinstance(x, dict) for x in preprocessing)
    ):
        raise CacheError("record/preprocessing count differs from tensor history")
    previous = -1
    for index, record in enumerate(records):
        if (
            not isinstance(record, dict)
            or type(record.get("record_index")) is not int
            or record["record_index"] != index
        ):
            raise CacheError("invalid physical record order")
        owner = _integer(record.get("owner_state_ordinal"), "owner ordinal")
        if owner <= previous:
            raise CacheError("duplicate or unordered physical owner")
        previous = owner
        _integer(record.get("owner_state_id"), "owner logical state")
        _integer(record.get("owner_frame"), "owner frame")
        safe_relative(record.get("png_path"), suffix=".png")
        _hex(record.get("png_sha256"))
    mapping = plan.get("state_records")
    if not isinstance(mapping, list) or not mapping:
        raise CacheError("missing logical-state mapping")
    for logical_ordinal, index in enumerate(mapping):
        if index is not None and (type(index) is not int or not 0 <= index < count):
            raise CacheError("record index outside payload history")
        if (
            index is not None
            and records[index]["owner_state_ordinal"] > logical_ordinal
        ):
            raise CacheError("future physical owner in logical-state mapping")
    if {x for x in mapping if x is not None} != set(range(count)):
        raise CacheError("payload history is not completely covered")
    for index, record in enumerate(records):
        owner = record["owner_state_ordinal"]
        if owner >= len(mapping) or mapping[owner] != index:
            raise CacheError("physical owner does not own its logical-state record")
    fingerprint(metadata)  # Also reject non-JSON/non-finite metadata.


def _tensor_header(tensor):
    import torch

    if (
        type(tensor) is not torch.Tensor
        or tensor.device.type != "cpu"
        or tensor.layout != torch.strided
        or tensor.ndim != 4
        or any(n <= 0 for n in tensor.shape)
        or not tensor.is_contiguous()
    ):
        raise CacheError("payload latent layout must be contiguous CPU UCHW")
    dtype = str(tensor.dtype).removeprefix("torch.")
    if dtype not in _DTYPES:
        raise CacheError("unsupported latent storage dtype")
    if (
        tensor.storage_offset() != 0
        or tensor.untyped_storage().nbytes() != tensor.numel() * tensor.element_size()
    ):
        raise CacheError("latent storage contains hidden tensor history")
    return list(tensor.shape), dtype


def _load(path, *, mmap=True):
    import torch

    try:
        value = torch.load(str(path), map_location="cpu", weights_only=True, mmap=mmap)
    except Exception as exc:
        raise CacheError(
            "cannot load safe per-View numeric payload: " + str(path)
        ) from exc
    if not isinstance(value, dict) or set(value) != {
        "metadata",
        "latents",
        "record_sha256",
    }:
        raise CacheError("invalid per-View payload envelope")
    tensor = value["latents"]
    shape, dtype = _tensor_header(tensor)
    _metadata(value["metadata"], shape[0])
    hashes = value["record_sha256"]
    if not isinstance(hashes, list) or len(hashes) != shape[0]:
        raise CacheError("wrong per-record checksum count")
    for item in hashes:
        _hex(item)
    return value, shape, dtype


def inspect_view_payload(path, expected_metadata=None, *, full=True):
    """Offline audit; may inspect every version and hash the whole numeric file."""
    import torch

    path = _absolute(path)
    if not path.is_file():
        raise CacheError("per-View payload missing")
    before = _stat(path)
    value, shape, dtype = _load(path)
    if expected_metadata is not None and value["metadata"] != expected_metadata:
        raise CacheError("payload recipe/source/View identity mismatch")
    if full:
        for index, expected in enumerate(value["record_sha256"]):
            row = value["latents"][index]
            if not torch.isfinite(row).all() or tensor_sha256(row) != expected:
                raise CacheError("latent record is damaged or non-finite")
    file_hash = digest(path)
    if _stat(path) != before:
        raise CacheError("per-View payload changed during audit")
    return {
        "path": path.name,
        "sha256": file_hash,
        "bytes": before[2],
        "shape": shape,
        "dtype": dtype,
        "metadata": value["metadata"],
        "metadata_sha256": fingerprint(value["metadata"]),
        "record_sha256": value["record_sha256"],
    }


def write_view_payload(path, metadata, latents):
    """Validate then atomically publish one immutable View, without overwrite."""
    import torch

    path = _absolute(path)
    if path.suffix != ".pt" or path.exists():
        raise CacheError("per-View target must be a new .pt file")
    if type(latents) is not torch.Tensor or latents.device.type != "cpu":
        raise CacheError("writer accepts only plain CPU tensors")
    tensor = latents.detach().contiguous()
    if (
        tensor.storage_offset() != 0
        or tensor.untyped_storage().nbytes() != tensor.numel() * tensor.element_size()
    ):
        tensor = tensor.clone()
    shape, _ = _tensor_header(tensor)
    _metadata(metadata, shape[0])
    if not torch.isfinite(tensor).all():
        raise CacheError("refuse non-finite latent tensor")
    value = {
        "metadata": metadata,
        "latents": tensor,
        "record_sha256": [tensor_sha256(row) for row in tensor],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".view-", suffix=".tmp", dir=path.parent)
    temp = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            torch.save(value, stream)
            stream.flush()
            os.fsync(stream.fileno())
        result = inspect_view_payload(temp, metadata)
        _absolute(path)
        try:
            os.link(temp, path)
        except FileExistsError as exc:
            raise CacheError("per-View target was concurrently published") from exc
        _fsync_directory(path.parent)
        result["path"] = path.name
        return result
    finally:
        temp.unlink(missing_ok=True)


def _stat(path):
    try:
        status = path.stat()
    except OSError as exc:
        raise CacheError("cache payload is unavailable") from exc
    return status.st_dev, status.st_ino, status.st_size, status.st_mtime_ns


@dataclass(frozen=True)
class EpisodeIndex:
    episode_root: Path
    cache_root: Path
    manifest: dict
    states_by_id: dict

    @property
    def episode_key(self):
        return self.manifest["episode_key"]

    @property
    def recipe_id(self):
        return self.manifest["recipe"]["recipe_id"]


def validate_payload_binding(index, view_id, entry, info):
    """Match already-loaded payload headers to the sealed episode index.

    This is deliberately independent from original-PNG auditing. It neither
    opens files nor materializes tensor history, and applies equally to lazy
    selected-View reads and offline verification with source auditing disabled.
    File checksums/sizes are compared when an offline inspector supplies them;
    a lazy reader supplies only metadata, shape, dtype and record checksums.
    """
    if not isinstance(index, EpisodeIndex):
        raise CacheError("payload binding requires an opened episode index")
    view_id = _view_id(view_id)
    if (
        not isinstance(entry, dict)
        or index.manifest["views"].get(view_id) != entry
        or not isinstance(info, dict)
    ):
        raise CacheError("payload binding requires the indexed View entry")
    metadata, shape = info.get("metadata"), info.get("shape")
    if (
        not isinstance(metadata, dict)
        or not isinstance(shape, list)
        or len(shape) != 4
        or shape != entry["shape"]
    ):
        raise CacheError("selected payload identity/header differs from index")
    for dimension in shape:
        _integer(dimension, "latent dimension", positive=True)
    _metadata(metadata, shape[0])
    if (
        info.get("dtype") != entry["dtype"]
        or fingerprint(metadata) != entry["metadata_sha256"]
        or info.get("record_sha256") != entry["record_sha256"]
        or metadata["episode_key"] != index.episode_key
        or metadata["recipe_id"] != index.recipe_id
        or metadata["source"] != index.manifest["source"]
        or metadata["view_id"] != view_id
        or metadata["view_plan"]["state_records"] != entry["state_records"]
        or metadata["view_plan"]["path"] != entry["path"]
        or ("sha256" in info and info["sha256"] != entry["sha256"])
        or ("bytes" in info and info["bytes"] != entry["bytes"])
    ):
        raise CacheError("selected payload identity/header differs from index")
    states = index.manifest["states"]
    if (
        "states" in metadata and fingerprint(metadata["states"]) != fingerprint(states)
    ) or (
        "episode" in metadata
        and fingerprint(metadata["episode"])
        != fingerprint(index.manifest.get("episode"))
    ):
        raise CacheError("payload episode/logical-state identity differs from index")
    recipe_prep = index.manifest["recipe"]["preprocessing"]
    canvas_hw = [recipe_prep["height"], recipe_prep["width"]]
    for record, prep in zip(
        metadata["view_plan"]["records"], metadata["preprocessing"], strict=True
    ):
        actual_canvas = prep.get("canvas_hw")
        original_hw = record.get("original_hw")
        if (
            not isinstance(actual_canvas, list)
            or len(actual_canvas) != 2
            or any(type(n) is not int or n <= 0 for n in actual_canvas)
            or actual_canvas != canvas_hw
        ):
            raise CacheError("payload preprocessing canvas differs from sealed recipe")
        if (
            not isinstance(original_hw, list)
            or len(original_hw) != 2
            or any(type(n) is not int or n <= 0 for n in original_hw)
            or fingerprint(prep.get("original_hw")) != fingerprint(original_hw)
        ):
            raise CacheError(
                "payload preprocessing original dimensions differ from owner"
            )
        ordinal = record["owner_state_ordinal"]
        if (
            ordinal >= len(states)
            or states[ordinal]["logical_state_id"] != record["owner_state_id"]
            or states[ordinal]["frame"] != record["owner_frame"]
        ):
            raise CacheError("physical owner identity differs from source index")
        expected_png = (
            f"state_{ordinal:06d}_frame_{record['owner_frame']:06d}/{view_id}.png"
        )
        allowed_pngs = {expected_png}
        if index.manifest["source"].get("schema") == "g2_sealed_spatial_source_v1":
            allowed_pngs.add(f"_spatial_inputs/{ordinal}/{view_id}.png")
        if record["png_path"] not in allowed_pngs:
            raise CacheError("physical PNG path differs from canonical View owner")
    return True


def open_episode_index(episode_root, expected_recipe_id=None):
    """Read only the small source/cache JSON index, not any numeric View file."""
    root = _absolute(episode_root)
    cache = Path(contained(root, "vae_cache"))
    try:
        manifest_path = Path(contained(cache, "manifest.json"))
        marker_path = Path(contained(cache, "COMPLETE.json"))
        manifest = read_json(manifest_path, limit=_JSON_LIMIT)
        complete = read_json(marker_path, limit=_JSON_LIMIT)
    except (OSError, ValueError, TypeError) as exc:
        raise CacheError("complete cache index is missing or invalid") from exc
    if not isinstance(manifest, dict) or manifest.get("schema") != INDEX_SCHEMA:
        raise CacheError("wrong cache index schema")
    if (
        not isinstance(complete, dict)
        or complete.get("schema") != COMPLETE_SCHEMA
        or complete.get("complete") is not True
        or complete.get("manifest_sha256") != digest(manifest_path)
    ):
        raise CacheError("cache completion does not bind its index")
    key = manifest.get("episode_key")
    if not isinstance(key, str) or not key or complete.get("episode_key") != key:
        raise CacheError("cache episode identity differs")
    recipe = manifest.get("recipe")
    if not isinstance(recipe, dict):
        raise CacheError("missing cache recipe")
    validate_recipe(recipe)
    recipe_id = _hex(recipe.get("recipe_id"))
    if (
        recipe_id != fingerprint({k: v for k, v in recipe.items() if k != "recipe_id"})
        or complete.get("recipe_id") != recipe_id
        or (expected_recipe_id is not None and expected_recipe_id != recipe_id)
    ):
        raise CacheError("cache recipe identity differs")
    source = manifest.get("source")
    if not isinstance(source, dict):
        raise CacheError("missing cache source identity")
    # New profiles bind immutable spatial readiness, before final profile
    # publication. Keep the legacy file pair strict; this JSON-only dispatch
    # does not import a renderer, scanner or VAE in training readers.
    if source.get("schema") == "g2_sealed_spatial_source_v1":
        if (
            source.get("identity_manifest") != "spatial_source.json"
            or source.get("readiness_marker") != "SPATIAL_SOURCE_READY.json"
        ):
            raise CacheError("unknown sealed-source identity files")
        source_files = [
            ("manifest_sha256", "spatial_source.json"),
            ("complete_sha256", "SPATIAL_SOURCE_READY.json"),
        ]
    else:
        source_files = [
            ("manifest_sha256", "episode_manifest.json"),
            ("complete_sha256", "COMPLETE.json"),
        ]
    for name, filename in source_files:
        expected = _hex(source.get(name))
        try:
            if digest(contained(root, filename)) != expected:
                raise CacheError("source identity differs from cache")
        except OSError as exc:
            raise CacheError("source identity is unavailable") from exc
    states = manifest.get("states")
    if not isinstance(states, list) or not states:
        raise CacheError("missing cache logical states")
    by_id = {}
    previous_frame = -1
    for ordinal, state in enumerate(states):
        if (
            not isinstance(state, dict)
            or type(state.get("state_ordinal")) is not int
            or state["state_ordinal"] != ordinal
        ):
            raise CacheError("invalid cache state ordinal")
        logical = _integer(state.get("logical_state_id"), "logical state")
        frame = _integer(state.get("frame"), "logical frame")
        if logical in by_id or frame <= previous_frame:
            raise CacheError("duplicate state or unordered frame")
        by_id[logical] = state
        previous_frame = frame
    views = manifest.get("views")
    if not isinstance(views, dict):
        raise CacheError("missing cache View directory")
    for view_id, record in views.items():
        view_id = _view_id(view_id)
        if not isinstance(record, dict) or record.get("path") != view_id + ".pt":
            raise CacheError("View path is not identity-bound")
        shape = record.get("shape")
        if (
            not isinstance(shape, list)
            or len(shape) != 4
            or any(type(x) is not int or x < 1 for x in shape)
            or record.get("dtype") not in _DTYPES
            or (
                "storage_dtype" in recipe and recipe["storage_dtype"] != record["dtype"]
            )
        ):
            raise CacheError("invalid cache View shape/dtype")
        _integer(record.get("bytes"), "payload byte size", positive=True)
        _hex(record.get("sha256"))
        _hex(record.get("metadata_sha256"))
        hashes = record.get("record_sha256")
        mapping = record.get("state_records")
        if (
            not isinstance(hashes, list)
            or len(hashes) != shape[0]
            or not isinstance(mapping, list)
            or len(mapping) != len(states)
        ):
            raise CacheError("cache record/mapping coverage differs")
        for checksum in hashes:
            _hex(checksum)
        for index in mapping:
            if index is not None and (
                type(index) is not int or not 0 <= index < shape[0]
            ):
                raise CacheError("cache record mapping out of bounds")
        if {x for x in mapping if x is not None} != set(range(shape[0])):
            raise CacheError("cache View has uncovered records")
    return EpisodeIndex(root, cache, manifest, by_id)


class ViewReader:
    """Own at most max_views/max_bytes mappings; return only a selected-row copy.

    Eviction drops the reader's mapping reference. Selected CHW copies belong
    to the caller and cannot poison cached mmap data through in-place mutation.
    """

    def __init__(self, index, *, max_views=4, max_bytes=256 * 1024 * 1024, mmap=True):
        if not isinstance(index, EpisodeIndex):
            raise CacheError("reader requires an opened episode index")
        _integer(max_views, "max_views", positive=True)
        _integer(max_bytes, "max_bytes", positive=True)
        if type(mmap) is not bool:
            raise CacheError("mmap must be boolean")
        self.index = index
        self.max_views = max_views
        self.max_bytes = max_bytes
        self.mmap = mmap
        self._cache = OrderedDict()
        self.cached_bytes = 0

    @property
    def cached_views(self):
        return tuple(self._cache)

    def close(self):
        self._cache.clear()
        self.cached_bytes = 0

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()

    def _payload(self, view_id, entry):
        path = Path(contained(self.index.cache_root, entry["path"]))
        token = _stat(path)
        if token[2] != entry["bytes"]:
            raise CacheError("selected payload byte size changed")
        if view_id in self._cache:
            item = self._cache[view_id]
            if item["stat"] != token:
                raise CacheError("selected payload changed after mapping")
            self._cache.move_to_end(view_id)
            return item
        if entry["bytes"] > self.max_bytes:
            raise CacheError("selected View exceeds reader byte budget")
        while self._cache and (
            len(self._cache) >= self.max_views
            or self.cached_bytes + entry["bytes"] > self.max_bytes
        ):
            _, removed = self._cache.popitem(last=False)
            self.cached_bytes -= removed["bytes"]
        value, shape, dtype = _load(path, mmap=self.mmap)
        validate_payload_binding(
            self.index,
            view_id,
            entry,
            {
                "metadata": value["metadata"],
                "shape": shape,
                "dtype": dtype,
                "record_sha256": value["record_sha256"],
            },
        )
        if _stat(path) != token:
            raise CacheError("selected payload changed while loading")
        item = {
            "value": value,
            "stat": token,
            "verified": set(),
            "bytes": entry["bytes"],
        }
        self._cache[view_id] = item
        self.cached_bytes += entry["bytes"]
        return item

    def read_view(self, view_id, logical_state_id):
        view_id = _view_id(view_id)
        if (
            type(logical_state_id) is not int
            or logical_state_id not in self.index.states_by_id
        ):
            raise CacheError("unknown logical state")
        state = self.index.states_by_id[logical_state_id]
        result = {
            "episode_key": self.index.episode_key,
            "view_id": view_id,
            "logical_state_id": logical_state_id,
            "logical_frame": state["frame"],
            "state_ordinal": state["state_ordinal"],
            "present": False,
            "latent": None,
            "owner": None,
            "preprocessing": None,
        }
        entry = self.index.manifest["views"].get(view_id)
        if entry is None:
            return result
        record_index = entry["state_records"][state["state_ordinal"]]
        if record_index is None:
            return result
        import torch

        item = self._payload(view_id, entry)
        value = item["value"]
        record = value["metadata"]["view_plan"]["records"][record_index]
        if record["owner_state_ordinal"] > state["state_ordinal"]:
            raise CacheError("future physical owner cannot serve current state")
        row = value["latents"][record_index]
        if record_index not in item["verified"]:
            if (
                not torch.isfinite(row).all()
                or tensor_sha256(row) != entry["record_sha256"][record_index]
            ):
                raise CacheError("selected latent record is damaged or non-finite")
            item["verified"].add(record_index)
        result.update(
            present=True,
            latent=row.clone(),
            record_index=record_index,
            owner=copy.deepcopy(record),
            preprocessing=copy.deepcopy(
                value["metadata"]["preprocessing"][record_index]
            ),
        )
        return result

    def read_many(self, logical_state_id, selected_view_ids):
        if (
            type(logical_state_id) is not int
            or logical_state_id not in self.index.states_by_id
        ):
            raise CacheError("unknown logical state")
        if not isinstance(selected_view_ids, (list, tuple)):
            raise CacheError("selected Views require an ordered list or tuple")
        selected = {}
        result = []
        for view in selected_view_ids:
            view = _view_id(view)
            if view not in selected:
                selected[view] = self.read_view(view, logical_state_id)
            result.append(selected[view])
        return result
