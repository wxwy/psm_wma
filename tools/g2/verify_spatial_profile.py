"""Validate only the new Stage-A producer protocol; never loads a VAE."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from g2.io import ContractError, read_json
from g2.offline.output_profile import OutputProfile
from g2.offline.stage_a import validate_profile_episode


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode-root", type=Path, required=True)
    parser.add_argument("--output-profile", type=Path)
    parser.add_argument(
        "--allow-source-ready",
        action="store_true",
        help="accept sealed source for inspection; exit 75 if VAE is pending",
    )
    args = parser.parse_args(argv)
    try:
        expected = (
            OutputProfile.from_dict(read_json(args.output_profile))
            if args.output_profile
            else None
        )
        result = validate_profile_episode(
            args.episode_root,
            expected_profile=expected,
            require_complete=not args.allow_source_ready,
        )
    except (ContractError, ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps(dict(status="REJECTED", error=str(exc)), sort_keys=True))
        return 2
    print(
        json.dumps(
            dict(
                schema=result["schema"],
                episode_id=result["episode_id"],
                source_id=result["source_id"],
                source_ready=result["source_ready"],
                profile_complete=result["profile_complete"],
                pending=result["pending"],
                training_ready=False,
            ),
            sort_keys=True,
        )
    )
    return 0 if result["profile_complete"] else 75


if __name__ == "__main__":
    raise SystemExit(main())
