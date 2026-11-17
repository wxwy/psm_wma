"""Only control processes bearing this run's exact inherited ownership token."""

from __future__ import annotations

import os
import signal
import subprocess
import time
from pathlib import Path

from g2.latent_cache.contract import CacheError

TOKEN = "G2_PRODUCTION_RUN_ID"


def owned_groups(run_id, proc=Path("/proc")):
    groups = {}
    for path in proc.iterdir():
        if not path.name.isdigit():
            continue
        try:
            env = (path / "environ").read_bytes().split(b"\0")
            if (TOKEN + "=" + run_id).encode() not in env:
                continue
            pid = int(path.name)
            if path.stat().st_uid != os.getuid():
                raise CacheError("foreign uid in claimed production process")
            groups.setdefault(os.getpgid(pid), []).append(pid)
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return groups


def terminate_owned(run_id, *, grace_seconds=5):
    groups = owned_groups(run_id)

    # No use of stale PID alone: verify every surviving process in each group
    # has our token before signaling. Never target the caller's own group.
    def checked_signal(pgid, sig):
        if pgid == os.getpgrp():
            raise CacheError("refuse to signal controller process group")
        owned = set(owned_groups(run_id).get(pgid, []))
        if not owned:
            return
        for path in Path("/proc").iterdir():
            if path.name.isdigit():
                try:
                    pid = int(path.name)
                    if os.getpgid(pid) == pgid and pid not in owned:
                        # Zombies have no environment and require no signal.
                        state = (path / "stat").read_text().split(") ", 1)[1].split()[0]
                        if state != "Z":
                            raise CacheError(
                                "mixed ownership in production process group"
                            )
                except (FileNotFoundError, ProcessLookupError, PermissionError):
                    continue
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass

    for pgid in groups:
        checked_signal(pgid, signal.SIGTERM)
    deadline = time.monotonic() + grace_seconds
    while owned_groups(run_id) and time.monotonic() < deadline:
        time.sleep(0.05)
    for pgid in owned_groups(run_id):
        checked_signal(pgid, signal.SIGKILL)
    return sorted(groups)


def start_owned(command, *, env, run_id, cwd, stdout=None):
    if (
        not run_id
        or any(c not in "0123456789abcdef" for c in run_id)
        or len(run_id) != 64
    ):
        raise CacheError("invalid production ownership token")
    return subprocess.Popen(
        list(map(str, command)),
        cwd=cwd,
        env=dict(env, **{TOKEN: run_id}),
        start_new_session=True,
        stdout=stdout,
        stderr=subprocess.STDOUT if stdout is not None else None,
    )
