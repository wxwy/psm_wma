"""Terminal observation remains bounded, identity-scoped and outside acceptance."""

import json
import sys
import threading
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from robocasa_eval_progress import EvaluationProgress  # noqa: E402

DIGEST = "a" * 64


class Clock:
    value = 0.0

    def __call__(self):
        return self.value


def append(path, records):
    with path.open("a") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def live(*, event="stage", episode=0, task="CloseFridge", attempt="CloseFridge/attempt_0001", **fields):
    return dict(
        schema="psm_eval_live_progress_v1",
        evaluation_run_digest=DIGEST,
        evaluation_attempt_id=attempt,
        task=task,
        episodes=5,
        event=event,
        episode=episode,
        stage="executing",
        **fields,
    )


def setup(tmp_path, *, clock=None):
    messages = []
    reporter = EvaluationProgress(sink=messages.append, clock=clock or Clock())
    reporter.update(
        0,
        gpu="2",
        task="CloseFridge",
        attempt_dir=tmp_path,
        attempt_id="CloseFridge/attempt_0001",
        run_digest=DIGEST,
        episodes=5,
        stage="executing",
    )
    reporter._cycle()
    messages.clear()
    return reporter, messages


def audit(*, episode=0, attempt="CloseFridge/attempt_0001", **fields):
    return dict(evaluation_run_digest=DIGEST, evaluation_attempt_id=attempt, episode=episode, **fields)


def test_cadence_uses_monotonic_clock_without_timing_performance_assertion(tmp_path):
    clock = Clock()
    reporter, messages = setup(tmp_path, clock=clock)
    clock.value = 4.99
    reporter._cycle()
    assert messages == []
    clock.value = 5
    reporter._cycle()
    assert len(messages) == 1 and "event=heartbeat" in messages[0]
    assert "episode=?/5" in messages[0] and "steps=?/?" in messages[0]
    reporter._cycle()
    assert len(messages) == 1
    clock.value = 10
    reporter._cycle()
    assert len(messages) == 2


def test_episode_events_immediate_before_heartbeat_and_actual_latency_field(tmp_path):
    reporter, messages = setup(tmp_path)
    append(tmp_path / "live_progress.jsonl", [live(event="episode_start", steps=0, predictions=0, max_steps=900)])
    append(tmp_path / "rollout00_actions.jsonl", [audit(source_step=0), audit(source_step=1)])
    append(tmp_path / "rollout00_predictions.jsonl", [audit(latency_ms=1234.56, step_before_query=0)])
    reporter._cycle()
    assert len(messages) == 1
    assert "event=episode_start" in messages[0]
    assert "episode=1/5" in messages[0] and "steps=2/900" in messages[0]
    assert "predictions=1" in messages[0] and "latest_prediction_ms=1234.6" in messages[0]
    append(
        tmp_path / "live_progress.jsonl",
        [live(event="episode_end", steps=2, predictions=1, outcome="behavioral_failure")],
    )
    reporter._cycle()
    assert "event=episode_end" in messages[-1]
    assert "episode_outcome=behavioral_failure" in messages[-1]


def test_read_complete_newline_incrementally_without_counting_twice(tmp_path):
    reporter, messages = setup(tmp_path)
    path = tmp_path / "rollout00_actions.jsonl"
    first = json.dumps(audit(source_step=0))
    path.write_text(first[:20])
    reporter._cycle()
    assert reporter._observations[0].values["episode"] is None
    with path.open("a") as handle:
        handle.write(first[20:] + "\n")
    reporter._cycle()
    values = reporter._observations[0].values
    assert values["episode"] == 0 and values["steps"] == 1
    reporter._cycle()
    assert values["steps"] == 1
    append(path, [audit(source_step=1)])
    reporter._cycle()
    assert values["steps"] == 2


def test_prediction_latency_uses_the_newest_prediction_frontier(tmp_path):
    clock = Clock()
    reporter, messages = setup(tmp_path, clock=clock)
    append(tmp_path / "live_progress.jsonl", [live(predictions=2, last_prediction_ms=250)])
    path = tmp_path / "rollout00_predictions.jsonl"
    append(path, [audit(latency_ms=10, step_before_query=0)])
    reporter._cycle()
    values = reporter._observations[0].values
    # Legal child ordering: live prediction 2 exists before audit prediction 2.
    assert values["predictions"] == 2 and values["last_prediction_ms"] == 250
    clock.value = 5
    reporter._cycle()
    assert "predictions=2 latest_prediction_ms=250.0" in messages[-1]
    append(path, [audit(latency_ms=250, step_before_query=16)])
    reporter._cycle()
    assert values["predictions"] == 2 and values["last_prediction_ms"] == 250
    # A complete newer audit record may lead the latest live observation.
    append(path, [audit(latency_ms=360, step_before_query=32)])
    reporter._cycle()
    assert values["predictions"] == 3 and values["last_prediction_ms"] == 360
    clock.value = 10
    reporter._cycle()
    assert "predictions=3 latest_prediction_ms=360.0" in messages[-1]


@pytest.mark.parametrize(
    "field,value",
    [
        ("evaluation_run_digest", "b" * 64),
        ("evaluation_attempt_id", "CloseFridge/attempt_9999"),
        ("task", "NavigateKitchen"),
        ("schema", "foreign_v1"),
        ("episodes", 4),
        ("episode", True),
    ],
)
def test_wrong_live_identity_or_typed_episode_is_ignored(tmp_path, field, value):
    reporter, messages = setup(tmp_path)
    record = live(event="episode_start", steps=999)
    record[field] = value
    append(tmp_path / "live_progress.jsonl", [record])
    reporter._cycle()
    assert messages == []
    assert reporter._observations[0].values["episode"] is None


def test_malformed_nonfinite_oversized_and_truncated_records_fail_open(tmp_path):
    reporter, messages = setup(tmp_path)
    path = tmp_path / "live_progress.jsonl"
    path.write_bytes(
        b'not JSON\n{"x": NaN}\n' + b"x" * 70000 + b"\n" + json.dumps(live(event="episode_start")).encode()
    )
    reporter._cycle()
    assert messages == []
    with path.open("ab") as handle:
        handle.write(b"\n")
    reporter._cycle()
    assert len(messages) == 1 and "episode_start" in messages[0]


def test_wrong_audit_identity_and_latency_are_not_shown(tmp_path):
    reporter, messages = setup(tmp_path)
    append(tmp_path / "rollout00_actions.jsonl", [audit(attempt="Other/attempt_0001", source_step=0)])
    append(tmp_path / "rollout00_predictions.jsonl", [audit(latency_ms=float("nan")), audit(latency_ms=True)])
    reporter._cycle()
    assert reporter._observations[0].values["episode"] is None
    assert reporter._observations[0].values["last_prediction_ms"] is None


def test_audit_fallback_advances_episode_and_resets_old_counts(tmp_path):
    reporter, messages = setup(tmp_path)
    append(tmp_path / "rollout00_actions.jsonl", [audit(source_step=0), audit(source_step=1)])
    reporter._cycle()
    assert reporter._observations[0].values["steps"] == 2
    append(tmp_path / "rollout01_actions.jsonl", [audit(episode=1, source_step=0)])
    reporter._cycle()
    assert reporter._observations[0].values["episode"] == 1
    assert reporter._observations[0].values["steps"] == 1


def test_task_switch_drains_old_episode_before_final_and_never_mixes_new_binding(tmp_path):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    reporter, messages = setup(first)
    append(first / "live_progress.jsonl", [live(event="episode_end", episode=4, steps=45)])
    reporter.update(0, stage="complete", event="task_complete")
    reporter.update(
        0,
        task="NavigateKitchen",
        attempt_dir=second,
        attempt_id="NavigateKitchen/attempt_0001",
        stage="model_loading",
    )
    reporter._cycle()
    assert "event=episode_end" in messages[0] and "task=CloseFridge" in messages[0]
    assert "event=task_complete" in messages[1] and "steps=45/?" in messages[1]
    assert "task=NavigateKitchen" in messages[2] and "episode=?/5" in messages[2]
    assert reporter._observations[0].values["steps"] is None


def test_task_only_update_clears_previous_attempt_binding(tmp_path):
    reporter, messages = setup(tmp_path)
    append(tmp_path / "rollout00_actions.jsonl", [audit(source_step=0)])
    reporter.update(0, task="NavigateKitchen", stage="model_loading")
    reporter._cycle()
    assert reporter._states[0]["attempt_dir"] is None
    assert reporter._observations[0].values["steps"] is None


def test_late_child_stage_cannot_replace_root_final_validation(tmp_path):
    reporter, messages = setup(tmp_path)
    append(tmp_path / "live_progress.jsonl", [dict(live(event="episode_end"), stage="environment_close")])
    reporter.update(0, stage="result_validation")
    reporter._cycle()
    assert "stage=result_validation" in messages[-1]
    reporter.update(0, stage="failed", error="encoder\nfailed\x1b", event="error")
    reporter._cycle()
    assert "stage=failed" in messages[-1]
    assert "encoder failed " in messages[-1] and messages[-1].count("\n") == 1


@pytest.mark.parametrize("failure", [BrokenPipeError, OSError, ValueError])
def test_sink_failure_disables_only_observer(tmp_path, failure):
    calls = []

    def broken(line):
        calls.append(line)
        raise failure("injected UI sink failure")

    reporter = EvaluationProgress(sink=broken)
    reporter.update(0, stage="model_loading")
    reporter._cycle()
    assert not reporter.enabled and len(calls) == 1
    reporter.update(0, event="error", error="business failure")
    reporter.close()


def test_disabled_never_reads_or_starts_thread(monkeypatch, tmp_path):
    def forbidden(*args, **kwargs):
        raise AssertionError("disabled observation touched a resource")

    monkeypatch.setattr(Path, "open", forbidden)
    monkeypatch.setattr(threading.Thread, "start", forbidden)
    reporter = EvaluationProgress(enabled=False)
    reporter.update(0, attempt_dir=tmp_path, stage="model_loading", event="error")
    reporter.start()
    reporter._cycle()
    reporter.close()
    assert reporter._thread is None


def test_reader_failure_is_ignored_without_touching_business_state(tmp_path, monkeypatch):
    reporter, messages = setup(tmp_path)
    original = Path.open

    def denied(path, *args, **kwargs):
        if path.name == "live_progress.jsonl":
            raise PermissionError("observational log unavailable")
        return original(path, *args, **kwargs)

    (tmp_path / "live_progress.jsonl").touch()
    monkeypatch.setattr(Path, "open", denied)
    reporter._cycle()
    reporter.update(0, stage="failed", error="real error", event="error")
    reporter._cycle()
    assert reporter.enabled and "real error" in messages[-1]


def test_default_sink_flushes_every_line(tmp_path, monkeypatch):
    class Stdout:
        def __init__(self):
            self.lines, self.flushes = [], 0

        def write(self, value):
            self.lines.append(value)

        def flush(self):
            self.flushes += 1

    stdout = Stdout()
    monkeypatch.setattr(sys, "stdout", stdout)
    reporter = EvaluationProgress()
    reporter.update(0, stage="model_loading")
    reporter._cycle()
    assert stdout.flushes == 1 and len(stdout.lines) == 1


def test_single_daemon_serializes_multiple_workers_and_close_drains_updates(tmp_path):
    calls = []
    reporter = EvaluationProgress(sink=lambda line: calls.append((threading.current_thread().name, line)))
    reporter.start()
    for worker in range(4):
        reporter.update(worker, gpu=str(worker), task=f"Task{worker}", stage="model_loading")
        reporter.update(worker, stage="complete", event="task_complete")
    reporter.close()
    assert not reporter._thread.is_alive()
    assert reporter._thread.daemon
    assert len(calls) == 8
    assert {name for name, _ in calls} == {"robocasa-eval-progress"}
    for worker in range(4):
        assert any(f"worker={worker}" in line and "event=task_complete" in line for _, line in calls)


def test_producer_update_never_calls_blocked_sink_or_reads_files(tmp_path):
    entered, release = threading.Event(), threading.Event()

    def sink(line):
        entered.set()
        release.wait(3)

    reporter = EvaluationProgress(sink=sink).start()
    try:
        reporter.update(0, stage="model_loading")
        assert entered.wait(2)
        # The UI is blocked in its sink; worker updates still only append memory.
        done = threading.Event()
        producer = threading.Thread(target=lambda: (reporter.update(0, event="task_complete"), done.set()))
        producer.start()
        assert done.wait(1)
        producer.join()
    finally:
        release.set()
        reporter.close()
    assert not reporter._thread.is_alive()


def test_thread_start_failure_is_observational_only_and_close_is_idempotent(monkeypatch):
    def failure(thread):
        raise RuntimeError("cannot start optional UI thread")

    monkeypatch.setattr(threading.Thread, "start", failure)
    reporter = EvaluationProgress(sink=lambda line: None)
    reporter.start()
    assert not reporter.enabled
    reporter.update(0, stage="model_loading")
    reporter.close()
    reporter.close()


def test_progress_reads_never_create_or_modify_business_artifacts(tmp_path):
    reporter, messages = setup(tmp_path)
    append(tmp_path / "live_progress.jsonl", [live(event="episode_end", steps=1)])
    append(tmp_path / "rollout00_actions.jsonl", [audit(source_step=0)])
    before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.iterdir()}
    reporter._cycle()
    reporter.close()
    after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in tmp_path.iterdir()}
    assert before == after


@pytest.mark.parametrize("interval", [0, -1, float("inf"), float("nan"), "invalid"])
def test_invalid_optional_interval_disables_observer(interval):
    reporter = EvaluationProgress(interval_s=interval)
    reporter.start()
    reporter.update(0, event="task_complete")
    reporter.close()
    assert not reporter.enabled and reporter._thread is None
