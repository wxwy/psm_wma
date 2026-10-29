"""Independent Fresh/Resume/Dry-run/explicit Owner release entry."""

from __future__ import annotations

import hashlib
import json
import tempfile
import time
from pathlib import Path

from cosmos_framework.evaluation.robocasa_v2.contract import digest
from cosmos_framework.evaluation.robocasa_v2.scheduler import slot_disposition
from cosmos_framework.evaluation.robocasa_v2.store import (
    Store,
    read,
    save,
    write,
    write_report,
)
from robocasa_episode_resume.model_identity import verification_record

from robocasa_eval_v2.config import resolve, execution
from robocasa_eval_v2.identity import discover, prepare, runtime_environment
from robocasa_eval_v2.runtime import Runtime
from robocasa_eval_v2.resources import physical_slots


def main(argv=None, *, prepare_inputs=prepare, runtime_type=Runtime):
    args, cfg = resolve(argv)
    root = Path(cfg["output_dir"])
    if args.mode == "dry-run":
        tasks = discover(cfg)
        dispositions = []
        if (root / "manifest.json").exists():
            manifest = read(root / "manifest.json")
            store = Store(root, manifest)
            if (
                manifest["task_order"] != [t for t, _ in tasks]
                or manifest["episodes_per_task"] != cfg["episodes_per_task"]
                or manifest.get("execution") != execution(cfg)
            ):
                raise ValueError("dry-run scientific plan differs from frozen Run")
            for ep in range(cfg["episodes_per_task"]):
                for task, _ in tasks:
                    action = {
                        "skip_valid_core": "skip_valid",
                        "skip_owner_pending": "skip_owner_pending",
                        "execute": "execute_missing",
                    }[slot_disposition(store, task, ep)]
                    dispositions.append({"task": task, "episode": ep, "action": action})
        print(
            json.dumps(
                {
                    "mode": "CPU_PREVIEW_ONLY",
                    "resolved": cfg,
                    "task_order": [t for t, _ in tasks],
                    "physical_slots": physical_slots(cfg, len(tasks)),
                    "used_gpus": sorted(set(physical_slots(cfg, len(tasks)).values())),
                    "slots": [
                        [t, ep]
                        for ep in range(cfg["episodes_per_task"])
                        for t, _ in tasks
                    ],
                    "resume_dispositions": dispositions,
                    "runtime_attested": False,
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
        environment = runtime_environment(cache)
    else:
        manifest = read(root / "manifest.json")
        store = Store(root, manifest)
        inputs = environment = None
    with store.locked():
        if args.mode == "resume":
            anchor = read(root / "_internal/run_inputs.json")
            _, inputs, environment = prepare_inputs(
                cfg, cache=cache, anchor=anchor, manifest=manifest
            )
        else:
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
        print(json.dumps(report, ensure_ascii=False))
        if error is not None:
            import sys

            print(
                "[eval-v2] stopped: " + repr(error)[:8192], file=sys.stderr, flush=True
            )
        return 1 if error is not None or not report["results_qualified"] else 0
