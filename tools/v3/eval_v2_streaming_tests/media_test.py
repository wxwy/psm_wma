"""No no-op rollout composition, and neither strict media nor Ready Policy starves."""
# ruff: noqa: F811 -- imported pytest fixtures.

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from tools.v3.eval_v2_production_tests.native_test import native, native_execute
from tools.v3.eval_v2_replan_tests.support import (
    systems as systems,
    clock_kernel as clock_kernel,
    client,
    predict,
    registration,
)


def test_none_without_rollout_has_only_policy_and_required_local_compositions(
    tmp_path, monkeypatch
):
    original = native.compose
    calls = []

    def compose(obs):
        calls.append(None)
        return original(obs)

    monkeypatch.setattr(native, "compose", compose)
    row, env, requests, value = native_execute(
        tmp_path, monkeypatch, success_at=17, horizon=20
    )
    # One initial view + two Policy observations + 17 completed Local evidence views.
    assert row["steps"] == 17 and row["replans"] == 2 and len(calls) == 20
    assert not list(value.root.glob("**/*.mp4"))


def test_ready_inference_between_two_strict_decodes_and_strict_decode_not_starved(
    systems,
):
    _, actor, direct = systems(max_batch_size=2, batch_wait_ms=1000)
    values = [
        client(
            direct,
            registration(direct, i),
            "all" if i < 2 else "none",
            max_infer_batch_size=2,
        )
        for i in range(3)
    ]
    generate, decode = actor.generate_many, actor.decode_media
    entered, release = threading.Event(), threading.Event()
    order = []

    def generating(payloads, updates):
        order.append(f"generate{len(payloads)}")
        if len(payloads) == 2:
            entered.set()
            assert release.wait(5)
        return generate(payloads, updates)

    def decoding(value):
        order.append("decode")
        return decode(value)

    actor.generate_many, actor.decode_media = generating, decoding
    with ThreadPoolExecutor(3) as pool:
        first = [pool.submit(predict, value) for value in values[:2]]
        try:
            assert entered.wait(3)
            last = pool.submit(predict, values[2])
            limit = time.monotonic() + 3
            while actor.info()["queued"] != 1:
                assert time.monotonic() < limit
                time.sleep(0.01)
            release.set()
            for task in [*first, last]:
                assert len(task.result(5)["action"]) == 16
            assert order == ["generate2", "decode", "generate1", "decode"]
        finally:
            release.set()
            for value in values:
                value.close()
