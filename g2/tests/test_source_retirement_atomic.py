"""Hard-exit actual atomic_json after temp fsync, not a Python exception."""

from __future__ import annotations

import multiprocessing
import os
from pathlib import Path

import pytest

from g2.latent_cache import final_source as final
from g2.latent_cache import ledger_archive, storage
from g2.latent_cache.streaming import EventSpool
from g2.tests.test_source_retirement_faults import acknowledged_job


def _exit_before_publish(spool_root, job, target, relative):
    spool = EventSpool.open(spool_root)
    destination = Path(target) / relative
    link, replace = storage.os.link, storage.os.replace

    def stop_link(source, dest, *a, **k):
        if Path(dest) == destination:
            os._exit(77)
        return link(source, dest, *a, **k)

    def stop_replace(source, dest, *a, **k):
        if Path(dest) == destination:
            os._exit(77)
        return replace(source, dest, *a, **k)

    storage.os.link = stop_link
    storage.os.replace = stop_replace
    ledger_archive.archive(spool, job)


@pytest.mark.parametrize("relative", [final.JOURNAL, "vae_cache/manifest.json"])
def test_actual_fsynced_atomic_temp_is_recovered_only_under_sql_bound_intent(
    tmp_path, monkeypatch, relative
):
    kwargs, target, encoder, spool, job = acknowledged_job(tmp_path, monkeypatch)
    child = multiprocessing.get_context("fork").Process(
        target=_exit_before_publish, args=(str(spool.root), job, str(target), relative)
    )
    child.start()
    child.join(20)
    assert child.exitcode == 77
    assert list((target / relative).parent.glob(".json-*.tmp"))
    assert (target / final.FULL).exists()
    assert EventSpool.open(spool.root).reap(job)
    assert not list(target.rglob(".json-*.tmp")) and not (target / final.FULL).exists()
    assert storage.open_episode_index(target).manifest["schema"] == final.INDEX_SCHEMA
