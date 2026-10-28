"""Real CPU encoding process, bounded error paths; never ffmpeg-decode MP4."""

import base64
import io
import random
import time

import numpy as np
from cosmos_framework.evaluation.robocasa_v2.media import MediaSink
from PIL import Image


def stalled_encoder(queue, directory, fps, rollout):
    time.sleep(60)


def test_real_cpu_stream_encoder_writes_single_rollout_and_generated_clip(tmp_path):
    frame = np.zeros((16, 16, 3), np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(frame).save(buffer, format="PNG")
    py = random.getstate()
    npstate = np.random.get_state()
    sink = MediaSink(tmp_path / "media", rollout=True, generated="all", grace_s=10.0)
    sink.frame(frame)
    sink.prediction(0, {"video": [base64.b64encode(buffer.getvalue()).decode()]})
    result = sink.close()
    assert not result["forced_encoder_cleanup"] and result["dropped"] == 0
    assert (tmp_path / "media/rollout.mp4").stat().st_size > 0
    assert (tmp_path / "media/generated/replan_0000.mp4").stat().st_size > 0
    assert random.getstate() == py and np.array_equal(
        np.random.get_state()[1], npstate[1]
    )


def test_stalled_encoder_is_bounded_and_requests_owned_task_cleanup(tmp_path):
    sink = MediaSink(tmp_path / "media", grace_s=0.1, target=stalled_encoder)
    for _ in range(10):
        sink.frame(np.zeros((16, 16, 3), np.uint8))
    start = time.monotonic()
    result = sink.close()
    assert result["forced_encoder_cleanup"] and not sink.process.is_alive()
    assert result["dropped"] > 0 and time.monotonic() - start < 2


def test_optional_generated_video_bounds_do_not_throw_into_policy(tmp_path):
    sink = MediaSink(tmp_path, rollout=False, generated="none")
    sink.generated = "all"
    sink.prediction(0, {"video": ["x"] * 66})
    assert sink.close()["errors"]
