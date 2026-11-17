"""Exact managed-work leases and crash-safe cleanup, never source-data GC."""

from __future__ import annotations

import json
import os
import shutil
from contextlib import contextmanager
from pathlib import Path

from g2.io import digest, read_json
from g2.latent_cache.contract import CacheError, contained, fingerprint
from g2.latent_cache.storage import _fsync_directory, atomic_json, build_lock

GUARD = ".g2_managed_work_root.json"
LEASE = ".g2_episode_work.json"


def episode_work_path(row, config, profile):
    work = (
        Path(config.work_root) / row["task_class"] / f"episode_{row['episode_id']:06d}"
    )
    if config.sim_direct_geometry_only:
        work = work / (
            "direct_gt_geometry_only_color_only_v1"
            if config.sim_color_only
            else "direct_gt_geometry_only_v1"
        )
    if profile is not None:
        work = work / ("stage_a_" + profile.to_dict()["profile_id"])
    return work.absolute()


def real_path(path):
    path = Path(path).absolute()
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise CacheError("managed work path must not traverse symlinks")
    return Path(os.path.abspath(path))


def init_root(root, spool_root, output_root, protected=()):
    root = real_path(root)
    protected = (*protected, spool_root, output_root)
    for item in protected:
        p = Path(item).resolve()
        if root == p or root in p.parents or p in root.parents:
            raise CacheError("managed work overlaps protected input/output/code path")
    body = dict(
        schema="g2_managed_work_root_v1",
        root=str(root),
        spool=str(Path(spool_root).absolute()),
        output=str(Path(output_root).absolute()),
    )
    root.mkdir(parents=True, exist_ok=True)
    # The caller creates this once before concurrent workers start.
    with build_lock(root / ".g2-initialize"):
        guard = root / GUARD
        if guard.exists():
            if read_json(contained(root, GUARD)) != body:
                raise CacheError(
                    "managed work root belongs to a different production run"
                )
        else:
            if any(p.name != ".g2-initialize" for p in root.iterdir()):
                raise CacheError("refuse to claim nonempty unowned work root")
            atomic_json(guard, body)
    return body


@contextmanager
def producer_work(row, config, profile, spool, job):
    root = real_path(config.work_root)
    guard = read_json(contained(root, GUARD))
    if guard["spool"] != str(spool.root) or guard["output"] != str(
        Path(config.output_root).absolute()
    ):
        raise CacheError("work guard/spool/output identity differs")
    work = episode_work_path(row, config, profile)
    if root not in work.parents:
        raise CacheError("episode work escapes managed root")
    lease = dict(
        schema="g2_episode_work_lease_v1",
        job_id=job,
        work_root=str(root),
        work=str(work),
        guard_sha256=digest(root / GUARD),
        episode_key=f"{row['task_class']}/episode_{row['episode_id']:06d}",
        source_fingerprint=row["source_fingerprint"],
        profile_id=profile.to_dict()["profile_id"],
        source_row_sha256=fingerprint(row),
        keep_work=bool(config.keep_work),
    )
    with build_lock(root / ".g2-work-locks" / job):
        # Validate before mkdir: a late producer must never recreate a path
        # after the collector has renamed/deleted it or archived the job.
        with spool._db() as db:
            active = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
            expected_target = Path(config.output_root) / row["expected_relative_output"]
            if (
                active is None
                or active["done"]
                or active["target"] != str(expected_target.absolute())
            ):
                raise CacheError(
                    "cannot create work for an inactive or different target job"
                )
            scope = json.loads(active["scope"])
            if any(
                scope[key] != lease[key]
                for key in ("episode_key", "source_fingerprint", "profile_id")
            ):
                raise CacheError("work producer source differs from active job")
        if work.exists():
            if (
                not (work / LEASE).is_file()
                or read_json(contained(work, LEASE)) != lease
            ):
                raise CacheError("existing work has no matching episode/source lease")
        else:
            work.mkdir(parents=True)
            atomic_json(work / LEASE, lease)
        registration = dict(lease=lease, lease_sha256=digest(work / LEASE))
        with spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
            if active is None or active["done"]:
                raise CacheError("cannot create work for an archived completed job")
            encoded = json.dumps(registration, sort_keys=True)
            if active["work_lease"] is not None and active["work_lease"] != encoded:
                raise CacheError("work registration differs from prior producer")
            db.execute("UPDATE jobs SET work_lease=? WHERE id=?", (encoded, job))
        yield work


def cleanup_registered_work(spool, job, row, proof):
    """None means renderer lock busy; no deletion or completion claim."""
    if row.get("work_lease") is None:
        return dict(status="not_registered")
    info = json.loads(row["work_lease"])
    lease = info["lease"]
    root = real_path(lease["work_root"])
    work = real_path(lease["work"])
    if root not in work.parents or work == root:
        raise CacheError("registered work is outside managed root")
    guard = read_json(contained(root, GUARD))
    scope = json.loads(row["scope"])
    if (
        digest(root / GUARD) != lease["guard_sha256"]
        or guard["spool"] != str(spool.root)
        or scope["episode_key"] != lease["episode_key"]
        or scope["source_fingerprint"] != lease["source_fingerprint"]
        or scope["profile_id"] != lease["profile_id"]
        or lease["job_id"] != job
    ):
        raise CacheError("cleanup lease source/episode identity differs")
    if lease["keep_work"]:
        return dict(status="kept_by_explicit_config", lease=info)
    cleanup_rel = "work_cleanup/" + job + ".json"
    cleanup_path = contained(spool.root, cleanup_rel, allow_missing=True)
    intent_path = contained(
        spool.root, "work_cleanup/" + job + ".intent.json", allow_missing=True
    )
    completed = dict(
        schema="g2_managed_work_cleanup_v1",
        status="complete",
        lease=info,
        published_source_id=proof["source_id"],
        cache_manifest_sha256=proof["verified_cache"]["cache_manifest_sha256"],
    )
    try:
        with build_lock(root / ".g2-work-locks" / job):
            from g2.latent_cache.production import cache_receipt, target_lock

            with build_lock(target_lock(row["target"])):
                if cache_receipt(row["target"]) != proof["verified_cache"]:
                    raise CacheError("published result changed before work cleanup")
                if cleanup_path.exists():
                    if read_json(cleanup_path) != completed or work.exists():
                        raise CacheError("cleanup receipt/work recreation conflict")
                    return completed
                trash_root = root / ".g2-trash"
                trash_root.mkdir(exist_ok=True)
                trash = contained(root, ".g2-trash/" + job, allow_missing=True)
                if work.exists() and trash.exists():
                    raise CacheError("both live and trash work exist; refuse ambiguity")
                candidate = work if work.exists() else trash
                intent = dict(
                    schema="g2_managed_work_cleanup_intent_v1",
                    lease=info,
                    published_source_id=proof["source_id"],
                )
                prior_intent = read_json(intent_path) if intent_path.exists() else None
                if prior_intent is not None and prior_intent != intent:
                    raise CacheError("cleanup intent differs")
                if work.exists() or (trash.exists() and prior_intent is None):
                    if (
                        digest(contained(candidate, LEASE)) != info["lease_sha256"]
                        or read_json(candidate / LEASE) != lease
                    ):
                        raise CacheError("work lease changed before deletion")
                elif not trash.exists() and prior_intent is None:
                    raise CacheError("missing work without durable cleanup intent")
                if prior_intent is None:
                    atomic_json(intent_path, intent)
                if candidate.exists():
                    if candidate == work:
                        os.rename(work, trash)
                        _fsync_directory(work.parent)
                        _fsync_directory(trash_root)
                    shutil.rmtree(trash)
                    _fsync_directory(trash_root)
                # Missing work after a crash is safe only with our durable
                # cleanup intent, not by trusting an arbitrary missing path.
                atomic_json(cleanup_path, completed)
                return completed
    except CacheError as exc:
        if isinstance(exc.__cause__, BlockingIOError):
            return None
        raise
