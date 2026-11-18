"""Bounded CPU-only Episode finalization for the persistent batch engine.

The coordinator retains the per-Episode publication lease. A spawned child
uses the unchanged verified build / handoff / archive protocol for one pinned
job. The child never encodes RGB or uses GPU and only handles posthoc Stage B.
Its SQLite and output commits are durable and replayable after interruption.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .contract import CacheError


class DescriptorOnlyEncoder:
    """A build-only descriptor, never a substitute for numerical encoding."""

    def __init__(self, descriptor):
        self._descriptor = descriptor

    def descriptor(self):
        import copy

        return copy.deepcopy(self._descriptor)

    def encode(self, *_args, **_kwargs):
        raise CacheError("CPU finalizer must never encode a pixel")


def cpu_initializer():
    """Exclude CUDA from spawned cache assembly/verification processes."""
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["COSMOS_DEVICE"] = "cpu"
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"


def finalize_job(spool_root, job_id, expected_recipe_id):
    """Finalize one *already sealed* posthoc job using original durable APIs."""
    from .batch_queue import BatchQueue
    from .ledger_archive import check_identity, lookup
    from .production import build_profile, cache_receipt
    from .streaming import EventSpool

    spool = EventSpool.open(Path(spool_root))
    if (
        not spool.view_first
        or spool.source_policy is not None
        or spool.recipe["recipe_id"] != expected_recipe_id
    ):
        raise CacheError("CPU finalizer refuses foreign lifecycle or recipe")

    with spool._db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if row is None:
            record = lookup(spool, db, job=job_id)
            if record is None:
                raise CacheError("finalization job missing from durable ledger")
            check_identity(record)
            return {"job": job_id, "archived": True}
        row = dict(row)

    if row["error"]:
        raise CacheError("finalizer refuses failed job: " + row["error"])
    if row["done"] == 0:
        if not row["sealed"] or not row["source_ready"]:
            raise CacheError("finalizer requires sealed published source")
        queue = BatchQueue(spool, _initialize=False)
        if not queue.finalizable(job_id):
            raise CacheError("finalizer requires every numerical batch complete")
        encoder = DescriptorOnlyEncoder(spool.recipe["encoder"])
        build_profile(
            row["target"],
            encoder,
            preprocessing=spool.recipe["preprocessing"],
            storage_dtype="float32",
            resume=True,
            record_provider=lambda vid, record, recipe: spool.result(
                job_id, vid, record, recipe
            ),
            cleanup=True,
            posthoc=True,
            _recipe=spool.recipe,
        )
        receipt = cache_receipt(row["target"])
        with spool._db() as db:
            # Re-check the live row inside the durable handoff transaction.
            current = db.execute(
                "SELECT source_ready,sealed,done,error,scope FROM jobs WHERE id=?",
                (job_id,),
            ).fetchone()
            if (
                current is None
                or current["done"] != 0
                or current["error"]
                or current["source_ready"] != row["source_ready"]
                or current["sealed"] != row["sealed"]
                or current["scope"] != row["scope"]
            ):
                raise CacheError("concurrent finalization changed job source")
            audit = [
                dict(batch_id=r["id"], attempts=json.loads(r["attempts"]))
                for r in db.execute(
                    "SELECT DISTINCT b.id,b.attempts FROM engine_batches b "
                    "JOIN engine_members m ON m.batch=b.id WHERE m.job=?",
                    (job_id,),
                )
            ]
            handoff = dict(
                schema="g2_batch_verified_cache_handoff_v1",
                verified_cache=receipt,
                numerical_executions=audit,
            )
            db.execute(
                "UPDATE jobs SET done=1,completion_receipt=? WHERE id=?",
                (json.dumps(handoff, sort_keys=True), job_id),
            )
    # Owned work cleanup can legitimately defer archival while keeping the
    # numerical COMPLETE and its durable handoff. The manager re-enqueues this
    # done row after the cleanup deadline without re-encoding or overwriting.
    return {"job": job_id, "archived": bool(spool.reap(job_id))}
