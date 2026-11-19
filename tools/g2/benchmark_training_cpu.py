"""Bounded Issue #90 probes for DATA_C, CAP2, and cached pixel geometry.

The provider experiment exercises the selected certified reads with isolated
providers and preserves the submitted order. It excludes G1 raw/cache reads and
does not reproduce Phase5 worker dispatch. CAP2 compares tokenizer outputs with
the existing Child memoizer, with the same main-thread CFG draws. Geometry uses
a synthetic latent and the two native cached-video resize paths.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import resource
import threading
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields, is_dataclass
from pathlib import Path
from queue import SimpleQueue
from time import perf_counter, process_time
from types import SimpleNamespace

from g2.latent_cache.storage import tensor_sha256


def _digest(value):
    import torch

    def encode(item):
        if isinstance(item, torch.Tensor):
            return {
                "dtype": str(item.dtype),
                "shape": list(item.shape),
                "sha256": tensor_sha256(item),
            }
        if is_dataclass(item):
            return {
                field.name: encode(getattr(item, field.name)) for field in fields(item)
            }
        if isinstance(item, dict):
            return {name: encode(value) for name, value in item.items()}
        if isinstance(item, (list, tuple)):
            return [encode(value) for value in item]
        return item

    data = json.dumps(
        encode(value), sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    return hashlib.sha256(data.encode()).hexdigest()


def _timed(fn):
    before = resource.getrusage(resource.RUSAGE_SELF)
    start, cpu = perf_counter(), process_time()
    result = fn()
    wall, cpu = perf_counter() - start, process_time() - cpu
    after = resource.getrusage(resource.RUSAGE_SELF)
    return result, {
        "wall_seconds": wall,
        "process_cpu_seconds": cpu,
        "voluntary_context_switches": after.ru_nvcsw - before.ru_nvcsw,
        "involuntary_context_switches": after.ru_nivcsw - before.ru_nivcsw,
    }


def _schedule(provider, frames, episode_count, explicit_windows=()):
    if explicit_windows:
        if len(explicit_windows) > 16:
            raise ValueError("at most 16 explicit replay windows are supported")
        episodes = []
        for spec in explicit_windows:
            task, ep, start = spec.split("/")
            ep, start = int(ep), int(start)
            key = (task, ep)
            if (
                key not in provider.train_episode_keys
                or start < 0
                or start + frames > provider.data.rows[key]["window_count"]
            ):
                raise ValueError(
                    "explicit replay window exceeds the certified Train index"
                )
            episodes.append((task, ep, start))
    else:
        selected = sorted(
            key
            for key in provider.train_episode_keys
            if provider.data.rows[key]["window_count"] >= frames
        )[:episode_count]
        if len(selected) != episode_count:
            raise ValueError(
                "too few certified Train episodes for the requested window"
            )
        episodes = [(task, ep, 0) for task, ep in selected]
    return [
        (task, ep, start + frame)
        for frame in range(frames)
        for task, ep, start in episodes
    ]


def _read_common(provider, key):
    task, ep, frame = key
    return provider.read_common(task_class=task, episode_index=ep, decision_frame=frame)


def _provider_run(open_provider, schedule, cache_size, workers, top_variant):
    providers = []
    loads = []
    available = SimpleQueue()
    local = threading.local()
    try:
        for _ in range(max(workers, 1)):
            fork = getattr(providers[0], "fork_for_worker", None) if providers else None
            provider = fork() if fork else open_provider()
            providers.append(provider)
            # Each fresh instance has empty private LRUs; the certified
            # manifests, readers and source verification are unchanged.
            if provider.data.cache or provider._views or provider._language:
                raise ValueError("paired provider case must start with empty LRUs")
            provider._episode_cache_size = provider.data.max_episodes = cache_size
            original_load = provider.data.load
            events = []
            loads.append(events)

            def record_load(row, load=original_load, timings=events):
                start = perf_counter()
                result = load(row)
                timings.append(perf_counter() - start)
                return result

            provider.data.load = record_load
            available.put(provider)

        def initialize():
            local.provider = available.get_nowait()

        def read(key):
            provider = local.provider
            start = perf_counter()
            common = _read_common(provider, key)
            common_seconds = perf_counter() - start
            start = perf_counter()
            views = (
                provider.read_selected_views(
                    common["identity"], top_view_variant=top_variant
                )
                if top_variant is not None
                else ()
            )
            return common, views, common_seconds, perf_counter() - start

        def execute():
            if not workers:
                initialize()
                return [read(key) for key in schedule]
            with ThreadPoolExecutor(
                max_workers=workers, initializer=initialize
            ) as pool:
                return list(pool.map(read, schedule))

        rows, metrics = _timed(execute)
        metrics.update(
            joint_and_state15_misses=sum(len(events) for events in loads),
            joint_and_state15_load_seconds=sum(sum(events) for events in loads),
            common_read_seconds=sum(row[2] for row in rows),
            selected_view_read_seconds=sum(row[3] for row in rows)
            if top_variant
            else 0,
            selected_view_requests=sum(
                provider.view_read_count for provider in providers
            ),
            selected_view_count=sum(len(row[1]) for row in rows),
            result_sha256=_digest([(common, views) for common, views, _, _ in rows]),
        )
        return metrics
    finally:
        for provider in providers:
            provider.close()


def _case_matrix(open_provider, schedule, caches, worker_counts, repeats, top_variant):
    cases = [(size, workers) for size in caches for workers in worker_counts]
    runs = {case: [] for case in cases}
    for repeat in range(repeats):
        # Counterbalance the case order while holding request ordering fixed.
        for size, workers in cases if repeat % 2 == 0 else reversed(cases):
            runs[size, workers].append(
                _provider_run(open_provider, schedule, size, workers, top_variant)
            )
    all_digests = {
        result["result_sha256"] for group in runs.values() for result in group
    }
    if len(all_digests) != 1:
        raise RuntimeError("DATA_C state/text/view result changed across cases")
    return [
        {"cache_size": size, "workers": workers, "repeats": runs[size, workers]}
        for size, workers in cases
    ]


class _CountedTokenizer:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.calls = 0

    def tokenize_text(self, *args, **kwargs):
        self.calls += 1
        return self.tokenizer.tokenize_text(*args, **kwargs)


def _cap2_run(tasks, recipe, tokenizer, seed, memoized):
    from cosmos_framework.data.generator.action.utils.static_task_text import (
        prepare_static_task_text,
        resolve_consumer_text_dropout,
    )
    from cosmos_framework.data.generator.action.utils.transforms import (
        ActionTransformPipeline,
    )

    counted = _CountedTokenizer(tokenizer)
    if memoized:
        pipeline = object.__new__(ActionTransformPipeline)
        pipeline.static_task_text_recipe = recipe
        pipeline.text_tokenizer = SimpleNamespace(_processor=counted)
        pipeline._g2_static_token_cache = OrderedDict()
        prepare = pipeline._prepare_cached_g2_text
    else:

        def prepare(task, *, dropout_applied):
            return prepare_static_task_text(
                task, recipe, counted, dropout_applied=dropout_applied
            )

    def execute():
        result = []
        for task in tasks:
            dropped = resolve_consumer_text_dropout({}, recipe.cfg_dropout_rate)
            result.append(prepare(task, dropout_applied=dropped))
        return result

    saved = random.getstate()
    try:
        random.seed(seed)
        result, metrics = _timed(execute)
        rng_sha = _digest(random.getstate())
    finally:
        random.setstate(saved)
    return {
        **metrics,
        "tokenizer_calls": counted.calls,
        "dropped": sum(row["text_dropout_applied"] for row in result),
        "result_sha256": _digest(result),
        "final_python_rng_sha256": rng_sha,
    }


def _compact_run(samples, compact):
    import torch
    from cosmos_framework.data.generator.action.utils.cached_pixel_geometry import (
        CachedGeometryResize,
        cached_pixel_placeholder,
    )
    from cosmos_framework.data.generator.action.utils.transforms import VideoResize

    resize = VideoResize()
    canvas = tuple(
        int(v)
        for v in resize(
            {"video": torch.zeros((3, 1, 256, 512), dtype=torch.uint8)}, None
        )["image_size"]
    )
    if compact:
        resize = CachedGeometryResize(resize, canvas)
    latent = torch.zeros((5, 48, canvas[0] // 16, canvas[1] // 16), dtype=torch.float32)

    def execute():
        for _ in range(samples):
            video = cached_pixel_placeholder(compact=compact)
            row = resize(
                {
                    "video": video,
                    "video_latent": latent,
                    "cached_latent_required": True,
                },
                None,
            )
        return video, row

    (video, row), metrics = _timed(execute)
    if row["video_latent"] is not latent:
        raise ValueError("image geometry must preserve the same latent")
    return {
        **metrics,
        "input_storage_bytes": video.untyped_storage().nbytes(),
        "output_storage_bytes": row["video"].untyped_storage().nbytes(),
        "geometry_sha256": _digest(
            (list(row["video"].shape), row["image_size"], latent)
        ),
    }


def _integers(arg, allowed):
    values = list(dict.fromkeys(map(int, arg.split(","))))
    if not values or not set(values) <= allowed:
        raise ValueError("invalid benchmark case choices")
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("probe", choices=("provider", "cap2", "compact"))
    parser.add_argument("--recipe", type=Path, help="materialized formal G2 recipe")
    parser.add_argument(
        "--edge", type=Path, help="local Edge processor assets for CAP2"
    )
    parser.add_argument("--episodes", type=int, choices=range(1, 17), default=8)
    parser.add_argument("--frames", type=int, choices=range(1, 17), default=16)
    parser.add_argument(
        "--window",
        action="append",
        default=[],
        metavar="TASK/EPISODE/START",
        help="replay a certified Train window in the given slot order (repeatable)",
    )
    parser.add_argument("--repeats", type=int, choices=range(1, 11), default=3)
    parser.add_argument(
        "--workers", default="0,1,2,4,8", help="provider-only worker counts"
    )
    parser.add_argument(
        "--caches", default="4,16", help="provider-only episode LRU sizes"
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="CAP2 legacy Python RNG seed"
    )
    args = parser.parse_args()

    os.environ.update(
        CUDA_VISIBLE_DEVICES="",
        COSMOS_DEVICE="cpu",
        COSMOS_TRAINING="1",
        HF_HUB_OFFLINE="1",
        TRANSFORMERS_OFFLINE="1",
    )
    import torch

    torch.set_num_threads(1)
    output = {"probe": args.probe, "torch_cpu_threads": torch.get_num_threads()}
    if args.probe == "compact":
        samples = args.frames * args.episodes
        runs = {mode: [] for mode in ("dense", "compact")}
        for repeat in range(args.repeats):
            for mode in tuple(runs) if repeat % 2 == 0 else reversed(runs):
                runs[mode].append(_compact_run(samples, mode == "compact"))
        if (
            len({run["geometry_sha256"] for group in runs.values() for run in group})
            != 1
        ):
            raise RuntimeError("compact placeholder changed official cached geometry")
        output.update(
            samples=samples,
            cases=runs,
            scope="synthetic cached pixels and native resize",
        )
    else:
        if args.recipe is None:
            parser.error("provider and CAP2 probes require --recipe")
        from examples.psm_wma_robocasa_g2_recipe import G2RunRecipe

        recipe = G2RunRecipe.open(args.recipe)
        if (
            recipe.provider_factory
            != "g2.data.verified_provider:open_verified_provider"
        ):
            parser.error("CPU probe requires the tracked certified DATA_C provider")

        def open_provider():
            return recipe.data_adapter().provider

        provider = open_provider()
        try:
            schedule = _schedule(provider, args.frames, args.episodes, args.window)
            if args.probe == "cap2":
                tasks = [
                    _read_common(provider, key)["static_task_text"] for key in schedule
                ]
        finally:
            provider.close()
        output.update(
            profile=recipe.training.profile,
            recipe_identity=recipe.identity,
            consumer_count=len(schedule),
            request_order_sha256=_digest(schedule),
        )
        if args.probe == "provider":
            output["scope"] = (
                "certified DATA_C provider only; excludes G1 raw/cache and Phase5 dispatch"
            )
            top = (
                recipe.global_memory.top_view_variant
                if recipe.global_memory.enabled
                else None
            )
            output["cases"] = _case_matrix(
                open_provider,
                schedule,
                _integers(args.caches, {4, 8, 16}),
                _integers(args.workers, {0, 1, 2, 4, 8}),
                args.repeats,
                top,
            )
        else:
            from cosmos_framework.data.generator.action.utils.transforms import (
                ActionTransformPipeline,
            )
            from cosmos_framework.data.generator.processors import build_processor

            if not hasattr(ActionTransformPipeline, "_prepare_cached_g2_text"):
                parser.error("CAP2 A/B requires the Child candidate memoizer")
            if args.edge is None or not args.edge.is_dir():
                parser.error(
                    "CAP2 A/B requires a local Edge processor --edge directory"
                )
            tokenizer = build_processor(tokenizer_type=str(args.edge.resolve()))
            runs = {mode: [] for mode in ("uncached", "memoized")}
            for repeat in range(args.repeats):
                for mode in tuple(runs) if repeat % 2 == 0 else reversed(runs):
                    runs[mode].append(
                        _cap2_run(
                            tasks, recipe.text, tokenizer, args.seed, mode == "memoized"
                        )
                    )
            if (
                len(
                    {
                        (row["result_sha256"], row["final_python_rng_sha256"])
                        for group in runs.values()
                        for row in group
                    }
                )
                != 1
            ):
                raise RuntimeError(
                    "CAP2 memoizer changed text values or the subsequent RNG state"
                )
            output["cases"] = runs
            output["scope"] = (
                "CAP2 tokenizer fields and Python CFG RNG; excludes full transform"
            )
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
