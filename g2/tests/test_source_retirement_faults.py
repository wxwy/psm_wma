"""Real process exits at source-transaction boundaries on synthetic CPU data."""

from __future__ import annotations

import errno
import json
import multiprocessing
import os
import threading
from pathlib import Path

import pytest

from g2.io import digest, read_json, write_json
from g2.latent_cache import final_source as final
from g2.latent_cache import ledger_archive, source_retirement
from g2.latent_cache.contract import CacheError
from g2.latent_cache.storage import open_episode_index
from g2.latent_cache.streaming import EventSpool, final_pixel_event
from g2.offline.stage_a import validate_profile_episode
from g2.tests.test_source_capsule import capsule_case, complete_working


def acknowledged_job(tmp_path, monkeypatch):
    case = capsule_case(tmp_path)
    kwargs, target, encoder, spool, job = case
    complete_working(kwargs, target, encoder, spool, job)
    # Hold exactly the collector boundary, after the real full cache handoff
    # and durable ACK. No source/numeric verifier or ACK is simulated here.
    with monkeypatch.context() as patch:
        patch.setattr(ledger_archive, "archive", lambda *a, **k: False)
        assert not spool.adopt_completed(job)
    with spool._db() as db:
        assert db.execute("SELECT done FROM jobs WHERE id=?", (job,)).fetchone()[0] == 2
    return case


def _hard_exit(spool_root, job, phase):
    spool = EventSpool.open(spool_root)

    def fail(point):
        if point == phase:
            os._exit(77)

    ledger_archive.archive(spool, job, failpoint=fail)


PHASES = [
    "capsule_intent_bound",
    "capsule_before_intent_write",
    "capsule_intent_fsynced",
    "capsule_before_write:spatial_source_index.json",
    "capsule_published:spatial_source_index.json",
    "capsule_published:SPATIAL_SOURCE_FINAL_READY.json",
    "capsule_published:vae_cache/manifest.json",
    "capsule_published:vae_cache/COMPLETE.json",
    "capsule_published:episode_manifest.json",
    "capsule_published:SOURCE_RETIREMENT.json",
    "capsule_verified_before_retire",
    "capsule_before_source_rename:spatial_source.json",
    "capsule_source_renamed:spatial_source.json",
    "capsule_before_source_delete:spatial_source.json",
    "capsule_source_deleted:spatial_source.json",
    "capsule_source_deleted:SPATIAL_SOURCE_READY.json",
    "capsule_before_final_complete",
    "capsule_final_complete",
    "capsule_journal_removed",
    "receipt_before_gc",
    "gc_before_commit",
    "gc_after_commit",
]


@pytest.mark.parametrize("phase", PHASES)
def test_hard_exit_recovers_every_source_swap_and_ledger_boundary(
    tmp_path, monkeypatch, phase
):
    kwargs, target, encoder, spool, job = acknowledged_job(tmp_path, monkeypatch)
    payloads = {
        str(p.relative_to(target)): digest(p)
        for p in (target / "vae_cache").rglob("*.pt")
    }
    child = multiprocessing.get_context("fork").Process(
        target=_hard_exit, args=(str(spool.root), job, phase)
    )
    child.start()
    child.join(20)
    assert child.exitcode == 77
    restarted = EventSpool.open(spool.root)
    assert restarted.reap(job)
    assert validate_profile_episode(target)["schema"] == final.PROFILE_SCHEMA
    assert not (target / final.FULL).exists() and not (target / final.JOURNAL).exists()
    assert payloads == {p: digest(target / p) for p in payloads}
    assert (
        restarted.stats()["completed_jobs"] == 1
        and restarted.stats()["active_records"] == 0
    )
    assert restarted.reap(job)


def test_two_writers_and_reader_during_retirement_fail_closed(tmp_path, monkeypatch):
    *_, spool, job = acknowledged_job(tmp_path, monkeypatch)
    with spool._db() as db:
        target = Path(
            db.execute("SELECT target FROM jobs WHERE id=?", (job,)).fetchone()[0]
        )
    entered = threading.Event()
    release = threading.Event()
    errors = []

    def pause(phase):
        if phase == "capsule_verified_before_retire":
            entered.set()
            assert release.wait(10)

    def writer():
        try:
            ledger_archive.archive(spool, job, failpoint=pause)
        except BaseException as exc:
            errors.append(exc)

    thread = threading.Thread(target=writer)
    thread.start()
    assert entered.wait(10)
    try:
        with pytest.raises(CacheError, match="builder"):
            ledger_archive.archive(spool, job)
        with pytest.raises(CacheError, match="lease is busy"):
            open_episode_index(target)
        assert (target / final.FULL).exists()
    finally:
        release.set()
        thread.join(15)
    assert not errors and not thread.is_alive()
    assert open_episode_index(target).manifest["schema"] == final.INDEX_SCHEMA


@pytest.mark.parametrize(
    "name", ["spatial_source_index.json", ".source_retirement/unexpected.keep"]
)
def test_unexpected_retirement_files_are_preserved_without_deleting_source(
    tmp_path, monkeypatch, name
):
    kwargs, target, encoder, spool, job = acknowledged_job(tmp_path, monkeypatch)
    path = target / name
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(b"preserve")
    with pytest.raises(CacheError, match="unexpected"):
        spool.reap(job)
    assert path.read_bytes() == b"preserve" and (target / final.FULL).exists()


def test_low_disk_before_intent_retains_original_complete_publication(
    tmp_path, monkeypatch
):
    kwargs, target, encoder, spool, job = acknowledged_job(tmp_path, monkeypatch)
    before = {
        p: digest(target / p)
        for p in (
            "spatial_source.json",
            "SPATIAL_SOURCE_READY.json",
            "episode_manifest.json",
            "COMPLETE.json",
            "vae_cache/manifest.json",
            "vae_cache/COMPLETE.json",
        )
    }
    atomic = source_retirement.atomic_json

    def no_disk(path, *a, **kw):
        if str(path).endswith("transaction.json"):
            raise OSError(errno.ENOSPC, "TEST_ONLY_FULL_DISK")
        return atomic(path, *a, **kw)

    with monkeypatch.context() as patch:
        patch.setattr(source_retirement, "atomic_json", no_disk)
        with pytest.raises(OSError):
            spool.reap(job)
    assert before == {p: digest(target / p) for p in before}
    assert spool.reap(job)


def test_tampered_sql_bound_journal_refuses_source_deletion(tmp_path, monkeypatch):
    kwargs, target, encoder, spool, job = acknowledged_job(tmp_path, monkeypatch)

    def interrupt(phase):
        if phase == "capsule_intent_fsynced":
            raise RuntimeError("TEST_ONLY_STOP")

    with pytest.raises(RuntimeError):
        ledger_archive.archive(spool, job, failpoint=interrupt)
    journal = target / final.JOURNAL
    data = read_json(journal)
    data["scope"]["recipe_id"] = "0" * 64
    write_json(journal, data)
    with pytest.raises(CacheError, match="scope|binding"):
        spool.reap(job)
    assert (target / final.FULL).exists()


@pytest.mark.parametrize("replacement", [None, {"capsule_sha256": "0" * 64}])
def test_finished_capsule_still_requires_original_sql_intent_before_gc(
    tmp_path, monkeypatch, replacement
):
    _, target, _, spool, job = acknowledged_job(tmp_path, monkeypatch)

    def interrupt(phase):
        if phase == "capsule_journal_removed":
            raise RuntimeError("TEST_ONLY_STOP_BEFORE_SQL_GC")

    with pytest.raises(RuntimeError):
        ledger_archive.archive(spool, job, failpoint=interrupt)
    assert not (target / final.JOURNAL).exists()
    assert open_episode_index(target).manifest["schema"] == final.INDEX_SCHEMA
    with spool._db() as db:
        original = db.execute(
            "SELECT retirement FROM jobs WHERE id=?", (job,)
        ).fetchone()[0]
        db.execute(
            "UPDATE jobs SET retirement=? WHERE id=?",
            (None if replacement is None else json.dumps(replacement), job),
        )
    with pytest.raises(CacheError, match="durable SQL retirement binding"):
        spool.reap(job)
    assert spool.stats()["completed_jobs"] == 0
    with spool._db() as db:
        db.execute("UPDATE jobs SET retirement=? WHERE id=?", (original, job))
    assert spool.reap(job)


def test_explicitly_kept_renderer_work_cannot_retire_source(tmp_path, monkeypatch):
    _, target, _, spool, job = acknowledged_job(tmp_path, monkeypatch)
    with spool._db() as db:
        row = dict(db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone())
    proof = ledger_archive.published_proof(row, json.loads(row["scope"]))
    with pytest.raises(CacheError, match="released managed renderer work"):
        source_retirement.finalize(
            spool, job, row, proof, {"acked": 1}, {"status": "kept_by_explicit_config"}
        )
    assert (target / final.FULL).exists()
    assert not (target / final.JOURNAL).exists()
    assert spool.reap(job)


@pytest.mark.parametrize(
    "component",
    [
        "working_proof",
        "work_cleanup",
        "retired_source",
        "retired_ready",
        "archive",
        "disposition",
    ],
)
def test_coordinated_receipt_and_complete_changes_cannot_escape_capsule(
    tmp_path, monkeypatch, component
):
    _, target, _, spool, job = acknowledged_job(tmp_path, monkeypatch)

    def interrupt(phase):
        if phase == "capsule_journal_removed":
            raise RuntimeError("TEST_ONLY_BEFORE_GC")

    with pytest.raises(RuntimeError):
        ledger_archive.archive(spool, job, failpoint=interrupt)
    capsule_sha = digest(target / final.CAPSULE)
    receipt = read_json(target / final.RECEIPT)
    if component == "working_proof":
        receipt[component]["source_id"] = "0" * 64
    elif component == "work_cleanup":
        receipt[component] = {"status": "kept_by_explicit_config"}
    elif component in ("retired_source", "retired_ready"):
        key = (
            final.FULL if component == "retired_source" else "SPATIAL_SOURCE_READY.json"
        )
        receipt["retired_files"][key] = "0" * 64
    elif component == "archive":
        receipt["full_audit_archive"] = {"path": "TEST_ONLY_UNAUTHENTICATED_ARCHIVE"}
    else:
        receipt["source_disposition"] = "TEST_ONLY_NOT_RETIRED"
    write_json(target / final.RECEIPT, receipt)
    complete = read_json(target / "COMPLETE.json")
    complete["source_retirement_sha256"] = digest(target / final.RECEIPT)
    write_json(target / "COMPLETE.json", complete)
    assert digest(target / final.CAPSULE) == capsule_sha
    with pytest.raises(CacheError, match="retirement provenance"):
        open_episode_index(target)
    with pytest.raises(CacheError, match="retirement provenance"):
        spool.reap(job)
    assert spool.stats()["completed_jobs"] == 0


@pytest.mark.parametrize(
    "which",
    [
        final.CAPSULE,
        final.READY,
        final.RECEIPT,
        "vae_cache/manifest.json",
        "vae_cache/COMPLETE.json",
        "COMPLETE.json",
    ],
)
def test_corrupt_final_hashes_fail_without_loading_all_views(tmp_path, which):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    complete_working(kwargs, target, encoder, spool, job)
    assert spool.adopt_completed(job)
    path = target / which
    value = read_json(path)
    value["TEST_ONLY_CORRUPTION"] = True
    write_json(path, value)
    with pytest.raises(CacheError):
        open_episode_index(target)
    with pytest.raises(CacheError):
        spool.reap(job)


def test_final_late_events_are_idempotent_and_wrong_scope_is_rejected(tmp_path):
    kwargs, target, encoder, spool, job = capsule_case(tmp_path)
    complete_working(kwargs, target, encoder, spool, job)
    source = read_json(target / final.FULL)
    vid = next(iter(source["views"]))
    owner = source["views"][vid]["owners"][0]
    desc = source["final_pixel_events"][owner["event_id"]]
    event = final_pixel_event(
        target / owner["path"],
        episode_key=desc["episode_key"],
        source_fingerprint=desc["source_fingerprint"],
        profile_id=desc["profile_id"],
        view_id=vid,
        canonical_view_id=desc["canonical_view_id"],
        variant=desc["variant"],
        expected_size=desc["size_wh"],
    )
    assert spool.adopt_completed(job)
    assert spool.enqueue(job, event) == "completed_by_cache"
    with pytest.raises(CacheError):
        spool.register(
            target,
            episode_key="NavigateKitchen/episode_000001",
            source_fingerprint=kwargs["source_fingerprint"],
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
    with pytest.raises(CacheError):
        spool.register(
            target,
            episode_key="NavigateKitchen/episode_000000",
            source_fingerprint="0" * 64,
            profile_id=kwargs["profile"].to_dict()["profile_id"],
        )
