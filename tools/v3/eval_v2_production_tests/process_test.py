"""Actual CPU processes/sockets: owned cleanup, stale PID refusal and framing."""

import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest
from cosmos_framework.evaluation.robocasa_v2.wire import receive
from robocasa_eval_v2_processes import Actor, Registry
from robocasa_processes import group_members

ACTOR_CODE = """
import socket,sys
from cosmos_framework.evaluation.robocasa_v2.wire import receive,send
s=socket.socket(fileno=int(sys.argv[1]));send(s,{'kind':'READY','nonce':'cpu'})
while True:
 x=receive(s)
 if x['op']=='stall':
  import time;time.sleep(60)
 send(s,{'nonce':'cpu','request_id':x['request_id'],'closed':True})
 if x['op']=='close':break
"""


def actor(tmp_path, timeout=1.0):
    registry = Registry(tmp_path, 0.2)
    parent, child = socket.socketpair()
    proc, record = registry.start(
        [sys.executable, "-c", ACTOR_CODE, str(child.fileno())],
        kind="CPU_actor",
        pass_fds=(child.fileno(),),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    child.close()
    value = Actor(
        proc,
        record,
        parent,
        registry,
        "cpu",
        threading.Event(),
        SimpleNamespace(poll=lambda: None),
        timeout,
    )
    assert value._receive()["kind"] == "READY"
    return value


def test_owned_inherited_socket_actor_close_has_no_live_group(tmp_path):
    value = actor(tmp_path)
    pid = value.owned.proc.pid
    assert value.request("echo")["closed"]
    value.close()
    assert not group_members(pid)
    assert list((tmp_path / "_internal/process_closed").glob("*.json"))


def test_episode_deadline_is_shared_across_requests_and_never_sent_to_worker(tmp_path):
    value = actor(tmp_path, timeout=5.0)
    try:
        deadline = time.monotonic() + 0.2
        assert value.request("echo", deadline=deadline)["closed"]
        start = time.monotonic()
        with pytest.raises((EOFError, OSError)):
            value.request("stall", deadline=deadline)
        assert time.monotonic() - start < 1.0
        assert value.timeout == 5.0
        with pytest.raises(TimeoutError, match="total wall deadline"):
            value.request("echo", deadline=time.monotonic() - 1)
    finally:
        value.close()
    assert not group_members(value.owned.pgid)


def test_stalled_actor_request_is_bounded_and_unrelated_process_survives(tmp_path):
    foreign = subprocess.Popen(
        [sys.executable, "-c", "import time;time.sleep(60)"], start_new_session=True
    )
    value = actor(tmp_path, timeout=0.15)
    start = time.monotonic()
    try:
        with pytest.raises((EOFError, OSError)):
            value.request("stall")
        value.stop.set()
        value.close()
        assert time.monotonic() - start < 3
        assert foreign.poll() is None and not group_members(value.owned.pgid)
    finally:
        foreign.terminate()
        foreign.wait(timeout=2)
        if value.owned.proc.poll() is None:
            value.registry.close(value.owned, value.record)


def test_registry_recovery_and_reused_pid_identity_never_signal_foreign(tmp_path):
    registry = Registry(tmp_path, 0.2)
    owned, record = registry.start(
        [sys.executable, "-c", "import time;time.sleep(60)"], kind="CPU_recover"
    )
    try:
        from cosmos_framework.evaluation.robocasa_v2.store import sealed, write

        path = tmp_path / "_internal/processes" / f"{record['id']}.json"
        bad = {
            **record,
            "identity": dict(
                record["identity"], start_ticks=record["identity"]["start_ticks"] + 1
            ),
        }
        write(path, sealed(bad), replace=True)
        with pytest.raises(RuntimeError, match="PID reuse"):
            registry.recover()
        assert owned.proc.poll() is None
        write(path, sealed(record), replace=True)
        registry.recover()
        assert not group_members(owned.pgid)
    finally:
        if owned.proc.poll() is None:
            try:
                owned.close()
            except ChildProcessError:
                pass


@pytest.mark.parametrize(
    "payload", [b"\0\x20\0\0", b"\0\0\0\x02[]", b"\0\0\0\x02\xff\xff"]
)
def test_wire_rejects_oversized_nonobject_and_bad_encoding(payload):
    parent, child = socket.socketpair()
    try:
        parent.sendall(payload)
        parent.shutdown(socket.SHUT_WR)
        with pytest.raises((ValueError, UnicodeError, EOFError)):
            receive(child)
    finally:
        parent.close()
        child.close()


def test_protected_child_dies_when_its_coordinator_disappears(tmp_path):
    # This pytest process is the living subreaper, so it can reap the orphan.
    import ctypes
    import os

    from robocasa_eval_v2_processes import process_identity

    libc = ctypes.CDLL(None, use_errno=True)
    assert libc.prctl(36, 1, 0, 0, 0) == 0
    path = tmp_path / "pid.txt"
    code = 'from robocasa_eval_v2_processes import Registry; import os,sys; from pathlib import Path; r=Registry(Path(sys.argv[1]),.1); p,rec=r.start([sys.executable,"-c","import time;time.sleep(60)"],kind="CPU_parent_loss"); Path(sys.argv[2]).write_text(str(p.proc.pid)); os._exit(0)'
    parent = subprocess.Popen(
        [sys.executable, "-c", code, str(tmp_path / "owned"), str(path)]
    )
    parent.wait(timeout=5)
    pid = int(path.read_text())
    end = time.monotonic() + 3
    while time.monotonic() < end:
        try:
            got, _ = os.waitpid(pid, os.WNOHANG)
            if got == pid:
                break
        except ChildProcessError:
            if process_identity(pid) is None:
                break
        time.sleep(0.02)
    assert process_identity(pid) is None
