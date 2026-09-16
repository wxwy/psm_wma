"""How many optimizer steps can the production segment catalogue actually serve?

The active Local-Memory route draws every training member from a frozen window
plan built out of the episode catalogue, and it consumes that catalogue
monotonically: ``_peek_block`` advances a per-slot cursor and only leaves a
stream once ``cursor == blocks - 1``, while ``_commit_block`` never rewinds.
A window is ``grad_accum_iter`` members and each member takes exactly one whole
block, so

    steps_served = total_blocks / grad_accum_iter

and once every slot is drained ``freeze_window`` raises
``RuntimeError("active Local window exhausted every segment stream")``.  The
catalogue is built once in ``on_train_start`` and never rebuilt, so this is a
hard ceiling on the whole run rather than a per-epoch budget.

``block_count`` is ``valid_start_count // ttt_tbptt_steps``
(``canonical_local_memory_producer.py:113-115``), i.e. one block is one T-frame
training segment, so the ceiling is a property of the dataset plus the TBPTT
width and cannot be raised by scheduler or driver behaviour.

This probe measures it directly on the real datasets and producers instead of
inferring it.  It is CPU-only and loads no latents: only the parquet frame index
and the per-episode block counts are touched.

Run (roots come from the environment, as in ``probe_r09_b_active_static``):

    LIBERO_ROOT=... LIBERO_LATENT_CACHE_ROOT=... \
        python tools/g0/probe_block_capacity.py \
        --output-json artifacts/g0/active_static_probe/probe_block_capacity.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "cosmos-framework"))

from probe_r09_b_active_static import SUITES, _build_dataset  # noqa: E402

from cosmos_framework.data.generator.action.datasets.canonical_local_memory_producer import (  # noqa: E402
    CanonicalLocalMemorySegmentProducer,
)
from cosmos_framework.model.generator.mot.active_local_memory_launch import (  # noqa: E402
    canonical_segment_streams,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-json", type=Path, default=None)
    parser.add_argument("--b-stream", type=int, default=8)
    parser.add_argument("--ga", type=int, default=16, help="window size = b_stream * ga")
    parser.add_argument("--ttt-tbptt-steps", type=int, default=16)
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
            suite,
            libero_root=libero_root,
            cache_root=cache_root,
            max_episodes=args.max_episodes,
        )
        producers[suite] = CanonicalLocalMemorySegmentProducer(
            dataset,
            category=suite,
            ttt_tbptt_steps=args.ttt_tbptt_steps,
            manifest_digest="capacity-probe",
            config_digest="capacity-probe",
            source_digest=cache_root,
        )

    streams = canonical_segment_streams(producers, b_stream=args.b_stream)

    per_slot_blocks: dict[int, int] = {}
    per_slot_streams: dict[int, int] = {}
    per_category_blocks: dict[str, int] = {}
    for stream in streams:
        blocks = int(producers[stream.category].block_count(stream))
        per_slot_blocks[stream.slot_id] = per_slot_blocks.get(stream.slot_id, 0) + blocks
        per_slot_streams[stream.slot_id] = per_slot_streams.get(stream.slot_id, 0) + 1
        per_category_blocks[stream.category] = per_category_blocks.get(stream.category, 0) + blocks

    total_blocks = sum(per_slot_blocks.values())
    slots = len(per_slot_blocks)
    # Windows are filled to the per-category quota, so a category whose slots are
    # thin relative to its share drains before the catalogue as a whole does.
    per_category_share = window_members / len(per_category_blocks)
    per_category_windows = {
        category: round(blocks / per_category_share, 2)
        for category, blocks in per_category_blocks.items()
    }

    report = {
        "result": "PASS",
        "b_stream": args.b_stream,
        "ga": args.ga,
        "window_members": window_members,
        "ttt_tbptt_steps": args.ttt_tbptt_steps,
        "streams": len(streams),
        "slots": slots,
        "per_slot_streams": {str(k): per_slot_streams[k] for k in sorted(per_slot_streams)},
        "per_slot_blocks": {str(k): per_slot_blocks[k] for k in sorted(per_slot_blocks)},
        "per_category_blocks": {k: per_category_blocks[k] for k in sorted(per_category_blocks)},
        "total_blocks": total_blocks,
        "windows_served": round(total_blocks / window_members, 2),
        "per_category_windows": {k: per_category_windows[k] for k in sorted(per_category_windows)},
        "min_slot_blocks": min(per_slot_blocks.values()),
        "windows_until_first_slot_drained": round(
            min(per_slot_blocks.values()) / (window_members / slots), 2
        ),
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    if args.output_json is not None:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(f"[out] wrote {args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
