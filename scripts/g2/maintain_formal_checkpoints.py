#!/usr/bin/env python3
"""Safe, repository-owned G2 formal R1/R2 DCP retention watcher.

Permanently keep Iter 1000 and every multiple of 5000 through 30000.
Temporarily protect the current latest completed checkpoint, because it is
needed by strict same-job Resume even if it is not a permanent milestone.
Never alter latest_checkpoint.txt or checkpoint save cadence.
This script does NOT import any external project code.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

KEEP = frozenset({1000, 5000, 10000, 15000, 20000, 25000, 30000})
ITER_NAME = re.compile(r"iter_([0-9]{9})\Z")
TAG_NAME = re.compile(r"[a-z0-9][a-z0-9_-]{0,47}\Z")
COMPONENTS = ("model", "optim", "scheduler", "trainer")
LATEST_FILE = "latest_checkpoint.txt"
MARKER = "complete.v1.json"
MARKER_SCHEMA = "psm_v3_sync_local_v1"
IDENTITY_SCHEMA = "corrected_phase5_f0_v1"


class SafetyRefusal(RuntimeError):
    """Refuse to delete on a missing, changed, or ambiguous safety invariant."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _real_directory(path: Path) -> bool:
    return path.is_dir() and not path.is_symlink()


def _real_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink()


def job_root(output_root: Path, profile: str, tag: str) -> Path:
    if profile not in {"r1", "r2"} or not TAG_NAME.fullmatch(tag):
        raise ValueError("expected profile r1|r2 and a safe formal job tag")
    return (
        output_root
        / "psm_wma_v3"
        / "corrected_phase5"
        / f"{profile}_g2_formal_30000_{tag}"
    )


def _validate_identity(job: Path, profile: str) -> None:
    identity = job / "v3_job_identity.json"
    if not _real_file(identity):
        raise SafetyRefusal("missing or aliased formal job identity")
    record = json.loads(identity.read_text(encoding="utf-8"))
    semantic = record.get("semantic")
    if (
        record.get("schema") != IDENTITY_SCHEMA
        or record.get("namespace") != str(job)
        or record.get("diagnostic_only_do_not_resume") is not False
        or not isinstance(semantic, dict)
        or semantic.get("training_profile") != f"g2_{profile.upper()}"
        or semantic.get("root") != record.get("root")
        or semantic.get("child") != record.get("child")
        or not isinstance(record.get("root"), str)
        or not isinstance(record.get("child"), str)
        or not re.fullmatch(r"[0-9a-f]{40}", record["root"])
        or not re.fullmatch(r"[0-9a-f]{40}", record["child"])
    ):
        raise SafetyRefusal("not the expected, non-diagnostic R1/R2 training job")


def _read_latest(ckpts: Path) -> tuple[str, int] | None:
    pointer = ckpts / LATEST_FILE
    if not pointer.exists() and not pointer.is_symlink():
        return None
    if not _real_file(pointer):
        raise SafetyRefusal("latest checkpoint pointer is not a regular file")
    content = pointer.read_text(encoding="utf-8")
    if len(content) > 40:
        raise SafetyRefusal("oversize latest checkpoint pointer")
    match = ITER_NAME.fullmatch(content.strip())
    if not match:
        raise SafetyRefusal("invalid latest checkpoint pointer")
    iteration = int(match.group(1))
    if iteration < 100 or iteration > 30000 or iteration % 100:
        raise SafetyRefusal("latest checkpoint outside formal 100-step schedule")
    return match.group(0), iteration


def _published(ckpts: Path, name: str) -> bool:
    match = ITER_NAME.fullmatch(name)
    if not match:
        return False
    directory = ckpts / name
    marker = directory / MARKER
    if not _real_directory(directory) or not _real_file(marker):
        return False
    try:
        record = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    iteration = int(match.group(1))
    if (
        not isinstance(record, dict)
        or record.get("schema") != MARKER_SCHEMA
        or record.get("complete") is not True
        or record.get("checkpoint") != name
        or type(record.get("iteration")) is not int
        or record["iteration"] != iteration
        or record.get("world_size") != 4
        or not isinstance(record.get("components"), dict)
        or not set(COMPONENTS).issubset(record["components"])
        or not isinstance(record.get("sidecars"), dict)
        or not {str(k) for k in range(4)}.issubset(record["sidecars"])
    ):
        return False
    for component in COMPONENTS:
        part = directory / component
        if not _real_directory(part) or not _real_file(part / ".metadata"):
            return False
    loader = directory / "dataloader"
    if not _real_directory(loader):
        return False
    return all(_real_file(loader / f"rank_{rank}.pkl") for rank in range(4))


def sweep(
    output_root: Path,
    profile: str,
    tag: str,
    *,
    apply: bool = False,
    min_age_seconds: int = 30,
) -> dict:
    """Plan or perform a single fail-closed pass within exactly one formal job."""
    if min_age_seconds < 0:
        raise ValueError("negative min_age_seconds")
    output_root = Path(output_root).absolute()
    job = job_root(output_root, profile, tag)
    result = {
        "at_utc": _now(),
        "profile": profile.upper(),
        "tag": tag,
        "mode": "APPLY" if apply else "DRY_RUN",
        "keep_permanent": sorted(KEEP),
        "protected_latest": None,
        "eligible": [],
        "deleted": [],
        "skipped": [],
    }
    if not job.exists() and not job.is_symlink():
        result["status"] = "WAIT_JOB"
        return result
    if not _real_directory(job):
        raise SafetyRefusal("non-regular formal job directory")
    _validate_identity(job, profile)
    ckpts = job / "checkpoints"
    if not ckpts.exists() and not ckpts.is_symlink():
        result["status"] = "WAIT_FIRST_DCP"
        return result
    if not _real_directory(ckpts):
        raise SafetyRefusal("non-regular checkpoints directory")
    latest = _read_latest(ckpts)
    if latest is None:
        result["status"] = "WAIT_FIRST_DCP"
        return result
    latest_name, latest_iteration = latest
    result["protected_latest"] = latest_name
    if not _published(ckpts, latest_name):
        result["status"] = "WAIT_COMPLETE_LATEST"
        return result
    now = time.time()
    for path in sorted(ckpts.iterdir()):
        match = ITER_NAME.fullmatch(path.name)
        if match is None:
            continue  # .iter_* staging, pointer, and all unknown files untouched
        iteration = int(match.group(1))
        if iteration in KEEP or iteration >= latest_iteration:
            continue
        if iteration <= 0 or iteration > 30000 or iteration % 100:
            result["skipped"].append([path.name, "off_schedule"])
            continue
        if not _published(ckpts, path.name):
            result["skipped"].append([path.name, "incomplete_or_unsafe"])
            continue
        marker_age = now - (path / MARKER).stat().st_mtime
        if marker_age < min_age_seconds:
            result["skipped"].append([path.name, "recent_publish"])
            continue
        result["eligible"].append(path.name)
        if not apply:
            continue
        # In case the writer atomically changed the pointer while we scanned,
        # stop this pass and re-evaluate on the next iteration.
        if _read_latest(ckpts) != latest or not _published(ckpts, latest_name):
            result["status"] = "RETRY_POINTER_CHANGED"
            return result
        if not _published(ckpts, path.name) or path.is_symlink():
            result["status"] = "RETRY_CANDIDATE_CHANGED"
            return result
        shutil.rmtree(path)
        result["deleted"].append(path.name)
    result["status"] = "APPLIED" if apply else "DRY_RUN"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("r1", "r2"), required=True)
    parser.add_argument("--job-tag", required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--min-age-seconds", type=int, default=30)
    parser.add_argument("--apply", action="store_true", help="Permanently delete eligible completed non-milestone DCPs")
    parser.add_argument("--once", action="store_true", help="Run exactly one pass and exit")
    args = parser.parse_args()
    if not 30 <= args.interval_seconds <= 3600:
        parser.error("interval-seconds must be 30..3600")
    if not 0 <= args.min_age_seconds <= 3600:
        parser.error("min-age-seconds must be 0..3600")
    job_root(args.output_root, args.profile, args.job_tag)  # fail early
    while True:
        try:
            report = sweep(
                args.output_root,
                args.profile,
                args.job_tag,
                apply=args.apply,
                min_age_seconds=args.min_age_seconds,
            )
            print(json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True)
        except (OSError, ValueError, SafetyRefusal) as error:
            print(json.dumps({
                "at_utc": _now(),
                "status": "SAFETY_REFUSAL",
                "type": type(error).__name__,
                "message": str(error),
            }, sort_keys=True), file=sys.stderr, flush=True)
            raise SystemExit(1) from error  # never retry an unexpected destructive condition
        if args.once:
            return
        time.sleep(args.interval_seconds)


if __name__ == "__main__":
    main()
