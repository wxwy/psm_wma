"""Explicit real/fake batch replay, preserving each original ordered context.

Ordinary training reads never import this module or construct an encoder.
"""

from pathlib import Path

from .batch_contract import is_batch, validate_context
from .builder import _read_rgb, verify_episode
from .contract import CacheError, contained
from .storage import _load, open_episode_index


def verify_replay(dataset_root, encoder, *, tasks=None, episodes=None):
    import torch

    from .batch_engine import discover_published
    from .sealed_source import scan_source

    data = Path(dataset_root).absolute()
    roots = discover_published(data, tasks=tasks, episodes=episodes)
    selected, contexts, plans = {}, {}, {}
    recipe = None
    for root in roots:
        verify_episode(root)
        index = open_episode_index(root)
        current = index.manifest["recipe"]
        if not is_batch(current) or current["encoder"] != encoder.descriptor():
            raise CacheError("batch replay needs the original batch recipe and encoder")
        if recipe is not None and current != recipe:
            raise CacheError("mixed numerical recipes cannot share one replay")
        recipe = current
        for vid, row in index.manifest["views"].items():
            payload, _, _ = _load(contained(root / "vae_cache", row["path"]))
            meta = payload["metadata"]
            for n, prep in enumerate(meta["preprocessing"]):
                execution = prep["numerical_execution"]
                key = execution["batch_id"]
                context = meta["batch_executions"][key]
                validate_context(context, recipe)
                if key in contexts and contexts[key] != context:
                    raise CacheError("numerical context differs across View files")
                contexts[key] = context
                selected.setdefault(key, []).append(
                    (execution["position"], payload["latents"][n])
                )
    maximum, count = 0.0, 0
    for key, context in contexts.items():
        images = []
        for member in context["members"]:
            event = member["event"]
            episode = event["episode_key"]
            root = (
                contained(
                    data,
                    "tasks/"
                    + episode.split("/")[0]
                    + "/episodes/"
                    + episode.split("/")[1],
                )
                if not (data / "episode_manifest.json").exists()
                else data
            )
            if episode not in plans:
                plan = scan_source(root, view_first=True)
                if plan["episode_key"] != episode:
                    raise CacheError("batch replay member belongs to another episode")
                plans[episode] = (root, plan)
            _, plan = plans[episode]
            matches = [
                r
                for r in plan["views"][event["view_id"]]["records"]
                if r.get("event_id") == event["event_id"]
                and r["png_sha256"] == event["rgb_sha256"]
            ]
            if not matches:
                raise CacheError(
                    "original batch input no longer resolves to its verified owner"
                )
            images.append(_read_rgb(plan, matches[0]))
        produced = encoder.encode_batch(images, recipe["preprocessing"])
        for position, cached in selected[key]:
            value = produced[position][0]
            if not torch.equal(value, cached):
                raise CacheError("same ordered numerical context failed exact replay")
            maximum = max(maximum, float((value - cached).abs().max()))
            count += 1
    if not roots or not count:
        raise CacheError("no batch cache records selected for replay")
    return dict(
        complete=True,
        recipe_id=recipe["recipe_id"],
        episodes_checked=len(roots),
        batch_contexts_checked=len(contexts),
        records_checked=count,
        max_abs_error=maximum,
        atol=0,
        rtol=0,
        training_ready=False,
    )
