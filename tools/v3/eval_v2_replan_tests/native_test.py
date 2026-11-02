"""Actual native Episode/HTTP/action codec, synthetic physics/model and CPU video."""
# ruff: noqa: F811 -- pytest resolves imported fixture names in parameters.

import json
import time

import numpy as np
import pytest
from cosmos_framework.simulation.robocasa import closed_loop_eval as native
from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode

from tools.v3.eval_v2_replan_tests.support import (
    clock_kernel as clock_kernel,
)
from tools.v3.eval_v2_replan_tests.support import (
    http_server,
    registration,
)
from tools.v3.eval_v2_replan_tests.support import (
    systems as systems,
)


class Environment:
    def __init__(self, success_at=145):
        self.success_at, self.steps = success_at, 0
        self.actions = []
        self.observation = {
            f"{cam}_image": np.zeros((256, 256, 3), dtype=np.uint8)
            for cam in native.CAMS
        }

    def reset(self):
        self.steps = 0
        return self.observation

    def step(self, action):
        self.steps += 1
        self.actions.append(action.copy())
        return self.observation, 0.0, False, {}

    def _check_success(self):
        return self.steps >= self.success_at

    def get_ep_meta(self):
        return {"lang": "Close the fridge / 关闭冰箱"}


@pytest.mark.parametrize("fault", [False, True])
def test_native_last_replan_immediate_success_media_fault_keeps_Core_End_ACK(
    tmp_path, monkeypatch, systems, fault
):
    service, actor, direct = systems()
    assignment = registration(direct)
    if fault:
        actor.decode_media = lambda _: (_ for _ in ()).throw(
            OSError("injected media decoder failure")
        )
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    env = Environment()
    with http_server(service) as (base, _):
        settings = dict(
            server_url=base,
            horizon=160,
            predict_timeout_s=5,
            max_infer_batch_size=1,
            execution_profile="phase_b",
            local_memory_mode="off",
            save_generated_video="all",
            save_rollout_mp4=False,
            encoder_grace_s=0.1,
            media_drain_timeout_s=10,
        )
        episode = NativeEpisode(env, settings)
        assert episode.initialize()["initial_success"] is False
        attempt = dict(
            task="CloseFridge",
            episode=0,
            generation=1,
            attempt_id="attempt-1",
            stream_id="stream-1",
            seed=0,
            manifest_digest="a" * 64,
        )
        result = episode.execute(
            attempt,
            reset_index=0,
            directory=tmp_path / "episode",
            transaction_assignment=assignment,
            episode_deadline=time.monotonic() + 90,
        )
    assert result["observation"]["environment_success"] is True
    assert (
        result["replans"] == 10 and len(env.actions) == 145 and len(service.calls) == 10
    )
    assert (
        result["local_session"]["reset_ack"] is True and actor.info()["sessions"] == 0
    )
    assert not result["media_process_fault"]
    completion = json.loads(
        (tmp_path / "episode/generated_media_completion.json").read_bytes()
    )
    assert completion["status"] == ("MEDIA_INCOMPLETE" if fault else "COMPLETE")
    assert completion["expected"] == 10
    if not fault:
        assert (
            completion["saved"] == completion["acknowledged"] == 10
            and completion["missing"] == []
        )
    else:
        assert completion["saved"] == 0 and completion["missing"] == list(range(10))
    predictions = [
        json.loads(x)
        for x in (tmp_path / "episode/predictions.jsonl").read_text().splitlines()
    ]
    assert [x["source_step"] for x in predictions] == list(range(0, 145, 16))
