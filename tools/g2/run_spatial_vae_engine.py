"""Shared true B1..32/T1 multi-GPU engine, independent or producer-fed.

Planning computes source/weight/recipe identity without constructing Wan.
Independent mode watches published episodes; sync mode serves final-pixel events.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("independent", "sync"), required=True)
    p.add_argument("--spool-root", type=Path, required=True)
    p.add_argument("--dataset-root", type=Path)
    p.add_argument("--weights", type=Path, required=True)
    p.add_argument("--cosmos-root", type=Path)
    p.add_argument("--task", action="append")
    p.add_argument("--episode", type=int, action="append")
    p.add_argument("--engine-config", type=Path)
    p.add_argument("--gpus", default=None, help="physical indices, default4,5,6,7")
    p.add_argument("--max-batch-size", type=int)
    p.add_argument(
        "--finalize-workers",
        type=int,
        default=0,
        help="CPU-only independent posthoc Episode finalizers (0=original serial)",
    )
    p.add_argument("--max-wait-ms", type=float)
    p.add_argument("--idle-timeout-s", type=float)
    p.add_argument("--max-events", type=int, default=512)
    p.add_argument("--max-spool-bytes", type=int, default=512 * 1024**2)
    p.add_argument("--max-result-bytes", type=int, default=4 * 1024**3)
    p.add_argument("--max-records", type=int, default=100000)
    p.add_argument("--source-policy", type=Path)
    p.add_argument("--stop-file", type=Path)
    p.add_argument("--expected-episodes", type=Path)
    p.add_argument("--producer-done", type=Path)
    p.add_argument("--expected-recipe-id")
    p.add_argument("--expected-weights-sha256")
    p.add_argument("--resume", action="store_true")
    p.add_argument("--serve", action="store_true", help="sync lifecycle (no idle exit)")
    p.add_argument(
        "--isolated-test",
        action="store_true",
        help="permit explicit one-shot crash injection in a separate sample",
    )
    action = p.add_mutually_exclusive_group(required=True)
    action.add_argument("--plan", "--dry-run", dest="plan", action="store_true")
    action.add_argument("--initialize", action="store_true")
    action.add_argument("--execute", action="store_true")
    return p


def main(argv=None):
    p = parser()
    a = p.parse_args(argv)
    try:
        from g2.io import read_json
        from g2.latent_cache.batch_contract import make_batch_recipe
        from g2.latent_cache.batch_encoding import WanBatchEncoder
        from g2.latent_cache.batch_engine import BatchEngine, engine_config, initialize
        from g2.latent_cache.contract import CacheError
        from g2.latent_cache.streaming import ConsumerLimits

        if not 0 <= a.finalize_workers <= 8 or (
            a.mode != "independent" and a.finalize_workers
        ):
            raise ValueError("finalize-workers must be 0..8, independent-only")
        cfg = read_json(a.engine_config) if a.engine_config else {}
        for key, value in (
            (
                "gpus",
                [int(g) for g in a.gpus.split(",")] if a.gpus is not None else None,
            ),
            ("max_batch_size_per_gpu", a.max_batch_size),
            ("batch_wait_ms", a.max_wait_ms),
            ("idle_timeout_s", a.idle_timeout_s),
        ):
            if value is not None:
                cfg[key] = value
        cfg = engine_config(cfg, allow_test=a.isolated_test)
        os.environ["CUDA_VISIBLE_DEVICES"] = ",".join(map(str, cfg["gpus"]))
        if a.mode == "independent" and (
            a.dataset_root is None or a.serve or a.source_policy
        ):
            raise CacheError(
                "independent mode needs a published dataset, with explicit separate Stage C"
            )
        if a.mode == "sync" and (
            a.dataset_root or a.expected_episodes or a.producer_done
        ):
            raise CacheError(
                "sync uses producer events and supervisor completion, not discovery"
            )
        cosmos = (
            a.cosmos_root or Path(__file__).resolve().parents[2] / "cosmos-framework"
        )
        encoder = WanBatchEncoder(
            a.weights,
            cosmos_root=cosmos,
            device="cuda:0",
            max_batch_size=cfg["max_batch_size_per_gpu"],
        )
        recipe = make_batch_recipe(
            encoder.descriptor(), max_batch_size=cfg["max_batch_size_per_gpu"]
        )
        if a.expected_recipe_id and recipe["recipe_id"] != a.expected_recipe_id:
            raise CacheError("batch recipe differs from the pinned recipe")
        if (
            a.expected_weights_sha256
            and recipe["encoder"]["legacy_loader"]["weights_sha256"]
            != a.expected_weights_sha256
        ):
            raise CacheError("local weights differ from the pinned hash")
        if a.plan:
            print(
                json.dumps(
                    dict(
                        schema="g2_multigpu_batch_engine_plan_v1",
                        mode=a.mode,
                        finalize_workers=a.finalize_workers,
                        config=cfg,
                        recipe=recipe,
                        model_loaded=False,
                        production_started=False,
                        training_ready=False,
                    ),
                    sort_keys=True,
                )
            )
            return 0
        policy = read_json(a.source_policy) if a.source_policy else None
        spool, spec = initialize(
            a.spool_root,
            weights=a.weights,
            cosmos_root=cosmos,
            config=cfg,
            source_policy=policy,
            lifecycle="view_first_posthoc_v1"
            if a.mode == "independent"
            else "streaming_v1",
            limits=ConsumerLimits(a.max_events, a.max_spool_bytes),
            max_result_bytes=a.max_result_bytes,
            max_records=a.max_records,
            allow_test=a.isolated_test,
        )
        if a.initialize:
            print(
                json.dumps(
                    dict(
                        initialized=True,
                        recipe_id=spool.recipe["recipe_id"],
                        model_loaded=False,
                    ),
                    sort_keys=True,
                )
            )
            return 0
        engine = BatchEngine(
            spool,
            spec,
            mode=a.mode,
            dataset_root=a.dataset_root,
            tasks=a.task,
            episodes=a.episode,
            stop_file=a.stop_file,
            expected=a.expected_episodes,
            producer_done=a.producer_done,
            resume=a.resume,
            finalize_workers=a.finalize_workers,
        )
        result = engine.run()
        print(json.dumps(result, sort_keys=True))
        return 75 if result["status"] == "PAUSED" else 0
    except (ValueError, OSError, RuntimeError, KeyError, TypeError) as exc:
        print(
            json.dumps(dict(error=str(exc), complete=False, source_retained=True)),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
