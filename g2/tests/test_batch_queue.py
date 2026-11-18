"""Real SQLite/concurrency/OS crash tests; numeric model is CPU-only fixture."""

import multiprocessing
import os
import time

import pytest

from g2.latent_cache.batch_contract import make_batch_recipe
from g2.latent_cache.batch_queue import BatchQueue
from g2.latent_cache.batch_worker import execute_claim
from g2.latent_cache.contract import CacheError
from g2.latent_cache.streaming import ConsumerLimits, EventSpool
from g2.tests.batch_helpers import FakeBatchEncoder


def events_case(tmp_path, n=35, *, limit=128, budget=64 * 1024**2):
    from PIL import Image

    from g2.latent_cache.streaming import final_pixel_event

    encoder = FakeBatchEncoder()
    spool = EventSpool(
        tmp_path / "spool",
        make_batch_recipe(encoder.descriptor()),
        limits=ConsumerLimits(limit, 4 * 1024**2),
        max_result_bytes=budget,
    )
    job = spool.register(
        tmp_path / "unpublished",
        episode_key="Task/episode_000000",
        source_fingerprint="a" * 64,
        profile_id="b" * 64,
    )
    events = []
    for i in range(n):
        path = tmp_path / f"pixel_{i}.png"
        Image.new("RGB", (16, 16), (i % 255, 4, 3)).save(path)
        event = final_pixel_event(
            path,
            episode_key="Task/episode_000000",
            source_fingerprint="a" * 64,
            profile_id="b" * 64,
            view_id="sixview/floor_top",
            canonical_view_id="sixview/floor_top",
            variant="clean",
            expected_size=[16, 16],
        )
        spool.enqueue(job, event, timeout_s=0)
        events.append(event)
    return spool, encoder, job, events


def test_maximum_wait_tail_and_durable_ack_inputs(tmp_path):
    spool, enc, job, events = events_case(tmp_path)
    now = [100.0]
    with spool._db() as db:
        db.execute("UPDATE engine_members SET ready_at=100")
    q = BatchQueue(spool, batch_wait_ms=500, clock=lambda: now[0])
    q.register_worker("a", 4)
    claim = q.claim("a")
    assert len(claim["context"]["members"]) == 32
    result = execute_claim(q, enc, claim, physical_gpu=4)
    assert result["native_called"] and enc.calls == 1
    assert spool.stats()["pending_inputs"] == 3
    assert q.claim("a") is None
    now[0] += 0.5
    tail = q.claim("a")
    assert tail["context"]["input_shape"] == [3, 3, 1, 256, 256]
    execute_claim(q, enc, tail, physical_gpu=4)
    assert enc.calls == 2 and spool.stats()["pending_inputs"] == 0


def _crash(root, claim, phase):
    spool = EventSpool.open(root)
    execute_claim(
        BatchQueue(spool), FakeBatchEncoder(), claim, physical_gpu=4, crash_once=phase
    )


@pytest.mark.parametrize("phase", ["numeric_fsynced", "after_ack:0", "after_ack:7"])
def test_hard_exit_reclaims_fixed_batch_and_compares_partial_numerics(tmp_path, phase):
    spool, enc, job, events = events_case(tmp_path, 32)
    q = BatchQueue(spool)
    q.register_worker("dead", 4)
    claim = q.claim("dead")
    p = multiprocessing.get_context("spawn").Process(
        target=_crash, args=(str(spool.root), claim, phase)
    )
    p.start()
    p.join(30)
    assert p.exitcode == 77
    # No input is released while any member still needs an exact replay.
    assert spool.stats()["pending_inputs"] == 32
    q.expire_dead_worker(os.getpid())
    q.register_worker("new", 5)
    replay = q.claim("new")
    assert replay["context"] == claim["context"] and replay["token"] != claim["token"]
    with pytest.raises(CacheError, match="stale"):
        q.ack(claim, 0, "c" * 64)
    result = execute_claim(q, enc, replay, physical_gpu=5)
    assert result["reused_files"] >= 1 and enc.calls == 1
    assert spool.stats()["pending_inputs"] == 0


def test_exact_replay_change_rejected_before_new_publication(tmp_path):
    spool, enc, job, _ = events_case(tmp_path, 8)
    q = BatchQueue(spool, batch_wait_ms=0)
    q.register_worker("old", 4)
    claim = q.claim("old")
    p = multiprocessing.get_context("spawn").Process(
        target=_crash, args=(str(spool.root), claim, "after_ack:0")
    )
    p.start()
    p.join(30)
    assert p.exitcode == 77
    q.expire_dead_worker(os.getpid())
    q.register_worker("new", 5)
    again = q.claim("new")
    with pytest.raises(CacheError, match="replay changed"):
        execute_claim(q, FakeBatchEncoder(offset=1), again, physical_gpu=5)
    assert len(list((spool.root / "records").rglob("*.pt"))) == 1
    assert spool.stats()["pending_inputs"] == 8


def test_fair_parallel_claims_heartbeats_and_oom_keep_members(tmp_path):
    spool, _, _, _ = events_case(tmp_path, 70)
    now = [time.time()]
    q = BatchQueue(spool, clock=lambda: now[0], lease_s=2, batch_wait_ms=0)
    q.register_worker("w1", 4)
    q.register_worker("w2", 5)
    a = q.claim("w1")
    b = q.claim("w2")
    assert len(a["context"]["members"]) == len(b["context"]["members"]) == 32
    assert a["context"]["batch_id"] != b["context"]["batch_id"]
    now[0] += 1
    q.heartbeat("w1", a["context"]["batch_id"], a["token"])
    q.fail(b, "controlled OOM")
    assert spool.stats()["pending_inputs"] == 70
    q.retry_failed()
    retry = q.claim("w2")
    assert retry["context"] == b["context"]
    now[0] += 4
    with pytest.raises(CacheError, match="stale"):
        q.fence(a["context"]["batch_id"], a["token"])


def test_budget_backpressure_and_temp_cleanup(tmp_path):
    spool, enc, job, _ = events_case(tmp_path, 2, budget=1)
    q = BatchQueue(spool, batch_wait_ms=0)
    q.register_worker("a", 4)
    assert q.claim("a") is None and spool.stats()["pending_inputs"] == 2
    assert q.capacity_pressure()["blocked"] is True
    spool.max_result_bytes = 1024**2
    claim = q.claim("a")
    directory = spool.root / "records" / claim["context"]["batch_id"]
    directory.mkdir(parents=True)
    (directory / ".view-owned.tmp").write_bytes(b"interrupted")
    execute_claim(q, enc, claim, physical_gpu=4)
    assert not list(directory.glob(".view-*"))
    assert q.capacity_pressure()["blocked"] is False
