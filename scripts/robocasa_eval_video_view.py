#!/usr/bin/env python3
"""Export independent, descriptive video copies without altering evaluation evidence."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
import unicodedata
from pathlib import Path

SCHEMA = "psm_robocasa_video_view_v1"
_ATTEMPT = re.compile(r"attempt_[0-9]{4,}\Z")
_VIDEO = re.compile(r"rollout([0-9]+)(_generated(?:_replan([0-9]+))?)?\.mp4\Z")


def _safe(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"symlink paths are not supported: {path}")
    return path


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def _sha(path: Path) -> str:
    path = _safe(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as handle:
        before = os.fstat(handle.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"not a regular file: {path}")
        digest = hashlib.sha256()
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
        after = os.fstat(handle.fileno())
    if _witness(before) != _witness(after) or _witness(_safe(path).stat()) != _witness(before):
        raise ValueError(f"file changed while hashing: {path}")
    return digest.hexdigest()


def _witness(value):
    return value.st_ino, value.st_dev, value.st_size, value.st_mtime_ns, value.st_ctime_ns


def _load(path: Path, warnings: list[str], default=None):
    if not path.exists():
        return default
    try:
        _safe(path)
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, ValueError) as error:
        warnings.append(f"cannot read {path}: {type(error).__name__}: {error}")
        return default


def _slug(instruction: str | None, maximum: int = 96) -> str:
    if instruction is None:
        return "unknown_instruction"
    value = unicodedata.normalize("NFKC", instruction).casefold()
    value = "".join(character if character.isalnum() else "_" for character in value)
    value = re.sub(r"_+", "_", value).strip("_")
    if not value:
        return "empty_instruction_" + hashlib.sha256(instruction.encode()).hexdigest()[:10]
    # Byte limits, rather than character limits, keep UTF-8 names below NAME_MAX.
    if len(value.encode()) > maximum:
        suffix = "_" + hashlib.sha256(instruction.encode()).hexdigest()[:10]
        value = value.encode()[: maximum - len(suffix)].decode("utf-8", errors="ignore").rstrip("_") + suffix
    return value


def _bound(row: dict, *, digest, attempt_id, episode: int) -> bool:
    if type(row.get("ep", row.get("episode"))) is not int or row.get("ep", row.get("episode")) != episode:
        return False
    if "evaluation_attempt_id" in row and row["evaluation_attempt_id"] != attempt_id:
        return False
    return digest is None or "evaluation_run_digest" not in row or row["evaluation_run_digest"] == digest


def _episode_metadata(directory: Path, episode: int, digest, warnings):
    attempt_id = f"{directory.parent.name}/{directory.name}"
    candidates = []
    individual = _load(directory / f"rollout{episode:02d}_episode.json", warnings)
    if individual is not None:
        candidates.append(("episode.prompt", individual))
    results = _load(directory / "results.json", warnings, [])
    if isinstance(results, list):
        matching = [
            row for row in results if isinstance(row, dict) and type(row.get("ep")) is int and row["ep"] == episode
        ]
        if len(matching) > 1:
            warnings.append(f"duplicate episode metadata: {directory} episode {episode}")
            return "incomplete", None, None
        if matching:
            candidates.append(("results.prompt", matching[0]))
    valid = []
    for origin, row in candidates:
        if not isinstance(row, dict) or not _bound(row, digest=digest, attempt_id=attempt_id, episode=episode):
            warnings.append(f"foreign or invalid episode metadata: {directory} episode {episode}")
            return "incomplete", None, None
        valid.append((origin, row))
    outcomes = {_outcome(row) for _, row in valid}
    status = outcomes.pop() if len(outcomes) == 1 else "incomplete"
    prompts = [(origin, row["prompt"]) for origin, row in valid if isinstance(row.get("prompt"), str)]
    if len({prompt for _, prompt in prompts}) > 1:
        warnings.append(f"conflicting actual instructions: {directory} episode {episode}")
        return status, None, None
    if prompts:
        return status, prompts[0][1], prompts[0][0]
    live = directory / "live_progress.jsonl"
    instructions = set()
    if live.exists():
        try:
            _safe(live)
            with live.open("rb") as handle:
                while line := handle.readline(65537):
                    if len(line) > 65536 or not line.endswith(b"\n"):
                        warnings.append(f"incomplete/oversized live instruction record: {live}")
                        break
                    row = json.loads(line)
                    if (
                        isinstance(row, dict)
                        and row.get("schema") == "psm_eval_live_progress_v1"
                        and row.get("evaluation_attempt_id") == attempt_id
                        and row.get("task") == directory.parent.name
                        and digest is not None
                        and row.get("evaluation_run_digest") == digest
                        and type(row.get("episode")) is int
                        and row["episode"] == episode
                        and isinstance(row.get("instruction"), str)
                    ):
                        instructions.add(row["instruction"])
        except (OSError, ValueError) as error:
            warnings.append(f"cannot read live instruction {live}: {error}")
    if len(instructions) == 1:
        return status, instructions.pop(), "live_progress.instruction"
    if len(instructions) > 1:
        warnings.append(f"conflicting live instructions: {directory} episode {episode}")
    return status, None, None


def _outcome(row: dict) -> str:
    if isinstance(row.get("error"), str) and (
        row["error"] == "KeyboardInterrupt" or row["error"].startswith("KeyboardInterrupt:")
    ):
        return "incomplete"
    if row.get("outcome") == "runtime_error" or row.get("error") is not None:
        return "error"
    if row.get("outcome") == "success" and row.get("policy") is True:
        return "success"
    if row.get("outcome") == "behavioral_failure" and row.get("policy") is False:
        return "fail"
    return "incomplete"


def _publish_json(path: Path, value) -> None:
    _safe(path)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".video_view_", delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(_canonical(value) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _copy(source: Path, destination: Path, digest: str) -> None:
    """Copy bytes into a new inode and atomically publish without replacing any file."""
    _safe(source)
    _safe(destination)
    fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    temporary = None
    try:
        with os.fdopen(fd, "rb") as reader:
            before = os.fstat(reader.fileno())
            if not stat.S_ISREG(before.st_mode):
                raise ValueError("video source is not a regular file")
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".video_view_", delete=False) as writer:
                temporary = Path(writer.name)
                shutil.copyfileobj(reader, writer, length=1024 * 1024)
                writer.flush()
                os.fsync(writer.fileno())
            if _witness(before) != _witness(os.fstat(reader.fileno())):
                raise ValueError("video changed while copying")
        if _witness(before) != _witness(_safe(source).stat()) or _sha(temporary) != digest:
            raise ValueError("video changed since its identity was computed")
        os.chmod(temporary, stat.S_IMODE(before.st_mode))
        os.utime(temporary, ns=(before.st_atime_ns, before.st_mtime_ns))
        os.link(temporary, destination)  # Link only our independent temporary copy, never the source.
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def export_videos(run_dir: Path, *, view_dir: Path | None = None) -> dict:
    """Best-effort browsing export; this never writes task evidence or changes eval status."""
    result = {
        "schema": SCHEMA,
        "status": "OK",
        "run_dir": str(Path(run_dir).absolute()),
        "view_dir": str(Path(view_dir).absolute()) if view_dir is not None else None,
        "index_file": None,
        "exported_count": 0,
        "reused_count": 0,
        "conflict_count": 0,
        "error_count": 0,
        "records": [],
        "warnings": [],
    }
    warnings = result["warnings"]
    try:
        run_dir = _safe(run_dir)
        if not run_dir.is_dir():
            raise ValueError("run directory does not exist")
        view_dir = _safe(view_dir if view_dir is not None else run_dir / "videos_view")
        result.update(run_dir=str(run_dir), view_dir=str(view_dir), index_file=str(view_dir / "index.json"))
        if view_dir.is_relative_to(run_dir) and view_dir != run_dir / "videos_view":
            raise ValueError("inside a run only the canonical videos_view directory is allowed")
        tasks = []
        for task in sorted(run_dir.iterdir()):
            if task == run_dir / "videos_view":
                continue
            if task.name.startswith("_") or not task.name.isidentifier():
                continue
            if task.is_symlink():
                warnings.append(f"skipping symlink task: {task}")
                continue
            if task.is_dir() and any(_ATTEMPT.fullmatch(child.name) for child in task.iterdir()):
                tasks.append(task)
        if view_dir == run_dir or any(view_dir.is_relative_to(task) for task in tasks):
            raise ValueError("video view must be separate from original task/evidence directories")
        manifest = _load(run_dir / "evaluation_manifest.json", warnings, {})
        digest = manifest.get("digest") if isinstance(manifest, dict) else None
        marker = {"schema": SCHEMA, "run_dir": str(run_dir), "evaluation_run_digest": digest}
        view_dir.mkdir(parents=True, exist_ok=True)
        marker_path = view_dir / ".video_view.json"
        if marker_path.exists():
            if _load(marker_path, warnings) != marker:
                raise ValueError("video view belongs to another run or identity")
        elif any(view_dir.iterdir()):
            raise ValueError("existing nonempty video view has no ownership marker")
        else:
            fd = os.open(marker_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(_canonical(marker) + b"\n")
        lock_fd = os.open(view_dir / ".export.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
        with os.fdopen(lock_fd, "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            index_path = view_dir / "index.json"
            index = (
                _load(index_path, warnings)
                if index_path.exists()
                else {"schema": SCHEMA, "run_dir": str(run_dir), "records": []}
            )
            if (
                not isinstance(index, dict)
                or index.get("schema") != SCHEMA
                or index.get("run_dir") != str(run_dir)
                or not isinstance(index.get("records"), list)
                or any(not isinstance(row, dict) for row in index["records"])
            ):
                raise ValueError("invalid existing video view index")
            for task in tasks:
                for directory in sorted(task.iterdir()):
                    if not _ATTEMPT.fullmatch(directory.name):
                        continue
                    try:
                        _safe(directory)
                        _export_attempt(directory, view_dir, digest, index, result)
                    except (OSError, ValueError) as error:
                        result["error_count"] += 1
                        warnings.append(f"cannot export attempt {directory}: {type(error).__name__}: {error}")
            if result["error_count"] or result["conflict_count"]:
                result["status"] = "PARTIAL"
            index["last_export"] = {
                key: result[key]
                for key in ("status", "exported_count", "reused_count", "conflict_count", "error_count", "warnings")
            }
            _publish_json(index_path, index)
    except (OSError, ValueError) as error:
        result["status"] = "ERROR"
        warnings.append(f"video view export failed: {type(error).__name__}: {error}")
    return result


def _export_attempt(directory, view_dir, run_digest, index, result):
    warnings = result["warnings"]
    marker_path = directory / "attempt.json"
    marker = _load(marker_path, warnings) if marker_path.exists() else {}
    if not isinstance(marker, dict):
        raise ValueError("invalid attempt marker")
    digest = marker.get("evaluation_run_digest", run_digest)
    if run_digest is not None and digest != run_digest:
        raise ValueError("foreign attempt run digest")
    if "attempt_id" in marker and marker["attempt_id"] != directory.name:
        raise ValueError("foreign attempt namespace")
    files = []
    logical = {}
    for source in sorted(directory.glob("*.mp4")):
        match = _VIDEO.fullmatch(source.name)
        if match is None:
            continue
        _safe(source)
        episode = int(match[1])
        kind = "generated_prediction" if match[2] else "environment"
        replan = int(match[3]) if match[3] is not None else (0 if match[2] else None)
        key = (episode, kind, replan)
        logical[key] = logical.get(key, 0) + 1
        files.append((source, episode, kind, replan, match[3]))
    metadata = {}
    for source, episode, kind, replan, replan_text in files:
        if logical[(episode, kind, replan)] != 1:
            result["conflict_count"] += 1
            warnings.append(f"ambiguous duplicate Episode/video identity: {source}")
            continue
        try:
            if episode not in metadata:
                metadata[episode] = _episode_metadata(directory, episode, digest, warnings)
            status, instruction, instruction_source = metadata[episode]
            if instruction is None:
                warnings.append(f"actual instruction missing: {source}")
            digest_source = _sha(source)
            row = {
                "task": directory.parent.name,
                "attempt": directory.name,
                "evaluation_attempt_id": f"{directory.parent.name}/{directory.name}",
                "evaluation_run_digest": digest,
                "episode": episode,
                "status": status,
                "attempt_status": marker.get("status", "UNKNOWN"),
                "instruction": instruction,
                "instruction_missing": instruction is None,
                "instruction_source": instruction_source,
                "original_path": str(source),
                "original_sha256": digest_source,
                "video_kind": kind,
                "prediction_replan": replan,
                "prediction_role": None if kind == "environment" else "replan" if replan_text else "first_prediction",
            }
            identity = hashlib.sha256(_canonical(row)).hexdigest()
            row["export_id"] = identity
            existing = next((item for item in index["records"] if item.get("export_id") == identity), None)
            if existing is not None:
                destination = _safe(Path(existing["output_path"]))
                same_inode = (destination.stat().st_dev, destination.stat().st_ino) == (
                    source.stat().st_dev,
                    source.stat().st_ino,
                )
                if same_inode or not destination.is_relative_to(view_dir) or _sha(destination) != digest_source:
                    raise ValueError("existing export changed or no longer belongs to the view")
                result["reused_count"] += 1
                result["records"].append(existing)
                continue
            previous = [item for item in index["records"] if item.get("original_path") == str(source)]
            revision = max((item.get("revision", 0) for item in previous), default=0) + 1
            suffix = "" if kind == "environment" else f"_generated_replan{replan:04d}"
            name = f"rollout{episode:02d}_{status}_{_slug(instruction)}{suffix}"
            if revision > 1:
                name += f"__rev_{revision:02d}_{identity[:10]}"
            destination = _safe(view_dir / directory.parent.name / directory.name / (name + ".mp4"))
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                result["conflict_count"] += 1
                warnings.append(f"existing unindexed export retained without overwrite: {destination}")
                continue
            _copy(source, destination, digest_source)
            row.update(output_path=str(destination), revision=revision)
            index["records"].append(row)
            result["records"].append(row)
            result["exported_count"] += 1
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["error_count"] += 1
            warnings.append(f"cannot export video {source}: {type(error).__name__}: {error}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--view-dir", type=Path)
    args = parser.parse_args()
    result = export_videos(args.run_dir, view_dir=args.view_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["status"] in {"ERROR", "PARTIAL"} else 0


if __name__ == "__main__":
    raise SystemExit(main())
