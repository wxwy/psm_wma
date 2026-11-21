"""Independent Fresh/Resume/Dry-run/explicit Owner release entry."""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
import uuid
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.contract import digest
from cosmos_framework.evaluation.robocasa_v2.scheduler import slot_disposition
from cosmos_framework.evaluation.robocasa_v2.store import (
    Store,
    read,
    save,
    write,
    write_report,
    write_runtime_probe,
)
from robocasa_episode_resume.model_identity import verification_record

from robocasa_eval_v2.config import execution, rendering, resolve
from robocasa_eval_v2.identity import (
    discover,
    g2_experiment,
    prepare,
    runtime_environment,
    verify_f27_resume_source,
    with_runtime_caches,
)
from robocasa_eval_v2.resources import physical_slots, render_slots
from robocasa_eval_v2.runtime import Runtime


def main(argv=None, *, prepare_inputs=prepare, runtime_type=Runtime):
    args, cfg = resolve(argv)
    root = Path(cfg["output_dir"])
    approval_key = None
    if args.f27_resume_approval is not None:
        approval_key = "f27_resume_approval"
    elif args.end_fairness_resume_approval is not None:
        approval_key = "end_fairness_resume_approval"
    approval = read(getattr(args, approval_key)) if approval_key else None
    if approval_key is not None and not isinstance(approval, dict):
        raise ValueError("invalid Run-bound Resume source approval")
    options = {approval_key: approval} if approval_key else {}
    if args.mode == "dry-run":
        tasks = discover(cfg)
        dispositions = []
        end_execution = None
        if (root / "manifest.json").exists():
            manifest = read(root / "manifest.json")
            store = Store(root, manifest)
            if args.f27_resume_approval is not None:
                verify_f27_resume_source(manifest, approval)
            if (
                manifest["task_order"] != [t for t, _ in tasks]
                or manifest["episodes_per_task"] != cfg["episodes_per_task"]
                or manifest.get("execution") != execution(cfg)
                or manifest["experiment"].get("g2") != g2_experiment(cfg)
                or (
                    manifest.get("rendering") is not None
                    and manifest["rendering"] != rendering(cfg)
                )
            ):
                raise ValueError("dry-run scientific plan differs from frozen Run")
            if args.end_fairness_resume_approval is not None:
                anchor = read(root / "_internal/run_inputs.json")
                with tempfile.TemporaryDirectory(
                    prefix="psm-eval-v2-resume-preview-"
                ) as temporary:
                    _, inputs, _ = prepare_inputs(
                        cfg,
                        cache=Path(temporary),
                        anchor=anchor,
                        manifest=manifest,
                        **options,
                    )
                end_execution = inputs["end_fairness_execution"]
            for ep in range(cfg["episodes_per_task"]):
                for task, _ in tasks:
                    action = {
                        "skip_valid_core": "skip_valid",
                        "skip_owner_pending": "skip_owner_pending",
                        "execute": "execute_missing",
                    }[slot_disposition(store, task, ep)]
                    dispositions.append({"task": task, "episode": ep, "action": action})
        elif approval_key is not None:
            raise ValueError("Resume source approval requires an existing Run manifest")
        print(
            json.dumps(
                {
                    "mode": "CPU_PREVIEW_ONLY",
                    "resolved": cfg,
                    "task_order": [t for t, _ in tasks],
                    "physical_slots": physical_slots(cfg, len(tasks)),
                    "physical_slot_capacity": len(physical_slots(cfg, len(tasks))),
                    "executable_slot_capacity": min(
                        len(physical_slots(cfg, len(tasks))),
                        sum(d["action"] == "execute_missing" for d in dispositions)
                        if dispositions
                        else len(tasks) * cfg["episodes_per_task"],
                    ),
                    "render_slots": render_slots(cfg, len(tasks)),
                    "used_gpus": sorted(set(physical_slots(cfg, len(tasks)).values())),
                    "slots": [
                        [t, ep]
                        for ep in range(cfg["episodes_per_task"])
                        for t, _ in tasks
                    ],
                    "resume_dispositions": dispositions,
                    "runtime_attested": end_execution is not None,
                    **(
                        {"end_fairness_execution": end_execution}
                        if end_execution is not None
                        else {}
                    ),
                    "models_loaded": 0,
                    "environments_created": 0,
                },
                indent=2,
            )
        )
        return 0
    if args.mode == "authorize":
        if args.owner_decision is None:
            raise ValueError("explicit externally provided --owner-decision required")
        decision = read(args.owner_decision)
        manifest = read(root / "manifest.json")
        store = Store(root, manifest)
        if (
            set(decision)
            != {
                "schema",
                "approved_by",
                "owner_decision_ref",
                "manifest_digest",
                "slots",
            }
            or decision["schema"] != "psm_eval_v2_owner_release_v1"
            or decision["approved_by"] != "Owner"
            or decision["manifest_digest"] != manifest["digest"]
            or not decision["owner_decision_ref"]
            or not decision["slots"]
        ):
            raise ValueError("invalid targeted Owner release document")
        targets = [(v["task"], v["episode"]) for v in decision["slots"]]
        if len(set(targets)) != len(targets):
            raise ValueError("duplicate Owner target")
        with store.locked():
            # Prevalidate every target before publishing any permit.
            for task, ep in targets:
                if store.slot(task, ep)["status"] not in (
                    "skipped_init_error",
                    "scene_admission_exhausted",
                ):
                    raise ValueError(
                        "Owner release can only target blocked missing slots"
                    )
            raw = args.owner_decision.read_bytes()
            sha = hashlib.sha256(raw).hexdigest()
            path = root / "_internal/owner_decisions" / f"{sha}.json"
            if not path.exists():
                write(path, decision)
            for task, ep in targets:
                store.authorize_retry(
                    task, ep, owner_ref=decision["owner_decision_ref"] + ":" + sha
                )
        print(json.dumps({"owner_released": targets, "no_execution": True}))
        return 0
    cache = root / "_internal/cache"
    if args.mode == "fresh":
        # Imports may materialize caches. They must not create/adopt the fresh
        # namespace before its exclusive mkdir succeeds.
        with tempfile.TemporaryDirectory(prefix="psm-eval-v2-preflight-") as temporary:
            manifest, inputs, environment = prepare_inputs(cfg, cache=Path(temporary))
        store = Store(root, manifest)
        store.create()
        if manifest["experiment"].get("g2") is None:
            environment = runtime_environment(cache)
        else:
            environment = with_runtime_caches(environment, cache)
    else:
        manifest = read(root / "manifest.json")
        store = Store(root, manifest)
        inputs = environment = None
    with store.locked():
        if args.mode == "resume":
            anchor = read(root / "_internal/run_inputs.json")
            _, inputs, environment = prepare_inputs(
                cfg, cache=cache, anchor=anchor, manifest=manifest, **options
            )
        # Verify every retained Core before publishing the invocation or
        # launching work under a different approved source identity.
        transition = {}
        if approval_key is not None:
            transition = {
                **options,
                "retained_valid_cores": [
                    {
                        "task": task,
                        "episode": row["episode"],
                        "core_digest": digest(row),
                    }
                    for task in manifest["task_order"]
                    for row in store.rows(task)
                ],
            }
        if args.end_fairness_resume_approval is not None:
            transition.update(
                inputs["end_fairness_execution"],
                frozen_run={
                    "manifest_sha256": hashlib.sha256(
                        (root / "manifest.json").read_bytes()
                    ).hexdigest(),
                    "run_inputs_sha256": hashlib.sha256(
                        (root / "_internal/run_inputs.json").read_bytes()
                    ).hexdigest(),
                },
            )
        probe = {
            "manifest_digest": manifest["digest"],
            "evaluation_runtime": inputs["runtime"],
            "runtime_probe_evidence": inputs["runtime_probe_evidence"],
        }
        inputs = {
            key: value
            for key, value in inputs.items()
            if key not in ("runtime", "runtime_probe_evidence")
        }
        inputs["runtime"] = {"digest": probe["evaluation_runtime"]["digest"]}
        probe_path = root / "_internal/runtime_probe" / f"{uuid.uuid4().hex}.json"
        write_runtime_probe(probe_path, probe)
        if args.mode == "fresh":
            write(root / "_internal/run_inputs.json", inputs)
        anchor = read(root / "_internal/run_inputs.json")
        record = verification_record(
            inputs["model"], run_root=root, anchor_sha256=digest(anchor)
        )
        write(root / "_internal/verification_cache.json", record, replace=True)
        save(
            root / "_internal/invocations" / f"{time.time_ns()}.json",
            {
                "mode": args.mode,
                "resolved": cfg,
                "actual_root": inputs["actual_root"],
                "clock_preflight": inputs.get("clock_preflight"),
                **transition,
                "runtime_probe": {
                    "path": str(probe_path.relative_to(root)),
                    "canonical_sha256": digest(probe),
                },
            },
        )
        runtime = runtime_type(store, cfg, inputs, environment)
        try:
            report, error = runtime.run()
        except BaseException as failed:
            error = failed
            try:
                runtime.close()
            except BaseException as cleanup_error:
                write(
                    root / "_internal/cleanup_failure.json",
                    {"error": repr(cleanup_error)[:8192]},
                    replace=True,
                )
            write(
                root / "_internal/last_failure.json",
                {"error": repr(failed)[:8192]},
                replace=True,
            )
            try:
                report = store.publish_views()
            except Exception as invalid:
                report = {
                    "schema": "psm_eval_v2_blocked_evidence",
                    "manifest_digest": manifest["digest"],
                    "status": "BLOCKED_EVIDENCE",
                    "sr": None,
                    "partial_sr_valid_only": None,
                    "results_qualified": False,
                    "error": repr(invalid)[:8192],
                    "core_records_unchanged": True,
                }
                write_report(root / "summary.json", report)
        write(
            root / "_internal/coordination_metrics.json", store.metrics(), replace=True
        )
        media_incomplete = False
        if cfg.get("save_generated_video") == "all":
            from robocasa_eval_v2.generated_media import publish

            try:
                media_report = publish(store)
            except (OSError, ValueError) as failed:
                media_report = {
                    "status": "MEDIA_INCOMPLETE",
                    "error": repr(failed)[:1024],
                    "independent_of_SR": True,
                }
            media_incomplete = media_report["status"] != "COMPLETE"
            report = {**report, "generated_media": media_report}
            if media_incomplete:
                import sys

                print(
                    "[eval-v2] MEDIA_INCOMPLETE: see media_summary.json; Core/SR unchanged",
                    file=sys.stderr,
                    flush=True,
                )
        print(json.dumps(report, ensure_ascii=False))
        if error is not None:
            import sys

            print(
                "[eval-v2] stopped: " + repr(error)[:8192], file=sys.stderr, flush=True
            )
        return (
            1
            if error is not None or not report["results_qualified"] or media_incomplete
            else 0
        )
