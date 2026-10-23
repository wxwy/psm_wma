"""Design-only legacy Episode ingest; no production launcher imports this module.

The caller owns the evaluation lease and model-identity comparison. This scanner
only reads original evidence, using its original digest and original media policy.
It never upgrades an old Task marker, rewrites a result or claims scene continuity
for a future restarted simulator.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from robocasa_eval_results import (  # noqa: E402
    _json,
    _jsonl,
    _marker,
    _safe,
    _unique_object,
    _validate_local_cleanup,
    _vector,
    validate_attempt,
    validate_media,
)
from v3_evaluation_identity import sha256_file  # noqa: E402

_ATTEMPT = re.compile(r"attempt_(\d{4,})\Z")
_ARTIFACT = re.compile(r"rollout(\d+)_(?:episode\.json|actions\.jsonl|predictions\.jsonl|cleanup\.json)\Z")


class EpisodeEvidenceError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def _fail(code, message):
    raise EpisodeEvidenceError(code, message)


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def _policy(protocol):
    result = {
        "save_rollout_mp4": protocol.get("save_rollout_mp4"),
        "save_generated_video": protocol.get("save_generated_video"),
        "save_init_png": protocol.get("save_init_png"),
    }
    if (
        type(result["save_rollout_mp4"]) is not bool
        or type(result["save_init_png"]) is not bool
        or result["save_generated_video"] not in {"none", "first", "all"}
    ):
        _fail("UNKNOWN_ORIGINAL_MEDIA_POLICY", "original manifest must explicitly record its media policy")
    return result


def _manifest(manifest):
    if not isinstance(manifest, dict) or not isinstance(manifest.get("identity"), dict):
        _fail("INVALID_MANIFEST", "legacy manifest is not a digest-bound identity object")
    identity = manifest["identity"]
    if manifest.get("digest") != hashlib.sha256(_canonical(identity)).hexdigest():
        _fail("INVALID_MANIFEST_DIGEST", "legacy manifest canonical digest does not match")
    if identity.get("schema") != "psm_v3_eval_identity_vendor_v1":
        _fail("UNSUPPORTED_LEGACY_SCHEMA", "legacy runtime/ABI provenance is unavailable in this schema")
    protocol = identity.get("protocol")
    if not isinstance(protocol, dict):
        _fail("INVALID_PROTOCOL", "legacy protocol is missing")
    for key, expected in {
        "H_pred": 16,
        "server_action_chunk_size": 16,
        "raw_action_dim": 15,
        "max_action_dim": 64,
        "policy_seed": 0,
        "fps": 20,
        "camera_set": "left_wrist",
        "use_state": True,
        "base_encoding": "raw",
        "local_memory_mode": "required",
    }.items():
        if type(protocol.get(key)) is not type(expected) or protocol[key] != expected:
            _fail("INCOMPATIBLE_LEGACY_ABI", f"original protocol {key} is incompatible with required raw15/state15")
    if type(protocol.get("R")) is not int or not 1 <= protocol["R"] <= 16:
        _fail("INCOMPATIBLE_LEGACY_ABI", "original action horizon is invalid")
    for field in ("root_sha", "child_sha"):
        if not isinstance(identity.get(field), str) or not re.fullmatch(r"[0-9a-f]{40}", identity[field]):
            _fail("INVALID_SOURCE_PROVENANCE", f"missing original {field}")
    runtime = identity.get("evaluation_runtime")
    if not isinstance(runtime, dict) or runtime.get("schema") != "psm_robocasa_runtime_v1":
        _fail("INVALID_RUNTIME", "original runtime attestation missing")
    body = {key: value for key, value in runtime.items() if key != "digest"}
    if runtime.get("digest") != hashlib.sha256(_canonical(body)).hexdigest():
        _fail("INVALID_RUNTIME_DIGEST", "original runtime canonical digest is corrupt")
    task_rows = identity.get("tasks")
    if not isinstance(task_rows, list) or not task_rows:
        _fail("INVALID_LEGACY_TASKS", "original manifest has no task provenance")
    names = []
    for row in task_rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("task"), str)
            or not row["task"].isidentifier()
            or row["task"] == "all"
        ):
            _fail("INVALID_LEGACY_TASKS", "unsafe or missing original task name")
        names.append(row["task"])
    if len(names) != len(set(names)):
        _fail("INVALID_LEGACY_TASKS", "ambiguous duplicate original task source")
    if "seed" in protocol and protocol["seed"] is not None and type(protocol["seed"]) is not int:
        _fail("INVALID_LEGACY_SEED", "original seed provenance is not an integer or explicit unspecified value")
    _policy(protocol)
    return identity, protocol


def _completed_progress(attempt_dir, *, digest, attempt_id):
    """An unfinished final write/start preserves earlier complete ordered pairs."""
    path = _safe(attempt_dir / "episode_progress.jsonl")
    completed, expected, active, tail = set(), 0, False, False
    with path.open("rb") as handle:
        while line := handle.readline(4097):
            if len(line) > 4096:
                _fail("CORRUPT_PROGRESS", "oversized original progress record")
            if not line.endswith(b"\n"):
                tail = True
                break
            try:
                row = json.loads(
                    line,
                    object_pairs_hook=_unique_object,
                    parse_constant=lambda x: _fail("CORRUPT_PROGRESS", f"nonfinite progress {x}"),
                )
            except (ValueError, UnicodeError) as error:
                _fail("CORRUPT_PROGRESS", str(error))
            if (
                not isinstance(row, dict)
                or row.get("schema") != "psm_episode_progress_v1"
                or row.get("evaluation_run_digest") != digest
                or row.get("evaluation_attempt_id") != attempt_id
                or type(row.get("episode")) is not int
                or row["episode"] != expected
                or row.get("event") != ("end" if active else "start")
            ):
                _fail("CORRUPT_PROGRESS", "original episode progress is duplicate, foreign or out of order")
            if active:
                completed.add(expected)
                expected += 1
            active = not active
    return completed, tail or active


def _runtime(attempt_dir, identity):
    runtime = _json(attempt_dir / "runtime_attestation.json", unique_keys=True)
    if runtime != identity["evaluation_runtime"]:
        _fail("FOREIGN_RUNTIME", "attempt runtime differs from its original manifest")
    return runtime


def _media(attempt_dir, row, *, policy, requested, sim_python, digest, attempt_id):
    episode, predictions = row["ep"], row["replans"]
    prefix = f"rollout{episode:02d}"
    hashes, videos = {}, {"rollout": [], "generated": [], "init_png": []}

    def check(name, kind, category):
        path = _safe(attempt_dir / name)
        observed = validate_media(path, sim_python=sim_python, kind=kind)
        hashes[name] = sha256_file(path)
        videos[category].append(str(path))
        return observed

    if policy["save_rollout_mp4"]:
        check(f"{prefix}.mp4", "mp4", "rollout")
    if policy["save_init_png"]:
        check(f"{prefix}_init.png", "png", "init_png")
    mode = policy["save_generated_video"]
    names = (
        []
        if mode == "none"
        else [f"{prefix}_generated.mp4"]
        if mode == "first"
        else [f"{prefix}_generated_replan{index:04d}.mp4" for index in range(predictions)]
    )
    if row.get("generated_videos") != names or sorted(
        path.name for path in attempt_dir.glob(f"{prefix}_generated*.mp4")
    ) != sorted(names):
        _fail("CORRUPT_MEDIA", "original generated artifacts do not match their original policy")
    if names:
        path = attempt_dir / f"{prefix}_generated_manifest.json"
        generated = _json(path, unique_keys=True)
        if (
            not isinstance(generated, dict)
            or generated.get("schema") != "psm_generated_video_v1"
            or generated.get("status") != "COMPLETE"
            or generated.get("evaluation_run_digest") != digest
            or generated.get("evaluation_attempt_id") != attempt_id
            or generated.get("mode") != mode
            or not isinstance(generated.get("videos"), list)
            or len(generated["videos"]) != len(names)
        ):
            _fail("CORRUPT_MEDIA", "original generated manifest is foreign or incomplete")
        hashes[path.name] = sha256_file(path)
        audit = _jsonl(attempt_dir / row["predictions_file"], digest=digest, episode=episode, attempt_id=attempt_id)
        for index, (record, name) in enumerate(zip(generated["videos"], names, strict=True)):
            if (
                not isinstance(record, dict)
                or type(record.get("replan")) is not int
                or record["replan"] != index
                or record.get("file") != name
                or record.get("source_step") != audit[index]["step_before_query"]
                or type(record.get("frames")) is not int
                or record["frames"] <= 0
            ):
                _fail("CORRUPT_MEDIA", "original generated video lost its prediction correspondence")
            if check(name, "mp4", "generated")["frames"] != record["frames"]:
                _fail("CORRUPT_MEDIA", "original generated frame count is inconsistent")
    expected_requested = (
        0
        if requested["save_generated_video"] == "none"
        else 1
        if requested["save_generated_video"] == "first"
        else predictions
    )
    missing = []
    if requested["save_rollout_mp4"] and not videos["rollout"]:
        missing.append("rollout_mp4")
    if requested["save_init_png"] and not videos["init_png"]:
        missing.append("init_png")
    missing.extend(f"generated_prediction_{index}" for index in range(len(names), expected_requested))
    return {
        "available_rollout": bool(videos["rollout"]),
        "available_generated": len(names),
        "prediction_count": predictions,
        "available_init_png": bool(videos["init_png"]),
        "expected_generated_per_original_policy": len(names),
        "original_policy": policy,
        "requested_policy": requested,
        "missing_requested_media": missing,
        "videos_view": videos,
    }, hashes


def _verify_legacy_episode_core(attempt_dir, episode, *, manifest, sim_python, requested_media=None):
    """Validate Episode evidence after the source-level completion claim guard."""
    attempt_dir = _safe(Path(attempt_dir))
    identity, protocol = _manifest(manifest)
    digest, task = manifest["digest"], attempt_dir.parent.name
    marker = _marker(attempt_dir, digest)
    attempt_id = f"{task}/{attempt_dir.name}"
    if task not in {value.get("task") for value in identity.get("tasks", []) if isinstance(value, dict)}:
        _fail("FOREIGN_TASK", "attempt task is not in the original manifest")
    if type(episode) is not int or episode < 0:
        _fail("INVALID_EPISODE", "source episode index must be a nonnegative integer")
    completed, _ = _completed_progress(attempt_dir, digest=digest, attempt_id=attempt_id)
    if episode not in completed:
        _fail("INCOMPLETE_EPISODE", "episode has no complete ordered original start/end pair")
    runtime = _runtime(attempt_dir, identity)
    path = attempt_dir / f"rollout{episode:02d}_episode.json"
    row = _json(path, unique_keys=True)
    if (
        not isinstance(row, dict)
        or type(row.get("ep")) is not int
        or row["ep"] != episode
        or row.get("evaluation_run_digest") != digest
        or row.get("evaluation_attempt_id") != attempt_id
    ):
        _fail("FOREIGN_EPISODE", "episode result identity differs from its original attempt")
    if row.get("outcome") not in {"success", "behavioral_failure"}:
        _fail("NON_COMPLETED_OUTCOME", "runtime_error/interrupted episodes are not reusable")
    if (
        type(row.get("policy")) is not bool
        or row.get("error") is not None
        or row["policy"] != (row["outcome"] == "success")
    ):
        _fail("CORRUPT_OUTCOME", "episode typed outcome is inconsistent")
    aggregate = attempt_dir / "results.json"
    if aggregate.exists():
        values = _json(aggregate, unique_keys=True)
        if not isinstance(values, list):
            _fail("AMBIGUOUS_AGGREGATE", "original task result is not a list")
        matches = [
            value
            for value in values
            if isinstance(value, dict) and type(value.get("ep")) is int and value["ep"] == episode
        ]
        if len(matches) != 1 or matches[0] != row:
            _fail("AMBIGUOUS_AGGREGATE", "task and episode records conflict or duplicate the source index")
    horizon = runtime.get("protocol", {}).get("official_horizons", {}).get(task)
    if type(horizon) is not int or horizon <= 0:
        _fail("UNKNOWN_ORIGINAL_HORIZON", "cannot prove normal horizon termination without original registry witness")
    if type(row.get("steps")) is not int or not 0 < row["steps"] <= horizon:
        _fail("CORRUPT_EPISODE_LENGTH", "completed episode steps lie outside its original official horizon")
    if row["outcome"] == "behavioral_failure" and row["steps"] != horizon:
        _fail("EARLY_BEHAVIORAL_FAILURE", "behavioral failure did not reach its original horizon")
    prefix = f"rollout{episode:02d}"
    _validate_local_cleanup(attempt_dir / f"{prefix}_cleanup.json")
    cleanup = _json(attempt_dir / f"{prefix}_cleanup.json", unique_keys=True)
    if (
        row.get("actions_file") != f"{prefix}_actions.jsonl"
        or row.get("predictions_file") != f"{prefix}_predictions.jsonl"
    ):
        _fail("FOREIGN_AUDIT_PATH", "audit files are not the source episode's canonical paths")
    actions = _jsonl(attempt_dir / row["actions_file"], digest=digest, episode=episode, attempt_id=attempt_id)
    predictions = _jsonl(attempt_dir / row["predictions_file"], digest=digest, episode=episode, attempt_id=attempt_id)
    if (
        type(row.get("completed_action_records")) is not int
        or row["completed_action_records"] != len(actions)
        or row["steps"] != len(actions)
        or type(row.get("replans")) is not int
        or row["replans"] != len(predictions)
    ):
        _fail("CORRUPT_AUDIT_COUNTS", "episode and original audit counts differ")
    for index, action in enumerate(actions):
        if (
            type(action.get("source_step")) is not int
            or action["source_step"] != index
            or action.get("evidence_completed") is not True
            or not _vector(action.get("predicted_raw15"), 15)
            or not _vector(action.get("canonical_executed_raw15"), 15)
            or not _vector(action.get("submitted_env12"), 12)
        ):
            _fail("CORRUPT_ACTION", "raw15/state15 action evidence is incomplete or out of order")
    previous, local_episode = -1, None
    for prediction in predictions:
        frontier = prediction.get("step_before_query")
        if type(frontier) is not int or not previous < frontier < len(actions) or (previous == -1 and frontier != 0):
            _fail("CORRUPT_PREDICTION_FRONTIER", "prediction no longer corresponds to executed action frontier")
        local = prediction.get("local_memory")
        if (
            not isinstance(local, dict)
            or local.get("session_id") != cleanup["session_id"]
            or type(local.get("consumer_step")) is not int
            or local["consumer_step"] != frontier
            or not isinstance(local.get("episode_id"), str)
            or re.fullmatch(r"[0-9a-f]{32}", local["episode_id"]) is None
            or (local_episode is not None and local["episode_id"] != local_episode)
        ):
            _fail(
                "CORRUPT_LOCAL_ACKNOWLEDGEMENT",
                "Local-TTT prediction/cleanup session or completed-evidence acknowledgement differs",
            )
        local_episode = local["episode_id"]
        previous = frontier
    policy = _policy(protocol)
    requested = _policy(requested_media) if requested_media is not None else policy
    try:
        coverage, hashes = _media(
            attempt_dir,
            row,
            policy=policy,
            requested=requested,
            sim_python=sim_python,
            digest=digest,
            attempt_id=attempt_id,
        )
    except EpisodeEvidenceError:
        raise
    except (OSError, ValueError) as error:
        raise EpisodeEvidenceError("CORRUPT_ORIGINAL_MEDIA", str(error)) from error
    for name in (
        "attempt.json",
        "runtime_attestation.json",
        "episode_progress.jsonl",
        path.name,
        f"{prefix}_cleanup.json",
        row["actions_file"],
        row["predictions_file"],
    ):
        hashes[name] = sha256_file(_safe(attempt_dir / name))
    if aggregate.exists():
        hashes["results.json"] = sha256_file(aggregate)
    if marker["status"] == "COMPLETE":
        hashes["process_cleanup.json"] = sha256_file(_safe(attempt_dir / "process_cleanup.json"))
    seed = protocol.get("seed")
    semantic = {
        "outcome": row["outcome"],
        "policy": row["policy"],
        "steps": row["steps"],
        "replans": row["replans"],
        "actions": [
            {
                key: value
                for key, value in action.items()
                if key not in {"evaluation_run_digest", "evaluation_attempt_id", "episode"}
            }
            for action in actions
        ],
        "predictions": [prediction.get("action_chunk") for prediction in predictions],
    }
    return {
        "task": task,
        "outcome": row["outcome"],
        "policy": row["policy"],
        "effective_seed": seed,
        "seed_source": "original_manifest.protocol.seed" if "seed" in protocol else "UNKNOWN",
        "sampling_protocol": "legacy_task_stream",
        "source_root": identity["root_sha"],
        "source_child": identity["child_sha"],
        "runtime_digest": runtime["digest"],
        "source_episode": episode,
        "source_index": episode,
        "sort_key": [int(_ATTEMPT.fullmatch(attempt_dir.name)[1]), episode],
        "source_ref": {
            "path": str(path),
            "run_dir": str(attempt_dir.parent.parent),
            "original_digest": digest,
            "attempt": attempt_dir.name,
            "attempt_id": attempt_id,
            "source_episode": episode,
            "hashes": hashes,
        },
        "media_coverage": coverage,
        "semantic_digest": hashlib.sha256(_canonical(semantic)).hexdigest(),
        "original_task_status": marker["status"],
    }


def _validated_complete_source(attempt_dir, *, manifest, sim_python, requested_media):
    """A v1 COMPLETE claim must pass its original whole-Task contract, never salvage."""
    identity, protocol = _manifest(manifest)
    marker = _marker(attempt_dir, manifest["digest"])
    if marker["status"] != "COMPLETE":
        return None
    if requested_media is not None:
        _policy(requested_media)
    policy = _policy(protocol)
    try:
        validate_attempt(
            attempt_dir,
            digest=manifest["digest"],
            expected_trials=protocol.get("trials"),
            runtime_digest=identity["evaluation_runtime"]["digest"],
            video_mode=policy["save_generated_video"],
            rollout_enabled=policy["save_rollout_mp4"],
            init_png_enabled=policy["save_init_png"],
            sim_python=sim_python,
        )
        # Buffer every Episode before publishing any from this COMPLETE source.
        # The core also checks horizon/Local acknowledgement consistency; failure
        # of a later Episode must not leave earlier ones silently salvaged.
        return [
            _verify_legacy_episode_core(
                attempt_dir, episode, manifest=manifest, sim_python=sim_python, requested_media=requested_media
            )
            for episode in range(protocol["trials"])
        ]
    except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
        raise EpisodeEvidenceError(
            "CORRUPT_LEGACY_COMPLETE_MARKER",
            f"original COMPLETE claim is inconsistent with its own {protocol.get('trials')!r}-episode contract: {error}",
        ) from error


def verify_legacy_episode(attempt_dir, episode, *, manifest, sim_python, requested_media=None):
    """Read one Episode; a COMPLETE Task first requires full original validation."""
    attempt_dir = _safe(Path(attempt_dir))
    complete = _validated_complete_source(
        attempt_dir, manifest=manifest, sim_python=sim_python, requested_media=requested_media
    )
    if complete is not None:
        if type(episode) is not int or not 0 <= episode < len(complete):
            _fail("INVALID_EPISODE", "source episode index is outside the original complete task")
        return complete[episode]
    return _verify_legacy_episode_core(
        attempt_dir, episode, manifest=manifest, sim_python=sim_python, requested_media=requested_media
    )


def scan_legacy_run(run_dir, *, sim_python, tasks=None, requested_media=None):
    """Return verified records plus explicit exclusions, without changing a byte."""
    run_dir = _safe(Path(run_dir))
    manifest = _json(run_dir / "evaluation_manifest.json", unique_keys=True)
    identity, _ = _manifest(manifest)
    known = {
        value["task"]
        for value in identity.get("tasks", [])
        if isinstance(value, dict) and isinstance(value.get("task"), str)
    }
    if isinstance(tasks, str):
        _fail("INVALID_TASK_FILTER", "task filter must be a collection, not a task-name string")
    requested_tasks = known if tasks is None else set(tasks)
    if any(not isinstance(task, str) or not task.isidentifier() or task == "all" for task in requested_tasks):
        _fail("INVALID_TASK_FILTER", "unsafe task filter")
    selected = sorted(requested_tasks & known)
    records, diagnostics, chosen = (
        [],
        [
            dict(
                code="NO_LEGACY_TASK_SOURCE",
                task=task,
                message="current task has no source in this original manifest; schedule it as new",
            )
            for task in sorted(requested_tasks - known)
        ],
        {},
    )
    for task in selected:
        task_dir = _safe(run_dir / task)
        if not task_dir.exists():
            continue
        attempts = []
        for path in task_dir.iterdir():
            _safe(path)
            match = _ATTEMPT.fullmatch(path.name)
            if not path.is_dir() or match is None:
                diagnostics.append(
                    dict(
                        code="UNKNOWN_ATTEMPT_ENTRY",
                        task=task,
                        path=str(path),
                        message="unrecognized entry not imported",
                    )
                )
                continue
            attempts.append((int(match[1]), path))
        ranks = [rank for rank, _ in attempts]
        for rank, attempt in sorted(attempts):
            if ranks.count(rank) != 1:
                diagnostics.append(
                    dict(
                        code="AMBIGUOUS_ATTEMPT_INDEX",
                        task=task,
                        path=str(attempt),
                        message="multiple original directories claim the same numeric attempt index; neither source is imported",
                    )
                )
                continue
            try:
                complete_records = _validated_complete_source(
                    attempt, manifest=manifest, sim_python=sim_python, requested_media=requested_media
                )
                completed, unfinished = _completed_progress(
                    attempt, digest=manifest["digest"], attempt_id=f"{task}/{attempt.name}"
                )
            except (OSError, ValueError, TypeError) as error:
                diagnostics.append(
                    dict(
                        code=getattr(error, "code", "CORRUPT_ATTEMPT_EVIDENCE"),
                        task=task,
                        attempt=attempt.name,
                        path=str(attempt),
                        message=str(error),
                    )
                )
                continue
            candidates = (
                set(range(len(complete_records)))
                if complete_records is not None
                else {int(match[1]) for path in attempt.iterdir() if (match := _ARTIFACT.fullmatch(path.name))}
                | completed
            )
            if unfinished:
                candidates.add(len(completed))
                diagnostics.append(
                    dict(
                        code="PARTIAL_PROGRESS_TAIL",
                        task=task,
                        attempt=attempt.name,
                        path=str(attempt / "episode_progress.jsonl"),
                        message="unfinished final progress event excluded; earlier complete ordered pairs remain candidates",
                    )
                )
            for episode in sorted(candidates):
                path = attempt / f"rollout{episode:02d}_episode.json"
                try:
                    record = (
                        complete_records[episode]
                        if complete_records is not None
                        else _verify_legacy_episode_core(
                            attempt, episode, manifest=manifest, sim_python=sim_python, requested_media=requested_media
                        )
                    )
                except (OSError, ValueError, TypeError, KeyError, IndexError) as error:
                    diagnostics.append(
                        dict(
                            code=getattr(error, "code", "CORRUPT_EPISODE_EVIDENCE"),
                            task=task,
                            attempt=attempt.name,
                            episode=episode,
                            path=str(path),
                            message=str(error),
                        )
                    )
                    continue
                key = (task, record["effective_seed"], episode)
                if key in chosen:
                    original = chosen[key]
                    code = (
                        "DUPLICATE_EXCLUDED"
                        if original["semantic_digest"] == record["semantic_digest"]
                        else "DUPLICATE_CONFLICT_EXCLUDED"
                    )
                    diagnostics.append(
                        dict(
                            code=code,
                            task=task,
                            episode=episode,
                            chosen=original["source_ref"],
                            excluded=record["source_ref"],
                            message="oldest numeric valid attempt wins; outcomes never determine priority",
                        )
                    )
                    continue
                chosen[key] = record
                records.append(record)
    return {
        "schema": "psm_episode_legacy_scan_prototype_v1",
        "records": records,
        "diagnostics": diagnostics,
        "original_manifest": manifest,
    }
