"""Verified final-capsule publication and journaled retirement of working audits.

Called only by the acknowledged-job collector, never by a training reader.
Numeric PT files, PNG/SG/metadata/task/language files are never rewritten.
"""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

from g2.io import digest, read_json

from . import final_source as final
from .contract import CacheError, contained, fingerprint
from .retirement_policy import validate_target
from .source_locks import writer_lease
from .storage import _fsync_directory, atomic_json, build_lock

OLD_READY = "SPATIAL_SOURCE_READY.json"
MOVED = {
    final.FULL: ".source_retirement/spatial_source.retiring",
    OLD_READY: ".source_retirement/readiness.retiring",
}


def json_bytes(value):
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
        + "\n"
    ).encode()


def json_sha(value):
    return hashlib.sha256(json_bytes(value)).hexdigest()


def _audit_archive(root, source, scope, policy, job):
    if not policy["keep_full_audit"]:
        return None
    base = Path(policy["audit_archive_root"])
    base.mkdir(parents=True, exist_ok=True)
    guard = base / ".g2_audit_archive.json"
    identity = dict(
        schema="g2_external_audit_archive_v1", policy_id=fingerprint(policy)
    )
    with build_lock(base / ".initialize"):
        if guard.exists():
            if read_json(contained(base, guard.name)) != identity:
                raise CacheError("audit archive belongs to another policy")
        else:
            if any(p.name != ".initialize" for p in base.iterdir()):
                raise CacheError("refuse unowned nonempty archive root")
            atomic_json(guard, identity)
    path = contained(base, job + ".json.gz", allow_missing=True)
    raw = contained(root, final.FULL)
    sha = digest(raw)
    if not path.exists():
        temporary = contained(base, job + ".tmp", allow_missing=True)
        if temporary.exists():
            temporary.unlink()
        fd = os.open(
            temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600
        )
        with os.fdopen(fd, "wb") as stream:
            with gzip.GzipFile(
                filename="", fileobj=stream, mode="wb", compresslevel=1, mtime=0
            ) as zipped:
                with raw.open("rb") as inp:
                    for block in iter(lambda: inp.read(1024 * 1024), b""):
                        zipped.write(block)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        temporary.unlink()
        _fsync_directory(base)
    h = hashlib.sha256()
    with gzip.open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    if h.hexdigest() != sha:
        raise CacheError("external audit archive is not the verified original")
    receipt = dict(
        schema="g2_external_full_audit_receipt_v1",
        job_id=job,
        scope=scope,
        source_id=source["source_id"],
        full_source_sha256=sha,
        working_readiness=read_json(contained(root, OLD_READY)),
        gzip_sha256=digest(path),
        gzip_bytes=path.stat().st_size,
        retention_policy=policy["audit_retention_policy"],
    )
    rp = contained(base, job + ".receipt.json", allow_missing=True)
    if rp.exists():
        if read_json(rp) != receipt:
            raise CacheError("external archive receipt conflict")
    else:
        atomic_json(rp, receipt)
    return dict(
        path=str(path),
        sha256=digest(path),
        bytes=path.stat().st_size,
        receipt_sha256=digest(rp),
        retention_policy=policy["audit_retention_policy"],
    )


def _prepare(spool, job, row, proof, statuses, cleanup):
    from g2.offline.stage_a import validate_profile_episode

    from .production import cache_receipt
    from .storage import open_episode_index

    scope = json.loads(row["scope"])
    root = validate_target(spool.source_policy, row["target"], scope)
    if cleanup.get("status") not in ("complete", "not_registered"):
        raise CacheError("source retirement requires released managed renderer work")
    manifest = validate_profile_episode(root)
    if manifest["schema"] == final.PROFILE_SCHEMA:
        raise CacheError(
            "finalized source requires its original retirement journal/SQL binding"
        )
    source = read_json(contained(root, final.FULL))
    for rel in (final.CAPSULE, final.READY, final.RECEIPT, "spatial_source.json.gz"):
        if contained(root, rel, allow_missing=True).exists():
            raise CacheError(
                "unexpected final-source/audit file before retirement; retain it: "
                + rel
            )
    if (
        not all(
            manifest["output_profile"][k]
            for k in (
                "sixview_png",
                "island_png",
                "spatial_metadata",
                "scene_graph",
                "task_entities",
                "selection",
                "language",
                "robot_pose",
                "view_vae",
            )
        )
        or any(
            o["path"].startswith("_spatial_inputs/")
            for v in source["views"].values()
            for o in v["owners"]
        )
        or any(source[k] != scope[k] for k in ("source_fingerprint", "profile_id"))
        or digest(root / final.FULL) != (row["source_ready"] or row["sealed"])
        or source["source_id"] != proof["source_id"]
        or cache_receipt(root) != proof["verified_cache"]
    ):
        raise CacheError(
            "retirement requires the fully verified retained-PNG job scope"
        )
    index = open_episode_index(root)
    views, projections = final.compact_views(source)
    attestation = dict(
        job_id=job,
        scope=scope,
        working_proof_sha256=fingerprint(proof),
        ack_status_counts=statuses,
        work_cleanup_sha256=fingerprint(cleanup),
        policy_sha256=fingerprint(spool.source_policy),
    )
    archive = _audit_archive(root, source, scope, spool.source_policy, job)
    capsule = dict(
        schema=final.CAPSULE_SCHEMA,
        episode_id=source["episode_id"],
        task_class=source["task_class"],
        episode_key=scope["episode_key"],
        source_id=source["source_id"],
        source_fingerprint=source["source_fingerprint"],
        profile_id=source["profile_id"],
        world_frame=source["world_frame"],
        source_inputs_sha256=source["source_inputs_sha256"],
        input_identity=dict(
            mapping_sha256=spool.source_policy["mapping_sha256"],
            source_versions=spool.source_policy["source_versions"],
        ),
        working_source=index.manifest["source"],
        working_readiness=read_json(contained(root, OLD_READY)),
        working_cache_receipt=proof["verified_cache"],
        working_source_disposition="VERIFIED_HISTORICAL_HASH_NOT_AN_EXISTING_FILE",
        product_inventory_sha256=final.product_identity(manifest),
        numeric_inventory_sha256=fingerprint(
            dict(states=index.manifest["states"], views=index.manifest["views"])
        ),
        state_index="vae_cache/manifest.json:states",
        product_index="episode_manifest.json:states,files",
        recipe_id=index.recipe_id,
        views=views,
        projections=projections,
        final_pixel_events=source["final_pixel_events"],
        attestation=attestation,
        attestation_id=fingerprint(attestation),
        full_audit_archive=archive,
    )
    capsule["capsule_id"] = fingerprint(capsule)
    if len(json_bytes(capsule)) >= 1024 * 1024:
        raise CacheError(
            f"necessary final source capsule is not below1MiB; retain audit: bytes={len(json_bytes(capsule))}, owners={sum(len(v['owners']) for v in views.values())}, projections={len(projections)}, states={len(manifest['states'])}"
        )
    csha = json_sha(capsule)
    ready = dict(
        schema=final.SOURCE_SCHEMA,
        source_id=capsule["source_id"],
        capsule_id=capsule["capsule_id"],
        source_manifest_sha256=csha,
        attestation_id=capsule["attestation_id"],
        complete_source_index=True,
    )
    binding = dict(
        schema=final.SOURCE_SCHEMA,
        source_id=capsule["source_id"],
        capsule_id=capsule["capsule_id"],
        manifest_sha256=csha,
        complete_sha256=json_sha(ready),
        identity_manifest=final.CAPSULE,
        readiness_marker=final.READY,
        validation_scope="VERIFIED_FINAL_CAPSULE_RETIRED_WORKING_AUDIT",
        working_source=index.manifest["source"],
        view_index_sha256=index.manifest["source"]["view_index_sha256"],
    )
    cache = copy.deepcopy(index.manifest)
    cache.update(schema=final.INDEX_SCHEMA, source=binding)
    cc = read_json(contained(root, "vae_cache/COMPLETE.json"))
    cc.update(
        schema=final.COMPLETE_SCHEMA,
        manifest_sha256=json_sha(cache),
        source_index_sha256=csha,
        attestation_id=capsule["attestation_id"],
    )
    new_receipt = dict(
        proof["verified_cache"],
        schema="g2_verified_profile_vae_v2",
        cache_manifest_sha256=json_sha(cache),
        cache_complete_sha256=json_sha(cc),
        source_index_sha256=csha,
    )
    updated = dict(
        manifest,
        schema=final.PROFILE_SCHEMA,
        source_format=final.SOURCE_SCHEMA,
        source_index_sha256=csha,
        vae_receipt=new_receipt,
    )
    files = {
        final.CAPSULE: capsule,
        final.READY: ready,
        "vae_cache/manifest.json": cache,
        "vae_cache/COMPLETE.json": cc,
        "episode_manifest.json": updated,
    }
    retirement = dict(
        schema=final.RECEIPT_SCHEMA,
        source_id=source["source_id"],
        episode_key=scope["episode_key"],
        recipe_id=index.recipe_id,
        attestation_id=capsule["attestation_id"],
        capsule_sha256=csha,
        working_proof=proof,
        work_cleanup=cleanup,
        final_files={p: json_sha(v) for p, v in files.items()},
        retired_files={
            final.FULL: digest(root / final.FULL),
            OLD_READY: digest(root / OLD_READY),
        },
        full_audit_archive=archive,
        source_disposition="REMOVED_ONLY_AFTER_VERIFIED_FINAL_SOURCE_PUBLICATION",
    )
    files[final.RECEIPT] = retirement
    complete = read_json(contained(root, "COMPLETE.json"))
    complete.update(
        schema=final.PROFILE_SCHEMA,
        episode_manifest_sha256=json_sha(updated),
        source_index_sha256=csha,
        source_retirement_sha256=json_sha(retirement),
    )
    files["COMPLETE.json"] = complete
    result = dict(
        schema="g2_source_retirement_transaction_v2",
        job_id=job,
        scope=scope,
        policy_sha256=fingerprint(spool.source_policy),
        files=files,
        old_proof=proof,
        cleanup=cleanup,
        retired_files=retirement["retired_files"],
        old_source_bytes=(root / final.FULL).stat().st_size,
        product_files=manifest["files"],
        numeric_files={
            v["path"]: v["sha256"] for v in index.manifest["views"].values()
        },
    )
    if len(json_bytes(result)) > 8 * 1024 * 1024:
        raise CacheError("source retirement transaction exceeds finite8MiB budget")
    return result


def _pending(spool, job, root):
    path = contained(root, final.JOURNAL)
    txn = read_json(path, limit=8 * 1024 * 1024)
    with spool._db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
    if (
        row is None
        or row["done"] != 2
        or txn["job_id"] != job
        or json.loads(row["scope"]) != txn["scope"]
        or txn["policy_sha256"] != fingerprint(spool.source_policy)
    ):
        raise CacheError("retirement journal differs from active acknowledged scope")
    bound = json.loads(row["retirement"]) if row["retirement"] is not None else None
    if bound != dict(
        journal_sha256=digest(path),
        capsule_sha256=json_sha(txn["files"][final.CAPSULE]),
    ):
        raise CacheError("retirement journal changed after durable SQL binding")
    if txn["retired_files"][final.FULL] != (row["source_ready"] or row["sealed"]):
        raise CacheError("retired working source differs from acknowledged job")
    return txn


def _sweep_owned_atomic_temps(root, bound):
    """Only a prior durable SQL intent owns atomic temp names in these dirs."""
    for directory in (root, root / "vae_cache", root / ".source_retirement"):
        if not directory.exists():
            continue
        for path in directory.iterdir():
            if not (path.name.startswith(".json-") and path.name.endswith(".tmp")):
                continue
            if bound is None or path.is_symlink() or not path.is_file():
                raise CacheError(
                    "unexpected/unowned retirement atomic temporary; retain it"
                )
            path.unlink()
            _fsync_directory(directory)


def finalize(
    spool, job, row, proof=None, statuses=None, cleanup=None, *, failpoint=None
):
    """False means a reader/writer is active. Never infer missing source as valid."""
    from .ledger_archive import published_proof
    from .production import target_lock

    policy = spool.source_policy
    scope = json.loads(row["scope"])
    root = validate_target(policy, row["target"], scope)
    started = time.monotonic()

    def point(name):
        if failpoint:
            failpoint(name)

    try:
        with (
            build_lock(target_lock(root)),
            build_lock(root / "vae_cache"),
            writer_lease(root),
        ):
            journal = contained(root, final.JOURNAL, allow_missing=True)
            with spool._db() as db:
                active = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
            if active is None or json.loads(active["scope"]) != scope:
                raise CacheError("source retirement lost its acknowledged job")
            row = dict(active)
            bound = (
                json.loads(active["retirement"])
                if active and active["retirement"] is not None
                else None
            )
            _sweep_owned_atomic_temps(root, bound)
            if journal.parent.exists():
                allowed = {
                    "transaction.json",
                    "spatial_source.retiring",
                    "readiness.retiring",
                }
                if any(
                    p.name not in allowed or p.is_symlink()
                    for p in journal.parent.iterdir()
                ):
                    raise CacheError(
                        "unexpected retirement staging file; never remove it"
                    )
            manifest = read_json(contained(root, "episode_manifest.json"))
            if not journal.exists() and manifest["schema"] == final.PROFILE_SCHEMA:
                published_proof(row, scope)
                return True
            if not journal.exists():
                if proof is None or statuses is None or cleanup is None:
                    raise CacheError(
                        "retirement requires complete durable ACK and cleanup proof"
                    )
                txn = _prepare(spool, job, row, proof, statuses, cleanup)
                expected = dict(
                    journal_sha256=json_sha(txn),
                    capsule_sha256=json_sha(txn["files"][final.CAPSULE]),
                )
                with spool._db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    current = db.execute(
                        "SELECT retirement,done,scope FROM jobs WHERE id=?", (job,)
                    ).fetchone()
                    if (
                        current is None
                        or current["done"] != 2
                        or json.loads(current["scope"]) != scope
                    ):
                        raise CacheError("retirement intent lost its acknowledged job")
                    if (
                        current["retirement"] is not None
                        and json.loads(current["retirement"]) != expected
                    ):
                        raise CacheError(
                            "retirement intent changed before journal recreation"
                        )
                    db.execute(
                        "UPDATE jobs SET retirement=? WHERE id=?",
                        (json.dumps(expected, sort_keys=True), job),
                    )
                row["retirement"] = json.dumps(expected, sort_keys=True)
                point("capsule_intent_bound")
                point("capsule_before_intent_write")
                atomic_json(journal, txn)
                point("capsule_intent_fsynced")
            txn = _pending(spool, job, root)
            # Remove the episode marker during multi-file publication. Readers
            # hold leases or fail closed on the journal after a writer crash.
            complete_path = contained(root, "COMPLETE.json", allow_missing=True)
            if complete_path.exists():
                complete_path.unlink()
                _fsync_directory(root)
            for rel, value in txn["files"].items():
                if rel == "COMPLETE.json":
                    continue
                path = contained(root, rel, allow_missing=True)
                if path.exists() and digest(path) == json_sha(value):
                    continue
                point("capsule_before_write:" + rel)
                atomic_json(path, value, replace=path.exists())
                point("capsule_published:" + rel)
            # All training products and numeric files must still equal the
            # fully verified working publication before any audit byte goes.
            for rel, sha in txn["product_files"].items():
                if digest(contained(root, rel)) != sha:
                    raise CacheError(
                        "training product changed before source retirement"
                    )
            for rel, sha in txn["numeric_files"].items():
                if digest(contained(root, "vae_cache/" + rel)) != sha:
                    raise CacheError("numeric payload changed before source retirement")
            for rel, value in txn["files"].items():
                if rel != "COMPLETE.json" and digest(contained(root, rel)) != json_sha(
                    value
                ):
                    raise CacheError(
                        "new final indices failed pre-retirement hash verification"
                    )
            point("capsule_verified_before_retire")
            for rel, moved_rel in MOVED.items():
                original = contained(root, rel, allow_missing=True)
                moved = contained(root, moved_rel, allow_missing=True)
                expected = txn["retired_files"][rel]
                if original.exists() and moved.exists():
                    raise CacheError("ambiguous original and retiring audit files")
                if original.exists():
                    if digest(original) != expected:
                        raise CacheError("working audit changed before retirement")
                    point("capsule_before_source_rename:" + rel)
                    os.rename(original, moved)
                    _fsync_directory(root)
                    _fsync_directory(moved.parent)
                    point("capsule_source_renamed:" + rel)
                if moved.exists():
                    if digest(moved) != expected:
                        raise CacheError("retiring audit changed")
                    point("capsule_before_source_delete:" + rel)
                    moved.unlink()
                    _fsync_directory(moved.parent)
                    point("capsule_source_deleted:" + rel)
            # Missing old files are accepted only under the original SQL-bound
            # transaction, never by a v1 validator or a training reader.
            point("capsule_before_final_complete")
            atomic_json(root / "COMPLETE.json", txn["files"]["COMPLETE.json"])
            point("capsule_final_complete")
            published_proof(row, scope)
            metrics = dict(
                schema="g2_source_retirement_metrics_v1",
                job_id=job,
                old_source_bytes=txn["old_source_bytes"],
                capsule_bytes=(root / final.CAPSULE).stat().st_size,
                attempt_wall_s=time.monotonic() - started,
                archive=txn["files"][final.CAPSULE]["full_audit_archive"],
                real_vae_numeric_gate="NOT_INFERRED_FROM_RETIREMENT",
            )
            atomic_json(
                spool.root / "source_retirement_metrics" / f"{job}.json",
                metrics,
                replace=True,
            )
            journal.unlink()
            _fsync_directory(journal.parent)
            journal.parent.rmdir()
            _fsync_directory(root)
            point("capsule_journal_removed")
            return True
    except CacheError as exc:
        if isinstance(exc.__cause__, BlockingIOError):
            return False
        raise


def resume_pending(spool, job):
    with spool._db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
    if row is None:
        return True
    root = Path(row["target"])
    if not (root / final.JOURNAL).exists():
        return True
    return finalize(spool, job, dict(row))
