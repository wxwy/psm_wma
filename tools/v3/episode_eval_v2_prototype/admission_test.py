"""D4 scene admission CPU negative/positive tests; no real simulator."""

import pytest

from tools.v3.episode_eval_v2_prototype.admission import admit_scene
from tools.v3.episode_eval_v2_prototype.store import Store
from tools.v3.episode_eval_v2_prototype.store_test import (
    Crash,
    admitted,
    bytes_of_results,
    close_streams,
    complete,
    fresh,
    inject,
    valid,
)


class FakeInit:
    def __init__(self, sequence):
        self.sequence = iter(sequence)
        self.reset_calls = self.predicate_calls = self.model_calls = self.action_calls = self.local_begins = 0
        self.item = False

    def reset(self):
        self.reset_calls += 1
        self.item = next(self.sequence)
        if isinstance(self.item, Exception) and not isinstance(self.item, PredicateError):
            raise self.item

    def _check_success(self):
        self.predicate_calls += 1
        if isinstance(self.item, PredicateError):
            raise self.item
        return self.item


class PredicateError(RuntimeError):
    pass


def safe_recover(error, stage, env):
    assert isinstance(error, Exception) and stage in ("reset", "initial_success")
    return env  # CPU fake only: no EGL/Local/process resources exist.


def attempt(value, ep=0):
    return value.begin_episode("CloseFridge", ep)


def test_three_errors_then_admitted_legal_scene_and_no_model_action_Local_during_admission(tmp_path):
    value = fresh(tmp_path)
    env = FakeInit([OSError("reset1"), PredicateError("precheck2"), None, False])
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        state, _ = admit_scene(value, a, env, safe_recover)
        assert state["status"] == "admitted" and state["consecutive_errors"] == 0
        assert state["count"] == env.reset_calls == 4
        assert (env.model_calls, env.action_calls, env.local_begins) == (0, 0, 0)
        events = value.events(a)
        errs = [x for x in events if x["kind"] == "INIT_ERROR"]
        assert [x["data"]["stage"] for x in errs] == ["reset", "initial_success", "initial_success"]
        assert [x["data"]["type"] for x in errs] == ["OSError", "PredicateError", "ValueError"]
        assert all(x["attempt"]["episode"] == 0 and x["time_ns"] > 0 for x in errs)
        valid(value, a, success=False)
        with pytest.raises(ValueError, match="immutable"):
            attempt(value)


def test_legal_degenerate_precheck_breaks_error_streak_without_counting_success(tmp_path):
    value = fresh(tmp_path)
    env = FakeInit([OSError("x")] * 3 + [True] + [OSError("x")] * 3 + [False])
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        state, _ = admit_scene(value, a, env, safe_recover)
        assert state["status"] == "admitted" and state["count"] == 8
        report = value.summary()[0]
        assert report["success"] == 0 and report["tasks"]["CloseFridge"]["admission_rejections"] == 1
        assert report["tasks"]["CloseFridge"]["initialization_errors"] == 6
        valid(value, a)
        assert value.summary()[0]["success"] == 1


def test_fourth_error_skips37_and_allows38_to49_then_owner_only_gap_retry(tmp_path):
    value = fresh(tmp_path, episodes=50)
    with value.locked():
        value.begin_task("CloseFridge")
        for ep in range(37):
            complete(value, "CloseFridge", ep, success=ep % 2 == 0)
        a = attempt(value, 37)
        env = FakeInit([OSError(f"init_error_{i}") for i in range(4)])
        state, _ = admit_scene(value, a, env, safe_recover)
        assert state["status"] == "skipped_init_error" and state["consecutive_errors"] == 4
        for ep in range(38, 50):
            complete(value, "CloseFridge", ep, success=False)
        original = bytes_of_results(value)
        report = value.publish_views()
        assert report["valid"] == 49 and report["skipped_init_error"] == 1 and report["sr"] is None
        ids = report["tasks"]["CloseFridge"]["missing_blocked_ids"]
        assert [(x["task"], x["episode"]) for x in ids] == [("CloseFridge", 37)]
        assert len(ids[0]["error_diagnostics"]) == 4
        assert {e["message"] for e in ids[0]["error_diagnostics"]} == {f"init_error_{i}" for i in range(4)}
        close_streams(value, "CloseFridge")
    with Store(value.root, value.manifest).locked() as resumed:
        resumed.begin_task("CloseFridge")
        with pytest.raises(ValueError, match="Owner authorization"):
            attempt(resumed, 37)
        assert bytes_of_results(resumed) == original
        with pytest.raises(ValueError):
            resumed.authorize_retry("CloseFridge", 37, owner_ref="")
        permit = resumed.authorize_retry("CloseFridge", 37, owner_ref="Owner explicit synthetic request #37")
        a = admitted(resumed, attempt(resumed, 37))
        assert a["authorization"] == permit
        valid(resumed, a, success=False)
        after = bytes_of_results(resumed)
        assert all(after[k] == v for k, v in original.items())
        assert resumed.publish_views()["valid"] == 50
        with pytest.raises(ValueError, match="immutable"):
            attempt(resumed, 37)


def test_degenerate_resampling_limit_is_bounded_not_success_or_initial_error(tmp_path):
    value = fresh(tmp_path)
    env = FakeInit([True] * 100)
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        state, _ = admit_scene(value, a, env, safe_recover)
        assert state["status"] == "scene_admission_exhausted"
        assert env.reset_calls == 32 and state["consecutive_errors"] == 0
        report = value.publish_views()
        assert report["sr"] is None and report["success"] == report["failure"] == 0
        assert report["tasks"]["CloseFridge"]["admission_rejections"] == 32
        assert report["tasks"]["CloseFridge"]["initialization_errors"] == 0
        with pytest.raises(ValueError, match="terminal/blocked"):
            value.begin_initialization(a)
        complete(value, "CloseFridge", 1)


@pytest.mark.parametrize("boundary", ["after_event_INIT_BEGIN", "after_event_INIT_ERROR"])
def test_admission_crash_replays_persisted_counter_no_fake_errors_or_budget_reset(tmp_path, boundary):
    value = fresh(tmp_path)
    with pytest.raises(Crash), value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        for _ in range(3):
            value.begin_initialization(a)
            value.initialization_outcome(a, error=OSError("before crash"), stage="reset", safe_to_retry=True)
        value.fault = inject(boundary)
        value.begin_initialization(a)
        value.initialization_outcome(a, error=OSError("fourth persisted"), stage="reset", safe_to_retry=True)
    with Store(value.root, value.manifest).locked() as resumed:
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge")
        if boundary == "after_event_INIT_ERROR":
            assert resumed.slot("CloseFridge", 0)["status"] == "skipped_init_error"
            with pytest.raises(ValueError, match="Owner authorization"):
                attempt(resumed)
        else:
            newer = attempt(resumed)
            env = FakeInit([OSError("fourth real error")])
            state, _ = admit_scene(resumed, newer, env, safe_recover)
            assert state["status"] == "skipped_init_error" and state["consecutive_errors"] == 4
            events = [e for x in resumed._attempts("CloseFridge", 0) for e in resumed.events(x)]
            assert sum(e["kind"] == "INIT_ERROR" for e in events) == 4
            assert sum(e["kind"] == "INIT_BEGIN" for e in events) == 5
            assert any(e["kind"] == "INTERRUPTED" for e in events)


def test_crash_after_admitted_scene_cannot_inherit_old_observation_or_make_Core_commit(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        old = admitted(value, attempt(value))
    with Store(value.root, value.manifest).locked() as resumed:
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge", seed=42)
        new = attempt(resumed)
        assert new["attempt_id"] != old["attempt_id"]
        admitted(resumed, new)
        assert resumed.events(new)[-1]["data"]["reset_index"] == 0
        valid(resumed, new)
        assert resumed.rows("CloseFridge")[0]["seed"] == 42


@pytest.mark.parametrize("recover", [lambda *x: None, lambda *x: (_ for _ in ()).throw(RuntimeError("cleanup failed"))])
def test_unsafe_resources_are_process_error_safe_stop_not_four_strike_skip(tmp_path, recover):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        state, _ = admit_scene(value, a, FakeInit([RuntimeError("EGL destroyed")]), recover)
        assert state["status"] == "invalid" and state["count"] == 1
        report = value.publish_views()
        assert report["invalid"] == 1 and report["skipped_init_error"] == 0
        assert report["unresolved_process_errors"] == 1 and report["sr"] is None
        with pytest.raises(ValueError, match="current process fault"):
            value.begin_episode("CloseFridge", 1)


def test_keyboard_interrupt_is_not_recoverable_init_error_and_keeps_inflight_evidence(tmp_path):
    class Interrupted(FakeInit):
        def reset(self):
            raise KeyboardInterrupt("stop")

    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        with pytest.raises(KeyboardInterrupt):
            admit_scene(value, a, Interrupted([]), safe_recover)
        assert [e["kind"] for e in value.events(a)] == ["INIT_BEGIN"]
        assert value.summary()[0]["interrupted"] == 1


def test_crash_after_three_errors_and_legal_true_resets_consecutive_counter(tmp_path):
    value = fresh(tmp_path)
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        for _ in range(3):
            value.begin_initialization(a)
            value.initialization_outcome(a, error=ValueError("reset"), stage="reset", safe_to_retry=True)
        value.begin_initialization(a)
        assert value.initialization_outcome(a, initial_success=True)["consecutive_errors"] == 0
    with Store(value.root, value.manifest).locked() as resumed:
        close_streams(resumed, "CloseFridge")
        resumed.begin_task("CloseFridge")
        a = attempt(resumed)
        state, _ = admit_scene(resumed, a, FakeInit([OSError("x")] * 3 + [False]), safe_recover)
        assert state["status"] == "admitted" and state["consecutive_errors"] == 0


def test_safe_environment_rebuild_has_explicit_boundary_and_retains_init_error(tmp_path):
    value = fresh(tmp_path)
    new_env = FakeInit([False])
    with value.locked():
        value.begin_task("CloseFridge")
        a = attempt(value)
        state, env = admit_scene(value, a, FakeInit([OSError("recoverable construction")]), lambda *x: new_env)
        assert env is new_env and state["status"] == "admitted"
        events = value.events(a)
        assert [e["kind"] for e in events] == ["INIT_BEGIN", "INIT_ERROR", "ENV_REBUILT", "INIT_BEGIN", "ADMITTED"]
        assert events[-1]["data"]["reset_index"] == 1  # stream reset ordinal, new env lifetime recorded separately.
        valid(value, a)


def test_50_four_error_skips_publish_all_diagnostics_without_Core_size_limit_collision(tmp_path):
    value = fresh(tmp_path, episodes=50)
    with value.locked():
        value.begin_task("CloseFridge")
        for ep in range(50):
            a = value.begin_episode("CloseFridge", ep)
            state, _ = admit_scene(value, a, FakeInit([OSError("x" * 2048)] * 4), safe_recover)
            assert state["status"] == "skipped_init_error"
        close_streams(value, "CloseFridge")
        report = value.publish_views()
        assert report["status"] == "partial" and report["sr"] is None and report["valid"] == 0
        assert report["skipped_init_error"] == 50
        assert len(report["tasks"]["CloseFridge"]["missing_blocked_ids"]) == 50
        assert all(len(x["error_diagnostics"]) == 4 for x in report["tasks"]["CloseFridge"]["missing_blocked_ids"])
        assert (value.root / "summary.json").stat().st_size > 256 * 1024
