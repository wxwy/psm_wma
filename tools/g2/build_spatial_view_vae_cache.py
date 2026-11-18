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
        default=None,
        help="legacy defaults B=1; explicit batch engine defaults maximum B=32 per GPU",
    )
    result.add_argument("--engine", choices=("legacy", "batch"), default="legacy")
    result.add_argument("--engine-config", type=Path)
    result.add_argument("--gpus", default=None)
    result.add_argument("--max-wait-ms", type=float)
    result.add_argument("--idle-timeout-s", type=float)
    result.add_argument("--expected-episodes", type=Path)
    result.add_argument("--producer-done", type=Path)
    result.add_argument(
        "--resume",
        action="store_true",
        help="reuse only complete per-view files with identical source and recipe",
    )
    result.add_argument(
        "--view-first",
        action="store_true",
        help="explicit posthoc lifecycle; original published View profile remains unchanged",
    )
    result.add_argument(
        "--spool-root",
        type=Path,
        help="new external bounded posthoc record spool; required for View-first execute",
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
    if args.batch_size is None:
        args.batch_size = 32 if args.engine == "batch" else 1
    if args.engine == "batch":
        if (
            not args.view_first
            or args.spool_root is None
            or args.height != 256
            or args.width != 256
            or args.storage_dtype != "float32"
            or args.interpolation != "lanczos"
        ):
            command.error(
                "batch mode requires explicit View-first/spool and256/FP32/lanczos"
            )
        from tools.g2.run_spatial_vae_engine import main as batch_main

        forward = [
            "--mode",
            "independent",
            "--spool-root",
            str(args.spool_root),
            "--dataset-root",
            str(args.dataset_root),
            "--weights",
            str(args.weights),
            "--max-batch-size",
            str(args.batch_size),
            "--plan" if args.dry_run else "--execute",
        ]
        for flag, val in (
            ("--cosmos-root", args.cosmos_root),
            ("--engine-config", args.engine_config),
            ("--gpus", args.gpus),
            ("--max-wait-ms", args.max_wait_ms),
            ("--idle-timeout-s", args.idle_timeout_s),
            ("--expected-episodes", args.expected_episodes),
            ("--producer-done", args.producer_done),
            ("--expected-weights-sha256", args.expected_weights_sha256),
        ):
            if val is not None:
                forward += [flag, str(val)]
        for flag, items in (("--task", args.task), ("--episode", args.episode)):
            for val in items or []:
                forward += [flag, str(val)]
        if args.resume:
            forward.append("--resume")
        return batch_main(forward)
    if args.batch_size != 1:
        command.error(
            "this candidate supports independent B=1 only; mixed-batch parity is NOT_RUN"
        )
    if args.view_first and args.execute and args.spool_root is None:
        command.error("--view-first --execute requires a separate --spool-root")
    if args.spool_root is not None and not args.view_first:
        command.error("--spool-root here requires explicit --view-first")
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
                results.append(
                    plan_episode(episode, recipe, view_first=True)
                    if args.view_first
                    else plan_episode(episode, recipe)
                )
            elif args.view_first:
                from g2.latent_cache.posthoc import build_view_first_cache

                results.append(
                    build_view_first_cache(
                        episode,
                        encoder,
                        spool_root=args.spool_root,
                        preprocessing=preprocessing,
                        storage_dtype=args.storage_dtype,
                        resume=args.resume,
                    )
                )
            else:
                from g2.latent_cache.production import build_profile
                from g2.latent_cache.sealed_source import is_sealed

                build = build_profile if is_sealed(episode) else build_episode
                results.append(
                    build(
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
        return 75 if any(row.get("pending") for row in results) else 0
    except (OSError, ValueError, RuntimeError) as error:
        print(
            json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
