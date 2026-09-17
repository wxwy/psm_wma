"""Production-driver rollover boundary witness: production queue_seed on the real catalog.

This is criterion 2's production-path half (DS LOW + GPT HIGH-2 planning layer): the
**production** ``ActiveLocalMemoryWindowDriver._maybe_rollover`` (not the probe's
reference rollover) runs on the real full catalog with the **production queue_seed**
derived from the frozen digests, and plans windows continuously across the §10.1
112-window exhaustion boundary.  ``producer.produce`` is never called, so this stays a
pure planning-layer witness; the GPU short-run is a separate Gate.

Production queue_seed (config ``action_policy_libero_edge_all.py:344-346``):
  manifest_digest = PSM_R09_B2_STREAM_MANIFEST_ROOT or "libero4in1-4suite-manifest"
  config_digest   = PSM_R09_B_TTT_ACTIVE_CONFIG_DIGEST or "v035-frozen-local-ttt"
  source_digest   = LIBERO_LATENT_CACHE_ROOT or "libero4in1-latent-cache"
  queue_seed      = int(sha256(f"{manifest}|{config}|{source}").hexdigest()[:16], 16)

Run (mirrors ``probe_epoch_reuse_planning.py``):
    LIBERO_ROOT=... LIBERO_LATENT_CACHE_ROOT=... \
        python tools/g0/probe_epoch_reuse_production_driver.py \
        --output-json artifacts/g0/active_static_probe/probe_epoch_reuse_production_driver.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cosmos-framework"))

from probe_r09_b_active_static import (  # noqa: E402
    SUITES,
    TTT_TBPTT_STEPS,
    _build_dataset,
    _local_memory_shim,
)

from cosmos_framework.data.generator.action.datasets.canonical_local_memory_producer import (  # noqa: E402
    CanonicalLocalMemorySegmentProducer,
)
from cosmos_framework.model.generator.mot.active_local_memory_driver import (  # noqa: E402
    ActiveLocalMemoryWindowDriver,
)
from cosmos_framework.model.generator.mot.active_local_memory_launch import (  # noqa: E402
    SuiteRoutedSegmentProducer,
    canonical_segment_adapter_from_model,
    canonical_segment_streams,
    canonical_slow_parameters_from_model,
)
from cosmos_framework.model.generator.mot.canonical_segment_adapter_scheduler import (  # noqa: E402
    queue_permutation,
)
from cosmos_framework.model.generator.mot.canonical_segment_runtime import (  # noqa: E402
    CanonicalSegmentRuntimeOwner,
)
from cosmos_framework.model.generator.mot.local_memory_segment import (  # noqa: E402
    RankLocalSegmentScheduler,
)
from cosmos_framework.model.generator.mot.production_active_wiring import (  # noqa: E402
    ProductionActiveWiringRegistry,
)
from cosmos_framework.model.generator.mot.production_segment_wiring import (  # noqa: E402
    CanonicalSegmentWiring,
)


def _production_queue_seed(manifest_digest: str, config_digest: str, source_digest: str) -> int:
    preimage = f"{manifest_digest}|{config_digest}|{source_digest}"
    return int(hashlib.sha256(preimage.encode("utf-8")).hexdigest()[:16], 16)


def _slot_of(stream) -> tuple[int, int]:
    return (int(stream.slot_id), int(stream.episode_index))


def _replay_by_slot(driver: ActiveLocalMemoryWindowDriver, slot: int) -> tuple[tuple[int, int], ...]:
    """Independent criterion-10 replay: reorder ``_by_slot`` from the raw reference order."""
    category = driver._slot_category[slot]
    category_slots = [s for s in driver._by_slot if driver._slot_category[s] == category]
    reference = sorted(
        (stream for other in category_slots for stream in driver._by_slot[other]),
        key=lambda stream: (driver.producer.source_digest, str(stream.episode_index)),
    )
    permutation = queue_permutation(
        queue_seed=driver._queue_seed,
        epoch=driver._slot_epoch[slot],
        category=category,
        catalog_size=len(reference),
    )
    ordered = [reference[index] for index in permutation]
    own = {_slot_of(stream) for stream in driver._by_slot[slot]}
    return tuple(_slot_of(stream) for stream in ordered if _slot_of(stream) in own)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--target-windows", type=int, default=120)
    parser.add_argument("--max-episodes", type=int, default=None)
    args = parser.parse_args()

    libero_root = os.environ.get("LIBERO_ROOT")
    cache_root = os.environ.get("LIBERO_LATENT_CACHE_ROOT")
    if not libero_root:
        raise RuntimeError("LIBERO_ROOT is required")
    if not cache_root:
        raise RuntimeError("LIBERO_LATENT_CACHE_ROOT is required")

    manifest_digest = os.environ.get("PSM_R09_B2_STREAM_MANIFEST_ROOT") or "libero4in1-4suite-manifest"
    config_digest = os.environ.get("PSM_R09_B_TTT_ACTIVE_CONFIG_DIGEST") or "v035-frozen-local-ttt"
    source_digest = cache_root
    queue_seed = _production_queue_seed(manifest_digest, config_digest, source_digest)

    producers = {}
    for suite in SUITES:
        dataset = _build_dataset(
            suite, libero_root=libero_root, cache_root=cache_root, max_episodes=args.max_episodes
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
    streams = canonical_segment_streams(producers, b_stream=8)
    slot_categories = {stream.slot_id: stream.category for stream in streams}
    all_slots = tuple(sorted(slot_categories))

    model = _local_memory_shim()
    wiring = CanonicalSegmentWiring(
        canonical_segment_adapter_from_model(model), canonical_slow_parameters_from_model(model)
    )
    scheduler = RankLocalSegmentScheduler(rank=0, target_distribution={s: 1.0 / len(SUITES) for s in SUITES})
    registry = ProductionActiveWiringRegistry(CanonicalSegmentRuntimeOwner(scheduler, wiring))
    driver = ActiveLocalMemoryWindowDriver(
        registry=registry, producer=router, streams=streams, window_members=128, queue_seed=queue_seed
    )

    planned = TTT_TBPTT_STEPS
    windows = 0
    boundary = 0
    rollover_records: list[dict] = []
    error: str | None = None
    try:
        while windows < args.target_windows:
            before_epochs = dict(driver._slot_epoch)
            driver._maybe_rollover()
            after_epochs = dict(driver._slot_epoch)
            if after_epochs != before_epochs:
                boundary += 1
                reused = sorted(slot for slot in all_slots if after_epochs.get(slot, 0) > before_epochs.get(slot, 0))
                continued = sorted(slot for slot in all_slots if after_epochs.get(slot, 0) == before_epochs.get(slot, 0))
                if len(rollover_records) < 5:
                    rollover_records.append(
                        {
                            "boundary": boundary,
                            "windows": windows,
                            "reused_slots": reused,
                            "continued_slots": continued,
                            "slot_epoch": dict(driver._slot_epoch),
                        }
                    )
            freeze = driver.freeze_window()
            for index, member in enumerate(freeze.members):
                identity = freeze.identities[index]
                if member.rebind_before_admit:
                    driver._rebind_terminal(int(member.stream.slot_id))
                admitted = scheduler.admit((identity,))
                scheduler.commit(admitted, planned)
            windows += 1
    except Exception as exc:  # noqa: BLE001
        error = repr(exc)

    # Criterion 10 replay: every reused slot's _by_slot must equal the independent
    # replay.  An epoch-0 slot was never reused, so its _by_slot keeps the initial
    # round-robin order and is not replayed (design §3.3: queue_permutation only
    # applies to a reused slot's fresh-episode reorder).
    replay_mismatch = []
    for slot in all_slots:
        if driver._slot_epoch.get(slot, 0) == 0:
            continue
        got = tuple(_slot_of(stream) for stream in driver._by_slot[slot])
        want = _replay_by_slot(driver, slot)
        if got != want:
            replay_mismatch.append({"slot": slot, "want_len": len(want), "got_len": len(got)})

    crossed_113 = windows > 112
    result_pass = error is None and crossed_113 and not replay_mismatch and driver._window_index == windows
    report = {
        "result": "PASS" if result_pass else "FAIL",
        "manifest_digest": manifest_digest,
        "config_digest": config_digest,
        "source_digest": source_digest,
        "queue_seed": queue_seed,
        "windows_total": windows,
        "window_index": driver._window_index,
        "boundary_crossed_113": crossed_113,
        "rollover_boundaries": boundary,
        "rollover_records": rollover_records,
        "slot_epoch": driver._slot_epoch,
        "committed_identities": len(scheduler.committed_identities),
        "criterion10_replay_mismatches": replay_mismatch,
        "error": error,
    }
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
        print(f"[out] wrote {args.output_json}")
    return 0 if result_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
