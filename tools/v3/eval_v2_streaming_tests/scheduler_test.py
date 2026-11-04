"""Real leased Store and deterministic streaming concurrency, no model/physics."""

import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest
from cosmos_framework.evaluation.robocasa_v2.contract import (
    EnvironmentOutcome,
    result_record,
)
from cosmos_framework.evaluation.robocasa_v2.scheduler import StreamingScheduler
from cosmos_framework.evaluation.robocasa_v2.store import Store, records
from robocasa_eval_v2.identity import ATOMIC_TASKS
from tools.v3.eval_v2_production_tests.store_test import close_streams, fixture_core
from tools.v3.eval_v2_production_tests.store_test import cleaned
from tools.v3.eval_v2_streaming_tests.capacity_test import streaming_manifest


def fresh(path, tasks=("CloseFridge",), episodes=4):
    value = Store(path / "run", streaming_manifest(tasks, episodes))
    value.create()
    return value


def complete(scheduler, claim):
    value, a = scheduler.store, claim["attempt"]
    init = value.begin_initialization(a)
    assert (
        value.initialization_outcome(a, initial_success=False)["status"] == "admitted"
    )
    grant = value.allocate_environment(a["task"], a["physical_slot_id"])
    sampling = dict(
        environment_id=grant["environment_id"],
        actual_seed=grant["seed"],
        environment_reset_index=0,
        physical_slot_id=a["physical_slot_id"],
        protocol=value.manifest["protocol"]["sampling"],
    )
    value.bind_sampling(a, sampling)
    observed = EnvironmentOutcome(value.manifest["horizons"][a["task"]], [True]).finish(
        normal=True
    )
    row = result_record(
        value.manifest,
        **{
            k: a[k]
            for k in (
                "task",
                "episode",
                "generation",
                "stream_id",
                "attempt_id",
                "worker_id",
                "seed",
            )
        },
        reset_index=init["reset_index"],
        observation=observed,
        instruction="CPU scene",
        replans=1,
        elapsed_seconds=0.01,
        sampling=sampling,
    )
    staging = fixture_core(value, a, row)
    scene = staging / "scene_provenance.json"
    scene.write_text(
        json.dumps(dict(json.loads(scene.read_bytes()), sampling=sampling))
    )
    scheduler.commit(claim, row, staging=staging)
    scheduler.finish(claim)
    return row


def test_64_slots_more_than_18_tasks_no_round_barrier_and_no_duplicate_claims(tmp_path):
    value = fresh(tmp_path, ATOMIC_TASKS, 50)
    slots = {f"slot{i}": uuid.uuid4().hex for i in range(64)}
    with value.locked():
        scheduler = StreamingScheduler(value, slots)
        claims = [scheduler.dispatch(w) for w in slots]
        keys = {(c["task"], c["episode"]) for c in claims}
        assert len(keys) == len(scheduler.inflight) == 64
        assert {c["task"] for c in claims} == set(ATOMIC_TASKS)
        assert len({c["attempt"]["physical_slot_id"] for c in claims}) == 64
        assert max(c["episode"] for c in claims) >= 3
        with pytest.raises(ValueError, match="busy"):
            scheduler.dispatch("slot0")
        slow = claims[0]
        fast = claims[18]  # Same Task, later Episode, while Episode0 is still owned.
        assert fast["task"] == slow["task"] and fast["episode"] > slow["episode"]
        complete(scheduler, fast)
        next_claim = scheduler.dispatch(fast["physical_worker"])
        assert next_claim and scheduler.inflight[slow["physical_worker"]] == slow
        assert (next_claim["task"], next_claim["episode"]) not in keys
        assert not any(
            x["kind"] == "ROUND_BARRIER"
            for x in records(value.root / "_internal/scheduler" / scheduler.invocation)
        )
        scheduler.cancel("CPU controlled stop; unfinished work remains pending")
        for task in ATOMIC_TASKS:
            close_streams(value, task)


def test_task_affinity_is_bounded_and_all_tasks_make_progress(tmp_path):
    value = fresh(tmp_path, ATOMIC_TASKS[:3], 12)
    with value.locked():
        scheduler = StreamingScheduler(value, {"worker": uuid.uuid4().hex})
        order = []
        while not scheduler.done:
            claim = scheduler.dispatch("worker")
            if claim:
                order.append(claim["task"])
                complete(scheduler, claim)
        assert set(order[:9]) == set(ATOMIC_TASKS[:3])
        assert all(order.count(t) == 12 for t in ATOMIC_TASKS[:3])
        assert all(len(set(order[i : i + 5])) > 1 for i in range(len(order) - 5))
        for task in ATOMIC_TASKS[:3]:
            close_streams(value, task)
        assert value.publish_views()["valid"] == 36


def test_concurrent_environment_seed_allocation_and_cross_slot_binding_fail_closed(
    tmp_path,
):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        slots = [uuid.uuid4().hex for _ in range(32)]
        with ThreadPoolExecutor(32) as pool:
            grants = list(
                pool.map(
                    lambda slot: value.allocate_environment("CloseFridge", slot), slots
                )
            )
        assert sorted(g["ordinal"] for g in grants) == list(range(32))
        assert len({g["seed"] for g in grants}) == 32
        scheduler = StreamingScheduler(value, {"a": slots[0], "b": slots[1]})
        a, b = scheduler.dispatch("a"), scheduler.dispatch("b")
        value.begin_initialization(a["attempt"])
        value.initialization_outcome(a["attempt"], initial_success=False)
        sampling = dict(
            environment_id=grants[1]["environment_id"],
            actual_seed=grants[1]["seed"],
            physical_slot_id=slots[1],
            environment_reset_index=0,
            protocol=value.manifest["protocol"]["sampling"],
        )
        with pytest.raises(ValueError, match="sampling contradicts"):
            value.bind_sampling(a["attempt"], sampling)
        with pytest.raises(ValueError, match="misrouted"):
            scheduler.finish(dict(b, physical_worker="a"))
        scheduler.cancel("controlled test stop")
        close_streams(value, "CloseFridge")


def test_resume_keeps_core_and_owner_pending_until_explicit_authorization(tmp_path):
    value = fresh(tmp_path, episodes=3)
    with value.locked():
        scheduler = StreamingScheduler(
            value, {"a": uuid.uuid4().hex, "b": uuid.uuid4().hex}
        )
        first, skipped = scheduler.dispatch("a"), scheduler.dispatch("b")
        complete(scheduler, first)
        for _ in range(4):
            value.begin_initialization(skipped["attempt"])
            value.initialization_outcome(
                skipped["attempt"],
                error=ValueError("known sampling"),
                stage="reset",
                safe_to_retry=True,
            )
        scheduler.finish(skipped)
        original = (value._slot("CloseFridge", 0) / "result.json").read_bytes()
        scheduler.cancel("controlled Resume boundary")
        close_streams(value, "CloseFridge")
    resumed = Store(value.root, value.manifest)
    with resumed.locked():
        scheduler = StreamingScheduler(resumed, {"new": uuid.uuid4().hex})
        last = scheduler.dispatch("new")
        assert last["episode"] == 2
        complete(scheduler, last)
        assert scheduler.dispatch("new") is None and scheduler.done
        assert [x[2] for x in scheduler.resume_scan[:2]] == [
            "skip_valid_core",
            "skip_owner_pending",
        ]
        assert (
            resumed._slot("CloseFridge", 0) / "result.json"
        ).read_bytes() == original
        close_streams(resumed, "CloseFridge")


def test_task_fault_blocks_sibling_commit_without_poisoning_other_task(tmp_path):
    value = fresh(tmp_path, ATOMIC_TASKS[:2], 4)
    with value.locked():
        scheduler = StreamingScheduler(
            value, {f"s{i}": uuid.uuid4().hex for i in range(3)}
        )
        a, other, sibling = [scheduler.dispatch(w) for w in scheduler.workers]
        assert a["task"] == sibling["task"] != other["task"]
        value.record_process_error(
            a["task"], "server_exit", "CPU injected exit", attempt=a["attempt"]
        )
        with pytest.raises(ValueError, match="fault|unresolved|safe stop"):
            complete(scheduler, sibling)
        complete(scheduler, other)
        assert value.slot(other["task"], 0)["result"] is not None
        scheduler.cancel("expected task-scoped fault")
        for task in ATOMIC_TASKS[:2]:
            close_streams(value, task)


def test_cleanup_probe_does_not_hold_store_metadata_lock(tmp_path):
    value = fresh(tmp_path)
    entered, release = Event(), Event()
    with value.locked():
        stream = value.begin_task("CloseFridge")

        def probe(record):
            entered.set()
            assert release.wait(5)
            return cleaned(record)

        with ThreadPoolExecutor(2) as pool:
            cleanup = pool.submit(
                value.cleanup_stream, "CloseFridge", stream["stream_id"], probe
            )
            assert entered.wait(3)
            try:
                grant = pool.submit(
                    value.allocate_environment, "CloseFridge", uuid.uuid4().hex
                ).result(3)
                assert grant["task"] == "CloseFridge" and not cleanup.done()
            finally:
                release.set()
            assert cleanup.result(3)["stream"] == {
                k: v for k, v in stream.items() if k != "action"
            }
