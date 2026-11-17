"""SQLite stress uses tiny synthetic acknowledged rows, not fake GPU acceptance."""

from __future__ import annotations

import hashlib
import json
import multiprocessing
import os
import threading
from pathlib import Path

import pytest

from g2.io import digest, write_json
from g2.latent_cache import ledger_archive
from g2.latent_cache.contract import CacheError, fingerprint, make_recipe
from g2.latent_cache.streaming import EventSpool, final_pixel_event
from g2.tests.test_view_vae_builder import PREPROCESS, FakeEncoder


def sql_spool(tmp_path, records=128):
    return EventSpool(
        tmp_path / "spool",
        make_recipe(FakeEncoder().descriptor(), PREPROCESS),
        max_records=records,
    )


def seed_verified_rows(spool, root, eid, n=1):
    """Only the SQL residency boundary is simulated. Real full proof is tested
    by the unchanged A2 integration tests; no production verifier is bypassable.
    """
    from PIL import Image

    target = root / f"episode_{eid:06d}"
    target.mkdir(parents=True)
    png = target / "TEST_ONLY.png"
    Image.new("RGB", (2, 2), (12, 34, 56)).save(png)
    source_fp = hashlib.sha256(str(eid).encode()).hexdigest()
    profile = "b" * 64
    key = f"NavigateKitchen/episode_{eid:06d}"
    job = spool.register(
        target, episode_key=key, source_fingerprint=source_fp, profile_id=profile
    )
    event = final_pixel_event(
        png,
        episode_key=key,
        source_fingerprint=source_fp,
        profile_id=profile,
        view_id="sixview/floor_top",
        canonical_view_id="sixview/floor_top",
        variant="clean",
    )
    write_json(
        target / "spatial_source.json",
        dict(
            scope="TEST_ONLY_SQLITE_ACKNOWLEDGED_ROW_SIMULATION",
            final_pixel_events={event.event_id: event.descriptor()},
        ),
    )
    sha = digest(target / "spatial_source.json")
    rows = []
    for i in range(n):
        ident = event.event_id if i == 0 else fingerprint(dict(job=job, i=i))
        rows.append(
            (ident, job, json.dumps(event.descriptor()), None, "completed_by_cache")
        )
    with spool._db() as db:
        db.execute("BEGIN IMMEDIATE")
        db.executemany(
            "INSERT INTO events(id,job,descriptor,png,status) VALUES(?,?,?,?,?)", rows
        )
        db.execute("UPDATE jobs SET done=2,source_ready=? WHERE id=?", (sha, job))
    return job, target, event


def sqlite_only_proof(row, scope):
    target = Path(row["target"])
    return dict(
        scope="TEST_ONLY_SQLITE_BOUNDARY_NOT_SOURCE_OR_VAE_ACCEPTANCE",
        source_id="c" * 64,
        verified_cache=dict(
            recipe_id=scope["recipe_id"], cache_manifest_sha256="d" * 64
        ),
        identity_files={"spatial_source.json": digest(target / "spatial_source.json")},
        profile_complete=True,
    )


def test_over_100k_events_1001_jobs_bounded_active_working_set(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_archive, "published_proof", sqlite_only_proof)
    spool = sql_spool(tmp_path, 128)
    peak_events = peak_jobs = 0
    for eid in range(1001):
        job, target, event = seed_verified_rows(spool, tmp_path / "dataset", eid, 101)
        stats = spool.stats()
        peak_events = max(peak_events, stats["active_records"])
        peak_jobs = max(peak_jobs, stats["active_jobs"])
        assert ledger_archive.archive(spool, job)
        assert spool.stats()["active_records"] == spool.stats()["active_jobs"] == 0
    assert 1001 * 101 > 100000 and peak_events == 101 and peak_jobs == 1
    assert spool.stats()["completed_jobs"] == 1001
    # Cumulative records exceed the old100k while the cap remains128.
    assert spool.max_records == 128
    record = spool.completed_receipt(job)
    scope = json.loads(record["job"]["scope"])
    assert (
        spool.register(
            target,
            **{
                k: scope[k] for k in ("episode_key", "source_fingerprint", "profile_id")
            },
        )
        == job
    )
    assert spool.enqueue(job, event, timeout_s=0) == "completed_by_cache"
    assert spool.job_status(job) == "complete"
    with pytest.raises(CacheError, match="another source"):
        spool.register(
            target,
            episode_key=scope["episode_key"],
            source_fingerprint="e" * 64,
            profile_id=scope["profile_id"],
        )
    with pytest.raises(CacheError, match="recipe or limits"):
        EventSpool(
            spool.root,
            make_recipe(FakeEncoder(identity="b").descriptor(), PREPROCESS),
            max_records=128,
        )
    result = dict(
        logical_events=101101,
        jobs=1001,
        max_records=128,
        peak_active_events=peak_events,
        peak_active_jobs=peak_jobs,
        database_bytes=spool.database.stat().st_size,
        scope="SQLITE_STRESS_NOT_RENDER_THROUGHPUT",
    )
    write_json(tmp_path / "stress_receipt.json", result)


def _crash_gc(spool_root, job, phase):
    ledger_archive.published_proof = sqlite_only_proof
    spool = EventSpool.open(spool_root)

    def crash(point):
        if point == phase:
            os._exit(77)

    ledger_archive.archive(spool, job, failpoint=crash)


@pytest.mark.parametrize(
    "phase", ["receipt_before_gc", "gc_before_commit", "gc_after_commit"]
)
def test_gc_hard_crash_is_atomic_and_idempotent(tmp_path, monkeypatch, phase):
    monkeypatch.setattr(ledger_archive, "published_proof", sqlite_only_proof)
    spool = sql_spool(tmp_path)
    job, target, event = seed_verified_rows(spool, tmp_path / "data", 0, 3)
    ctx = multiprocessing.get_context("fork")
    child = ctx.Process(target=_crash_gc, args=(str(spool.root), job, phase))
    child.start()
    child.join(15)
    assert child.exitcode == 77
    assert EventSpool.open(spool.root).job_status(job) == "complete"
    assert ledger_archive.archive(spool, job)
    assert spool.stats()["completed_jobs"] == 1 and spool.stats()["active_records"] == 0
    assert spool.enqueue(job, event) == "completed_by_cache"


def test_concurrent_reader_and_two_gc_writers_preserve_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_archive, "published_proof", sqlite_only_proof)
    spool = sql_spool(tmp_path)
    job, _, _ = seed_verified_rows(spool, tmp_path / "data", 0, 10)
    entered = threading.Event()
    release = threading.Event()
    errors = []

    def pause(point):
        if point == "gc_before_commit":
            entered.set()
            assert release.wait(5)

    def writer():
        try:
            ledger_archive.archive(spool, job, failpoint=pause)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=writer)
    thread.start()
    assert entered.wait(5)
    assert spool.job_status(job) == "complete"  # Reads precommit snapshot.
    with pytest.raises(CacheError, match="another builder"):
        ledger_archive.archive(spool, job)
    release.set()
    thread.join(5)
    assert not thread.is_alive() and not errors
    assert spool.job_status(job) == "complete" and spool.stats()["completed_jobs"] == 1


def test_pending_inputs_and_damaged_tombstones_never_reclaim(tmp_path, monkeypatch):
    monkeypatch.setattr(ledger_archive, "published_proof", sqlite_only_proof)
    spool = sql_spool(tmp_path)
    job, target, event = seed_verified_rows(spool, tmp_path / "data", 0)
    with spool._db() as db:
        db.execute(
            "UPDATE events SET status='pending',png=? WHERE job=?", (b"retained", job)
        )
    with pytest.raises(CacheError, match="unacknowledged"):
        ledger_archive.archive(spool, job)
    assert spool.stats()["pending_inputs"] == 1
    with spool._db() as db:
        db.execute(
            "UPDATE events SET status='completed_by_cache',png=NULL WHERE job=?", (job,)
        )
    ledger_archive.archive(spool, job)
    with spool._db() as db:
        path = db.execute(
            "SELECT receipt_path FROM completed WHERE id=?", (job,)
        ).fetchone()[0]
    (spool.root / path).write_text("{}")
    with pytest.raises(CacheError, match="tombstone"):
        spool.job_status(job)
    with pytest.raises(CacheError, match="tombstone"):
        spool.register(
            target,
            episode_key=event.episode_key,
            source_fingerprint=event.source_fingerprint,
            profile_id=event.profile_id,
        )
