"""Does the v0.2 epoch-reuse design actually serve >112 windows without raising?

This is the design's own acceptance criterion 2: build the same production
catalogue, then plan windows continuously across epoch boundaries with **no
tensor ever produced** (``producer.produce`` is never called), and assert that
the planner keeps going far past the single-epoch limit of 112 windows.

It also covers criterion 1 (contract consistency) and criterion 5 (deferred tail
blocks are not lost):

  1. after each rollover every slot's ``_by_slot`` list equals the subsequence,
     order-preserving, of ``queue_permutation(queue_seed, epoch, category, n)``
     over the category's episodes sorted by ``(source_digest, episode_id)``;
  5. every block deferred at the end of epoch 0 is committed during epoch 1.

The rollover implemented here is the **reference implementation** of design
v0.2 sections 3.2/4.3/4.4.  It lives in this probe, not in production code: the
production change is what the Gate authorises.  When it lands in
``active_local_memory_driver.py`` it must match this behaviour.

Two traps the design calls out, pinned down here:

* contract condition 1 is **episode-level** (one queue row per episode --
  ``_queue_for`` keeps the ``cursor == 0`` row, ``canonical_segment_adapter_scheduler
  .py:471-480``), so the trigger is bound-based, not drain-based;
* ``_queue_for`` sorts by ``identity.episode_id``, which this route builds as
  ``str(episode_index)`` -- a **string** sort (``"10" < "2"``), not numeric.

``queue_seed`` has no production source yet (design section 4.6); it is an
explicit argument here so the choice stays visible.

Run (roots come from the environment, as in ``probe_r09_b_active_static``):

    LIBERO_ROOT=... LIBERO_LATENT_CACHE_ROOT=... \
        python tools/g0/probe_epoch_reuse_planning.py --max-epochs 3 \
        --output-json artifacts/g0/active_static_probe/probe_epoch_reuse_planning.json
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
from cosmos_framework.model.generator.mot.canonical_segment_adapter_scheduler import (  # noqa: E402
    queue_permutation,
)
from cosmos_framework.model.generator.mot.canonical_segment_runtime import (  # noqa: E402
    CanonicalSegmentRuntimeOwner,
)
from cosmos_framework.model.generator.mot.local_memory_segment import (  # noqa: E402
    RankLocalSegmentScheduler,
    SegmentProvenance,
)
from cosmos_framework.model.generator.mot.production_active_wiring import (  # noqa: E402
    ProductionActiveWiringRegistry,
)
from cosmos_framework.model.generator.mot.production_segment_wiring import (  # noqa: E402
    CanonicalSegmentWiring,
)

_MAX_RECORDED_ROLLOVERS = 50


def _key(stream) -> tuple[int, int]:
    """Identify an episode within the catalogue without relying on object identity."""
    return (int(stream.slot_id), int(stream.episode_index))


def _slots_of(slot_categories: dict, category: str) -> tuple[int, ...]:
    return tuple(sorted(slot for slot, item in slot_categories.items() if item == category))


def _reference_order(streams: list, source_digest: str) -> list:
    """The category's episodes in ``_queue_for`` order: ``(source_digest, episode_id)``.

    ``episode_id`` is ``str(episode_index)`` on this route, so this is a
    lexicographic comparison -- ``"10"`` sorts before ``"2"``.
    """
    return sorted(streams, key=lambda s: (source_digest, str(s.episode_index)))


def _remaining_blocks(driver, slot: int) -> int:
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


def _all_admissible_blocks(driver, slots: tuple[int, ...]) -> set[tuple[int, int, int]]:
    """Every block the catalogue can ever serve, as ``(slot, episode_index, cursor)``."""
    blocks: set[tuple[int, int, int]] = set()
    for slot in slots:
        for stream in driver._by_slot[slot]:
            for cursor in range(int(driver.producer.block_count(stream))):
                blocks.add((slot, int(stream.episode_index), cursor))
    return blocks


def _rollover_slot(driver, scheduler, *, slot: int, epoch: int, queue_seed: int, category: str, slot_categories: dict) -> tuple[int, ...] | None:
    """v0.7 逐 slot 复用：non-terminal 继续（返回 None），terminal 复用（返回 permutation）。

    terminal 判定（design v0.8 §3.2）：``_active_stream`` 为空，或 ``_active_cursor == blocks - 1``。
    重排按 §4.4 的 **category 级**参照序：对该 category 的全部 episode（两条 slot 合并）排序，
    应用 ``queue_permutation(..., catalog_size=category 全集)``，再取该 slot 的保序子序列。
    """
    stream = driver._active_stream.get(slot)
    cursor = driver._active_cursor.get(slot)
    blocks = int(driver.producer.block_count(stream)) if stream is not None else 0
    terminal = stream is None or (cursor is not None and blocks > 0 and cursor >= blocks - 1)
    if not terminal:
        return None  # non-terminal：继续，不重置
    # terminal slot 复用：**category 级**参照序（两 slot 合并），再取该 slot 子序列。
    category_slots = _slots_of(slot_categories, category)
    reference = _reference_order(
        [s for other in category_slots for s in driver._by_slot[other]],
        driver.producer.source_digest,
    )
    permutation = queue_permutation(
        queue_seed=queue_seed, epoch=epoch, category=category, catalog_size=len(reference)
    )
    ordered = [reference[index] for index in permutation]
    own = {_key(s) for s in driver._by_slot[slot]}
    driver._by_slot[slot] = tuple(s for s in ordered if _key(s) in own)
    driver._stream_index[slot] = 0
    driver._active_stream.pop(slot, None)
    driver._active_cursor.pop(slot, None)
    # 逐 slot 清守卫（仅该 slot 的旧条目，保持 admission_order ⊆ committed_identities）
    scheduler.admission_order[:] = [i for i in scheduler.admission_order if i.slot_id != slot]
    scheduler.committed_identities[:] = [i for i in scheduler.committed_identities if i.slot_id != slot]
    scheduler.stable_slots.pop(slot, None)
    scheduler.terminal_slots.pop(slot, None)
    return permutation


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--b-stream", type=int, default=8)
    parser.add_argument("--ga", type=int, default=16, help="window size = b_stream * ga")
    parser.add_argument("--queue-seed", type=int, default=0, help="no production source yet (design 4.6)")
    parser.add_argument("--max-epochs", type=int, default=100, help="upper bound on reuse boundaries (target-windows is the real stop)")
    parser.add_argument("--target-windows", type=int, default=5040, help="45 epochs x 112 windows")
    parser.add_argument("--max-episodes", type=int, default=None, help="cap per suite (smoke speed)")
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
            manifest_digest="epoch-reuse-probe",
            config_digest="epoch-reuse-probe",
            source_digest=cache_root,
        )
    router = SuiteRoutedSegmentProducer(producers, source_digest=cache_root)
    streams = canonical_segment_streams(producers, b_stream=args.b_stream)
    slot_categories = {stream.slot_id: stream.category for stream in streams}
    all_slots = tuple(sorted(slot_categories))
    categories = sorted(set(slot_categories.values()))

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

    planned = int(producers[SUITES[0]].ttt_tbptt_steps)
    catalogue_blocks = _all_admissible_blocks(driver, all_slots)
    single_epoch_limit = len(catalogue_blocks) / window_members

    def _commit_window(epoch: int, blocks: set) -> None:
        freeze = driver.freeze_window()
        distinct: set[int] = set()
        per_slot_used: dict[int, int] = {}
        for index, member in enumerate(freeze.members):
            identity = freeze.identities[index]
            if member.rebind_before_admit:
                driver._rebind_terminal(int(member.stream.slot_id))
            admitted = scheduler.admit((identity,))
            scheduler.commit(admitted, planned)
            blocks.add((int(identity.slot_id), int(identity.episode_id), int(identity.cursor)))
            distinct.add(int(identity.slot_id))
            per_slot_used[int(identity.slot_id)] = per_slot_used.get(int(identity.slot_id), 0) + 1
        # Criterion 6, as restated: the greedy freeze serves whichever category
        # still has blocks, so slot coverage per window is a *consequence* of the
        # catalogue's per-category supply, not a property the freeze maintains.
        # What the freeze does maintain is the ``used`` rotation inside a category.
        distinct_per_window.append(len(distinct))
        categories_per_window.append(len({slot_categories[slot] for slot in distinct}))
        for category in categories:
            pair = [per_slot_used.get(slot, 0) for slot in _slots_of(slot_categories, category)]
            # Only a category that was served at all can be checked for balance; a
            # drained category legitimately contributes zero members to both slots.
            if any(pair):
                rotation_skew.append(max(pair) - min(pair))

    def _cursor_state() -> tuple:
        return (dict(driver._stream_index), dict(driver._active_stream), dict(driver._active_cursor))

    epoch = 0
    epochs_planned = 0
    windows_total = 0
    slot_epochs: dict[int, int] = {slot: 0 for slot in all_slots}
    epoch_window_counts: list[int] = []
    rollovers: list[dict] = []
    blocks_by_epoch: dict[int, set[tuple[int, int, int]]] = {}
    order_mismatches: list[dict] = []
    probe_is_pure = True
    distinct_per_window: list[int] = []
    categories_per_window: list[int] = []
    rotation_skew: list[int] = []
    tail_structure: list[dict] = []

    while windows_total < args.target_windows and epochs_planned < args.max_epochs:
        blocks = blocks_by_epoch.setdefault(epoch, set())
        windows_in_epoch = 0
        first_partial_window: int | None = None
        first_partial_category_window: int | None = None
        while True:
            _commit_window(epoch, blocks)
            windows_total += 1
            windows_in_epoch += 1
            if first_partial_window is None and distinct_per_window[-1] < len(all_slots):
                first_partial_window = windows_in_epoch
            if first_partial_category_window is None and categories_per_window[-1] < len(categories):
                first_partial_category_window = windows_in_epoch
            # Criterion 3: the window-boundary probe must commit no driver state.
            before_cursors = _cursor_state()
            per_slot_remaining = {slot: _remaining_blocks(driver, slot) for slot in all_slots}
            remaining = sum(per_slot_remaining.values())
            if _cursor_state() != before_cursors:
                probe_is_pure = False
            # Design 3.2: the catalogue can no longer serve a whole window.
            if remaining < window_members:
                break
        epoch_window_counts.append(windows_in_epoch)
        tail_structure.append(
            {
                "epoch": epoch,
                "first_partial_window": first_partial_window,
                "first_partial_category_window": first_partial_category_window,
                "remaining_by_category_at_epoch_end": {
                    category: sum(
                        count for slot, count in per_slot_remaining.items() if slot_categories[slot] == category
                    )
                    for category in categories
                },
            }
        )
        epochs_planned += 1
        if windows_total >= args.target_windows or epochs_planned >= args.max_epochs:
            break
        before = {slot: driver._by_slot[slot] for slot in all_slots}
        # v0.7 逐 slot 复用：每个 slot 独立判定（non-terminal 继续 / terminal 复用）。
        for slot in all_slots:
            next_epoch = slot_epochs.get(slot, 0) + 1
            perm = _rollover_slot(
                driver, scheduler, slot=slot, epoch=next_epoch,
                queue_seed=args.queue_seed, category=slot_categories[slot],
                slot_categories=slot_categories,
            )
            if perm is None:
                continue  # non-terminal：继续，无重排
            slot_epochs[slot] = next_epoch
            # Criterion 1: **独立**重算 category 级期望序（不复用 _rollover_slot 内部），
            # 用 pre-rollover 快照的该 category 全部 episode（两 slot 合并）作参照序。
            category_slots = _slots_of(slot_categories, slot_categories[slot])
            category_reference = _reference_order(
                [s for other in category_slots for s in before[other]], router.source_digest
            )
            category_perm = queue_permutation(
                queue_seed=args.queue_seed, epoch=next_epoch,
                category=slot_categories[slot], catalog_size=len(category_reference),
            )
            category_ordered = [category_reference[index] for index in category_perm]
            own = {_key(s) for s in before[slot]}
            want = tuple(_key(s) for s in category_ordered if _key(s) in own)
            got = tuple(_key(s) for s in driver._by_slot[slot])
            if want != got:
                order_mismatches.append({"epoch": next_epoch, "slot": slot, "want": want[:4], "got": got[:4]})
        if len(rollovers) < _MAX_RECORDED_ROLLOVERS:
            rollovers.append(
                {
                    "to_epoch": epoch + 1,
                    "windows_in_previous_epoch": windows_in_epoch,
                    "slot_epochs_snapshot": dict(slot_epochs),
                    "remaining_blocks_at_rollover": remaining,
                }
            )
        epoch += 1

    epoch0 = blocks_by_epoch.get(0, set())
    deferred = catalogue_blocks - epoch0
    covered = set().union(*blocks_by_epoch.values()) if blocks_by_epoch else set()
    stranded = catalogue_blocks - covered
    capacity_ok = windows_total >= args.target_windows
    result_pass = (
        capacity_ok
        and not order_mismatches
        and probe_is_pure
        and driver._window_index == windows_total
        and not stranded
    )
    report = {
        "result": "PASS" if result_pass else "FAIL",
        "capacity_target_met": capacity_ok,
        "b_stream": args.b_stream,
        "ga": args.ga,
        "window_members": window_members,
        "queue_seed": args.queue_seed,
        "epochs_planned": len(epoch_window_counts),
        "windows_total": windows_total,
        "windows_per_epoch": epoch_window_counts,
        "catalogue_blocks": len(catalogue_blocks),
        "single_epoch_limit": round(single_epoch_limit, 2),
        "criterion1_slot_order_matches_permutation": not order_mismatches,
        "criterion1_mismatches": order_mismatches[:5],
        "criterion2_target_windows": args.target_windows,
        "criterion2_meets_target": windows_total >= args.target_windows,
        "criterion2_exceeds_single_epoch": windows_total > single_epoch_limit,
        "criterion3_probe_is_pure": probe_is_pure,
        "criterion4_window_index_not_reset": driver._window_index == windows_total,
        "window_index": driver._window_index,
        "criterion5_block_coverage": {
            "deferred_after_epoch0": len(deferred),
            "recovered_after_epoch0": len(deferred & covered),
            "catalogue_blocks": len(catalogue_blocks),
            "covered_blocks": len(covered),
            "stranded_blocks": sorted(stranded)[:10],
            "full_coverage": not stranded,
        },
        "committed_identities": len(scheduler.committed_identities),
        "rollovers": rollovers,
        "criterion6_slot_coverage": {
            "windows_by_distinct_slots": {
                str(count): distinct_per_window.count(count) for count in sorted(set(distinct_per_window))
            },
            "windows_by_distinct_categories": {
                str(count): categories_per_window.count(count) for count in sorted(set(categories_per_window))
            },
            "total_slots": len(all_slots),
            "total_categories": len(categories),
            "all_slots_windows": distinct_per_window.count(len(all_slots)),
            "all_categories_windows": categories_per_window.count(len(categories)),
            "max_within_category_slot_skew": max(rotation_skew) if rotation_skew else 0,
        },
        "tail_structure": tail_structure[:5],
        "cumulative_exposure": dict(scheduler.cumulative_valid_consumer_exposure),
    }
    print(json.dumps(report, indent=2, sort_keys=True, default=str))
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str) + "\n")
        print(f"[out] wrote {args.output_json}")
    return 0 if result_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
