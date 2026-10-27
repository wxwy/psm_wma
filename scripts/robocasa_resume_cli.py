"""Current-plan admission and views for the manual RoboCasa evaluation launcher."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import subprocess
import threading
import time
import uuid
from pathlib import Path

from robocasa_episode_resume import MAX_RECOVERY_BYTES, bounded_episode_count, bounded_episode_index
from robocasa_episode_resume.model_identity import build_model_identity, verify_model_observation
from robocasa_episode_resume.plan import build_plan, build_report, render_plan, source_key
from robocasa_eval_results import _unique_object
from robocasa_input_verification import InvocationInputGuard, snapshot_inputs
from robocasa_resume_execution import execute_planned_batches
from robocasa_resume_store import RunStore


def _protocol(args, gpus):
    return {
        "seed": args.seed,
        "R": args.action_horizon,
        "H_pred": 16,
        "server_action_chunk_size": 16,
        "raw_action_dim": 15,
        "max_action_dim": 64,
        "policy_seed": 0,
        "num_steps": args.num_steps,
        "guidance": args.guidance,
        "trials": args.num_test_episodes,
        "fps": 20,
        "camera_set": "left_wrist",
        "use_state": True,
        "base_encoding": "raw",
        "local_memory_mode": "required",
        "image_size": 256,
        "cam_size": 256,
        "success_latch": 1,
        "manual_schema": "psm_wma_robocasa_eval_v1",
        "gpu_ids": gpus,
        "slots_per_gpu": 1,
        "base_port": args.base_port,
        "server_python": str(args.server_python),
        "save_rollout_mp4": args.save_rollout_mp4,
        "save_generated_video": args.save_generated_video,
        "save_init_png": args.save_init_png,
        "save_action_jsonl": True,
        "save_prediction_jsonl": True,
        "server_lifecycle": args.server_lifecycle,
        "on_infrastructure_error": args.on_infrastructure_error,
        "timeouts": {
            "server_start_s": args.server_start_timeout_s,
            "predict_request_s": args.predict_request_timeout_s,
            "episode_wall_s": args.episode_wall_timeout_s,
            "task_wall_s": args.task_wall_timeout_s,
            "terminate_grace_s": args.terminate_grace_s,
        },
    }


def _media(args):
    return {name: getattr(args, name) for name in ("save_rollout_mp4", "save_generated_video", "save_init_png")}


def _provenance(manifest):
    identity = manifest["identity"]
    return {
        "source_root": identity["root_sha"],
        "source_child": identity["child_sha"],
        "runtime_digest": identity["evaluation_runtime"]["digest"],
        "config_sha256": identity["config_sha256"],
        "task_metadata_by_task": {row["task"]: row["env_metadata_sha256"] for row in identity["tasks"]},
    }


def _view_provenance(queue_api):
    """Record the current view producer without pretending a runtime was executed."""
    result = {"runtime_digest": None, "runtime_probed": False}
    for name, directory in (("source_root", queue_api.ROOT), ("source_child", queue_api.CHILD)):
        try:
            result[name] = subprocess.check_output(
                ["git", "-C", str(directory), "rev-parse", "HEAD"], text=True
            ).strip()
        except (OSError, subprocess.CalledProcessError):
            result[name] = None
    return result


def _summary(
    plan, executed, errors, *, args, checkpoint, config_file, invocation, execution_result=None, running=False
):
    report = build_report(plan, executed, invocation_errors=errors)
    if running:
        # Coverage and absence of infrastructure errors are separate facts.
        report.update(status="RUNNING", sr=None, exit_code=None)
    report.update(
        checkpoint=str(checkpoint),
        config_file=str(config_file),
        action_horizon=args.action_horizon,
        expected_tasks=len(plan["selected_tasks"]),
        invocation_dir=str(invocation),
        total_trials=report["completed"],
        total_successes=sum(row["successes"] for row in report["tasks"].values()),
        completed_tasks=sum(row["remaining"] == 0 for row in report["tasks"].values()),
        task_failures=len(
            {
                row.get("task")
                for row in errors
                if row.get("task") in report["tasks"] and row.get("stage") != "not_executed"
            }
        ),
        worker_errors={f"_worker_{index}": row for index, row in enumerate(errors)},
        job_results=(execution_result or {}).get("jobs", []),
    )
    all_media = {"rollout_mp4s": [], "generated_mp4s": []}
    for task, row in report["tasks"].items():
        sources = row["episode_sources"]
        row.update(
            trials=row["completed"],
            rollouts=sources,
            source_results_files=sorted(
                {str(Path(ref["source_ref"]["path"]).parent / "results.json") for ref in sources}
            ),
            error="; ".join(item["error"] for item in errors if item.get("task") == task) or None,
        )
        row["rollout_mp4s"], row["generated_mp4s"] = [], []
        for source in sources:
            available = source.get("media_coverage", {}).get("videos_view", {})
            if available.get("rollout"):
                paths = available["rollout"]
                row["rollout_mp4s"].extend([paths] if isinstance(paths, str) else paths)
            row["generated_mp4s"].extend(available.get("generated", []))
        for kind in all_media:
            all_media[kind].extend(row[kind])
    report.update({kind: sorted(set(paths)) for kind, paths in all_media.items()})
    return report


def _progress_starts(job):
    """Read terminal C01 authority atomically, bounded by bytes/rows/episodes.

    A corrupt source contributes no speculative starts, even if an earlier row
    was valid. Original evidence remains available to the source verifier.
    """
    path = job["attempt_dir"] / "episode_progress.jsonl"
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError("CORRUPT_PROGRESS: symlink")
    try:
        before = path.stat()
    except FileNotFoundError:
        return []  # A worker can fail before the simulator creates progress.
    if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_RECOVERY_BYTES:
        raise ValueError("CORRUPT_PROGRESS: nonregular or oversized file")
    count = bounded_episode_count(len(job["episodes"]), "reserved episodes")
    physical = [row["source_episode"] for row in job["episodes"]]
    for row in job["episodes"]:
        bounded_episode_index(row["logical_episode_index"], "reserved logical episode")
    if physical != list(range(count)):
        raise ValueError("CORRUPT_PROGRESS: invalid reserved physical mapping")
    started, rows, size = [], 0, 0

    def invalid(value):
        raise ValueError(f"CORRUPT_PROGRESS: nonfinite JSON {value}")

    with path.open("rb") as stream:
        while line := stream.readline(4097):
            size += len(line)
            if size > MAX_RECOVERY_BYTES or rows >= 2 * count:
                raise ValueError("CORRUPT_PROGRESS: byte/row limit exceeded")
            if len(line) > 4096 or not line.endswith(b"\n"):
                raise ValueError("CORRUPT_PROGRESS: oversized/truncated event")
            event = json.loads(line.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=invalid)
            if (
                not isinstance(event, dict)
                or event.get("schema") != "psm_episode_progress_v1"
                or event.get("evaluation_run_digest") != job["source_manifest"]["digest"]
                or event.get("evaluation_attempt_id") != f"{job['task']}/{job['attempt_dir'].name}"
                or type(event.get("episode")) is not int
                or event["episode"] != rows // 2
                or event.get("event") != ("end" if rows % 2 else "start")
            ):
                raise ValueError("CORRUPT_PROGRESS: identity/order mismatch")
            if rows % 2 == 0:
                started.append(rows // 2)
            rows += 1
        after = os.fstat(stream.fileno())

    def witness(item):
        return (item.st_dev, item.st_ino, item.st_size, item.st_mtime_ns, item.st_ctime_ns)

    if witness(before) != witness(after) or witness(after) != witness(path.stat()):
        raise ValueError("CORRUPT_PROGRESS: source changed during terminal read")
    return started


def _unfinished_executions(jobs, completed, *, errors):
    """Count only committed, ordered starts; persist per-source read failures."""
    closed = {(row["task"], row["logical_episode_index"]) for row in completed}
    failed = []
    for job in jobs:
        try:
            started = _progress_starts(job)
        except (OSError, ValueError, RecursionError) as error:
            errors.append(
                {
                    "stage": "final_progress_read",
                    "task": job["task"],
                    "path": str(job["attempt_dir"] / "episode_progress.jsonl"),
                    "error": f"{type(error).__name__}: {error}",
                }
            )
            continue
        physical = {row["source_episode"]: row for row in job["episodes"]}
        for index in started:
            slot = physical[index]["logical_episode_index"]
            if (job["task"], slot) not in closed:
                failed.append(
                    {
                        "task": job["task"],
                        "logical_episode_index": slot,
                        "effective_seed": job["seed"],
                        "verified": False,
                        "outcome": "runtime_error",
                        "error": "Episode started without valid complete evidence",
                    }
                )
    return failed


def _revalidate_selected_sources(plan, final_records, errors):
    """A reused source invalidated during execution cannot remain in the final view."""
    current = {source_key(row): row for row in final_records}
    mutable = {"attempt.json", "episode_progress.jsonl", "results.json", "process_cleanup.json"}
    result = copy.deepcopy(plan)
    for task, info in result["tasks"].items():
        valid = []
        for row in info["reused_sources"]:
            fresh = current.get(source_key(row))
            old_core = {name: value for name, value in row["source_ref"]["hashes"].items() if name not in mutable}
            new_core = {
                name: value
                for name, value in (fresh or {}).get("source_ref", {}).get("hashes", {}).items()
                if name not in mutable
            }
            if fresh is None or old_core != new_core:
                errors.append(
                    {
                        "task": task,
                        "stage": "final_source_verification",
                        "error": "SOURCE_EVIDENCE_CHANGED",
                        "source_ref": row["source_ref"],
                    }
                )
            else:
                valid.append(fresh)
        info["reused_sources"], info["reused"] = valid, len(valid)
    return result


def _view_export(queue_api, output_root, source_roots):
    """Each source retains its digest; browsing copies cannot change evaluation status."""
    for source_root in sorted(set(map(Path, source_roots))):
        try:
            view = None
            if source_root != output_root:
                source_id = hashlib.sha256(str(source_root).encode()).hexdigest()[:16]
                view = output_root / "videos_view" / "sources" / source_id
            exported = queue_api.export_videos(source_root, view_dir=view)
            print(f"video browsing export: status={exported['status']} index={exported['index_file']}", flush=True)
        except Exception as error:
            try:
                print(f"video browsing export unavailable: {type(error).__name__}: {error}", flush=True)
            except Exception:
                pass


def prepare_resume(args, cache, *, queue_api):
    """Default production admission: model identity and one shared lock before writes."""
    discovered = queue_api.discover_task_datasets(args.dataset_root.resolve(), None)
    mapping = dict(discovered)
    if args.list_tasks:
        print(json.dumps({"tasks": sorted(mapping)}, ensure_ascii=False, indent=2))
        return 0
    if args.tasks == "all":
        tasks = queue_api.discover_task_datasets(args.dataset_root.resolve(), args.expected_tasks)
    else:
        missing = sorted(set(args.tasks) - mapping.keys())
        if missing:
            raise ValueError(f"unknown underlying RoboCasa tasks: {missing}")
        tasks = [(name, mapping[name]) for name in sorted(args.tasks)]
    checkpoint, config_file = args.checkpoint_path.resolve(), args.config_file.absolute()
    output_root, gpus = args.output_dir.absolute(), args.gpus.split(",")
    destination = Path(os.path.abspath(output_root))
    for protected in (checkpoint, config_file.resolve(), args.dataset_root.resolve()):
        if destination == protected or destination.is_relative_to(protected) or protected.is_relative_to(destination):
            raise ValueError(f"evaluation output overlaps a read-only input: {protected}")

    def read_model():
        return build_model_identity(
            checkpoint=checkpoint, num_steps=args.num_steps, action_horizon=args.action_horizon, guidance=args.guidance
        )

    store = RunStore(
        output_root,
        current_identity_reader=read_model,
        resume=args.resume,
        allow_relocated_legacy_checkpoint=args.allow_relocated_legacy_checkpoint,
        model_identity_request=dict(
            checkpoint=checkpoint, num_steps=args.num_steps, action_horizon=args.action_horizon, guidance=args.guidance
        ),
    )
    output_root = store.root
    simulation_env = queue_api.launch_environment(cache)
    invocation_id = f"{time.time_ns()}_{os.getpid()}_{uuid.uuid4().hex[:8]}"

    def admitted(*, readonly):
        for index, telemetry in enumerate(store.verification_events, 1):
            print(f"model input verification {index}: {json.dumps(telemetry, sort_keys=True)}", flush=True)
        history = store.discover_history(sim_python=args.sim_python, requested_media=_media(args))
        provenance = _view_provenance(queue_api)

        def make_plan():
            return build_plan(
                history["records"],
                tasks=[name for name, _ in tasks],
                requested_episodes=args.num_test_episodes,
                requested_seed=args.seed,
                requested_media=_media(args),
                execution={"gpus": gpus, "base_port": args.base_port, "timeouts": _protocol(args, gpus)["timeouts"]},
                current_provenance=provenance,
                invocation_id=invocation_id,
                recovery_documents=history["recovery_documents"],
                recovery_observations=history.get("recovery_observations", ()),
                scan_diagnostics=history["diagnostics"],
            )

        plan = make_plan()
        bundle = None
        input_guard = None
        if any(row["new"] for row in plan["tasks"].values()):
            if not config_file.is_file():
                raise ValueError(f"config file missing: {config_file}")
            before_inputs = snapshot_inputs(config_file, tasks)
            bundle = queue_api.build_verified_evaluation_identity(
                sim_python=args.sim_python,
                lock_path=args.vendor_lock,
                asset_manifest=args.asset_manifest,
                simulation_env=simulation_env,
                root=queue_api.ROOT,
                checkpoint=checkpoint,
                config_file=config_file,
                tasks=tasks,
                protocol=_protocol(args, gpus),
                verified_model_identity=store.current_identity,
            )
            input_guard = InvocationInputGuard(config_file, bundle["manifest"], before_inputs)
            provenance.update(_provenance(bundle["manifest"]))
            provenance["runtime_probed"] = True
            plan = make_plan()
        store.current_provenance = copy.deepcopy(provenance)
        plan["view_producer"] = copy.deepcopy(provenance)
        plan["checkpoint_reads"] = copy.deepcopy(store.verification_events)
        print(render_plan(plan), flush=True)
        if readonly:
            preview = {
                "mode": "CPU_READ_ONLY_PREVIEW",
                "resolved_config": args.resolved_config,
                "output_dir": str(output_root),
                "resume_plan": plan,
                "model_identity": store.current_identity,
                "manifest": bundle["manifest"] if bundle else None,
                "commands": [],
            }
            if bundle:
                for task, info in plan["tasks"].items():
                    for batch in info["execution_batches"]:
                        batch_args = copy.copy(args)
                        batch_args.seed, batch_args.num_test_episodes = batch["effective_seed"], len(batch["episodes"])
                        preview["commands"].append(
                            {
                                "task": task,
                                "sampling_mode": info["sampling_mode"],
                                "server": queue_api.server_argv(batch_args, checkpoint, config_file, args.base_port),
                                "simulator": queue_api.simulator_argv(
                                    batch_args,
                                    mapping[task],
                                    output_root / "_invocations" / invocation_id / "unreserved" / task / "attempt_0001",
                                    args.base_port,
                                    "NOT_RESERVED_DRY_RUN",
                                    bundle["manifest"]["identity"]["evaluation_runtime"]["digest"],
                                    [name for name, _ in tasks],
                                ),
                            }
                        )
            print(json.dumps(preview, ensure_ascii=False, indent=2))
            return 0
        if bundle:
            queue_api.require_free_ports([args.base_port + index for index in range(len(gpus))])
        invocation = store.begin_invocation(
            plan, args.resolved_config, initial_manifest=bundle["manifest"] if bundle else None
        )
        if bundle:
            queue_api.atomic_write_json(invocation / "runtime_probe.json", bundle["runtime_probe_evidence"])
        jobs = []
        if bundle:
            for task, info in plan["tasks"].items():
                for batch in info["execution_batches"]:
                    source = copy.deepcopy(bundle["manifest"])
                    source["identity"]["config_file"] = str(config_file)
                    source["identity"]["protocol"].update(seed=batch["effective_seed"], trials=len(batch["episodes"]))
                    descriptor = {
                        **batch,
                        "task": task,
                        "dataset_dir": str(mapping[task]),
                        "seed": batch["effective_seed"],
                        "num_test_episodes": len(batch["episodes"]),
                        "sampling_mode": info["sampling_mode"],
                        "requested_seed": args.seed,
                        "sampler": {
                            "requested_seed": args.seed,
                            "sampling_mode": info["sampling_mode"],
                            "sampler_version": info["new_episodes"][0]["seed_family"]["sampler_version"],
                        },
                        "planned_episodes": [
                            row for row in info["new_episodes"] if row["execution_batch"] == batch["batch_index"]
                        ],
                    }
                    jobs.append(store.reserve_batch(invocation, descriptor, source))
        executed, state_lock = [], threading.Lock()

        def publish_running(job=None):
            records = (
                store.read_reserved_batch(
                    job,
                    sim_python=args.sim_python,
                    requested_media=_media(args),
                    deadline=job.get("validation_deadline"),
                    stop=job.get("validation_stop"),
                )["records"]
                if job
                else []
            )
            with state_lock:
                executed.extend(records)
                report = _summary(
                    plan,
                    executed,
                    [],
                    args=args,
                    checkpoint=checkpoint,
                    config_file=config_file,
                    invocation=invocation,
                    running=True,
                )
                store.write_report(invocation, report)

        publish_running()

        def verify_inputs(job, phase):
            verify_model_observation(store.current_identity)
            input_guard.verify(job["source_manifest"], phase)

        result = execute_planned_batches(
            args=args,
            checkpoint=checkpoint,
            config_file=config_file,
            jobs=jobs,
            gpus=gpus,
            output_root=invocation,
            simulation_env=simulation_env,
            queue_api=queue_api,
            verify_inputs=verify_inputs,
            on_completed=publish_running,
        )
        final_errors = list(result["errors"])
        try:
            final_history = store.discover_history(sim_python=args.sim_python, requested_media=_media(args))
        except Exception as error:
            final_errors.append({"stage": "final_source_revalidation", "error": f"{type(error).__name__}: {error}"})
            final_history = {"records": [], "diagnostics": [], "source_manifests": []}
        new_sources = [
            row for row in final_history["records"] if Path(row["source_ref"]["path"]).is_relative_to(invocation)
        ]
        try:
            verify_model_observation(store.current_identity)
            if input_guard is not None:
                input_guard.verify(bundle["manifest"], "final_input_verification")
        except Exception as error:
            final_errors.append({"stage": "final_input_verification", "error": f"{type(error).__name__}: {error}"})
        final_plan = _revalidate_selected_sources(plan, final_history["records"], final_errors)
        unfinished = _unfinished_executions(jobs, new_sources, errors=final_errors)
        report = _summary(
            final_plan,
            new_sources + unfinished,
            final_errors,
            args=args,
            checkpoint=checkpoint,
            config_file=config_file,
            invocation=invocation,
            execution_result=result,
        )
        report["diagnostics"].extend(row for row in final_history["diagnostics"] if row not in report["diagnostics"])
        report["checkpoint_reads"] = copy.deepcopy(store.verification_events)
        report["invocation_input_verification"] = {
            "subsequent_guard_checks": input_guard.checks if input_guard else 0,
            "subsequent_bytes_read": 0,
            "initial_full_config_task_verification": bundle is not None,
        }
        diagnostic_media = {"rollout_mp4s": [], "generated_mp4s": []}
        for job in jobs:
            for kind, paths in queue_api.task_video_files(job["attempt_dir"]).items():
                diagnostic_media[kind].extend(paths)
        report.update({f"diagnostic_{kind}": sorted(set(paths)) for kind, paths in diagnostic_media.items()})
        store.publish_catalog(final_history["records"])
        summary_path = store.write_report(invocation, report)
        print(
            f"RESUME RESULT reused={report['reused']} executed={report['executed']} excluded={report['excluded']} "
            f"remaining={report['remaining']} actual_seeds={report['actual_conditions']['effective_seeds']} "
            f"flags={report['actual_conditions']['flags']} status={report['status']}; summary={summary_path}",
            flush=True,
        )
        _view_export(
            queue_api, output_root, [output_root, *(Path(path).parent for path in final_history["source_manifests"])]
        )
        return report["exit_code"]

    if args.dry_run:
        store.preview()
        return admitted(readonly=True)
    with store.locked():
        return admitted(readonly=False)
