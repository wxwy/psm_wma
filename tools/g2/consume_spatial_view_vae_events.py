"""Independent bounded Stage-A event consumer; one resident B=1 Encode1 model.

--initialize only writes a recipe-bound spool; it does not load model weights.
--execute is an explicit real-VAE action requiring separate execution approval.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--spool-root", type=Path, required=True)
    p.add_argument("--weights", type=Path, required=True)
    p.add_argument("--expected-recipe-id")
    p.add_argument(
        "--source-policy",
        type=Path,
        help="explicit new-output v2 source-retirement policy JSON",
    )
    p.add_argument("--cosmos-root", type=Path)
    p.add_argument("--device", default="cuda")
    p.add_argument("--height", type=int, default=256)
    p.add_argument("--width", type=int, default=256)
    p.add_argument(
        "--interpolation", choices=("lanczos", "bilinear", "nearest"), default="lanczos"
    )
    p.add_argument(
        "--storage-dtype", choices=("float32", "float16", "bfloat16"), default="float32"
    )
    p.add_argument("--max-events", type=int, default=32)
    p.add_argument("--max-spool-bytes", type=int, default=256 * 1024**2)
    p.add_argument("--max-result-bytes", type=int, default=4 * 1024**3)
    p.add_argument(
        "--max-records",
        type=int,
        default=100000,
        help="active event/job working-set budget, not a lifetime limit",
    )
    p.add_argument(
        "--idle-seconds",
        type=float,
        default=60,
        help="finite exit timeout when no work remains",
    )
    p.add_argument(
        "--serve",
        action="store_true",
        help="stay alive through long GT/render gaps; supervisor stops via stop-file",
    )
    p.add_argument("--stop-file", type=Path)
    p.add_argument(
        "--retry-job",
        action="append",
        default=[],
        help="explicitly retry retained failed inputs",
    )
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--initialize", action="store_true")
    action.add_argument("--execute", action="store_true")
    action.add_argument(
        "--once", action="store_true", help="execute at most one encode/finalize step"
    )
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        import math

        from g2.io import read_json

        if not math.isfinite(args.idle_seconds) or args.idle_seconds < 0:
            raise ValueError("finite nonnegative idle timeout required")
        from g2.latent_cache.contract import make_recipe, preprocessing_recipe
        from g2.latent_cache.encoding import WanSingleFrameEncoder, validate_wan_canvas
        from g2.latent_cache.streaming import ConsumerLimits, EventConsumer, EventSpool

        validate_wan_canvas(args.height, args.width)
        encoder = WanSingleFrameEncoder(
            args.weights, device=args.device, cosmos_root=args.cosmos_root
        )
        recipe = make_recipe(
            encoder.descriptor(),
            preprocessing_recipe(args.height, args.width, args.interpolation),
            storage_dtype=args.storage_dtype,
        )
        if (
            args.expected_recipe_id is not None
            and recipe["recipe_id"] != args.expected_recipe_id
        ):
            raise ValueError("consumer environment/recipe differs from approved run")
        spool = EventSpool(
            args.spool_root,
            recipe,
            limits=ConsumerLimits(args.max_events, args.max_spool_bytes),
            max_result_bytes=args.max_result_bytes,
            max_records=args.max_records,
            source_policy=read_json(args.source_policy)
            if args.source_policy is not None
            else None,
        )
        steps = 0
        recovery = None
        if not args.initialize:
            from g2.latent_cache.storage import build_lock

            consumer = EventConsumer(spool, encoder)
            with build_lock(spool.root / "consumer"):
                recovery = consumer.recover_results()
                for job in args.retry_job:
                    spool.retry(job)
                deadline = time.monotonic() + args.idle_seconds
                while True:
                    if args.stop_file is not None and args.stop_file.exists():
                        break
                    if consumer._step():
                        steps += 1
                        deadline = time.monotonic() + args.idle_seconds
                    elif not args.serve and time.monotonic() >= deadline:
                        break
                    else:
                        time.sleep(0.05)
                    if args.once:
                        break
        stats = spool.stats()
        print(
            json.dumps(
                dict(
                    schema="g2_vae_consumer_receipt_v1",
                    recipe_id=recipe["recipe_id"],
                    initialized=True,
                    recovery=recovery,
                    steps=steps,
                    stats=stats,
                    model_loaded=getattr(encoder, "_tokenizer", None) is not None,
                    production_configuration_frozen=False,
                ),
                sort_keys=True,
            )
        )
        return (
            0
            if args.initialize
            else 2
            if stats["failed_jobs"]
            else 75
            if stats["unfinished_jobs"] or stats["active_jobs"]
            else 0
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps(dict(status="ERROR", error=str(exc))), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
