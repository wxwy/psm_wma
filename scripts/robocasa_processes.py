"""Bounded supervision of only the process groups created by this evaluation.

No model, simulator or GPU imports. Episode progress is an append-only protocol:
the evaluator writes start before reset and end after media and session cleanup.
"""

from __future__ import annotations

import ctypes
import json
import math
import os
import signal
import subprocess
import time
from pathlib import Path
from threading import Event


class EvaluationInterrupted(RuntimeError):
    """A wall budget, cancellation or infrastructure boundary was violated."""


def positive_seconds(value: float) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError("wall/request/grace timeouts must be finite and positive")
    return value


def group_members(pgid: int) -> dict[int, str]:
    members = {}
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            fields = (entry / "stat").read_text().rsplit(")", 1)[1].split()
            if int(fields[2]) == pgid:
                members[int(entry.name)] = fields[0]
        except (FileNotFoundError, ProcessLookupError):
            continue
    return members


def group_alive(pgid: int) -> bool:
    return any(state != "Z" for state in group_members(pgid).values())


class OwnedProcess:
    """Create a new session and retain its group even if the leader exits first."""

    def __init__(self, command, *, grace_s: float, **kwargs):
        self.grace_s = positive_seconds(grace_s)
        # Adopt orphaned grandchildren so a killed leader does not leave zombies
        # to a container PID1 which may never reap. Reap only this owned PGID.
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:  # Linux PR_SET_CHILD_SUBREAPER
            raise OSError(ctypes.get_errno(), "cannot enable evaluation child subreaper")
        self.proc = subprocess.Popen(command, start_new_session=True, **kwargs)
        self.pgid = self.proc.pid
        self.cleanup: dict = {"pid": self.proc.pid, "pgid": self.pgid, "signals": []}
        self._closed = False

    def close(self) -> dict:
        if self._closed:
            return self.cleanup
        try:
            if group_alive(self.pgid):
                self._signal(signal.SIGTERM)
                until = time.monotonic() + self.grace_s
                while group_alive(self.pgid) and time.monotonic() < until:
                    self.proc.poll()  # Reap the leader while waiting for descendants.
                    time.sleep(min(0.02, max(0, until - time.monotonic())))
                if group_alive(self.pgid):
                    self._signal(signal.SIGKILL)
            self.proc.wait(timeout=self.grace_s)
            until = time.monotonic() + self.grace_s
            while group_members(self.pgid) and time.monotonic() < until:
                try:
                    while os.waitpid(-self.pgid, os.WNOHANG)[0] > 0:
                        pass
                except ChildProcessError:
                    pass
                time.sleep(0.02)
            if group_members(self.pgid):
                raise EvaluationInterrupted(f"owned process group {self.pgid} survived cleanup or was not reaped")
            self.cleanup.update(returncode=self.proc.returncode, live_group=False, remaining_pids=[])
            self._closed = True
        except BaseException as error:
            self.cleanup["error"] = f"{type(error).__name__}: {error}"
            raise
        return self.cleanup

    def _signal(self, sig: signal.Signals) -> None:
        try:
            os.killpg(self.pgid, sig)
            self.cleanup["signals"].append(sig.name)
        except ProcessLookupError:
            pass


class EpisodeProgress:
    def __init__(self, path: Path, *, digest: str, episodes: int, attempt_id: str | None = None):
        # Older process-only callers may omit it; the formal queue always binds
        # this monitor to the same Task/Attempt as all other episode evidence.
        if attempt_id is not None and (not isinstance(attempt_id, str) or not attempt_id):
            raise ValueError("expected progress attempt identity must be a nonempty string")
        self.path, self.digest, self.episodes = path, digest, episodes
        self.attempt_id = attempt_id
        self.offset, self.next_episode, self.active = 0, 0, None
        self.started_at = time.monotonic()

    def poll(self) -> None:
        if not self.path.exists():
            return
        with self.path.open("rb") as handle:
            if self.path.stat().st_size < self.offset:
                raise EvaluationInterrupted("episode progress was truncated")
            handle.seek(self.offset)
            while True:
                line = handle.readline(4097)
                if not line:
                    return
                if len(line) > 4096:
                    raise EvaluationInterrupted("oversized episode progress event")
                if not line.endswith(b"\n"):
                    return  # Concurrent append: consume only a complete event.
                self.offset += len(line)
                row = json.loads(line)
                expected = self.next_episode
                if (
                    not isinstance(row, dict)
                    or row.get("schema") != "psm_episode_progress_v1"
                    or row.get("evaluation_run_digest") != self.digest
                    or (self.attempt_id is not None and row.get("evaluation_attempt_id") != self.attempt_id)
                    or type(row.get("episode")) is not int
                    or row["episode"] != expected
                    or expected >= self.episodes
                ):
                    raise EvaluationInterrupted("episode progress identity/order mismatch")
                if row.get("event") == "start" and self.active is None:
                    self.active = expected
                    # Observation time, never a child-controlled timestamp extending a budget.
                    self.started_at = time.monotonic()
                elif row.get("event") == "end" and self.active == expected:
                    self.active = None
                    self.next_episode += 1
                    self.started_at = time.monotonic()
                else:
                    raise EvaluationInterrupted("invalid episode start/end transition")

    @property
    def complete(self) -> bool:
        return self.active is None and self.next_episode == self.episodes


def supervise_simulator(
    owned: OwnedProcess,
    *,
    server: subprocess.Popen,
    task_deadline: float,
    episode_wall_s: float,
    progress: EpisodeProgress,
    stop: Event,
) -> int:
    while True:
        progress.poll()
        if stop.is_set():
            raise EvaluationInterrupted("evaluation cancelled")
        if server.poll() is not None:
            raise EvaluationInterrupted(f"action server exited during screening with code {server.returncode}")
        now = time.monotonic()
        if now >= task_deadline:
            raise EvaluationInterrupted("task wall timeout")
        # Also bounds environment construction before the first start event and
        # any stall after the last event, including env.close()/process teardown.
        if now - progress.started_at >= episode_wall_s:
            raise EvaluationInterrupted(
                f"episode wall timeout (next={progress.next_episode}, active={progress.active})"
            )
        code = owned.proc.poll()
        if code is not None:
            progress.poll()
            if code == 0 and not progress.complete:
                raise EvaluationInterrupted("simulator exited without complete episode progress")
            return code
        time.sleep(0.02)
