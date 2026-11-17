"""Read-only verification of completed per-View G2 VAE caches.

Ordinary verification does not import the VAE adapter or load weights. Optional
re-encoding is a separately requested real-VAE operation, not a CPU-test claim.
Run as ``python -m tools.g2.verify_spatial_view_vae_cache`` from the Root checkout.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--dataset-root", type=Path, required=True)
    result.add_argument("--task", action="append", default=None)
    result.add_argument(
        "--episode",
        type=int,
        action="append",
        default=None,
        help="global episode ID; repeat for an explicit selection",
    )
    result.add_argument(
        "--recipe-id", help="require an exact sealed recipe fingerprint"
    )
    result.add_argument(
        "--skip-source",
        action="store_true",
        help="audit cache files only; omit the full source-PNG rehash",
    )
    result.add_argument(
        "--reencode",
        action="store_true",
        help="explicitly load a real VAE and compare each physical owner again",
    )
    result.add_argument(
        "--weights", type=Path, help="required local weights for --reencode only"
    )
    result.add_argument("--expected-weights-sha256")
    result.add_argument("--cosmos-root", type=Path)
    result.add_argument("--device", default="cuda")
    result.add_argument(
        "--atol",
        type=float,
        default=0.0,
        help="explicit re-encode absolute tolerance; default strict zero",
    )
    result.add_argument(
        "--rtol",
        type=float,
        default=0.0,
        help="explicit re-encode relative tolerance; default strict zero",
    )
    return result


def main(argv=None):
    command = parser()
    args = command.parse_args(argv)
    if args.reencode and args.weights is None:
        command.error("--reencode requires --weights")
    if not args.reencode and (
        args.weights is not None
        or args.expected_weights_sha256 is not None
        or args.cosmos_root is not None
        or args.atol != 0
        or args.rtol != 0
    ):
        command.error(
            "weights/model/tolerance options require --reencode; use --recipe-id for read-only matching"
        )
    if any(not math.isfinite(x) or x < 0 for x in (args.atol, args.rtol)):
        command.error("re-encode tolerances must be finite and nonnegative")
    try:
        from g2.latent_cache.builder import discover_episodes, verify_episode

        encoder = None
        if args.reencode:
            from g2.latent_cache.encoding import WanSingleFrameEncoder

            encoder = WanSingleFrameEncoder(
                args.weights, device=args.device, cosmos_root=args.cosmos_root
            )
            if (
                args.expected_weights_sha256 is not None
                and encoder.descriptor()["weights_sha256"]
                != args.expected_weights_sha256
            ):
                raise ValueError(
                    "local VAE weights differ from --expected-weights-sha256"
                )
        episodes = discover_episodes(
            args.dataset_root, tasks=args.task, episodes=args.episode
        )
        reports = [
            verify_episode(
                episode,
                expected_recipe_id=args.recipe_id,
                check_source=not args.skip_source,
                reencoder=encoder,
                atol=args.atol,
                rtol=args.rtol,
            )
            for episode in episodes
        ]
        print(
            json.dumps(
                dict(
                    schema="g2_spatial_view_vae_verify_cli_v1",
                    action="verify_reencode" if args.reencode else "verify",
                    episode_count=len(reports),
                    results=reports,
                ),
                sort_keys=True,
                ensure_ascii=False,
                allow_nan=False,
            )
        )
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        print(
            json.dumps({"status": "ERROR", "error": str(error)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
