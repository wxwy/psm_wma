"""Actual production runtime + native HTTP loop with fake simulator/resources."""

from contextlib import ExitStack
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.native_test import Env, native, server
from tools.v3.eval_v2_production_tests.store_test import fresh


class CpuActor:
    def __init__(self, engine, pid):
        self.engine = engine
        self.owned = SimpleNamespace(
            proc=SimpleNamespace(pid=pid, poll=lambda: None), pgid=pid
        )
        self.channel = SimpleNamespace(shutdown=lambda *x: None)

    def request(self, op, **kwargs):
        if op == "initialize":
            return self.engine.initialize()
        if op == "execute":
            return self.engine.execute(
                kwargs["attempt"],
                reset_index=kwargs["reset_index"],
                directory=kwargs["directory"],
            )
        raise ValueError(op)

    def close(self):
        self.engine.env.close()
        return {"close_error": None}


def test_real_runtime_rounds_native_Core_then_resume_no_model_or_env_work(
    tmp_path, monkeypatch
):
    from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode

    value = fresh(tmp_path, tasks=("TaskB", "TaskA", "TaskC"), episodes=2)
    cfg = {
        "gpu_ids": [4, 5, 6],
        "episodes_per_task": 2,
        "base_port": 55000,
        "terminate_grace_s": 0.2,
    }
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.identity.guard", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.group_members", lambda pgid: {pgid: "S"}
    )
    counts = {"envs": 0, "resource_checks": 0}

    def resource(*a, **k):
        counts["resource_checks"] += 1

    with ExitStack() as stack:
        urls = [stack.enter_context(server())[0] for _ in range(3)]

        class RealCpuRuntime(Runtime):
            def _actor(self, claim):
                task = claim["task"]
                with self.setup_lock:
                    if task not in self.actors:
                        counts["envs"] += 1
                        slot = self.workers.index(claim["physical_worker"])
                        engine = NativeEpisode(
                            Env(success_at=100 if task == "TaskA" else 1),
                            {
                                "server_url": urls[slot],
                                "horizon": 2,
                                "predict_timeout_s": 2.0,
                                "save_rollout_mp4": False,
                                "save_generated_video": "none",
                            },
                        )
                        self.actors[task] = CpuActor(engine, 80000 + slot)
                    return self.actors[task]

        with value.locked():
            runtime = RealCpuRuntime(value, cfg, {}, {}, resource_probe=resource)
            report, error = runtime.run()
            errors_before = len(value.errors("TaskB"))
            runtime.close()  # Idempotent CLI failure cleanup must not invent a late fault.
            assert len(value.errors("TaskB")) == errors_before
        assert (
            error is None
            and report["valid"] == 6
            and report["success"] == 4
            and report["failure"] == 2
        )
        assert report["results_qualified"] and counts["envs"] == 3
        before = {
            str(p): p.read_bytes()
            for p in value.root.glob("tasks/*/episodes/*/result.json")
        }
        with Store(value.root, value.manifest).locked() as resumed:
            runtime = RealCpuRuntime(
                resumed,
                cfg,
                {},
                {},
                resource_probe=lambda *a, **k: pytest.fail(
                    "fully completed Resume must not inspect/use GPU"
                ),
            )
            report, error = runtime.run()
        assert error is None and report["valid"] == 6 and counts["envs"] == 3
        assert before == {
            str(p): p.read_bytes()
            for p in value.root.glob("tasks/*/episodes/*/result.json")
        }


def test_runtime_recovery_marks_unclosed_old_stream_before_new_work(tmp_path):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        old = value.begin_task("CloseFridge")
    with Store(value.root, value.manifest).locked() as resumed:
        cfg = {"gpu_ids": [4], "terminate_grace_s": 0.2}
        runtime = Runtime(resumed, cfg, {}, {}, resource_probe=lambda *a, **k: None)
        runtime.recover()
        error = resumed.errors("CloseFridge")[0]
        assert (
            error["stream_id"] == old["stream_id"]
            and error["stage"] == "unclosed_prior_coordinator"
        )
        assert error["resolution"] is None and resumed._cleaned(
            "CloseFridge", old["stream_id"]
        )


def test_real_runtime_executes_only_owner_released_hole_not_valid_later_failure(
    tmp_path, monkeypatch
):
    from cosmos_framework.simulation.robocasa.eval_v2_adapter import NativeEpisode

    from tools.v3.eval_v2_production_tests.store_test import close_streams, complete

    value = fresh(tmp_path, episodes=2)
    with value.locked():
        value.begin_task("CloseFridge")
        a = value.begin_episode("CloseFridge", 0)
        for _ in range(4):
            value.begin_initialization(a)
            value.initialization_outcome(
                a, error=ValueError("reset"), stage="reset", safe_to_retry=True
            )
        complete(value, "CloseFridge", 1, success=False)
        close_streams(value, "CloseFridge")
        original = (value._slot("CloseFridge", 1) / "result.json").read_bytes()
    cfg = {
        "gpu_ids": [4],
        "episodes_per_task": 2,
        "base_port": 55000,
        "terminate_grace_s": 0.2,
    }
    monkeypatch.setattr(native, "build_state_token", lambda _: [0.0] * 15)
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.identity.guard", lambda *a, **kw: None
    )
    monkeypatch.setattr(
        "robocasa_eval_v2.runtime.group_members", lambda pgid: {pgid: "S"}
    )
    with Store(value.root, value.manifest).locked() as resumed:
        report, error = Runtime(
            resumed,
            cfg,
            {},
            {},
            resource_probe=lambda *a, **k: pytest.fail(
                "ordinary Resume cannot auto-retry skip"
            ),
        ).run()
        assert error is None and report["skipped_init_error"] == 1
    with (
        server() as (url, calls),
        Store(value.root, value.manifest).locked() as resumed,
    ):
        resumed.authorize_retry(
            "CloseFridge", 0, owner_ref="CPU explicit Owner release"
        )

        class Targeted(Runtime):
            def _actor(self, claim):
                actor = CpuActor(
                    NativeEpisode(
                        Env(success_at=1),
                        {
                            "server_url": url,
                            "horizon": 2,
                            "predict_timeout_s": 2.0,
                            "save_rollout_mp4": False,
                            "save_generated_video": "none",
                        },
                    ),
                    80000,
                )
                self.actors[claim["task"]] = actor
                return actor

        report, error = Targeted(
            resumed, cfg, {}, {}, resource_probe=lambda *a, **k: None
        ).run()
        assert (
            error is None
            and report["valid"] == 2
            and report["success"] == report["failure"] == 1
        )
        assert len([c for c in calls if not c.get("_local_memory_command")]) == 1
        assert (
            resumed._slot("CloseFridge", 1) / "result.json"
        ).read_bytes() == original
