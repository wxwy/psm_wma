"""CPU process-group deadlines, cancellation and untrusted progress negative cases."""

import json
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from robocasa_processes import (  # noqa: E402
    EpisodeProgress,
    EvaluationInterrupted,
    OwnedProcess,
    group_alive,
    group_members,
    positive_seconds,
    supervise_simulator,
)


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_nonpositive_or_nonfinite_timeouts_reject(value):
    with pytest.raises(ValueError):
        positive_seconds(value)


def test_dead_leader_descendant_is_killed_but_foreign_process_survives(tmp_path):
    foreign = subprocess.Popen([sys.executable, "-c", "import time;time.sleep(60)"], start_new_session=True)
    ready = tmp_path / "ready"
    script = (
        "import subprocess,sys;subprocess.Popen([sys.executable,'-c',"
        + repr(
            f"import signal,time;from pathlib import Path;signal.signal(signal.SIGTERM,signal.SIG_IGN);Path({str(ready)!r}).touch();time.sleep(60)"
        )
        + "])"
    )
    owned = OwnedProcess([sys.executable, "-c", script], grace_s=0.2)
    try:
        owned.proc.wait(timeout=3)
        until = time.monotonic() + 3
        while not ready.exists() and time.monotonic() < until:
            time.sleep(0.01)
        assert ready.exists()
        witness = owned.close()
        assert witness["signals"] == ["SIGTERM", "SIGKILL"]
        assert group_members(owned.pgid) == {}
        assert foreign.poll() is None
    finally:
        owned.close()
        foreign.terminate()
        foreign.wait(timeout=3)


@pytest.mark.parametrize("failure", ["cancel", "task", "episode", "missing_progress", "server_exit"])
def test_supervisor_cancellation_and_both_wall_clocks(failure, tmp_path):
    stop = threading.Event()
    progress = EpisodeProgress(tmp_path / "progress", digest="identity", episodes=1)
    server = SimpleNamespace(poll=lambda: 17 if failure == "server_exit" else None, returncode=17)
    owned = OwnedProcess(
        [
            sys.executable,
            "-c",
            "pass" if failure == "missing_progress" else "import time;time.sleep(60)",
        ],
        grace_s=0.2,
    )
    if failure == "cancel":
        stop.set()
    try:
        with pytest.raises(EvaluationInterrupted):
            supervise_simulator(
                owned,
                server=server,
                task_deadline=time.monotonic() + (0.1 if failure == "task" else 5),
                episode_wall_s=0.1 if failure == "episode" else 5,
                progress=progress,
                stop=stop,
            )
    finally:
        owned.close()
    assert not group_alive(owned.pgid)


@pytest.mark.parametrize(
    "bad",
    [
        "wrong_digest",
        "duplicate_start",
        "end_first",
        "wrong_episode",
        "too_many",
        "truncate",
        "oversized",
    ],
)
def test_progress_order_identity_and_bounds(bad, tmp_path):
    path = tmp_path / "progress"
    progress = EpisodeProgress(path, digest="identity", episodes=1)
    start = {
        "schema": "psm_episode_progress_v1",
        "evaluation_run_digest": "identity",
        "episode": 0,
        "event": "start",
    }
    rows = [dict(start)]
    if bad == "wrong_digest":
        rows[0]["evaluation_run_digest"] = "foreign"
    elif bad == "wrong_episode":
        rows[0]["episode"] = 1
    elif bad == "end_first":
        rows[0]["event"] = "end"
    elif bad == "duplicate_start":
        rows.append(dict(start))
    elif bad == "too_many":
        rows.extend([dict(start, event="end"), dict(start, episode=1)])
    path.write_text("".join(json.dumps(row) + "\n" for row in rows))
    if bad == "oversized":
        path.write_text("x" * 5000)
    elif bad == "truncate":
        progress.poll()
        path.write_text("")
    with pytest.raises((EvaluationInterrupted, ValueError)):
        progress.poll()


def test_partial_append_cannot_fake_completed_episode(tmp_path):
    path = tmp_path / "progress"
    progress = EpisodeProgress(path, digest="identity", episodes=1)
    path.write_text('{"schema":')
    progress.poll()
    assert progress.offset == 0 and not progress.complete
