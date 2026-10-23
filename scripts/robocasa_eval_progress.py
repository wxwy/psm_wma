"""Best-effort terminal observations; never an evaluation acceptance or Resume input."""

from __future__ import annotations

import json
import math
import re
import sys
import threading
import time
from collections import deque
from pathlib import Path

_UNSET = object()
_LIVE_STAGES = {
    "environment_initialization",
    "executing",
    "predicting",
    "video_saving",
    "local_cleanup",
    "result_writing",
    "environment_close",
}
_ROOT_STAGES = {"result_validation", "evidence_validation", "process_cleanup", "complete", "failed"}
_IMMEDIATE = {"episode_start", "episode_end", "error", "task_complete", "task_error"}
_AUDIT_NAME = re.compile(r"rollout(\d+)_(?:actions|predictions)\.jsonl\Z")


def _number(value, *, positive=False):
    return type(value) in {int, float} and math.isfinite(value) and value >= (1 if positive else 0)


def _integer(value, *, positive=False):
    return type(value) is int and value >= (1 if positive else 0)


def _text(value, limit=100):
    if value is None:
        return "?"
    return "".join(c if c.isprintable() else " " for c in str(value))[:limit]


def _reject_constant(value):
    raise ValueError(f"nonfinite observation: {value}")


class _Tail:
    """Read bounded complete JSONL records; never consume an incomplete tail."""

    def __init__(self, path):
        self.path, self.offset, self.signature = Path(path), 0, None
        self.discarding, self.reset = False, False

    def read(self):
        self.reset = False
        if self.path.is_symlink():
            return [], False
        stat = self.path.stat()
        signature = (stat.st_dev, stat.st_ino)
        if signature != self.signature or stat.st_size < self.offset:
            self.signature, self.offset, self.discarding, self.reset = signature, 0, False, True
        rows, consumed = [], 0
        with self.path.open("rb") as stream:
            stream.seek(self.offset)
            while consumed < 256 * 1024 and len(rows) < 512:
                start = stream.tell()
                line = stream.readline(65537)
                if not line:
                    return rows, False
                consumed += len(line)
                if self.discarding or len(line) > 65536:
                    self.discarding = not line.endswith(b"\n")
                    self.offset = stream.tell()
                    continue
                if not line.endswith(b"\n"):
                    self.offset = start
                    return rows, False
                self.offset = stream.tell()
                try:
                    row = json.loads(line, parse_constant=_reject_constant)
                    if isinstance(row, dict):
                        rows.append(row)
                except (ValueError, UnicodeError):
                    pass
        return rows, True


class _Observation:
    def __init__(self):
        self.live = None
        self.audit = {}
        self.values = dict.fromkeys(
            ("episode", "steps", "predictions", "last_prediction_ms", "max_steps", "stage", "outcome")
        )


class EvaluationProgress:
    """One optional daemon owns file reads and output; producers only enqueue state."""

    def __init__(self, enabled=True, interval_s=5.0, sink=None, clock=time.monotonic):
        self.enabled = bool(enabled)
        try:
            self.interval_s = float(interval_s)
            self.enabled = self.enabled and math.isfinite(self.interval_s) and self.interval_s > 0
        except Exception:
            self.enabled, self.interval_s = False, 5.0
        self._sink, self._clock = sink, clock
        self._condition = threading.Condition()
        self._commands = deque(maxlen=4096)
        self._states, self._observations = {}, {}
        self._thread, self._closed, self._stopping = None, False, False
        self._last_periodic = None

    def start(self):
        if not self.enabled or self._closed or self._thread is not None:
            return self
        try:
            self._thread = threading.Thread(target=self._run, name="robocasa-eval-progress", daemon=True)
            self._thread.start()
        except Exception:
            self.enabled = False
        return self

    def update(
        self,
        worker_id,
        *,
        gpu=_UNSET,
        task=_UNSET,
        attempt_dir=_UNSET,
        attempt_id=_UNSET,
        run_digest=_UNSET,
        episodes=_UNSET,
        max_steps=_UNSET,
        stage=_UNSET,
        error=_UNSET,
        event=None,
    ):
        if not self.enabled or self._closed:
            return
        try:
            fields = {
                "gpu": gpu,
                "task": task,
                "attempt_dir": attempt_dir,
                "attempt_id": attempt_id,
                "run_digest": run_digest,
                "episodes": episodes,
                "max_steps": max_steps,
                "stage": stage,
                "error": error,
            }
            with self._condition:
                self._commands.append(
                    (worker_id, {key: value for key, value in fields.items() if value is not _UNSET}, event)
                )
                self._condition.notify()
        except Exception:
            pass

    def close(self):
        try:
            with self._condition:
                self._closed, self._stopping = True, True
                self._condition.notify_all()
            thread = self._thread
            if thread is not None and thread is not threading.current_thread() and thread.is_alive():
                thread.join(timeout=1.0)
        except Exception:
            pass

    def _run(self):
        try:
            while self.enabled:
                self._cycle()
                with self._condition:
                    if self._stopping:
                        if self._commands:
                            continue
                        return
                    self._condition.wait(timeout=0.1)
        except Exception:
            self.enabled = False

    @staticmethod
    def _binding(state):
        return tuple(state.get(key) for key in ("task", "attempt_dir", "attempt_id", "run_digest"))

    def _cycle(self):
        if not self.enabled:
            return
        with self._condition:
            commands = list(self._commands)
            self._commands.clear()
        for worker, fields, event in commands:
            state = self._states.setdefault(worker, {"worker": worker})
            updated = dict(state, **fields)
            if any(key in fields and fields[key] != state.get(key) for key in ("task", "attempt_dir", "attempt_id")):
                for key in ("attempt_dir", "attempt_id"):
                    if key not in fields:
                        updated[key] = None
            changed = self._binding(state) != self._binding(updated)
            if changed:
                self._poll(state, drain=True)
                self._observations[worker] = _Observation()
                state.clear()
                state.update(worker=worker, gpu=updated.get("gpu"))
                state.update(
                    {
                        key: value
                        for key, value in updated.items()
                        if key in {"task", "attempt_dir", "attempt_id", "run_digest", "episodes"}
                    }
                )
            if event in {"task_complete", "task_error", "error"}:
                self._poll(state, drain=True)
            old_stage = state.get("stage")
            state.update(fields)
            if event:
                self._emit(state, event)
            elif fields.get("stage") != old_stage and "stage" in fields:
                self._emit(state, "stage")
        for state in list(self._states.values()):
            self._poll(state)
        now = self._clock()
        if self._last_periodic is None:
            self._last_periodic = now
        elif now - self._last_periodic >= self.interval_s:
            for state in self._states.values():
                self._emit(state, "heartbeat")
            self._last_periodic = now

    @staticmethod
    def _matches(row, state, *, live=False):
        return (
            isinstance(state.get("run_digest"), str)
            and bool(state["run_digest"])
            and isinstance(state.get("attempt_id"), str)
            and bool(state["attempt_id"])
            and row.get("evaluation_run_digest") == state["run_digest"]
            and row.get("evaluation_attempt_id") == state["attempt_id"]
            and (
                not live
                or (
                    row.get("schema") == "psm_eval_live_progress_v1"
                    and row.get("task") == state.get("task")
                    and _integer(row.get("episodes"), positive=True)
                    and (state.get("episodes") is None or row["episodes"] == state["episodes"])
                )
            )
        )

    def _audit(self, state, observation, episode):
        if not _integer(episode):
            return
        directory = Path(state["attempt_dir"])
        record = observation.audit.setdefault(episode, {})
        for kind in ("actions", "predictions"):
            key = kind + "_tail"
            tail = record.setdefault(key, _Tail(directory / f"rollout{episode:02d}_{kind}.jsonl"))
            try:
                rows, _ = tail.read()
                if tail.reset:
                    record[kind] = None
                    if kind == "predictions":
                        record["latency_ms"] = None
                for row in rows:
                    if (
                        not self._matches(row, state)
                        or type(row.get("episode")) is not int
                        or row["episode"] != episode
                    ):
                        continue
                    if kind == "actions":
                        if not _integer(row.get("source_step")):
                            continue
                    elif not _number(row.get("latency_ms")):
                        continue
                    record[kind] = (record.get(kind) or 0) + 1
                    if kind == "predictions":
                        record["latency_ms"] = row["latency_ms"]
            except Exception:
                pass
        values = observation.values
        if values["episode"] != episode:
            return record
        for kind, field in (("actions", "steps"), ("predictions", "predictions")):
            if record.get(kind) is not None:
                values[field] = max(values.get(field) or 0, record[kind])
        # The child publishes live progress before its prediction audit callback.
        # An audit file one prediction behind must not replace the newer latency.
        if record.get("latency_ms") is not None and record.get("predictions", 0) >= (values.get("predictions") or 0):
            values["last_prediction_ms"] = record["latency_ms"]
        return record

    def _poll(self, state, *, drain=False):
        if not self.enabled or not state.get("attempt_dir") or state.get("stage") in {"complete", "failed"}:
            return
        observation = self._observations.setdefault(state["worker"], _Observation())
        if observation.live is None:
            observation.live = _Tail(Path(state["attempt_dir"]) / "live_progress.jsonl")
        try:
            for _ in range(16 if drain else 1):
                rows, more = observation.live.read()
                for row in rows:
                    if not self._matches(row, state, live=True):
                        continue
                    event, episode = row.get("event"), row.get("episode")
                    if event not in {"stage", "episode_start", "episode_end", "error"}:
                        continue
                    if episode is not None and (
                        not _integer(episode)
                        or (_integer(state.get("episodes"), positive=True) and episode >= state["episodes"])
                    ):
                        continue
                    if event in {"episode_start", "episode_end"} and episode is None:
                        continue
                    values = observation.values
                    if episode is not None and episode != values["episode"]:
                        if values["episode"] is not None and episode < values["episode"]:
                            continue
                        values.update(
                            episode=episode, steps=None, predictions=None, last_prediction_ms=None, outcome=None
                        )
                    for field in ("steps", "predictions", "max_steps"):
                        if _integer(row.get(field), positive=field == "max_steps"):
                            values[field] = row[field]
                    if _number(row.get("last_prediction_ms")):
                        values["last_prediction_ms"] = row["last_prediction_ms"]
                    if row.get("stage") in _LIVE_STAGES:
                        values["stage"] = row["stage"]
                    if row.get("outcome") in {"success", "behavioral_failure", "runtime_error"}:
                        values["outcome"] = row["outcome"]
                    if isinstance(row.get("error"), str) and row["error"]:
                        state["error"] = row["error"]
                    self._audit(state, observation, values["episode"])
                    if event in _IMMEDIATE:
                        self._emit(state, event)
                if not more:
                    break
        except Exception:
            pass
        values = observation.values
        try:
            episodes = sorted(
                {
                    int(match[1])
                    for path in Path(state["attempt_dir"]).iterdir()
                    if (match := _AUDIT_NAME.fullmatch(path.name))
                },
                reverse=True,
            )
            for episode in episodes[:32]:
                if _integer(state.get("episodes"), positive=True) and episode >= state["episodes"]:
                    continue
                if values["episode"] is not None and episode <= values["episode"]:
                    break
                record = self._audit(state, observation, episode)
                if any(record.get(kind) for kind in ("actions", "predictions")):
                    values.update(
                        episode=episode, steps=None, predictions=None, last_prediction_ms=None, stage=None, outcome=None
                    )
                    break
        except Exception:
            pass
        if values["episode"] is not None:
            self._audit(state, observation, values["episode"])

    def _emit(self, state, event):
        if not self.enabled:
            return
        observation = self._observations.get(state["worker"])
        values = observation.values if observation else {}
        episode = values.get("episode")
        stage = state.get("stage")
        if stage not in _ROOT_STAGES:
            stage = values.get("stage") or stage
        latency = values.get("last_prediction_ms")
        latency_text = f"{latency:.1f}" if _number(latency) else "?"
        line = (
            f"[eval-progress] worker={_text(state['worker'])} gpu={_text(state.get('gpu'))} "
            f"task={_text(state.get('task'))} episode={episode + 1 if _integer(episode) else '?'}/{_text(state.get('episodes'))} "
            f"steps={_text(values.get('steps'))}/{_text(values.get('max_steps') or state.get('max_steps'))} "
            f"predictions={_text(values.get('predictions'))} latest_prediction_ms={latency_text} "
        )
        line += f"stage={_text(stage)} event={_text(event)}"
        if values.get("outcome") is not None:
            line += " episode_outcome=" + _text(values["outcome"])
        if state.get("error"):
            line += " error=" + _text(state["error"], 180)
        try:
            if self._sink is None:
                sys.stdout.write(line + "\n")
                sys.stdout.flush()
            else:
                self._sink(line + "\n")
        except Exception:
            self.enabled = False
