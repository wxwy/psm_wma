"""Resume an already acknowledged owned source transaction; no render/encode."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.latent_cache.contract import CacheError
from g2.latent_cache.streaming import EventSpool


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spool-root", type=Path, required=True)
    p.add_argument("--job-id", required=True)
    p.add_argument("--execute", action="store_true")
    args = p.parse_args(argv)
    try:
        if not args.execute:
            raise CacheError("explicit --execute required to resume retirement")
        spool = EventSpool.open(args.spool_root)
        if spool.source_policy is None:
            raise CacheError("working-v1 spool has no source retirement authority")
        done = spool.reap(args.job_id)
        print(
            json.dumps(
                dict(
                    job_id=args.job_id, retirement_complete=done, training_ready=False
                ),
                sort_keys=True,
            )
        )
        return 0 if done else 75
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REJECTED", error=str(exc)), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
