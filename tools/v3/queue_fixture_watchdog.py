"""CPU test-only watchdog; real media and production deadlines remain intact."""

from __future__ import annotations

import json
import os
import signal
import tempfile
import time
from pathlib import Path


class FixtureWatchdogTimeout(AssertionError):
    pass


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
    if root_pid in rows:
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


def watch(process, source, *, case, hard_s, stall_s=180.0, poll_s=0.5, evidence_root=None, media_only=False):
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
    known, previous, samples = {}, None, []
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
    _retain(destination, source, state)  # Must precede SIGKILL/temp-dir cleanup.
    if reason:
        killed = []
        for row in reversed(rows):
            fresh = _processes().get(row["pid"])
            if fresh is not None and fresh["start"] == row["start"]:
                try:
                    os.kill(row["pid"], signal.SIGKILL)
                    killed.append(row["pid"])
                except ProcessLookupError:
                    pass
        process.wait(timeout=10)
        state["killed_owned_pids"] = killed
        state["returncode_after_cleanup"] = process.returncode
        (destination / "watchdog.json").write_text(json.dumps(state, indent=2) + "\n")
        raise FixtureWatchdogTimeout(f"{case}: {reason}; evidence={destination}")
    return code, destination
