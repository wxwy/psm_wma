"""Hard process exits during gzip retirement using the real v2 collector."""

import errno
import multiprocessing
import os

import pytest

from g2.io import digest
from g2.latent_cache import final_source as final
from g2.latent_cache import ledger_archive, source_retirement
from g2.latent_cache.contract import CacheError
from g2.latent_cache.posthoc import retire_view_first_cache
from g2.latent_cache.storage import ViewReader, open_episode_index
from g2.latent_cache.streaming import EventSpool
from g2.offline.stage_a import validate_profile_episode
from g2.offline.view_only_source import PACKED, RECEIPT
from g2.tests.test_view_first_retirement import encode_case, retirement_case


def ready_job(tmp_path, monkeypatch):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    # Real verified-cache handoff and durable done=2; only collector held.
    with monkeypatch.context() as patch:
        patch.setattr(ledger_archive, "archive", lambda *a, **kw: False)
        result = retire_view_first_cache(
            root, spool_root=policy["spool_root"], source_policy=policy
        )
    spool = EventSpool.open(policy["spool_root"])
    with spool._db() as db:
        row = db.execute("SELECT * FROM jobs WHERE id=?", (result["job"],)).fetchone()
        assert row["done"] == 2 and row["completion_receipt"] is not None
        assert db.execute("SELECT COUNT(*) FROM events").fetchone()[0] == 0
    return root, policy, spool, result["job"]


def crash_at(spool_path, job, phase):
    def fail(name):
        if name == phase:
            os._exit(77)

    ledger_archive.archive(EventSpool.open(spool_path), job, failpoint=fail)


PHASES = (
    [
        "capsule_intent_bound",
        "capsule_intent_fsynced",
        "capsule_published:spatial_source_index.json",
        "capsule_published:vae_cache/manifest.json",
        "capsule_published:episode_manifest.json",
        "capsule_verified_before_retire",
    ]
    + [
        f"{phase}:{rel}"
        for rel in (PACKED, RECEIPT, "SPATIAL_SOURCE_READY.json")
        for phase in (
            "capsule_before_source_rename",
            "capsule_source_renamed",
            "capsule_before_source_delete",
            "capsule_source_deleted",
        )
    ]
    + [
        "capsule_final_complete",
        "capsule_journal_removed",
        "receipt_before_gc",
        "gc_before_commit",
        "gc_after_commit",
    ]
)


@pytest.mark.parametrize("phase", PHASES)
def test_gzip_hard_exit_resumes_through_public_posthoc_adapter(
    tmp_path, monkeypatch, phase
):
    root, policy, spool, job = ready_job(tmp_path, monkeypatch)
    payloads = {
        str(p.relative_to(root)): digest(p) for p in (root / "vae_cache").rglob("*.pt")
    }
    child = multiprocessing.get_context("fork").Process(
        target=crash_at, args=(policy["spool_root"], job, phase)
    )
    child.start()
    child.join(20)
    assert child.exitcode == 77
    result = retire_view_first_cache(
        root, spool_root=policy["spool_root"], source_policy=policy
    )
    assert result["complete"]
    assert validate_profile_episode(root)["schema"] == final.PROFILE_SCHEMA
    assert not (root / final.JOURNAL).exists()
    assert all(
        not (root / name).exists()
        for name in (PACKED, RECEIPT, "SPATIAL_SOURCE_READY.json", final.FULL)
    )
    assert payloads == {p: digest(root / p) for p in payloads}
    stats = EventSpool.open(policy["spool_root"]).stats()
    assert stats["completed_jobs"] == 1 and stats["active_jobs"] == 0


def test_failed_capsule_write_keeps_gzip_then_recovers_before_manifest_validation(
    tmp_path, monkeypatch
):
    root, policy, spool, job = ready_job(tmp_path, monkeypatch)
    source_bytes = {
        p: digest(root / p) for p in (PACKED, RECEIPT, "SPATIAL_SOURCE_READY.json")
    }
    atomic = source_retirement.atomic_json

    def disk_full(path, *a, **kw):
        if str(path).endswith(final.CAPSULE):
            raise OSError(errno.ENOSPC, "TEST_ONLY_NO_SPACE")
        return atomic(path, *a, **kw)

    with monkeypatch.context() as patch:
        patch.setattr(source_retirement, "atomic_json", disk_full)
        with pytest.raises(OSError):
            spool.reap(job)
    assert source_bytes == {p: digest(root / p) for p in source_bytes}
    with pytest.raises(CacheError, match="retirement pending"):
        open_episode_index(root)
    assert retire_view_first_cache(
        root, spool_root=policy["spool_root"], source_policy=policy
    )["complete"]


def test_live_reader_defers_gzip_retirement_until_lease_released(tmp_path):
    root, policy = retirement_case(tmp_path)
    encode_case(tmp_path, root)
    reader = ViewReader(open_episode_index(root))
    try:
        result = retire_view_first_cache(
            root, spool_root=policy["spool_root"], source_policy=policy
        )
        assert not result["complete"] and (root / PACKED).exists()
        assert reader.read_view("sixview/floor_top", 0)["present"]
    finally:
        reader.close()
    assert retire_view_first_cache(
        root, spool_root=policy["spool_root"], source_policy=policy
    )["complete"]
