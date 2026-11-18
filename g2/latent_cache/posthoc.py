"""View-first lifecycle adapters over the existing record ledger and consumer.

No renderer, alternative encoder, fake stream ACK or output-profile upgrade.
All numerical writes and retry/ACK semantics belong to the existing core.
"""

from pathlib import Path

from g2.io import read_json

from .contract import CacheError, contained, make_recipe
from .storage import build_lock
from .streaming import ConsumerLimits, EventConsumer, EventSpool

LIFECYCLE = "view_first_posthoc_v1"


def coordinator(root):
    root = Path(root).absolute()
    return root.parent / (".posthoc-view-vae-" + root.name)


def _register(spool, root, manifest):
    job = spool.register(
        root,
        episode_key=f"{manifest['task_class']}/episode_{manifest['episode_id']:06d}",
        source_fingerprint=manifest["source_fingerprint"],
        profile_id=manifest["output_profile"]["profile_id"],
    )
    spool.offer_source(job)
    return job


def build_view_first_cache(
    root,
    encoder,
    *,
    spool_root,
    preprocessing=None,
    storage_dtype="float32",
    resume=False,
    limits=ConsumerLimits(),
    source_policy=None,
    failpoint=None,
):
    from g2.offline.stage_a import validate_profile_episode

    from .builder import verify_episode
    from .final_source import PROFILE_SCHEMA

    root = Path(root).absolute()
    recipe = make_recipe(
        encoder.descriptor(), preprocessing, storage_dtype=storage_dtype, batch_size=1
    )
    with build_lock(coordinator(root)):
        manifest = validate_profile_episode(root)
        if manifest["output_profile"]["view_vae"]:
            raise CacheError(
                "posthoc lifecycle requires a published View-first profile"
            )
        if manifest["schema"] == PROFILE_SCHEMA:
            return dict(
                already_complete=True,
                retired=True,
                audit=verify_episode(root, expected_recipe_id=recipe["recipe_id"]),
            )
        if (root / "vae_cache").exists() and not resume:
            raise CacheError("cache target exists; explicit resume is required")
        spool = EventSpool(
            spool_root,
            recipe,
            limits=limits,
            source_policy=source_policy,
            lifecycle=LIFECYCLE,
        )
        job = _register(spool, root, manifest)
        if resume:
            spool.retry(job)
        consumer = EventConsumer(spool, encoder, failpoint=failpoint)
        while True:
            with spool._db() as db:
                complete = db.execute(
                    "SELECT 1 FROM completed WHERE id=?", (job,)
                ).fetchone()
            if complete:
                spool.completed_receipt(job)
                return dict(
                    job=job,
                    complete=True,
                    retired=source_policy is not None,
                    audit=verify_episode(root, expected_recipe_id=recipe["recipe_id"]),
                )
            if not consumer.step():
                return dict(job=job, complete=False, pending=True, source_retained=True)


def retire_view_first_cache(root, *, spool_root, source_policy):
    """Explicit Stage C: genuine verified-cache handoff, never invented ACKs."""
    from g2.offline.stage_a import validate_profile_episode

    from . import final_source as final
    from .builder import verify_episode
    from .source_retirement import resume_pending

    root = Path(root).absolute()
    with build_lock(coordinator(root)):
        # Open/resume the original journal before validating partially swapped indices.
        if (Path(spool_root) / "config.json").exists():
            spool = EventSpool.open(spool_root)
            if spool.lifecycle != LIFECYCLE or spool.source_policy != source_policy:
                raise CacheError("posthoc retirement scope/policy differs")
            with spool._db() as db:
                row = db.execute(
                    "SELECT id,done FROM jobs WHERE target=?", (str(root),)
                ).fetchone()
            if row and row["done"]:
                if not resume_pending(spool, row["id"]):
                    return dict(complete=False, pending=True)
                return dict(complete=spool.reap(row["id"]))
        manifest = validate_profile_episode(root)
        if manifest["output_profile"]["view_vae"]:
            raise CacheError("posthoc retirement requires original View-first profile")
        if manifest["schema"] == final.PROFILE_SCHEMA:
            return dict(
                complete=True,
                already_complete=True,
                retired=True,
                audit=verify_episode(root),
            )
        recipe = read_json(contained(root, "vae_cache/manifest.json"))["recipe"]
        spool = EventSpool(
            spool_root, recipe, source_policy=source_policy, lifecycle=LIFECYCLE
        )
        job = _register(spool, root, manifest)
        return dict(job=job, complete=spool.adopt_completed(job))
