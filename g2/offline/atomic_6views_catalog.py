"""Discover official RoboCasa LeRobot source episodes without flat-v3 caches.

The official per-task episodes.jsonl (not the G2 acceptance folder) owns the
episode count/length. Existing flat-v3 parquet is an optional acceleration/
compatibility source; the fallback derives the same stable global IDs from
sorted task class and local episode index. No dataset-side files are changed.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import re

EPISODE_NAME = re.compile(r"episode_([0-9]{6})\Z")
REQUIRED = ("states.npz", "model.xml.gz", "ep_meta.json")


class CatalogError(ValueError):
    pass


def discover_raw(raw_root, *, tasks=None, log=print):
    raw_root = Path(raw_root).resolve(strict=True)
    if not raw_root.is_dir():
        raise CatalogError("raw source root is not a directory")
    paths = sorted(p for p in raw_root.iterdir() if p.is_dir())
    available = {p.name for p in paths}
    if tasks:
        unknown = set(tasks) - available
        if unknown:
            raise CatalogError("unknown source task(s): " + ",".join(sorted(unknown)))
        paths = [p for p in paths if p.name in tasks]
    if not paths:
        raise CatalogError("no official source task directories found")
    all_rows = []
    task_roots = {}
    offset = 0
    for task_dir in paths:
        candidates = sorted(task_dir.glob("*/lerobot"))
        if len(candidates) != 1:
            raise CatalogError("expected exactly one official LeRobot root for " + task_dir.name)
        root = candidates[0]
        episode_meta = root / "meta" / "episodes.jsonl"
        if not episode_meta.is_file():
            raise CatalogError("official episodes.jsonl missing for " + task_dir.name)
        extras = root / "extras"
        if not extras.is_dir():
            raise CatalogError("original per-episode assets directory missing for " + task_dir.name)
        local = []
        with episode_meta.open(encoding="utf-8") as stream:
            for lineno, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError as error:
                    raise CatalogError(f"invalid official {episode_meta}:{lineno}") from error
                eid, length = entry.get("episode_index"), entry.get("length")
                if type(eid) is not int or eid < 0 or type(length) is not int or length < 2:
                    raise CatalogError(f"invalid official episode identity: {episode_meta}:{lineno}")
                local.append((eid, length))
        local.sort()
        ids = [eid for eid, _ in local]
        if len(ids) != len(set(ids)) or ids != list(range(len(ids))):
            raise CatalogError("missing/duplicate official local episode indexes: " + task_dir.name)
        on_disk = {
            int(match.group(1))
            for d in extras.iterdir() if d.is_dir()
            if (match := EPISODE_NAME.fullmatch(d.name)) is not None
        }
        if on_disk != set(ids):
            raise CatalogError("official episode metadata and extras inventory differ: " + task_dir.name)
        for eid, length in local:
            source = extras / f"episode_{eid:06d}"
            if any(not (source / kind).is_file() for kind in REQUIRED):
                raise CatalogError("incomplete official model/pose source: " + str(source))
            all_rows.append({
                "task_class": task_dir.name,
                "local_episode_index": eid,
                "global_episode_index": offset + eid,
                "length": length,
            })
        task_roots[task_dir.name] = root
        offset += len(local)
        if log is not None:
            log(f"G2_DISCOVERY task={task_dir.name} episodes={len(local)} "
                f"total={offset} source={root}", flush=True)
    if log is not None:
        log(f"G2_DISCOVERY_COMPLETE tasks={len(paths)} episodes={len(all_rows)}",
            flush=True)
    return all_rows, task_roots


def discover_flat(mapping, raw_root, *, log=print):
    """Use an existing flat mapping if present, otherwise create from originals."""
    mapping = Path(mapping)
    if mapping.is_file():
        try:
            import pyarrow.parquet as pq
        except ImportError as error:
            raise CatalogError("pyarrow required to read existing flat mapping") from error
        columns = ("task_class", "local_episode_index", "global_episode_index", "length")
        rows = pq.read_table(mapping, columns=list(columns)).to_pylist()
        source = "flat_v3_mapping.parquet"
        tasks = {x["task_class"] for x in rows}
        task_roots = {}
        for task in sorted(tasks):
            candidates = sorted((Path(raw_root) / task).glob("*/lerobot"))
            if len(candidates) != 1:
                raise CatalogError("official source path unavailable for " + task)
            task_roots[task] = candidates[0]
        if log is not None:
            log(f"G2_DISCOVERY reused_flat_mapping={mapping} "
                f"tasks={len(tasks)} episodes={len(rows)}", flush=True)
    else:
        rows, task_roots = discover_raw(raw_root, log=log)
        source = "official_episodes_jsonl"
    for index, row in enumerate(rows):
        if row.get("global_episode_index") != index:
            raise CatalogError(f"noncanonical global ID at {index}")
    return rows, task_roots, source
