"""Shared identity for an EvalV2 Episode's current spatial publication."""

from __future__ import annotations

from g2.latent_cache.contract import fingerprint

PERIOD_FRAMES = 20
LIVE_VIEWS = "f27/latest_spatial_views.json"


def task_binding_identity(episode_id, source_sha256, task_set, text_id):
    return fingerprint(
        dict(
            episode_id=episode_id,
            source_sha256=source_sha256,
            task_set=task_set,
            text_id=text_id,
        )
    )
