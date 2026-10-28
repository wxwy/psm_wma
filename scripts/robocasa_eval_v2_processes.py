"""Real owned process registry and bounded inherited-socket actor supervision."""

from __future__ import annotations

import os
import signal
import socket
import sys
import threading
import time
import uuid
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.store import load, records, save
from cosmos_framework.evaluation.robocasa_v2.wire import receive, send
from robocasa_processes import OwnedProcess, group_members


def process_identity(pid):
    try:
        fields = (
            (Path("/proc") / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()
        )
        return {
            "pid": pid,
            "pgid": int(fields[2]),
            "session": int(fields[3]),
            "start_ticks": int(fields[19]),
        }
    except FileNotFoundError:
        return None


def verify_group(identity):
    current = process_identity(identity["pid"])
    if current is not None and current != identity:
        raise RuntimeError("PID reuse: refusing foreign process cleanup")
    for pid in group_members(identity["pgid"]):
        member = process_identity(pid)
        if member is not None and (
            member["session"] != identity["session"]
            or member["start_ticks"] < identity["start_ticks"]
        ):
            raise RuntimeError("ambiguous process group ownership")


class Registry:
    def __init__(self, root, grace):
        self.root = Path(root)
        self.grace = grace

    def start(self, command, *, kind, **kwargs):
        bootstrap = Path(__file__).with_name("robocasa_eval_v2_child.py")
        protected = [sys.executable, "-B", str(bootstrap), str(os.getpid()), *command]
        owned = OwnedProcess(protected, grace_s=self.grace, **kwargs)
        try:
            identity = process_identity(owned.proc.pid)
            if identity is None:
                raise RuntimeError("process exited before start-identity capture")
            record = {
                "id": uuid.uuid4().hex,
                "kind": kind,
                "identity": identity,
                "command": list(command),
            }
            save(self.root / "_internal/processes" / f"{record['id']}.json", record)
            return owned, record
        except BaseException:
            owned.close()
            raise

    def close(self, owned, record):
        verify_group(record["identity"])
        result = owned.close()
        receipt = {"record": record, "cleanup": result, "closed_ns": time.time_ns()}
        path = self.root / "_internal/process_closed" / f"{record['id']}.json"
        if not path.exists():
            save(path, receipt)
        return receipt

    def recover(self):
        receipts = []
        for rec in records(self.root / "_internal/processes"):
            path = self.root / "_internal/process_closed" / f"{rec['id']}.json"
            if path.exists():
                if load(path)["record"] != rec:
                    raise ValueError("foreign cleanup receipt")
                continue
            identity = rec["identity"]
            verify_group(identity)
            for sig in (signal.SIGTERM, signal.SIGKILL):
                if group_members(identity["pgid"]):
                    os.killpg(identity["pgid"], sig)
                    end = time.monotonic() + self.grace
                    while group_members(identity["pgid"]) and time.monotonic() < end:
                        try:
                            while os.waitpid(-identity["pgid"], os.WNOHANG)[0] > 0:
                                pass
                        except ChildProcessError:
                            pass
                        time.sleep(0.02)
            # Zombies of a crashed coordinator might be owned by PID1. They are
            # not running but cannot be attested reaped here: explicitly block.
            if group_members(identity["pgid"]):
                raise RuntimeError(
                    "prior owned group not reaped; manual cleanup required"
                )
            receipt = {
                "record": rec,
                "cleanup": {"live_group": False, "recovered": True},
                "closed_ns": time.time_ns(),
            }
            save(path, receipt)
            receipts.append(receipt)
        return receipts


class Actor:
    def __init__(self, owned, record, channel, registry, nonce, stop, server, timeout):
        self.owned, self.record, self.channel, self.registry = (
            owned,
            record,
            channel,
            registry,
        )
        self.nonce, self.stop, self.server, self.timeout = nonce, stop, server, timeout
        self.lock = threading.Lock()

    def _receive(self, *, closing=False):
        # A finite socket timeout bounds partial frames too. A monitor thread
        # shuts down the channel on cancellation/server death, unblocking recv.
        deadline = time.monotonic() + self.timeout
        done = threading.Event()

        def monitor():
            while not done.wait(0.05):
                if (
                    not closing
                    and (self.stop.is_set() or self.server.poll() is not None)
                ) or time.monotonic() >= deadline:
                    try:
                        self.channel.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    return

        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        try:
            self.channel.settimeout(self.timeout)
            result = receive(self.channel)
            if result.get("nonce") != self.nonce or result.get("kind") == "FATAL":
                raise RuntimeError(f"actor identity/fatal: {result}")
            if not closing and self.server.poll() is not None:
                raise RuntimeError("Action Server exited during Episode")
            return result
        except BaseException:
            if not closing:
                self.stop.set()
            raise
        finally:
            done.set()
            thread.join(1)

    def request(self, op, *, deadline=None, **kwargs):
        with self.lock:
            previous = self.timeout
            if deadline is not None:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("Episode total wall deadline exceeded")
                self.timeout = min(self.timeout, remaining)
            try:
                self.channel.settimeout(self.timeout)
                request_id = uuid.uuid4().hex
                send(
                    self.channel,
                    dict(op=op, request_id=request_id, nonce=self.nonce, **kwargs),
                )
                result = self._receive(closing=op == "close")
                if result.get("request_id") != request_id:
                    raise ValueError("stale actor response")
                return result
            finally:
                self.timeout = previous

    def close(self):
        error = None
        try:
            if self.owned.proc.poll() is None:
                self.timeout = min(self.timeout, self.registry.grace)
                self.request("close")
        except Exception as e:
            error = repr(e)
        finally:
            self.channel.close()
            proof = self.registry.close(self.owned, self.record)
        return dict(proof, close_error=error)
