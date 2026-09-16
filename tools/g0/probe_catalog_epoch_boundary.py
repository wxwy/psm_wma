"""Is the frozen epoch boundary reachable on the real active-route catalogue?

The catalog epoch-reuse design proposes to reuse the already-frozen contract in
``canonical_segment_adapter_scheduler.rollover_projected_if_safe`` (:542-549).
Its two conditions are evaluated at every *member* boundary, i.e. between two
members of a window, not only at window boundaries; this probe evaluates them at
window boundaries, which is where the design can act, and reports whether any
boundary satisfies both:

  1. every category's queue position has reached the end of its catalogue, and
  2. every stable slot is terminal (no episode straddles the boundary).

**Condition 1 is episode-level, not block-level.**  ``_admit_free_slot`` indexes
the permutation of ``_queue_for(category)`` with ``positions[category]``
(:512-517), ``_queue_for`` keeps the ``cursor == 0`` row of each episode
(:471-477), and ``_commit_admission`` increments the position once per episode
admission (:589-590).  So an episode whose first block has been committed counts
as admitted even while it still has blocks left.  A block-level reading ("does
this category still have a whole block left") is a strictly stronger predicate
and is reported separately, under ``final_state``, because it is what governs
whether another window can still be frozen.

``freeze_window`` either returns a full ``window_members`` plan or raises, so
"can another window be frozen" needs no separate probe: try, and a raise is the
boundary.  The driver's cursor state is saved and restored around the failing
attempt because ``freeze_window`` is not atomic -- it calls ``_commit_block``
per member, so a raise part-way through leaves the cursors advanced.

No latents are read: the walk drives ``freeze_window``, ``scheduler.admit``,
``scheduler.commit`` and ``driver._rebind_terminal`` only, all of which are
metadata.  ``producer.produce`` is never called, which is what keeps this cheap
enough to walk the full catalogue rather than one window.

Run (roots come from the environment, as in ``probe_r09_b_active_static``):

    LIBERO_ROOT=... LIBERO_LATENT_CACHE_ROOT=... \
        python tools/g0/probe_catalog_epoch_boundary.py \
        --output-json artifacts/g0/active_static_probe/probe_catalog_epoch_boundary.json
"""

from __future__ import annotations

import argparse
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

# Cap on the stored boundary index lists; the counts are exact regardless.
_MAX_RECORDED_BOUNDARIES = 20


def _save_cursors(driver: ActiveLocalMemoryWindowDriver) -> tuple:
    return (
        dict(driver._stream_index),
        dict(driver._active_stream),
        dict(driver._active_cursor),
        driver._window_index,
    )


def _restore_cursors(driver: ActiveLocalMemoryWindowDriver, saved: tuple) -> None:
    stream_index, active_stream, active_cursor, window_index = saved
    driver._stream_index = stream_index
    driver._active_stream = active_stream
    driver._active_cursor = active_cursor
    driver._window_index = window_index


def _last_admissible(driver: ActiveLocalMemoryWindowDriver) -> dict[int, int | None]:
    """Per slot, the index of its last episode that can still serve a block.

    Episodes with no whole block are skipped by ``_peek_block`` (:273-279) and
    are never admitted, so the contract's catalogue has no row for them.
    """
    last: dict[int, int | None] = {}
    for slot, episodes in driver._by_slot.items():
        index = None
        for position, episode in enumerate(episodes):
            if int(driver.producer.block_count(episode)) > 0:
                index = position
        last[slot] = index
    return last


def _remaining_blocks(driver: ActiveLocalMemoryWindowDriver, slot: int) -> int:
    """Whole blocks this slot can still serve; the pure inverse of ``_peek_block``."""
    stream = driver._active_stream.get(slot)
    position = driver._stream_index[slot]
    total = 0
    if stream is not None:
        blocks = int(driver.producer.block_count(stream))
        total += max(blocks - 1 - driver._active_cursor[slot], 0)
        position += 1
    while position < len(driver._by_slot[slot]):
        total += max(int(driver.producer.block_count(driver._by_slot[slot][position])), 0)
        position += 1
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--b-stream", type=int, default=8)
    parser.add_argument("--ga", type=int, default=16, help="window size = b_stream * ga")
    parser.add_argument("--max-episodes", type=int, default=None, help="cap per suite (smoke speed)")
    parser.add_argument("--max-windows", type=int, default=100000, help="runaway guard")
    args = parser.parse_args()

    libero_root = os.environ.get("LIBERO_ROOT")
    cache_root = os.environ.get("LIBERO_LATENT_CACHE_ROOT")
    if not libero_root:
        raise RuntimeError("LIBERO_ROOT is required")
    if not cache_root:
        raise RuntimeError("LIBERO_LATENT_CACHE_ROOT is required")

    window_members = args.b_stream * args.ga

    producers = {}
    for suite in SUITES:
        dataset = _build_dataset(
            suite, libero_root=libero_root, cache_root=cache_root, max_episodes=args.max_episodes
        )
        producers[suite] = CanonicalLocalMemorySegmentProducer(
            dataset,
            category=suite,
            ttt_tbptt_steps=TTT_TBPTT_STEPS,
            manifest_digest="epoch-boundary-probe",
            config_digest="epoch-boundary-probe",
            source_digest=cache_root,
        )
    router = SuiteRoutedSegmentProducer(producers, source_digest=cache_root)
    streams = canonical_segment_streams(producers, b_stream=args.b_stream)
    slot_category = {stream.slot_id: stream.category for stream in streams}
    total_blocks = sum(int(producers[stream.category].block_count(stream)) for stream in streams)
    admissible_episodes = {
        category: sum(
            1
            for stream in streams
            if stream.category == category and int(producers[category].block_count(stream)) > 0
        )
        for category in SUITES
    }

    model = _local_memory_shim()
    wiring = CanonicalSegmentWiring(
        canonical_segment_adapter_from_model(model), canonical_slow_parameters_from_model(model)
    )
    scheduler = RankLocalSegmentScheduler(
        rank=0, target_distribution={suite: 1.0 / len(SUITES) for suite in SUITES}
    )
    registry = ProductionActiveWiringRegistry(CanonicalSegmentRuntimeOwner(scheduler, wiring))
    driver = ActiveLocalMemoryWindowDriver(
        registry=registry,
        producer=router,
        streams=streams,
        window_members=window_members,
    )

    last_admissible = _last_admissible(driver)

    def _condition1() -> bool:
        """Contract condition 1: every category's last admissible episode admitted."""
        for slot, index in last_admissible.items():
            if index is None:
                continue
            if driver._active_stream.get(slot) is not driver._by_slot[slot][index]:
                return False
        return True

    def _condition2() -> bool:
        """Contract condition 2: every stable slot is terminal."""
        stable = dict(scheduler.stable_slots)
        terminal = dict(scheduler.terminal_slots)
        return all(slot in terminal for slot in stable)

    planned = int(producers[SUITES[0]].ttt_tbptt_steps)
    windows = 0
    boundary_error = None
    cond1_boundaries: list[int] = []
    cond2_boundaries: list[int] = []
    both_boundaries: list[int] = []
    cond1_true_count = 0
    cond2_true_count = 0
    while windows < args.max_windows:
        saved = _save_cursors(driver)
        try:
            freeze = driver.freeze_window()
        except RuntimeError as error:
            _restore_cursors(driver, saved)
            boundary_error = str(error)
            break
        # Mirror ``_produce``'s order: retire the finished terminal slot before
        # its successor is admitted, then admit/commit exactly one member.
        for index, member in enumerate(freeze.members):
            identity = freeze.identities[index]
            if member.rebind_before_admit:
                driver._rebind_terminal(int(member.stream.slot_id))
            admitted = scheduler.admit((identity,))
            scheduler.commit(admitted, planned)
        windows += 1
        # The boundary the design can act on is the one between windows.
        first, second = _condition1(), _condition2()
        if first:
            cond1_true_count += 1
            if len(cond1_boundaries) < _MAX_RECORDED_BOUNDARIES:
                cond1_boundaries.append(windows)
        if second:
            cond2_true_count += 1
            if len(cond2_boundaries) < _MAX_RECORDED_BOUNDARIES:
                cond2_boundaries.append(windows)
        if first and second and len(both_boundaries) < _MAX_RECORDED_BOUNDARIES:
            both_boundaries.append(windows)

    # ---- state at the boundary ---------------------------------------------
    remaining = {slot: _remaining_blocks(driver, slot) for slot in driver._by_slot}
    category_remaining = {
        category: sum(count for slot, count in remaining.items() if slot_category[slot] == category)
        for category in SUITES
    }
    stable_slots = dict(scheduler.stable_slots)
    terminal_slots = dict(scheduler.terminal_slots)
    non_terminal_stable = sorted(slot for slot in stable_slots if slot not in terminal_slots)

    report = {
        "result": "PASS",
        "b_stream": args.b_stream,
        "ga": args.ga,
        "window_members": window_members,
        "streams": len(streams),
        "admissible_episodes": admissible_episodes,
        "total_blocks": total_blocks,
        "windows_from_capacity": round(total_blocks / window_members, 2),
        "windows_completed": windows,
        "boundary_error": boundary_error,
        "boundary_conditions": {
            "condition1_boundaries": cond1_boundaries,
            "condition1_true_count": cond1_true_count,
            "condition2_boundaries": cond2_boundaries,
            "condition2_true_count": cond2_true_count,
            "both_true_boundaries": both_boundaries,
            "reachable": bool(both_boundaries),
        },
        "final_state": {
            # Block-level residue: blocks that no further window can consume.
            "remaining_blocks": remaining,
            "remaining_blocks_by_category": category_remaining,
            "stranded_blocks": sum(remaining.values()),
            "condition1_all_categories_drained": _condition1(),
            "condition2_all_stable_terminal": _condition2(),
            "stable_slots": sorted(stable_slots),
            "terminal_slots": sorted(terminal_slots),
            "stable_but_not_terminal": non_terminal_stable,
            "committed_identities": len(scheduler.committed_identities),
            "admission_order": len(scheduler.admission_order),
            "cumulative_exposure": dict(scheduler.cumulative_valid_consumer_exposure),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"[out] wrote {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
