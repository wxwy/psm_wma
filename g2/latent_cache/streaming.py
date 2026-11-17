"""Bounded final-pixel transport, durable numerical ACK and crash recovery.

The independent consumer shares #53 Encode1 validation and storage. Final source
ownership is sealed separately before VAE/profile completion, without fake
legacy markers. Private numeric chunks are reconciled to compact owner indices.
"""

from __future__ import annotations

import hashlib
import io
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .contract import CacheError, fingerprint, safe_relative
from .storage import atomic_json, build_lock


@dataclass(frozen=True)
class ConsumerLimits:
    max_events: int = 32
    max_spool_bytes: int = 256 * 1024 * 1024

    def __post_init__(self):
        if any(
            type(x) is not int or x < 1 for x in (self.max_events, self.max_spool_bytes)
        ):
            raise CacheError("consumer limits must be positive; no unbounded mode")


@dataclass(frozen=True)
class FinalPixelEvent:
    event_id: str
    episode_key: str
    view_id: str
    canonical_view_id: str
    variant: str
    rgb_sha256: str
    final_pixel_phase: str
    png_bytes: bytes
    source_fingerprint: str
    profile_id: str
    pixel_record_key: str
    size_wh: tuple[int, int]

    def descriptor(self):
        return {
            k: (list(v) if k == "size_wh" else v)
            for k, v in self.__dict__.items()
            if k != "png_bytes"
        }


def decode_final_png(data, *, expected_size=None):
    """Verify PNG structure and decode RGB pixels, not just the magic bytes."""
    from PIL import Image

    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != "PNG" or image.mode != "RGB":
                raise CacheError("final spatial input must be an RGB PNG")
            size = image.size
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
        if expected_size is not None and tuple(expected_size) != size:
            raise CacheError("final PNG dimensions differ from owner projection")
        return size
    except (OSError, ValueError, SyntaxError) as exc:
        raise CacheError(
            "final PNG decoding/projection check failed: " + str(exc)
        ) from exc


def final_pixel_event(
    path,
    *,
    episode_key,
    view_id,
    canonical_view_id,
    variant,
    source_fingerprint,
    profile_id,
    expected_size=None,
):
    safe_relative(view_id)
    safe_relative(canonical_view_id)
    if variant not in ("clean", "w_rbs"):
        raise CacheError("unknown finalized pixel variant")
    data = Path(path).read_bytes()
    size = decode_final_png(data, expected_size=expected_size)
    sha = hashlib.sha256(data).hexdigest()
    identity = dict(
        episode_key=episode_key,
        view_id=view_id,
        rgb_sha256=sha,
        source_fingerprint=source_fingerprint,
        profile_id=profile_id,
    )
    return FinalPixelEvent(
        fingerprint(identity),
        episode_key,
        view_id,
        canonical_view_id,
        variant,
        sha,
        "FINAL_MARKER_PIXELS" if variant == "w_rbs" else "FINAL_CLEAN_PIXELS",
        bytes(data),
        source_fingerprint,
        profile_id,
        # Numeric reuse is pixel+View+recipe based, separate from publication
        # scope. Language/template changes must not require new VAE math.
        fingerprint(dict(view_id=view_id, rgb_sha256=sha)),
        size,
    )


def seal_source(root, inventory):
    """Source readiness precedes VAE; queue admission is not profile completion."""
    from g2.offline.output_profile import SOURCE_SCHEMA

    if inventory.get("schema") != SOURCE_SCHEMA:
        raise CacheError("explicit new source inventory schema is required")
    body = dict(inventory)
    body["source_id"] = fingerprint(inventory)
    root = Path(root)
    atomic_json(root / "spatial_source.json", body)
    atomic_json(
        root / "SPATIAL_SOURCE_READY.json",
        dict(
            schema=SOURCE_SCHEMA,
            source_id=body["source_id"],
            source_manifest_sha256=hashlib.sha256(
                (root / "spatial_source.json").read_bytes()
            ).hexdigest(),
            complete_spatial_source=True,
            profile_complete=False,
        ),
    )
    return body["source_id"]


class DeliveryDeferred(CacheError):
    """Delivery may resume from retained final PNGs; provenance errors still fail."""


class QueueBackpressure(DeliveryDeferred):
    """Pending inputs occupy capacity; consuming them can free admission."""


class EventSpool:
    """Cross-process bounded admission and durable ACKs (SQLite FULL sync).

    Only pending/running input BLOBs count against queue capacity; a BLOB is
    removed in the ACK transaction after its audited numeric chunk is fsynced.
    Numeric chunks have a separate finite per-spool output budget. They are
    private build artifacts, not final per-record dataset files.
    """

    def __init__(
        self,
        root,
        recipe,
        *,
        limits=ConsumerLimits(),
        max_result_bytes=4 * 1024**3,
        max_records=100000,
        source_policy=None,
        _existing_only=False,
    ):
        import sqlite3

        from .contract import contained, validate_recipe

        self.root = Path(root).absolute()
        if any(p.is_symlink() for p in (self.root, *self.root.parents)):
            raise CacheError("spool path must not traverse symlinks")
        self.root.mkdir(parents=True, exist_ok=True)
        if (
            type(max_result_bytes) is not int
            or max_result_bytes < 1
            or type(max_records) is not int
            or max_records < 1
        ):
            raise CacheError("finite numeric/record budget required")
        self.recipe = validate_recipe(recipe)
        self.limits = limits
        self.max_result_bytes = max_result_bytes
        self.max_records = max_records
        from .retirement_policy import claim_policy, validate_policy

        self.source_policy = validate_policy(source_policy, self.root)
        if self.source_policy is not None:
            claim_policy(self.source_policy, existing_only=_existing_only)
        binding = dict(
            schema="g2_final_pixel_spool_v4"
            if self.source_policy is not None
            else "g2_final_pixel_spool_v3",
            recipe=recipe,
            max_events=limits.max_events,
            max_spool_bytes=limits.max_spool_bytes,
            max_result_bytes=max_result_bytes,
            max_records=max_records,
        )
        if self.source_policy is not None:
            binding["source_policy"] = self.source_policy
        if _existing_only:
            from g2.io import read_json

            if read_json(contained(self.root, "config.json")) != binding:
                raise CacheError("spool recipe or limits differ")
            self.database = contained(self.root, "events.sqlite")
            return  # Producer attachment never contends on initialization/schema writes.
        with build_lock(self.root / "init"):
            path = contained(self.root, "config.json", allow_missing=True)
            if path.exists():
                from g2.io import read_json

                if read_json(path) != binding:
                    raise CacheError("spool recipe or limits differ")
            else:
                atomic_json(path, binding)
            database = contained(self.root, "events.sqlite", allow_missing=True)
            with sqlite3.connect(database) as db:
                db.execute("PRAGMA journal_mode=DELETE")
                db.execute("PRAGMA synchronous=FULL")
                db.execute(
                    "CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, scope TEXT NOT NULL, target TEXT NOT NULL UNIQUE, source_ready TEXT, sealed TEXT, done INTEGER NOT NULL DEFAULT 0, error TEXT, completion_receipt TEXT, work_lease TEXT, cleanup_after REAL NOT NULL DEFAULT 0, retirement TEXT)"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS events (id TEXT NOT NULL, job TEXT NOT NULL, descriptor TEXT NOT NULL, png BLOB, status TEXT NOT NULL, result TEXT, result_sha TEXT, error TEXT, PRIMARY KEY(job,id))"
                )
                db.execute(
                    "CREATE TABLE IF NOT EXISTS completed (id TEXT PRIMARY KEY,target TEXT NOT NULL UNIQUE,scope TEXT NOT NULL,receipt_path TEXT NOT NULL,receipt_sha TEXT NOT NULL)"
                )
                db.execute("CREATE INDEX IF NOT EXISTS event_status ON events(status)")
                db.execute("CREATE INDEX IF NOT EXISTS event_result ON events(result)")
        self.database = database

    @classmethod
    def open(cls, root):
        from g2.io import read_json

        from .contract import contained

        cfg = read_json(contained(root, "config.json"))
        return cls(
            root,
            cfg["recipe"],
            limits=ConsumerLimits(cfg["max_events"], cfg["max_spool_bytes"]),
            max_result_bytes=cfg["max_result_bytes"],
            max_records=cfg["max_records"],
            source_policy=cfg.get("source_policy"),
            _existing_only=True,
        )

    @contextmanager
    def _db(self):
        import sqlite3

        db = sqlite3.connect(self.database, timeout=5, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def register(self, target, *, episode_key, source_fingerprint, profile_id):
        import json

        from .production import target_lock

        target = Path(target).absolute()
        from .storage import _hex

        _hex(source_fingerprint)
        _hex(profile_id)
        safe_relative(episode_key)
        if (
            target == self.root
            or target in self.root.parents
            or self.root in target.parents
        ):
            raise CacheError("spool must be separate from published episode")
        if any(p.is_symlink() for p in (target, *target.parents)):
            raise CacheError("stream target cannot traverse symlinks")
        scope = dict(
            episode_key=episode_key,
            source_fingerprint=source_fingerprint,
            profile_id=profile_id,
            target=str(target),
            recipe_id=self.recipe["recipe_id"],
        )
        if self.source_policy is not None:
            from .retirement_policy import validate_target

            validate_target(self.source_policy, target, scope)
        from g2.io import canonical

        if len(canonical(scope)) > 16384:
            raise CacheError("job scope exceeds finite ledger item budget")
        job = fingerprint(scope)
        with build_lock(target_lock(target)), self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            from .ledger_archive import check_identity, lookup

            completed = lookup(self, db, target=target)
            if completed is not None:
                if json.loads(completed["job"]["scope"]) != scope:
                    raise CacheError(
                        "archived target is bound to another source/recipe"
                    )
                check_identity(completed)
                return completed["job"]["id"]
            row = db.execute(
                "SELECT * FROM jobs WHERE target=?", (str(target),)
            ).fetchone()
            if row is not None and json.loads(row["scope"]) != scope:
                raise CacheError("stream target is bound to another source/recipe")
            if (
                row is None
                and db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
                >= self.max_records
            ):
                raise CacheError("finite job ledger budget reached")
            db.execute(
                "INSERT OR IGNORE INTO jobs(id,scope,target) VALUES(?,?,?)",
                (job, json.dumps(scope, sort_keys=True), str(target)),
            )
        return job

    def _scope(self, db, job, *, allow_failed=False):
        import json

        row = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
        if row is None:
            from .ledger_archive import lookup

            completed = lookup(self, db, job=job)
            if completed is None:
                raise CacheError("unknown producer job")
            row = dict(completed["job"], archived=True)

        if row["error"] and not allow_failed:
            raise DeliveryDeferred("consumer failed; inputs retained: " + row["error"])
        return row, json.loads(row["scope"])

    def enqueue(self, job, event, *, timeout_s=60):
        import json
        import math
        import time

        if (
            type(timeout_s) not in (int, float)
            or not math.isfinite(timeout_s)
            or timeout_s < 0
        ):
            raise CacheError("finite nonnegative enqueue timeout required")
        validate_event(event)
        if len(event.png_bytes) > self.limits.max_spool_bytes:
            raise DeliveryDeferred("one final image exceeds finite spool byte budget")
        deadline = time.monotonic() + timeout_s
        while True:
            with self._db() as db:
                db.execute("BEGIN IMMEDIATE")
                row, scope = self._scope(db, job)
                if isinstance(row, dict) and row.get("archived"):
                    from .ledger_archive import duplicate, lookup

                    return duplicate(self, lookup(self, db, job=job), event)
                for key in ("episode_key", "source_fingerprint", "profile_id"):
                    if event.descriptor()[key] != scope[key]:
                        raise CacheError("event belongs to another production scope")
                existing = db.execute(
                    "SELECT * FROM events WHERE id=? AND job=?", (event.event_id, job)
                ).fetchone()
                if existing:
                    if (
                        existing["job"] != job
                        or json.loads(existing["descriptor"]) != event.descriptor()
                    ):
                        raise CacheError("conflicting duplicate final-pixel event")
                    if existing["status"] == "failed":
                        raise DeliveryDeferred("event failed; explicit retry required")
                    return existing["status"]
                if row["sealed"] is not None or row["done"]:
                    raise CacheError("cannot add pixels to sealed production job")
                count, size = db.execute(
                    "SELECT COUNT(*),COALESCE(SUM(length(png)),0) FROM events WHERE png IS NOT NULL"
                ).fetchone()
                total = db.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                if total >= self.max_records:
                    raise DeliveryDeferred(
                        "active record ledger budget reached; await verified episode archival"
                    )
                if (
                    count < self.limits.max_events
                    and size + len(event.png_bytes) <= self.limits.max_spool_bytes
                ):
                    db.execute(
                        "INSERT INTO events(id,job,descriptor,png,status) VALUES(?,?,?,?,?)",
                        (
                            event.event_id,
                            job,
                            json.dumps(event.descriptor(), sort_keys=True),
                            event.png_bytes,
                            "pending",
                        ),
                    )
                    return "pending"
            if time.monotonic() >= deadline:
                raise QueueBackpressure(
                    "bounded queue backpressure timed out; no event was discarded"
                )
            time.sleep(min(0.05, max(0, deadline - time.monotonic())))

    def deliver(self, job, event, diagnostic_path, *, timeout_s=60):
        """Retain legal RGB/SG when numerical delivery is temporarily unavailable.

        Only delivery/capacity failures are deferred. Final-pixel provenance
        checks still raise. The final sealed source remains the durable input
        inventory, from which the consumer refills missing events after retry.
        """
        import sqlite3

        if Path(diagnostic_path).exists():
            validate_event(event)
            return "deferred"
        try:
            return self.enqueue(job, event, timeout_s=timeout_s)
        except (DeliveryDeferred, sqlite3.OperationalError, OSError) as exc:
            atomic_json(
                diagnostic_path,
                dict(
                    schema="g2_vae_delivery_pending_v1",
                    job=job,
                    event_id=event.event_id,
                    rgb_sha256=event.rgb_sha256,
                    status="pending",
                    error=str(exc),
                    inputs_retained=True,
                ),
            )
            return "deferred"

    def offer_source(self, job):
        """Persist a fully validated input inventory, even after encode failure."""
        from g2.io import digest, read_json

        from .sealed_source import scan_source

        with self._db() as db:
            row, scope = self._scope(db, job, allow_failed=True)
        if row["done"] and not (isinstance(row, dict) and row.get("archived")):
            from g2.offline.stage_a import validate_profile_episode

            validate_profile_episode(row["target"])
            return
        if isinstance(row, dict) and row.get("archived"):
            from .ledger_archive import check_identity

            check_identity(self.completed_receipt(job))
            return
        plan = scan_source(row["target"])
        source = read_json(Path(row["target"]) / "spatial_source.json")
        if plan["episode_key"] != scope["episode_key"] or any(
            source[k] != scope[k] for k in ("source_fingerprint", "profile_id")
        ):
            raise CacheError("offered source differs from producer scope")
        identity = digest(Path(row["target"]) / "spatial_source.json")
        if row["source_ready"] is not None and row["source_ready"] != identity:
            raise CacheError("offered source changed")
        with self._db() as db:
            db.execute("UPDATE jobs SET source_ready=? WHERE id=?", (identity, job))

    def refill_one(self, job):
        """Bounded refill from sealed bytes after a producer/consumer interruption."""
        from g2.io import digest, read_json

        from .contract import contained

        with self._db() as db:
            row, scope = self._scope(db, job)
            ids = {
                r[0] for r in db.execute("SELECT id FROM events WHERE job=?", (job,))
            }
        if row["done"]:
            from .ledger_archive import check_identity

            if isinstance(row, dict) and row.get("archived"):
                check_identity(self.completed_receipt(job))
            return False
        if digest(Path(row["target"]) / "spatial_source.json") != row["source_ready"]:
            raise CacheError("offered source changed during recovery")
        if isinstance(row, dict) and row.get("archived"):
            from .ledger_archive import check_identity

            check_identity(self.completed_receipt(job))
            return
        source = read_json(contained(row["target"], "spatial_source.json"))
        for vid, view in sorted(source["views"].items()):
            for owner in view["owners"]:
                if owner["event_id"] in ids:
                    continue
                desc = source["final_pixel_events"][owner["event_id"]]
                event = final_pixel_event(
                    contained(row["target"], owner["path"]),
                    episode_key=scope["episode_key"],
                    source_fingerprint=scope["source_fingerprint"],
                    profile_id=scope["profile_id"],
                    view_id=vid,
                    canonical_view_id=desc["canonical_view_id"],
                    variant=desc["variant"],
                    expected_size=desc["size_wh"],
                )
                if event.descriptor() != desc:
                    raise CacheError("recovery PNG differs from offered source")
                self.enqueue(job, event, timeout_s=0)
                return True
        self.seal(job)
        return True

    def seal(self, job):
        import json

        from g2.io import digest, read_json

        from .sealed_source import scan_source

        with self._db() as db:
            row, scope = self._scope(db, job)
        if row["done"] and not (isinstance(row, dict) and row.get("archived")):
            from g2.offline.stage_a import validate_profile_episode

            validate_profile_episode(row["target"])
            return
        if isinstance(row, dict) and row.get("archived"):
            from .ledger_archive import check_identity

            check_identity(self.completed_receipt(job))
            return
        plan = scan_source(row["target"])
        source = read_json(Path(row["target"]) / "spatial_source.json")
        if (
            any(source[k] != scope[k] for k in ("source_fingerprint", "profile_id"))
            or plan["episode_key"] != scope["episode_key"]
        ):
            raise CacheError("sealed episode differs from registered producer")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            current, _ = self._scope(db, job)
            if isinstance(current, dict) and current.get("archived"):
                return
            # All compact owners must refer to actual final byte events. Events
            # eliminated by compaction can remain private chunks, never index rows.
            for eid, desc in source["final_pixel_events"].items():
                event = db.execute(
                    "SELECT * FROM events WHERE id=? AND job=?", (eid, job)
                ).fetchone()
                if event is None or json.loads(event["descriptor"]) != desc:
                    raise CacheError("sealed owner lacks matching production event")
            seal = digest(Path(row["target"]) / "spatial_source.json")
            if row["sealed"] is not None and row["sealed"] != seal:
                raise CacheError("sealed job source changed")
            db.execute("UPDATE jobs SET sealed=? WHERE id=?", (seal, job))

    def enqueue_source(self, job, *, timeout_s=60):
        """Resume a ready source, without replaying renderer or fake COMPLETE."""
        from g2.io import read_json

        from .contract import contained

        with self._db() as db:
            row, scope = self._scope(db, job)
        if row["done"]:
            if isinstance(row, dict) and row.get("archived"):
                from .ledger_archive import check_identity

                check_identity(self.completed_receipt(job))
            from g2.offline.stage_a import validate_profile_episode

            validate_profile_episode(row["target"])
            return
        source = read_json(contained(row["target"], "spatial_source.json"))
        for vid, view in sorted(source["views"].items()):
            for owner in view["owners"]:
                with self._db() as db:
                    event = db.execute(
                        "SELECT * FROM events WHERE id=? AND job=?",
                        (owner["event_id"], job),
                    ).fetchone()
                if event is not None:
                    if event["status"] == "failed":
                        raise CacheError("failed event requires explicit retry")
                    continue
                desc = source["final_pixel_events"][owner["event_id"]]
                pixel = final_pixel_event(
                    contained(row["target"], owner["path"]),
                    episode_key=scope["episode_key"],
                    source_fingerprint=scope["source_fingerprint"],
                    profile_id=scope["profile_id"],
                    view_id=vid,
                    canonical_view_id=desc["canonical_view_id"],
                    variant=desc["variant"],
                    expected_size=desc["size_wh"],
                )
                if pixel.descriptor() != desc:
                    raise CacheError("resumed final source differs from sealed event")
                self.enqueue(job, pixel, timeout_s=timeout_s)
        self.seal(job)

    def stats(self):
        with self._db() as db:
            count, size = db.execute(
                "SELECT COUNT(*),COALESCE(SUM(length(png)),0) FROM events WHERE png IS NOT NULL"
            ).fetchone()
            statuses = dict(
                db.execute(
                    "SELECT status,COUNT(*) FROM events GROUP BY status"
                ).fetchall()
            )
            failed = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE error IS NOT NULL"
            ).fetchone()[0]
            unfinished = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE done=0"
            ).fetchone()[0]
            return dict(
                pending_inputs=count,
                pending_bytes=size,
                statuses=statuses,
                failed_jobs=failed,
                unfinished_jobs=unfinished,
                active_jobs=db.execute("SELECT COUNT(*) FROM jobs").fetchone()[0],
                active_records=db.execute("SELECT COUNT(*) FROM events").fetchone()[0],
                completed_jobs=db.execute("SELECT COUNT(*) FROM completed").fetchone()[
                    0
                ],
                cleanup_pending_jobs=db.execute(
                    "SELECT COUNT(*) FROM jobs WHERE done>=1"
                ).fetchone()[0],
            )

    def retry(self, job):
        """Explicit failed-job retry retains pixels and all previously valid ACKs."""
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("UPDATE jobs SET error=NULL WHERE id=?", (job,))
            db.execute(
                "UPDATE events SET status='pending',error=NULL WHERE job=? AND status='failed'",
                (job,),
            )

    def job_status(self, job):
        with self._db() as db:
            row, _ = self._scope(db, job)
            return (
                "complete"
                if row["done"]
                else "sealed"
                if row["sealed"]
                else "source_ready"
                if row["source_ready"]
                else "producing"
            )

    def reap(self, job):
        """ACK chunks may be removed only after a verified final dataset copy."""
        from g2.io import digest
        from g2.offline.stage_a import validate_profile_episode

        from .contract import contained

        with self._db() as db:
            row, _ = self._scope(db, job)
            if not row["done"]:
                raise CacheError(
                    "cannot release results before final verified publication"
                )
            if isinstance(row, dict) and row.get("archived"):
                from .ledger_archive import check_identity

                check_identity(self.completed_receipt(job))
                return True
            events = db.execute("SELECT * FROM events WHERE job=?", (job,)).fetchall()
        if self.source_policy is not None:
            from .source_retirement import resume_pending

            if not resume_pending(self, job):
                return False
        validate_profile_episode(row["target"])
        handoff = None
        if row["completion_receipt"] is not None:
            import json

            from .production import cache_receipt

            handoff = json.loads(row["completion_receipt"])
            from . import final_source as final

            current_cache = cache_receipt(row["target"])
            if current_cache["schema"] == "g2_verified_profile_vae_v2":
                current_cache = final.load_capsule(row["target"])[
                    "working_cache_receipt"
                ]
            if handoff["verified_cache"] != current_cache:
                raise CacheError("completed cache changed after durable stream handoff")
        for event in events:
            adopted = event["status"] == "completed_by_cache" and handoff is not None
            if not adopted and (event["status"] != "acked" or not event["result"]):
                raise CacheError("cannot release an unacknowledged result")
            import json

            desc = json.loads(event["descriptor"])
            expected = (
                "records/"
                + fingerprint(
                    dict(
                        pixel_record_key=desc["pixel_record_key"],
                        recipe_id=self.recipe["recipe_id"],
                    )
                )
                + ".pt"
            )
            result = event["result"] or expected
            if result != expected:
                raise CacheError("result cleanup path is not the owned numeric key")
            with self._db() as db:
                shared = db.execute(
                    "SELECT COUNT(*) FROM events JOIN jobs ON events.job=jobs.id WHERE events.result=? AND events.job!=? AND jobs.done=0",
                    (result, job),
                ).fetchone()[0]
                if not shared:
                    import json

                    pending = db.execute(
                        "SELECT events.descriptor FROM events JOIN jobs ON events.job=jobs.id WHERE events.job!=? AND jobs.done=0 AND events.status IN ('pending','running','failed')",
                        (job,),
                    ).fetchall()
                    key = json.loads(event["descriptor"])["pixel_record_key"]
                    shared = any(
                        json.loads(p[0])["pixel_record_key"] == key for p in pending
                    )
            if shared:
                continue
            path = contained(self.root, result, allow_missing=True)
            if path.exists():
                if (
                    event["result_sha"] is not None
                    and digest(path) != event["result_sha"]
                ):
                    raise CacheError("result changed before release")
                path.unlink()
                from .storage import _fsync_directory

                _fsync_directory(path.parent)
        with self._db() as db:
            db.execute("UPDATE jobs SET done=2 WHERE id=?", (job,))
        from .ledger_archive import archive

        return archive(self, job)

    def completed_receipt(self, job):
        from .ledger_archive import lookup

        with self._db() as db:
            receipt = lookup(self, db, job=job)
        if receipt is None:
            raise CacheError("job has not been archived")
        return receipt

    def adopt_completed(self, job):
        """Accept only a fully audited same-scope/recipe final cache handoff.

        Numerical posthoc completion can legally release temporary PNGs before
        an earlier stream job finishes. Persist this proof and retire its pending
        BLOBs atomically instead of trying to refill missing, released inputs.
        """
        import json

        from g2.io import digest, read_json
        from g2.offline.stage_a import validate_profile_episode

        from .contract import contained
        from .production import cache_receipt, target_lock

        with self._db() as db:
            row, scope = self._scope(db, job, allow_failed=True)
        expected = row["source_ready"] or row["sealed"]
        if expected is None:
            raise CacheError("completion handoff requires a bound offered source")
        try:
            with build_lock(target_lock(row["target"])):
                validate_profile_episode(row["target"])
                source = read_json(contained(row["target"], "spatial_source.json"))
                receipt = cache_receipt(row["target"])
                if (
                    digest(Path(row["target"]) / "spatial_source.json") != expected
                    or receipt["recipe_id"] != self.recipe["recipe_id"]
                    or any(
                        source[k] != scope[k]
                        for k in ("source_fingerprint", "profile_id")
                    )
                    or f"{source['task_class']}/episode_{source['episode_id']:06d}"
                    != scope["episode_key"]
                ):
                    raise CacheError(
                        "posthoc completion source or recipe differs from stream job"
                    )
                proof = dict(
                    schema="g2_stream_completed_cache_handoff_v1",
                    source_sha256=expected,
                    verified_cache=receipt,
                    prior_failure=row["error"],
                )
                with self._db() as db:
                    db.execute("BEGIN IMMEDIATE")
                    db.execute(
                        "UPDATE events SET png=NULL,status=CASE WHEN status='acked' THEN 'acked' ELSE 'completed_by_cache' END,error=NULL WHERE job=?",
                        (job,),
                    )
                    db.execute(
                        "UPDATE jobs SET done=1,error=NULL,completion_receipt=? WHERE id=?",
                        (json.dumps(proof, sort_keys=True), job),
                    )
        except CacheError as exc:
            if isinstance(exc.__cause__, BlockingIOError):
                return False  # Other endpoint still owns publication/cleanup.
            raise
        return self.reap(job)

    def result(self, job, view_id, record, recipe):
        import json

        from .contract import contained
        from .storage import _load, inspect_view_payload

        if recipe != self.recipe:
            raise CacheError("streamed numerical recipe differs from final builder")
        with self._db() as db:
            event = db.execute(
                "SELECT * FROM events WHERE id=? AND job=?", (record["event_id"], job)
            ).fetchone()
        if event is None or event["status"] != "acked":
            raise CacheError("owner has no durable numerical ACK")
        desc = json.loads(event["descriptor"])
        if (
            desc["view_id"] != view_id
            or desc["rgb_sha256"] != record["png_sha256"]
            or desc["pixel_record_key"] != record["pixel_record_key"]
        ):
            raise CacheError("compact owner/event reconciliation differs")
        path = contained(self.root, event["result"])
        info = inspect_view_payload(path)
        if info["sha256"] != event["result_sha"]:
            raise CacheError("ACK numeric chunk changed")
        validate_chunk(info, desc, recipe)
        value, _, _ = _load(path)
        return value["latents"][0].clone(), value["metadata"]["preprocessing"][0]


def validate_event(event):
    validate_descriptor(event.descriptor())
    if hashlib.sha256(event.png_bytes).hexdigest() != event.rgb_sha256:
        raise CacheError("final event bytes differ from sealed descriptor")
    decode_final_png(event.png_bytes, expected_size=event.size_wh)


def validate_descriptor(desc):
    from g2.io import canonical
    from g2.offline.spatial_metadata import asset_identity

    from .storage import _hex

    event = FinalPixelEvent(
        png_bytes=b"",
        **{k: (tuple(v) if k == "size_wh" else v) for k, v in desc.items()},
    )
    _hex(event.source_fingerprint)
    _hex(event.profile_id)
    safe_relative(event.episode_key)
    if len(canonical(desc)) > 16384:
        raise CacheError("final event metadata exceeds finite ledger item budget")
    actual = asset_identity(event.view_id + ".png")
    expected = dict(
        episode_key=event.episode_key,
        view_id=event.view_id,
        rgb_sha256=event.rgb_sha256,
        source_fingerprint=event.source_fingerprint,
        profile_id=event.profile_id,
    )
    if (
        fingerprint(expected) != event.event_id
        or actual["canonical_view_id"] != event.canonical_view_id
        or actual["variant"] != event.variant
        or fingerprint(dict(view_id=event.view_id, rgb_sha256=event.rgb_sha256))
        != event.pixel_record_key
        or desc["final_pixel_phase"]
        != ("FINAL_MARKER_PIXELS" if event.variant == "w_rbs" else "FINAL_CLEAN_PIXELS")
    ):
        raise CacheError("final event identity/content/phase differs")
    if len(event.size_wh) != 2 or any(
        type(v) is not int or v < 1 for v in event.size_wh
    ):
        raise CacheError("final event image dimensions invalid")


def _chunk_metadata(desc, recipe, prep):
    from .contract import PAYLOAD_SCHEMA

    record = dict(
        record_index=0,
        owner_state_ordinal=0,
        owner_state_id=0,
        owner_frame=0,
        png_path=desc["view_id"] + ".png",
        png_sha256=desc["rgb_sha256"],
        original_hw=list(reversed(desc["size_wh"])),
        color_mode="RGB",
    )
    return dict(
        schema=PAYLOAD_SCHEMA,
        episode_key="pixel/" + desc["pixel_record_key"],
        recipe_id=recipe["recipe_id"],
        view_id=desc["view_id"],
        source=dict(
            manifest_sha256=desc["rgb_sha256"],
            complete_sha256=recipe["recipe_id"],
            schema="g2_final_pixel_numeric_v1",
            pixel_record_key=desc["pixel_record_key"],
        ),
        view_plan=dict(
            path=desc["view_id"] + ".pt", records=[record], state_records=[0]
        ),
        preprocessing=[prep],
        record_layout="CHW",
        view_layout="UCHW",
    )


def validate_chunk(info, desc, recipe):
    from .builder import _check_metadata

    prep = info["metadata"]["preprocessing"][0]
    _check_metadata(info["metadata"], _chunk_metadata(desc, recipe, prep), recipe)
    if (
        info["dtype"] != recipe["storage_dtype"]
        or prep.get("latent_shape") != info["shape"][1:]
        or prep.get("storage_conversion", {}).get("to_dtype") != recipe["storage_dtype"]
    ):
        raise CacheError("numeric ACK layout/precision differs from sealed recipe")


class EventConsumer:
    """One independent process reuses one encoder across producer episodes."""

    def __init__(self, spool, encoder, *, failpoint=None):
        self.spool, self.encoder, self.failpoint = spool, encoder, failpoint
        self._result_bytes = None
        if encoder.descriptor() != spool.recipe["encoder"]:
            raise CacheError("consumer encoder differs from spool recipe")

    def step(self):
        """Exclusive consumer; restart replays running records idempotently."""
        from .storage import build_lock

        with build_lock(self.spool.root / "consumer"):
            self.recover_results()
            return self._step()

    def recover_results(self):
        """Under the consumer lock, discard unpublished atomic-write leftovers.

        Hard process exit skips storage's finally. The private .view-*.tmp
        names have no ACK; PNG input remains durable. Removing a leftover hard
        link after publication preserves its .pt name. Count every other real
        file against the budget, rather than silently ignoring unknown bytes.
        """
        from .contract import contained
        from .storage import _fsync_directory

        directory = contained(self.spool.root, "records", allow_missing=True)
        removed, total = 0, 0
        if directory.exists():
            for entry in directory.iterdir():
                path = contained(self.spool.root, "records/" + entry.name)
                if not path.is_file():
                    raise CacheError("unexpected directory in private numeric staging")
                if path.name.startswith(".view-") and path.name.endswith(".tmp"):
                    path.unlink()
                    removed += 1
                else:
                    total += path.stat().st_size
            if removed:
                _fsync_directory(directory)
        self._result_bytes = total
        if total > self.spool.max_result_bytes:
            raise CacheError("existing numeric staging exceeds finite result budget")
        return dict(removed_unpublished_temps=removed, numeric_bytes=total)

    def _step(self):
        import json
        import time
        from io import BytesIO

        import numpy as np
        from PIL import Image

        from .builder import encode_record
        from .contract import contained
        from .production import build_profile
        from .storage import inspect_view_payload, write_view_payload

        if self.encoder.descriptor() != self.spool.recipe["encoder"]:
            raise CacheError("consumer computational identity changed")
        with self.spool._db() as db:
            completed_candidates = db.execute(
                "SELECT id,target FROM jobs WHERE done=0 AND (source_ready IS NOT NULL OR sealed IS NOT NULL) ORDER BY rowid"
            ).fetchall()
            event = db.execute(
                "SELECT events.* FROM events JOIN jobs ON events.job=jobs.id WHERE events.status IN ('pending','running') AND jobs.error IS NULL AND jobs.done=0 ORDER BY events.rowid LIMIT 1"
            ).fetchone()
            job = db.execute(
                "SELECT * FROM jobs WHERE sealed IS NOT NULL AND done=0 AND error IS NULL AND NOT EXISTS (SELECT 1 FROM events WHERE events.job=jobs.id AND events.status!='acked') ORDER BY rowid LIMIT 1"
            ).fetchone()
            cleanup = db.execute(
                "SELECT id FROM jobs WHERE done>=1 AND error IS NULL AND cleanup_after<=? ORDER BY rowid LIMIT 1",
                (time.time(),),
            ).fetchone()
            offered = db.execute(
                "SELECT id FROM jobs WHERE source_ready IS NOT NULL AND sealed IS NULL AND done=0 AND error IS NULL ORDER BY rowid LIMIT 1"
            ).fetchone()
        for candidate in completed_candidates:
            if (Path(candidate["target"]) / "COMPLETE.json").exists():
                try:
                    adopted = self.spool.adopt_completed(candidate["id"])
                    self._result_bytes = None
                    return adopted
                except Exception as exc:
                    with self.spool._db() as db:
                        db.execute(
                            "UPDATE jobs SET error=? WHERE id=?",
                            (str(exc), candidate["id"]),
                        )
                    raise
        if job is None and cleanup is None and offered is not None:
            try:
                return self.spool.refill_one(offered["id"])
            except QueueBackpressure:
                pass  # Drain a pending input below, then retry finite admission.
            except Exception as exc:
                with self.spool._db() as db:
                    db.execute(
                        "UPDATE jobs SET error=? WHERE id=?", (str(exc), offered["id"])
                    )
                raise
        if cleanup is not None:
            progress = self.spool.reap(cleanup["id"])
            self._result_bytes = None
            cleanup = None
            if progress:
                return True
        # Finalize/reap ready episodes while other renderers are still active;
        # requiring global queue idleness would accumulate the entire corpus.
        if event is None or job is not None or cleanup is not None:
            if job is None:
                return False
            try:
                from g2.io import digest

                if digest(Path(job["target"]) / "spatial_source.json") != job["sealed"]:
                    raise CacheError("source changed after production seal")
                build_profile(
                    job["target"],
                    self.encoder,
                    preprocessing=self.spool.recipe["preprocessing"],
                    storage_dtype=self.spool.recipe["storage_dtype"],
                    resume=True,
                    record_provider=lambda vid, record, recipe: self.spool.result(
                        job["id"], vid, record, recipe
                    ),
                    cleanup=True,
                )
                if self.failpoint:
                    self.failpoint("profile_before_ack")
                with self.spool._db() as db:
                    db.execute("UPDATE jobs SET done=1 WHERE id=?", (job["id"],))
                self.spool.reap(job["id"])
                self._result_bytes = None
                return True
            except Exception as exc:
                with self.spool._db() as db:
                    db.execute(
                        "UPDATE jobs SET error=? WHERE id=?", (str(exc), job["id"])
                    )
                raise
        desc = json.loads(event["descriptor"])
        with self.spool._db() as db:
            db.execute(
                "UPDATE events SET status='running' WHERE id=? AND job=?",
                (event["id"], event["job"]),
            )
        try:
            immutable = FinalPixelEvent(
                png_bytes=bytes(event["png"]),
                **{k: (tuple(v) if k == "size_wh" else v) for k, v in desc.items()},
            )
            validate_event(immutable)
            # One private chunk per immutable event; it survives a crash before ACK.
            relative = (
                "records/"
                + fingerprint(
                    dict(
                        pixel_record_key=desc["pixel_record_key"],
                        recipe_id=self.spool.recipe["recipe_id"],
                    )
                )
                + ".pt"
            )
            path = contained(self.spool.root, relative, allow_missing=True)
            if path.exists():
                info = inspect_view_payload(path)
            else:
                with Image.open(BytesIO(immutable.png_bytes)) as image:
                    rgb = np.array(image, copy=True)
                stored, prep = encode_record(self.encoder, rgb, self.spool.recipe)
                if self._result_bytes is None:
                    self.recover_results()
                used = self._result_bytes
                # Conservative file/header reservation; inspect the exact serialized
                # size too before ACK. Exhaustion is explicit, never silent loss.
                if (
                    used + stored.numel() * stored.element_size() + 65536
                    > self.spool.max_result_bytes
                ):
                    raise CacheError("finite numeric staging budget exceeded")
                info = write_view_payload(
                    path,
                    _chunk_metadata(desc, self.spool.recipe, prep),
                    stored.unsqueeze(0),
                )
                self._result_bytes += info["bytes"]
                if self._result_bytes > self.spool.max_result_bytes:
                    raise CacheError("numeric staging budget exceeded; input retained")
            validate_chunk(info, desc, self.spool.recipe)
            if self.encoder.descriptor() != self.spool.recipe["encoder"]:
                raise CacheError(
                    "consumer computational identity changed during Encode1"
                )
            if self.failpoint:
                self.failpoint("numeric_before_ack")
            with self.spool._db() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "UPDATE events SET status='acked',result=?,result_sha=?,png=NULL,error=NULL WHERE id=? AND job=?",
                    (relative, info["sha256"], event["id"], event["job"]),
                )
            return True
        except Exception as exc:
            with self.spool._db() as db:
                db.execute(
                    "UPDATE events SET status='failed',error=? WHERE id=? AND job=?",
                    (str(exc), event["id"], event["job"]),
                )
                db.execute(
                    "UPDATE jobs SET error=? WHERE id=?", (str(exc), event["job"])
                )
            raise


def publish_final_pixels(
    stage, report, sink, *, episode_key, source_fingerprint, profile_id
):
    """Called only after final material/background and variant-specific overlay.

    ARROW_ONLY admits marked pixels only; REUSE_ALL admits nothing. Physical
    repeated bytes are idempotent; compact owners are reconciled at source seal.
    """
    from g2.offline.spatial_metadata import asset_identity

    from .contract import contained

    assets = report.get("views", [])
    materialized = set(
        report.get("scene_materialized_views", [a["rgb_file"] for a in assets])
    )
    for asset in assets:
        if asset["rgb_file"] not in materialized:
            continue
        identity = asset_identity(asset["rgb_file"])
        event = final_pixel_event(
            contained(stage, asset["rgb_file"]),
            episode_key=episode_key,
            source_fingerprint=source_fingerprint,
            profile_id=profile_id,
            view_id=identity["view_id"],
            canonical_view_id=identity["canonical_view_id"],
            variant=identity["variant"],
        )
        if event.rgb_sha256 != asset["sha256"]:
            raise CacheError("renderer report changed after final pixel publication")
        sink(event)


def producer_sink(spool_root, job, *, diagnostic_path=None):
    spool = EventSpool.open(spool_root)
    with spool._db() as db:
        _, scope = spool._scope(db, job, allow_failed=True)
    sink = (
        (lambda event: spool.deliver(job, event, diagnostic_path))
        if diagnostic_path is not None
        else (lambda event: spool.enqueue(job, event))
    )
    return spool, scope, sink
