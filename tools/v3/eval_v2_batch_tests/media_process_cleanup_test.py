"""Bounded cleanup proof with deterministic ownership and pidfd fault injection."""

import errno
import os
import signal
import subprocess
import sys
import time
from types import SimpleNamespace

import pytest
import robocasa_eval_v2_processes as processes


def ident(pid):
    return dict(pid=pid, pgid=100, session=100, start_ticks=pid)


class World:
    def __init__(self):
        self.time = 0.0
        self.rows = {100: "S", 200: "S"}
        self.identities = {pid: ident(pid) for pid in self.rows}
        self.signals = []
        self.reaped = []
        self.on_pause = lambda: None
        self.on_signal = (
            lambda pid, sig: self.rows.pop(pid, None) if sig == signal.SIGKILL else None
        )
        self.actor = SimpleNamespace(
            owned=SimpleNamespace(
                pgid=100, proc=SimpleNamespace(pid=100, poll=lambda: None)
            ),
            record={"identity": self.identities[100]},
        )

    def pause(self, seconds):
        self.time += seconds
        self.on_pause()

    def send(self, expected, sig):
        assert expected == self.identities[expected["pid"]]
        self.signals.append((expected["pid"], sig))
        self.on_signal(expected["pid"], sig)

    def reap(self, pid, flags):
        assert self.rows[pid] == "Z"
        self.reaped.append(pid)
        self.rows.pop(pid)
        return pid, 0

    def run(self, helpers=(), **overrides):
        args = dict(
            members=lambda pgid: dict(self.rows),
            identity=lambda pid: self.identities.get(pid) if pid in self.rows else None,
            send_signal=self.send,
            reap=self.reap,
            clock=lambda: self.time,
            pause=self.pause,
        )
        args.update(overrides)
        return processes.quiesce_media(self.actor, helpers, 0.1, **args)


def test_normal_late_exit_does_not_signal_slow_media():
    world = World()
    world.on_pause = lambda: world.rows.pop(200, None)
    assert world.run()["clean"]
    assert world.signals == [] and world.time <= 0.1


def test_owned_zombie_is_reaped_without_signalling_actor():
    world = World()
    world.rows[200] = "Z"
    assert world.run()["clean"]
    assert world.reaped == [200] and world.signals == []


def test_ignored_term_is_killed_boundedly_and_actor_survives():
    world = World()
    result = world.run()
    assert result["clean"] and set(world.rows) == {100}
    assert world.signals == [(200, signal.SIGTERM), (200, signal.SIGKILL)]
    assert world.time <= 0.31 and len(result["actions"]) == 2


def test_survivor_after_kill_still_blocks_core_followup():
    world = World()
    world.on_signal = lambda pid, sig: None
    with pytest.raises(RuntimeError, match="descendants remain after Core commit"):
        world.run()
    assert world.time <= 0.31 and 200 in world.rows


@pytest.mark.parametrize(
    "field,value", [("pgid", 99), ("session", 99), ("start_ticks", 1)]
)
def test_foreign_process_identity_never_gets_signalled(field, value):
    world = World()
    world.identities[200][field] = value
    with pytest.raises(RuntimeError, match="foreign process"):
        world.run()
    assert world.signals == []


def test_unregistered_actor_or_reused_actor_refuses_cleanup():
    world = World()
    world.actor.record = {}
    with pytest.raises(RuntimeError, match="unproven Actor identity"):
        world.run()
    assert world.signals == []


def test_pid_reuse_before_signal_is_refused_without_touching_replacement():
    world = World()
    calls = 0

    def identity(pid):
        nonlocal calls
        if pid == 200 and world.time >= 0.1:
            calls += 1
            if calls == 2:
                return dict(world.identities[200], start_ticks=999)
        return world.identities.get(pid)

    with pytest.raises(RuntimeError, match="PID reuse"):
        world.run(identity=identity)
    assert world.signals == []


def test_new_descendant_during_cleanup_is_not_omitted():
    world = World()

    def on_signal(pid, sig):
        if sig == signal.SIGTERM:
            world.rows[201] = "S"
            world.identities[201] = ident(201)
        else:
            world.rows.pop(pid)

    world.on_signal = on_signal
    assert world.run()["clean"]
    assert set(world.rows) == {100}
    assert (200, signal.SIGKILL) in world.signals and (
        201,
        signal.SIGKILL,
    ) in world.signals


def test_live_resource_tracker_is_allowed_but_exited_helper_need_not_persist():
    world = World()
    command = [
        b"python",
        b"-c",
        b"from multiprocessing.resource_tracker import main;main(5)",
    ]
    assert world.run([200], read_command=lambda pid: command)["clean"]
    assert world.signals == []
    world.rows.pop(200)
    assert world.run([200])["clean"]


def test_foreign_helper_is_rejected_before_reading_command():
    world = World()
    world.identities[200]["pgid"] = 99
    commands = []
    with pytest.raises(RuntimeError, match="unverified media helper"):
        world.run([200], read_command=lambda pid: commands.append(pid))
    assert commands == [] and world.signals == []


def test_helper_that_exits_during_command_read_is_harmless():
    world = World()

    def read(pid):
        world.rows.pop(pid)
        raise FileNotFoundError(errno.ENOENT, "exited")

    assert world.run([200], read_command=read)["clean"]


def test_fake_tracker_command_cannot_hide_residual_process():
    world = World()
    with pytest.raises(RuntimeError, match="unverified media helper"):
        world.run([200], read_command=lambda pid: [b"not_resource_tracker"])
    assert world.signals == []


def test_pidfd_signal_pins_identity_and_closes_descriptor():
    expected, events = ident(200), []
    processes.signal_media_process(
        expected,
        signal.SIGKILL,
        identity=lambda pid: expected,
        open_pidfd=lambda pid, flags: events.append(("open", pid)) or 7,
        fd_signal=lambda fd, sig: events.append(("signal", fd, sig)),
        close_fd=lambda fd: events.append(("close", fd)),
    )
    assert events == [("open", 200), ("signal", 7, signal.SIGKILL), ("close", 7)]


def test_pidfd_refuses_reused_pid_and_closes_without_signalling():
    events = []
    with pytest.raises(RuntimeError, match="PID reuse"):
        processes.signal_media_process(
            ident(200),
            signal.SIGTERM,
            identity=lambda pid: dict(ident(pid), start_ticks=999),
            open_pidfd=lambda pid, flags: 7,
            fd_signal=lambda fd, sig: events.append("signal"),
            close_fd=lambda fd: events.append("close"),
        )
    assert events == ["close"]


def test_pidfd_unavailable_is_fail_closed(monkeypatch):
    monkeypatch.delattr(processes.os, "pidfd_open", raising=False)
    with pytest.raises(RuntimeError, match="pidfd.*unavailable"):
        processes.signal_media_process(ident(200), signal.SIGTERM)


def test_real_owned_orphan_is_killed_and_reaped_without_touching_foreign_process(
    tmp_path,
):
    """Actual CPU process group/pidfd integration, no simulator or encoder library."""
    ready = tmp_path / "orphan_ready"
    actor_ready = tmp_path / "actor_ready"
    child_code = (
        "import os,signal,time;from pathlib import Path;"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
        f"Path({str(ready)!r}).write_text(str(os.getpid()));"
        "time.sleep(60)"
    )
    spawner = (
        f"import subprocess,sys;subprocess.Popen([sys.executable,'-c',{child_code!r}])"
    )
    code = (
        "import subprocess,sys,time;from pathlib import Path;"
        f"p=subprocess.Popen([sys.executable,'-c',{spawner!r}]);p.wait();"
        f"Path({str(actor_ready)!r}).touch();time.sleep(60)"
    )
    foreign = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(60)"], start_new_session=True
    )
    registry = processes.Registry(tmp_path, 0.3)
    owned = record = None
    try:
        owned, record = registry.start(
            [sys.executable, "-c", code], kind="CPU_media_cleanup"
        )
        until = time.monotonic() + 10
        while not (ready.exists() and actor_ready.exists()):
            assert owned.proc.poll() is None
            assert time.monotonic() < until, "bounded CPU orphan startup expired"
            time.sleep(0.01)
        pid = int(ready.read_text())
        assert processes.process_identity(pid)["pgid"] == owned.pgid
        result = processes.quiesce_media(
            SimpleNamespace(owned=owned, record=record), [], 0.1
        )
        assert result["clean"] and processes.process_identity(pid) is None
        assert foreign.poll() is None and owned.proc.poll() is None
        assert (pid, "SIGKILL") in [
            (row["pid"], row["action"]) for row in result["actions"]
        ]
        with pytest.raises(ChildProcessError):
            os.waitpid(pid, os.WNOHANG)  # Already reaped, not merely a zombie.
    finally:
        if owned is not None:
            registry.close(owned, record)
        foreign.terminate()
        foreign.wait(timeout=3)
