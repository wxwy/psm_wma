"""Production native loop + real HTTP codec/client, fake environment/model only."""

import json
import threading
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import numpy as np
import pytest
from cosmos_framework.evaluation.robocasa_v2.contract import result_record
from cosmos_framework.evaluation.robocasa_v2.evidence import validate
from cosmos_framework.simulation.robocasa import closed_loop_eval as native
from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode

from tools.v3.eval_v2_production_tests.store_test import fresh

RAW = [0.2, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.5]


@contextmanager
def server(*, bad_ack=False, reset_failure=False):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            value = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(value)
            if value.get("_local_memory_command") == "reset":
                response = {
                    "local_memory": {
                        "status": "wrong" if reset_failure else "reset",
                        "session_id": value["session_id"],
                    }
                }
            else:
                m = value["local_memory"]
                response = {
                    "action": [RAW] * 16,
                    "local_memory": {
                        k: m[k] for k in ("session_id", "episode_id", "consumer_step")
                    },
                }
                if bad_ack:
                    response["local_memory"]["consumer_step"] += 1
            raw = json.dumps(response).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    t = threading.Thread(target=http.serve_forever, daemon=True)
    t.start()
    try:
        yield f"http://127.0.0.1:{http.server_port}", calls
    finally:
        http.shutdown()
        http.server_close()
        t.join(2)


class Env:
    def __init__(self, success_at=2, initial=False, predicate_error=False):
        self.resets = 0
        self.steps = 0
        self.success_at = success_at
        self.initial = initial
        self.predicate_error = predicate_error
        self.actions = []
        self.obs = {
            f"{cam}_image": np.zeros((256, 256, 3), np.uint8) for cam in native.CAMS
        }
        self.sim = SimpleNamespace(
            data=SimpleNamespace(qpos=np.zeros(1), qvel=np.zeros(1)),
            forward=lambda: None,
        )

    def reset(self):
        self.resets += 1
        self.steps = 0
        return self.obs

    def get_ep_meta(self):
        return {"lang": "Actual Episode instruction / 关闭冰箱"}

    def step(self, action):
        self.actions.append(action.copy())
        self.steps += 1
        return self.obs, 99.0, False, {}

    def _check_success(self):
        if self.steps and self.predicate_error:
            raise RuntimeError("post-action predicate broke")
        return self.initial if self.steps == 0 else self.steps >= self.success_at

    def close(self):
        pass


class BadMedia:
    def __init__(self, *a, **k):
        pass

    def frame(self, *a):
        raise OSError("encoder/frame failure")

    def prediction(self, *a):
        raise OSError("generated decode failure")

    def close(self):
        return {"errors": ["bad media"], "independent_of_SR": True}


def native_execute(
    tmp_path,
    monkeypatch,
    *,
    success_at=2,
    horizon=2,
    media_factory=None,
    bad_ack=False,
    reset_failure=False,
    predicate_error=False,
):
    value = fresh(tmp_path, episodes=1)
    # Test fake environment has no robosuite dependency. Native raw15 decoder,
    # HTTP prediction, Local ledger/ack/completed evidence/end/reset are real.
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    value.manifest["horizons"]["CloseFridge"] = horizon
    # Rebuild manifest when changing scientific horizon.
    from cosmos_framework.evaluation.robocasa_v2.contract import build_manifest

    m = value.manifest
    m = build_manifest(
        tasks=m["tasks"],
        episodes=1,
        seed=m["seed"],
        horizons={"CloseFridge": horizon},
        experiment=m["experiment"],
    )
    from cosmos_framework.evaluation.robocasa_v2.store import Store

    value = Store(tmp_path / "native", m)
    value.create()
    env = Env(success_at, predicate_error=predicate_error)
    with (
        server(bad_ack=bad_ack, reset_failure=reset_failure) as (url, calls),
        value.locked(),
    ):
        value.begin_task("CloseFridge")
        a = value.begin_episode("CloseFridge", 0)
        engine = NativeEpisode(
            env,
            {
                "server_url": url,
                "horizon": horizon,
                "predict_timeout_s": 2.0,
                "save_rollout_mp4": False,
                "save_generated_video": "none",
            },
            **({"media_factory": media_factory} if media_factory else {}),
        )
        value.begin_initialization(a)
        result = engine.initialize()
        assert result["initial_success"] is False
        state = value.initialization_outcome(a, initial_success=False)
        directory = value._ledger("CloseFridge", 0) / "work" / a["attempt_id"]
        result = engine.execute(
            a,
            reset_index=state["last_event"]["data"]["reset_index"],
            directory=directory,
        )
        row = result_record(
            m,
            task="CloseFridge",
            episode=0,
            generation=a["generation"],
            attempt_id=a["attempt_id"],
            worker_id=a["worker_id"],
            stream_id=a["stream_id"],
            seed=a["seed"],
            reset_index=0,
            **result_to_kwargs(result),
        )
        validate(directory, row)
        value.commit(row, staging=directory)
        return row, env, calls, value


def result_to_kwargs(result):
    return {
        k: result[k]
        for k in ("observation", "instruction", "replans", "elapsed_seconds")
    }


def test_native_http_Local_two_replans_raw15_env12_real_evidence_and_one_reset(
    tmp_path, monkeypatch
):
    row, env, calls, value = native_execute(
        tmp_path, monkeypatch, success_at=17, horizon=20
    )
    assert row["outcome"] == "success" and row["steps"] == 17 and row["replans"] == 2
    assert (
        env.resets == 1
        and len(env.actions) == 17
        and all(x.shape == (12,) for x in env.actions)
    )
    assert (
        calls[0]["local_memory"]["consumer_step"] == 0
        and calls[0]["local_memory"]["reset"] is True
    )
    assert (
        len(calls[1]["local_memory"]["evidence"]) == 16
        and calls[1]["local_memory"]["consumer_step"] == 16
    )
    assert calls[-1]["_local_memory_command"] == "reset"
    assert row["instruction"] == "Actual Episode instruction / 关闭冰箱"
    assert (value._slot("CloseFridge", 0) / "actions.jsonl").is_file()


def test_broken_media_never_changes_environment_success_or_Core_commit(
    tmp_path, monkeypatch
):
    row, env, calls, value = native_execute(
        tmp_path, monkeypatch, media_factory=BadMedia
    )
    assert row["outcome"] == "success" and row["steps"] == 2
    assert (
        calls[-1]["_local_memory_command"] == "reset"
        and len(value.rows("CloseFridge")) == 1
    )


def test_horizon_failure_with_high_reward_is_valid_and_never_retried(
    tmp_path, monkeypatch
):
    row, env, calls, value = native_execute(tmp_path, monkeypatch, success_at=100)
    assert row["outcome"] == "failure" and row["steps"] == 2
    with value.locked():
        with pytest.raises(ValueError, match="immutable"):
            value.begin_episode("CloseFridge", 0)


@pytest.mark.parametrize(
    "options", [{"bad_ack": True}, {"reset_failure": True}, {"predicate_error": True}]
)
def test_native_ack_reset_or_strict_predicate_error_never_publishes_failure(
    tmp_path, monkeypatch, options
):
    with pytest.raises((RuntimeError, ValueError)):
        native_execute(tmp_path, monkeypatch, **options)
    assert not list((tmp_path / "native").glob("tasks/*/episodes/ep_*/result.json"))


def test_initial_success_rejection_calls_no_policy_or_Local(tmp_path):
    env = Env(initial=True)
    engine = NativeEpisode(
        env,
        {
            "server_url": "http://unused",
            "horizon": 2,
            "predict_timeout_s": 1.0,
            "save_rollout_mp4": False,
        },
    )
    assert engine.initialize()["initial_success"] is True and not env.actions
    with pytest.raises(ValueError, match="admitted"):
        engine.execute({}, reset_index=0, directory=tmp_path / "unused")


def test_native_v2_http_ignores_proxy_and_uses_owned_loopback(tmp_path, monkeypatch):
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")
    monkeypatch.setenv("NO_PROXY", "")
    row, env, calls, value = native_execute(tmp_path, monkeypatch)
    assert row["outcome"] == "success" and calls[-1]["_local_memory_command"] == "reset"
