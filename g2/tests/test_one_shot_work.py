"""Managed native-work cleanup is independent of VAE temp-input cleanup."""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from g2.latent_cache.contract import CacheError
from g2.latent_cache.streaming import EventConsumer
from g2.offline.stage_a import package_stage_a, validate_profile_episode
from g2.offline.work_lifecycle import LEASE, episode_work_path, init_root, producer_work
from g2.tests.test_stage_a_streaming import PowerLoss, setup_case


def work_case(tmp_path):
    kwargs, target, encoder, spool, job = setup_case(tmp_path / "case")
    config = SimpleNamespace(
        work_root=tmp_path / "managed",
        output_root=target.parent,
        sim_direct_geometry_only=True,
        sim_color_only=True,
        keep_work=False,
    )
    row = dict(
        episode_id=0,
        task_class="NavigateKitchen",
        source_fingerprint="a" * 64,
        spatial_frames=[0, 10, 20],
        expected_relative_output="published",
    )
    init_root(config.work_root, spool.root, config.output_root)
    return kwargs, target, encoder, spool, job, config, row


def test_completed_work_waits_for_renderer_lease_then_reclaims(tmp_path):
    kwargs, target, encoder, spool, job, config, row = work_case(tmp_path)
    with producer_work(row, config, kwargs["profile"], spool, job) as work:
        (work / "native_work.bin").write_bytes(b"x" * 65536)
        package_stage_a(
            destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
        )
        spool.offer_source(job)
        consumer = EventConsumer(spool, encoder)
        for _ in range(20):
            if not consumer.step():
                break
        assert validate_profile_episode(target)["profile_complete"]
        assert work.exists() and spool.stats()["active_jobs"] == 1
        assert not spool.reap(job)  # Live producer lock cannot be bypassed.
    assert spool.reap(job)
    assert not work.exists() and spool.stats()["active_jobs"] == 0
    receipt = spool.completed_receipt(job)
    assert receipt["work_cleanup"]["status"] == "complete"
    assert spool.reap(job)  # Archive+cleanup are idempotent.


def _producer_hard_crash(spool_root, row, config, profile):
    from g2.latent_cache.streaming import EventSpool

    spool = EventSpool.open(spool_root)
    with producer_work(row, config, profile, spool, config.job) as work:
        (work / "incomplete.bin").write_bytes(b"keep")
        os._exit(77)


def test_producer_crash_before_seal_preserves_and_resumes_work(tmp_path):
    kwargs, target, encoder, spool, job, config, row = work_case(tmp_path)
    config.job = job
    child = multiprocessing.get_context("fork").Process(
        target=_producer_hard_crash,
        args=(str(spool.root), row, config, kwargs["profile"]),
    )
    child.start()
    child.join(15)
    assert child.exitcode == 77
    work = episode_work_path(row, config, kwargs["profile"])
    with pytest.raises(CacheError, match="before final"):
        spool.reap(job)
    assert (work / "incomplete.bin").read_bytes() == b"keep"
    with producer_work(row, config, kwargs["profile"], spool, job) as resumed:
        assert resumed == work
        package_stage_a(
            destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
        )
        spool.offer_source(job)
    consumer = EventConsumer(spool, encoder)
    for _ in range(20):
        if not consumer.step():
            break
    assert spool.job_status(job) == "complete" and not work.exists()


def test_cleanup_partial_delete_crash_recovers_without_touching_other_work(
    tmp_path, monkeypatch
):
    import g2.offline.work_lifecycle as lifecycle

    kwargs, target, encoder, spool, job, config, row = work_case(tmp_path)
    unrelated = config.work_root / "other-task"
    unrelated.mkdir()
    (unrelated / "keep").write_bytes(b"private evidence")
    with producer_work(row, config, kwargs["profile"], spool, job) as work:
        (work / "remaining.bin").write_bytes(b"partial")
        package_stage_a(
            destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
        )
        spool.offer_source(job)
    original = lifecycle.shutil.rmtree

    def interrupt(path, *args, **kw):
        (Path(path) / LEASE).unlink()
        raise PowerLoss()

    consumer = EventConsumer(spool, encoder)
    with monkeypatch.context() as context:
        context.setattr(lifecycle.shutil, "rmtree", interrupt)
        with pytest.raises(PowerLoss):
            for _ in range(20):
                consumer.step()
    assert not work.exists() and (config.work_root / ".g2-trash" / job).exists()
    assert spool.reap(job)
    assert not (config.work_root / ".g2-trash" / job).exists()
    assert (unrelated / "keep").read_bytes() == b"private evidence"
    assert original is lifecycle.shutil.rmtree


def test_mismatched_lease_and_protected_or_unowned_roots_refuse_cleanup(tmp_path):
    kwargs, target, encoder, spool, job, config, row = work_case(tmp_path)
    with producer_work(row, config, kwargs["profile"], spool, job) as work:
        package_stage_a(
            destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
        )
        spool.offer_source(job)
    (work / LEASE).write_text("{}")
    consumer = EventConsumer(spool, encoder)
    with pytest.raises(CacheError, match="lease"):
        for _ in range(20):
            consumer.step()
    assert work.exists()
    with pytest.raises(CacheError, match="overlaps"):
        init_root(target.parent / "bad-work", spool.root, target.parent)
    unknown = tmp_path / "unknown"
    unknown.mkdir()
    (unknown / "evidence").write_text("preserve")
    with pytest.raises(CacheError, match="unowned"):
        init_root(unknown, spool.root, target.parent)
    assert (unknown / "evidence").read_text() == "preserve"


def test_late_producer_cannot_recreate_archived_work(tmp_path):
    kwargs, target, encoder, spool, job, config, row = work_case(tmp_path)
    with producer_work(row, config, kwargs["profile"], spool, job) as work:
        package_stage_a(
            destination=target, event_sink=lambda e: spool.enqueue(job, e), **kwargs
        )
        spool.offer_source(job)
    consumer = EventConsumer(spool, encoder)
    while consumer.step():
        pass
    assert spool.stats()["completed_jobs"] == 1 and not work.exists()
    with pytest.raises(CacheError, match="inactive"):
        with producer_work(row, config, kwargs["profile"], spool, job):
            pytest.fail("late producer must not acquire completed work")
    assert not work.exists()
