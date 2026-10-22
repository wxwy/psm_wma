"""Task-boundary attempts and complete, decodable RoboCasa evidence validation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

from robocasa_processes import OwnedProcess
from v3_evaluation_identity import validate_task_results

SCHEMA = "psm_robocasa_task_attempt_v1"
_ATTEMPT = re.compile(r"attempt_(\d{4,})\Z")
_DIGEST = re.compile(r"[0-9a-f]{64}\Z")


def _safe(path: Path) -> Path:
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError(f"evidence path must not contain symlinks: {path}")
    return path


def _json(path: Path):
    path = _safe(path)
    if not path.is_file():
        raise ValueError(f"missing evidence file: {path}")
    return json.loads(path.read_text(encoding="utf-8"), parse_constant=lambda x: _invalid(f"nonfinite JSON: {x}"))


def _invalid(message: str):
    raise ValueError(message)


def _atomic(path: Path, payload: dict) -> None:
    _safe(path)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=path.parent, prefix=".attempt_", delete=False
    ) as f:
        pending = Path(f.name)
        try:
            json.dump(payload, f, ensure_ascii=False, allow_nan=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        except BaseException:
            pending.unlink(missing_ok=True)
            raise
    try:
        os.replace(pending, path)
    finally:
        pending.unlink(missing_ok=True)


def _check_digest(digest: str) -> None:
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        raise ValueError("evaluation digest must be a SHA256 hex string")


def _marker(directory: Path, digest: str | None = None) -> dict:
    directory = _safe(directory)
    row = _json(directory / "attempt.json")
    if (
        not isinstance(row, dict)
        or row.get("schema") != SCHEMA
        or row.get("attempt_id") != directory.name
        or not _ATTEMPT.fullmatch(directory.name)
        or row.get("status") not in {"RUNNING", "FAILED", "COMPLETE"}
    ):
        raise ValueError("invalid task attempt marker")
    _check_digest(row.get("evaluation_run_digest"))
    if digest is not None and row["evaluation_run_digest"] != digest:
        raise ValueError("foreign task attempt digest")
    return row


def _attempts(task_root: Path, digest: str) -> list[Path]:
    _check_digest(digest)
    task_root = _safe(task_root)
    if not task_root.exists():
        return []
    if not task_root.is_dir():
        raise ValueError("task output must be a directory")
    directories = []
    for directory in sorted(task_root.iterdir()):
        _safe(directory)
        if not directory.is_dir() or not _ATTEMPT.fullmatch(directory.name):
            raise ValueError("unrecognized/legacy task output; never import or overwrite it")
        marker = directory / "attempt.json"
        _safe(marker)
        # An interruption between mkdir and marker publication is a partial
        # attempt too. It can never count as complete or be reused.
        if marker.exists():
            _marker(directory, digest)
        directories.append(directory)
    return directories


def start_attempt(task_root: Path, *, digest: str, resume: bool) -> Path:
    """Reserve a fresh namespace; the simulator always starts at episode zero."""
    directories = _attempts(task_root, digest)
    if directories and not resume:
        raise FileExistsError("task output already exists; explicit same-identity resume required")
    task_root = _safe(task_root)
    task_root.mkdir(parents=True, exist_ok=True)
    index = max((int(path.name.split("_")[1]) for path in directories), default=0) + 1
    directory = task_root / f"attempt_{index:04d}"
    directory.mkdir()  # Exclusive reservation, never merge concurrent attempts.
    _atomic(
        directory / "attempt.json",
        {"schema": SCHEMA, "attempt_id": directory.name, "evaluation_run_digest": digest, "status": "RUNNING"},
    )
    return directory


def _jsonl(path: Path, *, digest: str, episode: int, attempt_id: str) -> list[dict]:
    path = _safe(path)
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing/empty audit JSONL: {path}")
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.endswith("\n") or len(line) > 16 * 1024 * 1024:
                raise ValueError("truncated/oversized audit JSONL record")
            row = json.loads(line, parse_constant=lambda x: _invalid(f"nonfinite audit JSON: {x}"))
            if (
                not isinstance(row, dict)
                or row.get("evaluation_run_digest") != digest
                or type(row.get("episode")) is not int
                or row["episode"] != episode
                or row.get("evaluation_attempt_id") != attempt_id
            ):
                raise ValueError("foreign episode/attempt audit record")
            rows.append(row)
    return rows


def _vector(value, width: int) -> bool:
    return (
        isinstance(value, list)
        and len(value) == width
        and all(type(x) in {int, float} and math.isfinite(x) for x in value)
    )


_MEDIA_PROBE = r"""
import json, subprocess, sys
from pathlib import Path
import imageio_ffmpeg
path, kind = sys.argv[1:]
if kind == 'png':
    from PIL import Image
    with Image.open(path) as image:
        if image.format != 'PNG' or min(image.size) <= 0:
            raise ValueError('invalid PNG')
        image.verify()
    print(json.dumps({'kind': 'png', 'decoded': True}))
else:
    result = subprocess.run([
        imageio_ffmpeg.get_ffmpeg_exe(), '-nostdin', '-v', 'error',
        '-xerror', '-err_detect', 'explode', '-threads', '1', '-filter_threads', '1', '-i', str(Path(path)),
        '-map', '0:v:0', '-an', '-progress', 'pipe:1', '-nostats', '-f', 'null', '-'
    ], capture_output=True, text=True, timeout=90)
    if result.returncode:
        raise RuntimeError('video decode failed: ' + result.stderr[-2000:])
    counts = [int(line.split('=', 1)[1]) for line in result.stdout.splitlines() if line.startswith('frame=')]
    if not counts or max(counts) <= 0:
        raise ValueError('video contains no decodable frames')
    print(json.dumps({'kind': 'mp4', 'decoded': True, 'frames': max(counts)}))
"""


def _remaining(deadline: float | None, maximum: float = 110.0, stop=None) -> float:
    if stop is not None and stop.is_set():
        raise InterruptedError("evaluation cancelled while validating evidence")
    remaining = maximum if deadline is None else min(maximum, deadline - time.monotonic())
    if remaining <= 0:
        raise TimeoutError("task wall deadline expired while validating evidence")
    return remaining


def validate_media(path: Path, *, sim_python: Path, kind: str, deadline: float | None = None, stop=None) -> dict:
    """Decode in the selected simulator interpreter without importing a simulator."""
    path = _safe(path)
    if kind not in {"png", "mp4"} or not path.is_file() or path.stat().st_size == 0:
        raise ValueError(f"missing/empty required media: {path}")
    before = path.stat()
    timeout = _remaining(deadline, stop=stop)
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1")
    owned = OwnedProcess(
        [str(sim_python), "-B", "-c", _MEDIA_PROBE, str(path), kind],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        grace_s=0.2,
    )
    process = owned.proc
    try:
        until = time.monotonic() + timeout
        while True:
            try:
                stdout, stderr = process.communicate(timeout=min(0.1, _remaining(until, stop=stop)))
                break
            except subprocess.TimeoutExpired:
                continue
    except BaseException as error:
        try:
            owned.close()  # Also reap adopted FFmpeg grandchildren, never foreign groups.
        except BaseException as cleanup_error:
            error.add_note(f"decoder cleanup failed: {cleanup_error!r}")
        raise
    else:
        owned.close()
    finally:
        process.stdout.close()
        process.stderr.close()
    if process.returncode:
        raise ValueError(f"required media not decodable: {path}: {stderr[-2000:]}")
    observed = json.loads(stdout)
    after = _safe(path).stat()
    if (
        before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
        or before.st_ctime_ns != after.st_ctime_ns
        or observed.get("kind") != kind
        or observed.get("decoded") is not True
    ):
        raise ValueError("media changed during decode or invalid decoder result")
    return observed


def validate_attempt(
    attempt_dir: Path,
    *,
    digest: str,
    expected_trials: int,
    video_mode: str,
    rollout_enabled: bool,
    init_png_enabled: bool,
    sim_python: Path,
    deadline: float | None = None,
    runtime_digest: str | None = None,
    stop=None,
) -> list[dict]:
    """Reject partial, foreign, mixed or media-incomplete task evidence."""
    attempt_dir = _safe(attempt_dir)
    _remaining(deadline, stop=stop)
    _marker(attempt_dir, digest)
    for artifact in attempt_dir.rglob("*"):
        _safe(artifact)
    cleanup = _json(attempt_dir / "process_cleanup.json")
    if not isinstance(cleanup, dict) or set(cleanup) != {"server", "simulator"}:
        raise ValueError("complete task requires both owned process cleanup witnesses")
    for witness in cleanup.values():
        if (
            not isinstance(witness, dict)
            or "error" in witness
            or type(witness.get("pid")) is not int
            or witness["pid"] <= 0
            or type(witness.get("pgid")) is not int
            or witness["pgid"] <= 0
            or witness.get("live_group") is not False
            or witness.get("remaining_pids") != []
        ):
            raise ValueError("task process cleanup is incomplete or failed")
    if runtime_digest is not None:
        _check_digest(runtime_digest)
        runtime = _json(attempt_dir / "runtime_attestation.json")
        if not isinstance(runtime, dict) or runtime.get("digest") != runtime_digest:
            raise ValueError("missing or foreign in-process runtime attestation")
        body = {key: value for key, value in runtime.items() if key != "digest"}
        canonical = json.dumps(
            body, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode()
        if hashlib.sha256(canonical).hexdigest() != runtime_digest:
            raise ValueError("in-process runtime attestation digest is corrupt")
    if video_mode not in {"none", "first", "all"}:
        raise ValueError("invalid generated video mode")
    attempt_identity = f"{attempt_dir.parent.name}/{attempt_dir.name}"
    rows = _json(attempt_dir / "results.json")
    validate_task_results(rows, digest=digest, expected_trials=expected_trials)
    for episode, row in enumerate(rows):
        _remaining(deadline, stop=stop)
        if row["error"] is not None:
            raise ValueError("runtime errors cannot complete a task attempt")
        if row.get("evaluation_attempt_id") != attempt_identity:
            raise ValueError("foreign task attempt episode result")
        prefix = f"rollout{episode:02d}"
        if _json(attempt_dir / f"{prefix}_episode.json") != row:
            raise ValueError("episode record differs from task result")
        for key, suffix in (("actions_file", "actions"), ("predictions_file", "predictions")):
            if row.get(key) != f"{prefix}_{suffix}.jsonl":
                raise ValueError("audit file is not the current episode's canonical artifact")
        actions = _jsonl(attempt_dir / row["actions_file"], digest=digest, episode=episode, attempt_id=attempt_identity)
        predictions = _jsonl(
            attempt_dir / row["predictions_file"], digest=digest, episode=episode, attempt_id=attempt_identity
        )
        if (
            type(row.get("completed_action_records")) is not int
            or row["completed_action_records"] != len(actions)
            or type(row.get("steps")) is not int
            or row["steps"] != len(actions)
            or type(row.get("replans")) is not int
            or row["replans"] != len(predictions)
        ):
            raise ValueError("audit counts do not match the episode result")
        for index, action in enumerate(actions):
            if (
                type(action.get("source_step")) is not int
                or action["source_step"] != index
                or action.get("evidence_completed") is not True
                or not _vector(action.get("predicted_raw15"), 15)
                or not _vector(action.get("canonical_executed_raw15"), 15)
                or not _vector(action.get("submitted_env12"), 12)
            ):
                raise ValueError("invalid/incomplete raw15-to-env12 action evidence")
        previous = -1
        for prediction in predictions:
            step = prediction.get("step_before_query")
            if type(step) is not int or not previous < step < len(actions) or (previous == -1 and step != 0):
                raise ValueError("invalid prediction/action frontier")
            previous = step
        if rollout_enabled:
            validate_media(
                attempt_dir / f"{prefix}.mp4", sim_python=sim_python, kind="mp4", deadline=deadline, stop=stop
            )
        if init_png_enabled:
            validate_media(
                attempt_dir / f"{prefix}_init.png", sim_python=sim_python, kind="png", deadline=deadline, stop=stop
            )
        generated = row.get("generated_videos")
        names = (
            []
            if video_mode == "none"
            else [f"{prefix}_generated.mp4"]
            if video_mode == "first"
            else [f"{prefix}_generated_replan{index:04d}.mp4" for index in range(len(predictions))]
        )
        if generated != names:
            raise ValueError("generated video evidence does not match the selected mode")
        if sorted(path.name for path in attempt_dir.glob(f"{prefix}_generated*.mp4")) != sorted(names):
            raise ValueError("unexpected generated video artifact")
        if video_mode != "none":
            manifest = _json(attempt_dir / f"{prefix}_generated_manifest.json")
            if (
                not isinstance(manifest, dict)
                or manifest.get("schema") != "psm_generated_video_v1"
                or manifest.get("status") != "COMPLETE"
                or manifest.get("evaluation_run_digest") != digest
                or manifest.get("evaluation_attempt_id") != attempt_identity
                or manifest.get("mode") != video_mode
                or not isinstance(manifest.get("videos"), list)
                or len(manifest["videos"]) != len(names)
            ):
                raise ValueError("invalid generated video manifest")
            for index, (record, name) in enumerate(zip(manifest["videos"], names, strict=True)):
                if (
                    not isinstance(record, dict)
                    or record.get("replan") != index
                    or type(record.get("replan")) is not int
                    or record.get("source_step") != predictions[index]["step_before_query"]
                    or record.get("file") != name
                    or type(record.get("frames")) is not int
                    or record["frames"] <= 0
                ):
                    raise ValueError("generated video manifest lost replan/source correspondence")
                decoded = validate_media(
                    attempt_dir / name, sim_python=sim_python, kind="mp4", deadline=deadline, stop=stop
                )
                if decoded["frames"] != record["frames"]:
                    raise ValueError("generated video frame count differs from manifest")
    return rows


def finish_attempt(attempt_dir: Path, **kwargs) -> list[dict]:
    rows = validate_attempt(attempt_dir, **kwargs)
    marker = _marker(attempt_dir, kwargs["digest"])
    if marker["status"] != "RUNNING":
        raise ValueError("only a running attempt can be committed complete")
    _atomic(attempt_dir / "attempt.json", dict(marker, status="COMPLETE"))
    return rows


def fail_attempt(attempt_dir: Path, error: str) -> None:
    if not isinstance(error, str) or not error:
        raise ValueError("failed attempt requires an error witness")
    marker = _marker(attempt_dir)
    if marker["status"] == "COMPLETE":
        raise ValueError("cannot change a completed attempt")
    if marker["status"] == "FAILED":
        errors = list(marker.get("additional_errors", []))
        if error != marker.get("error") and error not in errors:
            errors.append(error)
        _atomic(attempt_dir / "attempt.json", dict(marker, additional_errors=errors))
    else:
        _atomic(attempt_dir / "attempt.json", dict(marker, status="FAILED", error=error))


def find_completed_attempt(task_root: Path, **kwargs) -> Path | None:
    complete = []
    for directory in _attempts(task_root, kwargs["digest"]):
        if not (directory / "attempt.json").exists():
            continue
        marker = _marker(directory, kwargs["digest"])
        if marker["status"] == "COMPLETE":
            validate_attempt(directory, **kwargs)
            complete.append(directory)
    if len(complete) > 1:
        raise ValueError("multiple completed attempts for one task; ambiguous results")
    return complete[0] if complete else None
