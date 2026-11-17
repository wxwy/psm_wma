"""Strict final-source v2 offline inspection; never constructs a VAE."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.latent_cache import final_source as final
from g2.latent_cache.builder import verify_episode
from g2.latent_cache.contract import CacheError
from g2.offline.source_capacity import episode_bytes
from g2.offline.stage_a import validate_profile_episode


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--episode-root", type=Path, required=True)
    p.add_argument("--recipe-id")
    p.add_argument("--file-bytes", action="store_true")
    args = p.parse_args(argv)
    try:
        manifest = validate_profile_episode(args.episode_root)
        if manifest["schema"] != final.PROFILE_SCHEMA:
            raise CacheError(
                "strict v2 verification does not relabel a legacy/working package"
            )
        audit = verify_episode(args.episode_root, expected_recipe_id=args.recipe_id)
        result = dict(
            schema=final.CAPSULE_SCHEMA,
            profile_complete=True,
            working_source_retired=True,
            cache=audit,
            capacity=episode_bytes(args.episode_root, include_files=args.file_bytes),
            training_ready=False,
        )
        print(json.dumps(result, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REJECTED", error=str(exc)), sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
