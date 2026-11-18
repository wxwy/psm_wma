"""Read-only, per-task capacity accounting. Never renders or declares full start."""

from __future__ import annotations

import math
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

from g2.io import read_json
from g2.latent_cache.contract import CacheError, contained

EPISODE = re.compile(r"episode_(\d{6})$")


def category(path):
    if path.name == "spatial_source.json.gz":
        return "working_source_gzip"
    if path.name == "SPATIAL_SOURCE_GZIP.json":
        return "working_source_receipt"
    if path.name == "spatial_source.json":
        return "working_source"
    if path.name in (
        "spatial_source_index.json",
        "SPATIAL_SOURCE_FINAL_READY.json",
        "SOURCE_RETIREMENT.json",
    ):
        return "source_index"
    if path.suffix == ".png":
        return "png"
    if "vae_cache" in path.parts and path.suffix == ".pt":
        return "latent"
    if path.name.endswith(".json.gz"):
        return "scene_graph_gz"
    if path.name == "spatial_metadata.json":
        return "spatial_metadata"
    if path.name == "task_entities.json":
        return "task_entities"
    if path.name == "language.json":
        return "language"
    if path.name in ("episode_manifest.json", "COMPLETE.json", "manifest.json"):
        return "indices"
    return "other"


def episode_bytes(root, *, include_files=False):
    root = Path(root).absolute()
    if any(p.is_symlink() for p in (root, *root.parents)) or not root.is_dir():
        raise CacheError("capacity audit requires a real episode directory")
    totals = Counter()
    counts = Counter()
    allocated = 0
    rows = []
    for directory, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            if (Path(directory) / name).is_symlink():
                raise CacheError("symlink in capacity input; no traversal")
        for name in sorted(files):
            path = Path(directory) / name
            if not path.is_file():
                raise CacheError("non-file in capacity input")
            rel = path.relative_to(root)
            stat = path.stat()
            kind = category(rel)
            totals[kind] += stat.st_size
            counts[kind] += 1
            allocated += stat.st_blocks * 512
            if include_files:
                rows.append(
                    dict(
                        path=rel.as_posix(),
                        category=kind,
                        bytes=stat.st_size,
                        allocated_bytes=stat.st_blocks * 512,
                    )
                )
    manifest = read_json(contained(root, "episode_manifest.json"))
    result = dict(
        episode_root=str(root),
        task_class=manifest["task_class"],
        episode_id=manifest["episode_id"],
        logical_bytes=sum(totals.values()),
        allocated_bytes=allocated,
        file_count=sum(counts.values()),
        bytes_by_category=dict(totals),
        files_by_category=dict(counts),
        physical_png_owners=counts["png"],
        logical_states=len(manifest.get("states", [])),
        complete_marker_present=(root / "COMPLETE.json").is_file(),
        source_transaction_pending=(
            root / ".source_retirement/transaction.json"
        ).exists(),
    )
    if include_files:
        result["files"] = rows
    return result


def corpus_bytes(dataset_root):
    root = Path(dataset_root).absolute()
    tasks = contained(root, "tasks")
    episodes = []
    for task in sorted(tasks.iterdir()):
        directory = contained(root, "tasks/" + task.name + "/episodes")
        for path in sorted(directory.iterdir()):
            match = EPISODE.fullmatch(path.name)
            if not match:
                continue
            row = episode_bytes(path)
            if row["task_class"] != task.name or row["episode_id"] != int(match[1]):
                raise CacheError("capacity episode identity differs from directory")
            episodes.append(row)
    if not episodes:
        raise CacheError("capacity corpus is empty")
    seen = set()
    grouped = defaultdict(list)
    for row in episodes:
        key = (row["task_class"], row["episode_id"])
        if key in seen:
            raise CacheError("duplicate capacity episode identity")
        seen.add(key)
        grouped[key[0]].append(row)
    by_task = {}
    for task, rows in grouped.items():
        sizes = sorted(r["logical_bytes"] for r in rows)
        cats = Counter()
        files = Counter()
        for row in rows:
            cats.update(row["bytes_by_category"])
            files.update(row["files_by_category"])
        by_task[task] = dict(
            episodes=len(rows),
            logical_bytes=sum(sizes),
            mean_bytes=sum(sizes) / len(sizes),
            p50_bytes=sizes[(len(sizes) - 1) // 2],
            p95_bytes=sizes[math.ceil(0.95 * len(sizes)) - 1],
            min_bytes=sizes[0],
            max_bytes=sizes[-1],
            bytes_by_category=dict(cats),
            files_by_category=dict(files),
            logical_states=sum(r["logical_states"] for r in rows),
            physical_png_owners=sum(r["physical_png_owners"] for r in rows),
        )
    return dict(
        schema="g2_readonly_capacity_corpus_v1",
        dataset_root=str(root),
        episodes=episodes,
        by_task=by_task,
        episode_count=len(episodes),
        task_count=len(grouped),
        logical_bytes=sum(r["logical_bytes"] for r in episodes),
        allocated_bytes=sum(r["allocated_bytes"] for r in episodes),
        file_count=sum(r["file_count"] for r in episodes),
        scope="FILE_BYTE_COUNTS_NOT_SOURCE_PIXEL_OR_TRAINING_ACCEPTANCE",
    )


def capacity_report(
    old_root,
    new_root,
    *,
    available_bytes,
    reserve_bytes=8 * 1024**3,
    expected_episodes=9126,
    expected_tasks=18,
):
    from g2.latent_cache import final_source as final
    from g2.offline.stage_a import validate_profile_episode

    if any(
        type(v) is not int or v < 0
        for v in (available_bytes, reserve_bytes, expected_episodes, expected_tasks)
    ):
        raise CacheError(
            "capacity budgets/counts must be explicit nonnegative integers"
        )
    old = corpus_bytes(old_root)
    new = corpus_bytes(new_root)
    previous = {(r["task_class"], r["episode_id"]): r for r in old["episodes"]}
    deltas = defaultdict(list)
    samples = []
    for row in new["episodes"]:
        manifest = validate_profile_episode(row["episode_root"])
        if (
            manifest["schema"] != final.PROFILE_SCHEMA
            or row["source_transaction_pending"]
        ):
            raise CacheError("capacity samples must be fully retired v2 outputs")
        key = (row["task_class"], row["episode_id"])
        if key not in previous:
            raise CacheError("new sample has no same-identity old baseline")
        base = previous[key]
        delta = row["logical_bytes"] - base["logical_bytes"]
        deltas[key[0]].append(delta)
        samples.append(
            dict(
                task_class=key[0],
                episode_id=key[1],
                old_bytes=base["logical_bytes"],
                new_bytes=row["logical_bytes"],
                delta_bytes=delta,
                old_png_owners=base["physical_png_owners"],
                new_png_owners=row["physical_png_owners"],
                new_latent_bytes=row["bytes_by_category"].get("latent", 0),
                new_source_index_bytes=row["bytes_by_category"].get("source_index", 0),
                note="MEASURED_SAMPLE_DELTA_NOT_A_PER_TASK_VARIANT_GUARANTEE",
            )
        )
    all_deltas = [d for values in deltas.values() for d in values]
    lower = upper = 0
    strata = {}
    missing = sorted(set(old["by_task"]) - set(deltas))
    for task, baseline in old["by_task"].items():
        task_samples = deltas.get(task, ())
        values = task_samples or all_deltas
        lo = baseline["logical_bytes"] + baseline["episodes"] * min(values)
        hi = baseline["logical_bytes"] + baseline["episodes"] * max(values)
        lower += max(0, lo)
        upper += max(0, hi)
        strata[task] = dict(
            old_episode_count=baseline["episodes"],
            old_bytes=baseline["logical_bytes"],
            measured_samples=len(task_samples),
            conditional_lower_bytes=max(0, lo),
            conditional_upper_bytes=max(0, hi),
            method="SAME_TASK_SAMPLE_DELTA_RANGE"
            if task_samples
            else "UNVALIDATED_OTHER_TASK_DELTA_SENSITIVITY",
        )
    fits = upper + reserve_bytes <= available_bytes
    complete_coverage = (
        not missing
        and old["episode_count"] == expected_episodes
        and old["task_count"] == expected_tasks
    )
    return dict(
        schema="g2_source_capacity_report_v1",
        old=old,
        new_samples=samples,
        by_task_projection=strata,
        expected_episode_count=expected_episodes,
        expected_task_count=expected_tasks,
        measured_task_count=sum(bool(v) for v in deltas.values()),
        missing_new_task_samples=missing,
        available_bytes=available_bytes,
        required_output_reserve_bytes=reserve_bytes,
        conditional_lower_bytes=lower,
        conditional_upper_bytes=upper,
        candidate_bound_fits=fits,
        all_task_sample_coverage=complete_coverage,
        verdict="STRATIFIED_CANDIDATE_REQUIRES_GPT_APPROVAL"
        if fits and complete_coverage
        else "HOLD_CAPACITY",
        full_production_authorized=False,
        training_ready=False,
        uncertainty=[
            "sample deltas are not worst-case bounds for unseen variants",
            "PNG/owner/state distributions vary across tasks",
            "available_bytes may be an operator scenario; no deletion was performed",
            "native work and32-worker resource gate are separate",
        ],
    )
