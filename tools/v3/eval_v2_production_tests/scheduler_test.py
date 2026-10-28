"""D5 actual coordinator/attempt/Core path with fake asynchronous CPU workers."""

import json
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from threading import Event

import pytest
from cosmos_framework.evaluation.robocasa_v2.admission import admit_scene
from cosmos_framework.evaluation.robocasa_v2.scheduler import (
    RoundScheduler,
    logical_plan,
)
from cosmos_framework.evaluation.robocasa_v2.store import Store, records

from tools.v3.eval_v2_production_tests.admission_test import FakeInit, safe_recover
from tools.v3.eval_v2_production_tests.contract_test import record
from tools.v3.eval_v2_production_tests.store_test import (
    Crash,
    admitted,
    bytes_of_results,
    close_streams,
    complete,
    fixture_core,
    fresh,
    inject,
)

WORKERS = ["GPU4", "GPU5", "GPU6"]


def commit_claim(scheduler, claim, success=True, finish=True):
    value = scheduler.store
    a = admitted(value, claim["attempt"])
    reset = value.events(a)[-1]["data"]["reset_index"]
    row = record(
        value.manifest, {**a, "reset_index": reset}, a["episode"], success=success
    )
    scheduler.commit(claim, row, staging=fixture_core(value, a, row))
    if finish:
        scheduler.finish(claim)
    return row


def drain(scheduler, *, fail_odd=False):
    dispatched = []
    while not scheduler.done:
        progress = False
        for worker in scheduler.workers:
            claim = scheduler.dispatch(worker)
            if claim is not None:
                dispatched.append((claim["task"], claim["episode"]))
                commit_claim(
                    scheduler, claim, success=not fail_odd or claim["episode"] % 2 == 0
                )
                progress = True
        if not progress and not scheduler.done:
            raise AssertionError("scheduler stalled without in-flight worker")
    return dispatched


def test_900_exact_episode_major_dispatch_real_store_path_and_index_no_model_per_episode(
    tmp_path,
):
    # Intentionally not lexicographic: manifest must preserve Owner's Task order.
    tasks = tuple(
        f"Task{i:02d}"
        for i in [6, 1, 12, 4, 0, 17, 2, 5, 7, 3, 8, 9, 10, 11, 13, 14, 15, 16]
    )
    value = fresh(tmp_path, tasks=tasks, episodes=50, formal=True)
    assert value.manifest["tasks"] == value.manifest["task_order"] == list(tasks)
    expected = [(t, ep) for ep in range(50) for t in tasks]
    assert logical_plan(value.manifest) == expected and len(set(expected)) == 900
    model_loads = dict.fromkeys(WORKERS, 0)
    env_builds = dict.fromkeys(tasks, 0)
    task_streams = {}
    with value.locked():
        scheduler = RoundScheduler(value, WORKERS)
        for w in WORKERS:
            model_loads[w] += 1  # mock lifecycle, NOT real model loads.
        dispatched = []
        while not scheduler.done:
            for worker in WORKERS:
                claim = scheduler.dispatch(worker)
                if claim is None:
                    continue
                task = claim["task"]
                a = claim["attempt"]
                if task not in task_streams:
                    env_builds[task] += 1
                    task_streams[task] = a["stream_id"]
                assert task_streams[task] == a["stream_id"]
                dispatched.append((task, claim["episode"]))
                commit_claim(scheduler, claim, success=claim["episode"] % 2 == 0)
        assert dispatched == expected
        assert all(n == 1 for n in model_loads.values()) and all(
            n == 1 for n in env_builds.values()
        )
        for task in tasks:
            close_streams(value, task)
        report = value.publish_views()
        events = records(value.root / "_internal/scheduler" / scheduler.invocation)
    assert report["valid"] == 900 and report["success"] == report["failure"] == 450
    assert report["sr"] == 0.5 and report["results_qualified"]
    rows = [
        json.loads(line)
        for line in (value.root / "episodes.jsonl").read_text().splitlines()
    ]
    assert [(r["task"], r["episode"]) for r in rows] == expected
    assert sum(e["kind"] == "ROUND_BARRIER" for e in events) == 50
    assert sum(e["kind"] == "DISPATCH" for e in events) == 900
    (value.root / "summary.json").write_bytes(b"broken derived view")
    with value.locked():
        assert value.publish_views() == report
    print(
        "V2_PRODUCTION_COORDINATION_METRICS " + json.dumps(value.metrics()), flush=True
    )
    assert value.metrics()["record_io"]["disk_reads"] < 40000
    print(
        "V2_R2_SYNTHETIC_WITNESS "
        + json.dumps(
            {
                "tasks": 18,
                "episodes": 900,
                "success": 450,
                "failure": 450,
                "sr": 0.5,
                "prototype_only": False,
                "actual_scheduler_dispatch": 900,
                "round_barriers": 50,
                "mock_model_loads": model_loads,
                "mock_env_builds": sum(env_builds.values()),
            }
        )
    )


def test_three_asynchronous_workers_same_round_parallel_with_strict_barrier(tmp_path):
    tasks = tuple(f"Task{i:02d}" for i in range(18))
    value = fresh(tmp_path, tasks=tasks, episodes=2)
    other_finished = Event()
    first_started = Event()
    maximum = 0
    with value.locked(), ThreadPoolExecutor(max_workers=3) as executor:
        scheduler = RoundScheduler(value, WORKERS)

        def execute(claim):
            if claim["episode"] == 0 and claim["task"] == "Task00":
                first_started.set()
                assert other_finished.wait(10), "other worker never made progress"
            commit_claim(scheduler, claim, success=claim["episode"] == 0)
            if claim["episode"] == 0 and claim["task"] == "Task02":
                other_finished.set()

        futures = set()
        while not scheduler.done:
            for worker in WORKERS:
                if worker in scheduler.inflight:
                    continue
                c = scheduler.dispatch(worker)
                if c:
                    futures.add(executor.submit(execute, c))
            maximum = max(maximum, len(futures))
            if futures:
                completed, futures = wait(
                    futures, timeout=15, return_when=FIRST_COMPLETED
                )
                assert completed, "CPU worker watchdog"
                for f in completed:
                    f.result()
        assert first_started.is_set() and other_finished.is_set() and maximum >= 3
        events = records(value.root / "_internal/scheduler" / scheduler.invocation)
        dispatch = [
            (e["data"]["task"], e["data"]["episode"])
            for e in events
            if e["kind"] == "DISPATCH"
        ]
        assert dispatch == logical_plan(value.manifest)
        barriers = [i for i, e in enumerate(events) if e["kind"] == "ROUND_BARRIER"]
        first_round_done = max(
            i for i, e in enumerate(events) if e["kind"] == "FINISH" and e["round"] == 0
        )
        next_round_begin = min(
            i
            for i, e in enumerate(events)
            if e["kind"] == "DISPATCH" and e["round"] == 1
        )
        assert first_round_done < barriers[0] < next_round_begin
        assert len(value.summary()[1]) == 36


@pytest.mark.parametrize(
    "point",
    [
        "before_dispatch",
        "after_dispatch",
        "before_core_commit",
        "after_core_commit",
        "after_finish",
        "after_round_barrier",
    ],
)
def test_crash_resume_scans_same_plan_and_skips_exactly_valid_success_and_failure(
    tmp_path, point
):
    value = fresh(tmp_path, tasks=("TaskB", "TaskA", "TaskC"), episodes=3)
    old_claim = None
    with value.locked():
        scheduler = RoundScheduler(value, WORKERS)
        # Complete one first-round failure; all other crash points retain it.
        c = scheduler.dispatch("GPU4")
        commit_claim(scheduler, c, success=False)
        if point != "before_dispatch":
            old_claim = scheduler.dispatch("GPU5")
            if point in ("before_core_commit", "after_core_commit"):
                value.fault = inject(point)
                with pytest.raises(Crash):
                    commit_claim(scheduler, old_claim, finish=False)
            elif point in ("after_finish", "after_round_barrier"):
                commit_claim(scheduler, old_claim)
                if point == "after_round_barrier":
                    c = scheduler.dispatch("GPU6")
                    commit_claim(scheduler, c)
                    old_claim = scheduler.dispatch("GPU4")  # crosses barrier into ep1
            # after_dispatch has no Core evidence at all.
        original = bytes_of_results(value)
        committed = {
            (t, r["episode"])
            for t in value.manifest["task_order"]
            for r in value.rows(t)
        }
        scheduler.cancel("simulated coordinator interruption")
    resumed = Store(value.root, value.manifest)
    with resumed.locked():
        for t in value.manifest["task_order"]:
            close_streams(resumed, t)
        scheduler = RoundScheduler(resumed, WORKERS)
        if old_claim:
            row = record(resumed.manifest, old_claim["attempt"], old_claim["episode"])
            with pytest.raises(ValueError, match="stale"):
                scheduler.commit(old_claim, row, staging=None)
        dispatched = drain(scheduler)
        assert dispatched == [
            x for x in logical_plan(value.manifest) if x not in committed
        ]
        after = bytes_of_results(resumed)
        assert all(after[k] == v for k, v in original.items())
        assert resumed.rows("TaskB")[0]["outcome"] == "failure"
        assert len(resumed.summary()[1]) == 9


def test_owner_skipped37_and_valid38_are_both_skipped_on_resume_only_released_hole_runs(
    tmp_path,
):
    value = fresh(tmp_path, episodes=50)
    with value.locked():
        value.begin_task("CloseFridge")
        for ep in range(37):
            complete(value, "CloseFridge", ep, success=ep % 2 == 0)
        a = value.begin_episode("CloseFridge", 37)
        state, _ = admit_scene(value, a, FakeInit([OSError("reset")] * 4), safe_recover)
        assert state["status"] == "skipped_init_error"
        for ep in range(38, 50):
            complete(value, "CloseFridge", ep, success=False)
        close_streams(value, "CloseFridge")
        original = bytes_of_results(value)
    with Store(value.root, value.manifest).locked() as resumed:
        scheduler = RoundScheduler(resumed, WORKERS)
        assert drain(scheduler) == []
        assert scheduler.resume_scan[37] == ("CloseFridge", 37, "skip_owner_pending")
        assert scheduler.resume_scan[38] == ("CloseFridge", 38, "skip_valid_core")
        assert (
            resumed.summary()[0]["sr"] is None and bytes_of_results(resumed) == original
        )
    with Store(value.root, value.manifest).locked() as resumed:
        resumed.authorize_retry(
            "CloseFridge", 37, owner_ref="explicit Owner test decision"
        )
        scheduler = RoundScheduler(resumed, WORKERS)
        assert drain(scheduler) == [("CloseFridge", 37)]
        assert all(bytes_of_results(resumed)[k] == v for k, v in original.items())
        assert resumed.summary()[0]["valid"] == 50


def test_duplicate_gpu_claim_or_direct_store_bypass_is_refused_and_inflight_not_DONE(
    tmp_path,
):
    value = fresh(tmp_path, tasks=("TaskA", "TaskB", "TaskC"), episodes=2)
    with value.locked():
        scheduler = RoundScheduler(value, WORKERS)
        c = scheduler.dispatch("GPU4")
        with pytest.raises(ValueError, match="already has"):
            scheduler.dispatch("GPU4")
        with pytest.raises(ValueError, match="ticket"):
            value.begin_episode("TaskA", 0)
        with pytest.raises(ValueError, match="not finished"):
            scheduler.finish(c)
        commit_claim(scheduler, c, finish=False)
        row = value.rows("TaskA")[0]
        with pytest.raises(ValueError, match="ticket"):
            value.commit(row, staging=None)
        with pytest.raises(ValueError, match="cross-slot"):
            scheduler.commit(c, dict(row, task="TaskB"), staging=None)
        scheduler.finish(c)
        with pytest.raises(ValueError, match="stale"):
            scheduler.commit(c, row, staging=None)
        c2 = scheduler.dispatch("GPU5")
        c3 = scheduler.dispatch("GPU6")
        assert c2["episode"] == c3["episode"] == 0
        assert scheduler.dispatch("GPU4") is None
        scheduler.cancel("infrastructure unsafe stop")
        with pytest.raises(ValueError, match="cancelled"):
            scheduler.dispatch("GPU4")
        assert value.summary()[0]["valid"] == 1


def test_resume_refuses_unclean_old_workers_and_valid_core_corruption(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        scheduler = RoundScheduler(value, WORKERS)
        c = scheduler.dispatch("GPU4")
        commit_claim(scheduler, c)
    with Store(value.root, value.manifest).locked() as resumed:
        with pytest.raises(ValueError, match="cleanup required"):
            RoundScheduler(resumed, WORKERS)
        close_streams(resumed, "CloseFridge")
        (resumed._slot("CloseFridge", 0) / "result.json").write_bytes(b"corrupt")
        scheduler = RoundScheduler(resumed, WORKERS)
        with pytest.raises(ValueError):
            scheduler.dispatch("GPU4")
        assert not scheduler.done


def test_live_four_strike_skip_is_round_disposition_not_success_and_next_round_waits(
    tmp_path,
):
    value = fresh(tmp_path, tasks=("TaskA", "TaskB", "TaskC"), episodes=2)
    with value.locked():
        scheduler = RoundScheduler(value, WORKERS)
        c0 = scheduler.dispatch("GPU4")
        c1 = scheduler.dispatch("GPU5")
        c2 = scheduler.dispatch("GPU6")
        state, _ = admit_scene(
            value, c0["attempt"], FakeInit([OSError("reset")] * 4), safe_recover
        )
        assert state["status"] == "skipped_init_error"
        scheduler.finish(c0)
        assert scheduler.dispatch("GPU4") is None
        commit_claim(scheduler, c2, success=False)
        assert scheduler.dispatch("GPU4") is None
        commit_claim(scheduler, c1)
        next_claim = scheduler.dispatch("GPU4")
        assert next_claim["episode"] == 1
        commit_claim(scheduler, next_claim)
        assert drain(scheduler) == [("TaskB", 1), ("TaskC", 1)]
        report = value.summary()[0]
        assert (
            report["valid"] == 5
            and report["skipped_init_error"] == 1
            and report["sr"] is None
        )
        assert report["failure"] == 1 and report["success"] == 4
