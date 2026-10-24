"""CPU test-only watchdog; real media and production deadlines remain intact."""

from __future__ import annotations

import ctypes
import json
import os
import signal
import sys
import tempfile
import time
from pathlib import Path


class FixtureWatchdogTimeout(AssertionError):
    def __init__(self, message, state=None):
        super().__init__(message)
        self.state = state


def _processes():
    rows = {}
    for path in Path("/proc").glob("[0-9]*/stat"):
        try:
            raw = path.read_text()
            fields = raw[raw.rfind(")") + 2 :].split()
            pid = int(path.parent.name)
            rows[pid] = {
                "pid": pid,
                "ppid": int(fields[1]),
                "pgid": int(fields[2]),
                "state": fields[0],
                "ticks": int(fields[11]) + int(fields[12]),
                "start": fields[19],
                "command": (path.parent / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace"),
            }
        except (OSError, ValueError, IndexError):
            continue
    return rows


def _owned(rows, root_pid, known):
    owned = {pid for pid, start in known.items() if pid in rows and rows[pid]["start"] == start}
    if root_pid in rows and (root_pid not in known or rows[root_pid]["start"] == known[root_pid]):
        owned.add(root_pid)
    while True:
        added = {pid for pid, row in rows.items() if row["ppid"] in owned}
        if added <= owned:
            break
        owned |= added
    for pid in owned:
        known[pid] = rows[pid]["start"]
    return [rows[pid] for pid in sorted(owned)]


def _files(source):
    result = {}
    for path in source.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            stat = path.stat()
            result[str(path.relative_to(source))] = (stat.st_size, stat.st_mtime_ns)
        except OSError:
            continue
    return result


def _retain(destination, source, state):
    # Bounded snapshots preserve raw tiny fixture media, manifests, console and
    # partial JSONL before termination. Skips are explicit, never silent truncation.
    skipped, used = [], 0
    for name, (size, _) in _files(source).items():
        path = source / name
        if size > 32 * 1024 * 1024 or used + size > 128 * 1024 * 1024:
            skipped.append(name)
            continue
        target = destination / "source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("rb") as reader, target.open("wb") as writer:
                remaining = size
                while remaining:
                    chunk = reader.read(min(65536, remaining))
                    if not chunk:
                        break
                    writer.write(chunk)
                    remaining -= len(chunk)
            used += size - remaining
            if remaining:
                skipped.append(f"{name}: changed/shortened during snapshot")
        except OSError as error:
            skipped.append(f"{name}: {error}")
    state["snapshot_skipped"] = skipped
    state["snapshot_scope"] = "bounded prefix at observed file size; concurrent later appends excluded"
    (destination / "watchdog.json").write_text(json.dumps(state, indent=2) + "\n")


def _freeze(process, known, until):
    """Stop writers first, then close over descendants (including new sessions)."""
    rows = []
    while time.monotonic() < until:
        rows = _owned(_processes(), process.pid, known)
        moving = [r for r in rows if r["state"] not in {"T", "t", "Z"}]
        if not moving:
            return rows
        for row in moving:  # Root first prevents its threads spawning more work.
            fresh = _processes().get(row["pid"])
            if fresh is not None and fresh["start"] == row["start"]:
                try:
                    os.kill(row["pid"], signal.SIGSTOP)
                except ProcessLookupError:
                    pass
        time.sleep(0.01)
    raise RuntimeError("owned processes could not be frozen within cleanup budget")


def _cleanup_owned(process, known, state):
    until = time.monotonic() + 10
    state.update(killed_owned_pids=[], cleanup_errors=[], cleanup_budget_s=10)
    try:
        _freeze(process, known, min(until, time.monotonic() + 2))
    except Exception as error:
        state["cleanup_errors"].append(f"freeze: {type(error).__name__}: {error}")
    while time.monotonic() < until:
        rows = _owned(_processes(), process.pid, known)
        live = [row for row in rows if row["state"] != "Z"]
        if not live:
            break
        for row in reversed(live):
            fresh = _processes().get(row["pid"])
            if fresh is not None and fresh["start"] == row["start"]:
                try:
                    os.kill(row["pid"], signal.SIGKILL)
                    if row["pid"] not in state["killed_owned_pids"]:
                        state["killed_owned_pids"].append(row["pid"])
                except OSError as error:
                    state["cleanup_errors"].append(f"kill {row['pid']}: {error}")
        time.sleep(0.01)
    # Popen owns/reaps the root; only reap identified adopted children, never a
    # global waitpid(-1) which could steal another fixture's process status.
    if process.poll() is None:
        process.kill()
    try:
        process.wait(timeout=max(0.01, until - time.monotonic()))
    except Exception as error:
        state["cleanup_errors"].append(f"root reap: {error}")
    while time.monotonic() < until:
        children = [r for r in _owned(_processes(), process.pid, known) if r["pid"] != process.pid]
        if not children:
            break
        for row in children:
            try:
                os.waitpid(row["pid"], os.WNOHANG)
            except ChildProcessError:
                pass
        time.sleep(0.01)
    rows = _owned(_processes(), process.pid, known)
    state["cleanup_final_processes"] = rows
    state["cleanup_remaining_live"] = [r["pid"] for r in rows if r["state"] != "Z"]
    state["returncode_after_cleanup"] = process.returncode


def _cleanup(process, known, state):
    # Linux /proc is already a fixture prerequisite. Temporarily adopt orphaned
    # descendants so killed separate-session children can be reaped, not merely
    # left as zombies under PID1. Never waitpid(-1) or touch foreign controls.
    libc = ctypes.CDLL(None, use_errno=True)
    previous = ctypes.c_int()
    changed = False
    try:
        if libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "GET_CHILD_SUBREAPER")
        if previous.value == 0:
            if libc.prctl(36, 1, 0, 0, 0) != 0:
                raise OSError(ctypes.get_errno(), "SET_CHILD_SUBREAPER")
            changed = True
        state["cleanup_subreaper_original"] = previous.value
    except OSError as error:
        state["cleanup_subreaper_error"] = str(error)
    try:
        _cleanup_owned(process, known, state)
    finally:
        if changed:
            state["cleanup_subreaper_restored"] = libc.prctl(36, previous.value, 0, 0, 0) == 0


def _failure_report(destination, state):
    for name in ("watchdog.json", "cleanup.json"):
        try:
            (destination / name).write_text(json.dumps(state, indent=2) + "\n")
            return
        except Exception as error:
            state.setdefault("diagnostic_write_errors", []).append(f"{name}: {type(error).__name__}: {error}")
    # A full evidence volume must not erase the exception's readable diagnosis.
    print("WATCHDOG_FAILURE " + json.dumps(state, ensure_ascii=True), file=sys.stderr, flush=True)


def _watch(process, source, *, case, hard_s, stall_s, poll_s, evidence_root, media_only, known):
    """CPU-tick/file advances reset idle, never the independent hard deadline.

    Merely being runnable is not progress. Process identity includes start ticks;
    cleanup targets only observed descendants, including their separate sessions.
    """
    if min(hard_s, stall_s, poll_s) <= 0:
        raise ValueError("watchdog budgets must be positive")
    evidence_root = Path(
        evidence_root or os.environ.get("PSM_WMA_FIXTURE_EVIDENCE_DIR", "/tmp/psm-wma-queue-fixture-evidence")
    )
    evidence_root.mkdir(parents=True, exist_ok=True)
    destination = Path(tempfile.mkdtemp(prefix=f"{case}_", dir=evidence_root))
    started = last_progress = time.monotonic()
    previous, samples = None, []
    reason = None
    while True:
        rows = _owned(_processes(), process.pid, known)
        files = _files(source)
        if media_only:
            # UI/server/eval logs can heartbeat while the real action is stuck.
            files = {
                name: value for name, value in files.items() if Path(name).suffix in {".json", ".jsonl", ".mp4", ".png"}
            }
        active = [r for r in rows if not media_only or "ffmpeg" in r["command"] or " -B -c " in r["command"]]
        fingerprint = (files, tuple((r["pid"], r["start"], r["ticks"]) for r in active))
        now = time.monotonic()
        if fingerprint != previous:
            last_progress = now
            previous = fingerprint
        if not samples or now - started - samples[-1]["elapsed_s"] >= 1:
            samples.append({"elapsed_s": now - started, "processes": rows})
        code = process.poll()
        if code is not None:
            break
        if now - started >= hard_s:
            reason = "hard_limit"
            break
        if now - last_progress >= stall_s:
            reason = "no_cpu_or_file_progress"
            break
        time.sleep(poll_s)
    if code is not None and code != 0:
        reason = f"scenario_exit_{code}"
    state = {
        "case": case,
        "root_pid": process.pid,
        "hard_s": hard_s,
        "stall_s": stall_s,
        "reason": reason,
        "progress_policy": "core artifacts/media CPU; heartbeat excluded" if media_only else "file/owned CPU advances",
        "elapsed_s": time.monotonic() - started,
        "returncode_before_cleanup": process.poll(),
        "samples": samples,
        "owned_at_snapshot": rows,
        "files_at_snapshot": _files(source),
    }
    snapshot_error = None
    try:
        if reason:
            state["frozen_before_snapshot"] = _freeze(process, known, time.monotonic() + 2)
        _retain(destination, source, state)
    except BaseException as error:
        snapshot_error = error
        state["snapshot_error"] = f"EVIDENCE_SNAPSHOT_FAILED: {type(error).__name__}: {error}"
        reason = reason or "EVIDENCE_SNAPSHOT_FAILED"
        state["reason"] = reason
    finally:
        if reason:
            # This path is independent of fallible snapshot/report I/O. Refresh
            # ownership after retention, even if a hook resumed/spawned a child.
            _cleanup(process, known, state)
    if reason:
        _failure_report(destination, state)
        if isinstance(snapshot_error, (KeyboardInterrupt, SystemExit)):
            raise snapshot_error
        raise FixtureWatchdogTimeout(
            f"{case}: {reason}; {state.get('snapshot_error', '')}; evidence={destination}", state
        ) from snapshot_error
    return code, destination


def watch(process, source, *, case, hard_s, stall_s=180.0, poll_s=0.5, evidence_root=None, media_only=False):
    """Guard the entire lifecycle, including evidence allocation/observation I/O."""
    known = {}
    try:
        return _watch(
            process,
            source,
            case=case,
            hard_s=hard_s,
            stall_s=stall_s,
            poll_s=poll_s,
            evidence_root=evidence_root,
            media_only=media_only,
            known=known,
        )
    except FixtureWatchdogTimeout:
        raise  # Terminal snapshot path already performed unconditional cleanup.
    except BaseException as error:
        state = {
            "case": case,
            "root_pid": process.pid,
            "reason": "WATCHDOG_INTERNAL_FAILED",
            "snapshot_error": f"EVIDENCE_SNAPSHOT_FAILED: {type(error).__name__}: {error}",
        }
        try:
            _cleanup(process, known, state)
        finally:
            try:
                print("WATCHDOG_FAILURE " + json.dumps(state, ensure_ascii=True), file=sys.stderr, flush=True)
            except OSError:
                pass  # The raised exception still carries readable diagnostics.
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        raise FixtureWatchdogTimeout(f"{case}: {state['snapshot_error']}", state) from error
