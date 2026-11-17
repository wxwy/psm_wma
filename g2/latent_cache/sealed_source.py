"""Explicit Stage-A readiness adapter; legacy COMPLETE scanner is unchanged.

The historical cache header names manifest_sha256/complete_sha256 bind the
immutable spatial_source and SPATIAL_SOURCE_READY files for this schema. They
never refer to a fabricated episode COMPLETE or the later final profile hash.
"""

from __future__ import annotations

from pathlib import Path

from g2.io import digest, read_json

from .contract import CacheError, contained


def is_sealed(root):
    from g2.offline.output_profile import SCHEMA

    from .final_source import PROFILE_SCHEMA

    return read_json(contained(root, "episode_manifest.json")).get("schema") in (
        SCHEMA,
        PROFILE_SCHEMA,
    )


def scan_source(root):
    if not is_sealed(root):
        from .source import scan_episode

        return scan_episode(root)
    from g2.offline.stage_a import validate_profile_episode

    root = Path(root).absolute()
    manifest = validate_profile_episode(
        root, require_complete=False, _check_cache=False
    )
    if not manifest["output_profile"]["view_vae"]:
        raise CacheError(
            "new source profile declares VAE disabled; do not change its completed output contract"
        )
    from . import final_source as final

    is_final = manifest["schema"] == final.PROFILE_SCHEMA
    source_path = contained(root, final.CAPSULE if is_final else "spatial_source.json")
    ready_path = contained(
        root, final.READY if is_final else "SPATIAL_SOURCE_READY.json"
    )
    before = (digest(source_path), digest(ready_path))
    source = (
        final.materialize_source(root, manifest) if is_final else read_json(source_path)
    )
    states = [
        dict(state_ordinal=i, logical_state_id=r["state_id"], frame=r["frame"])
        for i, r in enumerate(source["states"])
    ]
    views = {}
    for vid, view in sorted(source["views"].items()):
        records = []
        for i, owner in enumerate(view["owners"]):
            event = source["final_pixel_events"][owner["event_id"]]
            from .streaming import validate_descriptor

            validate_descriptor(event)
            if (
                event["source_fingerprint"] != source["source_fingerprint"]
                or event["profile_id"] != source["profile_id"]
                or event["episode_key"]
                != f"{source['task_class']}/episode_{source['episode_id']:06d}"
            ):
                raise CacheError("event computational scope differs from sealed source")
            records.append(
                dict(
                    record_index=i,
                    owner_state_ordinal=owner["state_id"],
                    owner_state_id=owner["state_id"],
                    owner_frame=owner["frame"],
                    png_path=owner["path"],
                    png_sha256=owner["sha256"],
                    original_hw=list(reversed(event["size_wh"])),
                    color_mode="RGB",
                    event_id=owner["event_id"],
                    pixel_record_key=event["pixel_record_key"],
                )
            )
        views[vid] = dict(
            path=vid + ".pt",
            records=records,
            state_records=view["state_records"],
            spatial_metadata=dict(
                status="SEALED_NATIVE_RENDERER", source_id=source["source_id"]
            ),
        )
    if before != (digest(source_path), digest(ready_path)):
        raise CacheError("spatial readiness changed while planning")
    binding = (
        final.source_binding(final.load_capsule(root), root)
        if is_final
        else dict(
            schema=source["schema"],
            source_id=source["source_id"],
            manifest_sha256=before[0],
            complete_sha256=before[1],
            identity_manifest="spatial_source.json",
            readiness_marker="SPATIAL_SOURCE_READY.json",
            validation_scope="SEALED_SPATIAL_SOURCE_AND_FINAL_PIXELS",
        )
    )
    return dict(
        episode_root=str(root),
        episode_key=f"{source['task_class']}/episode_{source['episode_id']:06d}",
        episode=dict(task_class=source["task_class"], episode_id=source["episode_id"]),
        source=binding,
        states=states,
        views=views,
    )


def verify_source(plan):
    current = scan_source(plan["episode_root"])
    if current != {k: plan[k] for k in current}:
        raise CacheError("sealed or legacy source changed during encoding")
    return True


def released_inputs(root, source):
    """A release is valid only against an intact complete numerical cache.

    No retained PNG, SG, metadata or raw renderer file can be released here.
    The immutable source still lists original PNG hashes after bounded spool
    cleanup; cache view metadata supplies the exact hash/record mapping.
    """
    path = Path(root) / "VAE_INPUT_RELEASE.json"
    if not path.exists():
        return {}
    from .builder import verify_episode
    from .storage import open_episode_index

    receipt = read_json(contained(root, path.name))
    from . import final_source as final

    if source.get("schema") == final.SOURCE_SCHEMA:
        capsule = final.load_capsule(root)
        if receipt != dict(
            schema="g2_released_vae_inputs_v1",
            source_id=source["source_id"],
            cache_manifest_sha256=capsule["working_cache_receipt"][
                "cache_manifest_sha256"
            ],
            files={},
        ):
            raise CacheError(
                "final retained-PNG source has invalid old input-release provenance"
            )
        return {}
    verify_episode(root, check_source=False)
    index = open_episode_index(root)
    allowed = {
        o["path"]: o["sha256"]
        for v in source["views"].values()
        for o in v["owners"]
        if o["path"] and o["path"].startswith("_spatial_inputs/")
    }
    if (
        receipt.get("schema") != "g2_released_vae_inputs_v1"
        or receipt.get("source_id") != source["source_id"]
        or receipt.get("cache_manifest_sha256")
        != digest(index.cache_root / "manifest.json")
        or receipt.get("files") != allowed
    ):
        raise CacheError("input release does not match sealed source/cache")
    # Compare every released byte hash to the immutable cached owner inventory.
    for vid, view in source["views"].items():
        cached = index.manifest["views"].get(vid)
        if cached is None:
            raise CacheError("released source has no numerical view")
        from .storage import inspect_view_payload

        meta = inspect_view_payload(contained(index.cache_root, cached["path"]))[
            "metadata"
        ]
        for owner, record in zip(
            view["owners"], meta["view_plan"]["records"], strict=True
        ):
            if (
                owner["path"] != record["png_path"]
                or owner["sha256"] != record["png_sha256"]
            ):
                raise CacheError(
                    "released PNG hash/owner differs from numerical record"
                )
        if meta["source"].get("source_id") != source["source_id"]:
            raise CacheError("released numeric source differs")
    return allowed
