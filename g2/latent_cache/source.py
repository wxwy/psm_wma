"""Read the existing G2 image index without loading or reconstructing a scene.

This module validates the completed manifest and its physical PNG ownership
index. It does not recertify SG geometry, material provenance, or training
readiness. The original G2 package validators remain the authority for those
contracts. Only builders/auditors import this module; numerical cache readers
do not import the offline producer or this resolver.
"""

from __future__ import annotations

import hashlib
import warnings
from io import BytesIO
from pathlib import Path, PurePosixPath

from PIL import Image

from g2.io import ContractError, parse_json, sha
from g2.offline.scene_view_event_index import resolve_indexed_png, validate_view_path

SCHEMAS = frozenset("g2_atomic_compact_6views_v" + str(i) for i in (1, 2, 3))
_JSON_LIMIT = 128 * 1024 * 1024


def _hash(payload):
    return hashlib.sha256(payload).hexdigest()


def _root(path):
    root = Path(path).absolute()
    # Do not erase evidence of a symlink by resolving it before inspection.
    for component in (root, *root.parents):
        if component.is_symlink():
            raise ContractError("symlink in episode root: " + str(component))
    if not root.is_dir():
        raise ContractError("episode root is not a directory")
    return root.resolve(strict=True)


def _safe_path(root, relative, *, directory=False, optional=False):
    if not isinstance(relative, str):
        raise ContractError("unsafe episode-relative path")
    path = PurePosixPath(relative)
    if (
        not relative
        or "\\" in relative
        or any(ord(c) < 32 or ord(c) == 127 for c in relative)
        or path.is_absolute()
        or ".." in path.parts
        or str(path) != relative
    ):
        raise ContractError("unsafe episode-relative path")
    full = root
    for part in path.parts:
        full = full / part
        if full.is_symlink():
            raise ContractError("symlink in source path: " + str(full))
    exists = full.exists()
    if optional and not exists:
        return full
    valid = full.is_dir() if directory else full.is_file()
    if not valid:
        raise ContractError("missing or invalid source path: " + str(full))
    if root not in full.resolve(strict=True).parents:
        raise ContractError("source path escapes episode")
    return full


def _json(root, name):
    path = _safe_path(root, name)
    if path.stat().st_size > _JSON_LIMIT:
        raise ContractError("source JSON exceeds byte limit")
    raw = path.read_bytes()
    if len(raw) > _JSON_LIMIT:
        raise ContractError("source JSON exceeds byte limit")
    obj = parse_json(raw.decode("utf-8"))
    if not isinstance(obj, dict):
        raise ContractError("source JSON must be an object")
    return obj, _hash(raw)


def _inventory(row, schema):
    files, refs = row.get("view_pngs"), row.get("view_refs", {})
    if not isinstance(files, list) or not isinstance(refs, dict):
        raise ContractError("invalid physical/reference view inventory")
    if schema.endswith("v1") and refs:
        raise ContractError("v1 package cannot contain indexed PNG references")
    if not schema.endswith("v1") and "view_refs" not in row:
        raise ContractError("indexed package must provide view_refs")
    for path in (*files, *refs):
        if (
            not isinstance(path, str)
            or "\\" in path
            or any(ord(c) < 32 or ord(c) == 127 for c in path)
            or validate_view_path(path) != path
        ):
            raise ContractError("unsafe or noncanonical view path")
    if len(files) != len(set(files)) or set(files) & set(refs):
        raise ContractError("duplicate physical/indexed PNG")
    return files, refs


def _png(root, relative):
    path = _safe_path(root, relative)
    raw = path.read_bytes()
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format != "PNG" or image.mode != "RGB":
                    raise ContractError("source must be a uint8 RGB PNG")
                width, height = image.size
                image.verify()
            # verify() checks the container; load() also checks decoded data.
            with Image.open(BytesIO(raw)) as image:
                image.load()
    except (
        OSError,
        ValueError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as error:
        raise ContractError("unreadable RGB PNG: " + relative) from error
    return _hash(raw), [height, width]


def scan_episode(episode_root):
    """Plan all declared views, hashing each physical owner exactly once.

    ``ref_state`` stays an ordinal into the original manifest. Optional sparse
    ``state_id`` values are retained as logical identities, never substituted
    for physical owner ordinals or for original source frame numbers.
    """
    root = _root(episode_root)
    doc, manifest_sha = _json(root, "episode_manifest.json")
    complete, complete_sha = _json(root, "COMPLETE.json")
    rows, schema = doc.get("states"), doc.get("schema")
    eid, task = doc.get("episode_id"), doc.get("task_class")
    if (
        not isinstance(schema, str)
        or schema not in SCHEMAS
        or complete.get("schema") != schema
        or doc.get("complete") is not True
        or complete.get("complete") is not True
        or doc.get("training_ready") is not False
        or complete.get("training_ready", False) is not False
        or doc.get("source_renderer") != "f27"
        or complete.get("renderer") != "f27"
        or type(eid) is not int
        or eid < 0
        or type(complete.get("episode_id")) is not int
        or complete.get("episode_id") != eid
        or not isinstance(task, str)
        or not task
        or task in (".", "..")
        or any(c in task for c in ("/", "\\"))
        or any(ord(c) < 32 or ord(c) == 127 for c in task)
        or not isinstance(rows, list)
        or not rows
        or type(doc.get("state_count")) is not int
        or doc["state_count"] != len(rows)
        or type(complete.get("state_count")) is not int
        or complete["state_count"] != len(rows)
        or complete.get("episode_manifest_sha256") != manifest_sha
        or complete.get("source_fingerprint") != doc.get("source_fingerprint")
    ):
        raise ContractError("invalid completed source episode identity")
    if doc.get("source_fingerprint") is not None:
        sha(doc["source_fingerprint"], "source_fingerprint")

    states, inventories = [], []
    logical_ids, previous_frame = set(), -1
    for ordinal, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ContractError("invalid source state")
        frame, logical = row.get("frame"), row.get("state_id", ordinal)
        if (
            type(frame) is not int
            or frame <= previous_frame
            or type(logical) is not int
            or logical < 0
            or logical in logical_ids
        ):
            raise ContractError(
                "invalid source frame/logical-state ordering or identity"
            )
        previous_frame = frame
        logical_ids.add(logical)
        states.append(
            {"state_ordinal": ordinal, "logical_state_id": logical, "frame": frame}
        )
        inventories.append(_inventory(row, schema))
        _safe_path(
            root,
            f"state_{ordinal:06d}_frame_{frame:06d}",
            directory=True,
            optional=True,
        )

    all_paths = sorted({p for files, refs in inventories for p in (*files, *refs)})
    views, aliases = {}, set()
    for path in all_paths:
        view_id = str(PurePosixPath(path).with_suffix(""))
        if view_id in aliases:
            raise ContractError("different PNG paths alias one logical view")
        aliases.add(view_id)
        records, owner_records, indices = [], {}, []
        for ordinal, (files, refs) in enumerate(inventories):
            if path not in files and path not in refs:
                indices.append(None)
                continue
            try:
                resolved = resolve_indexed_png(rows, ordinal, path, root)
            except (ValueError, KeyError, IndexError, OSError) as error:
                raise ContractError("invalid direct PNG owner/reference") from error
            owner = ordinal if path in files else refs[path]["ref_state"]
            if owner not in owner_records:
                relative = resolved.relative_to(root).as_posix()
                png_sha, hw = _png(root, relative)
                record_index = len(records)
                records.append(
                    {
                        "record_index": record_index,
                        "owner_state_ordinal": owner,
                        "owner_state_id": states[owner]["logical_state_id"],
                        "owner_frame": states[owner]["frame"],
                        "png_path": relative,
                        "png_sha256": png_sha,
                        "original_hw": hw,
                        "color_mode": "RGB",
                    }
                )
                owner_records[owner] = record_index
            indices.append(owner_records[owner])
        views[view_id] = {
            "path": view_id + ".pt",
            "records": records,
            "state_records": indices,
            "spatial_metadata": {
                "status": "NOT_IN_IMAGE_INDEX",
                "world_origin": None,
                "robot_pose": None,
            },
        }

    # Manifest changes during planning must not yield a mixed source identity.
    if (
        _json(root, "episode_manifest.json")[1] != manifest_sha
        or _json(root, "COMPLETE.json")[1] != complete_sha
    ):
        raise ContractError("source manifest changed during planning")
    return {
        "episode_root": str(root),
        "episode_key": f"{task}/episode_{eid:06d}",
        "episode": {"task_class": task, "episode_id": eid},
        "source": {
            "manifest_sha256": manifest_sha,
            "complete_sha256": complete_sha,
            "schema": schema,
            "validation_scope": "MANIFEST_AND_PHYSICAL_VIEW_INDEX_ONLY",
        },
        "states": states,
        "views": views,
    }


def verify_source(plan):
    """Recheck original manifest, references and every unique owner PNG.

    Extra encoding/storage metadata attached by the caller is ignored. No
    original source is modified and no cache payload, SG, or model is loaded.
    """
    current = scan_episode(plan["episode_root"])
    for key in ("episode_root", "episode_key", "episode", "source", "states"):
        if current[key] != plan.get(key):
            raise ContractError("source identity changed: " + key)
    if set(current["views"]) != set(plan.get("views", {})):
        raise ContractError("source view inventory changed")
    for name, view in current["views"].items():
        expected = plan["views"][name]
        if (
            view["path"] != expected.get("path")
            or view["state_records"] != expected.get("state_records")
            or len(view["records"]) != len(expected.get("records", []))
        ):
            raise ContractError("source owner index changed: " + name)
        for actual, recorded in zip(view["records"], expected["records"]):
            if any(recorded.get(key) != value for key, value in actual.items()):
                raise ContractError("source PNG changed: " + name)
    return True
