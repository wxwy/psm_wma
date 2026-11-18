"""Batch/lease extension of EventSpool's existing authoritative SQLite queue.

Only short SQL transactions run under the database writer lock. GPU work and
numeric fsync run outside it. Immutable ordered membership survives retries.
"""

from __future__ import annotations

import json
import os
import time
import uuid

from g2.io import canonical

from .batch_contract import make_context, record_path, validate_context
from .contract import CacheError, contained


def initialize_schema(spool):
    with spool._db() as db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS engine_batches (id TEXT PRIMARY KEY,context TEXT NOT NULL,state TEXT NOT NULL,worker TEXT,token TEXT,lease_until REAL NOT NULL DEFAULT 0,started REAL,attempts TEXT NOT NULL DEFAULT '[]',error TEXT,reserved_bytes INTEGER NOT NULL)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engine_members (job TEXT NOT NULL,event TEXT NOT NULL,ready_at REAL NOT NULL,batch TEXT,position INTEGER,PRIMARY KEY(job,event),UNIQUE(batch,position))"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS engine_member_batch ON engine_members(batch)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engine_workers (id TEXT PRIMARY KEY,gpu TEXT NOT NULL,pid INTEGER NOT NULL,seen REAL NOT NULL,state TEXT NOT NULL,claims INTEGER NOT NULL DEFAULT 0)"
        )
        db.execute(
            "CREATE TABLE IF NOT EXISTS engine_metrics (gpu TEXT PRIMARY KEY,value TEXT NOT NULL)"
        )


def admitted(db, job, event, now):
    db.execute(
        "INSERT INTO engine_members(job,event,ready_at) VALUES(?,?,?)",
        (job, event, now),
    )


def reservation(context):
    return len(context["members"]) * (
        48 * 16 * 16 * 4 + 16384 + 2 * len(canonical(context))
    )


class BatchQueue:
    def __init__(
        self, spool, *, lease_s=60, batch_wait_ms=500, clock=time.time, _initialize=True
    ):
        from .batch_contract import is_batch

        if not is_batch(spool.recipe):
            raise CacheError("batch queue requires a distinct versioned batch recipe")
        if not 1 <= lease_s <= 3600 or not 0 <= batch_wait_ms <= 60000:
            raise CacheError("finite positive lease and bounded batch wait required")
        self.spool, self.lease_s, self.wait_s, self.clock = (
            spool,
            lease_s,
            batch_wait_ms / 1000,
            clock,
        )
        if _initialize:
            initialize_schema(spool)

    def register_worker(self, worker, gpu, pid=None):
        with self.spool._db() as db:
            db.execute(
                "INSERT INTO engine_workers(id,gpu,pid,seen,state) VALUES(?,?,?,?, 'idle')",
                (worker, str(gpu), pid or os.getpid(), self.clock()),
            )

    def heartbeat(self, worker, batch=None, token=None):
        now = self.clock()
        with self.spool._db() as db:
            db.execute("UPDATE engine_workers SET seen=? WHERE id=?", (now, worker))
            if batch is not None:
                changed = db.execute(
                    "UPDATE engine_batches SET lease_until=? WHERE id=? AND worker=? AND token=? AND state='running' AND lease_until>=?",
                    (now + self.lease_s, batch, worker, token, now),
                ).rowcount
                if changed != 1:
                    finished = db.execute(
                        "SELECT state,token FROM engine_batches WHERE id=?", (batch,)
                    ).fetchone()
                    if (
                        finished is not None
                        and finished["state"] == "complete"
                        and finished["token"] == token
                    ):
                        return
                    raise CacheError("worker lost its fenced batch lease")

    def claim(self, worker, *, flush=False):
        now = self.clock()
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            active = db.execute(
                "SELECT * FROM engine_workers WHERE id=?", (worker,)
            ).fetchone()
            if active is None:
                raise CacheError("batch worker was not registered")
            db.execute("UPDATE engine_workers SET seen=? WHERE id=?", (now, worker))
            # Fair admission across live idle GPUs, without a lock around encode.
            preferred = db.execute(
                "SELECT id FROM engine_workers WHERE seen>=? AND state='idle' ORDER BY claims,id LIMIT 1",
                (now - self.lease_s,),
            ).fetchone()
            if preferred is not None and preferred[0] != worker:
                return None
            previous = db.execute(
                "SELECT * FROM engine_batches WHERE state='ready' OR (state='running' AND lease_until<?) ORDER BY rowid LIMIT 1",
                (now,),
            ).fetchone()
            if previous is None:
                rows = db.execute(
                    "SELECT e.job,e.id,e.descriptor,m.ready_at FROM engine_members m JOIN events e ON e.job=m.job AND e.id=m.event JOIN jobs j ON j.id=e.job WHERE m.batch IS NULL AND e.status='pending' AND j.done=0 AND j.error IS NULL ORDER BY m.ready_at,e.rowid LIMIT ?",
                    (self.spool.recipe["batch_size"],),
                ).fetchall()
                if not rows or (
                    len(rows) < self.spool.recipe["batch_size"]
                    and not flush
                    and now - rows[0]["ready_at"] < self.wait_s
                ):
                    return None
                context = make_context(
                    self.spool.recipe,
                    [
                        dict(job=r["job"], event=json.loads(r["descriptor"]))
                        for r in rows
                    ],
                )
                reserve = reservation(context)
                used = db.execute(
                    "SELECT COALESCE(SUM(reserved_bytes),0) FROM engine_batches"
                ).fetchone()[0]
                if reserve + used > self.spool.max_result_bytes:
                    return (
                        None  # Persistent numeric backpressure, never discard inputs.
                    )
                db.execute(
                    "INSERT INTO engine_batches(id,context,state,reserved_bytes) VALUES(?,?,'ready',?)",
                    (context["batch_id"], json.dumps(context, sort_keys=True), reserve),
                )
                for position, row in enumerate(rows):
                    db.execute(
                        "UPDATE engine_members SET batch=?,position=? WHERE job=? AND event=? AND batch IS NULL",
                        (context["batch_id"], position, row["job"], row["id"]),
                    )
                previous = db.execute(
                    "SELECT * FROM engine_batches WHERE id=?", (context["batch_id"],)
                ).fetchone()
            context = json.loads(previous["context"])
            validate_context(context, self.spool.recipe)
            attempts = json.loads(previous["attempts"])
            if len(attempts) >= 64:
                raise CacheError("batch retry audit budget exhausted; retain source")
            token = uuid.uuid4().hex
            ready = [
                r[0]
                for r in db.execute(
                    "SELECT ready_at FROM engine_members WHERE batch=? ORDER BY position",
                    (context["batch_id"],),
                )
            ]
            wait = dict(
                min_seconds=max(0, now - max(ready)),
                max_seconds=max(0, now - min(ready)),
            )
            attempts.append(
                dict(
                    token=token,
                    worker=worker,
                    gpu=active["gpu"],
                    started=now,
                    queue_wait=wait,
                )
            )
            db.execute(
                "UPDATE engine_batches SET state='running',worker=?,token=?,lease_until=?,started=?,attempts=?,error=NULL WHERE id=?",
                (
                    worker,
                    token,
                    now + self.lease_s,
                    now,
                    json.dumps(attempts, sort_keys=True),
                    context["batch_id"],
                ),
            )
            db.execute(
                "UPDATE engine_workers SET state='running',claims=claims+1 WHERE id=?",
                (worker,),
            )
            db.execute(
                "UPDATE events SET status='running' WHERE (job,id) IN (SELECT job,event FROM engine_members WHERE batch=?) AND status!='acked'",
                (context["batch_id"],),
            )
            return dict(
                context=context,
                token=token,
                worker=worker,
                gpu=active["gpu"],
                reserved_bytes=previous["reserved_bytes"],
                queue_wait=wait,
            )

    def _fence(self, db, batch, token):
        row = db.execute("SELECT * FROM engine_batches WHERE id=?", (batch,)).fetchone()
        if (
            row is None
            or row["state"] != "running"
            or row["token"] != token
            or row["lease_until"] < self.clock()
        ):
            raise CacheError("stale batch lease cannot publish or ACK")
        return row

    def fence(self, batch, token):
        with self.spool._db() as db:
            return dict(self._fence(db, batch, token))

    def native_attempt(self, claim, completed=None):
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._fence(db, claim["context"]["batch_id"], claim["token"])
            attempts = json.loads(row["attempts"])
            actual = next(a for a in attempts if a["token"] == claim["token"])
            actual["native_input_shape"] = claim["context"]["input_shape"]
            if completed is None:
                actual["native_started"] = self.clock()
            else:
                actual["native_completed"] = self.clock()
                actual["metrics"] = completed
            db.execute(
                "UPDATE engine_batches SET attempts=? WHERE id=?",
                (json.dumps(attempts, sort_keys=True), row["id"]),
            )

    def expire_dead_worker(self, pid):
        """Coordinator calls only after its own Process has exited/joined."""
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            workers = [
                r[0]
                for r in db.execute("SELECT id FROM engine_workers WHERE pid=?", (pid,))
            ]
            for worker in workers:
                db.execute(
                    "UPDATE engine_batches SET state='ready',worker=NULL,token=NULL,lease_until=0 WHERE worker=? AND state='running'",
                    (worker,),
                )
                db.execute(
                    "UPDATE engine_workers SET state='stopped',seen=0 WHERE id=?",
                    (worker,),
                )

    def inputs(self, claim):
        context, token = claim["context"], claim["token"]
        with self.spool._db() as db:
            self._fence(db, context["batch_id"], token)
            result = []
            for member in context["members"]:
                event = member["event"]
                row = db.execute(
                    "SELECT descriptor,png FROM events WHERE job=? AND id=?",
                    (member["job"], event["event_id"]),
                ).fetchone()
                if (
                    row is None
                    or json.loads(row["descriptor"]) != event
                    or row["png"] is None
                ):
                    raise CacheError(
                        "fixed-batch replay lost an input; never change members"
                    )
                result.append(bytes(row["png"]))
        return result

    def expected(self, job, event):
        with self.spool._db() as db:
            row = db.execute(
                "SELECT b.context,m.position,b.state FROM engine_members m JOIN engine_batches b ON b.id=m.batch WHERE m.job=? AND m.event=?",
                (job, event),
            ).fetchone()
        if row is None:
            raise CacheError("numeric event has no immutable batch assignment")
        context = json.loads(row["context"])
        validate_context(context, self.spool.recipe)
        member = context["members"][row["position"]]
        if member["job"] != job or member["event"]["event_id"] != event:
            raise CacheError("batch assignment differs from original event")
        return context, row["position"], record_path(context, row["position"])

    def ack(self, claim, position, file_sha):
        context, token = claim["context"], claim["token"]
        member = context["members"][position]
        name = record_path(context, position)
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._fence(db, context["batch_id"], token)
            row = db.execute(
                "SELECT * FROM events WHERE job=? AND id=?",
                (member["job"], member["event"]["event_id"]),
            ).fetchone()
            if row is None or json.loads(row["descriptor"]) != member["event"]:
                raise CacheError("ACK event source changed")
            if row["status"] == "acked" and (
                row["result"] != name or row["result_sha"] != file_sha
            ):
                raise CacheError("retry attempted a silent numerical replacement")
            # Keep *all* input BLOBs until the whole immutable batch is durable.
            db.execute(
                "UPDATE events SET status='acked',result=?,result_sha=?,error=NULL WHERE job=? AND id=?",
                (name, file_sha, member["job"], member["event"]["event_id"]),
            )

    def complete(self, claim, metrics):
        context, token = claim["context"], claim["token"]
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._fence(db, context["batch_id"], token)
            incomplete = db.execute(
                "SELECT COUNT(*) FROM engine_members m JOIN events e ON e.job=m.job AND e.id=m.event WHERE m.batch=? AND (e.status!='acked' OR e.result IS NULL OR e.result_sha IS NULL)",
                (context["batch_id"],),
            ).fetchone()[0]
            if incomplete:
                raise CacheError(
                    "whole-batch completion requires every durable per-record ACK"
                )
            db.execute(
                "UPDATE engine_batches SET state='complete',lease_until=0 WHERE id=?",
                (context["batch_id"],),
            )
            db.execute(
                "UPDATE engine_workers SET state='idle',seen=? WHERE id=?",
                (self.clock(), claim["worker"]),
            )
            db.execute(
                "UPDATE events SET png=NULL WHERE (job,id) IN (SELECT job,event FROM engine_members WHERE batch=?)",
                (context["batch_id"],),
            )
            previous = db.execute(
                "SELECT value FROM engine_metrics WHERE gpu=?", (str(claim["gpu"]),)
            ).fetchone()
            value = (
                json.loads(previous[0])
                if previous
                else dict(
                    batches=0,
                    records=0,
                    batch_histogram={},
                    encode_seconds=0.0,
                    io_ack_seconds=0.0,
                    peak_allocated_bytes=0,
                    peak_reserved_bytes=0,
                )
            )
            count = len(context["members"])
            value["batches"] += 1
            value["records"] += count
            native = bool(metrics.get("native_called"))
            value["native_batches"] = value.get("native_batches", 0) + int(native)
            value["native_records"] = value.get("native_records", 0) + (
                count if native else 0
            )
            value["native_cuda_ms"] = value.get("native_cuda_ms", 0) + (
                metrics.get("native_cuda_ms") or 0
            )
            value["max_queue_wait_seconds"] = max(
                value.get("max_queue_wait_seconds", 0),
                claim["queue_wait"]["max_seconds"],
            )
            value["batch_histogram"][str(count)] = (
                value["batch_histogram"].get(str(count), 0) + 1
            )
            for key in ("encode_seconds", "io_ack_seconds"):
                value[key] += metrics[key]
            for key in ("peak_allocated_bytes", "peak_reserved_bytes"):
                value[key] = max(value[key], metrics[key])
            db.execute(
                "INSERT INTO engine_metrics(gpu,value) VALUES(?,?) ON CONFLICT(gpu) DO UPDATE SET value=excluded.value",
                (str(claim["gpu"]), json.dumps(value, sort_keys=True)),
            )

    def fail(self, claim, error):
        context = claim["context"]
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                self._fence(db, context["batch_id"], claim["token"])
            except CacheError:
                return  # A stale worker cannot poison its successor.
            db.execute(
                "UPDATE engine_batches SET state='failed',error=?,lease_until=0 WHERE id=?",
                (str(error), context["batch_id"]),
            )
            db.execute(
                "UPDATE engine_workers SET state='idle' WHERE id=?", (claim["worker"],)
            )
            db.execute(
                "UPDATE events SET status='failed',error=? WHERE (job,id) IN (SELECT job,event FROM engine_members WHERE batch=?) AND status!='acked'",
                (str(error), context["batch_id"]),
            )
            for job in {m["job"] for m in context["members"]}:
                db.execute("UPDATE jobs SET error=? WHERE id=?", (str(error), job))

    def retry_failed(self):
        with self.spool._db() as db:
            db.execute("BEGIN IMMEDIATE")
            for row in db.execute(
                "SELECT id FROM engine_batches WHERE state='failed'"
            ).fetchall():
                db.execute(
                    "UPDATE engine_batches SET state='ready',error=NULL,worker=NULL,token=NULL,lease_until=0 WHERE id=?",
                    (row["id"],),
                )
                db.execute(
                    "UPDATE events SET status='pending',error=NULL WHERE (job,id) IN (SELECT job,event FROM engine_members WHERE batch=?) AND status='failed'",
                    (row["id"],),
                )
                db.execute(
                    "UPDATE jobs SET error=NULL WHERE id IN (SELECT job FROM engine_members WHERE batch=?)",
                    (row["id"],),
                )

    def finalizable(self, job):
        with self.spool._db() as db:
            return not db.execute(
                "SELECT 1 FROM engine_members m LEFT JOIN engine_batches b ON b.id=m.batch WHERE m.job=? AND (m.batch IS NULL OR b.state!='complete') LIMIT 1",
                (job,),
            ).fetchone()

    def stats(self):
        with self.spool._db() as db:
            return dict(
                batch_states=dict(
                    db.execute(
                        "SELECT state,COUNT(*) FROM engine_batches GROUP BY state"
                    ).fetchall()
                ),
                gpu={
                    r["gpu"]: json.loads(r["value"])
                    for r in db.execute("SELECT * FROM engine_metrics")
                },
                reserved_numeric_bytes=db.execute(
                    "SELECT COALESCE(SUM(reserved_bytes),0) FROM engine_batches"
                ).fetchone()[0],
                pending_members=db.execute(
                    "SELECT COUNT(*) FROM engine_members WHERE batch IS NULL"
                ).fetchone()[0],
            )

    def capacity_pressure(self):
        """Report admission pressure without changing an immutable batch/budget."""
        with self.spool._db() as db:
            rows = db.execute(
                "SELECT e.job,e.descriptor FROM engine_members m JOIN events e ON e.job=m.job AND e.id=m.event JOIN jobs j ON j.id=e.job WHERE m.batch IS NULL AND e.status='pending' AND j.done=0 AND j.error IS NULL ORDER BY m.ready_at,e.rowid LIMIT ?",
                (self.spool.recipe["batch_size"],),
            ).fetchall()
            used = db.execute(
                "SELECT COALESCE(SUM(reserved_bytes),0) FROM engine_batches"
            ).fetchone()[0]
        required = (
            reservation(
                make_context(
                    self.spool.recipe,
                    [
                        dict(job=r["job"], event=json.loads(r["descriptor"]))
                        for r in rows
                    ],
                )
            )
            if rows
            else 0
        )
        return dict(
            blocked=bool(rows) and used + required > self.spool.max_result_bytes,
            required_bytes=required,
            reserved_bytes=used,
            limit_bytes=self.spool.max_result_bytes,
        )

    def collect(self):
        """Only batches whose every job has a verified existing tombstone may go."""
        from .storage import build_lock

        with self.spool._db() as db:
            rows = db.execute(
                "SELECT id FROM engine_batches b WHERE b.state='complete' AND NOT EXISTS(SELECT 1 FROM engine_members m JOIN jobs j ON j.id=m.job WHERE m.batch=b.id)"
            ).fetchall()
        for row in rows:
            key = row["id"]
            try:
                with build_lock(self.spool.root / "batch_locks" / key):
                    from .ledger_archive import lookup

                    with self.spool._db() as db:
                        jobs = db.execute(
                            "SELECT DISTINCT job FROM engine_members WHERE batch=?",
                            (key,),
                        ).fetchall()
                        if any(lookup(self.spool, db, job=j[0]) is None for j in jobs):
                            raise CacheError(
                                "batch GC requires genuine verified completed-job receipts"
                            )
                    directory = contained(
                        self.spool.root, "records/" + key, allow_missing=True
                    )
                    if directory.exists():
                        if any(directory.iterdir()):
                            raise CacheError(
                                "completed batch still has unverified numeric staging"
                            )
                        directory.rmdir()
                        from .storage import _fsync_directory

                        _fsync_directory(directory.parent)
                    with self.spool._db() as db:
                        db.execute("BEGIN IMMEDIATE")
                        if db.execute(
                            "SELECT 1 FROM engine_members m JOIN jobs j ON j.id=m.job WHERE m.batch=?",
                            (key,),
                        ).fetchone():
                            continue
                        db.execute("DELETE FROM engine_members WHERE batch=?", (key,))
                        db.execute(
                            "DELETE FROM engine_batches WHERE id=? AND state='complete'",
                            (key,),
                        )
            except CacheError as exc:
                if not isinstance(exc.__cause__, BlockingIOError):
                    raise


def expected_result(spool, job, event, descriptor):
    from .batch_contract import is_batch
    from .contract import fingerprint

    if is_batch(spool.recipe):
        return BatchQueue(spool, _initialize=False).expected(job, event)[2]
    return (
        "records/"
        + fingerprint(
            dict(
                pixel_record_key=descriptor["pixel_record_key"],
                recipe_id=spool.recipe["recipe_id"],
            )
        )
        + ".pt"
    )
