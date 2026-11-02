"""Real synthetic CPU FFmpeg, durable receipts and bounded failure cleanup."""

import errno
import threading
import time
from pathlib import Path

import numpy as np
import pytest
from cosmos_framework.evaluation.robocasa_v2 import generated_video
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink, _encode

from tools.v3.eval_v2_replan_tests.support import png_frames


def delayed_encoder(queue, directory, fps, rollout, ack):
    release = Path(directory) / "release"
    while not release.exists():
        time.sleep(0.01)
    _encode(queue, directory, fps, rollout, ack)


def dead_encoder(*args):
    raise OSError(errno.ENOSPC, "injected full disk before VIDEO_SAVED")


def stalled_encoder(*args):
    while True:
        time.sleep(0.1)


def strict_sink(directory, **kwargs):
    options = dict(
        rollout=False,
        generated="all",
        grace_s=0.05,
        drain_timeout_s=10,
        identity=dict(
            task="CloseFridge", episode=0, generation=1, attempt_id="attempt-1"
        ),
    )
    options.update(kwargs)
    directory.mkdir(exist_ok=True)
    return MediaSink(directory, **options)


def test_queue_full_and_slow_encoder_wait_for_saved_not_two_second_grace(tmp_path):
    sink = strict_sink(tmp_path, target=delayed_encoder)
    # Four actual accepted items fill the bounded queue while the child is gated.
    for _ in range(4):
        sink.queue.put(("frame", np.zeros((32, 32, 3), dtype=np.uint8)), timeout=1)
    result, errors = [], []

    def save():
        try:
            result.append(sink.prediction(0, {"video": png_frames()}))
        except Exception as error:
            errors.append(error)

    thread = threading.Thread(target=save)
    thread.start()
    try:
        time.sleep(0.2)
        assert thread.is_alive() and not result and not errors
        assert not (tmp_path / "generated/replan_0000.mp4").exists()
        (tmp_path / "release").touch()
        thread.join(15)
        assert not thread.is_alive() and not errors
        receipt = result[0]
        assert receipt["status"] == "VIDEO_SAVED" and receipt["frames"] == 3
        assert (
            generated_video.inspect_video(
                tmp_path / receipt["path"], frames=3, size=[32, 32]
            )["sha256"]
            == receipt["sha256"]
        )
    finally:
        (tmp_path / "release").touch()
        thread.join(15)
        outcome = sink.close()
    assert outcome["dropped"] == 0 and not outcome["forced_encoder_cleanup"]
    assert (
        not outcome["process_cleanup_failed"]
        and outcome["generated_media"]["status"] == "COMPLETE"
    )
    assert not sink.process.is_alive() and not sink.queue._thread.is_alive()


@pytest.mark.parametrize("target", [dead_encoder, stalled_encoder])
def test_encoder_death_and_timeout_are_explicit_and_reaped(tmp_path, target):
    sink = strict_sink(tmp_path, target=target, drain_timeout_s=1)
    started = time.monotonic()
    try:
        with pytest.raises(RuntimeError, match="MEDIA_INCOMPLETE"):
            sink.prediction(0, {"video": png_frames()})
    finally:
        outcome = sink.close()
    assert time.monotonic() - started < 5
    assert outcome["generated_media"]["status"] == "MEDIA_INCOMPLETE"
    assert not outcome["process_cleanup_failed"] and not sink.process.is_alive()
    assert not sink.queue._thread.is_alive()
    assert not list(tmp_path.glob("generated/*.mp4"))


def test_final_replan_saved_before_immediate_close_and_replay_is_idempotent(tmp_path):
    sink = strict_sink(tmp_path)
    value = {"video": png_frames(), "_media_binding": {"request_key": "b" * 64}}
    try:
        receipt = sink.prediction(9, value)
        assert sink.prediction(9, value) == receipt
        assert len(list(tmp_path.glob("generated/*.mp4"))) == 1
        assert not list(tmp_path.glob("generated/.*.tmp.mp4"))
        outcome = sink.close()
        assert outcome["generated_media"]["saved"] == [9]
        assert (
            not outcome["forced_encoder_cleanup"]
            and not outcome["process_cleanup_failed"]
        )
    finally:
        sink.close()


def test_foreign_replay_does_not_overwrite_original_and_reports_incomplete(tmp_path):
    sink = strict_sink(tmp_path)
    try:
        receipt = sink.prediction(0, {"video": png_frames()})
        with pytest.raises(RuntimeError, match="MEDIA_INCOMPLETE"):
            sink.prediction(0, {"video": png_frames(), "_media_binding": "foreign"})
        assert generated_video.file_sha(tmp_path / receipt["path"]) == receipt["sha256"]
    finally:
        outcome = sink.close()
    assert outcome["generated_media"]["status"] == "MEDIA_INCOMPLETE"


def test_encode_error_returns_VIDEO_FAILED_without_publishing(tmp_path):
    sink = strict_sink(tmp_path)
    try:
        with pytest.raises(RuntimeError, match="VIDEO_FAILED"):
            sink.prediction(0, {"video": ["not-a-PNG"]})
    finally:
        outcome = sink.close()
    assert outcome["generated_media"]["status"] == "MEDIA_INCOMPLETE"
    assert not list(tmp_path.glob("generated/*.mp4"))
    assert not list(tmp_path.glob("generated/.*.tmp.mp4"))
    assert not outcome["process_cleanup_failed"]


@pytest.mark.parametrize("fault", ["disk_full", "decode_mismatch", "rename"])
def test_failed_atomic_encode_never_publishes_final_or_receipt(
    tmp_path, monkeypatch, fault
):
    if fault == "disk_full":
        monkeypatch.setattr(
            generated_video.os,
            "fsync",
            lambda *_: (_ for _ in ()).throw(OSError(errno.ENOSPC, "full")),
        )
    elif fault == "decode_mismatch":
        monkeypatch.setattr(
            generated_video,
            "inspect_video",
            lambda *a, **k: (_ for _ in ()).throw(ValueError("frame count")),
        )
    else:
        monkeypatch.setattr(
            generated_video.os,
            "replace",
            lambda *_: (_ for _ in ()).throw(OSError(errno.EIO, "rename")),
        )
    with pytest.raises((ValueError, OSError)):
        generated_video.write_generated(
            tmp_path, {"index": 0, "video": png_frames(), "binding": {}}, 20
        )
    assert not list(tmp_path.glob("generated/*.mp4"))
    assert not list(tmp_path.glob("generated/*.json"))
    assert not list(tmp_path.glob("generated/.*.tmp.mp4"))


@pytest.mark.parametrize("mode", ["none", "first"])
def test_optional_modes_keep_nonblocking_fast_path(tmp_path, mode):
    sink = MediaSink(
        tmp_path, rollout=False, generated=mode, grace_s=0.05, target=stalled_encoder
    )
    try:
        for i in range(10):
            assert sink.prediction(i, {"video": png_frames()}) is None
        assert sink._ack is None and not sink.saved
    finally:
        outcome = sink.close()
    assert "generated_media" not in outcome and not outcome["process_cleanup_failed"]
