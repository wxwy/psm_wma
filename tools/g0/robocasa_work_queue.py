"""Task-level dynamic work queue for RoboCasa latent-cache builders.

This module is intentionally stdlib-only so claim/recovery semantics can be tested
without importing torch, LeRobot, or Cosmos.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import time
from pathlib import Path
from typing import Any


_QUEUE_DIR = ".work_queue"
_CLAIMS_DIR = "claims"
_TASK_MANIFESTS_DIR = "task_manifests"


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def task_manifest_path(output_root: Path, task_slug: str) -> Path:
    return output_root / _QUEUE_DIR / _TASK_MANIFESTS_DIR / f"{task_slug}.json"


def _claim_path(output_root: Path, task_slug: str) -> Path:
    return output_root / _QUEUE_DIR / _CLAIMS_DIR / task_slug


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _local_claim_is_stale(claim_path: Path) -> bool:
    owner_path = claim_path / "owner.json"
    try:
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        # A worker could die between mkdir() and owner publication. Reclaim only
        # after a short grace period so another live worker is not raced.
        try:
            age_s = time.time() - claim_path.stat().st_mtime
        except FileNotFoundError:
            return False
        return age_s >= 120.0

    if owner.get("hostname") != socket.gethostname():
        # Cross-host liveness cannot be proven safely from this process.
        return False
    try:
        pid = int(owner["pid"])
    except (KeyError, TypeError, ValueError):
        return False
    return not _pid_alive(pid)


def try_claim_task(
    *,
    output_root: Path,
    task_slug: str,
    task_class: str,
    worker_id: str,
) -> Path | None:
    """Atomically claim one task.

    The existence of a per-task manifest is the durable "done" authority.
    Claims only protect tasks that have not published that manifest yet.
    """

    manifest = task_manifest_path(output_root, task_slug)
    if manifest.is_file():
        return None

    claims_dir = output_root / _QUEUE_DIR / _CLAIMS_DIR
    claims_dir.mkdir(parents=True, exist_ok=True)
    claim = _claim_path(output_root, task_slug)

    while True:
        try:
            claim.mkdir()
        except FileExistsError:
            if manifest.is_file():
                return None
            if not _local_claim_is_stale(claim):
                return None
            stale = claim.with_name(f"{claim.name}.stale.{os.getpid()}.{time.time_ns()}")
            try:
                claim.rename(stale)
            except FileNotFoundError:
                continue
            except OSError:
                return None
            shutil.rmtree(stale, ignore_errors=True)
            continue

        atomic_write_json(
            claim / "owner.json",
            {
                "task_class": task_class,
                "task_slug": task_slug,
                "worker_id": worker_id,
                "hostname": socket.gethostname(),
                "pid": os.getpid(),
                "claimed_at_unix_s": time.time(),
            },
        )
        return claim


def release_claim(claim_path: Path) -> None:
    """Release a claim after success or failure.

    Episode outputs are independently atomic and resumable, so releasing on
    failure allows a later worker to resume the same task.
    """

    shutil.rmtree(claim_path, ignore_errors=True)
