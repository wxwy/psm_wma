"""Durable episode tombstones; only active events occupy the working ledger."""

from __future__ import annotations

import json
from pathlib import Path

from g2.io import digest, read_json

from .contract import CacheError, contained
from .storage import atomic_json, build_lock


def published_proof(row, scope):
    from g2.offline.stage_a import validate_profile_episode

    from .production import cache_receipt

    root = Path(row["target"])
    manifest = validate_profile_episode(root)
    receipt = cache_receipt(root)
    from . import final_source as final

    source = final.load_source(root)
    is_final = source["schema"] == final.SOURCE_SCHEMA
    if is_final:
        bound = json.loads(row["retirement"]) if row.get("retirement") else None
        if (
            bound is None
            or bound.get("capsule_sha256") != digest(root / final.CAPSULE)
            or final.load_capsule(root)["attestation"]["scope"] != scope
        ):
            raise CacheError(
                "final capsule differs from durable SQL retirement binding"
            )
    actual = final.working_source_sha(root)
    if (
        actual != (row["source_ready"] or row["sealed"])
        or any(source[k] != scope[k] for k in ("source_fingerprint", "profile_id"))
        or f"{source['task_class']}/episode_{source['episode_id']:06d}"
        != scope["episode_key"]
        or receipt["recipe_id"] != scope["recipe_id"]
    ):
        raise CacheError("published episode differs from active scope")
    from g2.offline.view_only_source import working_source_info

    names = (
        (
            final.CAPSULE,
            final.READY,
            final.RECEIPT,
            "episode_manifest.json",
            "COMPLETE.json",
            "vae_cache/manifest.json",
            "vae_cache/COMPLETE.json",
        )
        if is_final
        else (
            *working_source_info(root)["files"],
            "episode_manifest.json",
            "COMPLETE.json",
            "vae_cache/manifest.json",
            "vae_cache/COMPLETE.json",
        )
    )
    files = {p: digest(contained(root, p)) for p in names}
    return dict(
        source_id=source["source_id"],
        verified_cache=receipt,
        identity_files=files,
        profile_complete=manifest["profile_complete"],
        **(
            dict(source_lifecycle="view_first_posthoc_v1")
            if not manifest["output_profile"]["view_vae"]
            else {}
        ),
        **(
            dict(
                working_verified_cache=final.load_capsule(root)[
                    "working_cache_receipt"
                ],
                source_index_sha256=digest(root / final.CAPSULE),
            )
            if is_final
            else {}
        ),
    )


def lookup(spool, db, *, job=None, target=None):
    row = db.execute(
        "SELECT * FROM completed WHERE " + ("id=?" if job is not None else "target=?"),
        (job if job is not None else str(target),),
    ).fetchone()
    if row is None:
        return None
    path = contained(spool.root, row["receipt_path"])
    if digest(path) != row["receipt_sha"]:
        raise CacheError("completed tombstone is missing or damaged")
    record = read_json(path)
    if (
        record.get("schema")
        not in (
            "g2_published_episode_tombstone_v1",
            "g2_published_episode_tombstone_v2",
        )
        or record["job"]["id"] != row["id"]
        or record["job"]["target"] != row["target"]
        or record["job"]["scope"] != row["scope"]
    ):
        raise CacheError("completed tombstone/index identity differs")
    return record


def check_identity(record):
    root = Path(record["job"]["target"])
    for rel, sha in record["verification"]["identity_files"].items():
        if digest(contained(root, rel)) != sha:
            raise CacheError("archived published identity changed")


def duplicate(spool, record, event):
    check_identity(record)
    from .final_source import load_source

    source = (
        load_source(record["job"]["target"])
        if record["schema"] == "g2_published_episode_tombstone_v2"
        or record["verification"].get("source_lifecycle") == "view_first_posthoc_v1"
        else read_json(contained(record["job"]["target"], "spatial_source.json"))
    )
    if source["final_pixel_events"].get(event.event_id) != event.descriptor():
        raise CacheError("late event is not a declared archived final owner")
    return "completed_by_cache"


def archive(spool, job, *, failpoint=None):
    """File/fsync first, SQLite receipt+deletes in one FULL-sync transaction.

    A crash before commit leaves a retryable done row; after commit readers
    resolve the same job through its compact tombstone. No unacknowledged job
    or event is eligible. The per-episode receipt is the permanent audit trail.
    """
    with build_lock(spool.root / "archive_locks" / job):
        with spool._db() as db:
            previous = lookup(spool, db, job=job)
            if previous is not None:
                check_identity(previous)
                return True
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
            if row is None or row["done"] != 2 or row["error"]:
                raise CacheError("only fully reaped jobs may leave the active ledger")
            row = dict(row)
            scope = json.loads(row["scope"])
            statuses = dict(
                db.execute(
                    "SELECT status,COUNT(*) FROM events WHERE job=? GROUP BY status",
                    (job,),
                ).fetchall()
            )
            if set(statuses) - {"acked", "completed_by_cache"}:
                raise CacheError("cannot archive unacknowledged events")
        if spool.source_policy is not None:
            from .source_retirement import resume_pending

            if not resume_pending(spool, job):
                return False
            with spool._db() as db:
                row = dict(
                    db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
                )
        proof = published_proof(row, scope)
        from g2.offline.work_lifecycle import cleanup_registered_work

        cleanup = cleanup_registered_work(spool, job, row, proof)
        if cleanup is None:
            import time

            with spool._db() as db:
                db.execute(
                    "UPDATE jobs SET cleanup_after=? WHERE id=?",
                    (time.time() + 0.2, job),
                )
            return False
        if spool.source_policy is not None:
            from .source_retirement import finalize

            if not finalize(
                spool, job, row, proof, statuses, cleanup, failpoint=failpoint
            ):
                import time

                with spool._db() as db:
                    db.execute(
                        "UPDATE jobs SET cleanup_after=? WHERE id=?",
                        (time.time() + 0.2, job),
                    )
                return False
            with spool._db() as db:
                row = dict(
                    db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
                )
            proof = published_proof(row, scope)
        receipt = dict(
            schema="g2_published_episode_tombstone_v2"
            if spool.source_policy is not None
            else "g2_published_episode_tombstone_v1",
            job=row,
            verification=proof,
            work_cleanup=cleanup,
            event_status_counts=statuses,
        )
        relative = "completed/" + job[:2] + "/" + job + ".json"
        path = contained(spool.root, relative, allow_missing=True)
        if path.exists():
            old = read_json(path)
            # Scheduling retry time is not part of immutable publication scope.
            old["job"]["cleanup_after"] = row["cleanup_after"]
            if old != receipt:
                raise CacheError("existing completed receipt differs; never overwrite")
            receipt = read_json(path)
        else:
            atomic_json(path, receipt)
        if failpoint:
            failpoint("receipt_before_gc")
        with spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
            if (
                current is None
                or current["scope"] != row["scope"]
                or current["done"] != 2
            ):
                raise CacheError("job changed during ledger archival")
            if db.execute(
                "SELECT COUNT(*) FROM events WHERE job=? AND (png IS NOT NULL OR status NOT IN ('acked','completed_by_cache'))",
                (job,),
            ).fetchone()[0]:
                raise CacheError("cannot GC pending inputs")
            db.execute(
                "INSERT INTO completed(id,target,scope,receipt_path,receipt_sha) VALUES(?,?,?,?,?)",
                (job, row["target"], row["scope"], relative, digest(path)),
            )
            db.execute("DELETE FROM events WHERE job=?", (job,))
            db.execute("DELETE FROM jobs WHERE id=?", (job,))
            if failpoint:
                failpoint("gc_before_commit")
        if failpoint:
            failpoint("gc_after_commit")
        return True


def verify_archived_payload_bytes(spool, target):
    """Fast *byte-exact* recheck of a previously fully verified tombstone.

    The receipt was produced only after a full profile/source/numeric audit.
    Recheck its original signed identity files plus every published product and
    every PT byte hash. An unchanged byte set cannot acquire new semantic errors,
    so repeating the expensive JSON/MuJoCo/torch parsing is unnecessary.
    Unarchived or foreign caches still take the original full verification path.
    """
    root = Path(target).absolute()
    with spool._db() as db:
        record = lookup(spool, db, target=root)
    if record is None:
        return False
    scope = json.loads(record["job"]["scope"])
    if (
        record["job"]["target"] != str(root)
        or scope.get("target") != str(root)
        or scope.get("recipe_id") != spool.recipe["recipe_id"]
        or record["verification"]["verified_cache"]["recipe_id"]
        != spool.recipe["recipe_id"]
    ):
        raise CacheError("archived source/recipe is not the current batch scope")

    # The complete/index/manifests and compressed/raw source are all bound
    # by the archived, SHA256-protected receipt.
    check_identity(record)
    manifest = read_json(contained(root, "episode_manifest.json"))
    if (
        manifest.get("source_fingerprint") != scope["source_fingerprint"]
        or manifest.get("output_profile", {}).get("profile_id") != scope["profile_id"]
        or not isinstance(manifest.get("files"), dict)
    ):
        raise CacheError("archived profile/source differs from the durable scope")
    for relative, expected_sha in manifest["files"].items():
        if digest(contained(root, relative)) != expected_sha:
            raise CacheError("archived Stage-A product bytes changed: " + relative)

    index = read_json(contained(root, "vae_cache/manifest.json"))
    if (
        index.get("recipe", {}).get("recipe_id") != scope["recipe_id"]
        or not isinstance(index.get("views"), dict)
        or not index["views"]
    ):
        raise CacheError("archived numeric manifest is not the verified recipe")
    for view_id, entry in index["views"].items():
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("path"), str)
            or not isinstance(entry.get("sha256"), str)
            or digest(contained(root / "vae_cache", entry["path"])) != entry["sha256"]
        ):
            raise CacheError("archived PT bytes changed: " + view_id)
    # Check the identity again to reject mutation while scanning its products.
    check_identity(record)
    return True
