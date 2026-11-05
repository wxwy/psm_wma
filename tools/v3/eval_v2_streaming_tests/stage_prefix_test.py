"""CPU-only regression: stage 2/5, then resume same frozen 5EP scientific Run."""

import uuid

import pytest
from cosmos_framework.evaluation.robocasa_v2.scheduler import StreamingScheduler
from cosmos_framework.evaluation.robocasa_v2.store import Store
from robocasa_eval_v2.runtime import limit_streaming_scheduler_to_prefix
from tools.v3.eval_v2_production_tests.store_test import close_streams
from tools.v3.eval_v2_streaming_tests.scheduler_test import complete, fresh


def test_stage_two_then_resume_five_with_identical_manifest_and_core(tmp_path):
    tasks = ("CloseFridge", "OpenDrawer", "TurnOffStove")
    store = fresh(tmp_path, tasks, episodes=5)
    expected_manifest = store.manifest["digest"]
    with store.locked():
        s = StreamingScheduler(store, {"w": uuid.uuid4().hex})
        limit_streaming_scheduler_to_prefix(s, 2)
        observed = []
        while not s.done:
            claim = s.dispatch("w")
            if claim is None:
                continue
            observed.append((claim["task"], claim["episode"]))
            complete(s, claim)
        assert len(observed) == 6
        assert sorted(observed) == sorted((t, ep) for t in tasks for ep in (0, 1))
        for task in tasks:
            close_streams(store, task)
        partial = store.publish_views()
        assert (partial["valid"], partial["pending"], partial["expected"]) == (6, 9, 15)
        assert partial["manifest_digest"] == expected_manifest
    from pathlib import Path
    old_core = (store.root / "tasks" / "CloseFridge" / "episodes" / "ep_000" / "result.json").read_bytes()
    resumed = Store(store.root, store.manifest)
    with resumed.locked():
        s = StreamingScheduler(resumed, {"new": uuid.uuid4().hex})
        limit_streaming_scheduler_to_prefix(s, None)
        additions = []
        while not s.done:
            claim = s.dispatch("new")
            if claim is None:
                continue
            additions.append((claim["task"], claim["episode"]))
            complete(s, claim)
        assert len(additions) == 9
        assert sorted(additions) == sorted((t, ep) for t in tasks for ep in (2, 3, 4))
        for task in tasks:
            close_streams(resumed, task)
        final = resumed.publish_views()
        assert (final["valid"], final["pending"], final["expected"]) == (15, 0, 15)
        assert final["manifest_digest"] == expected_manifest
    assert (store.root / "tasks" / "CloseFridge" / "episodes" / "ep_000" / "result.json").read_bytes() == old_core


def test_invalid_stage_limits_fail_closed(tmp_path):
    store = fresh(tmp_path, ("CloseFridge",), episodes=3)
    with store.locked():
        s = StreamingScheduler(store, {"one": uuid.uuid4().hex})
        for invalid in (-1, 0, 3, 4, True, 1.2, "2"):
            with pytest.raises(ValueError):
                limit_streaming_scheduler_to_prefix(s, invalid)
        limit_streaming_scheduler_to_prefix(s, 2)
        assert [*s.pending["CloseFridge"]] == [0, 1]
        s.cancel("bounded fixture teardown")
        close_streams(store, "CloseFridge")
