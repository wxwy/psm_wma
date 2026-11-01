"""CPU-only Queue/encoder cleanup; fake encoder targets never invoke FFmpeg."""

import errno
import gc
import multiprocessing as mp
import signal
import threading
import time
from collections import deque
from multiprocessing.queues import Queue, _sentinel
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink, _ReaderClose


def drain(queue, directory, fps, rollout):
    Path(directory).mkdir(parents=True, exist_ok=True)
    Path(directory, "ready").touch()
    count = 0
    while queue.get() is not None:
        count += 1
    Path(directory, "count").write_text(str(count))


def ignore_term(queue, directory, fps, rollout):
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    Path(directory).mkdir(parents=True, exist_ok=True)
    Path(directory, "ready").touch()
    while True:
        time.sleep(0.05)


def wait_ready(sink, directory):
    until = time.monotonic() + 15
    while not (directory / "ready").exists():
        assert sink.process.is_alive(), "CPU encoder exited before ready"
        assert time.monotonic() < until, "bounded CPU encoder startup expired"
        time.sleep(0.01)


@pytest.mark.parametrize("round_index", range(2))
def test_eight_cpu_slots_repeatedly_drain_queue_without_background_errors(
    tmp_path, monkeypatch, round_index
):
    background = []
    monkeypatch.setattr(threading, "excepthook", background.append)
    sinks = []
    try:
        for slot in range(8):
            directory = tmp_path / f"round{round_index}_slot{slot}"
            sink = MediaSink(directory, target=drain, grace_s=2)
            sinks.append(sink)
            wait_ready(sink, directory)
            sink.frame(np.zeros((16, 16, 3), dtype=np.uint8))
        for slot, sink in enumerate(sinks):
            result = sink.close()
            assert result["process_cleanup_failed"] is False
            assert result["encoder_alive"] is result["feeder_alive"] is False
            assert not result["forced_encoder_cleanup"]
            assert result["errors"] == []
            assert sink.process.exitcode == 0
            assert sink.queue._reader.closed and sink.queue._writer.closed
            assert (
                tmp_path / f"round{round_index}_slot{slot}" / "count"
            ).read_text() == "1"
            assert result == sink.close()
            sink.frame(np.zeros((1, 1, 3), dtype=np.uint8))
            assert sink.dropped == 1 and not sink.queue._thread.is_alive()
        assert background == []
    finally:
        for sink in sinks:
            sink.close()


def test_full_pipe_ignored_term_is_reaped_without_feeder_ebadf_or_semaphore_error(
    tmp_path, monkeypatch
):
    background = []
    monkeypatch.setattr(threading, "excepthook", background.append)
    sink = MediaSink(tmp_path, target=ignore_term, grace_s=0.15)
    try:
        wait_ready(sink, tmp_path)
        # > pipe capacity, < production frame cap; the child never reads.
        for _ in range(10):
            sink.frame(np.zeros((512, 512, 3), dtype=np.uint8))
        start = time.monotonic()
        result = sink.close()
        assert time.monotonic() - start < 3
        assert result["forced_encoder_cleanup"] is True
        assert result["process_cleanup_failed"] is False
        assert result["encoder_alive"] is result["feeder_alive"] is False
        assert sink.process.exitcode == -signal.SIGKILL
        assert sink.queue._reader.closed and sink.queue._writer.closed
        assert result["dropped"] > 0
        assert background == []
        assert not any(
            "Bad file descriptor" in e or "semaphore" in e for e in result["errors"]
        )
    finally:
        sink.close()


def test_reader_close_is_serialized_and_idempotent_when_both_threads_enter():
    entered, release = threading.Event(), threading.Event()
    calls, errors = [], []

    def close():
        calls.append("closed")
        entered.set()
        assert release.wait(2)

    guard = _ReaderClose(close, errors, 1)
    feeder = threading.Thread(target=guard)
    parent = threading.Thread(target=guard)
    feeder.start()
    assert entered.wait(2)
    parent.start()
    release.set()
    feeder.join(2)
    parent.join(2)
    assert not feeder.is_alive() and not parent.is_alive()
    assert calls == ["closed"] and errors == [] and not guard.failed


@pytest.mark.parametrize("code,failed", [(errno.EBADF, False), (errno.EIO, True)])
def test_reader_close_error_is_diagnostic_not_an_escaping_feeder_exception(
    code, failed
):
    calls, errors = [], []

    def close():
        calls.append(1)
        raise OSError(code, "injected fd failure")

    guard = _ReaderClose(close, errors, 0.05)
    guard()
    guard()
    assert calls == [1] and guard.failed is failed
    assert len(errors) == 1 and "injected fd failure" in errors[0]


def test_reader_lock_timeout_is_bounded_and_stays_failed():
    errors = []
    guard = _ReaderClose(lambda: None, errors, 0.01)
    with guard.lock:
        start = time.monotonic()
        guard()
    guard()
    assert time.monotonic() - start < 1 and guard.failed
    assert "did not quiesce" in errors[0]


def test_start_failure_closes_both_queue_descriptors(tmp_path, monkeypatch):
    ctx = mp.get_context("spawn")
    process_type = ctx.Process

    def fail_start(self):
        raise OSError(errno.EBADF, "injected encoder start failure")

    monkeypatch.setattr(process_type, "start", fail_start)
    sink = MediaSink(tmp_path, target=drain)
    result = sink.close()
    assert sink.process is None
    assert sink.queue._reader.closed and sink.queue._writer.closed
    assert not result["process_cleanup_failed"]
    assert "injected encoder start failure" in result["errors"][0]


def test_real_stdlib_sentinel_error_control_and_guarded_semaphore_path():
    """An injected reader EBADF reproduces DS's secondary semaphore failure."""
    errors, writes = [], []

    def ebadf():
        raise OSError(errno.EBADF, "injected sentinel reader close")

    def feed(reader_close):
        Queue._feed(
            deque([_sentinel]),
            threading.Condition(),
            lambda raw: None,
            threading.Lock(),
            reader_close,
            lambda: writes.append("closed"),
            True,
            lambda error, obj: errors.append(repr(error)),
            threading.BoundedSemaphore(1),
        )

    with pytest.raises(ValueError, match="released too many times"):
        feed(ebadf)  # Controlled RED of CPython's error path, not an old-code Gate.
    diagnostics = []
    feed(_ReaderClose(ebadf, diagnostics, 0.05))
    assert writes == ["closed"] and errors == []
    assert len(diagnostics) == 1 and "injected sentinel reader close" in diagnostics[0]


@pytest.mark.parametrize("alive", ["encoder", "feeder"])
def test_actual_unquiesced_encoder_or_feeder_remains_a_process_fault(tmp_path, alive):
    sink = MediaSink(tmp_path, rollout=False)

    def connection():
        return SimpleNamespace(close=lambda: None)

    thread = SimpleNamespace(
        join=lambda timeout: None, is_alive=lambda: alive == "feeder"
    )
    sink.queue = SimpleNamespace(
        put_nowait=lambda value: None,
        cancel_join_thread=lambda: None,
        close=lambda: None,
        _reader=connection(),
        _writer=connection(),
        _thread=thread,
    )
    sink._reader_guard = _ReaderClose(sink.queue._reader.close, sink.errors, 0.01)
    sink.queue._reader.close = sink._reader_guard
    sink.process = SimpleNamespace(
        join=lambda timeout: None,
        terminate=lambda: None,
        kill=lambda: None,
        is_alive=lambda: alive == "encoder",
        exitcode=0,
    )
    result = sink.close()
    assert result["process_cleanup_failed"] is True
    assert result[f"{alive}_alive"] is True


def test_core_local_result_survives_successful_forced_media_cleanup(
    tmp_path, monkeypatch
):
    from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode
    from tools.v3.eval_v2_production_tests.native_test import native_execute

    outcomes = []
    execute = NativeEpisode.execute

    def record(self, *args, **kwargs):
        result = execute(self, *args, **kwargs)
        outcomes.append(result)
        return result

    monkeypatch.setattr(NativeEpisode, "execute", record)

    class ReapedMedia:
        def __init__(self, *args, **kwargs):
            pass

        def frame(self, frame):
            pass

        def prediction(self, index, result):
            pass

        def close(self):
            return {
                "forced_encoder_cleanup": True,
                "process_cleanup_failed": False,
                "errors": ["OSError(9, 'Bad file descriptor')"],
            }

    row, _, calls, value = native_execute(
        tmp_path, monkeypatch, media_factory=ReapedMedia
    )
    assert row["outcome"] == "success" and len(value.rows("CloseFridge")) == 1
    assert calls[-1]["_local_memory_command"] == "reset"
    assert outcomes[0]["media_process_fault"] is False


def test_optional_disabled_media_creates_no_process(tmp_path):
    before = set(p.pid for p in mp.active_children())
    sink = MediaSink(tmp_path, rollout=False)
    assert not sink.close()["process_cleanup_failed"]
    gc.collect()
    assert set(p.pid for p in mp.active_children()) == before
