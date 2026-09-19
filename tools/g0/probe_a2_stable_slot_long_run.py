"""Metadata-only long-run witness for synchronized stable-slot A2.

This probe uses the production A2 classes themselves:
  * GroupedActiveLocalMemoryWindowDriver
  * GroupedSegmentRuntimeOwner._stage_scheduler

It never calls producer.produce(), never materializes latents, and never runs the
Transformer.  It therefore isolates the long-run data-lifecycle contract:
stable-slot synchronized grouping, episode chronology, terminal rebind,
slot-local catalog epoch reuse, queue replay, and the ability to serve a target
number of optimizer windows.

Default geometry matches the accepted A2 implementation:
  B_stream=8, T=16, GA=16 => 128 consumers/native forward,
  16 native forwards/update => 2048 consumers/update.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cosmos-framework"))

from probe_r09_b_active_static import SUITES, TTT_TBPTT_STEPS, _build_dataset, _local_memory_shim  # noqa: E402

from cosmos_framework.data.generator.action.datasets.canonical_local_memory_producer import (  # noqa: E402
    CanonicalLocalMemorySegmentProducer,
)
from cosmos_framework.model.generator.mot.active_local_memory_launch import (  # noqa: E402
    SuiteRoutedSegmentProducer,
    canonical_segment_adapter_from_model,
    canonical_segment_streams,
    canonical_slow_parameters_from_model,
)
from cosmos_framework.model.generator.mot.canonical_segment_adapter_scheduler import queue_permutation  # noqa: E402
from cosmos_framework.model.generator.mot.grouped_active_driver import GroupedActiveLocalMemoryWindowDriver  # noqa: E402
from cosmos_framework.model.generator.mot.grouped_active_runtime import (  # noqa: E402
    GroupedActiveWiringRegistry,
    GroupedSegmentRuntimeOwner,
    _SCHEDULER_FIELDS,
)
from cosmos_framework.model.generator.mot.local_memory_segment import RankLocalSegmentScheduler  # noqa: E402
from cosmos_framework.model.generator.mot.production_segment_wiring import CanonicalSegmentWiring  # noqa: E402


def _digest(manifest: str, config: str, source: str) -> str:
    return hashlib.sha256(f"{manifest}|{config}|{source}".encode("utf-8")).hexdigest()


def _stream_key(stream: Any) -> tuple[int, int]:
    return int(stream.slot_id), int(stream.episode_index)


def _expected_slot_order(
    *,
    original_streams: tuple[Any, ...],
    slot: int,
    epoch: int,
    category: str,
    queue_seed: int,
    source_digest: str,
) -> tuple[tuple[int, int], ...]:
    category_streams = [stream for stream in original_streams if stream.category == category]
    reference = sorted(category_streams, key=lambda stream: (source_digest, str(stream.episode_index)))
    permutation = queue_permutation(
        queue_seed=queue_seed,
        epoch=epoch,
        category=category,
        catalog_size=len(reference),
    )
    ordered = [reference[index] for index in permutation]
    return tuple(_stream_key(stream) for stream in ordered if int(stream.slot_id) == slot)


def _write(path: Path | None, payload: dict[str, Any]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n")
    print(f"[out] wrote {path}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--capacity-output-json", type=Path, default=None)
    parser.add_argument("--reuse-output-json", type=Path, default=None)
    parser.add_argument("--target-windows", type=int, default=5000)
    parser.add_argument("--b-stream", type=int, default=8)
    parser.add_argument("--ga", type=int, default=16)
    parser.add_argument("--max-episodes", type=int, default=None)
    parser.add_argument("--progress-every", type=int, default=250)
    args = parser.parse_args()

    if args.target_windows <= 0 or args.b_stream <= 0 or args.ga <= 0:
        raise ValueError("target-windows, b-stream and ga must be positive")

    libero_root = os.environ.get("LIBERO_ROOT")
    cache_root = os.environ.get("LIBERO_LATENT_CACHE_ROOT")
    if not libero_root or not cache_root:
        raise RuntimeError("LIBERO_ROOT and LIBERO_LATENT_CACHE_ROOT are required")

    manifest_digest = os.environ.get("PSM_R09_B2_STREAM_MANIFEST_ROOT") or "libero4in1-4suite-manifest"
    config_digest = os.environ.get("PSM_R09_B_TTT_ACTIVE_CONFIG_DIGEST") or "v035-frozen-local-ttt"
    catalog_digest = _digest(manifest_digest, config_digest, cache_root)
    queue_seed = int(catalog_digest[:16], 16)

    producers: dict[str, CanonicalLocalMemorySegmentProducer] = {}
    for suite in SUITES:
        dataset = _build_dataset(
            suite,
            libero_root=libero_root,
            cache_root=cache_root,
            max_episodes=args.max_episodes,
        )
        producers[suite] = CanonicalLocalMemorySegmentProducer(
            dataset,
            category=suite,
            ttt_tbptt_steps=TTT_TBPTT_STEPS,
            manifest_digest=manifest_digest,
            config_digest=config_digest,
            source_digest=cache_root,
        )

    router = SuiteRoutedSegmentProducer(producers, source_digest=cache_root)
    streams = canonical_segment_streams(producers, b_stream=args.b_stream)
    slot_categories = {int(stream.slot_id): stream.category for stream in streams}
    slots = tuple(sorted(slot_categories))
    if slots != tuple(range(args.b_stream)):
        raise RuntimeError(f"stable slot ids are not dense 0..B_stream-1: {slots}")

    model = _local_memory_shim()
    wiring = CanonicalSegmentWiring(
        canonical_segment_adapter_from_model(model),
        canonical_slow_parameters_from_model(model),
    )
    scheduler = RankLocalSegmentScheduler(
        rank=0,
        target_distribution={suite: 1.0 / len(SUITES) for suite in SUITES},
    )
    owner = GroupedSegmentRuntimeOwner(scheduler, wiring)
    registry = GroupedActiveWiringRegistry(owner)
    driver = GroupedActiveLocalMemoryWindowDriver(
        group_size=args.b_stream,
        manifest_digest=manifest_digest,
        config_digest=config_digest,
        registry=registry,
        producer=router,
        streams=streams,
        window_members=args.ga,
        plan_chain_id="a2-long-run-probe",
        catalog_digest=catalog_digest,
        queue_seed=queue_seed,
        prefetch_depth=0,
    )

    t = int(TTT_TBPTT_STEPS)
    per_slot_catalog_blocks = {
        slot: sum(int(router.block_count(stream)) for stream in driver._by_slot[slot])
        for slot in slots
    }
    per_slot_segments = Counter({slot: 0 for slot in slots})
    per_slot_rebinds = Counter({slot: 0 for slot in slots})
    per_slot_epoch_events = Counter({slot: 0 for slot in slots})
    last_identity: dict[int, Any] = {}
    replay_mismatches: list[dict[str, Any]] = []
    chronology_errors: list[str] = []
    group_shape_errors: list[str] = []
    rollover_records: list[dict[str, Any]] = []
    max_committed_audit = 0
    max_admission_audit = 0
    windows_completed = 0
    groups_completed = 0
    logical_segments = 0
    error: str | None = None

    try:
        while windows_completed < args.target_windows:
            window_number = windows_completed + 1
            epochs_before = dict(driver._slot_epoch)

            # Production _arm_initial() calls this before freeze_window().
            driver._maybe_rollover()
            epochs_after_boundary = dict(driver._slot_epoch)

            freeze = driver.freeze_window()
            group_plan = driver._plan_groups(freeze)
            epochs_after_freeze = dict(driver._slot_epoch)

            if len(group_plan.members) != args.ga:
                group_shape_errors.append(
                    f"window {window_number}: groups={len(group_plan.members)} expected={args.ga}"
                )
                break
            if len(freeze.identities) != args.ga * args.b_stream:
                group_shape_errors.append(
                    f"window {window_number}: logical rows={len(freeze.identities)} "
                    f"expected={args.ga * args.b_stream}"
                )
                break

            changed_slots = [
                slot for slot in slots if epochs_after_freeze[slot] != epochs_before[slot]
            ]
            if changed_slots:
                record = {
                    "window": window_number,
                    "changed_slots": changed_slots,
                    "epoch_before": {str(s): epochs_before[s] for s in changed_slots},
                    "epoch_after_boundary": {str(s): epochs_after_boundary[s] for s in changed_slots},
                    "epoch_after_freeze": {str(s): epochs_after_freeze[s] for s in changed_slots},
                }
                if len(rollover_records) < 64:
                    rollover_records.append(record)
                for slot in changed_slots:
                    delta = epochs_after_freeze[slot] - epochs_before[slot]
                    if delta <= 0:
                        raise RuntimeError("slot epoch moved backwards or did not advance")
                    per_slot_epoch_events[slot] += delta
                    expected = _expected_slot_order(
                        original_streams=streams,
                        slot=slot,
                        epoch=epochs_after_freeze[slot],
                        category=slot_categories[slot],
                        queue_seed=queue_seed,
                        source_digest=cache_root,
                    )
                    got = tuple(_stream_key(stream) for stream in driver._by_slot[slot])
                    if got != expected:
                        replay_mismatches.append(
                            {
                                "window": window_number,
                                "slot": slot,
                                "epoch": epochs_after_freeze[slot],
                                "got_len": len(got),
                                "expected_len": len(expected),
                            }
                        )

            for group_index, group in enumerate(group_plan.members):
                group_slots = tuple(int(identity.slot_id) for identity in group.row_identities)
                if group_slots != slots:
                    group_shape_errors.append(
                        f"window {window_number} group {group_index}: slots={group_slots}"
                    )
                    break
                if tuple(group.row_planned_n_valid) != (t,) * args.b_stream:
                    group_shape_errors.append(
                        f"window {window_number} group {group_index}: row counts={group.row_planned_n_valid}"
                    )
                    break

                for identity in group.row_identities:
                    slot = int(identity.slot_id)
                    previous = last_identity.get(slot)
                    if previous is not None:
                        exact_continuation = (
                            previous.episode_id == identity.episode_id
                            and previous.category == identity.category
                            and previous.source_digest == identity.source_digest
                            and identity.cursor == previous.cursor + 1
                        )
                        legal_rebind = previous.training_stream_end and identity.cursor == 0
                        if not (exact_continuation or legal_rebind):
                            chronology_errors.append(
                                f"window {window_number} group {group_index} slot {slot}: "
                                f"{previous.episode_id}:{previous.cursor}/terminal={previous.training_stream_end} "
                                f"-> {identity.episode_id}:{identity.cursor}"
                            )
                        if legal_rebind:
                            per_slot_rebinds[slot] += 1
                    elif identity.cursor != 0:
                        chronology_errors.append(
                            f"window {window_number} group {group_index} slot {slot}: first cursor={identity.cursor}"
                        )
                    last_identity[slot] = identity
                    per_slot_segments[slot] += 1

                # Exact scheduler metadata path used by GroupedSegmentRuntimeOwner.prepare().
                candidate = owner._stage_scheduler(group)
                for name in _SCHEDULER_FIELDS:
                    setattr(owner.scheduler, name, getattr(candidate, name))
                groups_completed += 1
                logical_segments += args.b_stream
                max_committed_audit = max(max_committed_audit, len(owner.scheduler.committed_identities))
                max_admission_audit = max(max_admission_audit, len(owner.scheduler.admission_order))

            if group_shape_errors or chronology_errors or replay_mismatches:
                break

            windows_completed += 1
            if args.progress_every and windows_completed % args.progress_every == 0:
                print(
                    f"[progress] windows={windows_completed}/{args.target_windows} "
                    f"slot_epoch={driver._slot_epoch} "
                    f"committed_audit={len(owner.scheduler.committed_identities)}",
                    flush=True,
                )
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {exc}"

    expected_segments_per_slot = args.target_windows * args.ga
    expected_logical_segments = args.target_windows * args.ga * args.b_stream
    expected_consumers = expected_logical_segments * t
    exposure = {
        str(k): int(v)
        for k, v in sorted(owner.scheduler.cumulative_valid_consumer_exposure.items())
    }
    exposure_total = sum(exposure.values())
    expected_category_consumers = expected_consumers // len(SUITES)

    capacity_pass = (
        error is None
        and windows_completed == args.target_windows
        and driver._window_index == args.target_windows
        and groups_completed == args.target_windows * args.ga
        and logical_segments == expected_logical_segments
        and all(per_slot_segments[slot] == expected_segments_per_slot for slot in slots)
        and exposure_total == expected_consumers
        and all(exposure.get(suite, 0) == expected_category_consumers for suite in SUITES)
        and not group_shape_errors
        and not chronology_errors
    )
    reuse_pass = (
        capacity_pass
        and all(driver._slot_epoch[slot] > 0 for slot in slots)
        and all(per_slot_epoch_events[slot] == driver._slot_epoch[slot] for slot in slots)
        and not replay_mismatches
        and all(per_slot_rebinds[slot] > 0 for slot in slots)
    )

    capacity = {
        "result": "PASS" if capacity_pass else "FAIL",
        "target_windows": args.target_windows,
        "windows_completed": windows_completed,
        "b_stream": args.b_stream,
        "ga": args.ga,
        "ttt_tbptt_steps": t,
        "native_forwards_per_update": args.ga,
        "logical_segments_per_update": args.ga * args.b_stream,
        "consumers_per_update": args.ga * args.b_stream * t,
        "logical_segments_total": logical_segments,
        "expected_logical_segments_total": expected_logical_segments,
        "consumers_total": exposure_total,
        "expected_consumers_total": expected_consumers,
        "per_slot_catalog_blocks": {str(k): per_slot_catalog_blocks[k] for k in slots},
        "per_slot_segments_consumed": {str(k): per_slot_segments[k] for k in slots},
        "expected_segments_per_slot": expected_segments_per_slot,
        "category_consumer_exposure": exposure,
        "expected_consumers_per_category": expected_category_consumers,
        "driver_window_index": driver._window_index,
        "groups_completed": groups_completed,
        "group_shape_errors": group_shape_errors[:20],
        "chronology_errors": chronology_errors[:20],
        "error": error,
    }

    reuse = {
        "result": "PASS" if reuse_pass else "FAIL",
        "target_windows": args.target_windows,
        "windows_completed": windows_completed,
        "queue_seed": queue_seed,
        "catalog_digest": catalog_digest,
        "slot_category": {str(k): slot_categories[k] for k in slots},
        "slot_epoch": {str(k): driver._slot_epoch[k] for k in slots},
        "slot_epoch_events": {str(k): per_slot_epoch_events[k] for k in slots},
        "per_slot_rebinds": {str(k): per_slot_rebinds[k] for k in slots},
        "rollover_records": rollover_records,
        "queue_replay_mismatches": replay_mismatches[:20],
        "max_committed_identity_audit": max_committed_audit,
        "max_admission_order_audit": max_admission_audit,
        "error": error,
    }

    combined = {
        "schema": "a2_stable_slot_long_run_planning_v1",
        "result": "PASS" if capacity_pass and reuse_pass else "FAIL",
        "implementation_child": os.popen(
            f"git -C {Path(__file__).resolve().parents[2] / 'cosmos-framework'} rev-parse HEAD"
        ).read().strip(),
        "manifest_digest": manifest_digest,
        "config_digest": config_digest,
        "source_digest": cache_root,
        "capacity": capacity,
        "epoch_reuse": reuse,
    }

    print(json.dumps(combined, indent=2, sort_keys=True, default=str))
    _write(args.output_json, combined)
    _write(args.capacity_output_json, capacity)
    _write(args.reuse_output_json, reuse)
    return 0 if combined["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
