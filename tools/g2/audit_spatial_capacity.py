"""Read-only corpus bytes/stratification; output must be outside inputs and Git."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.latent_cache.contract import CacheError
from g2.latent_cache.retirement_policy import overlap, real_path
from g2.latent_cache.storage import atomic_json
from g2.offline.source_capacity import capacity_report, corpus_bytes


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--old-root", type=Path, required=True)
    p.add_argument("--new-root", type=Path)
    p.add_argument("--available-bytes", type=int)
    p.add_argument("--reserve-bytes", type=int, default=8 * 1024**3)
    p.add_argument("--expected-episodes", type=int, default=9126)
    p.add_argument("--expected-tasks", type=int, default=18)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        out = real_path(str(args.output.absolute()))
        for root in (args.old_root, args.new_root, Path(__file__).resolve().parents[2]):
            if root is not None and overlap(out, root.resolve()):
                raise CacheError(
                    "capacity report must be outside input datasets and tracked source"
                )
        if args.new_root is not None:
            if args.available_bytes is None:
                raise CacheError("explicit capacity scenario bytes required")
            report = capacity_report(
                args.old_root,
                args.new_root,
                available_bytes=args.available_bytes,
                reserve_bytes=args.reserve_bytes,
                expected_episodes=args.expected_episodes,
                expected_tasks=args.expected_tasks,
            )
        else:
            report = corpus_bytes(args.old_root)
        atomic_json(out, report)
        print(
            json.dumps(
                dict(
                    output=str(out),
                    verdict=report.get("verdict", "READ_ONLY_COUNTS"),
                    production_started=False,
                ),
                sort_keys=True,
            )
        )
        return 75 if report.get("verdict") == "HOLD_CAPACITY" else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REJECTED", error=str(exc))))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
