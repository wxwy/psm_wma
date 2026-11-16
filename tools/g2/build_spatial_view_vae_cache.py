"""Plan or explicitly build independent G2 spatial-View Encode1 caches.

Run from the PSM-WMA root with ``python -m tools.g2.build_spatial_view_vae_cache``.
Planning hashes local dependencies and PNG owners but never instantiates a VAE.
Real encoding is a separate, explicitly selected action, not authorized by the
Issue52 code/CPU implementation itself.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--dataset-root",
        type=Path,
        required=True,
        help="existing G2 root containing tasks/<task>/episodes/episode_<id>",
    )
    result.add_argument(
        "--task",
        action="append",
        default=None,
        help="repeat to select task classes; omitted means all",
    )
    result.add_argument(
        "--episode",
        type=int,
        action="append",
        default=None,
        help="repeat to select global episode IDs",
    )
    result.add_argument(
        "--weights",
        type=Path,
        required=True,
        help="existing local Wan VAE weight file; never downloaded",
    )
    result.add_argument(
        "--expected-weights-sha256",
        help="optional expected fingerprint, checked before any encoding",
    )
    result.add_argument(
        "--cosmos-root",
        type=Path,
        help="local fixed Cosmos checkout; default is Root/cosmos-framework",
    )
    result.add_argument(
        "--device",
        default="cuda",
        help="cpu, cuda or cuda:<index>; dry-run does not initialize it",
    )
    result.add_argument(
        "--height",
        type=int,
        default=256,
        help="candidate canvas height, not a production configuration freeze",
    )
    result.add_argument(
        "--width",
        type=int,
        default=256,
        help="candidate canvas width, not a production configuration freeze",
    )
    result.add_argument(
        "--interpolation", choices=("lanczos", "bilinear", "nearest"), default="lanczos"
    )
    result.add_argument(
        "--storage-dtype",
        choices=("float32", "float16", "bfloat16"),
        default="float32",
        help="FP32 is the initial baseline; low precision requires its own real Gate",
    )
    result.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="this candidate supports B=1 only; mixed-batch real parity is NOT_RUN",
    )
    result.add_argument(
        "--resume",
        action="store_true",
        help="reuse only complete per-view files with identical source and recipe",
    )
    action = result.add_mutually_exclusive_group(required=True)
    action.add_argument(
        "--dry-run",
        "--plan",
        dest="dry_run",
        action="store_true",
        help="report every valid View/owner/ref and output path; do not create cache",
    )
    action.add_argument(
        "--execute",
        action="store_true",
        help="actually encode; use only after separate real-VAE execution authorization",
    )
    return result


def main(argv=None):
    command = parser()
    args = command.parse_args(argv)
    if args.batch_size != 1:
        command.error(
            "this candidate supports independent B=1 only; mixed-batch parity is NOT_RUN"
        )
    try:
        from g2.latent_cache.builder import (
            build_episode,
            discover_episodes,
            plan_episode,
        )
        from g2.latent_cache.contract import make_recipe, preprocessing_recipe
        from g2.latent_cache.encoding import WanSingleFrameEncoder, validate_wan_canvas

        validate_wan_canvas(args.height, args.width)
        preprocessing = preprocessing_recipe(
            args.height, args.width, args.interpolation
        )
        encoder = WanSingleFrameEncoder(
            args.weights, device=args.device, cosmos_root=args.cosmos_root
        )
        identity = encoder.descriptor()
        if (
            args.expected_weights_sha256 is not None
            and identity["weights_sha256"] != args.expected_weights_sha256
        ):
            raise ValueError("local VAE weights differ from --expected-weights-sha256")
        recipe = make_recipe(
            identity,
            preprocessing,
            storage_dtype=args.storage_dtype,
            batch_size=args.batch_size,
        )
        episodes = discover_episodes(
            args.dataset_root, tasks=args.task, episodes=args.episode
        )
        results = []
        for episode in episodes:
            if args.dry_run:
                results.append(plan_episode(episode, recipe))
            else:
                results.append(
                    build_episode(
                        episode,
                        encoder,
                        preprocessing=preprocessing,
                        storage_dtype=args.storage_dtype,
                        batch_size=args.batch_size,
                        resume=args.resume,
                    )
                )
        report = dict(
            schema="g2_spatial_view_vae_cli_v1",
            action="plan" if args.dry_run else "build",
            episode_count=len(results),
            results=results,
            production_configuration_frozen=False,
        )
        if args.dry_run:
            report.update(vae_loaded=False, gpu_accessed=False, cache_written=False)
        print(json.dumps(report, sort_keys=True, ensure_ascii=False, allow_nan=False))
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(
            json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
