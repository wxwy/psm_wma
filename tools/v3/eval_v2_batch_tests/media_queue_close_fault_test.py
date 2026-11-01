"""RM-M01: unknown Queue shutdown errors stay authoritative after later cleanup."""

import errno
import json
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink, _ReaderClose


def stopped_sink(directory, *, operation=None, exception="eio", writer_ebadf=False):
    """Already-stopped encoder/feeder; only selected close operations can fail."""
    sink = MediaSink(directory, rollout=False, generated="none", grace_s=0.01)
    calls = []

    def call(name):
        calls.append(name)
        if name == operation:
            if exception == "eio":
                raise OSError(errno.EIO, f"injected {name}")
            raise ValueError(f"injected {name}")
        if name == "writer" and writer_ebadf:
            raise OSError(errno.EBADF, "injected tolerated writer close")

    reader = SimpleNamespace(close=lambda: call("reader"))
    writer = SimpleNamespace(close=lambda: call("writer"))
    sink._reader_guard = _ReaderClose(reader.close, sink.errors, sink.grace_s)
    reader.close = sink._reader_guard
    sink.queue = SimpleNamespace(
        put_nowait=lambda value: None,
        cancel_join_thread=lambda: call("cancel_join_thread"),
        close=lambda: call("close"),
        _reader=reader,
        _writer=writer,
        _thread=None,
    )
    sink.process = SimpleNamespace(
        join=lambda timeout: None, is_alive=lambda: False, exitcode=0
    )
    return sink, calls


@pytest.mark.parametrize("operation", ["cancel_join_thread", "close"])
@pytest.mark.parametrize("exception", ["eio", "value_error"])
@pytest.mark.parametrize("writer_ebadf", [False, True])
def test_unknown_queue_error_stays_failed_even_after_descriptors_close(
    tmp_path, operation, exception, writer_ebadf
):
    sink, calls = stopped_sink(
        tmp_path, operation=operation, exception=exception, writer_ebadf=writer_ebadf
    )
    result = sink.close()
    assert result["encoder_alive"] is result["feeder_alive"] is False
    assert result["process_cleanup_failed"] is True
    assert "injected " + operation in result["errors"][0]
    assert "reader" in calls and "writer" in calls
    assert result["independent_of_SR"] is True
    before = list(calls)
    assert sink.close() == result and calls == before


@pytest.mark.parametrize("writer_ebadf", [False, True])
def test_clean_queue_or_tolerated_descriptor_ebadf_does_not_invent_failure(
    tmp_path, writer_ebadf
):
    sink, calls = stopped_sink(tmp_path, writer_ebadf=writer_ebadf)
    result = sink.close()
    assert result["process_cleanup_failed"] is False
    assert calls == ["cancel_join_thread", "close", "reader", "writer"]
    assert bool(result["errors"]) is writer_ebadf


@pytest.mark.parametrize(
    "kind", ["queue_eio", "queue_value_error", "descriptor_ebadf", "forced_reaped"]
)
def test_native_adapter_reports_unknown_failure_without_changing_core_or_local_reset(
    tmp_path, monkeypatch, kind
):
    from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode
    from tools.v3.eval_v2_production_tests.native_test import native_execute

    outcomes = []
    execute = NativeEpisode.execute

    def record(self, *args, **kwargs):
        result = execute(self, *args, **kwargs)
        outcomes.append(result)
        return result

    def factory(directory, **kwargs):
        sink, _ = stopped_sink(
            directory,
            operation="cancel_join_thread"
            if kind == "queue_eio"
            else "close"
            if kind == "queue_value_error"
            else None,
            exception="value_error" if kind == "queue_value_error" else "eio",
            writer_ebadf=kind == "descriptor_ebadf",
        )
        sink.forced = kind == "forced_reaped"
        return sink

    monkeypatch.setattr(NativeEpisode, "execute", record)
    row, _, calls, value = native_execute(tmp_path, monkeypatch, media_factory=factory)
    fault = kind.startswith("queue_")
    assert outcomes[0]["media_process_fault"] is fault
    diagnostic = json.loads(
        (value._slot("CloseFridge", 0) / "media_diagnostics.json").read_text()
    )
    assert diagnostic["process_cleanup_failed"] is fault
    assert diagnostic["forced_encoder_cleanup"] is (kind == "forced_reaped")
    assert row["outcome"] == "success" and row["steps"] == 2
    assert len(value.rows("CloseFridge")) == 1
    assert calls[-1]["_local_memory_command"] == "reset"
    assert outcomes[0]["local_session"]["reset_ack"] is True
