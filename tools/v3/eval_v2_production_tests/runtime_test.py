"""Production Slot-pool runtime with real native HTTP codecs, fake physics/GPUs."""

import json

import pytest
from cosmos_framework.evaluation.robocasa_v2.scheduler import logical_plan
from cosmos_framework.evaluation.robocasa_v2.store import Store, records
from robocasa_eval_v2.runtime import Runtime

from tools.v3.eval_v2_production_tests.native_test import server
from tools.v3.eval_v2_production_tests.slot_test import CpuSlotRuntime, prepare_monkey
from tools.v3.eval_v2_production_tests.store_test import fresh


def cfg(g=3, episodes=2):
    return {
        "gpu_ids": list(range(g)),
        "episodes_per_task": episodes,
        "base_port": 18000,
        "terminate_grace_s": 0.2,
    }


@pytest.mark.parametrize("g", [1, 2, 3, 4, 8])
@pytest.mark.parametrize("n", [1, 2, 4, 7, 18])
def test_dynamic_GPU_Task_matrix_runs_actual_runtime_Slot_and_native_code(
    tmp_path, monkeypatch, g, n
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, tasks=tuple(f"Task{i}" for i in range(n)), episodes=2)
    events = []
    with server() as (url, calls), value.locked():
        runtime = CpuSlotRuntime(value, cfg(g), url, events)
        report, error = runtime.run()
        assert (
            error is None and report["valid"] == n * 2 and report["results_qualified"]
        )
        assert (
            runtime.max_actors <= min(g, n)
            and len(runtime.server_loads) == runtime.max_actors
        )
        ledger = records(next((value.root / "_internal/scheduler").iterdir()))
        assert [
            (v["data"]["task"], v["data"]["episode"])
            for v in ledger
            if v["kind"] == "DISPATCH"
        ] == logical_plan(value.manifest)
        assert sum(v["kind"] == "ROUND_BARRIER" for v in ledger) == 2
        active = peak = 0
        for kind, *rest in events:
            if kind == "make":
                active += 1
            elif kind == "close":
                active -= 1
            peak = max(peak, active)
        assert active == 0 and peak <= min(g, n)
        rows = [
            json.loads(x)
            for x in (value.root / "episodes.jsonl").read_text().splitlines()
        ]
        assert all(
            r["sampling"]["actual_seed"] >= 0
            and r["sampling"]["environment_reset_index"] >= 0
            for r in rows
        )
        assert len({r["sampling"]["physical_slot_id"] for r in rows}) <= g
        requests = [c["local_memory"] for c in calls if "local_memory" in c]
        assert len(requests) == 2 * n and all(
            m["reset"] is True and m["consumer_step"] == 0 and not m["evidence"]
            for m in requests
        )
        assert len({r["session_id"] for r in requests}) == 2 * n


def test_real_runtime_rounds_native_Core_then_resume_no_model_or_env_work(
    tmp_path, monkeypatch
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, tasks=("TaskB", "TaskA", "TaskC"), episodes=2)
    with server() as (url, calls), value.locked():
        runtime = CpuSlotRuntime(value, cfg(2), url, [])
        report, error = runtime.run()
        assert error is None and report["success"] == 4 and report["failure"] == 2
        before = {
            str(p): p.read_bytes()
            for p in value.root.glob("tasks/*/episodes/*/result.json")
        }
        runtime.close()  # idempotent
    with Store(value.root, value.manifest).locked() as resumed:
        runtime = Runtime(
            resumed,
            cfg(2),
            {},
            {},
            resource_probe=lambda *a, **kw: pytest.fail(
                "completed Resume cannot inspect GPU"
            ),
        )
        report, error = runtime.run()
        assert error is None and report["valid"] == 6
        assert before == {
            str(p): p.read_bytes()
            for p in value.root.glob("tasks/*/episodes/*/result.json")
        }


def test_runtime_recovery_marks_unclosed_old_stream_before_new_work(tmp_path):
    value = fresh(tmp_path, episodes=1)
    with value.locked():
        old = value.begin_task("CloseFridge")
    with Store(value.root, value.manifest).locked() as resumed:
        runtime = Runtime(
            resumed, cfg(1, 1), {}, {}, resource_probe=lambda *a, **k: None
        )
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
    from tools.v3.eval_v2_production_tests.store_test import close_streams, complete

    prepare_monkey(monkeypatch)
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
    with Store(value.root, value.manifest).locked() as resumed:
        report, error = Runtime(
            resumed,
            cfg(1),
            {},
            {},
            resource_probe=lambda *a, **k: pytest.fail("cannot auto-retry skip"),
        ).run()
        assert error is None and report["skipped_init_error"] == 1
    with (
        server() as (url, calls),
        Store(value.root, value.manifest).locked() as resumed,
    ):
        resumed.authorize_retry(
            "CloseFridge", 0, owner_ref="CPU explicit Owner release"
        )
        report, error = CpuSlotRuntime(resumed, cfg(1), url, []).run()
        assert (
            error is None
            and report["valid"] == 2
            and report["success"] == report["failure"] == 1
        )
        assert len([c for c in calls if "local_memory" in c]) == 1
        assert (
            resumed._slot("CloseFridge", 1) / "result.json"
        ).read_bytes() == original


def test_actual_runtime_four_init_errors_release_clean_and_continue_other_task(
    tmp_path, monkeypatch
):
    from tools.v3.eval_v2_production_tests.slot_test import TrackedEnv

    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, tasks=("TaskA", "TaskB"), episodes=2)
    events = []

    class RandomizationError(Exception):
        pass

    RandomizationError.__module__ = "robosuite.utils.errors"

    class Rejected(TrackedEnv):
        def reset(self):
            if self.task == "TaskA":
                raise RandomizationError("CPU recoverable sampler")
            return super().reset()

    with server() as (url, calls), value.locked():
        runtime = CpuSlotRuntime(
            value,
            cfg(1),
            url,
            events,
            factory=lambda t, s, g: Rejected(t, g["seed"], events, success_at=1),
        )
        report, error = runtime.run()
        assert (
            error is None and report["skipped_init_error"] == 2 and report["valid"] == 2
        )
        assert (
            report["sr"] is None
            and report["clean_execution"]
            and len([x for x in calls if "local_memory" in x]) == 2
        )
        assert runtime.actors[runtime.workers[0]].slot.state == "CLEAN"
    with Store(value.root, value.manifest).locked() as resumed:
        report, error = Runtime(
            resumed,
            cfg(1),
            {},
            {},
            resource_probe=lambda *a, **kw: pytest.fail(
                "Owner-pending slots cannot auto-run"
            ),
        ).run()
        assert (
            error is None and report["skipped_init_error"] == 2 and report["valid"] == 2
        )


def test_runtime_quarantine_then_explicit_resume_uses_new_slot_session_and_proofs(
    tmp_path, monkeypatch
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, episodes=1)
    with server(reset_failure=True) as (url, first_calls), value.locked():
        old = CpuSlotRuntime(value, cfg(1, 1), url, [])
        report, error = old.run()
        assert error is not None and report["valid"] == 0 and report["invalid"] == 1
        assert not report["results_qualified"] and value.errors("CloseFridge")
        old_session = next(
            c["local_memory"]["session_id"] for c in first_calls if "local_memory" in c
        )
    with (
        server() as (url, calls),
        Store(value.root, value.manifest).locked() as resumed,
    ):
        new = CpuSlotRuntime(resumed, cfg(1, 1), url, [])
        report, error = new.run()
        assert error is None and report["valid"] == 1 and report["results_qualified"]
        assert (
            report["resolved_process_errors"] > 0
            and not report["unresolved_process_errors"]
        )
        payload = next(c["local_memory"] for c in calls if "local_memory" in c)
        assert (
            payload["session_id"] != old_session
            and payload["reset"] is True
            and payload["consumer_step"] == 0
            and not payload["evidence"]
        )
        assert old.slot_ids != new.slot_ids


def test_late_zero_exit_after_valid_core_blocks_clean_without_retesting(
    tmp_path, monkeypatch
):
    prepare_monkey(monkeypatch)
    value = fresh(tmp_path, episodes=1)

    class LateExit(CpuSlotRuntime):
        def _actor(self, claim):
            actor = super()._actor(claim)
            actor.owned.proc.poll = lambda: 0 if actor.slot.state == "CLEAN" else None
            return actor

    with server() as (url, calls), value.locked():
        report, error = LateExit(value, cfg(1, 1), url, []).run()
        assert error is not None and report["valid"] == 1 and report["sr"] == 1.0
        assert not report["clean_execution"] and not report["results_qualified"]
        faults = value.errors("CloseFridge")
        assert faults and all(e["core_committed_at_fault"] for e in faults)
        original = (value._slot("CloseFridge", 0) / "result.json").read_bytes()
    with (
        server() as (url, calls),
        Store(value.root, value.manifest).locked() as resumed,
    ):
        report, error = CpuSlotRuntime(resumed, cfg(1, 1), url, []).run()
        assert (
            error is None
            and report["results_qualified"]
            and report["resolved_process_errors"]
        )
        assert not calls  # execution-only fresh health, never repeat a valid Episode.
        assert (
            resumed._slot("CloseFridge", 0) / "result.json"
        ).read_bytes() == original
