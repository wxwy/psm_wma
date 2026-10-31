"""Foreground No-TTT stdout/stderr split. Stdlib only; never imports training.

Raw bytes reach the unique log before a progress copy reaches the console.
Initialization is displayed in full through the Trainer's Starting training log;
only subsequent progress lines are copied to the console.
Linux subreaper ownership covers torchrun Ranks in separate sessions; process
tree scans occur only on exit/cancellation, never while training is running.
"""

from __future__ import annotations

import ctypes
import os
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_ANSI = re.compile(rb"\x1b\[[0-?]*[ -/]*[@-~]")
_TRAINING_LOG = re.compile(
    rb"\[\d{2}-\d{2} \d{2}:\d{2}:\d{2}\|(?:[^\r\n]*\|[ \t]*)?INFO\|"
    rb"(?:[^\r\n]*[/\\])?cosmos_framework[/\\]trainer[/\\]__init__\.py:"
    rb"\d+:train\] Starting training\.\.\."
)


def _starts_training(line):
    plain = _ANSI.sub(b"", line).rstrip(b"\r")
    return (
        plain == b"Starting training..." or _TRAINING_LOG.fullmatch(plain) is not None
    )


def _write_all(fd, value):
    view = memoryview(value)
    while view:
        count = os.write(fd, view)
        if count <= 0:
            raise OSError("short log write")
        view = view[count:]


def _console(fd, text):
    try:
        _write_all(
            fd,
            text if isinstance(text, bytes) else text.encode("utf-8", errors="replace"),
        )
    except OSError:
        pass  # A detached terminal must not prevent durable file logging.


def _owned():
    rows = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            fields = path.read_text().rsplit(")", 1)[1].split()
            rows[int(path.parent.name)] = (int(fields[1]), fields[19], fields[0])
        except (OSError, ValueError, IndexError):
            continue
    result, parents = {}, {os.getpid()}
    while True:
        found = {
            pid: row
            for pid, row in rows.items()
            if row[0] in parents and pid not in result
        }
        if not found:
            return result
        result.update(found)
        parents.update(found)


def _signal(pid, row, sig):
    try:
        fresh = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        if fresh[19] == row[1]:  # Do not signal a PID reused after the snapshot.
            os.kill(pid, sig)
    except ProcessLookupError:
        pass
    except FileNotFoundError:
        pass


class _Output:
    def __init__(self, pipe, log_fd):
        self.pipe, self.log_fd = pipe, log_fd
        self.selector = selectors.DefaultSelector()
        os.set_blocking(pipe.fileno(), False)
        self.selector.register(pipe, selectors.EVENT_READ)
        self.pending, self.tail = b"", b""
        self.discard = self.eof = False
        self.training_started = False
        self.error = None

    def poll(self, timeout):
        if self.eof:
            time.sleep(min(timeout, 0.02))
            return
        if not self.selector.select(timeout):
            return
        chunk = os.read(self.pipe.fileno(), 65536)
        if not chunk:
            self.eof = True
            self.selector.unregister(self.pipe)
            return
        self.tail = (self.tail + chunk)[-8192:]
        if self.error is not None:
            return  # Fail-closed teardown is in progress; no more console copies.
        try:
            _write_all(self.log_fd, chunk)
        except OSError as exc:
            self.error = exc
            raise
        # Bound console framing even for an enormous/unterminated JSON line.
        # The raw log has no such limit and always receives every byte.
        parts = chunk.split(b"\n")
        for index, part in enumerate(parts):
            complete = index < len(parts) - 1
            if not self.training_started:
                # Stream even partial/huge/invalid-UTF8 initialization bytes.
                # The complete marker is echoed before changing mode, including
                # when later filtered lines are in this same read() chunk.
                _console(1, part + b"\n" if complete else part)
            if not self.discard:
                self.pending += part
                if len(self.pending) > 16384:
                    self.pending, self.discard = b"", True
            if complete:
                if not self.training_started:
                    if not self.discard and _starts_training(self.pending):
                        self.training_started = True
                elif not self.discard and self.pending.startswith(
                    b"[CorrectedV3][progress] "
                ):
                    _console(
                        1, (self.pending + b"\n").decode("utf-8", errors="replace")
                    )
                self.pending, self.discard = b"", False

    def close(self):
        self.selector.close()
        self.pipe.close()


def _cleanup(process, output, requested):
    """Only descendants of this standalone supervisor, including adopted Ranks."""
    if process.poll() is None:
        process.send_signal(requested or signal.SIGTERM)
    until = time.monotonic() + 7
    kill_at = time.monotonic() + 5
    signalled = set()
    while time.monotonic() < until:
        process.poll()  # Popen alone reaps the torchrun leader.
        rows = _owned()
        if not rows:
            break
        for pid, row in rows.items():
            if time.monotonic() >= kill_at and row[2] != "Z":
                _signal(pid, row, signal.SIGSTOP)
        for pid, row in reversed(list(rows.items())):
            if row[2] != "Z":
                if time.monotonic() >= kill_at:
                    _signal(pid, row, signal.SIGKILL)
                elif process.returncode is not None and (pid, row[1]) not in signalled:
                    _signal(pid, row, requested or signal.SIGTERM)
                    signalled.add((pid, row[1]))
            if pid != process.pid:
                try:
                    os.waitpid(pid, os.WNOHANG)
                except ChildProcessError:
                    pass
        if output is None:
            time.sleep(0.02)
        else:
            try:
                output.poll(0.02)
            except OSError as exc:
                output.error = exc
    if _owned():
        raise RuntimeError("owned Rank/Worker processes survived bounded cleanup")
    if output is None:
        process.stdout.close()
        return
    # Writers are now gone; retain the rest of their pipe, including tracebacks.
    until = time.monotonic() + 2
    while not output.eof and time.monotonic() < until:
        try:
            output.poll(0.02)
        except OSError as exc:
            output.error = exc
    if not output.eof:
        raise RuntimeError("owned stdout/stderr did not close after cleanup")


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if (
        len(args) < 4
        or args[2] != "--"
        or not args[1].startswith("no_ttt_")
        or any(c in args[1] for c in "/\\\r\n")
    ):
        _console(
            2, "Usage: no_ttt_console.py OUTPUT_ROOT NO_TTT_JOB -- COMMAND [ARGS...]\n"
        )
        return 2
    output = process = None
    log_fd = None
    path = "not created"
    requested, previous = [], {}
    error, code = None, 1
    try:
        directory = Path(args[0]) / "_launch_logs" / args[1]
        directory.mkdir(parents=True, exist_ok=True)
        log_fd, path = tempfile.mkstemp(
            prefix=f"launch_{time.time_ns()}_", suffix=".log", dir=directory
        )
        # This is a standalone CLI process, not a library changing its caller.
        Path("/proc/self/stat").read_text()
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "cannot enable owned child subreaper")
        for sig in (signal.SIGINT, signal.SIGTERM):
            previous[sig] = signal.signal(
                sig, lambda signum, frame: requested.append(signum)
            )
        _console(1, f"[NoTTT][log] full log: {path}\n")
        process = subprocess.Popen(
            args[3:],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
            bufsize=0,
        )
        output = _Output(process.stdout, log_fd)
        while process.poll() is None and not requested:
            output.poll(0.1)
        code = (
            process.returncode if process.returncode is not None else 128 + requested[0]
        )
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        try:
            if process is not None:
                _cleanup(process, output, requested[0] if requested else None)
                if output is not None and output.error is not None:
                    raise output.error
        except Exception as exc:
            error = f"{type(exc).__name__}: {exc}"
        finally:
            if output is not None:
                try:
                    output.close()
                except OSError as exc:
                    error = f"log pipe close failed: {exc}"
            if log_fd is not None:
                try:
                    os.fsync(log_fd)
                except OSError as exc:
                    error = f"log persistence failed: {exc}"
                finally:
                    try:
                        os.close(log_fd)
                    except OSError as exc:
                        error = f"log close failed: {exc}"
            for sig, handler in previous.items():
                signal.signal(sig, handler)
    code = (
        1
        if error
        else 128 + requested[0]
        if requested
        else 128 - code
        if code < 0
        else code
    )
    if code:
        _console(
            2,
            f"[NoTTT][failed] exit={code}; training_exit={process.returncode if process else 'not started'}; "
            f"{error or 'training failed or interrupted'}; full log: {path}\n",
        )
        if output is not None and output.tail:
            _console(
                2,
                "[NoTTT][failed] last raw output:\n"
                + output.tail.decode("utf-8", errors="replace")
                + "\n",
            )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
