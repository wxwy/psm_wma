"""Pure current-plan and Episode views; no model launch or evidence mutation."""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import stat
from pathlib import Path

from . import MAX_EPISODES, bounded_episode_count, bounded_episode_index, bounded_records
from .model_identity import compare_model_identity
from .reservation_recovery import (
    read_recovery_document,
    recover_pending_slots,
)
from .scene_sampling import plan_scene_sampling


def source_key(record):
    reference = record["source_ref"]
    locator = {
        "task": record["task"],
        "original_digest": reference["original_digest"],
        "attempt": reference["attempt"],
        "source_episode": reference["source_episode"],
    }
    return hashlib.sha256(json.dumps(locator, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def _core_snapshot(record):
    mutable = {"attempt.json", "episode_progress.jsonl", "results.json", "process_cleanup.json"}
    return {key: value for key, value in record["source_ref"]["hashes"].items() if key not in mutable}


def _priority(record):
    attempt = record["source_ref"]["attempt"]
    numeric = re.fullmatch(r"attempt_(\d+)", attempt)
    return record["task"], int(numeric[1]) if numeric else 2**63, str(attempt), record["source_episode"]


def _coverage(record, requested):
    coverage = copy.deepcopy(record.get("media_coverage", {}))
    mode = requested["save_generated_video"]
    if mode not in {"none", "first", "all"}:
        raise ValueError("invalid current generated media policy")
    required_generated = 0 if mode == "none" else 1 if mode == "first" else coverage.get("prediction_count")
    missing = []
    if requested["save_rollout_mp4"] and coverage.get("available_rollout") is not True:
        missing.append("rollout_mp4")
    if requested["save_init_png"] and coverage.get("available_init_png") is not True:
        missing.append("init_png")
    if required_generated is None:
        missing.append("generated_coverage_unknown")
    elif coverage.get("available_generated", 0) < required_generated:
        missing.append("generated_mp4")
    coverage.update(requested_policy=copy.deepcopy(requested), missing_requested_media=missing)
    return coverage


def _complete(record):
    return (
        record.get("verified") is True
        and record.get("outcome") in {"success", "behavioral_failure"}
        and type(record.get("policy")) is bool
        and (record["outcome"] == "success") == record["policy"]
        and record.get("error") is None
    )


def verified_scan_records(scan):
    """Trust-boundary adapter: only the scanner may produce input history records."""
    identity = scan.get("original_manifest", {}).get("identity", {})
    metadata = {row["task"]: row.get("env_metadata_sha256") for row in identity.get("tasks", [])}
    return [
        dict(
            copy.deepcopy(record),
            verified=True,
            logical_episode_index=record["source_episode"],
            config_sha256=identity.get("config_sha256"),
            task_metadata_sha256=metadata.get(record["task"]),
        )
        for record in scan["records"]
    ]


def _conditions(records):
    flags = []
    seeds = {record.get("effective_seed") for record in records}
    families = {record.get("requested_seed", record.get("effective_seed")) for record in records}
    runtimes = {record.get("runtime_digest") for record in records}
    sampling = {record.get("sampling_protocol") for record in records}
    sources = {(record.get("source_root"), record.get("source_child")) for record in records}
    configs = {record.get("config_sha256") for record in records}
    task_metadata = {}
    for record in records:
        task_metadata.setdefault(record["task"], set()).add(record.get("task_metadata_sha256"))
    if len(families - {None}) > 1:
        flags.append("MIXED_SEED")
    if len(seeds - {None}) > 1:
        flags.append("MULTIPLE_EFFECTIVE_ENV_SEEDS")
    if None in seeds or None in families:
        flags.append("UNKNOWN_SEED")
    if len(runtimes - {None}) > 1:
        flags.append("MIXED_RUNTIME")
    if None in runtimes:
        flags.append("UNKNOWN_RUNTIME")
    if len(sampling) > 1:
        flags.append("MIXED_SAMPLING_PROTOCOL")
    if len(sources) > 1:
        flags.append("MIXED_SOURCE_PROVENANCE")
    if len(configs - {None}) > 1:
        flags.append("MIXED_CONFIG")
    if None in configs:
        flags.append("UNKNOWN_CONFIG")
    if any(len(values - {None}) > 1 for values in task_metadata.values()):
        flags.append("MIXED_TASK_METADATA")
    if any(None in values for values in task_metadata.values()):
        flags.append("UNKNOWN_TASK_METADATA")
    return {
        "effective_seeds": sorted(seeds - {None}),
        "requested_seed_families": sorted(families - {None}),
        "runtime_digests": sorted(runtimes - {None}),
        "flags": flags,
        "benchmark_qualification": (
            "CONVENIENCE_AGGREGATE_NOT_SINGLE_CONDITION_BENCHMARK" if flags else "SOURCE_CONDITIONS_RECORDED"
        ),
    }


def build_plan(
    records,
    *,
    tasks,
    requested_episodes,
    requested_seed,
    requested_media,
    execution,
    current_provenance,
    invocation_id,
    pending_slots=None,
    recovery_documents=(),
    recovery_observations=(),
    scan_diagnostics=(),
):
    if (
        not tasks
        or len(tasks) != len(set(tasks))
        or any(not isinstance(task, str) or not task.isidentifier() for task in tasks)
        or type(requested_episodes) is not int
        or requested_episodes <= 0
        or type(requested_seed) is not int
        or requested_seed < 0
    ):
        raise ValueError("invalid current invocation plan")
    bounded_episode_count(requested_episodes, "requested_episodes")
    bounded_episode_count(len(tasks) * requested_episodes, "total requested Episodes")
    original = copy.deepcopy(bounded_records(records))
    reservations, progress = [], []
    for path in bounded_records(recovery_documents, "recovery documents"):
        document = read_recovery_document(path)
        for target, name in ((reservations, "reservations"), (progress, "progress_diagnostics")):
            values = document.get(name, [])
            if len(target) + len(values) > MAX_EPISODES:
                raise ValueError(f"combined {name} exceed the {MAX_EPISODES}-record resource bound")
            target.extend(values)
    # Store projects these rows from the original manifest and valid C01 bytes.
    # They reserve logical slots only; completed outcomes still require the
    # upstream Episode scanner. A bare in-memory slot hint is not authority.
    observations = copy.deepcopy(bounded_records(recovery_observations, "recovery observations"))
    if len(reservations) + len(observations) > MAX_EPISODES:
        raise ValueError(f"combined reservations exceed the {MAX_EPISODES}-record resource bound")
    for row in observations:
        reference = row.get("source_ref", {}) if isinstance(row, dict) else {}
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("task"), str)
            or not row["task"].isidentifier()
            or not isinstance(reference, dict)
            or not isinstance(reference.get("path"), str)
            or not Path(reference["path"]).is_absolute()
            or not isinstance(reference.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]) is None
        ):
            raise ValueError("recovery observations require a Task and actual persistent path/SHA256 witness")
    reservations.extend(observations)
    rows, observed, logical_slots, diagnostics = [], {}, {}, list(copy.deepcopy(scan_diagnostics))
    original.sort(key=_priority)
    for record in original:
        if record["task"] not in tasks:
            continue
        if not _complete(record):
            diagnostics.append({"code": "UNVERIFIED_OR_UNFINISHED_EXCLUDED", "task": record["task"]})
            continue
        key = source_key(record)
        if key in observed:
            if _core_snapshot(record) != _core_snapshot(observed[key]):
                raise ValueError(f"SOURCE_EVIDENCE_CHANGED: {key}")
            diagnostics.append({"code": "REPEATED_SOURCE_REFERENCE_EXCLUDED", "source_key": key})
            continue
        observed[key] = record
        if record.get("sampling_protocol") == "legacy_task_stream":
            record.setdefault("logical_episode_index", record["source_episode"])
        if "logical_episode_index" in record:
            bounded_episode_index(record["logical_episode_index"])
            slot = (record["task"], record["logical_episode_index"])
            if slot in logical_slots:
                diagnostics.append(
                    {"code": "LOGICAL_SLOT_DUPLICATE_EXCLUDED", "chosen": logical_slots[slot], "excluded": key}
                )
                continue
            logical_slots[slot] = key
        record["media_coverage"] = _coverage(record, requested_media)
        rows.append(record)
    plan = {
        "schema": "psm_episode_resume_plan_v1",
        "invocation_id": invocation_id,
        "requested_seed": requested_seed,
        "requested_episodes_per_task": requested_episodes,
        "selected_tasks": sorted(tasks),
        "requested_media": copy.deepcopy(requested_media),
        "execution": copy.deepcopy(execution),
        "tasks": {},
        "diagnostics": diagnostics,
        "warnings": [],
        "production_wired": True,
    }
    planned_sources = []
    for task in sorted(tasks):
        history = sorted(
            (row for row in rows if row["task"] == task),
            key=lambda row: (
                row.get("logical_episode_index", row["source_episode"]),
                str(row["source_ref"]["original_digest"]),
                str(row["source_ref"]["attempt"]),
            ),
        )
        selected = history[:requested_episodes]
        # Catalog IDs are never reassigned to another completed source. The
        # requested view's dense ordinal is separate from original physical ep.
        recovery = recover_pending_slots(
            task=task,
            completed_slots=history,
            reservations=reservations,
            progress_diagnostics=progress,
            requested_episodes=requested_episodes,
        )
        # Optional old API hints cannot invent a slot without durable authority.
        hints = (pending_slots or {}).get(task, [])
        for slot in bounded_records(hints, "pending logical slots"):
            bounded_episode_index(slot)
        if not set(hints).issubset(recovery["pending_slots"]):
            raise ValueError("UNPERSISTED_PENDING_HINT: pending slots require persistent recovery authority")
        pending = recovery["pending_slots"]
        next_slot = recovery["next_slot_floor"]
        new_count = requested_episodes - len(selected)
        sampling_mode = "resume_gap_independent" if history else "fresh_task_stream"
        if history:
            new_slots = pending[:new_count]
            if next_slot + new_count - len(new_slots) > MAX_EPISODES:
                raise ValueError("new logical Episode slots exceed the 100000-slot resource bound")
            new_slots.extend(range(next_slot, next_slot + new_count - len(new_slots)))
        else:
            # With no valid completed prefix the whole Task starts at its
            # original literal seed, including failed/quarantined old sources.
            new_slots = list(range(new_count))
        scene = plan_scene_sampling(
            task=task,
            requested_seed=requested_seed,
            new_logical_indices=new_slots,
            attempt_nonce=invocation_id,
            sampling_mode=sampling_mode,
            legacy_sources=selected,
        )
        planned_new = scene["new_episodes"]
        for row in planned_new:
            row.update(copy.deepcopy(current_provenance), task=task, sampling_protocol=scene["sampler_version"])
            row["task_metadata_sha256"] = current_provenance.get("task_metadata_by_task", {}).get(task)
        plan["tasks"][task] = {
            "requested": requested_episodes,
            "previous_completed": len(history),
            "reused": len(selected),
            "new": new_count,
            "excluded": len(history) - len(selected),
            "reused_sources": selected,
            "excluded_sources": history[requested_episodes:],
            "new_episodes": planned_new,
            "sampling_mode": sampling_mode,
            "execution_batches": scene["execution_batches"],
            "pending_recovery": recovery,
        }
        if new_count:
            plan["warnings"].extend(scene["warnings"])
        planned_sources.extend(selected + planned_new)
    plan["planned_conditions"] = _conditions(planned_sources)
    plan["historical_missing_requested_media"] = sum(
        len(row.get("media_coverage", {}).get("missing_requested_media", []))
        for value in plan["tasks"].values()
        for row in value["reused_sources"]
    )
    if not any(row["new"] for row in plan["tasks"].values()):
        plan["warnings"].append(
            {
                "code": "NO_NEW_EPISODES_AT_REQUESTED_SEED",
                "requested_seed": requested_seed,
                "actual_historical_seeds": plan["planned_conditions"]["effective_seeds"],
            }
        )
    return plan


def build_report(plan, executed, *, invocation_errors=()):
    """Aggregate only the selected, validated source references; never count an error as fail."""
    tasks, all_completed, errors = {}, [], list(copy.deepcopy(invocation_errors))
    planned = {
        (task, row["logical_episode_index"]): row
        for task, value in plan["tasks"].items()
        for row in value["new_episodes"]
    }
    by_slot, failed = {}, {}
    selected_keys = {source_key(row) for value in plan["tasks"].values() for row in value["reused_sources"]}
    for row in copy.deepcopy(executed):
        key = (row["task"], row["logical_episode_index"])
        if key not in planned or key in by_slot or key in failed:
            errors.append({"code": "UNPLANNED_OR_DUPLICATE_EXECUTION", "slot": list(key)})
            continue
        if row.get("effective_seed") != planned[key]["effective_seed"]:
            errors.append({"code": "EXECUTED_SEED_MISMATCH", "slot": list(key)})
            failed[key] = row
        elif _complete(row) and source_key(row) not in selected_keys:
            by_slot[key] = row
            selected_keys.add(source_key(row))
        else:
            failed[key] = row
            errors.append({"code": "EXECUTION_NOT_COMPLETE", "slot": list(key), "error": row.get("error")})
    for task, value in plan["tasks"].items():
        new = [row for (name, _), row in sorted(by_slot.items()) if name == task]
        ordered = sorted(
            value["reused_sources"] + new,
            key=lambda row: row.get("logical_episode_index", row["source_episode"]),
        )
        completed = [dict(copy.deepcopy(row), view_ordinal=index) for index, row in enumerate(ordered)]
        for row in completed:
            row["media_coverage"] = _coverage(row, plan["requested_media"])
        successes = sum(row["policy"] for row in completed)
        tasks[task] = {
            "requested": value["requested"],
            "previous_completed": value["previous_completed"],
            "reused": value["reused"],
            "executed": sum(name == task for name, _ in by_slot) + sum(name == task for name, _ in failed),
            "executed_completed": len(new),
            "excluded": value["excluded"],
            "failed": sum(name == task for name, _ in failed),
            "remaining": value["requested"] - len(completed),
            "successes": successes,
            "completed": len(completed),
            "partial_sr": successes / len(completed) if completed else None,
            "episode_sources": completed,
            "sampling_mode": value["sampling_mode"],
            "pending_recovery": copy.deepcopy(value["pending_recovery"]),
        }
        all_completed.extend(completed)
    requested = sum(row["requested"] for row in tasks.values())
    complete = len(all_completed) == requested and not errors
    for row in tasks.values():
        row["sr"] = row["successes"] / row["requested"] if complete else None
    media_missing = [row.get("media_coverage", {}).get("missing_requested_media", []) for row in all_completed]
    return {
        "schema": "psm_episode_resume_report_v1",
        "status": "COMPLETE" if complete else "PARTIAL",
        "requested_seed": plan["requested_seed"],
        "tasks": tasks,
        "requested": requested,
        "completed": len(all_completed),
        "reused": sum(row["reused"] for row in tasks.values()),
        "executed": sum(row["executed"] for row in tasks.values()),
        "excluded": sum(row["excluded"] for row in tasks.values()),
        "remaining": requested - len(all_completed),
        "failed": sum(row["failed"] for row in tasks.values()),
        "sr": sum(row["policy"] for row in all_completed) / requested if complete else None,
        "partial_sr": sum(row["policy"] for row in all_completed) / len(all_completed) if all_completed else None,
        "actual_conditions": _conditions(all_completed),
        "missing_requested_media": sum(len(missing) for missing in media_missing),
        "episodes_with_requested_media": sum(not missing for missing in media_missing),
        "requested_media_coverage": (
            sum(not missing for missing in media_missing) / len(all_completed) if all_completed else None
        ),
        "warnings": copy.deepcopy(plan["warnings"]),
        "diagnostics": copy.deepcopy(plan["diagnostics"]),
        "invocation_errors": errors,
        "exit_code": 0 if complete else 1,
    }


def render_plan(plan):
    lines = [f"RESUME PLAN requested_seed={plan['requested_seed']} tasks={plan['selected_tasks']}"]
    for task, row in plan["tasks"].items():
        lines.append(
            f"{task} requested={row['requested']} previous_completed={row['previous_completed']} "
            f"reused={row['reused']} new={row['new']} excluded={row['excluded']} "
            f"sampling_mode={row['sampling_mode']} pending={row['pending_recovery']['pending_slots']}"
        )
    lines.append(json.dumps({"conditions": plan["planned_conditions"], "warnings": plan["warnings"]}, sort_keys=True))
    return "\n".join(lines)


def locked_snapshot(run_dir: Path, *, expected_identity, current_identity_reader, snapshot_reader):
    """Read-only locked snapshot: validate identity before and after acquiring the existing lease."""

    def check():
        result = compare_model_identity(expected_identity, current_identity_reader())
        if result["status"] != "MATCH":
            raise ValueError(json.dumps(result, sort_keys=True))

    check()
    lock_path = Path(run_dir) / ".run.lock"
    # Historical current-schema runs already own this persistent file. Creating
    # a lock for older runs is a future migration step, not this read-only proof.
    if any(path.is_symlink() for path in (lock_path, *lock_path.parents)):
        raise ValueError("unsafe run lock path")
    fd = os.open(lock_path, os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "a") as handle:
        if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
            raise ValueError("run lock must be a regular file")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        check()
        return snapshot_reader()
